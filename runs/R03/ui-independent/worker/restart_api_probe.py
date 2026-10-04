#!/usr/bin/env python3
"""One-shot post-restart SQLite and two-client version-conflict evidence probe."""
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:40053"


def send(client, path, method="GET", payload=None):
    raw = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if raw is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=raw, headers=headers, method=method)
    try:
        with client.open(request, timeout=5) as response:
            return {"status": response.status, "body": json.loads(response.read())}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "body": json.loads(exc.read())}


client_a = urllib.request.build_opener()
client_b = urllib.request.build_opener()
initial = send(client_a, "/api/tickets")
ticket = next(row for row in initial["body"]["tickets"] if row["id"] == 1)
stale = send(client_b, "/api/tickets/1", "PATCH", {"status": "resolved", "expected_version": 1})
after_stale = send(client_a, "/api/tickets")
after_stale_ticket = next(row for row in after_stale["body"]["tickets"] if row["id"] == 1)
resolve = send(client_a, "/api/tickets/1", "PATCH", {"status": "resolved", "expected_version": 2})
reopen = send(client_a, "/api/tickets/1", "PATCH", {"status": "open", "expected_version": 3})
invalid = send(client_a, "/api/tickets/1", "PATCH", {"status": "resolved", "expected_version": 4})
final = send(client_a, "/api/tickets")
final_ticket = next(row for row in final["body"]["tickets"] if row["id"] == 1)
history = send(client_a, "/api/tickets/1/history")
history_rows = history["body"]["history"]
result = {
    "server_after_restart": BASE,
    "database": str(ROOT / "tickets-final.sqlite3"),
    "initial_persisted_state": {"status": ticket["status"], "version": ticket["version"]},
    "clients": {"client_a": "urllib opener A; reads and valid/invalid updates", "client_b": "separate urllib opener B; stale update"},
    "stale_update": stale,
    "state_after_stale": {"status": after_stale_ticket["status"], "version": after_stale_ticket["version"]},
    "valid_transitions": {"resolve": resolve, "reopen": reopen},
    "invalid_transition": invalid,
    "final_state": {"status": final_ticket["status"], "version": final_ticket["version"]},
    "history": history_rows,
    "checks": {
        "persisted_across_restart": ticket["status"] == "in_progress" and ticket["version"] == 2,
        "stale_conflict_without_overwrite": stale["status"] == 409 and after_stale_ticket["status"] == "in_progress" and after_stale_ticket["version"] == 2,
        "resolve_then_reopen": resolve["status"] == 200 and reopen["status"] == 200 and final_ticket["status"] == "open" and final_ticket["version"] == 4,
        "invalid_transition_rejected_without_overwrite": invalid["status"] == 400 and final_ticket["status"] == "open" and final_ticket["version"] == 4,
        "history_retained": len(history_rows) == 4 and [row["to_status"] for row in history_rows] == ["open", "in_progress", "resolved", "open"],
    },
}
result["all_checks_passed"] = all(result["checks"].values())
(ROOT / "restart-api-probe.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
