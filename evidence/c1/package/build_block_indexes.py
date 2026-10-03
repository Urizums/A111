#!/usr/bin/env python3
"""Build C1 package evidence indexes from the four retained sample trees."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
SAMPLES = ("B1", "A1", "A2", "B2")
ORDER = {name: i for i, name in enumerate(SAMPLES)}
SKILL = Path("/root/.codex/skills/remote-skills/skill-6ab323b7c2a081919b95502e8e7297f0")
CODE_PATHS = [
    WORK / "Study_Plan.md",
    WORK / "coordinator/Study_Freeze.json",
    WORK / "shared/Operator_Protocol.md",
    WORK / "shared/Worker_Protocol.md",
    WORK / "shared/capture.py",
    WORK / "materials/package.json",
    WORK / "materials/notes.txt",
    SKILL / "SKILL.md",
    SKILL / "scripts/hostbridge.py",
    SKILL / "scripts/hostdraft.py",
    SKILL / "scripts/packagectl.py",
    SKILL / "scripts/flowctl.py",
    SKILL / "scripts/templates.py",
    SKILL / "scripts/runledger.py",
    SKILL / "references/task-entry.md",
    SKILL / "references/host-bridge.md",
    SKILL / "references/host-drafts.md",
    SKILL / "references/host-execution.md",
    SKILL / "references/package-contract.md",
    Path(__file__).resolve(),
]

ANNOTATIONS = {
    "B1": {
        "business_acceptance": "pass",
        "controller_terminal": "completed",
        "capture_grade": "qualified with material gaps",
        "corrections": [
            "The first actions JSON ended with a literal backslash-n and its business-artifact verification failed with JSONDecodeError: Extra data; the rejected version and failure capture were retained.",
            "The first worker reply also had a literal backslash-n and was retained as preflight-rejected; no failed check-reply capture exists for that version. The final reply check passed.",
            "The first packagectl assessment used the raw source-byte hash and failed; the rejected result and capture were retained, then the original canonical package hash was used and assessment passed.",
        ],
        "recording_deviations": [
            "The original issue remained dispatching across a boot change without native creation evidence. The branch's actual call history was checked and confirmed no creation call had been made; one first actual spawn then used the saved issue arguments unchanged. No sample or issue was replaced.",
            "The original setup begin marker belongs to the prior boot; no same-boot setup end was backfilled, so that setup span is unverified.",
            "Three status snapshots were queried before their hostbridge observe imports and imported later. Each native query time remains in its actual native record; the later local import times remain in the late-observe logs and are not represented as query times.",
        ],
        "assistance": [
            "Root verified from this branch's call history that native creation had not been called and authorized one first creation using the unchanged saved issue arguments; it separately directed that the cross-boot setup span remain unverified.",
        ],
        "direct_write_disclosure": "Raw native returns, recovery facts, and tool-return messages were persisted through direct file-write APIs where recorded; these are not subprocess captures and remain separately identifiable in native/.",
    },
    "A1": {
        "business_acceptance": "pass",
        "controller_terminal": "completed",
        "capture_grade": "qualified with a worker process-capture gap",
        "corrections": [],
        "recording_deviations": [
            "The worker disclosed an initial uncaptured `mkdir -p artifacts/captures` process. The operation is not retroactively represented as a capture.",
            "The business file is a Flow response envelope with its actions array nested under artifacts; the independent v1 review inspected the nested array and passed the original acceptance.",
            "The third wait ended after worker messages, but the exact raw wait return was not available; the observation file labels this unknown and does not invent a timeout/result.",
        ],
        "assistance": [],
        "direct_write_disclosure": "Raw collaboration wait/status returns and coordinator review records were persisted through direct file-write APIs where identified; they remain separate from subprocess captures.",
    },
    "A2": {
        "business_acceptance": "pass",
        "controller_terminal": "completed",
        "capture_grade": "qualified with unverified worker setup and a missing decision-begin marker",
        "corrections": [
            "The worker reported two code-mode attempts to encode reply-authoring source failed before launching a subprocess; the successful authoring source and capture were retained.",
        ],
        "recording_deviations": [
            "The worker reported some initial inspection/capture-help queries were unrecorded. Its installed Forge SKILL read is unverified because the retained evidence does not establish whether it succeeded.",
            "The coordinator's first final-material read assumed `artifacts/captures/check-reply.json` and failed; the actual worker check-reply is `artifacts/check-reply.capture.json` and passed. The failed read capture is retained.",
            "A decision end marker exists but the begin marker was missed. The end was retained and no begin time or decision span was fabricated.",
            "The final wait notification result was not available verbatim; its observation explicitly preserves that limitation.",
        ],
        "assistance": [
            "Root said the package block could continue with the actual original order and that business, controller, and capture findings should remain distinct.",
        ],
        "direct_write_disclosure": "Raw native returns, worker messages, and the manually authored A-mode decision draft/final were persisted through direct file-write APIs; these are separately identified and are not subprocess captures.",
    },
    "B2": {
        "business_acceptance": "pass",
        "controller_terminal": "completed",
        "capture_grade": "qualified with coordinator protocol and marker deviations; worker skill read unverified",
        "corrections": [],
        "recording_deviations": [
            "Coordinator initialized the sample log/native/observation directories by direct patch writes before the first setup marker; this is disclosed in each directory's bootstrap note.",
            "A setup end marker was recorded after prepare and before issue. A second actual setup end was recorded after issue. Both remain; no single setup span is claimed.",
            "The first running snapshot was passed to hostbridge observe before accepted, and that capture failed. An accepted attempt with the list_agents snapshot also failed because it was not the creation receipt. Root clarified that accepted needs the original spawn return task_name; that original return was then accepted and the same saved status snapshot was observed successfully. No spawn was repeated.",
            "One coordinator inspection assumed the worker's `process-captures.jsonl` was newline-delimited JSON and failed. The file is one pretty-printed JSON capture despite its filename; the failed and corrected inspection captures remain.",
            "The worker reported reading the installed Forge SKILL, but the retained process read capture shows Worker_Protocol, package/notes, and three references rather than SKILL.md; the SKILL read remains unverified.",
        ],
        "assistance": [
            "Root explicitly directed retaining the failed observe and duplicate setup markers, and distinguished the original spawn return (accepted) from a list_agents snapshot (recover-accepted only for an unresolved issue). The saved spawn return was used for the original accepted transition.",
        ],
        "direct_write_disclosure": "Coordinator used direct patch writes for the bootstrap notes, exact raw native tool returns, worker final message, independent checker/review/results, and final decision; all actual subprocesses are separately captured.",
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(WORK.resolve()))


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def capture_records(sample: str):
    directory = ROOT / sample
    records = []
    parse_errors = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        value = load(path)
        if value is None:
            parse_errors.append({"path": rel(path), "sha256": sha(path), "reason": "not valid JSON document"})
            continue
        if isinstance(value, dict) and value.get("schema") == "forge-comparison-cli/1":
            records.append({
                "sample": sample,
                "capture_path": rel(path),
                "capture_sha256": sha(path),
                "record": value,
            })
    records.sort(key=lambda item: (item["record"].get("begin", {}).get("utc", ""), item["capture_path"]))
    return records, parse_errors


def marker_records(sample: str):
    directory = ROOT / sample
    records = []
    for base in (directory / "observations", directory / "artifacts/observations"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.json")):
            value = load(path)
            if isinstance(value, dict) and value.get("schema") == "forge-comparison-marker/1":
                records.append({"sample": sample, "marker_path": rel(path), "marker_sha256": sha(path), "record": value})
    return records


def native_records(sample: str):
    base = ROOT / sample / "native"
    observers, files = [], []
    if base.exists():
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            item = {"sample": sample, "path": rel(path), "size_bytes": path.stat().st_size, "sha256": sha(path)}
            if path.suffix.lower() == ".json":
                value = load(path)
                if value is not None:
                    item["json"] = value
                    if isinstance(value, dict) and value.get("schema") == "forge-comparison-native-observer/1":
                        observers.append({"sample": sample, "observer_path": rel(path), "observer_sha256": sha(path), "record": value})
            files.append(item)
    return observers, files


def marker_spans(sample: str, records):
    grouped = {}
    for item in records:
        r = item["record"]
        grouped.setdefault((r.get("actor"), r.get("stage")), []).append(r)
    result = []
    for (actor, stage), rows in sorted(grouped.items()):
        begins = [r for r in rows if r.get("event") == "begin"]
        ends = [r for r in rows if r.get("event") == "end"]
        status, duration = "unverified", None
        begin = begins[0] if len(begins) == 1 else None
        end = ends[0] if len(ends) == 1 else None
        if len(begins) == 1 and len(ends) == 1:
            if begin.get("boot_id") != end.get("boot_id"):
                status = "cross_boot_unverified"
            elif end.get("monotonic_ns", -1) < begin.get("monotonic_ns", 0):
                status = "negative_order_unverified"
            else:
                status = "same_boot_pair"
                duration = (end["monotonic_ns"] - begin["monotonic_ns"]) / 1_000_000_000
        elif len(ends) > 1:
            status = "duplicate_end_unverified"
        elif len(begins) > 1:
            status = "duplicate_begin_unverified"
        elif begins:
            status = "missing_end_unverified"
        elif ends:
            status = "missing_begin_unverified"
        result.append({
            "actor": actor,
            "stage": stage,
            "status": status,
            "duration_seconds": duration,
            "begin_markers": [r for r in begins],
            "end_markers": [r for r in ends],
        })
    return result


def stdout_json(record):
    try:
        return json.loads(record.get("stdout", ""))
    except Exception:
        return None


def sample_summary(sample, cli, markers, observers, unparsed):
    directory = ROOT / sample
    reqdoc = load(directory / "job/request.json") or {}
    request = reqdoc.get("request", {}) if isinstance(reqdoc, dict) else {}
    spawn_path = directory / "native/spawn-arguments.json"
    spawn = load(spawn_path) or {}
    state = load(directory / "state.json") or {}
    control = load(directory / "job/control.json") or {}
    ledger = load(directory / "job/ledger.json") or {}

    def has_script(argv, script_name):
        return any(str(token).endswith(script_name) for token in argv)

    flattened = [(item["capture_path"], item["record"]) for item in cli]
    checks = []
    assessments = []
    commits = []
    next_states = []
    decision_preflights = []
    reconciles = []
    source_checker = None
    for capture_path, record in flattened:
        argv = record.get("argv", [])
        if has_script(argv, "hostdraft.py") and "check-reply" in argv and "--help" not in argv:
            output = stdout_json(record) or {}
            checks.append({"path": capture_path, "actor": record.get("actor"), "exit_code": record.get("exit_code"), "status": output.get("status")})
        if has_script(argv, "packagectl.py") and "assess" in argv and "--help" not in argv:
            output = stdout_json(record) or {}
            assessments.append({"path": capture_path, "exit_code": record.get("exit_code"), "verdict": output.get("verdict"), "stderr": record.get("stderr", "")})
        if has_script(argv, "hostdraft.py") and "check-decision" in argv and "--help" not in argv:
            output = stdout_json(record) or {}
            decision_preflights.append({"path": capture_path, "exit_code": record.get("exit_code"), "status": output.get("status")})
        if has_script(argv, "hostbridge.py") and "commit" in argv and "--help" not in argv:
            output = stdout_json(record) or {}
            commits.append({"path": capture_path, "exit_code": record.get("exit_code"), "phase": output.get("phase"), "coordinator_outcome": output.get("coordinator_outcome")})
        if has_script(argv, "packagectl.py") and "next" in argv and "--help" not in argv:
            output = stdout_json(record) or {}
            next_states.append({"path": capture_path, "exit_code": record.get("exit_code"), "status": output.get("status"), "steps": output.get("steps")})
        if has_script(argv, "hostbridge.py") and "reconcile" in argv and "--help" not in argv:
            output = stdout_json(record) or {}
            ledger_report = output.get("ledger") or {}
            reconciles.append({"path": capture_path, "exit_code": record.get("exit_code"), "phase": output.get("phase"), "ledger_state": ledger_report.get("state"), "ledger_evidence_valid": ledger_report.get("evidence_valid")})
        if capture_path == f"package/{sample}/review/source-checker.json":
            source_checker = {"path": capture_path, "exit_code": record.get("exit_code"), "result": stdout_json(record)}

    queries = [r for r in observers if r["record"].get("tool") == "list_agents" and r["record"].get("event") == "intent"]
    spawns = [r for r in observers if r["record"].get("tool") == "spawn_agent" and r["record"].get("event") == "intent"]
    waits = []
    for path in sorted((directory / "native").glob("*notification-wait*")):
        waits.append({"path": rel(path), "sha256": sha(path), "return": load(path)})

    coord_markers = [m for m in markers if m["record"].get("actor") == "coordinator" and m["marker_path"].startswith(f"package/{sample}/observations/")]
    spans = marker_spans(sample, coord_markers)
    worker_check_valid = any(c["actor"] != "coordinator" and c["exit_code"] == 0 and c["status"] == "payload_valid" for c in checks)
    flow_status = (state.get("flow_state") or {}).get("status")
    outcome = ANNOTATIONS[sample]
    return {
        "sample": sample,
        "treatment": "A/manual" if sample.startswith("A") else "B/hostdraft",
        "worker_spawn_arguments": spawn,
        "worker_spawn_count_observed": len(spawns),
        "requested_model": spawn.get("model"),
        "requested_reasoning_effort": spawn.get("reasoning_effort"),
        "requested_fork_turns": spawn.get("fork_turns"),
        "host_internal_model_identity_verified": False,
        "job_id": request.get("job_id"),
        "attempt_id": request.get("attempt_id"),
        "request_hash": reqdoc.get("request_hash"),
        "invocation_id": request.get("invocation_id"),
        "package_hash": (state.get("package_hash") or (request.get("target_binding") or {}).get("package_hash")),
        "source_checker": source_checker,
        "v1_package_assessments": assessments,
        "worker_check_reply": checks,
        "worker_check_reply_passed": worker_check_valid,
        "decision_preflights": decision_preflights,
        "bridge_commits": commits,
        "package_checkpoint_queries": next_states,
        "original_terminal_state": {
            "flow_status": flow_status,
            "bridge_phase": control.get("phase"),
            "ledger_state": reconciles[-1]["ledger_state"] if reconciles else ledger.get("state"),
            "ledger_evidence_valid": reconciles[-1]["ledger_evidence_valid"] if reconciles else ledger.get("evidence_valid"),
            "reconcile_record": reconciles[-1] if reconciles else None,
        },
        "native_status_query_count": len(queries),
        "native_status_query_intent_refs": [q["observer_path"] for q in queries],
        "notification_wait_count": len(waits),
        "notification_wait_records": waits,
        "coordinator_stage_spans": spans,
        "unparsed_json_evidence": unparsed,
        "business_acceptance": outcome["business_acceptance"],
        "controller_terminal_grade": outcome["controller_terminal"],
        "capture_grade": outcome["capture_grade"],
        "corrections": outcome["corrections"],
        "recording_deviations": outcome["recording_deviations"],
        "parent_assistance": outcome["assistance"],
        "direct_write_disclosure": outcome["direct_write_disclosure"],
        "cli_capture_refs": [
            {"path": item["capture_path"], "sha256": item["capture_sha256"], "actor": item["record"].get("actor"), "exit_code": item["record"].get("exit_code")}
            for item in cli
        ],
        "native_observer_refs": [
            {"path": item["observer_path"], "sha256": item["observer_sha256"], "tool": item["record"].get("tool"), "event": item["record"].get("event")}
            for item in observers
        ],
        "marker_refs": [
            {"path": item["marker_path"], "sha256": item["marker_sha256"], "stage": item["record"].get("stage"), "event": item["record"].get("event"), "boot_id": item["record"].get("boot_id")}
            for item in markers
        ],
        "files_at_index_build_time": [
            {"path": rel(path), "size_bytes": path.stat().st_size, "sha256": sha(path)}
            for path in sorted(directory.rglob("*"))
            if path.is_file() and path.name != "index.json"
        ],
    }


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


all_cli, all_markers, all_native_observers, all_native_files = [], [], [], []
sample_data = {}
for sample in SAMPLES:
    cli, unparsed = capture_records(sample)
    markers = marker_records(sample)
    observers, native_files = native_records(sample)
    sample_data[sample] = (cli, markers, observers, native_files, unparsed)
    all_cli.extend(cli)
    all_markers.extend(markers)
    all_native_observers.extend(observers)
    all_native_files.extend(native_files)

all_cli.sort(key=lambda x: (ORDER[x["sample"]], x["record"].get("begin", {}).get("utc", ""), x["capture_path"]))
all_markers.sort(key=lambda x: (ORDER[x["sample"]], x["record"].get("monotonic_ns", 0), x["marker_path"]))
all_native_observers.sort(key=lambda x: (ORDER[x["sample"]], x["record"].get("monotonic_ns", 0), x["observer_path"]))
all_native_files.sort(key=lambda x: (ORDER[x["sample"]], x["path"]))

source_hashes = {}
for path in CODE_PATHS:
    key = str(path.resolve()) if path.is_absolute() else rel(path)
    source_hashes[key] = {"exists": path.is_file(), "sha256": sha(path) if path.is_file() else None, "size_bytes": path.stat().st_size if path.is_file() else None}

write_json(ROOT / "cli-index.json", {
    "schema": "forge-comparison-cli-index/1",
    "scope": "All captured subprocess records found in the four C1 package sample trees at index-build time. Each record preserves its original argv, stdout, stderr, exit, timestamps, and base64 fields.",
    "record_count": len(all_cli),
    "records": all_cli,
})
write_json(ROOT / "native-index.json", {
    "schema": "forge-comparison-native-index/1",
    "scope": "Local before-call intents and after-return observations, plus every raw file in each sample native directory. Observer timestamps are local capture times, not provider-side event timestamps.",
    "observer_count": len(all_native_observers),
    "observers": all_native_observers,
    "native_directory_files": all_native_files,
})
write_json(ROOT / "marker-index.json", {
    "schema": "forge-comparison-marker-index/1",
    "scope": "All coordinator and worker stage marker records under each sample observations directory; spans are computed only from a unique same-boot begin/end pair.",
    "marker_count": len(all_markers),
    "markers": all_markers,
})

summaries = []
for sample in SAMPLES:
    cli, markers, observers, native_files, unparsed = sample_data[sample]
    summary = sample_summary(sample, cli, markers, observers, unparsed)
    summaries.append(summary)
    write_json(ROOT / sample / "index.json", {
        "schema": "forge-comparison-sample-index/1",
        **summary,
    })

sample_by_name = {item["sample"]: item for item in summaries}
block_summary = {
    "schema": "forge-protocol-comparison-block-summary/1",
    "block": "C1 package",
    "sample_order": list(SAMPLES),
    "denominator": 4,
    "samples_retained": list(SAMPLES),
    "sources_and_code_hashes": source_hashes,
    "record_counts": {
        "cli_captures": len(all_cli),
        "native_observers": len(all_native_observers),
        "markers": len(all_markers),
        "native_directory_files": len(all_native_files),
        "native_status_queries": sum(item["native_status_query_count"] for item in summaries),
        "notification_waits": sum(item["notification_wait_count"] for item in summaries),
    },
    "grades": {
        "business_acceptance": {item["sample"]: item["business_acceptance"] for item in summaries},
        "controller_terminal": {item["sample"]: item["controller_terminal_grade"] for item in summaries},
        "capture_integrity": {item["sample"]: item["capture_grade"] for item in summaries},
    },
    "sample_indexes": [f"package/{sample}/index.json" for sample in SAMPLES],
    "full_indexes": ["package/cli-index.json", "package/native-index.json", "package/marker-index.json"],
    "samples": summaries,
    "block_level_disclosures": [
        "Before Operator_Protocol.md was read, an initial `pwd && ls -la` command ran without shared/capture.py. It was not rerun or represented as a capture.",
        "Two capture utility help probes (`capture.py --help` and `capture.py cli --help`) ran directly to learn the recording interface; they spawned no child process and are not wrapped captures.",
        "The final B2 block-index builder itself is invoked through shared/capture.py and its raw capture is expected at package/B2/logs/037-build-block-indexes.json. That final self-referential index-build capture is separately retained but excluded from the indexes it generates.",
        "Several coordinator patch-tool writes are not subprocess captures; each sample's direct_write_disclosure and retained raw native files identify these separately.",
    ],
    "timing_policy": "Raw marker records and uniquely paired same-boot spans are reported in sample indexes. Missing, cross-boot, duplicate, or reversed marker pairs remain unverified. No speed gain, acceleration, or cross-block comparison is claimed.",
    "terminal_boundary": "Bridge commit and packagectl checkpoint state are reported; this study does not claim successful hostdriver execution. Internal model identity, tokens, and costs were not verified by the bridge.",
    "overall_readout": "All four independently reviewed package outputs pass the unchanged v1 quotes and commitments criteria, and all four original bridge commits/checkpoint terminal states are completed. The block retains material capture/protocol deviations, so the traces are not represented as uniformly complete or assistance-free.",
}
write_json(ROOT / "block-summary.json", block_summary)

lines = [
    "# C1 package block evidence",
    "",
    "Four package samples were run in the frozen order B1, A1, A2, B2 against the unchanged package and notes. Each sample has an original bridge job, one requested gpt-6-luna/max/fork-none worker, an independent source review using the original v1 acceptance, and a recorded terminal checkpoint result.",
    "",
    "| Sample | Treatment | Business v1 | Controller terminal | Requested worker | Status queries / waits | Capture grade |",
    "|---|---|---|---|---|---:|---|",
]
for item in summaries:
    lines.append(f"| {item['sample']} | {item['treatment']} | {item['business_acceptance']} | {item['controller_terminal_grade']} | {item['requested_model']}/{item['requested_reasoning_effort']}/{item['requested_fork_turns']} | {item['native_status_query_count']} / {item['notification_wait_count']} | {item['capture_grade']} |")
lines.extend([
    "",
    "The v1 source rule is unchanged: every quote must be an exact substring; only explicit actions are included; unstated owners/dates remain null. The independently reviewed rows are in each sample's `review/source-review.md`. The frozen no-action branch was not run, and no cross-block or speed claim is made.",
    "",
    "Evidence indexes: `cli-index.json` preserves every captured argv/stdout/stderr/exit and timing record found at build time; `native-index.json` keeps native intent/return observers and raw native files; `marker-index.json` keeps all stage markers. Per-sample `index.json` files link the evidence and show only uniquely paired same-boot spans as durations. Missing, duplicate, or cross-boot markers remain unverified.",
    "",
    "Material qualifications are retained in `block-summary.json` and each sample index. B1 preserves boot-change recovery, late observe imports, worker/output corrections, and an initial package-assessment error. A1 preserves a worker's disclosed uncaptured mkdir and a Flow-envelope packaging caveat. A2 preserves unrecorded worker setup reports, an incorrect coordinator capture path, and a missing decision-begin marker. B2 preserves the premature duplicate setup end, two failed bridge state transitions before recovery with the original receipts, one failed capture-index parse, and an unverified worker SKILL read. Root assistance is documented where it affected recovery.",
    "",
    "The final index-builder subprocess is itself captured at `package/B2/logs/037-build-block-indexes.json`; it is excluded from the indexes it creates to avoid a self-referential capture. Earlier captured index/audit commands remain in the CLI index. Coordinator direct-write operations are disclosed separately in the sample indexes and raw-return files.",
    "",
    "Source, protocol, and installed Forge code hashes are listed in `block-summary.json`. Hostbridge telemetry reports internal model identity unverified and token/cost fields null.",
    "",
])
(ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")

print(json.dumps({
    "samples": list(SAMPLES),
    "cli_captures": len(all_cli),
    "native_observers": len(all_native_observers),
    "markers": len(all_markers),
    "status_queries": block_summary["record_counts"]["native_status_queries"],
    "waits": block_summary["record_counts"]["notification_waits"],
    "summary": "package/block-summary.json",
    "readme": "package/README.md",
}, ensure_ascii=False, indent=2))
