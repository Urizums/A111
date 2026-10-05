#!/usr/bin/env python3
"""Local support desk: real HTTP, SQLite persistence and optimistic updates."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
from urllib.parse import parse_qs, urlsplit

STATIC = Path(__file__).parent
TRANSITIONS = {'open': 'in_progress', 'in_progress': 'resolved', 'resolved': 'open'}


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def database(path):
    conn = sqlite3.connect(path, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def initialize(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with database(path) as c:
        c.executescript('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
                priority TEXT NOT NULL CHECK(priority IN ('low','normal','urgent')),
                status TEXT NOT NULL CHECK(status IN ('open','in_progress','resolved')),
                version INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL REFERENCES tickets(id),
                from_status TEXT, to_status TEXT NOT NULL, version INTEGER NOT NULL,
                at TEXT NOT NULL
            );
        ''')


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, body, content_type='application/json; charset=utf-8'):
        raw = json.dumps(body, ensure_ascii=False).encode() if not isinstance(body, bytes) else body
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'")
        self.end_headers(); self.wfile.write(raw)

    def body(self):
        if self.headers.get_content_type() != 'application/json':
            raise ValueError('请使用 JSON 请求。')
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise ValueError('请求长度无效。')
        if not 0 < size <= 32768:
            raise ValueError('请求内容为空或过长。')
        data = json.loads(self.rfile.read(size))
        if not isinstance(data, dict):
            raise ValueError('请求应为对象。')
        return data

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path in {'/', '/app.js', '/style.css'}:
            name = 'index.html' if url.path == '/' else url.path[1:]
            content_type = {'index.html':'text/html', 'app.js':'text/javascript', 'style.css':'text/css'}[name]
            return self.reply(200, (STATIC/name).read_bytes(), content_type+'; charset=utf-8')
        with database(self.server.db) as c:
            if url.path == '/api/tickets':
                query = parse_qs(url.query); status = query.get('status', [''])[0]; term = query.get('q', [''])[0].strip()
                if status and status not in TRANSITIONS:
                    return self.reply(400, dict(error='未知状态。'))
                rows = c.execute('SELECT * FROM tickets ORDER BY id DESC').fetchall()
                counts = {k: sum(r['status'] == k for r in rows) for k in TRANSITIONS}
                tickets = [dict(r) for r in rows if (not status or r['status'] == status)
                           and (not term or term.casefold() in (r['title']+' '+r['description']).casefold())]
                return self.reply(200, dict(tickets=tickets, counts=counts))
            parts = url.path.strip('/').split('/')
            if len(parts) == 4 and parts[:2] == ['api','tickets'] and parts[2].isdigit() and parts[3] == 'history':
                id = int(parts[2])
                if not c.execute('SELECT id FROM tickets WHERE id=?', (id,)).fetchone():
                    return self.reply(404, dict(error='工单不存在。'))
                return self.reply(200, dict(history=[dict(r) for r in c.execute('SELECT * FROM history WHERE ticket_id=? ORDER BY id', (id,))]))
        self.reply(404, dict(error='页面不存在。'))

    def do_POST(self):
        if urlsplit(self.path).path != '/api/tickets':
            return self.reply(404, dict(error='页面不存在。'))
        try:
            data = self.body()
            if set(data) != {'title', 'description', 'priority'}:
                raise ValueError('请填写标题、说明和优先级。')
            for field, maximum, label in [('title',120,'标题'), ('description',4000,'说明')]:
                if not isinstance(data[field], str) or not data[field].strip() or len(data[field].strip()) > maximum:
                    raise ValueError(label+'不能为空，且长度不能超过 '+str(maximum)+' 字。')
            if data['priority'] not in {'low','normal','urgent'}:
                raise ValueError('优先级无效。')
            at = now()
            with database(self.server.db) as c:
                row = c.execute('INSERT INTO tickets(title,description,priority,status,version,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',
                                (data['title'].strip(), data['description'].strip(), data['priority'], 'open', 1, at, at))
                id = row.lastrowid
                c.execute('INSERT INTO history(ticket_id,from_status,to_status,version,at) VALUES(?,?,?,?,?)', (id,None,'open',1,at))
                ticket = dict(c.execute('SELECT * FROM tickets WHERE id=?',(id,)).fetchone())
            self.reply(201, dict(ticket=ticket))
        except (ValueError, TypeError, UnicodeError) as exc:
            self.reply(400, dict(error=str(exc)))

    def do_PATCH(self):
        parts = urlsplit(self.path).path.strip('/').split('/')
        if len(parts) != 3 or parts[:2] != ['api','tickets'] or not parts[2].isdigit():
            return self.reply(404, dict(error='页面不存在。'))
        try:
            data = self.body()
            if set(data) != {'status','expected_version'} or type(data['expected_version']) is not int or data['expected_version'] < 1:
                raise ValueError('更新需要有效版本和状态。')
            with database(self.server.db) as c:
                c.execute('BEGIN IMMEDIATE')
                row = c.execute('SELECT * FROM tickets WHERE id=?',(int(parts[2]),)).fetchone()
                if not row:
                    return self.reply(404,dict(error='工单不存在。'))
                if data['expected_version'] != row['version']:
                    return self.reply(409,dict(error='工单已被其他操作更新。已载入最新状态，请确认后重试。',ticket=dict(row)))
                if data['status'] != TRANSITIONS[row['status']]:
                    raise ValueError('当前状态不能执行此转换。')
                at=now(); version=row['version']+1
                c.execute('UPDATE tickets SET status=?,version=?,updated_at=? WHERE id=?',(data['status'],version,at,row['id']))
                c.execute('INSERT INTO history(ticket_id,from_status,to_status,version,at) VALUES(?,?,?,?,?)',(row['id'],row['status'],data['status'],version,at))
                ticket=dict(c.execute('SELECT * FROM tickets WHERE id=?',(row['id'],)).fetchone())
            self.reply(200,dict(ticket=ticket))
        except (ValueError, TypeError, UnicodeError) as exc:
            self.reply(400,dict(error=str(exc)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database',type=Path,required=True);p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8765)
    a=p.parse_args();initialize(a.database)
    server=ThreadingHTTPServer((a.host,a.port),Handler);server.db=a.database
    print(json.dumps(dict(listening=server.server_address,database=str(a.database))),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
