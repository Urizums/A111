"""Compare clean rerun scientific outputs with the frozen production products."""
import hashlib
import json
from pathlib import Path
import pandas as pd

FROZEN = Path("runs/R21/execution/science-v1")
RERUN = Path("runs/R21/review/initial/reproduction-new")
FILES = [
    "future/shared_ridge10/predictions.csv", "future/shared_ridge10/replenishment.csv",
    "future/weekly_mean56/predictions.csv", "future/weekly_mean56/replenishment.csv",
    "results/historical_predictions_plans.csv", "results/science_summary.json",
    "results/selection.json", "results/group_stage_method_id_policy.csv",
    "results/group_stage_method_id_policy_holiday.csv", "results/group_stage_method_id_policy_horizon.csv",
    "results/group_stage_method_id_policy_item_id.csv", "results/group_stage_method_id_policy_store_id.csv",
    "results/interval_tradeoff.csv", "results/future_daily_summary.csv", "results/sensitivity.csv",
    "uncertainty/residual_coordinates_all.csv", "uncertainty/pool_membership_all_origins.csv",
    "uncertainty/residual_days_final_shared_ridge10.csv", "uncertainty/residual_days_final_weekly_mean56.csv",
]

def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def differences(a, b, prefix=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += differences(a.get(k, "<missing>"), b.get(k, "<missing>"), f"{prefix}.{k}".strip("."))
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [{"path": prefix, "left_len": len(a), "right_len": len(b)}]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += differences(x, y, f"{prefix}[{i}]")
        return out
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        delta = float(a) - float(b)
        return [] if abs(delta) <= 1e-12 else [{"path": prefix, "frozen": a, "rerun": b, "delta": delta}]
    return [] if a == b else [{"path": prefix, "frozen": a, "rerun": b}]

checks = []
for rel in FILES:
    left, right = FROZEN / rel, RERUN / rel
    if not left.is_file() or not right.is_file():
        checks.append({"path": rel, "both_exist": False})
        continue
    same = left.stat().st_size == right.stat().st_size and sha(left) == sha(right)
    detail = {"path": rel, "both_exist": True, "same_bytes": same,
              "frozen_bytes": left.stat().st_size, "rerun_bytes": right.stat().st_size,
              "frozen_sha256": sha(left), "rerun_sha256": sha(right)}
    if rel.endswith(".csv") and not same:
        a, b = pd.read_csv(left), pd.read_csv(right)
        cols = list(a.columns) == list(b.columns)
        detail["columns_equal"] = cols
        detail["shape_equal"] = a.shape == b.shape
        if cols and a.shape == b.shape:
            detail["dataframe_equal"] = a.equals(b)
    elif rel.endswith(".json") and not same:
        ja, jb = json.loads(left.read_text(encoding="utf-8")), json.loads(right.read_text(encoding="utf-8"))
        detail["parsed_json_equal"] = ja == jb
        detail["numeric_or_string_differences"] = differences(ja, jb)
    checks.append(detail)

report = {"schema": "r21-clean-rerun-comparison/1", "scope": "selected numeric/scientific output files only; no author verdicts or future truth", "files_checked": checks,
          "all_exist": all(x.get("both_exist") for x in checks),
          "all_byte_identical": all(x.get("same_bytes") for x in checks)}
(Path("runs/R21/review/initial") / "reproduction-comparison.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"files_checked": len(checks), "all_exist": report["all_exist"], "all_byte_identical": report["all_byte_identical"], "nonidentical": [x for x in checks if not x.get("same_bytes")]}, indent=2))
