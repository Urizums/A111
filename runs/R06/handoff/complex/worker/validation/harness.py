#!/usr/bin/env python3
"""Exercise the supplied fictional local app and retain each process result."""
import argparse
import base64
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

EXPECTED = [
    ("approved", "sample_rule_match"),
    ("manual", "category_review"),
    ("manual", "amount_unknown"),
    ("manual", "risk_review"),
    ("manual", "self_review"),
    ("manual", "evidence_missing"),
    ("manual", "amount_review"),
]


def utc():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate JSON key")
            out[key] = value
        return out
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs)


def append_jsonl(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def child(argv, phase, records, cwd):
    started = utc()
    mono_start = time.monotonic()
    result = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    mono_end = time.monotonic()
    record = {
        "phase": phase,
        "argv": list(argv),
        "cwd": str(cwd),
        "started_at": started,
        "ended_at": utc(),
        "monotonic_start": mono_start,
        "monotonic_end": mono_end,
        "duration_seconds": mono_end - mono_start,
        "exit_code": result.returncode,
        "stdout_base64": base64.b64encode(result.stdout).decode("ascii"),
        "stderr_base64": base64.b64encode(result.stderr).decode("ascii"),
        "stdout": result.stdout.decode("utf-8", errors="replace"),
        "stderr": result.stderr.decode("utf-8", errors="replace"),
    }
    append_jsonl(records, record)
    return result.returncode, result.stdout, result.stderr, record


def app_cmd(args, db, subcommand, *tail):
    return [sys.executable, str(args.app), "--database", str(db), subcommand, *map(str, tail)]


def parse_stdout(data, description):
    try:
        return json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"{description}: stdout is not JSON: {exc}") from exc


def inspect(args, db, ticket, records, cwd, phase):
    code, out, err, _ = child(app_cmd(args, db, "inspect", ticket), phase, records, cwd)
    if code != 0:
        raise RuntimeError(f"{phase}: inspect failed ({code}): {err.decode(errors='replace')}")
    return parse_stdout(out, phase)


def verify_response(obj, request, expected, policy_version):
    decision, reason = expected
    for key, value in {
        "ticket_id": request["ticket_id"],
        "decision": decision,
        "reason": reason,
        "policy_version": policy_version,
        "request_id": request["request_id"],
        "local_demo_only": True,
    }.items():
        if obj.get(key) != value:
            raise RuntimeError(f"response mismatch for {request['request_id']} field {key}: {obj.get(key)!r} != {value!r}")
    if type(obj.get("version")) is not int or obj["version"] < 1:
        raise RuntimeError(f"invalid response version for {request['request_id']}")
    if type(obj.get("reused")) is not bool:
        raise RuntimeError(f"missing reused flag for {request['request_id']}")


def app_decide(args, db, request_path, records, cwd, phase, crash=False):
    tail = [str(request_path), "--policy", str(args.policy)]
    if crash:
        tail.append("--simulate-crash-before-commit")
    return child(app_cmd(args, db, "decide", *tail), phase, records, cwd)


def get_attempt(args):
    ledger = load(args.journal / "ledger.json")
    if ledger.get("phase") != "running" or not ledger.get("attempts"):
        raise RuntimeError("bounded-run journal does not show the active attempt")
    attempt = ledger["attempts"][-1]
    return attempt["id"], attempt["repair_count"]


def ticket_audit_count(db, ticket):
    with sqlite3.connect(db) as conn:
        row = conn.execute("SELECT count(*) FROM audit WHERE ticket_id=?", (ticket,)).fetchone()
        return row[0]


