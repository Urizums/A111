#!/usr/bin/env python3
"""Frozen CLI acceptance harness for the local provider adapter."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT = Path('/workspace/A111/runs/future/provider-adapter')
ADAPTER = ROOT / 'adapter.py'
WORKER = Path(__file__).resolve().parent
RUNTIME = 'py' + str(sys.version_info.major) + '.' + str(sys.version_info.minor)
OUT = WORKER / (RUNTIME + '-acceptance-rerun')
DBS = OUT / 'db'
INPUTS = OUT / 'inputs'
OUT.mkdir(parents=True, exist_ok=True)
DBS.mkdir(exist_ok=True)
INPUTS.mkdir(exist_ok=True)
LOG = []
CHECKS = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(name, value):
    path = INPUTS / name
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=True, separators=(',', ':')))
    return path


def save_raw(name, text):
    path = INPUTS / name
    path.write_text(text)
    return path


def inspect_db(db):
    db = Path(db)
    if not db.exists():
        return {'exists': False, 'requests': [], 'events': []}
    try:
        c = sqlite3.connect('file:' + str(db) + '?mode=ro', uri=True)
        c.row_factory = sqlite3.Row
        req = [dict(row) for row in c.execute('SELECT * FROM requests ORDER BY rowid')]
        ev = [dict(row) for row in c.execute('SELECT * FROM events ORDER BY rowid')]
        c.close()
        return {'exists': True, 'requests': req, 'events': ev}
    except Exception as e:
        return {'exists': True, 'inspection_error': repr(e)}


def record(label, args, proc, db, expected_code, expected_json=None, expectation=None):
    stdout = proc.stdout.decode('utf-8', 'replace') if isinstance(proc.stdout, bytes) else proc.stdout
    stderr = proc.stderr.decode('utf-8', 'replace') if isinstance(proc.stderr, bytes) else proc.stderr
    parsed = None
    for raw in [stdout.strip(), stderr.strip()]:
        if raw:
            try:
                parsed = json.loads(raw)
                break
            except Exception:
                pass
    item = {
        'label': label,
        'command': list(args),
        'exit_code': proc.returncode,
        'stdout': stdout,
        'stderr': stderr,
        'parsed_json': parsed,
        'database_after_process_exit': inspect_db(db),
        'expected_exit_code': expected_code,
        'expectation': None if expectation is None else 'predicate asserted by harness',
    }
    if expected_json is not None:
        item['expected_json_subset'] = expected_json
    LOG.append(item)
    ok = proc.returncode == expected_code
    if expected_json is not None:
        ok = ok and isinstance(parsed, dict) and all(parsed.get(k) == v for k, v in expected_json.items())
    if expectation is not None:
        try:
            ok = ok and bool(expectation(item))
        except Exception as e:
            ok = False
            item['expectation_error'] = repr(e)
    CHECKS.append({'label': label, 'passed': bool(ok)})
    (OUT / 'commands.partial.json').write_text(json.dumps(LOG, indent=2, ensure_ascii=False) + '\n')
    return item


def call(label, dbname, command, value, expect_code=0, expect_json=None, expectation=None):
    db = DBS / dbname
    args = [sys.executable, str(ADAPTER), '--database', str(db), command, str(value)]
    proc = subprocess.run(args, capture_output=True, text=True)
    return record(label, args, proc, db, expect_code, expect_json, expectation)


def request(rid, idem, text='prompt alpha', limits=None):
    return {
        'request_id': rid,
        'idempotency_key': idem,
        'model': 'model-local-test',
        'input': text,
        'limits': limits if limits is not None else {'timeout_ms': 1, 'max_output_tokens': 1},
    }


def event(rid, eid, status, run='run-A', output=None, error=None, usage=None):
    return {
        'request_id': rid,
        'provider_run_id': run,
        'event_id': eid,
        'status': status,
        'output': output,
        'error': error,
        'usage': usage,
    }


def submit(label, db, obj, code=0, subset=None, expectation=None):
    # Make semantic-order variants possible without changing the request itself.
    path = save_json(label.replace('/', '_') + '.json', obj)
    return call(label, db, 'submit', path, code, subset, expectation)


def observe(label, db, obj, code=0, subset=None, expectation=None):
    path = save_json(label.replace('/', '_') + '.json', obj)
    return call(label, db, 'observe', path, code, subset, expectation)


def malformed(label, db, command, raw):
    path = save_raw(label.replace('/', '_') + '.json', raw)
    return call(label, db, command, path, 2, expectation=lambda x: bool(x['stderr'].strip()) and not x['database_after_process_exit']['requests'])


def check_state(label, db, predicate, description):
    state = inspect_db(DBS / db)
    try:
        passed = bool(predicate(state))
    except Exception as e:
        passed = False
        description += ' (predicate exception: ' + repr(e) + ')'
    CHECKS.append({'label': label, 'passed': passed, 'description': description, 'state': state})
    return state


def main():
    print('RUNTIME', sys.version.replace('\n', ' '))
    print('EXECUTABLE', sys.executable)
    print('ADAPTER_SHA256', sha(ADAPTER))
    print('CONTRACT_SHA256', sha(ROOT / 'contract.json'))

    # Request lifecycle and durable idempotency. DB is inspected after every CLI process.
    req_a = request('req-main', 'idem-main')
    submit('main-first-submit', 'lifecycle.db', req_a, subset={'created': True, 'should_dispatch': True, 'request_id': 'req-main', 'status': 'accepted'})
    check_state('main-durable-before-caller-dispatch', 'lifecycle.db', lambda s: len(s['requests']) == 1 and s['requests'][0]['status'] == 'accepted' and s['requests'][0]['payload'] == json.dumps(req_a, ensure_ascii=False, sort_keys=True, separators=(',', ':')), 'request row is committed in accepted state before caller dispatch')
    # JSON key order differs; protocol payload is unchanged.
    reordered = {'limits': {'max_output_tokens': 1, 'timeout_ms': 1}, 'input': 'prompt alpha', 'model': 'model-local-test', 'idempotency_key': 'idem-main', 'request_id': 'req-main'}
    submit('main-identical-retry-key-order-varied', 'lifecycle.db', reordered, subset={'created': False, 'should_dispatch': False, 'request_id': 'req-main', 'status': 'accepted'})
    submit('main-altered-content-same-idempotency', 'lifecycle.db', request('req-main-2', 'idem-main', 'prompt changed'), 2, expectation=lambda x: 'conflict' in x['stderr'].lower())
    submit('main-altered-idempotency-same-request-id', 'lifecycle.db', request('req-main', 'idem-other', 'prompt changed'), 2, expectation=lambda x: 'conflict' in x['stderr'].lower())
    check_state('main-conflicts-preserve-single-record', 'lifecycle.db', lambda s: len(s['requests']) == 1 and len(s['events']) == 0, 'both changed-content collisions leave the original single request intact')

    observe('main-ambiguous-dispatch-unknown', 'lifecycle.db', event('req-main', 'evt-unknown', 'unknown', None, None, 'dispatch outcome ambiguous', None), subset={'reused': False, 'status': 'unknown'})
    submit('main-retry-while-unknown-no-redispatch', 'lifecycle.db', req_a, subset={'created': False, 'should_dispatch': False, 'request_id': 'req-main', 'status': 'unknown'})
    call('main-reopen-get-unknown', 'lifecycle.db', 'get', 'req-main', 0, {'status': 'unknown', 'provider_run_id': None})
    observe('main-matching-provider-running', 'lifecycle.db', event('req-main', 'evt-running', 'running', 'run-A'), subset={'reused': False, 'status': 'running'})
    observe('main-provider-run-identity-drift', 'lifecycle.db', event('req-main', 'evt-drift', 'running', 'run-B'), 2, expectation=lambda x: 'identity changed' in x['stderr'].lower())
    observe('main-unbound-request-identity', 'lifecycle.db', event('req-not-known', 'evt-unbound', 'running', 'run-A'), 2, expectation=lambda x: 'unknown request' in x['stderr'].lower())
    success_a = event('req-main', 'evt-success', 'succeeded', 'run-A', 'accepted output', None, None)
    observe('main-success-null-usage', 'lifecycle.db', success_a, subset={'reused': False, 'status': 'succeeded'})
    observe('main-identical-terminal-event-repeat', 'lifecycle.db', success_a, subset={'reused': True, 'status': 'succeeded'})
    changed_duplicate = event('req-main', 'evt-success', 'succeeded', 'run-A', 'different output', None, None)
    observe('main-changed-duplicate-event-content', 'lifecycle.db', changed_duplicate, 2, expectation=lambda x: 'duplicate event content conflict' in x['stderr'].lower())
    observe('main-contradictory-new-terminal', 'lifecycle.db', event('req-main', 'evt-fail-after-success', 'failed', 'run-A', None, 'contradictory', None), 2, expectation=lambda x: 'terminal request' in x['stderr'].lower())
    call('main-reopen-get-terminal', 'lifecycle.db', 'get', 'req-main', 0, {'status': 'succeeded', 'provider_run_id': 'run-A'})
    check_state('main-reopen-history-intact', 'lifecycle.db', lambda s: len(s['requests']) == 1 and s['requests'][0]['status'] == 'succeeded' and len(s['events']) == 3 and all(json.loads(x['payload']).get('usage') is None for x in s['events']), 'fresh processes observe accepted -> unknown -> running -> succeeded event history; usage remains null')

    # Cancellation intent racing with success.
    req_b = request('req-cancel-success', 'idem-cancel-success', 'cancel race')
    submit('cancel-race-submit', 'cancel-success.db', req_b, subset={'created': True, 'should_dispatch': True, 'status': 'accepted'})
    observe('cancel-race-provider-running', 'cancel-success.db', event('req-cancel-success', 'evt-csrunning', 'running', 'run-C'), subset={'reused': False, 'status': 'running'})
    call('cancel-race-intent', 'cancel-success.db', 'cancel', 'req-cancel-success', 0, {'status': 'running', 'cancel_requested': True, 'terminal_proven': False})
    call('cancel-race-intent-does-not-settle', 'cancel-success.db', 'get', 'req-cancel-success', 0, {'status': 'running', 'cancel_requested': True, 'provider_run_id': 'run-C'})
    observe('cancel-race-success-settles', 'cancel-success.db', event('req-cancel-success', 'evt-csuccess', 'succeeded', 'run-C', 'success won race', None, None), subset={'reused': False, 'status': 'succeeded'})
    call('cancel-race-success-is-terminal-proof', 'cancel-success.db', 'get', 'req-cancel-success', 0, {'status': 'succeeded', 'cancel_requested': True, 'provider_run_id': 'run-C'})
    submit('cancel-race-retry-no-redispatch', 'cancel-success.db', req_b, subset={'created': False, 'should_dispatch': False, 'status': 'succeeded'})
    check_state('cancel-race-durable', 'cancel-success.db', lambda s: s['requests'][0]['cancel_requested'] == 1 and s['requests'][0]['status'] == 'succeeded' and len(s['events']) == 2, 'cancel intent persists, success is terminal, and both observations remain in history')

    # Explicit provider cancellation acknowledgement.
    req_c = request('req-cancel-ack', 'idem-cancel-ack', 'cancel ack')
    submit('cancel-ack-submit', 'cancel-ack.db', req_c, subset={'created': True, 'should_dispatch': True, 'status': 'accepted'})
    call('cancel-ack-intent', 'cancel-ack.db', 'cancel', 'req-cancel-ack', 0, {'status': 'accepted', 'cancel_requested': True, 'terminal_proven': False})
    observe('cancel-ack-provider-terminal', 'cancel-ack.db', event('req-cancel-ack', 'evt-cancel-ack', 'cancelled', 'run-D'), subset={'reused': False, 'status': 'cancelled'})
    call('cancel-ack-terminal-proof', 'cancel-ack.db', 'get', 'req-cancel-ack', 0, {'status': 'cancelled', 'cancel_requested': True, 'provider_run_id': 'run-D'})
    check_state('cancel-ack-durable', 'cancel-ack.db', lambda s: s['requests'][0]['status'] == 'cancelled' and s['requests'][0]['cancel_requested'] == 1 and len(s['events']) == 1, 'explicit cancellation acknowledgement is the durable terminal proof')

    # Strict request JSON and local numeric constraints.
    raw_request = json.dumps(request('x', 'i'), separators=(',', ':'))
    malformed('invalid-malformed-request-json', 'bad-malformed.db', 'submit', '{')
    malformed('invalid-duplicate-request-json-key', 'bad-duplicate.db', 'submit', raw_request[:-1] + ',"request_id":"second"}')
    nonfinite_req = raw_request.replace('"timeout_ms":1', '"timeout_ms":NaN')
    malformed('invalid-nonfinite-request-number', 'bad-nonfinite.db', 'submit', nonfinite_req)
    extra_req = request('x', 'i'); extra_req['extra'] = 'nope'
    submit('invalid-unknown-request-field', 'bad-extra.db', extra_req, 2)
    bool_req = request('x', 'i'); bool_req['limits']['max_output_tokens'] = True
    submit('invalid-bool-output-limit', 'bad-bool.db', bool_req, 2)
    zero_req = request('x', 'i'); zero_req['limits']['timeout_ms'] = 0
    submit('invalid-zero-timeout-limit', 'bad-zero.db', zero_req, 2)
    string_req = request('x', 'i'); string_req['limits']['timeout_ms'] = '100'
    submit('invalid-string-timeout-limit', 'bad-string-limit.db', string_req, 2)
    empty_req = request('x', 'i', '   ')
    submit('invalid-blank-input', 'bad-blank.db', empty_req, 2)
    invalid_id_req = request('bad id', 'i')
    submit('invalid-request-identifier', 'bad-identity.db', invalid_id_req, 2)
    # Limits are positive integers locally; no adapter upper ceiling is declared. Minimum value accepted.
    submit('limits-minimum-positive-values', 'limits-minimum.db', request('req-limits-min', 'idem-limits-min', 'minimum', {'timeout_ms': 1, 'max_output_tokens': 1}), subset={'created': True, 'should_dispatch': True, 'status': 'accepted'})

    # Strict event JSON, event fields/identity, and usage validation.
    raw_event = json.dumps(event('x', 'e', 'running', 'run-X'), separators=(',', ':'))
    malformed('invalid-malformed-event-json', 'bad-event-malformed.db', 'observe', '{')
    malformed('invalid-duplicate-event-json-key', 'bad-event-duplicate.db', 'observe', raw_event[:-1] + ',"event_id":"other"}')
    nonfinite_event = raw_event.replace('"usage":null', '"usage":{"input_tokens":NaN,"output_tokens":1}')
    malformed('invalid-nonfinite-event-usage', 'bad-event-nonfinite.db', 'observe', nonfinite_event)
    req_d = request('req-event-invalid', 'idem-event-invalid')
    submit('event-validation-seed-submit', 'event-invalid.db', req_d, subset={'created': True, 'should_dispatch': True})
    bad_extra_event = event('req-event-invalid', 'ev-extra', 'running', 'run-E'); bad_extra_event['extra'] = 1
    observe('invalid-unknown-event-field', 'event-invalid.db', bad_extra_event, 2)
    bad_usage_event = event('req-event-invalid', 'ev-usage-extra', 'running', 'run-E', usage={'input_tokens': 1, 'output_tokens': 1, 'provider': 'invented'})
    observe('invalid-unknown-usage-field', 'event-invalid.db', bad_usage_event, 2)
    bool_usage_event = event('req-event-invalid', 'ev-usage-bool', 'running', 'run-E', usage={'input_tokens': True, 'output_tokens': 1})
    observe('invalid-bool-usage-count', 'event-invalid.db', bool_usage_event, 2)
    negative_usage_event = event('req-event-invalid', 'ev-usage-negative', 'running', 'run-E', usage={'input_tokens': -1, 'output_tokens': 1})
    observe('invalid-negative-usage-count', 'event-invalid.db', negative_usage_event, 2)
    no_run_event = event('req-event-invalid', 'ev-no-run', 'running', None)
    observe('invalid-known-event-missing-provider-run-id', 'event-invalid.db', no_run_event, 2)
    invalid_event_id = event('req-event-invalid', 'bad event', 'running', 'run-E')
    observe('invalid-event-identity-syntax', 'event-invalid.db', invalid_event_id, 2)
    unknown_status = event('req-event-invalid', 'ev-status', 'pending', 'run-E')
    observe('invalid-event-status', 'event-invalid.db', unknown_status, 2)
    # Verify valid usage structure is accepted without treating null as zero.
    valid_usage = event('req-event-invalid', 'ev-valid-usage', 'running', 'run-E', usage={'input_tokens': 4, 'output_tokens': 2})
    observe('valid-measured-usage', 'event-invalid.db', valid_usage, subset={'reused': False, 'status': 'running'})
    unknown_after_running = event('req-event-invalid', 'ev-unknown-null-run', 'unknown', None, None, 'outcome uncertain', None)
    observe('valid-unknown-null-usage-identity', 'event-invalid.db', unknown_after_running, subset={'reused': False, 'status': 'unknown'})
    call('event-validation-reopen', 'event-invalid.db', 'get', 'req-event-invalid', 0, {'status': 'unknown', 'provider_run_id': 'run-E'})
    check_state('event-validation-history-and-null', 'event-invalid.db', lambda s: len(s['events']) == 2 and json.loads(s['events'][0]['payload'])['usage'] == {'input_tokens': 4, 'output_tokens': 2} and json.loads(s['events'][1]['payload'])['usage'] is None, 'valid measured usage is retained while unavailable usage remains null')

    # Same idempotency key racing in separate local CLI processes.
    concurrent_req = request('req-concurrent', 'idem-concurrent', 'same concurrent content')
    cp = save_json('concurrent-request.json', concurrent_req)
    cdb = DBS / 'concurrent.db'
    argv = [sys.executable, str(ADAPTER), '--database', str(cdb), 'submit', str(cp)]
    children = [subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
    children_results = [p.communicate() for p in children]
    summaries = []
    for idx, (out, err) in enumerate(children_results):
        class Proc:
            pass
        proc = Proc(); proc.stdout = out; proc.stderr = err; proc.returncode = children[idx].returncode
        rec = record('concurrent-identical-submit-' + str(idx + 1), argv, proc, cdb, 0)
        summaries.append(rec)
    parsed = [x['parsed_json'] for x in summaries]
    CHECKS.append({'label': 'concurrent-submit-one-dispatch-only', 'passed': len(parsed) == 2 and sorted(x.get('should_dispatch') for x in parsed if isinstance(x, dict)) == [False, True] and len(inspect_db(cdb)['requests']) == 1, 'description': 'local SQLite transaction serializes identical submissions to one dispatch decision and one durable request'})

    # Fresh final CLI process for history of each main durability flow.
    call('final-reopen-main-history', 'lifecycle.db', 'get', 'req-main')
    call('final-reopen-cancel-success-history', 'cancel-success.db', 'get', 'req-cancel-success')
    call('final-reopen-cancel-ack-history', 'cancel-ack.db', 'get', 'req-cancel-ack')

    result = {
        'runtime': sys.version.replace('\n', ' '),
        'executable': sys.executable,
        'candidate': str(ADAPTER),
        'candidate_sha256': sha(ADAPTER),
        'contract_sha256': sha(ROOT / 'contract.json'),
        'commands': LOG,
        'checks': CHECKS,
        'summary': {
            'checks_total': len(CHECKS),
            'checks_passed': sum(1 for x in CHECKS if x.get('passed')),
            'checks_failed': [x for x in CHECKS if not x.get('passed')],
            'cli_commands': len(LOG),
            'tokens': None,
            'cost': None,
            'provider_identity': None,
            'model_active_time': None,
        },
    }
    (OUT / 'results.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    print('RESULTS', OUT / 'results.json')
    print('SUMMARY', json.dumps(result['summary'], sort_keys=True))
    if result['summary']['checks_failed']:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
