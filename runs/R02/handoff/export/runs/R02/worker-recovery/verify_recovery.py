#!/usr/bin/env python3
"""Capture SQLite snapshots and grade the frozen local recovery experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

TABLES = ("locations", "assets", "service_events", "import_batches")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def snapshot(database):
    with sqlite3.connect(database) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        tables = {
            table: [list(row) for row in connection.execute(
                "SELECT * FROM " + table + " ORDER BY 1").fetchall()]
            for table in TABLES
        }
    raw = Path(database).read_bytes()
    return dict(database_sha256=hashlib.sha256(raw).hexdigest(),
                integrity_check=integrity, tables=tables)


def parse_record_stdout(path):
    record = read_json(path)
    return record, json.loads(record["stdout"])


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("--database", required=True, type=Path)
    snap.add_argument("--output", required=True, type=Path)
    post = sub.add_parser("post-crash")
    post.add_argument("--database", required=True, type=Path)
    post.add_argument("--baseline", required=True, type=Path)
    post.add_argument("--crash-record", required=True, type=Path)
    post.add_argument("--output", required=True, type=Path)
    final = sub.add_parser("final")
    final.add_argument("--database", required=True, type=Path)
    final.add_argument("--baseline", required=True, type=Path)
    final.add_argument("--post-crash", required=True, type=Path)
    final.add_argument("--after-apply", required=True, type=Path)
    final.add_argument("--freeze", required=True, type=Path)
    final.add_argument("--input", required=True, type=Path)
    final.add_argument("--seed", required=True, type=Path)
    final.add_argument("--importer", required=True, type=Path)
    final.add_argument("--worker", required=True, type=Path)
    final.add_argument("--validator", required=True, type=Path)
    final.add_argument("--skill", required=True, type=Path)
    final.add_argument("--crash-record", required=True, type=Path)
    final.add_argument("--retry-record", required=True, type=Path)
    final.add_argument("--repeat-record", required=True, type=Path)
    final.add_argument("--successor-record", required=True, type=Path)
    final.add_argument("--successor-validation", required=True, type=Path)
    final.add_argument("--successor-freeze", required=True, type=Path)
    final.add_argument("--successor-package", required=True, type=Path)
    final.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.mode == "snapshot":
        data = snapshot(args.database)
        data.update(schema="forge-sqlite-snapshot/1", database=str(args.database))
        write_json(args.output, data)
        print(json.dumps(dict(database_sha256=data["database_sha256"],
                              integrity_check=data["integrity_check"],
                              row_counts={key: len(value) for key, value in data["tables"].items()}),
                         sort_keys=True))
        return 0

    baseline = read_json(args.baseline)
    if args.mode == "post-crash":
        crash, worker = parse_record_stdout(args.crash_record)
        actual = snapshot(args.database)
        worker_wrote_before_exit = (
            crash["state"] == "finished" and crash["exit_code"] == 73
            and worker["state"] == "worker_exiting"
            and worker["transaction_active"] is True
            and worker["uncommitted_mutations"] >= 5
        )
        unchanged = actual["tables"] == baseline["tables"]
        result = dict(schema="forge-recovery-post-crash/1", passed=(
            worker_wrote_before_exit and unchanged and actual["integrity_check"] == "ok"),
            worker_record=dict(exit_code=crash["exit_code"], pid=worker["pid"],
                               transaction_active=worker["transaction_active"],
                               uncommitted_mutations=worker["uncommitted_mutations"]),
            baseline_database_sha256=baseline["database_sha256"],
            after_crash_database_sha256=actual["database_sha256"],
            same_rows_as_committed_baseline=unchanged,
            integrity_check=actual["integrity_check"],
            actual_tables=actual["tables"])
        write_json(args.output, result)
        print(json.dumps({key: result[key] for key in ["passed", "worker_record",
                              "baseline_database_sha256", "after_crash_database_sha256",
                              "same_rows_as_committed_baseline", "integrity_check"]}, sort_keys=True))
        return 0 if result["passed"] else 1

    freeze = read_json(args.freeze)
    batch = read_json(args.input)
    crash, worker = parse_record_stdout(args.crash_record)
    retry, applied = parse_record_stdout(args.retry_record)
    repeat, reused = parse_record_stdout(args.repeat_record)
    successor_command, successor_output = parse_record_stdout(args.successor_record)
    successor_validation = read_json(args.successor_validation)
    successor_freeze = read_json(args.successor_freeze)
    post_crash = read_json(args.post_crash)
    after_apply = read_json(args.after_apply)
    actual = snapshot(args.database)
    input_sha = sha256(args.input)
    source_hash = hashlib.sha256(json.dumps(batch, ensure_ascii=False, sort_keys=True,
                                          separators=(",", ":")).encode("utf-8")).hexdigest()
    crash_ok = (crash["state"] == "finished" and crash["exit_code"] == 73
                and worker["transaction_active"] is True
                and worker["uncommitted_mutations"] >= 5)
    rollback_ok = (post_crash["passed"] is True
                   and post_crash["same_rows_as_committed_baseline"] is True
                   and post_crash["integrity_check"] == "ok")
    retry_ok = (retry["state"] == "finished" and retry["exit_code"] == 0
                and applied["status"] == "applied"
                and applied["batch_id"] == batch["batch_id"]
                and applied["source_sha256"] == source_hash)
    rows = actual["tables"]
    expected_assets = {asset["asset_id"] for asset in batch["assets"]}
    actual_assets = {row[0] for row in rows["assets"]}
    expected_events = {event["event_id"] for asset in batch["assets"] for event in asset["service"]}
    actual_events = {row[0] for row in rows["service_events"]}
    application_ok = (expected_assets.issubset(actual_assets)
                      and expected_events.issubset(actual_events)
                      and len(rows["import_batches"]) == 2
                      and actual["integrity_check"] == "ok")
    repeat_ok = (repeat["state"] == "finished" and repeat["exit_code"] == 0
                 and reused["status"] == "reused"
                 and reused["source_sha256"] == source_hash
                 and after_apply["tables"] == actual["tables"]
                 and after_apply["database_sha256"] == actual["database_sha256"])
    input_ok = input_sha == freeze["input"]["sha256"]
    all_ok = crash_ok and rollback_ok and retry_ok and application_ok and repeat_ok and input_ok
    successor_ok = (successor_command["state"] == "finished"
                    and successor_command["exit_code"] == 0
                    and successor_output["passed"] is True
                    and successor_output["validation_exit_code"] == 0
                    and successor_validation["state"] == "finished"
                    and successor_validation["exit_code"] == 0
                    and successor_freeze["task_id"] == "R02-02"
                    and successor_freeze["input"]["sha256"] == sha256(args.input.parent / "flow-brief.json")
                    and successor_freeze["acceptance_sha256"] == "6d3a95c27efccdc814e87b7846549e5d18d90116095eac9533883b46e88c5e53"
                    and Path(args.successor_package).is_file())
    checks = [
        dict(id="a1", status="pass" if crash_ok and rollback_ok else "fail",
             evidence=["runs/R02/worker-recovery/02-seed-command.json",
                       "runs/R02/worker-recovery/04-crash-command.json",
                       "runs/R02/worker-recovery/05-post-crash-command.json"]),
        dict(id="a2", status="pass" if retry_ok and application_ok and repeat_ok and input_ok else "fail",
             evidence=["runs/R02/worker-recovery/frozen-acceptance.json",
                       "runs/R02/materials/recovery-batch.json",
                       "runs/R02/worker-recovery/04-crash-command.json",
                       "runs/R02/worker-recovery/06-retry-original-command.json",
                       "runs/R02/worker-recovery/07-after-apply-command.json",
                       "runs/R02/worker-recovery/08-retry-identical-command.json"]),
        dict(id="a3", status="pass" if all_ok and successor_ok else "fail",
             evidence=["runs/R02/worker-recovery/frozen-acceptance.json",
                       "runs/R02/worker-recovery/01-freeze-check-command.json",
                       "runs/R02/flow/frozen-acceptance.json",
                       "runs/R02/flow/01-successor-first-step-command.json",
                       "runs/R02/flow/02-successor-start-command.json"]),
    ]
    source_hashes = {
        "input": input_sha,
        "seed": sha256(args.seed),
        "importer": sha256(args.importer),
        "crash_worker": sha256(args.worker),
        "validator": sha256(args.validator),
        "route_skill": sha256(args.skill),
        "frozen_acceptance": sha256(args.freeze),
        "successor_freeze": sha256(args.successor_freeze),
        "successor_package": sha256(args.successor_package),
        "successor_validation_record": sha256(args.successor_validation),
        "successor_start_record": sha256(args.successor_record),
    }
    result = dict(
        schema="forge-continuation-result/1", task_id="R02-01", attempt_id="R02-01-1",
        requirements_hash=freeze["acceptance_sha256"], criteria=checks,
        effect=dict(
            target="Atomic recovery of the supplied JSON batch after a command worker exits with an open SQLite transaction.",
            hypothesis=freeze["effect_hypothesis"],
            baseline=dict(database_sha256=baseline["database_sha256"],
                          row_counts={name: len(value) for name, value in baseline["tables"].items()}),
            conditions=dict(python=sys.version, sqlite=sqlite3.sqlite_version,
                            crash_exit_code=crash["exit_code"],
                            staged_uncommitted_mutations=worker["uncommitted_mutations"],
                            input_sha256=input_sha, importer="repository CLI"),
            observations=dict(crash_and_rollback=crash_ok and rollback_ok,
                              unchanged_baseline_rows=post_crash["same_rows_as_committed_baseline"],
                              retry_applied=retry_ok, identical_retry_reused=repeat_ok,
                              successor_first_step_command_passed=successor_ok,
                              final_integrity=actual["integrity_check"],
                              final_database_sha256=actual["database_sha256"],
                              correction_rounds=0, user_or_parent_interventions=0),
            limits=["One controlled local SQLite database and one supplied batch; no power-loss, multi-process contention, provider, production, or cross-platform guarantee.",
                    "The worker's deliberate exit code 73 is an actual command-process termination, not a provider or native-model failure."],
            metrics=dict(batch_assets=len(batch["assets"]),
                         batch_service_events=sum(len(asset["service"]) for asset in batch["assets"]),
                         retry_count=1, correction_rounds=0,
                         model_active_time_seconds=None, provider_tokens=None, provider_cost=None,
                         user_interventions=0, parent_interventions=0)),
        source_hashes=source_hashes,
        next_action="Start R02-02 (reusable book-renewal agent flow) from its frozen original brief; implement one policy case first.")
    write_json(args.output, result)
    print(json.dumps(dict(passed=all_ok and successor_ok, checks=[dict(id=c["id"], status=c["status"]) for c in checks],
                          final_database_sha256=actual["database_sha256"], source_hashes=source_hashes),
                     ensure_ascii=False, sort_keys=True))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