def run_recovery(args, request_path, records, cwd, prior_attempt_dirs):
    db = args.out / "databases" / "recovery.sqlite3"
    db.parent.mkdir(parents=True, exist_ok=True)
    request = load(request_path)
    current = inspect(args, db, request["ticket_id"], records, cwd, "recovery_initial_inspect")
    if current["ticket"] is None:
        code, out, err, crash_record = app_decide(args, db, request_path, records, cwd, "recovery_controlled_crash", crash=True)
        if code != 75:
            raise RuntimeError(f"controlled crash expected exit 75, observed {code}: {err.decode(errors='replace')}")
        after_crash = inspect(args, db, request["ticket_id"], records, cwd, "recovery_inspect_after_crash")
        if after_crash["ticket"] is not None or after_crash["audit"]:
            raise RuntimeError("pre-commit crash left ticket or audit state")
        code, out, err, retry_record = app_decide(args, db, request_path, records, cwd, "recovery_same_request_retry")
        if code != 0:
            raise RuntimeError(f"same-request recovery retry failed ({code}): {err.decode(errors='replace')}")
        response = parse_stdout(out, "recovery_same_request_retry")
        verify_response(response, request, EXPECTED[0], args.policy_version)
        if response["reused"] is not False:
            raise RuntimeError("recovery retry unexpectedly reused a prior commit")
        return {"database": str(db), "crash_exit_code": 75, "rollback_ticket": None, "rollback_audit_count": 0, "retry": response, "crash_command": crash_record, "retry_command": retry_record}
    # A prior attempt may have completed the recovery sequence before a later check failed.
    # Preserve and re-read that evidence; do not reset the database or pretend to re-crash it.
    prior_crash = []
    for directory in prior_attempt_dirs:
        log = directory / "processes.jsonl"
        if not log.exists():
            continue
        for line in log.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("phase") == "recovery_controlled_crash" and row.get("exit_code") == 75:
                prior_crash.append(row)
    if not prior_crash:
        raise RuntimeError("recovery database exists but retained controlled-crash evidence is missing")
    if current["ticket"].get("version") != 1 or len(current["audit"]) != 1:
        raise RuntimeError("recovered request does not have exactly one committed audit row")
    code, out, err, retry_record = app_decide(args, db, request_path, records, cwd, "recovery_same_request_replay")
    if code != 0:
        raise RuntimeError(f"recovery replay failed ({code}): {err.decode(errors='replace')}")
    response = parse_stdout(out, "recovery_same_request_replay")
    verify_response(response, request, EXPECTED[0], args.policy_version)
    if response["reused"] is not True:
        raise RuntimeError("recovery replay did not reuse the prior committed response")
    return {"database": str(db), "prior_controlled_crash_exit_code": 75, "ticket": current["ticket"], "audit_count": len(current["audit"]), "replay": response, "prior_crash_records": len(prior_crash), "replay_command": retry_record}


