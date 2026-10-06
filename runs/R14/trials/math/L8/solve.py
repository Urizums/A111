"""Reproduce the bounded offline demand forecast and integer allocation."""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite numeric value; got {value!r}")
    return float(value)


def load_problem(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = obj.get("data")
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError("data must contain at least two weekly rows")
    stations = ["A", "B", "C"]
    weeks = []
    values = {s: [] for s in stations}
    for index, row in enumerate(rows):
        week = finite_number(row.get("week"), f"data[{index}].week")
        if week != int(week) or (weeks and week <= weeks[-1]):
            raise ValueError("week values must be strictly increasing integers")
        weeks.append(int(week))
        for s in stations:
            values[s].append(finite_number(row.get(s), f"data[{index}].{s}"))
    dist = obj["distribution"]
    total = finite_number(dist["total_available_units"], "total_available_units")
    if total != int(total) or total < 0:
        raise ValueError("total_available_units must be a nonnegative integer")
    caps, cost, penalty = {}, {}, {}
    for s in stations:
        cap = finite_number(dist["station_caps"][s], f"station_caps.{s}")
        c = finite_number(dist["delivery_cost_per_unit"][s], f"delivery_cost_per_unit.{s}")
        p = finite_number(dist["unmet_prediction_penalty_per_unit"][s], f"unmet_prediction_penalty_per_unit.{s}")
        if cap != int(cap) or cap < 0 or c < 0 or p < 0:
            raise ValueError(f"invalid cap/cost/penalty for station {s}")
        caps[s], cost[s], penalty[s] = int(cap), c, p
    return obj, weeks, values, int(total), caps, cost, penalty


def linear_predict(xs, ys, x):
    xm, ym = sum(xs) / len(xs), sum(ys) / len(ys)
    den = sum((a - xm) ** 2 for a in xs)
    slope = sum((a - xm) * (b - ym) for a, b in zip(xs, ys)) / den
    return ym + slope * (x - xm)


def solve(path, outdir):
    problem, weeks, data, stock, caps, costs, penalties = load_problem(path)
    stations = list(data)
    forecasts, validation = {}, {}
    for s in stations:
        forecasts[s] = linear_predict(weeks, data[s], weeks[-1] + 1)
        rows = []
        # Expanding-window one-step forecasts: only earlier observations fit each point.
        for j in range(3, len(weeks)):
            actual = data[s][j]
            trend = linear_predict(weeks[:j], data[s][:j], weeks[j])
            naive = data[s][j - 1]
            rows.append({"week": weeks[j], "actual": actual, "linear_trend": trend,
                         "last_value": naive, "linear_abs_error": abs(actual - trend),
                         "last_value_abs_error": abs(actual - naive)})
        validation[s] = {
            "n_one_step_origins": len(rows), "origins": rows,
            "linear_trend_mae": sum(r["linear_abs_error"] for r in rows) / len(rows),
            "last_value_mae": sum(r["last_value_abs_error"] for r in rows) / len(rows),
        }
    # Exhaustive enumeration is an exact oracle for this small bounded instance.
    best_obj, best_x, feasible_count = float("inf"), None, 0
    for alloc in itertools.product(*(range(caps[s] + 1) for s in stations)):
        if sum(alloc) > stock:
            continue
        feasible_count += 1
        obj = sum(costs[s] * x + penalties[s] * max(forecasts[s] - x, 0)
                  for s, x in zip(stations, alloc))
        if obj < best_obj:
            best_obj, best_x = obj, alloc
    allocation = dict(zip(stations, best_x))
    breakdown = {s: {"delivered_cost_CNY": costs[s] * allocation[s],
                     "unmet_units": max(forecasts[s] - allocation[s], 0),
                     "unmet_penalty_CNY": penalties[s] * max(forecasts[s] - allocation[s], 0)}
                 for s in stations}
    check_objective = sum(v["delivered_cost_CNY"] + v["unmet_penalty_CNY"] for v in breakdown.values())
    result = {
        "case_id": problem["case_id"], "status": "computed; producer self-check only",
        "units": problem["units"], "history_weeks": weeks,
        "data_audit": {"rows": len(weeks), "stations": stations, "missing": 0,
                       "duplicate_weeks": 0, "non_numeric_or_non_finite": 0,
                       "raw_values_used_without_imputation": True},
        "forecast_method": "ordinary least-squares linear trend on all observed weeks; extrapolate one week",
        "forecast_assumptions": ["trend remains locally linear for one step", "observations are comparable weekly demand"],
        "predictions_units_per_week": forecasts,
        "validation": {"design": "expanding-window one-step origins at weeks 4–8; fit uses only earlier weeks",
                       "selection_note": "small in-sample history; no held-out future beyond supplied weeks",
                       "by_station": validation},
        "allocation": allocation, "total_available_units": stock, "station_caps": caps,
        "total_allocated_units": sum(allocation.values()), "objective_CNY": check_objective,
        "objective_formula": "sum(cost_i*x_i + penalty_i*max(pred_i-x_i,0))",
        "objective_breakdown": breakdown, "feasibility": {
            "all_nonnegative_integers": all(isinstance(x, int) and x >= 0 for x in allocation.values()),
            "within_station_caps": all(allocation[s] <= caps[s] for s in stations),
            "within_total_stock": sum(allocation.values()) <= stock,
            "objective_independent_recalculation_matches": math.isclose(best_obj, check_objective),
            "enumerated_feasible_allocations": feasible_count,
            "optimality_evidence": "all integer allocations within caps and total stock enumerated; exact for stated objective and input"},
        "limitations": ["Forecast error estimates use only five short expanding-window origins.",
                        "Predictions are fractional expected demand; no integer rounding is needed in the objective.",
                        "Objective assumes stated linear costs/penalties and no cross-station effects.",
                        "No real contest rules, leaderboard, awards, or general performance claims were assessed."]
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    colors = {"A": "#2369bd", "B": "#e18727", "C": "#3b8c5a"}
    for s in stations:
        axes[0].plot(weeks, data[s], marker="o", color=colors[s], label=f"{s} observed")
        axes[0].scatter([weeks[-1] + 1], [forecasts[s]], marker="D", color=colors[s], label=f"{s} forecast")
    axes[0].set(title="Weekly demand and week 9 forecast", xlabel="Week", ylabel="Demand (units/week)")
    axes[0].grid(alpha=.25); axes[0].legend(ncol=2, fontsize=8)
    axes[1].bar(stations, [forecasts[s] for s in stations], color="#b9cbe0", label="Predicted demand")
    axes[1].bar(stations, [allocation[s] for s in stations], color="#2875b9", label="Allocated")
    axes[1].set(title=f"Week 9 allocation (objective ¥{check_objective:.2f})", xlabel="Station", ylabel="Units")
    axes[1].legend(); axes[1].grid(axis="y", alpha=.25)
    fig.suptitle("Offline practice case; source: supplied problem.json")
    fig.tight_layout()
    fig.savefig(outdir / "forecast_allocation.png", dpi=160)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    try:
        solve(args.problem, Path(args.outdir))
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
