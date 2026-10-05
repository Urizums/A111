#!/usr/bin/env python3
"""Fill the worker reply from retained local evidence without grading preflight."""
import hashlib
import json
import sys
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError(f"not a regular artifact: {path}")
    return {"path": str(path), "sha256": sha(path)}


def main():
    if len(sys.argv) != 5:
        raise SystemExit("usage: finalize_reply.py REQUEST DRAFT SUMMARY REPLY")
    request_path, draft_path, summary_path, reply_path = map(Path, sys.argv[1:])
    envelope = load(request_path)
    request = envelope["request"]
    draft = load(draft_path)
    summary = load(summary_path)
    task_path = Path(summary["successor_task"]["path"])
    task = load(task_path)
    ledger_path = request_path.parent.parent / "worker" / "validation" / "journal" / "ledger.json"
    ledger = load(ledger_path)
    attempt_path = ledger_path.parent / "attempt-1.json"
    attempt = load(attempt_path)

    outcomes = []
    for row in summary["outcomes"]:
        inspection = row["inspection"]
        outcomes.append({
            "ticket_id": row["request"]["ticket_id"],
            "request_id": row["request"]["request_id"],
            "decision": row["decision"]["decision"],
            "reason": row["decision"]["reason"],
            "policy_version": row["decision"]["policy_version"],
            "version": row["decision"]["version"],
            "local_demo_only": row["decision"]["local_demo_only"],
            "audit_rows": inspection["audit"],
        })

    concurrency = summary["same_version_concurrency"]
    concurrency_processes = concurrency["process_results"]
    crash = summary["commit_failure_recovery"]
    recovery_record = {
        "database": crash["database"],
        "controlled_crash_exit_code": crash.get("crash_exit_code", crash.get("prior_controlled_crash_exit_code")),
        "rollback_ticket": crash.get("rollback_ticket"),
        "rollback_audit_count": crash.get("rollback_audit_count"),
        "retry_or_replay": crash.get("retry", crash.get("replay")),
        "retained_crash_records": crash.get("prior_crash_records", 1),
    }
    if recovery_record["controlled_crash_exit_code"] != 75:
        raise ValueError("retained recovery evidence lacks expected exit 75")

    artifact_paths = [Path(item["path"]) for item in draft["artifacts"]]
    task_root = request_path.parent.parent / "worker"
    extra = [
        task_root / "reply.draft.json",
        task_root / "reply.draft-v2.json",
        task_root / "logs/commands/write-reply-draft.json",
        task_root / "logs/commands/write-reply-draft-v2.json",
        task_root / "logs/commands/worker-work-begin.json",
        task_root / "logs/commands/worker-work-end.json",
        task_root / "logs/commands/worker-reply-begin.json",
        task_root / "events/40771889682877_d89d800caf68407ba3b0e8db9cf1888b.json",
        task_root / "events/40931112665843_ff9eebd48acf45518dfd58b70b3b6eac.json",
        task_root / "events/40937104028542_a1cd7ca275e74468bd836cdc26c9b8b1.json",
    ]
    refs = []
    for path in [*artifact_paths, *extra]:
        ref_value = ref(path)
        if ref_value not in refs:
            refs.append(ref_value)

    reply = {
        "schema_version": "forge-host-reply/1",
        "job_id": request["job_id"],
        "attempt_id": request["attempt_id"],
        "request_hash": envelope["request_hash"],
        "outcome": "done",
        "result": {
            "delivery_type": "scoped_task",
            "status": "completed_with_recording_limitation",
            "policy": {
                "path": "/workspace/A111/runs/R06/approval/policy.json",
                "version": summary["policy_version"],
                "binding": "fictional_local_only; no real approval authority",
            },
            "original_batch": {
                "count": len(outcomes),
                "outcomes": outcomes,
                "audit_rows": summary["batch_audit_aggregate"]["audit_rows"],
                "distinct_tickets": summary["batch_audit_aggregate"]["distinct_tickets"],
            },
            "idempotency_and_conflicts": {
                "identical_retry_reused": summary["idempotency"]["reused"],
                "audit_state_unchanged": summary["idempotency"]["audit_state_unchanged"],
                "changed_content_or_identity_conflicts": summary["identity_conflicts"],
            },
            "precommit_crash_recovery": recovery_record,
            "same_version_concurrency": {
                "ticket_id": concurrency["ticket"],
                "two_processes_launched_from_expected_version_zero": len(concurrency_processes) == 2,
                "process_ids": [row.get("pid") for row in concurrency_processes],
                "exit_codes": [row["exit_code"] for row in concurrency_processes],
                "one_commit_one_conflict": sorted(row["exit_code"] for row in concurrency_processes) == [0, 3],
                "final_ticket": concurrency["ticket_state"],
                "final_audit": concurrency["audit"],
            },
            "successor_manual_review_task": {
                "path": str(task_path.resolve()),
                "sha256": sha(task_path),
                "task_id": task["task_id"],
                "status": task["status"],
                "entry_count": len(task["items"]),
                "missing_materials": task["missing_materials"],
                "notifications_sent": task["notifications_sent"],
                "external_effects": task["external_effects"],
                "real_assignment": task["real_assignment"],
            },
            "validation": {
                "mechanism": "C5 bounded_run.py with captured actual local subprocesses",
                "journal_path": str(ledger_path.resolve()),
                "journal_sha256": sha(ledger_path),
                "attempt_path": str(attempt_path.resolve()),
                "attempt_sha256": sha(attempt_path),
                "phase": ledger["phase"],
                "attempts": len(ledger["attempts"]),
                "failed_bounded_attempts": sum(item.get("exit_code") != 0 for item in ledger["attempts"]),
                "repairs_used": len(ledger["repairs"]),
                "repair_limit": ledger["limit"],
                "pre_freeze_correction": "One predicate in the new local harness was corrected during source review before bounded_run initialization; no frozen run failed and no candidate repair was recorded.",
                "controlled_crash": "The expected exit 75 is preserved as an inner application process result in processes.jsonl, not hidden as a failed bounded-run attempt.",
            },
            "delegation": {
                "delegated_workers": [],
                "reason": "The bound request allows one active worker on this checkpoint; this worker performed the source review and local process checks in one context.",
                "independence": "No separate peer review is claimed.",
            },
            "recording": {
                "raw_business_process_commands_and_results": str((task_root / "outputs/attempts/attempt-1-repair-0/processes.jsonl").resolve()),
                "captured_run_and_status_records": [str((task_root / "logs/commands/validation-attempt-1.json").resolve()), str((task_root / "logs/commands/bounded-status.json").resolve())],
                "first_incomplete_draft": {"path": str((task_root / "reply.draft.json").resolve()), "sha256": sha(task_root / "reply.draft.json"), "status": "preserved_superseded; its review artifact hash predates the recording-limit note"},
                "current_incomplete_draft": {"path": str(draft_path.resolve()), "sha256": sha(draft_path), "status": "preserved; identity and hashes scaffolded, outcome and result still null"},
                "preflight_record_path": str((task_root / "logs/protocol/preflight-final.json").resolve()),
                "recording_conformance": "partial",
                "recording_limit": "Initial source/material/app reads and CLI-help commands preceded capture.py logging, so the C2 first-command boundary and complete bootstrap command log cannot be reconstructed. The bounded business run, successor start, drafts, and final host preflight are captured.",
            },
            "limits": {
                "network_used": False,
                "notifications_sent": False,
                "external_effects": False,
                "real_approval_authority": False,
                "host_preflight_semantic_acceptance": "not_evaluated",
                "tokens": None,
                "cost": None,
                "model_active_time_seconds": None,
                "model": "gpt-6-luna",
                "reasoning_effort": "max",
                "worker_stage_elapsed_seconds_includes_tool_gaps": True,
            },
        },
        "artifacts": refs,
        "reason": None,
    }
    reply_path.parent.mkdir(parents=True, exist_ok=True)
    with reply_path.open("x", encoding="utf-8") as stream:
        json.dump(reply, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())
    print(json.dumps({"reply_path": str(reply_path.resolve()), "artifact_count": len(refs), "outcome": "done", "preflight_status": "not_run"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
