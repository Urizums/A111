"""Bounded R23 workflow probe: one 96-pair forecast day and constrained plan.

This is a design-domain demonstration, not the production runner or a quality
evaluation. It adapts only the frozen shared_ridge10 baseline definition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csr_matrix
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[3]
KEY = ["service_date", "store_id", "item_id"]
TABLES = ["demand_reports", "stores", "items", "calendar", "promotions", "weather"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs(raw: Path) -> dict:
    t = {n: pd.read_csv(raw / f"{n}.csv") for n in TABLES}
    for name in ["demand_reports", "promotions", "weather"]:
        for col in ["available_at", "announced_at"]:
            if col in t[name]:
                t[name][col] = pd.to_datetime(
                    t[name][col], format="%Y-%m-%dT%H:%M:%S", errors="raise"
                ).dt.tz_localize("Asia/Shanghai")
    t["decision"] = json.loads((raw / "decision.json").read_text(encoding="utf-8"))
    return t


def snapshot(t: dict, origin: str) -> pd.DataFrame:
    o = pd.Timestamp(origin).tz_localize("Asia/Shanghai")
    r = t["demand_reports"]
    r = r[r.available_at <= o].sort_values(KEY + ["revision"])
    r = r.drop_duplicates(KEY, keep="last")
    r = r[r.service_date < o.strftime("%Y-%m-%d")].sort_values(KEY).copy()
    if r.empty or not r.available_at.le(o).all():
        raise ValueError("empty or future-available training snapshot")
    return r


def feature_frame(t: dict, keys: pd.DataFrame, origin: str, train: pd.DataFrame) -> pd.DataFrame:
    o = pd.Timestamp(origin).tz_localize("Asia/Shanghai")
    p = t["promotions"]
    p = p[p.announced_at <= o].sort_values("announced_at").drop_duplicates(KEY, keep="last")
    x = keys.merge(t["calendar"], on="service_date", validate="many_to_one")
    x = x.merge(t["stores"], on="store_id", validate="many_to_one")
    x = x.merge(p[KEY + ["discount_fraction", "announced_at"]], on=KEY, how="left", validate="one_to_one")
    x["promo_known"] = x.discount_fraction.notna().astype(int)
    recent = train[train.service_date >= (o - pd.Timedelta(days=56)).strftime("%Y-%m-%d")]
    recent = recent[KEY].merge(p[KEY + ["discount_fraction"]], on=KEY, validate="one_to_one")
    impute = recent.groupby("item_id").discount_fraction.mean()
    x["discount_fraction"] = x.discount_fraction.fillna(x.item_id.map(impute)).fillna(0.0)
    x["time30"] = (pd.to_datetime(x.service_date) - pd.Timestamp("2026-05-01")).dt.days / 30.0
    x["origin"] = o.isoformat()
    if len(x) != len(keys) or x.duplicated(KEY).any():
        raise ValueError("feature join changed key cardinality")
    if not x.announced_at.dropna().le(o).all():
        raise ValueError("future promotion announcement leaked")
    return x


def matrix(x: pd.DataFrame) -> np.ndarray:
    s = x.store_id.str[1:].astype(int).to_numpy() - 1
    k = x.item_id.str[1:].astype(int).to_numpy() - 1
    a = np.zeros((len(x), 169), dtype=float)
    i = np.arange(len(x))
    a[i, s * 8 + k] = 1.0
    a[i, 96 + k * 7 + x.weekday_monday_zero.to_numpy(dtype=int)] = 1.0
    a[i, 152 + k] = x.time30.to_numpy()
    a[i, 160 + k] = x.discount_fraction.to_numpy()
    a[:, 168] = x.holiday.to_numpy() * 0.3
    return a


def predict(t: dict, origin: str, dates: list[str]) -> tuple[np.ndarray, pd.DataFrame]:
    train = snapshot(t, origin)
    train_x = feature_frame(t, train[KEY], origin, train)
    future_keys = pd.DataFrame(
        [(d, s, k) for d in dates for s in sorted(t["stores"].store_id) for k in sorted(t["items"].item_id)],
        columns=KEY,
    )
    future_x = feature_frame(t, future_keys, origin, train)
    model = Ridge(alpha=10, fit_intercept=False, solver="cholesky")
    model.fit(matrix(train_x), train.demand_units.to_numpy(dtype=float))
    point = np.maximum(model.predict(matrix(future_x)), 0).reshape(len(dates), 96)
    return point, future_x


def optimize(t: dict, scenarios: np.ndarray) -> tuple[np.ndarray, dict]:
    items = t["items"].set_index("item_id")
    pairs = [(s, k) for s in sorted(t["stores"].store_id) for k in sorted(t["items"].item_id)]
    cost = np.array([items.loc[k, "procurement_yuan"] for _, k in pairs], dtype=float)
    short = np.array([items.loc[k, "shortage_yuan"] for _, k in pairs], dtype=float)
    waste = np.array([items.loc[k, "waste_yuan"] for _, k in pairs], dtype=float)
    maxq = np.array([items.loc[k, "daily_max_units"] for _, k in pairs], dtype=int)
    if scenarios.ndim != 2 or scenarios.shape[1] != 96 or not np.isfinite(scenarios).all() or (scenarios < 0).any():
        raise ValueError("scenario matrix must be finite, nonnegative, and 96 columns")
    q_grid = np.arange(int(maxq.max()) + 1)
    mean_loss = (
        np.maximum(scenarios[:, :, None] - q_grid, 0) * short[None, :, None]
        + np.maximum(q_grid - scenarios[:, :, None], 0) * waste[None, :, None]
    ).mean(axis=0)
    gain = mean_loss[:, :-1] - mean_loss[:, 1:]
    ij = np.array([(i, j) for i in range(96) for j in range(maxq[i]) if gain[i, j] > 1e-10], dtype=int)
    if len(ij) == 0:
        q = np.zeros(96, dtype=int)
        return q, {"objective_yuan": float(mean_loss[:, 0].sum()), "status": "zero marginal gain"}
    c = -gain[ij[:, 0], ij[:, 1]]
    a = csr_matrix(np.vstack([np.ones(len(ij)), cost[ij[:, 0]]]))
    result = milp(
        c,
        integrality=np.ones(len(c)),
        bounds=Bounds(0, 1),
        constraints=LinearConstraint(a, [-np.inf, -np.inf], [1600, 6000]),
        options={"mip_rel_gap": 1e-9},
    )
    if result.x is None:
        raise RuntimeError(f"optimizer failed: {result.message}")
    q = np.bincount(ij[:, 0], weights=np.rint(result.x), minlength=96).astype(int)
    if (q < 0).any() or (q > maxq).any() or q.sum() > 1600 or float(q @ cost) > 6000:
        raise AssertionError("plan violates original daily constraints")
    return q, {"objective_yuan": float(mean_loss[np.arange(96), q].sum()), "status": str(result.message), "gap": float(result.mip_gap)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    raw = ROOT / "runs/R21/inputs/raw"
    t = load_inputs(raw)
    origin = t["decision"]["origin"]
    hist_origin = "2026-10-14T18:00:00"
    hist_dates = pd.date_range("2026-10-15", periods=14).strftime("%Y-%m-%d").tolist()
    hist_point, hist_features = predict(t, hist_origin, hist_dates)
    eval_rows = t["demand_reports"].copy()
    cutoff = pd.Timestamp(origin).tz_localize("Asia/Shanghai")
    eval_rows = eval_rows[eval_rows.available_at <= cutoff].sort_values(KEY + ["revision"]).drop_duplicates(KEY, keep="last")
    actual = (
        pd.MultiIndex.from_product([hist_dates, sorted(t["stores"].store_id), sorted(t["items"].item_id)], names=KEY)
        .to_frame(index=False)
        .merge(eval_rows[KEY + ["demand_units", "available_at", "revision"]], on=KEY, validate="one_to_one")
    )
    if len(actual) != 14 * 96 or actual.demand_units.isna().any():
        raise ValueError("historical 14-day residual window is incomplete at decision cutoff")
    err = actual.demand_units.to_numpy(dtype=float).reshape(14, 96) - hist_point
    point, features = predict(t, origin, ["2026-11-01"])
    scenarios = np.maximum(point[0][None, :] + err, 0.0)
    lower = np.round(np.quantile(scenarios, 0.05, axis=0), 10)
    upper = np.round(np.quantile(scenarios, 0.95, axis=0), 10)
    q, solver = optimize(t, scenarios)
    pairs = [(s, k) for s in sorted(t["stores"].store_id) for k in sorted(t["items"].item_id)]
    pred = pd.DataFrame({"service_date": "2026-11-01", "store_id": [s for s, _ in pairs], "item_id": [k for _, k in pairs]})
    pred["method_id"] = "shared_ridge10_probe"
    pred["demand_point_units"] = point[0]
    pred["lower90_units"] = lower
    pred["upper90_units"] = upper
    pred["interval_level"] = 0.9
    plan = pred[KEY + ["method_id"]].copy()
    plan["q_units"] = q
    out.mkdir(parents=True, exist_ok=True)
    pred.to_csv(out / "predictions.csv", index=False, encoding="utf-8", float_format="%.10f")
    plan.to_csv(out / "replenishment.csv", index=False, encoding="utf-8")
    hashes = {f"{name}.csv": sha256(raw / f"{name}.csv") for name in TABLES}
    hashes["decision.json"] = sha256(raw / "decision.json")
    summary = {
        "status": "bounded author probe; independent reception pending",
        "source_hashes": hashes,
        "decision_origin": origin,
        "historical_residual_origin": hist_origin,
        "historical_residual_window": [hist_dates[0], hist_dates[-1]],
        "residual_complete_day_vectors": 14,
        "final_rows": len(pred),
        "unique_keys": int(pred[KEY].drop_duplicates().shape[0]),
        "training_rows_final_origin": len(snapshot(t, origin)),
        "future_promotion_features_announced_by_origin": bool(features.announced_at.dropna().le(pd.Timestamp(origin).tz_localize("Asia/Shanghai")).all()),
        "weather_used": False,
        "daily_q_units": int(q.sum()),
        "daily_procurement_yuan": float(q @ np.array([t["items"].set_index("item_id").loc[k, "procurement_yuan"] for _, k in pairs])),
        "solver": solver,
        "limits": [
            "one future date only",
            "14 historical residual vectors are a plumbing smoke, not a validated 90% calibration",
            "no comparison, full horizon, sensitivity, paper, or independent acceptance performed",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
