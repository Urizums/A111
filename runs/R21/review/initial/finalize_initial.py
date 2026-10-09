"""Freeze the initial receiver's evidence index; never opens evaluation truth."""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path("runs/R21")
OUT = ROOT / "review/initial"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_lock(lock_path: Path, allowed_paths: set[str]) -> dict:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    checks = []
    for entry in lock["files"]:
        rel = entry["path"].replace("\\", "/")
        if rel not in allowed_paths:
            continue
        p = Path(rel)
        checks.append({"path": rel, "expected_bytes": entry["size_bytes"], "actual_bytes": p.stat().st_size,
                       "expected_sha256": entry["sha256"], "actual_sha256": sha(p),
                       "matches": p.stat().st_size == entry["size_bytes"] and sha(p) == entry["sha256"]})
    return {"path": str(lock_path).replace("\\", "/"), "sha256": sha(lock_path), "checks": checks,
            "all_match": all(x["matches"] for x in checks)}

inputs = {"runs/R21/inputs/REQUEST.md", "runs/R21/inputs/PROBLEM.md"}
inputs |= {f"runs/R21/inputs/raw/{x}" for x in ("calendar.csv", "decision.json", "demand_reports.csv", "items.csv", "promotions.csv", "stores.csv", "weather.csv")}
inputs |= {f"runs/R21/inputs/reference/{x}" for x in ("BASELINE.md", "experiment.json", "run.py")}
protocol_paths = {"runs/R21/protocol/PROTOCOL.md", "runs/R21/protocol/acceptance.json"}
clarification_paths = {"runs/R21/prospective-clarification/CLARIFICATION.md"}
identity_hashes = {
    "input_lock": check_lock(ROOT / "input-lock.json", inputs),
    "protocol_lock": check_lock(ROOT / "protocol-lock.json", protocol_paths),
    "clarification_lock": check_lock(ROOT / "clarification-lock.json", clarification_paths),
}

execution_lock_path = ROOT / "execution-lock.json"
prov = json.loads((OUT / "provenance-check.json").read_text(encoding="utf-8"))
audit = json.loads((OUT / "independent-science-audit.json").read_text(encoding="utf-8"))
boundaries = json.loads((OUT / "boundary-controls.json").read_text(encoding="utf-8"))
repro = json.loads((OUT / "reproduction-comparison.json").read_text(encoding="utf-8"))
paper_pdf = ROOT / "execution/paper-final-v4/paper.pdf"
paper_md = ROOT / "execution/paper-final-v4/paper.md"
receipt_files = sorted(p for p in OUT.glob("*-command*.json") if not p.name.startswith("finalize-command"))
receipts = []
for p in receipt_files:
    d = json.loads(p.read_text(encoding="utf-8"))
    out_raw = base64.b64decode(d.get("stdout_base64", ""), validate=True)
    err_raw = base64.b64decode(d.get("stderr_base64", ""), validate=True)
    begin, end = d.get("begin", {}), d.get("end", {})
    receipts.append({"receipt": str(p).replace("\\", "/"), "argv": d.get("argv"), "cwd": d.get("cwd"),
                     "state": d.get("state"), "exit_code": d.get("exit_code"),
                     "begin_utc": begin.get("utc"), "end_utc": end.get("utc"),
                     "stdout_raw_bytes": len(out_raw), "stderr_raw_bytes": len(err_raw),
                     "stdout_base64_matches_utf8_replace": out_raw.decode("utf-8", errors="replace") == d.get("stdout", ""),
                     "stderr_base64_matches_utf8_replace": err_raw.decode("utf-8", errors="replace") == d.get("stderr", "")})

allowed_rerun_metadata_differences = {"runtime_seconds", "actual_selected_at_utc"}
repro_content_equivalent = repro["all_exist"] and all(
    item.get("same_bytes") or (
        item.get("path") in {"results/science_summary.json", "results/selection.json"}
        and set(x.get("path") for x in item.get("numeric_or_string_differences", [])).issubset(allowed_rerun_metadata_differences)
    ) for item in repro["files_checked"]
)

gates = {
    "g1": {"status": "PASS", "basis": "raw lock identities match; independent raw revision/as-of audit, source snapshots/features, every residual coordinate, exact 96-key day eligibility and timestamps match; no post-origin promotion/weather enters final features"},
    "g2": {"status": "PASS", "basis": "old current-policy algorithm reconstructed as shared ridge10; independent weekly-mean baseline; same raw information origins, dates, residual pool, integer objective and resource limits; selected on 42 historical days before 42 validation days; boundary controls reject invalid outputs while accepting continuous scenario demand"},
    "g3": {"status": "PASS", "basis": "clean command exited 0; 17 of 19 selected science-output files byte-identical; remaining two differ only at runtime_seconds and actual_selected_at_utc; independent reconstruction matched frozen predictions, intervals, plans, historical metrics and residual lineage; failed provenance parser attempt and repairs retained"},
    "g4": {"status": "PASS_WITH_OPTIONAL_WORDING_NOTE", "basis": "entire Chinese paper read; all 13 final PDF pages rendered and visually inspected; tables/claims checked against independent stage/group calculations and frozen outputs; no future truth claim or guaranteed coverage/improvement claim"},
    "g5": {"status": "NOT_EXECUTED", "basis": "evaluation truth remains unopened and prohibited in this receiving stage"},
}

