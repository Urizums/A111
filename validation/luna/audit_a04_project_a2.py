#!/usr/bin/env python3
"""Bounded, read-only A04 evidence pass for the frozen project/A2 sample."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "validation/luna/a04_project_a2_evidence.json"
EVIDENCE = ROOT / "evidence/c1"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main() -> int:
    started = utc_now()
    study_text = (EVIDENCE / "Study_Plan.md").read_text(encoding="utf-8")
    manifest = json.loads((EVIDENCE / "Snapshot_Manifest.json").read_text(encoding="utf-8"))
    manifest_entries = {entry["relative_path"]: entry for entry in manifest["entries"]}

    rel_paths = [
        "project/A2/state.json",
        "project/A2/work.json",
        "project/A2/job/ledger.json",
    ]
    rel_paths += [f"project/A2/observations/{p.name}" for p in sorted((EVIDENCE / "project/A2/observations").glob("*.json"))]
    rel_paths += [
        f"project/A2/native/{name}"
        for name in [
            "spawn-arguments.json",
            "spawn-intent-observer.json",
            "spawn-return-observer.json",
            "spawn-return.json",
            "host-status-query.json",
        ]
    ]
    for i in range(1, 6):
        rel_paths.extend(
            f"project/A2/native/status-{i}-{suffix}.json"
            for suffix in ("intent-observer", "return-observer", "return")
        )
    rel_paths.extend(f"project/A2/native/wait-{i}-return.json" for i in range(1, 5))

    file_evidence = []
    manifest_errors = []
    for rel in rel_paths:
        local = EVIDENCE / rel
        data = local.read_bytes()
        actual_sha = hashlib.sha256(data).hexdigest()
        declared = manifest_entries.get(rel)
        if declared is None:
            manifest_errors.append({"path": rel, "error": "not in Snapshot_Manifest.json"})
        elif actual_sha != declared["sha256"] or len(data) != declared["size_bytes"]:
            manifest_errors.append(
                {
                    "path": rel,
                    "expected_sha256": declared["sha256"],
                    "actual_sha256": actual_sha,
                    "expected_size": declared["size_bytes"],
                    "actual_size": len(data),
                }
            )
        file_evidence.append(
            {
                "path": f"evidence/c1/{rel}",
                "original_path": declared.get("original_path") if declared else None,
                "sha256": actual_sha,
                "size_bytes": len(data),
                "manifest_match": bool(
                    declared
                    and actual_sha == declared["sha256"]
                    and len(data) == declared["size_bytes"]
                ),
            }
        )

    a2 = EVIDENCE / "project/A2"
    state = json.loads((a2 / "state.json").read_text(encoding="utf-8"))
    ledger = json.loads((a2 / "job/ledger.json").read_text(encoding="utf-8"))
    observations = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((a2 / "observations").glob("*.json"))]
    native = a2 / "native"

    groups: dict[str, dict[str, list[dict]]] = {}
    for event in observations:
        stage = event.get("stage", "<missing-stage>")
        kind = event.get("event", "<missing-event>")
        groups.setdefault(stage, {}).setdefault(kind, []).append(event)

    marker_stages = []
    for stage, pair in sorted(groups.items()):
        begins = pair.get("begin", [])
        ends = pair.get("end", [])
        begin = begins[0] if len(begins) == 1 else None
        end = ends[0] if len(ends) == 1 else None
        same_boot = bool(begin and end and begin.get("boot_id") == end.get("boot_id"))
        span = None
        if begin and end and same_boot:
            span = round((int(end["monotonic_ns"]) - int(begin["monotonic_ns"])) / 1_000_000_000, 6)
        marker_stages.append(
            {
                "stage": stage,
                "begin_count": len(begins),
                "end_count": len(ends),
                "begin_utc": begin.get("utc") if begin else None,
                "end_utc": end.get("utc") if end else None,
                "begin_monotonic_ns": begin.get("monotonic_ns") if begin else None,
                "end_monotonic_ns": end.get("monotonic_ns") if end else None,
                "boot_ids": sorted({x.get("boot_id") for x in begins + ends if x.get("boot_id")}),
                "same_boot_pair": same_boot,
                "marker_span_seconds": span,
            }
        )

    status_calls = []
    for i in range(1, 6):
        intent = json.loads((native / f"status-{i}-intent-observer.json").read_text(encoding="utf-8"))
        ret_obs = json.loads((native / f"status-{i}-return-observer.json").read_text(encoding="utf-8"))
        raw_return = json.loads((native / f"status-{i}-return.json").read_text(encoding="utf-8"))
        statuses = [x.get("agent_status") for x in raw_return.get("agents", [])]
        status_calls.append(
            {
                "index": i,
                "tool": intent.get("tool"),
                "intent_boot_id": intent.get("boot_id"),
                "return_boot_id": ret_obs.get("boot_id"),
                "same_boot": intent.get("boot_id") == ret_obs.get("boot_id"),
                "raw_statuses": statuses,
                "intent_path_prefix": intent.get("payload", {}).get("path_prefix"),
                "return_payload_sha256_matches": ret_obs.get("payload_sha256") == sha256(native / f"status-{i}-return.json"),
            }
        )

    waits = []
    for i in range(1, 5):
        raw = json.loads((native / f"wait-{i}-return.json").read_text(encoding="utf-8"))
        stage = next((x for x in marker_stages if x["stage"] == f"notification_wait_{i}"), None)
        waits.append(
            {
                "index": i,
                "raw_return": raw,
                "marker_span_seconds": stage["marker_span_seconds"] if stage else None,
                "configured_wait_parameter_record_present": any(
                    (native / name).is_file()
                    for name in (f"wait-{i}-intent.json", f"wait-{i}-arguments.json", f"notification-wait-{i}-arguments.json")
                ),
                "marker_begin_end_pair_present": bool(stage and stage["begin_count"] == 1 and stage["end_count"] == 1),
            }
        )

    required_coordinator_stages = ["setup", "receive", "review", "decision", "commit"]
    by_stage = {item["stage"]: item for item in marker_stages}
    stage_completeness = []
    for stage in required_coordinator_stages:
        item = by_stage.get(stage)
        stage_completeness.append(
            {
                "stage": stage,
                "begin_present": bool(item and item["begin_count"] == 1),
                "end_present": bool(item and item["end_count"] == 1),
                "complete_pair": bool(item and item["begin_count"] == 1 and item["end_count"] == 1 and item["same_boot_pair"]),
            }
        )

    snapshot_requirements = re.findall(r"at most 45-second native notification waits|Maximum five queries", study_text, flags=re.IGNORECASE)
    record = {
        "schema": "luna-bounded-a04-readonly/1",
        "created_at_utc": started,
        "finished_at_utc": utc_now(),
        "scope": "One sample only: frozen project/A2 marker/wait/cutoff completeness pass; not full A04 and not full C1 audit.",
        "requirements": {
            "audit_plan": "runs/S01/audit-plan.json:A04",
            "study_plan": "evidence/c1/Study_Plan.md:C06 and frozen operating protocol",
            "study_plan_relevant_phrases_found": snapshot_requirements,
            "evidence_mapping": "docs/EVIDENCE_MAP.md: original project paths map to evidence/c1/project; originals are not rewritten.",
        },
        "sample_state_at_cutoff": {
            "project_state_status": state.get("status"),
            "task_status": state.get("tasks", {}).get("aggregate_expenses", {}).get("status"),
            "attempt_outcome": state.get("tasks", {}).get("aggregate_expenses", {}).get("attempts", [{}])[-1].get("outcome"),
            "attempt_finished_at": state.get("tasks", {}).get("aggregate_expenses", {}).get("attempts", [{}])[-1].get("finished_at"),
            "active_attempt_id": state.get("tasks", {}).get("aggregate_expenses", {}).get("active_attempt_id"),
            "ledger_event_statuses": [ev.get("status") for job in ledger.get("jobs", {}).values() for attempt in job.get("attempts", []) for ev in attempt.get("events", [])],
        },
        "markers": marker_stages,
        "required_coordinator_stage_completeness": stage_completeness,
        "status_calls": status_calls,
        "notification_waits": waits,
        "audit_observations": [
            "The five saved list_agents return records each report the original A2 worker as running; the frozen query cap is five.",
            "The receive marker has a begin and no end; the state and ledger remain running/requested with no finish/response.",
            "Setup has one same-boot begin/end pair. Review, decision and commit markers are absent in this sample.",
            "All four saved notification-wait return records are present. No wait argument/intent record is present, so configured wait values cannot be verified from the cutoff evidence.",
            "Two wait marker spans exceed 45 seconds; without configured parameters and separate invocation boundaries, this is an observed span only, not proof of a native argument violation.",
            "The pass is limited to project/A2 and does not complete A04 across the eight-sample study or complete the C1 audit.",
        ],
        "manifest_validation": {"files_checked": len(file_evidence), "all_match": not manifest_errors, "errors": manifest_errors},
        "file_evidence": file_evidence,
        "native_calls_made_by_this_audit": 0,
        "historical_controller_commands_run": 0,
    }
    OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT.relative_to(ROOT)),
        "scope": record["scope"],
        "manifest_files_checked": len(file_evidence),
        "all_manifest_matches": not manifest_errors,
        "query_returns": [call["raw_statuses"] for call in status_calls],
        "wait_timed_out": [item["raw_return"].get("timed_out") for item in waits],
        "missing_stage_markers": [x["stage"] for x in stage_completeness if not x["complete_pair"]],
    }, ensure_ascii=False))
    return 1 if manifest_errors else 0


if __name__ == "__main__":
    sys.exit(main())
