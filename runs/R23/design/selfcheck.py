"""Author-side acceptance-surface checks for the bounded R23 probe only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DESIGN = ROOT / "runs/R23/design"
OUT = DESIGN / "probe-output-v2"
RAW = ROOT / "runs/R21/inputs/raw"
KEY = ["service_date", "store_id", "item_id"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    pred = pd.read_csv(OUT / "predictions.csv")
    plan = pd.read_csv(OUT / "replenishment.csv")
    scenarios = pd.read_csv(OUT / "scenarios.csv")
    feature = pd.read_csv(OUT / "feature_lineage.csv")
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    items = pd.read_csv(RAW / "items.csv").set_index("item_id")
    lock = json.loads((ROOT / "runs/R21/input-lock.json").read_text(encoding="utf-8"))
    expected_hash = {Path(x["path"]).name: x["sha256"] for x in lock["files"] if x["path"].startswith("runs/R21/inputs/raw/")}
    for name, want in expected_hash.items():
        assert digest(RAW / name) == want, f"raw hash differs: {name}"
    assert len(pred) == len(plan) == 96
    assert not pred.duplicated(KEY).any() and not plan.duplicated(KEY).any()
    assert pred[KEY].equals(plan[KEY])
    assert set(pred.service_date) == {"2026-11-01"}
    assert set(pred.method_id) == set(plan.method_id) == {"shared_ridge10_probe"}
    nums = pred[["demand_point_units", "lower90_units", "upper90_units", "interval_level"]].to_numpy(float)
    assert np.isfinite(nums).all() and (nums[:, :3] >= 0).all()
    assert (pred.lower90_units <= pred.upper90_units).all() and (pred.interval_level == 0.9).all()
    assert len(scenarios) == 14 * 96
    assert not scenarios.duplicated(["scenario_id", *KEY]).any()
    assert scenarios.groupby("scenario_id").size().eq(96).all()
    scenario_weights = scenarios.groupby("scenario_id").weight.agg(["min", "max"])
    assert np.allclose(scenario_weights["min"], scenario_weights["max"])
    assert abs(float(scenario_weights["min"].sum()) - 1.0) < 1e-8
    origin = pd.Timestamp(summary["decision_origin"]).tz_localize("Asia/Shanghai")
    labels = pd.to_datetime(scenarios.label_available_at, utc=True).dt.tz_convert("Asia/Shanghai")
    assert labels.le(origin).all(), "late label entered scenario set"
    announced = pd.to_datetime(feature.announced_at.dropna(), utc=True).dt.tz_convert("Asia/Shanghai")
    assert announced.le(origin).all(), "future promotion announcement entered features"
    assert len(feature) == 96 and not feature.duplicated(KEY).any()
    q = plan.q_units.to_numpy()
    assert np.isfinite(q).all() and (q >= 0).all() and (q == np.floor(q)).all()
    maxq = np.array([items.loc[k, "daily_max_units"] for k in plan.item_id], dtype=int)
    cost = np.array([items.loc[k, "procurement_yuan"] for k in plan.item_id], dtype=float)
    short = np.array([items.loc[k, "shortage_yuan"] for k in plan.item_id], dtype=float)
    waste = np.array([items.loc[k, "waste_yuan"] for k in plan.item_id], dtype=float)
    assert (q <= maxq).all() and int(q.sum()) <= 1600 and float(q @ cost) <= 6000
    assert int(q.sum()) == summary["daily_q_units"]
    assert abs(float(q @ cost) - summary["daily_procurement_yuan"]) < 1e-8
    wide = scenarios.pivot(index="scenario_id", columns=KEY, values="demand_units")
    assert wide.shape == (14, 96)
    values = wide.to_numpy(dtype=float)
    objective = float((np.maximum(values - q, 0) * short + np.maximum(q - values, 0) * waste).sum(axis=1).mean())
    assert abs(objective - summary["solver"]["objective_yuan"]) < 1e-6
    lo = np.round(np.quantile(values, 0.05, axis=0), 10)
    hi = np.round(np.quantile(values, 0.95, axis=0), 10)
    assert np.allclose(lo, pred.lower90_units.to_numpy(), atol=1e-9)
    assert np.allclose(hi, pred.upper90_units.to_numpy(), atol=1e-9)
    report = {
        "scope": "author self-check of one-date probe only",
        "raw_hashes_match_input_lock": True,
        "prediction_and_plan_rows": 96,
        "scenario_vectors": 14,
        "timestamp_boundaries": "scenario labels and used promotions available by decision origin",
        "daily_quantity": int(q.sum()),
        "daily_procurement_yuan": float(q @ cost),
        "recomputed_scenario_loss_yuan": objective,
        "independent_acceptance": "pending",
        "production_or_nominal_coverage_claim": False,
    }
    (DESIGN / "selfcheck.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
