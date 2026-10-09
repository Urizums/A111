"""Independent R21 raw-input and residual-readiness audit; no model fitting."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path

ROOT = Path("runs/R21")
RAW = ROOT / "inputs/raw"
OUT = ROOT / "review/preparation/raw-audit.json"
ORIGIN = datetime.fromisoformat("2026-10-31T18:00:00")
STORES = [f"S{i:02d}" for i in range(1, 13)]
ITEMS = [f"K{i:02d}" for i in range(1, 9)]
COORDS = {(s, i) for s in STORES for i in ITEMS}


def rows(name):
    with (RAW / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dt(s):
    return datetime.fromisoformat(s)


reports = rows("demand_reports.csv")
calendar = rows("calendar.csv")
promotions = rows("promotions.csv")
weather = rows("weather.csv")
stores = rows("stores.csv")
items = rows("items.csv")

raw_files = sorted(RAW.glob("*.csv"))
input_files = [ROOT / "inputs/REQUEST.md", ROOT / "inputs/PROBLEM.md"] + raw_files + sorted((ROOT / "inputs/reference").glob("*"))
protocol_files = [ROOT / "protocol/PROTOCOL.md", ROOT / "protocol/acceptance.json"]
identity = {str(p).replace("\\", "/"): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in input_files + protocol_files}

exact_rows = Counter(tuple(r[k] for k in reports[0]) for r in reports)
revision_rows = defaultdict(list)
for r in reports:
    revision_rows[(r["service_date"], r["store_id"], r["item_id"], r["revision"])].append(r)
exact_duplicate_count = sum(n - 1 for n in exact_rows.values() if n > 1)
conflicts = []
same_version_different_publication = []
revision_time_violations = []
for key, group in revision_rows.items():
    payloads = {tuple(r[k] for k in reports[0] if k not in ("available_at",)) for r in group}
    if len(payloads) > 1:
        conflicts.append({"key": key, "rows": group})
    elif len(group) > 1 and len({r["available_at"] for r in group}) > 1:
        same_version_different_publication.append({"key": key, "available_at": sorted({r["available_at"] for r in group})})
by_demand_key = defaultdict(list)
for r in reports:
    by_demand_key[(r["service_date"], r["store_id"], r["item_id"])].append(r)
for key, group in by_demand_key.items():
    ordered = sorted(group, key=lambda r: (int(r["revision"]), dt(r["available_at"])))
    latest_by_revision = {}
    for r in ordered:
        latest_by_revision.setdefault(int(r["revision"]), r)
    revs = sorted(latest_by_revision)
    times = [dt(latest_by_revision[v]["available_at"]) for v in revs]
    if any(b < a for a, b in zip(times, times[1:])):
        revision_time_violations.append({"key": key, "revisions": revs, "available_at_by_revision": [x.isoformat() for x in times]})

dates = [date.fromisoformat(r["service_date"]) for r in calendar]
cal_by_date = {r["service_date"]: r for r in calendar}
expected_dates = [(date(2026, 5, 1) + timedelta(days=i)).isoformat() for i in range((date(2026, 10, 31) - date(2026, 5, 1)).days + 1)]
report_dates = sorted({r["service_date"] for r in reports})
calendar_gaps = sorted(set(expected_dates) - set(cal_by_date))
report_gaps = sorted(set(expected_dates) - set(report_dates))

known_keys = {(r["service_date"], r["store_id"], r["item_id"]) for r in reports}
bad_coordinates = sorted({(r["store_id"], r["item_id"]) for r in reports if (r["store_id"], r["item_id"]) not in COORDS})
bad_demand = [r for r in reports if not r["demand_units"].isdigit() or int(r["demand_units"]) < 0]

def snapshot_latest(service_day, cutoff):
    chosen = {}
    for r in reports:
        if r["service_date"] != service_day or dt(r["available_at"]) > cutoff:
            continue
        key = (r["store_id"], r["item_id"])
        old = chosen.get(key)
        if old is None or (int(r["revision"]), dt(r["available_at"])) > (int(old["revision"]), dt(old["available_at"])):
            chosen[key] = r
    return chosen

residual_origins = []
o = date(2026, 7, 8)
while o <= date(2026, 10, 14):
    residual_origins.append(datetime.combine(o, datetime.min.time()).replace(hour=18))
    o += timedelta(days=14)
readiness = []
for forecast_origin in residual_origins:
    window_start = forecast_origin.date() + timedelta(days=1)
    window_end = forecast_origin.date() + timedelta(days=14)
    for calibration_origin in residual_origins + [ORIGIN]:
        if window_end >= calibration_origin.date():
            continue
        day_status = []
        for offset in range(14):
            sd = (window_start + timedelta(days=offset)).isoformat()
            labels = snapshot_latest(sd, calibration_origin)
            missing = sorted(COORDS - set(labels))
            day_status.append({"service_date": sd, "coordinates_present": len(labels), **({"missing_coordinates": missing} if missing else {})})
        complete = all(d["coordinates_present"] == 96 for d in day_status)
        readiness.append({"forecast_origin": forecast_origin.isoformat(), "window_start": window_start.isoformat(), "window_end": window_end.isoformat(), "calibration_origin": calibration_origin.isoformat(), "all_14_days_complete_96": complete, "complete_days": sum(d["coordinates_present"] == 96 for d in day_status), "min_coordinates_on_day": min(d["coordinates_present"] for d in day_status), "day_status": day_status})

latest_at_final = {}
for r in reports:
    if dt(r["available_at"]) <= ORIGIN:
        key = (r["service_date"], r["store_id"], r["item_id"])
        old = latest_at_final.get(key)
        if old is None or (int(r["revision"]), dt(r["available_at"])) > (int(old["revision"]), dt(old["available_at"])):
            latest_at_final[key] = r

promo_future = [r for r in promotions if date.fromisoformat(r["service_date"]) > ORIGIN.date() and dt(r["announced_at"]) > ORIGIN]
weather_future = [r for r in weather if date.fromisoformat(r["service_date"]) > ORIGIN.date() and dt(r["available_at"]) > ORIGIN]

result = {
    "schema": "r21-preparation-raw-audit/1",
    "scope": "authorized raw inputs only; no model fitting or future truth",
    "identities": identity,
    "expected_lock_files": {"runs/R21/inputs/input-lock.json": (ROOT / "inputs/input-lock.json").exists(), "runs/R21/protocol/protocol-lock.json": (ROOT / "protocol/protocol-lock.json").exists()},
    "row_counts": {"demand_reports": len(reports), "calendar": len(calendar), "promotions": len(promotions), "weather": len(weather), "stores": len(stores), "items": len(items)},
    "demand_report_columns": list(reports[0]) if reports else [],
    "coverage": {"calendar_start": min(dates).isoformat(), "calendar_end": max(dates).isoformat(), "calendar_rows": len(calendar), "expected_history_days": len(expected_dates), "calendar_missing_history_days": calendar_gaps, "report_missing_history_dates": report_gaps, "unique_observed_demand_keys": len(known_keys), "expected_history_grid_keys": len(expected_dates) * 96, "unknown_store_item_coordinates": bad_coordinates, "invalid_or_negative_demand_rows": bad_demand},
    "duplicate_revision_audit": {"exact_duplicate_rows_beyond_first": exact_duplicate_count, "unique_date_coordinate_revision_groups": len(revision_rows), "same_revision_conflicts": conflicts, "same_payload_revision_with_distinct_publication_times": same_version_different_publication, "revision_publication_time_order_violations": revision_time_violations},
    "final_origin_asof": {"origin": ORIGIN.isoformat(), "visible_demand_report_rows": sum(dt(r["available_at"]) <= ORIGIN for r in reports), "latest_visible_labels": len(latest_at_final), "visible_label_gaps_from_expected_history_grid": len(expected_dates) * 96 - len(latest_at_final), "late_historical_labels_by_service_date": {d: 96 - sum(1 for k in latest_at_final if k[0] == d) for d in expected_dates if sum(1 for k in latest_at_final if k[0] == d) != 96}, "future_promotion_rows_announced_after_origin": len(promo_future), "future_promotion_late_dates": sorted({r["service_date"] for r in promo_future}), "future_weather_rows_available_after_origin": len(weather_future), "future_weather_late_dates": sorted({r["service_date"] for r in weather_future})},
    "residual_group_readiness": readiness,
    "readiness_summary": {"planned_residual_origins": [x.isoformat() for x in residual_origins], "eligible_groups_at_final_origin": [x["forecast_origin"] for x in readiness if x["calibration_origin"] == ORIGIN.isoformat() and x["all_14_days_complete_96"]], "ineligible_groups_at_final_origin": [{"forecast_origin": x["forecast_origin"], "complete_days": x["complete_days"], "min_coordinates_on_day": x["min_coordinates_on_day"]} for x in readiness if x["calibration_origin"] == ORIGIN.isoformat() and not x["all_14_days_complete_96"]]},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"audit": str(OUT), "rows": result["row_counts"], "coverage": result["coverage"], "duplicates": result["duplicate_revision_audit"], "readiness": result["readiness_summary"], "locks": result["expected_lock_files"]}, ensure_ascii=False, indent=2))
