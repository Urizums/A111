#!/usr/bin/env python3
"""Reproduce the bounded offline demand-forecast and allocation exercise."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def read_problem(path):
    problem = json.loads(Path(path).read_text(encoding="utf-8"))
    stations = ["A", "B", "C"]
    rows = problem["data"]
    weeks = [row["week"] for row in rows]
    if weeks != list(range(1, len(rows) + 1)):
        raise ValueError("weeks must be unique, ordered, and contiguous from 1")
    if len(rows) < 4:
        raise ValueError("at least four chronological observations are required")
    for row in rows:
        if set(row) != {"week", *stations}:
            raise ValueError("each row must contain week and exactly stations A, B, C")
        for station in stations:
            value = row[station]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or value < 0:
                raise ValueError(f"demand {station} must be a finite nonnegative number")
    dist = problem["distribution"]
    for key in ("station_caps", "delivery_cost_per_unit", "unmet_prediction_penalty_per_unit"):
        if set(dist[key]) != set(stations):
            raise ValueError(f"{key} must define exactly A, B, C")
        for station, value in dist[key].items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or value < 0:
                raise ValueError(f"{key}.{station} must be finite and nonnegative")
    if isinstance(dist["total_available_units"], bool) or not isinstance(dist["total_available_units"], int) or dist["total_available_units"] < 0:
        raise ValueError("total_available_units must be a nonnegative integer")
    if any(not isinstance(dist["station_caps"][s], int) for s in stations):
        raise ValueError("station caps must be integer units")
    return problem


def predict(history, station, method):
    x = np.arange(1, len(history) + 1, dtype=float)
    y = np.array([row[station] for row in history], dtype=float)
    if method == "last_value":
        return float(y[-1])
    slope, intercept = np.polyfit(x, y, 1)
    return float(intercept + slope * (len(history) + 1))


def objective(allocation, prediction, dist, stations):
    return float(sum(dist["delivery_cost_per_unit"][s] * allocation[s]
                     + dist["unmet_prediction_penalty_per_unit"][s]
                     * max(prediction[s] - allocation[s], 0.0) for s in stations))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--figure", type=Path, required=True)
    args = parser.parse_args()
    problem = read_problem(args.problem)
    stations = ["A", "B", "C"]
    history = problem["data"]
    dist = problem["distribution"]

    audit = {
        "row_count": len(history), "stations": stations,
        "week_sequence": [row["week"] for row in history],
        "missing_cells": 0, "duplicate_weeks": 0,
        "numeric_finite_nonnegative_demand": True,
        "unit_from_source": problem["units"]["demand"],
        "per_station_min": {s: min(r[s] for r in history) for s in stations},
        "per_station_max": {s: max(r[s] for r in history) for s in stations},
        "limitations": "Only eight supplied observations; no external source, seasonality, stockout, or measurement-error metadata."
    }
    validation = {"design": "expanding-window one-step-ahead; each forecast uses only earlier weeks",
                  "origins_predicting": list(range(4, len(history) + 1)), "n_forecasts": {}, "methods": {}}
    for method in ("last_value", "linear_trend"):
        errors = {s: [] for s in stations}
        for target_week in range(4, len(history) + 1):
            train = history[:target_week - 1]
            actual = history[target_week - 1]
            for s in stations:
                errors[s].append(predict(train, s, method) - actual[s])
        flat = [abs(e) for values in errors.values() for e in values]
        validation["methods"][method] = {
            "mae_units_per_week": float(np.mean(flat)),
            "station_mae": {s: float(np.mean(np.abs(errors[s]))) for s in stations},
            "signed_errors": errors,
        }
        validation["n_forecasts"][method] = len(flat)
    selected = min(validation["methods"], key=lambda m: (validation["methods"][m]["mae_units_per_week"], m != "last_value"))
    forecasts = {s: max(0.0, predict(history, s, selected)) for s in stations}

    ranges = [range(min(dist["station_caps"][s], dist["total_available_units"]) + 1) for s in stations]
    feasible = []
    for values in itertools.product(*ranges):
        if sum(values) <= dist["total_available_units"]:
            x = dict(zip(stations, values))
            feasible.append((objective(x, forecasts, dist, stations), values))
    best_value = min(value for value, _ in feasible)
    best = min(values for value, values in feasible if abs(value - best_value) <= 1e-10)
    allocation = dict(zip(stations, best))
    result = {
        "case_id": problem["case_id"],
        "source": {"path": str(args.problem), "sha256": hashlib.sha256(args.problem.read_bytes()).hexdigest()},
        "units": problem["units"], "data_audit": audit,
        "forecast": {"selected_method": selected, "predictions_units_per_week": forecasts,
                     "selection_rule": "lowest pooled rolling-origin MAE; tie favors last_value",
                     "validation": validation},
        "allocation": {"week": 9, "integer_units": allocation,
                       "total_units": sum(allocation.values()),
                       "caps": dist["station_caps"], "available_units": dist["total_available_units"],
                       "objective_cny": objective(allocation, forecasts, dist, stations),
                       "objective_terms": {s: {"delivery": dist["delivery_cost_per_unit"][s] * allocation[s],
                                                "unmet": dist["unmet_prediction_penalty_per_unit"][s] * max(forecasts[s] - allocation[s], 0)} for s in stations},
                       "feasible_allocation_count": len(feasible),
                       "optimality_evidence": "Exhaustively enumerated every integer vector within each cap and total-stock limit; minimum objective selected over the full feasible set.",
                       "minimum_objective_gap_to_next_distinct": min((v - best_value for v, _ in feasible if v > best_value + 1e-10), default=None)},
        "interpretation_limits": ["Predictions are conditional on a short synthetic history and chosen rolling MAE rule.",
                                  "Allocation optimizes supplied forecast penalties and costs; these parameters are not empirically calibrated.",
                                  "No actual week-9 demand is supplied, so realized service or cost cannot be evaluated."]
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.figure.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    weeks = [r["week"] for r in history]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    colors = {"A": "#2667a8", "B": "#dd8452", "C": "#3a923a"}
    for s in stations:
        values = [r[s] for r in history]
        ax.plot(weeks, values, "o-", color=colors[s], label=f"{s} observed")
        ax.plot([8, 9], [values[-1], forecasts[s]], "--", color=colors[s], alpha=0.8)
        ax.scatter([9], [forecasts[s]], marker="s", color=colors[s])
        ax.scatter([9], [allocation[s]], marker="x", s=75, color=colors[s])
    ax.set(title="Weekly demand, week 9 forecast and allocation", xlabel="Week",
           ylabel="Demand / forecast (units/week); week-9 allocation (units)")
    ax.set_xticks(range(1, 10)); ax.grid(alpha=0.25)
    ax.plot([], [], "ks", label="Week 9 forecast")
    ax.plot([], [], "kx", label="Week 9 allocation")
    ax.legend(ncol=2, frameon=False)
    fig.tight_layout(); fig.savefig(args.figure, dpi=160); plt.close(fig)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"INPUT REJECTED: {exc}")
