"""R21 correction experiment: canonical identities and day-level readiness."""
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path("runs/R21")
PREP = ROOT / "review/preparation"
CORR = ROOT / "review/preparation-correction"
ORIGIN = datetime.fromisoformat("2026-10-31T18:00:00")
LABEL_CUTOFF = datetime.fromisoformat("2026-11-04T18:00:00")
HISTORY_END = date(2026, 10, 31)
COORDS = {(f"S{i:02d}", f"K{j:02d}") for i in range(1, 13) for j in range(1, 9)}


def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def read_rows(p: Path):
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def verify_lock(lock_path: Path, allowed: set[str], previous_hashes: dict[str, str]):
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    checked = []
    for row in lock["files"]:
        rel = row["path"].replace("\\", "/")
        if rel not in allowed:
            continue
        p = Path(rel)
        actual_hash = digest(p)
        actual_size = p.stat().st_size
        direct_hash = previous_hashes.get(rel)
        checked.append({
            "path": rel,
            "lock_size_bytes": row["size_bytes"],
            "actual_size_bytes": actual_size,
            "lock_sha256": row["sha256"],
            "actual_sha256": actual_hash,
            "original_preparation_sha256": direct_hash,
            "lock_match": actual_size == row["size_bytes"] and actual_hash == row["sha256"],
            "original_direct_hash_match": (direct_hash is None or direct_hash == actual_hash),
        })
    expected = sorted(allowed)
    checked_paths = sorted(x["path"] for x in checked)
    return {"lock_path": str(lock_path).replace("\\", "/"), "frozen_at": lock.get("frozen_at"), "expected_authorized_paths": expected, "checked_paths": checked_paths, "missing_authorized_entries": sorted(set(expected) - set(checked_paths)), "entries": checked, "all_lock_matches": len(checked) == len(expected) and all(x["lock_match"] for x in checked), "all_original_direct_hashes_match": all(x["original_direct_hash_match"] for x in checked)}


input_lock = json.loads((ROOT / "input-lock.json").read_text(encoding="utf-8"))
protocol_lock = json.loads((ROOT / "protocol-lock.json").read_text(encoding="utf-8"))
clarification_lock = json.loads((ROOT / "clarification-lock.json").read_text(encoding="utf-8"))
original_audit = json.loads((PREP / "raw-audit.json").read_text(encoding="utf-8"))
original_hashes = original_audit["identities"]
input_allowed = {x["path"] for x in input_lock["files"] if x["path"].startswith("runs/R21/inputs/")}
protocol_allowed = {"runs/R21/protocol/PROTOCOL.md", "runs/R21/protocol/acceptance.json"}
clarification_allowed = {"runs/R21/prospective-clarification/CLARIFICATION.md"}
input_identity = verify_lock(ROOT / "input-lock.json", input_allowed, {k: v["sha256"] for k, v in original_hashes.items()})
protocol_identity = verify_lock(ROOT / "protocol-lock.json", protocol_allowed, {k: v["sha256"] for k, v in original_hashes.items()})
clarification_identity = verify_lock(ROOT / "clarification-lock.json", clarification_allowed, {})

reports = read_rows(ROOT / "inputs/raw/demand_reports.csv")
by_key = {}
for row in reports:
    sd = date.fromisoformat(row["service_date"])
    if sd > HISTORY_END or datetime.fromisoformat(row["available_at"]) > LABEL_CUTOFF:
        continue
    key = (row["service_date"], row["store_id"], row["item_id"])
    old = by_key.get(key)
    order = (int(row["revision"]), datetime.fromisoformat(row["available_at"]))
    if old is None or order > (int(old["revision"]), datetime.fromisoformat(old["available_at"])):
        by_key[key] = row

origins = []
d = date(2026, 7, 8)
while d <= date(2026, 10, 14):
    origins.append(datetime.combine(d, datetime.min.time()).replace(hour=18))
    d += timedelta(days=14)
eligible_by_origin = {}
all_window_days = 0
for source in origins:
    days = []
    for offset in range(1, 15):
        sd = source.date() + timedelta(days=offset)
        all_window_days += 1
        labels = {key[1:] for key, row in by_key.items() if key[0] == sd.isoformat()}
        selected_rows = [row for key, row in by_key.items() if key[0] == sd.isoformat()]
        # A residual date may be used only after the service date ended and every
        # fixed Nov 4 evaluation-label version is already available at calibration.
        ready = sd < ORIGIN.date() and labels == COORDS and all(datetime.fromisoformat(r["available_at"]) <= ORIGIN for r in selected_rows)
        if ready:
            days.append(sd.isoformat())
    eligible_by_origin[source.isoformat()] = days

# Boundary fixture: one complete 96-coordinate day plus a second day with 95
# on-time coordinates and one coordinate arriving one second after calibration.
calibration = datetime.fromisoformat("2026-10-31T18:00:00")
equal_arrival = calibration
one_second_late = calibration + timedelta(seconds=1)
fixture = {}
for day in ("day_equal", "day_late"):
    fixture[day] = {coord: equal_arrival for coord in COORDS}
