# Support desk

Run Python 3.10+:

```sh
python3 challenges/ticket-desk/app.py --database /tmp/support-desk.sqlite3 --port 8765
```

Open http://127.0.0.1:8765. This is a real local HTTP/SQLite application: create,
search and filter tickets, progress/reopen them, and read retained history.
Versions prevent an old page from overwriting newer updates. Validation preserves
the draft. The desktop queue becomes single-column cards at narrow widths.

The default bind address is loopback. This example has no production identity,
shared-service authorization or public-hosting SLA. Keep runtime databases outside
the immutable CLI installation. JSON API: GET/POST /api/tickets, PATCH
/api/tickets/ID with status and expected_version, GET /api/tickets/ID/history.

Frozen requirements, real HTTP restart/conflict checks, source snapshots and
browser evidence are under runs/R03. API evidence is one self-contained journey
with nine state checks; it is not nine independent users or a performance study.
