"""Reproduce the bounded offline demand forecast and integer allocation."""
import argparse
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def load_problem(path):
    p = json.loads(Path(path).read_text(encoding="utf-8"))
    stations = list(p["distribution"]["station_caps"])
    weeks = [r["week"] for r in p["data"]]
    if len(set(weeks)) != len(weeks) or weeks != sorted(weeks):
        raise ValueError("weeks must be unique and increasing")
    if len(p["data"]) < 4 or not stations:
        raise ValueError("need at least four weekly observations and one station")
    for s in stations:
        vals = [r[s] for r in p["data"]]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) or v < 0 for v in vals):
            raise ValueError(f"demand for {s} must be finite and nonnegative")
        for key in ("station_caps", "delivery_cost_per_unit", "unmet_prediction_penalty_per_unit"):
            v = p["distribution"][key][s]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) or v < 0:
                raise ValueError(f"{key}[{s}] must be finite and nonnegative numeric")
        if not float(p["distribution"]["station_caps"][s]).is_integer():
            raise ValueError(f"station cap for {s} must be integer")
    total = p["distribution"]["total_available_units"]
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError("total_available_units must be a nonnegative integer")
    return p, stations


def forecast(rows, stations):
    weeks = np.array([r["week"] for r in rows], dtype=float)
    out = {}
    for s in stations:
        y = np.array([r[s] for r in rows], dtype=float)
        slope, intercept = np.polyfit(weeks, y, 1)
        out[s] = max(0.0, float(slope * (weeks[-1] + 1) + intercept))
    return out


def mae(actual, predicted):
    return float(np.mean(np.abs(np.asarray(actual) - np.asarray(predicted))))


def optimize(p, stations, pred):
    d = p["distribution"]
    caps = [int(d["station_caps"][s]) for s in stations]
    total = d["total_available_units"]
    costs = [float(d["delivery_cost_per_unit"][s]) for s in stations]
    penalties = [float(d["unmet_prediction_penalty_per_unit"][s]) for s in stations]
    demands = [float(pred[s]) for s in stations]
    best = None
    feasible = 0
    # Exhaustive oracle: finite bounded integer domain, no solver tolerance.
    for xs in itertools.product(*(range(c + 1) for c in caps)):
        if sum(xs) > total:
            continue
        feasible += 1
        value = sum(c * x + q * max(r - x, 0.0) for c, q, r, x in zip(costs, penalties, demands, xs))
        if best is None or value < best[0] - 1e-12:
            best = (value, xs)
    if best is None:
        raise ValueError("allocation constraints infeasible")
    return {"allocation": dict(zip(stations, best[1])), "objective": float(best[0]), "feasible_integer_vectors_enumerated": feasible,
            "objective_components": {s: {"delivery": costs[i] * best[1][i], "unmet": penalties[i] * max(demands[i] - best[1][i], 0.0)} for i, s in enumerate(stations)}}


def run(path, outdir):
    p, stations = load_problem(path)
    rows = p["data"]
    # Rolling-origin one-step validation. Each fit sees only weeks before target.
    folds = []
    for i in range(3, len(rows)):
        train = rows[:i]
        pred = forecast(train, stations)
        for s in stations:
            y = np.array([r["week"] for r in train], dtype=float)
            vals = np.array([r[s] for r in train], dtype=float)
            slope, intercept = np.polyfit(y, vals, 1)
            target = rows[i]
            folds.append({"target_week": target["week"], "station": s, "actual": target[s],
                          "linear_trend": max(0.0, float(slope * target["week"] + intercept)),
                          "last_observation": train[-1][s]})
    lin_mae = mae([f["actual"] for f in folds], [f["linear_trend"] for f in folds])
    naive_mae = mae([f["actual"] for f in folds], [f["last_observation"] for f in folds])
    pred = forecast(rows, stations)
    allocation = optimize(p, stations, pred)
    result = {
        "case_id": p["case_id"], "units": p["units"], "source": str(Path(path)),
        "forecast": {"method": "per-station ordinary least-squares linear trend on all observed weeks; extrapolate one week; floor at zero",
                     "decision_week": int(rows[-1]["week"] + 1), "values": pred,
                     "assumptions": ["weekly indices are evenly spaced", "trend remains locally linear for one-step extrapolation", "no future observations used"]},
        "validation": {"method": "rolling-origin one-step, training begins with first 3 weeks; targets weeks 4 through 8", "fold_count": len(rows)-3,
                       "station_fold_count": len(folds), "linear_trend_mae_units_per_week": lin_mae,
                       "last_observation_baseline_mae_units_per_week": naive_mae, "folds": folds,
                       "comparison_note": "descriptive on only five origins and three stations; not an inferential superiority claim"},
        "allocation": {**allocation, "constraints": {"total_available_units": p["distribution"]["total_available_units"],
                      "station_caps": p["distribution"]["station_caps"], "integer_nonnegative": True},
                      "total_allocated": sum(allocation["allocation"].values()),
                      "predicted_unmet_units": {s: max(pred[s]-allocation["allocation"][s], 0.0) for s in stations}},
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = np.arange(len(stations)); width = 0.36
    actual = [rows[-1][s] for s in stations]
    forecasts = [pred[s] for s in stations]
    allocated = [allocation["allocation"][s] for s in stations]
    ax.bar(x-width/2, actual, width, label=f"Observed week {rows[-1]['week']}", color="#4978a8")
    ax.bar(x+width/2, forecasts, width, label=f"Forecast week {rows[-1]['week']+1}", color="#e69f00")
    ax.scatter(x+width/2, allocated, color="#b23a48", marker="D", zorder=3, label="Allocated units")
    ax.set_xticks(x, stations); ax.set_ylabel("Demand / allocation (units per week)")
    ax.set_title("Observed demand, one-week forecast, and integer allocation")
    ax.legend(frameon=False); ax.grid(axis="y", alpha=.2); fig.tight_layout()
    fig.savefig(outdir / "forecast_allocation.png", dpi=180); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run(Path(args.input), Path(args.out))


if __name__ == "__main__":
    main()
