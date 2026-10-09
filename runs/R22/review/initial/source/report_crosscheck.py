"""Summarize independently rebuilt report metrics and source-consumer evidence."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
INITIAL = ROOT / "runs/R22/review/initial"
RESULTS = INITIAL / "rebuild-v5/results"
REPORT = ROOT / "runs/R22/execution/report-v1/REPORT.md"


def rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def select(name: str, **where: str) -> list[dict[str, str]]:
    return [row for row in rows(name) if all(row.get(key) == value for key, value in where.items())]


def main() -> None:
    report = REPORT.read_text(encoding="utf-8")
    data = {
        "overall": rows("group_overall.csv"),
        "early_late": rows("group_early_late.csv"),
        "activity": rows("group_activity.csv"),
        "activity_band": rows("group_activity_by_band.csv"),
        "store": rows("group_store.csv"),
        "item": rows("group_item.csv"),
        "combined_first_two": rows("combined_first_two.csv"),
        "paired_daily": rows("paired_daily.csv"),
        "daily_solver": rows("daily_solver.csv"),
        "origins": rows("origins.csv"),
    }
    report_mentions_340 = [line.strip() for line in report.splitlines() if "340.0" in line]
    report_claims = {
        "first_two_sample_counts": ["84", "8064"],
        "third_window_waste_text": report_mentions_340,
        "all_solver_rows": len(data["daily_solver"]),
        "solver_status_counts": {},
        "solver_gap_max": None,
        "solver_objective_bound_absdiff_max": None,
        "paired_per_origin": {},
        "empty_activity_band_rows": [],
        "report_page_markers": sum(1 for line in report.splitlines() if line.startswith("## ")),
    }
    for row in data["daily_solver"]:
        status = row["status"]
        report_claims["solver_status_counts"][status] = report_claims["solver_status_counts"].get(status, 0) + 1
    if data["daily_solver"]:
        report_claims["solver_gap_max"] = max(abs(float(r["gap"])) for r in data["daily_solver"])
        report_claims["solver_objective_bound_absdiff_max"] = max(abs(float(r["objective"]) - float(r["bound"])) for r in data["daily_solver"])
    for origin in sorted({r["origin"] for r in data["paired_daily"]}):
        subset = [r for r in data["paired_daily"] if r["origin"] == origin]
        diffs = [float(r["loss_W_minus_R"]) for r in subset]
        report_claims["paired_per_origin"][origin] = {
            "n_days": len(subset),
            "mean_W_minus_R": sum(diffs) / len(diffs),
            "min_W_minus_R": min(diffs),
            "max_W_minus_R": max(diffs),
            "R_lower": sum(x > 0 for x in diffs),
            "W_lower": sum(x < 0 for x in diffs),
            "ties": sum(x == 0 for x in diffs),
            "mean_score_W_minus_R": sum(float(r["score_W_minus_R"]) for r in subset) / len(subset),
        }
    for row in data["activity_band"]:
        if int(row["n_keys"]) == 0 or int(row["n_days"]) == 0:
            report_claims["empty_activity_band_rows"].append(row)
    print(json.dumps({"schema": "r22-report-crosscheck/1", "independent_rebuild": data, "derived_claims": report_claims,
                      "actual_model": None, "tokens": None, "cost": None}, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