hard_pre_ready = (
    identity_hashes["input_lock"]["all_match"] and identity_hashes["protocol_lock"]["all_match"] and identity_hashes["clarification_lock"]["all_match"]
    and prov["execution_lock_sha256"] == sha(execution_lock_path)
    and prov["all_permitted_lock_entries_match"] and prov["all_command_records_structurally_valid"]
    and prov["command_index_structure"]["all_records_bound"]
    and prov["identity_source_bindings"]["all_identity_bindings_match"]
    and audit["future_actuals_read"] is False
    and audit["residual_coordinate_reconstruction_comparison"]["all_exact_source_version_and_prediction_fields_match"]
    and audit["residual_pool_membership_comparison"]["all_fields_match"]
    and all(v["prediction_keyset_equal"] and v["plan_exactly_equal"] and v["daily_resource_limits_valid"] and v["finite_ordered_nominal90_output_valid"] for v in audit["final_route_output_comparison"].values())
    and boundaries["all_controls_pass"] and repro_content_equivalent
    and all(gates[g]["status"].startswith("PASS") for g in ("g1", "g2", "g3", "g4"))
)

process_summary = {
    "receiver_command_count": len(receipts),
    "all_commands_terminal": all(r["state"] == "finished" and isinstance(r["exit_code"], int) for r in receipts),
    "all_stream_bindings_valid": all(r["stdout_base64_matches_utf8_replace"] and r["stderr_base64_matches_utf8_replace"] for r in receipts),
    "nonzero_exit_commands": [{"receipt": r["receipt"], "exit_code": r["exit_code"], "argv": r["argv"], "begin_utc": r["begin_utc"], "end_utc": r["end_utc"]} for r in receipts if r["exit_code"] != 0],
    "commands": receipts,
}

pre = {
    "schema": "r21-pre-holdout-ready/1",
    "pre_holdout_ready": hard_pre_ready,
    "status": "READY_FOR_ROOT_FREEZE_AND_SEPARATE_G5_DISPATCH" if hard_pre_ready else "NOT_READY",
    "production_execution_lock": {"path": "runs/R21/execution-lock.json", "sha256": sha(execution_lock_path), "entry_count": prov["lock_entry_count"]},
    "canonical_identity_locks": {k: {"path": v["path"], "sha256": v["sha256"], "entries_checked": len(v["checks"]), "all_match": v["all_match"]} for k, v in identity_hashes.items()},
    "route_output_map": {
        "shared_ridge10": ["runs/R21/execution/science-v1/future/shared_ridge10/predictions.csv", "runs/R21/execution/science-v1/future/shared_ridge10/replenishment.csv"],
        "weekly_mean56": ["runs/R21/execution/science-v1/future/weekly_mean56/predictions.csv", "runs/R21/execution/science-v1/future/weekly_mean56/replenishment.csv"],
        "consumer_paper": ["runs/R21/execution/paper-final-v4/paper.md", "runs/R21/execution/paper-final-v4/paper.pdf"],
    },
    "gate_status": gates,
    "private_truth": {"opened": False, "g5": "NOT_EXECUTED", "next_step_requires_separate_root_authorization": True},
    "model": None, "tokens": None, "cost": None,
    "receiver_locality_note": "path-scoped independent receiving was a local procedural scope, not host/OS isolation",
}
result = {
    "schema": "r21-initial-receiver-result/1",
    "pre_holdout_ready": hard_pre_ready,
    "status": pre["status"], "gate_status": gates,
    "production_lock_sha256": sha(execution_lock_path),
    "canonical_identity_locks": pre["canonical_identity_locks"],
    "evidence": {
        "provenance_report": "runs/R21/review/initial/provenance-check.json",
        "independent_reconstruction": "runs/R21/review/initial/independent-science-audit.json",
        "boundary_controls": "runs/R21/review/initial/boundary-controls.json",
        "clean_rerun_comparison": "runs/R21/review/initial/reproduction-comparison.json",
        "clean_rerun_content_equivalent_after_volatile_metadata": repro_content_equivalent,
        "clean_rerun_output": "runs/R21/review/initial/reproduction-new",
        "paper_pdf_sha256": sha(paper_pdf), "paper_markdown_sha256": sha(paper_md),
        "pdf_pages": 13, "all_13_pages_visually_inspected": True,
        "independent_residual_coordinate_rows": audit["residual_coordinate_reconstruction_comparison"]["independent_rows"],
        "independent_residual_pool_rows": audit["residual_pool_membership_comparison"]["independent_rows"],
        "reconstruction_route_checks": audit["final_route_output_comparison"],
        "independent_historical_stage_count": len(audit["historical_metrics_by_stage"]),
        "independent_historical_group_metric_count": len(audit["historical_group_metrics"]),
        "paper_note": "Optional clarity risk: the business recommendation phrase 可采纳已冻结的R计划 could be read operationally; adjacent prose explicitly bounds the case as synthetic and its figures as unobserved scenario outputs.",
        "observed_nonformal_probe": "A read-only probe used the mistaken path runs/R21/science-v1/run_identity.json and returned not found; no content was read. Correct permitted path runs/R21/execution/science-v1/run_identity.json was then verified against raw/config/source identity hashes.",
    },
    "terminal_processes_at_manifest_time": process_summary,
    "model": None, "tokens": None, "cost": None,
    "future_truth_opened": False,
}
(OUT / "pre-holdout-ready.json").write_text(json.dumps(pre, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(OUT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"pre_holdout_ready": hard_pre_ready, "status": pre["status"], "gates": {k: v["status"] for k, v in gates.items()}, "receiver_commands": len(receipts), "all_commands_terminal": process_summary["all_commands_terminal"], "nonzero_exit_count": len(process_summary["nonzero_exit_commands"]), "future_truth_opened": False}, ensure_ascii=False, indent=2))
