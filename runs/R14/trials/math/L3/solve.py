#!/usr/bin/env python3
"""Reproducible forecast and exact bounded integer allocation for math-level-3."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


STATIONS = ("A", "B", "C")
ROOT = Path(__file__).resolve().parents[5]
DEFAULT_INPUT = ROOT / "runs/R14/cases/math/problem.json"


def load_problem(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        p = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"input is not valid UTF-8 JSON: {exc}") from exc
    if p.get("case_id") != "offline-demand-allocation-01":
        raise ValueError("unexpected case_id")
    data = p.get("data")
    if not isinstance(data, list) or len(data) < 4:
        raise ValueError("data must contain at least four weekly rows")
    weeks = []
    for expected, row in enumerate(data, 1):
        if not isinstance(row, dict) or row.get("week") != expected:
            raise ValueError("weeks must be unique consecutive integers starting at 1")
        vals = []
        for s in STATIONS:
            v = row.get(s)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) or v < 0:
                raise ValueError(f"demand {s} at week {expected} must be a finite nonnegative number")
            vals.append(float(v))
        weeks.append(vals)
    dist = p.get("distribution")
    if not isinstance(dist, dict):
        raise ValueError("distribution must be an object")
    total = dist.get("total_available_units")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError("total_available_units must be a nonnegative integer")
    for field in ("station_caps", "delivery_cost_per_unit", "unmet_prediction_penalty_per_unit"):
        values = dist.get(field)
        if not isinstance(values, dict) or set(values) != set(STATIONS):
            raise ValueError(f"{field} must contain exactly A, B, C")
        for s, v in values.items():
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise ValueError(f"{field}.{s} must be a nonnegative integer")
    return p


def forecast(history: np.ndarray) -> np.ndarray:
    x = np.arange(1, len(history) + 1, dtype=float)
    return np.array([np.polyval(np.polyfit(x, history[:, j], 1), len(history) + 1) for j in range(3)])


def objective(x: tuple[int, ...], pred: np.ndarray, costs: list[int], penalties: list[int]) -> float:
    return float(sum(costs[i] * x[i] + penalties[i] * max(float(pred[i]) - x[i], 0.0) for i in range(3)))


def solve(p: dict, input_bytes: bytes) -> dict:
    history = np.array([[float(row[s]) for s in STATIONS] for row in p["data"]], dtype=float)
    dist = p["distribution"]
    caps = [dist["station_caps"][s] for s in STATIONS]
    costs = [dist["delivery_cost_per_unit"][s] for s in STATIONS]
    penalties = [dist["unmet_prediction_penalty_per_unit"][s] for s in STATIONS]

    pred = forecast(history)
    validation = []
    for target_idx in range(4, len(history)):
        observed_history = history[:target_idx]
        predicted = forecast(observed_history)
        naive = observed_history[-1]
        validation.append({
            "target_week": target_idx + 1,
            "actual": dict(zip(STATIONS, history[target_idx].tolist())),
            "linear_trend": dict(zip(STATIONS, predicted.tolist())),
            "last_observation_baseline": dict(zip(STATIONS, naive.tolist())),
            "history_ends_at_week": target_idx,
        })
    mae = {}
    baseline_mae = {}
    for j, s in enumerate(STATIONS):
        mae[s] = float(np.mean([abs(r["linear_trend"][s] - r["actual"][s]) for r in validation]))
        baseline_mae[s] = float(np.mean([abs(r["last_observation_baseline"][s] - r["actual"][s]) for r in validation]))

    feasible_count = 0
    best = None
    best_value = float("inf")
    for x in itertools.product(*(range(c + 1) for c in caps)):
        if sum(x) > dist["total_available_units"]:
            continue
        feasible_count += 1
        val = objective(x, pred, costs, penalties)
        if val < best_value - 1e-10:
            best, best_value = x, val
    assert best is not None
    alloc = dict(zip(STATIONS, best))
    shortfall = {s: max(float(pred[j]) - best[j], 0.0) for j, s in enumerate(STATIONS)}
    delivery_cost = sum(costs[j] * best[j] for j in range(3))
    penalty_cost = sum(penalties[j] * shortfall[s] for j, s in enumerate(STATIONS))
    recomputed = float(delivery_cost + penalty_cost)

    outdir = Path(__file__).resolve().parent
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    colors = {"A": "#1769aa", "B": "#e07a18", "C": "#238636"}
    xhist = np.arange(1, len(history) + 1)
    for j, s in enumerate(STATIONS):
        axes[0].plot(xhist, history[:, j], "o-", color=colors[s], label=f"{s} observed")
        axes[0].scatter([len(history) + 1], [pred[j]], marker="D", color=colors[s])
        axes[0].plot([len(history), len(history) + 1], [history[-1, j], pred[j]], "--", color=colors[s], alpha=.65)
    axes[0].set(title="History and week 9 trend forecast", xlabel="Week", ylabel="Demand (units/week)", xticks=list(range(1, len(history) + 2)))
    axes[0].legend(frameon=False, ncol=2)
    idx = np.arange(3)
    axes[1].bar(idx - .18, pred, width=.36, label="Predicted demand", color="#8cbce6")
    axes[1].bar(idx + .18, [alloc[s] for s in STATIONS], width=.36, label="Allocated", color="#315a7d")
    axes[1].set(title="Week 9 allocation", xlabel="Station", ylabel="Units for week 9", xticks=idx, xticklabels=STATIONS)
    axes[1].legend(frameon=False)
    fig.suptitle("Offline practice data: source runs/R14/cases/math/problem.json")
    fig.savefig(outdir / "forecast_allocation.png", dpi=180)
    plt.close(fig)

    return {
        "case_id": p["case_id"],
        "input_path": "runs/R14/cases/math/problem.json",
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "units": p["units"],
        "prediction_method": "Per-station ordinary least-squares linear trend on weeks 1-8; no future actual values used.",
        "predictions_week9": dict(zip(STATIONS, pred.tolist())),
        "validation": {
            "design": "expanding-window one-step-ahead; train weeks 1-4 through 1-7, target weeks 5-8; same folds for both methods",
            "folds": validation,
            "mae_units_per_week": {"linear_trend": mae, "last_observation_baseline": baseline_mae},
            "aggregate_mae": {"linear_trend": float(np.mean(list(mae.values()))), "last_observation_baseline": float(np.mean(list(baseline_mae.values())))},
            "limitation": "Four temporally ordered folds from one short synthetic practice series; descriptive only, no uncertainty or generalization claim. The week-9 forecast is refit using all eight observed weeks.",
        },
        "allocation": alloc,
        "allocation_total_units": sum(best),
        "station_caps_units": dict(zip(STATIONS, caps)),
        "total_available_units": dist["total_available_units"],
        "shortfall_units": shortfall,
        "objective_components_cny": {"delivery": int(delivery_cost), "unmet_prediction_penalty": float(penalty_cost)},
        "objective_cny": recomputed,
        "objective_formula": "sum_i(cost_i*x_i + penalty_i*max(pred_i-x_i,0))",
        "optimization_evidence": {"method": "Exhaustive enumeration of all bounded integer triples satisfying sum(x)<=60; exact for the supplied caps and objective.", "feasible_integer_allocations_evaluated": feasible_count, "optimality_claim_scope": "global optimum over this finite feasible set, with fixed forecast inputs"},
        "checks": {
            "integer_nonnegative": all(isinstance(x, int) and x >= 0 for x in best),
            "within_caps": all(best[i] <= caps[i] for i in range(3)),
            "within_stock": sum(best) <= dist["total_available_units"],
            "objective_recomputed_from_components": abs(recomputed - objective(best, pred, costs, penalties)) < 1e-9,
        },
        "figure": "forecast_allocation.png",
        "figure_source": "Generated from this run's computed history, forecasts and allocation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "results.json")
    args = parser.parse_args()
    try:
        p = load_problem(args.input)
        result = solve(p, args.input.read_bytes())
    except (ValueError, OSError) as exc:
        print(f"INPUT_REJECTED: {exc}", file=sys.stderr)
        return 2
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"predictions_week9": result["predictions_week9"], "allocation": result["allocation"], "objective_cny": result["objective_cny"], "validation": result["validation"]["aggregate_mae"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
