"""Independent R22 reconstruction from authorized raw inputs and source traces.

No R22 result, author self-check, report claim, or expected aggregate is read.
All outputs are explicit and must be placed in a new directory under review/initial.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csr_matrix
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[5]
RAW = ROOT / "runs/R21/inputs/raw"
SOURCE = ROOT / "runs/R22/execution/source/v1"
TRACE = ROOT / "runs/R21/execution/science-v1"
EXECUTION = ROOT / "runs/R22/execution"
KEY = ["service_date", "store_id", "item_id"]
ORIGINS = ["2026-07-22T18:00:00", "2026-09-02T18:00:00", "2026-09-19T18:00:00"]
HORIZON = 42
CUTOFF = "2026-11-04T18:00:00"
LAST_LABEL_DATE = "2026-10-31"
METHODS = ["shared_ridge10", "weekly_mean56"]
CAPACITY, BUDGET = 1600, 6000


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def timestamp(value):
    value = pd.Timestamp(value)
    return value.tz_localize("Asia/Shanghai") if value.tzinfo is None else value.tz_convert("Asia/Shanghai")


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, float_format="%.10f", lineterminator="\n").encode("utf-8")


def source_csv_matches(frame: pd.DataFrame, path: Path) -> bool:
    # Windows text-mode CSV writing uses CRLF; normalize only record separators.
    return csv_bytes(frame) == path.read_bytes().replace(b"\r\n", b"\n")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(csv_bytes(frame))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, default=str)
        stream.write("\n")


class RawPanel:
    def __init__(self):
        self.tables = {}
        for name in ("demand_reports", "stores", "items", "calendar", "promotions", "weather"):
            frame = pd.read_csv(RAW / f"{name}.csv")
            frame["raw_row"] = np.arange(2, len(frame) + 2)
            source_cols = [c for c in frame.columns if c != "raw_row"]
            frame["raw_hash"] = [hashlib.sha256(str(row).encode()).hexdigest() for row in frame[source_cols].itertuples(index=False, name=None)]
            for col in ("available_at", "announced_at"):
                if col in frame:
                    frame[col] = pd.to_datetime(frame[col], format="%Y-%m-%dT%H:%M:%S", errors="raise").dt.tz_localize("Asia/Shanghai")
            self.tables[name] = frame
        self.decision = json.loads((RAW / "decision.json").read_text(encoding="utf-8"))
        self.stores = sorted(self.tables["stores"].store_id.astype(str).tolist())
        self.items = sorted(self.tables["items"].item_id.astype(str).tolist())
        self.pairs = [(store, item) for store in self.stores for item in self.items]
        item_table = self.tables["items"].set_index("item_id")
        self.cost = np.array([item_table.loc[item, "procurement_yuan"] for _, item in self.pairs], dtype=float)
        self.short = np.array([item_table.loc[item, "shortage_yuan"] for _, item in self.pairs], dtype=float)
        self.waste = np.array([item_table.loc[item, "waste_yuan"] for _, item in self.pairs], dtype=float)
        self.maxq = np.array([item_table.loc[item, "daily_max_units"] for _, item in self.pairs], dtype=int)
        self.audit = self._audit()

    def _audit(self):
        original = self.tables["demand_reports"]
        exact = original.drop_duplicates(subset=[c for c in original.columns if c not in ("raw_row", "raw_hash")]).copy()
        if exact.groupby(KEY + ["revision"]).size().max() > 1:
            raise ValueError("same-key same-revision conflict after exact duplicate collapse")
        if (exact.revision < 1).any() or not np.equal(exact.revision, np.floor(exact.revision)).all():
            raise ValueError("invalid revision")
        ordering = exact.groupby(KEY, sort=False).apply(lambda g: g.sort_values("revision").available_at.is_monotonic_increasing, include_groups=False)
        if not ordering.all():
            raise ValueError("revision arrival order is not monotone")
        self.tables["demand_reports"] = exact
        for name, keys in (("stores", ["store_id"]), ("items", ["item_id"]), ("calendar", ["service_date"]), ("promotions", KEY), ("weather", ["service_date", "zone_id", "kind", "available_at"])):
            if self.tables[name].duplicated(keys).any():
                raise ValueError(f"duplicate dimension/source key: {name}")
        for name, cols in (("demand_reports", ["demand_units", "settlement_yuan"]), ("items", ["procurement_yuan", "shortage_yuan", "waste_yuan", "daily_max_units"]), ("promotions", ["discount_fraction"]), ("calendar", ["weekday_monday_zero", "holiday"])):
            for col in cols:
                vals = self.tables[name][col].dropna().to_numpy(dtype=float)
                if not np.isfinite(vals).all() or (vals < 0).any():
                    raise ValueError(f"invalid finite/nonnegative source field {name}.{col}")
        if not np.equal(exact.demand_units, np.floor(exact.demand_units)).all():
            raise ValueError("nonintegral source demand")
        return {
            "raw_file_sha256": {p.name: sha_file(p) for p in sorted(RAW.iterdir()) if p.is_file()},
            "raw_table_rows_before_exact_duplicate_collapse": {name: int(len(frame)) for name, frame in ((k, v) for k, v in self.tables.items())},
            "exact_demand_duplicates_removed": int(len(original) - len(exact)),
            "demand_unique_coordinate_count": int(len(exact[KEY].drop_duplicates())),
            "stores": len(self.stores), "items": len(self.items), "coordinates_per_day": len(self.pairs),
            "revision_conflicts": 0, "revision_arrival_monotonic": True,
        }

    def snapshot(self, origin: str, purpose="train") -> pd.DataFrame:
        at = timestamp(origin)
        demand = self.tables["demand_reports"]
        available = demand[demand.available_at <= at].sort_values(KEY + ["revision"])
        latest = available.drop_duplicates(KEY, keep="last").sort_values(KEY).copy()
        if purpose == "train":
            latest = latest[latest.service_date < at.strftime("%Y-%m-%d")].copy()
        latest["origin"] = at.isoformat()
        latest["purpose"] = purpose
        if not latest.available_at.le(at).all():
            raise ValueError("snapshot includes an unavailable report")
        return latest.reset_index(drop=True)

    def grid(self, dates) -> pd.DataFrame:
        return pd.DataFrame([(d, store, item) for d in dates for store, item in self.pairs], columns=KEY)

    def features(self, keys: pd.DataFrame, origin: str, train: pd.DataFrame) -> pd.DataFrame:
        at = timestamp(origin)
        promotion = self.tables["promotions"]
        known_promo = promotion[promotion.announced_at <= at]
        out = keys.merge(self.tables["calendar"].drop(columns=["raw_row", "raw_hash"]), on="service_date", validate="many_to_one")
        out = out.merge(self.tables["stores"][["store_id", "zone_id"]], on="store_id", validate="many_to_one")
        p = known_promo[KEY + ["discount_fraction", "announced_at", "raw_row", "raw_hash"]].rename(columns={"raw_row": "promo_raw_row", "raw_hash": "promo_raw_hash"})
        out = out.merge(p, on=KEY, how="left", validate="one_to_one")
        out["promo_known"] = out.discount_fraction.notna().astype(int)
        lower = (at - pd.Timedelta(days=56)).strftime("%Y-%m-%d")
        recent_keys = train[train.service_date >= lower][KEY]
        impute = recent_keys.merge(known_promo[KEY + ["discount_fraction"]], on=KEY, validate="one_to_one").groupby("item_id").discount_fraction.mean()
        out["discount_fraction"] = out.discount_fraction.fillna(out.item_id.map(impute)).fillna(0)
        weather = self.tables["weather"]
        forecast = weather[(weather.kind == "forecast") & (weather.available_at <= at)].sort_values("available_at").drop_duplicates(["service_date", "zone_id"], keep="last")
        out = out.merge(forecast[["service_date", "zone_id", "rain_mm", "available_at", "raw_row"]].rename(columns={"available_at": "weather_available_at", "raw_row": "weather_raw_row"}), on=["service_date", "zone_id"], how="left", validate="many_to_one")
        out["weather_known"] = out.weather_available_at.notna().astype(int)
        out["time30"] = (pd.to_datetime(out.service_date) - pd.Timestamp("2026-05-01")).dt.days / 30
        out["origin"] = at.isoformat()
        if len(out) != len(keys) or out.duplicated(KEY).any():
            raise ValueError("feature join changed target grid")
        if not out.announced_at.dropna().le(at).all() or not out.weather_available_at.dropna().le(at).all():
            raise ValueError("feature uses a late-known source")
        return out


def feature_matrix(features: pd.DataFrame, holiday_scale=0.3) -> np.ndarray:
    stores = {value: i for i, value in enumerate(sorted(features.store_id.astype(str).unique()))}
    items = {value: i for i, value in enumerate(sorted(features.item_id.astype(str).unique()))}
    # Source uses S01..S12/K01..K08 indices. Explicit identifiers avoid row-order dependence.
    n = len(features)
    out = np.zeros((n, 169), dtype=float)
    for row, (store, item) in enumerate(features[["store_id", "item_id"]].itertuples(index=False, name=None)):
        si = int(str(store)[1:]) - 1 if str(store)[1:].isdigit() else stores[str(store)]
        ki = int(str(item)[1:]) - 1 if str(item)[1:].isdigit() else items[str(item)]
        out[row, si * 8 + ki] = 1
    item_index = features.item_id.astype(str).str[1:].astype(int).to_numpy() - 1
    weekdays = features.weekday_monday_zero.to_numpy(dtype=int)
    out[np.arange(n), 96 + item_index * 7 + weekdays] = 1
    out[np.arange(n), 152 + item_index] = features.time30.to_numpy(dtype=float)
    out[np.arange(n), 160 + item_index] = features.discount_fraction.to_numpy(dtype=float)
    out[:, 168] = features.holiday.to_numpy(dtype=float) * holiday_scale
    return out


def predictions(panel: RawPanel, origin: str, method: str, train: pd.DataFrame, target: pd.DataFrame):
    train_features = panel.features(train[KEY], origin, train)
    test_features = panel.features(target, origin, train)
    if method == "shared_ridge10":
        model = Ridge(alpha=10, fit_intercept=False, solver="cholesky")
        model.fit(feature_matrix(train_features, .3), train.demand_units.to_numpy(dtype=float))
        point = np.maximum(model.predict(feature_matrix(test_features, .3)), 0).reshape(-1, len(panel.pairs))
        return point, test_features, train_features, model.coef_
    if method == "weekly_mean56":
        recent = train[train.service_date >= (timestamp(origin) - pd.Timedelta(days=56)).strftime("%Y-%m-%d")].copy()
        recent["weekday"] = pd.to_datetime(recent.service_date).dt.weekday
        values = recent.groupby(["store_id", "item_id", "weekday"]).demand_units.mean()
        fallback = train.groupby(["store_id", "item_id"]).demand_units.mean()
        flattened = [values.get((s, k, int(w)), fallback.get((s, k), np.nan)) for s, k, w in test_features[["store_id", "item_id", "weekday_monday_zero"]].itertuples(index=False, name=None)]
        point = np.maximum(np.asarray(flattened, dtype=float), 0).reshape(-1, len(panel.pairs))
        return point, test_features, train_features, None
    raise ValueError(f"unknown fixed method {method}")


def realized_losses(q, demand, short_cost, waste_cost):
    q = np.asarray(q, dtype=float)
    demand = np.asarray(demand, dtype=float)
    return np.maximum(demand - q, 0) * short_cost, np.maximum(q - demand, 0) * waste_cost


def check_action(q, unit_cost, maxq, capacity, budget):
    q = np.asarray(q)
    if q.ndim != 1 or not np.isfinite(q).all() or (q < 0).any() or not np.equal(q, np.floor(q)).all():
        raise ValueError("action must be finite, nonnegative integer units")
    if (q > maxq).any() or q.sum() > capacity or np.dot(q, unit_cost) > budget + 1e-9:
        raise ValueError("action exceeds per-key or daily resources")


def optimize(scenarios, unit_cost, short_cost, waste_cost, maxq, capacity=CAPACITY, budget=BUDGET):
    scenarios = np.asarray(scenarios, dtype=float)
    if scenarios.ndim != 2 or scenarios.shape[1] != len(unit_cost) or not np.isfinite(scenarios).all() or (scenarios < 0).any():
        raise ValueError("scenario array must be finite, nonnegative, and match the key grid")
    levels = np.arange(int(np.max(maxq)) + 1, dtype=float)
    expected = (np.maximum(scenarios[:, :, None] - levels, 0) * short_cost[None, :, None] + np.maximum(levels - scenarios[:, :, None], 0) * waste_cost[None, :, None]).mean(axis=0)
    marginal = expected[:, :-1] - expected[:, 1:]
    if (np.diff(marginal, axis=1) > 1e-7).any():
        raise ValueError("expected loss marginal values are not concave")
    variables = np.argwhere(np.stack([marginal[i, :maxq[i]] > 1e-10 for i in range(len(maxq))]))
    if len(variables) == 0:
        q = np.zeros(len(maxq), dtype=int)
        base = float(expected[:, 0].sum())
        return q, {"status": 0, "message": "no beneficial marginal units", "gap": 0., "objective": base, "bound": base, "nodes": 0}
    item_ix, unit_ix = variables[:, 0], variables[:, 1]
    gain = marginal[item_ix, unit_ix]
    constraints = csr_matrix(np.vstack([np.ones(len(variables)), unit_cost[item_ix]]))
    result = milp(-gain, integrality=np.ones(len(gain)), bounds=Bounds(0, 1), constraints=LinearConstraint(constraints, [-np.inf, -np.inf], [capacity, budget]), options={"mip_rel_gap": 1e-9})
    if result.x is None:
        raise RuntimeError(f"integer optimizer returned no feasible action: {result.message}")
    q = np.bincount(item_ix, weights=np.rint(result.x), minlength=len(maxq)).astype(int)
    check_action(q, unit_cost, maxq, capacity, budget)
    actual = float(expected[np.arange(len(q)), q].sum())
    if abs(actual - (float(expected[:, 0].sum()) + float(result.fun))) > 1e-6:
        raise AssertionError("marginal objective does not reproduce direct expected loss")
    return q, {"status": int(result.status), "message": str(result.message), "gap": float(result.mip_gap), "objective": actual, "bound": float(expected[:, 0].sum() + result.mip_dual_bound), "nodes": int(result.mip_node_count)}


def day_ready(frame: pd.DataFrame, origin: str) -> tuple[bool, str]:
    if len(frame) != 96 or frame[KEY].drop_duplicates().shape[0] != 96:
        return False, "not exactly 96 unique coordinates"
    if frame.service_date.nunique() != 1:
        return False, "mixed service dates"
    if str(frame.service_date.iloc[0]) >= origin[:10]:
        return False, "service day not ended"
    if timestamp(frame.source_origin.iloc[0]) >= timestamp(origin):
        return False, "source origin is not strictly earlier"
    if pd.to_datetime(frame.available_at).max() > timestamp(origin):
        return False, "one or more exact used revisions arrived after target origin"
    return True, "eligible complete mature day"


def metric_row(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"n_keys": 0, "n_days": 0, "status": "not_estimable", **{k: None for k in ("mae", "rmse", "bias", "coverage", "below", "above", "mean_width", "interval_score", "shortage_yuan_per_day", "waste_yuan_per_day", "loss_yuan_per_day", "procurement_yuan_per_day", "units_per_day")}}
    days = frame.service_date.nunique()
    return {
        "n_keys": int(len(frame)), "n_days": int(days), "status": "estimated",
        "mae": float(frame.abs_error.mean()), "rmse": float(np.sqrt(frame.squared_error.mean())),
        "bias": float((frame.point - frame.actual).mean()), "coverage": float(frame.covered.mean()),
        "below": float((frame.actual < frame.lower90).mean()), "above": float((frame.actual > frame.upper90).mean()),
        "mean_width": float((frame.upper90 - frame.lower90).mean()), "interval_score": float(frame.interval_score.mean()),
        "shortage_yuan_per_day": float(frame.shortage_yuan.sum() / days), "waste_yuan_per_day": float(frame.waste_yuan.sum() / days),
        "loss_yuan_per_day": float((frame.shortage_yuan + frame.waste_yuan).sum() / days),
        "procurement_yuan_per_day": float(frame.procurement_yuan.sum() / days), "units_per_day": float(frame.q_units.sum() / days),
    }


def make_groups(history: pd.DataFrame, panel: RawPanel, output: Path) -> None:
    specs = {
        "overall": {}, "early_late": {"stage": ["1-14", "15-42"]},
        "seven_day_band": {"band": list(range(1, 7))}, "activity": {"holiday": [0, 1]},
        "activity_by_band": {"holiday": [0, 1], "band": list(range(1, 7))},
        "activity_by_stage": {"holiday": [0, 1], "stage": ["1-14", "15-42"]},
        "store": {"store_id": panel.stores}, "item": {"item_id": panel.items},
    }
    for label, dimensions in specs.items():
        rows = []
        for (origin, method), all_rows in history.groupby(["origin", "method"], sort=True):
            combos = itertools.product(*(dimensions.values())) if dimensions else [()]
            for vals in combos:
                subset = all_rows
                for name, val in zip(dimensions, vals):
                    subset = subset[subset[name] == val]
                rows.append({"origin": origin, "method": method, **dict(zip(dimensions, vals)), **metric_row(subset)})
        write_csv(output / f"results/group_{label}.csv", pd.DataFrame(rows))
    daily_rows = []
    for (origin, method, date), group in history.groupby(["origin", "method", "service_date"], sort=True):
        daily_rows.append({"origin": origin, "method": method, "service_date": date, "holiday": int(group.holiday.iloc[0]), "horizon": int(group.horizon.iloc[0]), **metric_row(group)})
    daily = pd.DataFrame(daily_rows)
    write_csv(output / "results/daily.csv", daily)
    piv = daily.pivot(index=["origin", "service_date", "holiday", "horizon"], columns="method", values=["loss_yuan_per_day", "interval_score"])
    piv.columns = ["_".join(col) for col in piv.columns]
    piv = piv.reset_index()
    piv["loss_W_minus_R"] = piv.loss_yuan_per_day_weekly_mean56 - piv.loss_yuan_per_day_shared_ridge10
    piv["score_W_minus_R"] = piv.interval_score_weekly_mean56 - piv.interval_score_shared_ridge10
    write_csv(output / "results/paired_daily.csv", piv)
    first_two = history[history.origin.isin(ORIGINS[:2])]
    if first_two.service_date.nunique() != 84:
        raise AssertionError("first two windows should describe 84 unique dates")
    combined = [{"method": method, **metric_row(frame)} for method, frame in first_two.groupby("method")]
    write_csv(output / "results/combined_first_two.csv", pd.DataFrame(combined))


def boundary_cases(panel: RawPanel, interface: pd.DataFrame) -> dict:
    origin = "2026-07-22T18:00:00"
    day = interface.iloc[:96].copy()
    day["service_date"] = "2026-07-09"
    day["source_origin"] = "2026-07-08T18:00:00"
    day["available_at"] = timestamp(origin)
    full, _ = day_ready(day, origin)
    partial, why_partial = day_ready(day.iloc[:95], origin)
    late = day.copy()
    late.loc[late.index[-1], "available_at"] = timestamp(origin) + pd.Timedelta(seconds=1)
    late_ok, _ = day_ready(late, origin)
    same_origin = day.copy(); same_origin["source_origin"] = origin
    same_ok, _ = day_ready(same_origin, origin)
    unfinished = day.copy(); unfinished["service_date"] = origin[:10]
    unfinished_ok, _ = day_ready(unfinished, origin)
    other_day = late.copy(); other_day["service_date"] = "2026-07-10"
    eligible_days = [date for date, group in pd.concat([day, other_day]).groupby("service_date") if day_ready(group, origin)[0]]

    # 3-coordinate exact oracle, separate from production size and results.
    unit_cost = panel.cost[:3]
    a, b, maxq = panel.short[:3], panel.waste[:3], panel.maxq[:3]
    small = np.array([[1.25, 3., 2.], [2., 2.5, 4.], [3., 1., 0.]])
    q, solver = optimize(small, unit_cost, a, b, maxq, capacity=4, budget=14)
    candidates = [np.asarray(z) for z in itertools.product(*(range(int(v) + 1) for v in maxq)) if sum(z) <= 4 and np.dot(z, unit_cost) <= 14]
    objectives = [float((np.maximum(small - z, 0) * a + np.maximum(z - small, 0) * b).sum(axis=1).mean()) for z in candidates]

    # Domain checks: continuous scenario demand is valid; decisions remain integral.
    fractional = np.array([[1.25, 2.75, 0.]])
    continuous_ok = bool(np.isfinite(fractional).all() and (fractional >= 0).all())
    bad_decisions = {}
    for label, candidate in (("fractional", np.array([.5, 0., 0.])), ("negative", np.array([-1, 0, 0])), ("nonfinite", np.array([np.nan, 0, 0])), ("per_key", maxq + 1), ("capacity", np.array([3, 3, 0])), ("budget", np.array([4, 4, 0]))):
        try:
            check_action(candidate, unit_cost, maxq, 4 if label == "capacity" else CAPACITY, 14 if label == "budget" else BUDGET)
        except ValueError:
            bad_decisions[label] = "rejected"
        else:
            bad_decisions[label] = "unexpectedly accepted"
    nonfinite_rejected = {}
    for label, scenario in (("nan", np.array([[np.nan, 1., 2.]])), ("infinity", np.array([[np.inf, 1., 2.]])), ("negative", np.array([[-1., 1., 2.]])), ("wrong_coordinates", np.ones((1, 95)))):
        try:
            optimize(scenario, unit_cost, a, b, maxq)
        except (ValueError, IndexError):
            nonfinite_rejected[label] = True
        else:
            nonfinite_rejected[label] = False

    reports = panel.tables["demand_reports"]
    versioned = reports[reports.revision > 1].sort_values("available_at").iloc[0]
    arrival = versioned.available_at
    before = panel.snapshot((arrival - pd.Timedelta(seconds=1)).isoformat(), "evaluation")
    at = panel.snapshot(arrival.isoformat(), "evaluation")
    k = tuple(versioned[col] for col in KEY)
    before_rev = before.set_index(KEY).loc[k, "revision"] if k in before.set_index(KEY).index else None
    at_rev = at.set_index(KEY).loc[k, "revision"]
    return {
        "day_readiness": {"complete_96_accepted": bool(full), "95_of_96_rejected": not bool(partial), "late_one_second_rejected": not bool(late_ok), "equal_source_origin_rejected": not bool(same_ok), "unended_service_day_rejected": not bool(unfinished_ok), "incomplete_neighbor_does_not_exclude_complete_day": eligible_days == ["2026-07-09"], "partial_reason": why_partial, "eligible_neighbor_days": eligible_days},
        "small_oracle": {"enumerated_actions": len(objectives), "oracle_loss": min(objectives), "independent_solver_loss": solver["objective"], "action": q.tolist(), "match": abs(min(objectives) - solver["objective"]) < 1e-7},
        "value_domains": {"fractional_scenarios_are_valid": continuous_ok, "action_rejections": bad_decisions, "invalid_scenario_rejections": nonfinite_rejected, "point_interval_containment_required": False},
        "mature_revision_boundary": {"raw_key": dict(zip(KEY, k)), "arrival": arrival.isoformat(), "revision_before_arrival": None if before_rev is None else int(before_rev), "revision_at_arrival": int(at_rev), "late_one_second_cutoff_excludes_revision": before_rev is None or before_rev < versioned.revision},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = Path(args.out).resolve()
    if output != (ROOT / "runs/R22/review/initial/rebuild-v2").resolve():
        raise ValueError("output must be the frozen explicit review/initial/rebuild destination")
    output.mkdir(parents=True, exist_ok=False)
    began = time.perf_counter()
    panel = RawPanel()
    config = json.loads((SOURCE / "config.json").read_text(encoding="utf-8"))
    if config["origins"] != ORIGINS or config["horizon_days"] != HORIZON:
        raise ValueError("frozen R22 config does not match this independent implementation")
    if config["evaluation_label_cutoff"] != CUTOFF or config["last_service_date"] != LAST_LABEL_DATE:
        raise ValueError("unexpected evaluation cutoff")
    labels = panel.snapshot(CUTOFF, "evaluation")
    labels = labels[labels.service_date <= LAST_LABEL_DATE].copy()
    interface = pd.read_csv(TRACE / "uncertainty/residual_coordinates_all.csv", dtype={"point": str})
    needed = KEY + ["revision", "available_at", "raw_row", "raw_hash", "method_id", "source_origin", "train_snapshot_sha256", "point", "error", "full_day_ready_at", "coordinates"]
    if not set(needed) <= set(interface.columns):
        raise ValueError("authorized residual trace schema missing required lineage fields")
    interface = interface[needed].copy()
    if interface.duplicated(["source_origin", "method_id"] + KEY).any():
        raise ValueError("duplicate source residual coordinate")

    # Independently re-create the mature label and error from raw reports.
    mature = labels[KEY + ["revision", "available_at", "raw_row", "raw_hash", "demand_units"]].rename(columns={"revision": "mature_revision", "available_at": "mature_available_at", "raw_row": "mature_raw_row", "raw_hash": "mature_raw_hash", "demand_units": "mature_demand"})
    rebuilt = interface.merge(mature, on=KEY, how="left", validate="many_to_one")
    if rebuilt.mature_demand.isna().any():
        raise ValueError("source coordinate has no mature raw label at fixed cutoff")
    for field in ("revision", "raw_row", "raw_hash"):
        if not (rebuilt[field].astype(str).to_numpy() == rebuilt[f"mature_{field}"].astype(str).to_numpy()).all():
            raise ValueError(f"source coordinate does not use the fixed mature label identity: {field}")
    if not (pd.to_datetime(rebuilt.available_at).astype(str).to_numpy() == pd.to_datetime(rebuilt.mature_available_at).astype(str).to_numpy()).all():
        raise ValueError("source coordinate maturity arrival differs from raw latest version")
    rebuilt["published_point"] = rebuilt.point.astype(float)
    rebuilt["error_rebuilt"] = rebuilt.mature_demand.to_numpy(dtype=float) - rebuilt.published_point.to_numpy(dtype=float)
    rebuilt["source_error_delta"] = rebuilt.error.astype(float) - rebuilt.error_rebuilt
    write_csv(output / "source_rebuild/residual_coordinates_rebuilt.csv", rebuilt)

    # Rebuild source-origin forecasts and compare lineage to allowed stored source artifacts.
    source_rows, source_summary = [], []
    source_origins = sorted(rebuilt.source_origin.unique())
    for source_origin in source_origins:
        if timestamp(source_origin) >= max(map(timestamp, ORIGINS)):
            continue
        train = panel.snapshot(source_origin)
        tag = source_origin[:10]
        train_path = TRACE / f"data/train_{tag}.csv"
        if not train_path.exists():
            raise ValueError(f"missing authorized source training snapshot for {source_origin}")
        if not source_csv_matches(train, train_path):
            raise AssertionError(f"independent as-of training snapshot differs at {source_origin}")
        if set(rebuilt.loc[rebuilt.source_origin == source_origin, "train_snapshot_sha256"]) != {sha_file(train_path)}:
            raise AssertionError(f"residual lineage snapshot identity mismatch at {source_origin}")
        windows = sorted(rebuilt.loc[rebuilt.source_origin == source_origin, "service_date"].unique())
        grid = panel.grid(windows)
        for method in METHODS:
            source_group = rebuilt[(rebuilt.source_origin == source_origin) & (rebuilt.method_id == method)].sort_values(KEY)
            if source_group.empty:
                continue
            target = source_group[KEY].reset_index(drop=True)
            point, forecast_features, train_features, coef = predictions(panel, source_origin, method, train, target)
            if method == "shared_ridge10":
                coeff_path = TRACE / f"models/coefficients_{tag}_shared_ridge10.json"
                coeff = np.asarray(json.loads(coeff_path.read_text(encoding="utf-8"))["coefficients"], dtype=float)
                if coef.shape != coeff.shape or not np.allclose(coef, coeff, rtol=0, atol=1e-9):
                    raise AssertionError(f"independent source coefficients differ at {source_origin}")
            calculated = point.ravel()
            published = source_group.published_point.to_numpy(dtype=float)
            max_delta = float(np.max(np.abs(calculated - published)))
            if max_delta > 5e-10:
                raise AssertionError(f"source point differs from published 10-digit point at {source_origin}/{method}: {max_delta}")
            source_group = source_group.copy()
            source_group["recomputed_point"] = calculated
            source_rows.append(source_group)
            source_summary.append({"source_origin": source_origin, "method": method, "days": len(windows), "coordinates": len(source_group), "train_snapshot_recreated": True, "max_point_delta": max_delta})
    write_csv(output / "source_rebuild/source_forecasts_rebuilt.csv", pd.concat(source_rows, ignore_index=True))
    write_csv(output / "source_rebuild/source_rebuild_summary.csv", pd.DataFrame(source_summary))

    all_history, pool_records, solver_records, origin_records = [], [], [], []
    for origin in ORIGINS:
        train = panel.snapshot(origin)
        tag = origin[:10]
        dates = pd.date_range(timestamp(origin).date() + pd.Timedelta(days=1), periods=HORIZON).strftime("%Y-%m-%d").tolist()
        target = panel.grid(dates)
        actual = target.merge(labels, on=KEY, how="left", validate="one_to_one")
        if len(actual) != HORIZON * 96 or actual.demand_units.isna().any():
            raise AssertionError(f"target label grid incomplete at {origin}")
        demand = actual.demand_units.to_numpy(dtype=float).reshape(HORIZON, 96)
        activity = panel.tables["calendar"].set_index("service_date").loc[dates, "holiday"].to_numpy(dtype=int)
        origin_records.append({"origin": origin, "train_rows": int(len(train)), "train_days": int(train.service_date.nunique()), "latest_train_service_date": str(train.service_date.max()), "latest_train_available_at": train.available_at.max().isoformat(), "first_target": dates[0], "last_target": dates[-1], "target_keys_per_route": int(len(target)), "activity_days": int(activity.sum())})
        for method in METHODS:
            point, features, _, _ = predictions(panel, origin, method, train, target)
            point = np.round(point, 10)
            source_method = rebuilt[rebuilt.method_id == method]
            pool_vectors, pool_members = [], []
            for (source_origin, service_date), day in source_method.groupby(["source_origin", "service_date"], sort=True):
                ready, reason = day_ready(day, origin)
                record = {"target_origin": origin, "method": method, "source_origin": source_origin, "service_date": service_date, "coordinates": int(len(day)), "ready_at": pd.to_datetime(day.available_at).max().isoformat(), "eligible": bool(ready), "reason": reason}
                pool_records.append(record)
                if ready:
                    error_vector = day.sort_values(KEY).error_rebuilt.to_numpy(dtype=float)
                    if error_vector.shape != (96,) or not np.isfinite(error_vector).all():
                        raise AssertionError("eligible residual vector is not a finite 96-coordinate day")
                    pool_vectors.append(error_vector)
                    pool_members.append(record)
            if not pool_vectors:
                raise AssertionError(f"empty mature residual pool at {origin}/{method}")
            if len({m["service_date"] for m in pool_members}) != len(pool_members):
                raise AssertionError("a residual day received duplicate weight")
            errors = np.asarray(pool_vectors)
            scenarios = np.maximum(point[None, :, :] + errors[:, None, :], 0)
            lower = np.round(np.quantile(scenarios, .05, axis=0, method="linear"), 10)
            upper = np.round(np.quantile(scenarios, .95, axis=0, method="linear"), 10)
            if not all(np.isfinite(v).all() and (v >= 0).all() for v in (point, lower, upper)) or (lower > upper).any():
                raise AssertionError("invalid point or interval domain/order")
            write_csv(output / f"data/train_{tag}.csv", train) if method == METHODS[0] else None
            write_csv(output / f"uncertainty/pool_{tag}_{method}.csv", pd.DataFrame(pool_members))
            write_csv(output / f"uncertainty/residual_vectors_{tag}_{method}.csv", pd.DataFrame(errors, columns=[f"{s}_{i}" for s, i in panel.pairs]))
            np.savez_compressed(output / f"uncertainty/scenarios_{tag}_{method}.npz", demand_units=scenarios, service_dates=np.array(dates), residual_dates=np.array([m["service_date"] for m in pool_members]), weights=np.ones(len(pool_members)) / len(pool_members))
            actions = []
            for ix, service_date in enumerate(dates):
                q, solver = optimize(scenarios[:, ix, :], panel.cost, panel.short, panel.waste, panel.maxq)
                check_action(q, panel.cost, panel.maxq, CAPACITY, BUDGET)
                sh, wa = realized_losses(q, scenarios[:, ix, :], panel.short, panel.waste)
                objective = float((sh + wa).mean(axis=0).sum())
                if abs(objective - solver["objective"]) > 1e-6:
                    raise AssertionError("independently recomputed objective mismatch")
                actions.append(q)
                solver_records.append({"origin": origin, "method": method, "service_date": service_date, "objective_recomputed": objective, "q_units": int(q.sum()), "procurement_yuan": float(q @ panel.cost), "capacity_slack": int(CAPACITY - q.sum()), "budget_slack_yuan": float(BUDGET - q @ panel.cost), "pool_days": len(errors), **solver})
            actions = np.asarray(actions, dtype=int)
            stage = np.where(np.arange(1, HORIZON + 1) <= 14, "1-14", "15-42")
            band = ((np.arange(1, HORIZON + 1) - 1) // 7 + 1).astype(int)
            joined = features[KEY + ["holiday", "promo_known", "weather_known"]].copy()
            joined["origin"] = origin; joined["method"] = method
            joined["horizon"] = np.repeat(np.arange(1, HORIZON + 1), 96)
            joined["stage"] = np.repeat(stage, 96); joined["band"] = np.repeat(band, 96)
            joined["point"] = point.ravel(); joined["actual"] = demand.ravel(); joined["lower90"] = lower.ravel(); joined["upper90"] = upper.ravel()
            joined["interval_level"] = .9; joined["covered"] = ((demand >= lower) & (demand <= upper)).ravel()
            joined["q_units"] = actions.ravel()
            joined["actual_revision"] = actual.revision.to_numpy(); joined["actual_available_at"] = actual.available_at.astype(str).to_numpy(); joined["actual_raw_row"] = actual.raw_row.to_numpy()
            joined["shortage_yuan"] = (np.maximum(demand - actions, 0) * panel.short).ravel()
            joined["waste_yuan"] = (np.maximum(actions - demand, 0) * panel.waste).ravel()
            joined["procurement_yuan"] = (actions * panel.cost).ravel()
            joined["abs_error"] = np.abs(joined.point - joined.actual); joined["squared_error"] = (joined.point - joined.actual) ** 2
            joined["interval_score"] = joined.upper90 - joined.lower90 + 20 * np.maximum(joined.lower90 - joined.actual, 0) + 20 * np.maximum(joined.actual - joined.upper90, 0)
            joined["residual_pool_days"] = len(errors)
            if joined.duplicated(["origin", "method"] + KEY).any() or len(joined) != 4032:
                raise AssertionError("forecast/action output grid is not 4032 unique rows")
            all_history.append(joined)
            prediction_frame = target.copy(); prediction_frame["method"] = method; prediction_frame["demand_point_units"] = point.ravel(); prediction_frame["lower90_units"] = lower.ravel(); prediction_frame["upper90_units"] = upper.ravel(); prediction_frame["interval_level"] = .9
            action_frame = target.copy(); action_frame["method"] = method; action_frame["q_units"] = actions.ravel()
            write_csv(output / f"predictions/{tag}_{method}.csv", prediction_frame)
            write_csv(output / f"plans/{tag}_{method}.csv", action_frame)
    history = pd.concat(all_history, ignore_index=True)
    if len(history) != 3 * 2 * 4032:
        raise AssertionError("full replay key count mismatch")
    write_csv(output / "results/keys.csv", history)
    write_csv(output / "results/daily_solver.csv", pd.DataFrame(solver_records))
    write_csv(output / "results/origins.csv", pd.DataFrame(origin_records))
    write_csv(output / "uncertainty/pool_membership.csv", pd.DataFrame(pool_records))
    make_groups(history, panel, output)
    boundaries = boundary_cases(panel, interface)
    write_json(output / "validation/boundaries.json", boundaries)
    source_trace_summary = {
        "source_rows": int(len(rebuilt)), "recomputed_rows": int(len(rebuilt)),
        "point_error_is_rebuilt_from_raw_mature_label_minus_published_point": True,
        "stored_error_used_as_truth": False,
        "exact_mature_identity_matches": True,
        "max_abs_stored_error_difference": float(rebuilt.source_error_delta.abs().max()),
        "source_forecasts_rebuilt": source_summary,
    }
    write_json(output / "source_rebuild/summary.json", source_trace_summary)
    write_json(output / "results/reconstruction.json", {
        "schema": "r22-independent-reconstruction/1", "protocol_origins": ORIGINS,
        "routes": METHODS, "rows": len(history), "rows_per_route_origin": 4032,
        "unique_days_first_two_windows": int(history[history.origin.isin(ORIGINS[:2])].service_date.nunique()),
        "third_window_overlap_dates_with_second": int(len(set(pd.date_range("2026-09-03", periods=42).strftime("%Y-%m-%d")) & set(pd.date_range("2026-09-20", periods=42).strftime("%Y-%m-%d")))),
        "source_rebuild": source_trace_summary, "boundary_cases": boundaries,
        "raw_audit": panel.audit, "elapsed_seconds": time.perf_counter() - began,
        "actual_model": None, "tokens": None, "cost": None,
    })
    print(json.dumps({"status": "independent reconstruction complete", "rows": len(history), "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
