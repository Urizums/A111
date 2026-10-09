#!/usr/bin/env python3
"""Independent, source-only reconstruction for the frozen R20 forward case.

Reads only runs/R20/forward-case/inputs and its input lock. Emits facts needed
for a later receiving review; it does not read or judge production artifacts.
"""
from __future__ import annotations
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CASE = ROOT / "runs/R20/forward-case"
INPUTS = CASE / "inputs"


def instant(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError(f"timestamp lacks timezone: {value}")
    return dt


def locked_sources() -> dict[str, str]:
    lock = json.loads((CASE / "input-lock.json").read_text(encoding="utf-8"))
    found = {}
    for item in lock["files"]:
        path = ROOT / item["path"]
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != item["size_bytes"] or digest != item["sha256"]:
            raise ValueError(f"locked input mismatch: {item['path']}")
        found[item["path"]] = digest
    return found


def read_csv(name: str) -> list[dict[str, str]]:
    with (INPUTS / "raw" / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def deduplicate_exact(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    unique = []
    seen = set()
    repeated = 0
    for row in rows:
        signature = tuple(sorted(row.items()))
        if signature in seen:
            repeated += 1
            continue
        seen.add(signature)
        unique.append(row)
    return unique, repeated


def main() -> None:
    hashes = locked_sources()
    decisions = json.loads((INPUTS / "raw/decisions.json").read_text(encoding="utf-8"))
    series = [r["series_id"] for r in read_csv("series.csv")]
    forecast_rows, duplicate_forecasts = deduplicate_exact(read_csv("forecasts.csv"))
    label_rows, duplicate_labels = deduplicate_exact(read_csv("labels.csv"))

    # Only predictions already available by their declared forecast origin can
    # instantiate the original fixed forecast. Later backfills remain visible
    # as rejected candidates and cannot replace that value.
    forecasts_by_key: dict[tuple[str, str], list[dict]] = {}
    rejected_forecasts = []
    for row in forecast_rows:
        origin = instant(row["forecast_origin"])
        available = instant(row["available_at"])
        key = (row["target_date"], row["series_id"])
        if available <= origin:
            forecasts_by_key.setdefault(key, []).append(row)
        else:
            rejected_forecasts.append({**row, "reason": "available_after_declared_forecast_origin"})

    fixed_forecasts = {}
    for key, rows in forecasts_by_key.items():
        signatures = {(r["forecast_origin"], r["prediction_units"]) for r in rows}
        if len(signatures) != 1:
            raise ValueError(f"ambiguous fixed forecast for {key}: {sorted(signatures)}")
        fixed_forecasts[key] = rows[0]

    final_by_key: dict[tuple[str, str], list[dict]] = {}
    for row in label_rows:
        final_by_key.setdefault((row["target_date"], row["series_id"]), []).append(row)

    forecast_dates = sorted({r["target_date"] for r in forecast_rows})
    origins = [instant(s) for s in decisions["origins"]]
    maturity = instant(decisions["evaluation_label_cutoff"])
    output = {
        "schema": "c13-independent-raw-reconstruction/1",
        "source_lock_verified": True,
        "input_sha256": hashes,
        "timezone": decisions["timezone"],
        "series_order": series,
        "exact_duplicate_forecast_rows_removed": duplicate_forecasts,
        "exact_duplicate_label_rows_removed": duplicate_labels,
        "post_origin_forecast_candidates_rejected": rejected_forecasts,
        "forecast_date_keys_missing_fixed_prediction": [
            {"target_date": d, "series_id": sid}
            for d in forecast_dates for sid in series
            if (d, sid) not in fixed_forecasts
        ],
        "origins": [],
    }

    for origin in origins:
        available_label_by_key: dict[tuple[str, str], dict] = {}
        for key, versions in final_by_key.items():
            arrived = [r for r in versions if instant(r["available_at"]) <= origin]
            if not arrived:
                continue
            max_revision = max(int(r["revision"]) for r in arrived)
            selected = [r for r in arrived if int(r["revision"]) == max_revision]
            values = {(r["available_at"], r["actual_units"]) for r in selected}
            if len(values) != 1:
                raise ValueError(f"conflicting available label version for {key}: {sorted(values)}")
            available_label_by_key[key] = selected[0]

        complete_vectors = []
        incomplete = []
        for date in forecast_dates:
            missing = [sid for sid in series if (date, sid) not in available_label_by_key]
            if missing:
                incomplete.append({"target_date": date, "missing_series_ids": missing})
                continue
            coordinates = []
            for sid in series:
                key = (date, sid)
                if key not in fixed_forecasts:
                    raise ValueError(f"complete label vector lacks fixed forecast: {key}")
                pred = Decimal(fixed_forecasts[key]["prediction_units"])
                label = available_label_by_key[key]
                actual = Decimal(label["actual_units"])
                coordinates.append({
                    "series_id": sid,
                    "forecast_origin": fixed_forecasts[key]["forecast_origin"],
                    "forecast_available_at": fixed_forecasts[key]["available_at"],
                    "prediction_units": str(pred),
                    "label_revision": int(label["revision"]),
                    "label_available_at": label["available_at"],
                    "actual_units": str(actual),
                    "residual_units": str(actual - pred),
                })
            complete_vectors.append({"target_date": date, "coordinates": coordinates})

        # Conservative maturity policy: a fixed evaluation version is usable
        # only after its frozen evaluation cutoff and after every selected value
        # has arrived. This intentionally may leave the pool empty at an earlier
        # decision origin; it never estimates risk from an empty set.
        mature_vectors = []
        maturity_block = origin < maturity
        if not maturity_block:
            for date in forecast_dates:
                keys = [(date, sid) for sid in series]
                selected_by_key = {}
                for key in keys:
                    versions = [r for r in final_by_key.get(key, [])
                                if instant(r["available_at"]) <= maturity]
                    if versions:
                        revision = max(int(r["revision"]) for r in versions)
                        choices = [r for r in versions if int(r["revision"]) == revision]
                        if len({(r["available_at"], r["actual_units"]) for r in choices}) != 1:
                            raise ValueError(f"conflicting evaluation version for {key}")
                        selected_by_key[key] = choices[0]
                if len(selected_by_key) != len(series):
                    continue
                if any(instant(selected_by_key[k]["available_at"]) > origin for k in keys):
                    continue
                coordinates = []
                for sid in series:
                    key = (date, sid)
                    pred = Decimal(fixed_forecasts[key]["prediction_units"])
                    label = selected_by_key[key]
                    actual = Decimal(label["actual_units"])
                    coordinates.append({
                        "series_id": sid,
                        "label_revision": int(label["revision"]),
                        "label_available_at": label["available_at"],
                        "prediction_units": str(pred),
                        "actual_units": str(actual),
                        "residual_units": str(actual - pred),
                    })
                mature_vectors.append({"target_date": date, "coordinates": coordinates})

        output["origins"].append({
            "decision_origin": origin.isoformat(),
            "visible_latest": {
                "complete_vectors": complete_vectors,
                "incomplete_dates": incomplete,
            },
            "fixed_evaluation_mature": {
                "evaluation_cutoff": maturity.isoformat(),
                "maturity_cutoff_after_decision_origin": maturity_block,
                "complete_vectors": mature_vectors,
            },
        })

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