def run_concurrency(args, attempt_dir, records, cwd, prior_attempt_dirs):
    db = args.out / "databases" / "concurrency.sqlite3"
    db.parent.mkdir(parents=True, exist_ok=True)
    ticket = "CASE-CONCURRENCY"
    current = inspect(args, db, ticket, records, cwd, "concurrency_initial_inspect")
    commands = []
    if current["ticket"] is None:
        gate = attempt_dir / "concurrency.gate"
        pids = []
        procs = []
        release_parent = time.monotonic()
        marker_paths = [attempt_dir / "concurrency-a.started.json", attempt_dir / "concurrency-b.started.json"]
        req_paths = [args.probes / "concurrency-a.json", args.probes / "concurrency-b.json"]
        app_commands = [app_cmd(args, db, "decide", str(path), "--policy", str(args.policy)) for path in req_paths]
        launch_rows = []
        for index, app_argv in enumerate(app_commands):
            gate_argv = [sys.executable, str(args.gate), str(gate), str(marker_paths[index]), *app_argv]
            started = utc()
            mono = time.monotonic()
            proc = subprocess.Popen(gate_argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            procs.append(proc)
            pids.append(proc.pid)
            launch_rows.append({"gate_argv": gate_argv, "actual_app_argv": app_argv, "pid": proc.pid, "launched_at": started, "launched_monotonic": mono})
        both_waiting = all(proc.poll() is None for proc in procs)
        if not both_waiting:
            raise RuntimeError("one concurrency process exited before common gate release")
        gate_release_at = utc()
        gate_release_monotonic = time.monotonic()
        with gate.open("x", encoding="utf-8") as stream:
            stream.write(gate_release_at + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        for index, proc in enumerate(procs):
            out, err = proc.communicate(timeout=15)
            code = proc.returncode
            marker = load(marker_paths[index]) if marker_paths[index].exists() else None
            row = {
                "phase": "concurrency_decide",
                **launch_rows[index],
                "gate_release_at": gate_release_at,
                "gate_release_monotonic": gate_release_monotonic,
                "both_waiting_before_release": both_waiting,
                "started_marker": marker,
                "ended_at": utc(),
                "exit_code": code,
                "stdout_base64": base64.b64encode(out).decode("ascii"),
                "stderr_base64": base64.b64encode(err).decode("ascii"),
                "stdout": out.decode("utf-8", errors="replace"),
                "stderr": err.decode("utf-8", errors="replace"),
            }
            append_jsonl(records, row)
            commands.append(row)
        codes = sorted(row["exit_code"] for row in commands)
        if codes != [0, 3]:
            raise RuntimeError(f"same-version concurrency expected one commit/one conflict, got exits {codes}")
        outputs = [parse_stdout(row["stdout"].encode(), "concurrency process") if row["exit_code"] == 0 else json.loads(row["stderr"]) for row in commands]
        committed = [row for row in outputs if row.get("decision") == "approved"]
        conflicted = [row for row in outputs if row.get("conflict") is True]
        if len(committed) != 1 or len(conflicted) != 1:
            raise RuntimeError("concurrency results are not one approved commit and one version conflict")
    else:
        # Initial concurrent results must remain in an earlier attempt log; retry is not a new concurrency proof.
        historical = []
        for directory in prior_attempt_dirs:
            log = directory / "processes.jsonl"
            if log.exists():
                historical.extend(json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip())
        commands = [row for row in historical if row.get("phase") == "concurrency_decide"]
        if len(commands) < 2 or sorted(row.get("exit_code") for row in commands[-2:]) != [0, 3]:
            raise RuntimeError("concurrency database exists but retained one-commit/one-conflict evidence is missing")
    final = inspect(args, db, ticket, records, cwd, "concurrency_final_inspect")
    if final["ticket"] is None or final["ticket"]["version"] != 1 or len(final["audit"]) != 1:
        raise RuntimeError("concurrency did not leave exactly one version-1 ticket and audit row")
    return {"database": str(db), "ticket": ticket, "ticket_state": final["ticket"], "audit": final["audit"], "process_results": commands[-2:]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--policy-version", required=True)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--probes", type=Path, required=True)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--manual-review", type=Path, required=True)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    args = parser.parse_args()
    attempt_number, repair_count = get_attempt(args)
    attempt_dir = args.out / "attempts" / f"attempt-{attempt_number}-repair-{repair_count}"
    attempt_dir.mkdir(parents=True, exist_ok=False)
    records = attempt_dir / "processes.jsonl"
    cwd = args.out
    prior_attempt_dirs = sorted((args.out / "attempts").glob("attempt-*-repair-*"))
    prior_attempt_dirs = [path for path in prior_attempt_dirs if path != attempt_dir]

    policy = load(args.policy)
    requests = sorted(args.requests.glob("request-*.json"), key=lambda p: int(p.stem.split("-")[-1]))
    if len(requests) != 7:
        raise RuntimeError(f"expected seven frozen original requests, got {len(requests)}")
    if policy["version"] != args.policy_version:
        raise RuntimeError("policy version input changed")

    # The recovery experiment uses the exact first original request bytes on an isolated local DB.
    recovery = run_recovery(args, requests[0], records, cwd, prior_attempt_dirs)

    # Apply the seven supplied requests in source order through the actual local CLI.
    db = args.out / "databases" / "original-batch.sqlite3"
    db.parent.mkdir(parents=True, exist_ok=True)
    outcomes = []
    for index, request_path in enumerate(requests):
        request = load(request_path)
        if request != load(requests[index]):
            raise RuntimeError("original request order/input drift")
        code, stdout, stderr, command = app_decide(args, db, request_path, records, cwd, f"batch_decide_{index + 1}")
        if code != 0:
            raise RuntimeError(f"batch request {request['request_id']} failed ({code}): {stderr.decode(errors='replace')}")
        result = parse_stdout(stdout, f"batch request {request['request_id']}")
        verify_response(result, request, EXPECTED[index], policy["version"])
        inspection = inspect(args, db, request["ticket_id"], records, cwd, f"batch_inspect_{index + 1}")
        if inspection["ticket"] is None or inspection["ticket"]["version"] != 1 or len(inspection["audit"]) != 1:
            raise RuntimeError(f"audit/version invariant failed for {request['ticket_id']}")
        audit = inspection["audit"][0]
        if (audit["decision"], audit["reason"], audit["request_id"], audit["policy_version"], audit["previous_version"], audit["new_version"]) != (EXPECTED[index][0], EXPECTED[index][1], request["request_id"], policy["version"], 0, 1):
            raise RuntimeError(f"audit row mismatch for {request['ticket_id']}")
        outcomes.append({"request": request, "decision": result, "inspection": inspection})

    # Identical retry reuses the first response and cannot append an audit row.
    before_idem = inspect(args, db, "CASE-1", records, cwd, "idempotency_before_retry")
    code, stdout, stderr, idem_record = app_decide(args, db, requests[0], records, cwd, "idempotency_identical_retry")
    if code != 0:
        raise RuntimeError(f"identical retry failed ({code}): {stderr.decode(errors='replace')}")
    replay = parse_stdout(stdout, "identical retry")
    verify_response(replay, load(requests[0]), EXPECTED[0], policy["version"])
    if replay["reused"] is not True:
        raise RuntimeError("identical retry did not reuse response")
    after_idem = inspect(args, db, "CASE-1", records, cwd, "idempotency_after_retry")
    if before_idem != after_idem:
        raise RuntimeError("identical retry changed ticket/audit state")

    # Both forms of request identity/content collision must fail closed without writes.
    conflict_results = []
    for name in ("conflict-same-key.json", "conflict-same-request-id.json"):
        path = args.probes / name
        code, stdout, stderr, record = app_decide(args, db, path, records, cwd, f"conflict_{name}")
        if code != 3:
            raise RuntimeError(f"{name} expected conflict exit 3, observed {code}")
        error = parse_stdout(stderr, f"{name} stderr")
        if error.get("conflict") is not True:
            raise RuntimeError(f"{name} did not return conflict evidence")
        conflict_results.append({"probe": name, "exit_code": code, "error": error})
    after_conflicts = inspect(args, db, "CASE-1", records, cwd, "conflict_after_state")
    if after_conflicts != after_idem:
        raise RuntimeError("identity/content conflicts changed original state")

    # No ticket appears in more than one audit row in the supplied batch.
    with sqlite3.connect(db) as conn:
        aggregate = conn.execute("SELECT count(*), count(DISTINCT ticket_id) FROM audit").fetchone()
    if aggregate != (7, 7):
        raise RuntimeError(f"batch should retain seven unique audit rows, got {aggregate}")

    concurrency = run_concurrency(args, attempt_dir, records, cwd, prior_attempt_dirs)

    # Run the real local successor process against actual retained manual audit rows.
    successor_path = args.out / "manual-review-task.json"
    code, stdout, stderr, successor_command = child(
        [sys.executable, str(args.manual_review), "--database", str(db), "--rules", str(args.rules), "--out", str(successor_path)],
        "successor_manual_review_start", records, cwd
    )
    if code != 0:
        raise RuntimeError(f"successor task did not start ({code}): {stderr.decode(errors='replace')}")
    successor_result = parse_stdout(stdout, "successor task start")
    successor = load(successor_path)
    manual_outcomes = [row for row in outcomes if row["decision"]["decision"] == "manual"]
    expected_tickets = [row["request"]["ticket_id"] for row in manual_outcomes]
    actual_tickets = [row["ticket_id"] for row in successor["items"]]
    if successor.get("status") != "started" or actual_tickets != expected_tickets:
        raise RuntimeError("successor task is not started on exactly the source-ordered manual entries")
    if successor.get("fictional_local_only") is not True or successor.get("notifications_sent") is not False or successor.get("external_effects") is not False or successor.get("real_assignment") is not None:
        raise RuntimeError("successor task exceeded local-record-only scope")
    required_material_fields = {"ticket_id", "reason", "needed_material"}
    if any(not required_material_fields.issubset(item) for item in successor["missing_materials"]):
        raise RuntimeError("successor missing-material record lacks a required field")

    summary = {
        "schema": "local-demo-approval-validation/1",
        "scope": "fictional local example only; no real authority or external effects",
        "policy_version": policy["version"],
        "source_order": [row["request"]["ticket_id"] for row in outcomes],
        "outcomes": outcomes,
        "idempotency": {"reused": replay["reused"], "audit_state_unchanged": True, "before": before_idem, "after": after_idem},
        "identity_conflicts": conflict_results,
        "batch_audit_aggregate": {"audit_rows": aggregate[0], "distinct_tickets": aggregate[1]},
        "commit_failure_recovery": recovery,
        "same_version_concurrency": concurrency,
        "successor_task": {"path": str(successor_path), "start_result": successor_result, "record": successor},
        "harness_attempt": {"attempt": attempt_number, "repairs_used": repair_count},
    }
    summary_path = attempt_dir / "summary.json"
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({
        "summary_path": str(summary_path),
        "batch_count": len(outcomes),
        "manual_count": len(manual_outcomes),
        "idempotency_reused": replay["reused"],
        "conflict_probes": len(conflict_results),
        "concurrency_exit_codes": sorted(row["exit_code"] for row in concurrency["process_results"]),
        "successor_task_id": successor["task_id"],
        "successor_status": successor["status"],
        "repairs_used": repair_count,
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"harness_error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise
