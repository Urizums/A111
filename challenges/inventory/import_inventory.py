#!/usr/bin/env python3
"""Atomically import versioned equipment JSON into a durable SQLite database."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import sqlite3


def exact(row, fields):
    if not isinstance(row,dict) or set(row) != set(fields):
        raise ValueError('Unexpected or missing fields: expected ' + ', '.join(fields))


def text(value):
    if not isinstance(value,str) or not value.strip():
        raise ValueError('Expected a nonempty string')
    return value


def validate(data):
    exact(data,['schema','batch_id','locations','assets'])
    if type(data['schema']) is not int or data['schema'] != 1:
        raise ValueError('Only inventory schema 1 is supported')
    text(data['batch_id'])
    if not isinstance(data['locations'],list) or not isinstance(data['assets'],list):
        raise ValueError('Locations and assets must be arrays')
    for location in data['locations']:
        exact(location,['code','name'])
        text(location['code']);text(location['name'])
    for asset in data['assets']:
        exact(asset,['asset_id','label','serial','location','condition','service'])
        for key in ['asset_id','label','serial','location']:text(asset[key])
        if asset['condition'] not in ['ready','repair','retired'] or not isinstance(asset['service'],list):
            raise ValueError('Invalid equipment condition or service history')
        for event in asset['service']:
            exact(event,['event_id','date','note'])
            text(event['event_id']);text(event['note'])
            if date.fromisoformat(text(event['date'])).isoformat() != event['date']:
                raise ValueError('Service dates must be ISO YYYY-MM-DD')


DDL = [
    'CREATE TABLE IF NOT EXISTS locations(code TEXT PRIMARY KEY, name TEXT NOT NULL)',
    '''CREATE TABLE IF NOT EXISTS assets(asset_id TEXT PRIMARY KEY, label TEXT NOT NULL,
       serial TEXT NOT NULL UNIQUE, location TEXT NOT NULL REFERENCES locations(code),
       condition TEXT NOT NULL CHECK(condition IN ('ready','repair','retired')))''',
    '''CREATE TABLE IF NOT EXISTS service_events(event_id TEXT PRIMARY KEY,
       asset_id TEXT NOT NULL REFERENCES assets(asset_id), date TEXT NOT NULL, note TEXT NOT NULL)''',
    '''CREATE TABLE IF NOT EXISTS import_batches(batch_id TEXT PRIMARY KEY,
       source_sha256 TEXT NOT NULL, result_json TEXT NOT NULL)''',
]


def migrate(data, database):
    validate(data)
    source_hash = hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    connection = sqlite3.connect(database,isolation_level=None,timeout=5)
    try:
        connection.execute('PRAGMA foreign_keys=ON')
        if connection.execute('PRAGMA foreign_keys').fetchone() != (1,):
            raise RuntimeError('SQLite foreign-key enforcement unavailable')
        connection.execute('BEGIN IMMEDIATE')
        for sql in DDL:connection.execute(sql)
        previous = connection.execute('SELECT source_sha256,result_json FROM import_batches WHERE batch_id=?',(data['batch_id'],)).fetchone()
        if previous:
            if previous[0] != source_hash:
                raise ValueError('Batch ID already exists with different content')
            connection.rollback()
            return dict(status='reused',**json.loads(previous[1]))
        for location in data['locations']:
            old = connection.execute('SELECT name FROM locations WHERE code=?',(location['code'],)).fetchone()
            if old and old[0] != location['name']:
                raise ValueError('Conflicting location: ' + location['code'])
            if not old:
                connection.execute('INSERT INTO locations VALUES (?,?)',(location['code'],location['name']))
        for asset in data['assets']:
            connection.execute('INSERT INTO assets VALUES (?,?,?,?,?)',tuple(asset[key] for key in ['asset_id','label','serial','location','condition']))
            for event in asset['service']:
                connection.execute('INSERT INTO service_events VALUES (?,?,?,?)',(event['event_id'],asset['asset_id'],event['date'],event['note']))
        result = dict(batch_id=data['batch_id'],source_sha256=source_hash,assets=len(data['assets']),
                      service_events=sum(len(a['service']) for a in data['assets']))
        connection.execute('INSERT INTO import_batches VALUES (?,?,?)',(data['batch_id'],source_hash,json.dumps(result,ensure_ascii=False)))
        connection.commit()
        return dict(status='applied',**result)
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path);p.add_argument('--database',required=True,type=Path)
    a=p.parse_args()
    try:
        result=migrate(json.loads(a.input.read_text()),a.database)
    except (OSError,ValueError,TypeError,sqlite3.Error) as exc:
        print(json.dumps(dict(status='rejected',error=str(exc)),ensure_ascii=False));return 2
    print(json.dumps(result,ensure_ascii=False));return 0


if __name__=='__main__':raise SystemExit(main())