late_coord = sorted(COORDS)[-1]
fixture["day_late"][late_coord] = one_second_late
fixture["day_95"] = {coord: equal_arrival for coord in sorted(COORDS)[:95]}
fixture_ready = {day: len([t for t in times.values() if t <= calibration]) == 96 and len(times) == 96 for day, times in fixture.items()}
partial_window_included = [day for day in ("day_equal", "day_late") if fixture_ready[day]]

# Exercise the reference optimizer's real-valued scenario interface with a tiny
# resource cap. q remains integer. The full reference implementation is imported
# only as the authorized baseline algorithm; this does not fit or score any model.
reference_path = ROOT / "inputs/reference/run.py"
spec = importlib.util.spec_from_file_location("r21_reference_baseline", reference_path)
reference = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(reference)
toy = SimpleNamespace(a=reference.np.array([3.0] * 96), b=reference.np.array([1.0] * 96), maxq=reference.np.array([2] * 96), cost=reference.np.array([1.0] * 96))
float_scenario = [[0.5] * 96]
float_q, float_eval = reference.optimize(toy, float_scenario, capacity=1, budget=1)

result = {
    "schema": "r21-correction-boundary-experiment/1",
    "purpose": "identity correction and interface-boundary experiment only; no candidate fit/performance and no future truth",
    "canonical_identities": {"input": input_identity, "protocol": protocol_identity, "clarification": clarification_identity},
    "original_preparation_wrong_path_finding": {
        "preserved": True,
        "original_paths_checked": ["runs/R21/inputs/input-lock.json", "runs/R21/protocol/protocol-lock.json"],
        "correction": "canonical locks are at runs/R21/input-lock.json and runs/R21/protocol-lock.json; the original absent-path finding did not indicate a missing source freeze"
    },
    "mature_evaluation_labels": {
        "cutoff": LABEL_CUTOFF.isoformat(),
        "service_date_max": HISTORY_END.isoformat(),
        "selected_unique_keys": len(by_key),
        "expected_keys": 184 * 96,
        "late_label_selection_rule": "highest revision available by cutoff; each selected version is separately checked against calibration-origin availability before residual use"
    },
    "day_level_residual_readiness": {
        "calibration_origin": ORIGIN.isoformat(),
        "unit": "one service day with all 96 coordinates",
        "source_window_length_days": 14,
        "source_origins": [x.isoformat() for x in origins],
        "forecast_window_days_total": all_window_days,
        "eligible_days_by_source_origin": eligible_by_origin,
        "eligible_day_count": sum(map(len, eligible_by_origin.values())),
        "partial_source_windows_with_at_least_one_eligible_day_and_one_unready_day": [origin for origin, days in eligible_by_origin.items() if days and len(days) < 14]
    },
    "small_boundary_experiment": {
        "equal_timestamp_arrival_is_ready": fixture_ready["day_equal"],
        "one_second_late_arrival_is_not_ready": not fixture_ready["day_late"],
        "95_of_96_is_not_ready": not fixture_ready["day_95"],
        "window_with_one_complete_day_and_one_incomplete_day_accepts_only_complete_day": partial_window_included == ["day_equal"],
        "coordinate_with_late_arrival": list(late_coord),
        "calibration_time": calibration.isoformat()
    },
    "scenario_domain_experiment": {
        "finite_nonnegative_fractional_scenario": 0.5,
        "reference_optimizer_accepts_fractional_scenario": True,
        "plan_remains_integer": bool((float_q == float_q.astype(int)).all()),
        "plan_units": int(float_q.sum()),
        "capacity": 1,
        "budget": 1,
        "solver_status": int(float_eval["status"])
    },
    "model": None,
    "tokens": None,
    "cost": None
}
assert input_identity["all_lock_matches"] and input_identity["all_original_direct_hashes_match"]
assert protocol_identity["all_lock_matches"] and protocol_identity["all_original_direct_hashes_match"]
assert clarification_identity["all_lock_matches"]
assert len(by_key) == 184 * 96
assert result["small_boundary_experiment"]["equal_timestamp_arrival_is_ready"]
assert result["small_boundary_experiment"]["one_second_late_arrival_is_not_ready"]
assert result["small_boundary_experiment"]["95_of_96_is_not_ready"]
assert result["small_boundary_experiment"]["window_with_one_complete_day_and_one_incomplete_day_accepts_only_complete_day"]
assert result["scenario_domain_experiment"]["plan_remains_integer"]
assert result["scenario_domain_experiment"]["plan_units"] <= 1
CORR.mkdir(parents=True, exist_ok=True)
(CORR / "boundary-experiment.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"output": str(CORR / "boundary-experiment.json"), "input_lock": input_identity["all_lock_matches"], "protocol_lock": protocol_identity["all_lock_matches"], "clarification_lock": clarification_identity["all_lock_matches"], "input_prior_hashes": input_identity["all_original_direct_hashes_match"], "protocol_prior_hashes": protocol_identity["all_original_direct_hashes_match"], "mature_keys": len(by_key), "eligible_residual_days": result["day_level_residual_readiness"]["eligible_day_count"], "partial_windows": result["day_level_residual_readiness"]["partial_source_windows_with_at_least_one_eligible_day_and_one_unready_day"], "boundary": result["small_boundary_experiment"], "continuous_scenario": result["scenario_domain_experiment"]}, ensure_ascii=False, indent=2))
