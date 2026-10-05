"""Durable local provider protocol; never performs a model or network call."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import re
import sqlite3
import sys

TERMINAL = {'succeeded', 'failed', 'cancelled'}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def load_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('Duplicate JSON key: ' + key)
            out[key] = value
        return out

    def nonfinite(value):
        raise ValueError('Non-finite JSON value: ' + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names):
        raise ValueError('Unexpected or missing fields: ' + ', '.join(names))


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,128}', value):
        raise ValueError('Invalid identity')


def request_valid(value):
    fields(value, ['request_id', 'idempotency_key', 'model', 'input', 'limits'])
    for name in ['request_id', 'idempotency_key', 'model']:
        identifier(value[name])
    if not isinstance(value['input'], str) or not value['input'].strip():
        raise ValueError('Input must be nonempty text')
    fields(value['limits'], ['timeout_ms', 'max_output_tokens'])
    for n in value['limits'].values():
        if type(n) is not int or n < 1:
            raise ValueError('Limits must be positive integers; declaration is not provider enforcement')


def event_valid(value):
    fields(value, ['request_id', 'provider_run_id', 'event_id', 'status', 'output', 'error', 'usage'])
    identifier(value['request_id']); identifier(value['event_id'])
    if value['status'] not in TERMINAL | {'running', 'unknown'}:
        raise ValueError('Invalid observed state')
    if value['provider_run_id'] is not None:
        identifier(value['provider_run_id'])
    elif value['status'] != 'unknown':
        raise ValueError('Known provider run identity required for this observation')
    if value['status'] == 'succeeded':
        if not isinstance(value['output'], str) or value['error'] is not None:
            raise ValueError('Success requires text output and no error')
    elif value['output'] is not None:
        raise ValueError('Non-success output must be null')
    if value['status'] in {'failed', 'unknown'}:
        if not isinstance(value['error'], str) or not value['error'].strip():
            raise ValueError('Failed/unknown observation requires an actual reason')
    elif value['error'] is not None:
        raise ValueError('Unexpected error field')
    if value['usage'] is not None:
        fields(value['usage'], ['input_tokens', 'output_tokens'])
        if any(type(n) is not int or n < 0 for n in value['usage'].values()):
            raise ValueError('Usage must be nonnegative measured integers or null')


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as c:
            c.execute('CREATE TABLE IF NOT EXISTS requests (request_id TEXT PRIMARY KEY, idem TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL, provider_run_id TEXT, cancel_requested INTEGER NOT NULL DEFAULT 0)')
            c.execute('CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, request_id TEXT NOT NULL REFERENCES requests(request_id), payload TEXT NOT NULL)')

    @contextmanager
    def db(self):
        c = sqlite3.connect(self.path, timeout=5)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        try:
            c.execute('BEGIN IMMEDIATE')
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

    @staticmethod
    def row(c, request_id):
        row = c.execute('SELECT * FROM requests WHERE request_id=?', (request_id,)).fetchone()
        if row is None:
            raise ValueError('Unknown request identity')
        return dict(row)

    def submit(self, request):
        request_valid(request)
        payload = canonical(request)
        with self.db() as c:
            prior = c.execute('SELECT * FROM requests WHERE idem=? OR request_id=?',
                              (request['idempotency_key'], request['request_id'])).fetchall()
            if prior:
                if len(prior) != 1 or prior[0]['payload'] != payload:
                    raise ValueError('Request identity/idempotency content conflict')
                return dict(created=False, should_dispatch=False, request_id=prior[0]['request_id'],
                            status=prior[0]['status'])
            c.execute('INSERT INTO requests(request_id,idem,payload,status) VALUES(?,?,?,?)',
                      (request['request_id'], request['idempotency_key'], payload, 'accepted'))
        return dict(created=True, should_dispatch=True, request_id=request['request_id'], status='accepted')

    def observe(self, event):
        event_valid(event)
        payload = canonical(event)
        with self.db() as c:
            row = self.row(c, event['request_id'])
            prior = c.execute('SELECT payload FROM events WHERE event_id=?', (event['event_id'],)).fetchone()
            if prior:
                if prior['payload'] != payload:
                    raise ValueError('Duplicate event content conflict')
                return dict(reused=True, status=row['status'])
            if row['status'] in TERMINAL:
                raise ValueError('Terminal request cannot accept another observation')
            if row['provider_run_id'] and event['provider_run_id'] not in {None, row['provider_run_id']}:
                raise ValueError('Provider run identity changed')
            c.execute('INSERT INTO events(event_id,request_id,payload) VALUES(?,?,?)',
                      (event['event_id'], event['request_id'], payload))
            c.execute('UPDATE requests SET status=?,provider_run_id=? WHERE request_id=?',
                      (event['status'], event['provider_run_id'] or row['provider_run_id'], event['request_id']))
        return dict(reused=False, status=event['status'])

    def cancel(self, request_id):
        identifier(request_id)
        with self.db() as c:
            row = self.row(c, request_id)
            if row['status'] not in TERMINAL:
                c.execute('UPDATE requests SET cancel_requested=1 WHERE request_id=?', (request_id,))
                row['cancel_requested'] = 1
        return dict(status=row['status'], cancel_requested=bool(row['cancel_requested']),
                    terminal_proven=row['status'] in TERMINAL)

    def get(self, request_id):
        identifier(request_id)
        with self.db() as c:
            row = self.row(c, request_id)
            events = [json.loads(e['payload']) for e in c.execute(
                'SELECT payload FROM events WHERE request_id=? ORDER BY rowid', (request_id,))]
        return dict(request=json.loads(row['payload']), status=row['status'],
                    provider_run_id=row['provider_run_id'], cancel_requested=bool(row['cancel_requested']),
                    events=events, boundary='Local observed ledger, not authenticated provider telemetry')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database', type=Path, required=True)
    p.add_argument('command', choices=['submit', 'observe', 'get', 'cancel'])
    p.add_argument('value', help='JSON file for submit/observe; request ID for get/cancel')
    a = p.parse_args()
    try:
        value = load_json(Path(a.value).read_text()) if a.command in {'submit', 'observe'} else a.value
        if a.command == 'submit': request_valid(value)
        if a.command == 'observe': event_valid(value)
        result = getattr(Store(a.database), a.command)(value)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, OSError, sqlite3.Error) as exc:
        print(json.dumps(dict(error=str(exc)), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
