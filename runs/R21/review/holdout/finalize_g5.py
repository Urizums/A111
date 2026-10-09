"""Verify terminal holdout evidence and write the final g5 receiver result."""
from __future__ import annotations
import base64, hashlib, json
from pathlib import Path
import pandas as pd

R = Path("runs/R21")
OUT = R / "review/holdout"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
binding = json.loads((OUT / "freeze-bindings.json").read_text(encoding="utf-8"))
first = json.loads((OUT / "first-truth-open.json").read_text(encoding="utf-8"))
metrics = json.loads((OUT / "metrics.json").read_text(encoding="utf-8"))
validation = json.loads((OUT / "validation.json").read_text(encoding="utf-8"))
result_path = OUT / "result.json"
result = json.loads(result_path.read_text(encoding="utf-8"))

receipt_paths = sorted(p for p in OUT.glob("*-command*.json") if not p.name.startswith("finalize"))
commands = []
for p in receipt_paths:
    d = json.loads(p.read_text(encoding="utf-8"))
    out = base64.b64decode(d.get("stdout_base64", ""), validate=True)
    err = base64.b64decode(d.get("stderr_base64", ""), validate=True)
    begin, end = d.get("begin", {}), d.get("end", {})
    out_matches = out.decode("utf-8", errors="replace") == d.get("stdout", "")
    err_matches = err.decode("utf-8", errors="replace") == d.get("stderr", "")
    commands.append({"receipt": str(p).replace("\\", "/"), "schema": d.get("schema"), "state": d.get("state"),
        "exit_code": d.get("exit_code"), "argv": d.get("argv"), "cwd": d.get("cwd"),
        "begin_utc": begin.get("utc"), "end_utc": end.get("utc"), "stdout_raw_bytes": len(out), "stderr_raw_bytes": len(err),
        "stdout_base64_matches_utf8_replace": out_matches, "stderr_base64_matches_utf8_replace": err_matches,
        "terminal_and_streams_valid": d.get("state") == "finished" and isinstance(d.get("exit_code"), int) and bool(begin.get("utc")) and bool(end.get("utc")) and out_matches and err_matches})

first_receipt_path = OUT / "03-first-truth-open-command.json"
first_receipt = json.loads(first_receipt_path.read_text(encoding="utf-8"))
open_time = pd.Timestamp(first["first_open_utc"])
receipt_begin = pd.Timestamp(first_receipt["begin"]["utc"])
receipt_end = pd.Timestamp(first_receipt["end"]["utc"])
identity_order_valid = (receipt_begin <= open_time <= receipt_end
    and pd.Timestamp(binding["execution_lock"]["frozen_at"]) < open_time
    and pd.Timestamp(binding["initial_lock"]["frozen_at"]) < open_time
    and pd.Timestamp(binding["evaluation_lock"]["frozen_at"]) < open_time
    and first["truth_identity"]["lock_identity_matches"] and first["all_bindings_precede_truth_open"])

group_df = pd.read_csv(OUT / "group_metrics.csv")
daily_df = pd.read_csv(OUT / "daily_route_metrics.csv")
daily_diff = pd.read_csv(OUT / "daily_route_differences.csv")
key_df = pd.read_csv(OUT / "key_metrics.csv")
required_groups = {"overall": 1, "date": 42, "activity": 2, "horizon_band": 6, "activity_x_horizon": 12, "store": 12, "item": 8}
actual_groups = {k: int(v) for k, v in group_df.groupby("dimension")["group"].nunique().to_dict().items()}
all_group_counts_present = all(actual_groups.get(k) == v for k, v in required_groups.items())
all_routes_have_complete_metrics = all(
    group_df[group_df.route == route].shape[0] == sum(required_groups.values())
    for route in ("shared_ridge10", "weekly_mean56"))

outputs = {
    "HOLDOUT_REPORT.md": sha(OUT / "HOLDOUT_REPORT.md"),
    "metrics.json": sha(OUT / "metrics.json"), "group_metrics.csv": sha(OUT / "group_metrics.csv"),
    "daily_route_metrics.csv": sha(OUT / "daily_route_metrics.csv"), "daily_route_differences.csv": sha(OUT / "daily_route_differences.csv"),
    "key_metrics.csv": sha(OUT / "key_metrics.csv"), "validation.json": sha(OUT / "validation.json"),
}
assert len(key_df) == 8064 and len(daily_df) == 84 and len(daily_diff) == 42
assert len(group_df) == 2 * sum(required_groups.values()) and all_group_counts_present and all_routes_have_complete_metrics
assert validation["passed"] and identity_order_valid
assert all(x["terminal_and_streams_valid"] for x in commands)
assert all(x["exit_code"] == 0 for x in commands)
assert not any(p.name.startswith("finalize") for p in receipt_paths)

process = {
    "all_command_receipts_seen_at_finalization_are_finished": True,
    "recorded_command_count": len(commands), "nonzero_exit_commands": [], "commands": commands,
    "no_known_command_session_remains_running": True,
    "finalizer_receipt": "runs/R21/review/holdout/finalize-g5-command.json (recorded by wrapper after this process exits)",
}
result.update({
    "g5_verdict": "PASS", "all_preregistered_metrics_and_groups_recomputed": True,
    "no_tuning_or_route_reselection": True, "no_causal_or_significance_claim": True,
    "4032_keys_not_independent_replicates": True, "truth_open_sequence_valid": identity_order_valid,
    "group_dimensions": actual_groups, "all_routes_have_complete_metrics": all_routes_have_complete_metrics,
    "output_sha256": outputs, "terminal_process_audit": process,
    "scope_exception": result.get("observed_unrecorded_read"),
})
result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(OUT / "process-status.json").write_text(json.dumps(process, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"g5_verdict": "PASS", "truth_sequence_valid": identity_order_valid,
    "truth_rows": validation["truth_rows"], "per_route_rows": validation["route_rows"],
    "group_dimensions": actual_groups, "group_rows": len(group_df), "daily_pair_rows": len(daily_diff),
    "key_metric_rows": len(key_df), "recorded_commands": len(commands),
    "all_terminal": process["all_command_receipts_seen_at_finalization_are_finished"], "files_written": list(outputs)}, ensure_ascii=False, indent=2))
