"""Independent prospective holdout scoring against the frozen R21 artifacts."""
from __future__ import annotations
from datetime import date
import hashlib, io, json
from pathlib import Path
import numpy as np
import pandas as pd

R = Path("runs/R21")
OUT = R / "review/holdout"
OUT.mkdir(parents=True, exist_ok=True)
KEY = ["service_date", "store_id", "item_id"]
ROUTES = ("shared_ridge10", "weekly_mean56")

def sha_bytes(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def read_lock(p: Path): return json.loads(p.read_text(encoding="utf-8"))
def lock_entry(d, rel): return next(x for x in d["files"] if x["path"].replace("\\", "/") == rel)
def locked_bytes(rel, lock):
    p = Path(rel); b = p.read_bytes(); e = lock_entry(lock, rel.replace("\\", "/"))
    assert len(b) == e["size_bytes"] and sha_bytes(b) == e["sha256"], f"locked file mismatch: {rel}"
    return b

initial_path, execution_path, evaluation_path = R / "review/initial-lock.json", R / "execution-lock.json", R / "evaluation-lock.json"
initial_lock, execution_lock, evaluation_lock = read_lock(initial_path), read_lock(execution_path), read_lock(evaluation_path)
initial_lock_sha, execution_lock_sha, evaluation_lock_sha = map(lambda p: hashlib.sha256(p.read_bytes()).hexdigest(), (initial_path, execution_path, evaluation_path))
bindings = json.loads((OUT / "freeze-bindings.json").read_text(encoding="utf-8"))
first_open = json.loads((OUT / "first-truth-open.json").read_text(encoding="utf-8"))
assert bindings["binding_valid"] and first_open["all_bindings_precede_truth_open"]
assert initial_lock_sha == bindings["initial_lock"]["sha256"]
assert execution_lock_sha == bindings["execution_lock"]["sha256"]
assert evaluation_lock_sha == bindings["evaluation_lock"]["sha256"]
assert first_open["truth_identity"]["actual_sha256"] == bindings["holdout_truth_lock_identity_only"]["expected_sha256"]

# Freeze-bound sources: evaluation truth, raw unit costs/caps, activity calendar,
# decision resource limits, and both candidates' original production outputs.
input_lock = read_lock(R / "input-lock.json")
truth_b = locked_bytes("runs/R21/evaluation/holdout_truth.csv", evaluation_lock)
items_b = locked_bytes("runs/R21/inputs/raw/items.csv", input_lock)
calendar_b = locked_bytes("runs/R21/inputs/raw/calendar.csv", input_lock)
decision_b = locked_bytes("runs/R21/inputs/raw/decision.json", input_lock)
truth = pd.read_csv(io.BytesIO(truth_b))
items = pd.read_csv(io.BytesIO(items_b))
calendar = pd.read_csv(io.BytesIO(calendar_b))
decision = json.loads(decision_b.decode("utf-8"))

assert decision["horizon_days"] == 42 and decision["capacity_units_per_day"] == 1600 and decision["procurement_budget_yuan_per_day"] == 6000
assert len(truth) == 4032 and truth[KEY].duplicated().sum() == 0
assert len(items) == 8 and items["item_id"].nunique() == 8
assert items["item_id"].is_unique and set(items["item_id"]) == set(truth["item_id"])
assert set(truth["service_date"]) == set(pd.date_range(decision["future_begin"], decision["future_end"]).strftime("%Y-%m-%d"))
assert len(calendar[calendar["service_date"].isin(truth["service_date"])]) == 42
assert truth["demand_units"].notna().all() and np.isfinite(truth["demand_units"].to_numpy(float)).all()
assert (truth["demand_units"] >= 0).all()
cal = calendar[["service_date", "holiday"]].copy()
cal["holiday"] = cal["holiday"].astype(int)
assert cal["service_date"].is_unique and cal["holiday"].isin([0, 1]).all()
item_cost = items.set_index("item_id")["procurement_yuan"].to_dict()
item_short = items.set_index("item_id")["shortage_yuan"].to_dict()
item_waste = items.set_index("item_id")["waste_yuan"].to_dict()
item_cap = items.set_index("item_id")["daily_max_units"].to_dict()

frames = []
route_source_hashes = {}
for route in ROUTES:
    pred_rel = f"runs/R21/execution/science-v1/future/{route}/predictions.csv"
    plan_rel = f"runs/R21/execution/science-v1/future/{route}/replenishment.csv"
    pb, qb = locked_bytes(pred_rel, execution_lock), locked_bytes(plan_rel, execution_lock)
    route_source_hashes[route] = {"predictions_sha256": sha_bytes(pb), "replenishment_sha256": sha_bytes(qb)}
    p = pd.read_csv(io.BytesIO(pb)); q = pd.read_csv(io.BytesIO(qb))
    assert p[KEY].duplicated().sum() == 0 and q[KEY].duplicated().sum() == 0
    assert len(p) == len(q) == 4032
    assert set(p[KEY].itertuples(index=False, name=None)) == set(q[KEY].itertuples(index=False, name=None))
    assert set(p["method_id"]) == {route} and set(q["method_id"]) == {route}
    z = p.merge(q, on=KEY + ["method_id"], validate="one_to_one").merge(truth, on=KEY, validate="one_to_one").merge(items, on="item_id", validate="many_to_one").merge(cal, on="service_date", validate="many_to_one")
    assert len(z) == 4032
    z["route"] = route
    numeric_cols = ["demand_point_units", "lower90_units", "upper90_units", "interval_level", "q_units", "demand_units", "procurement_yuan", "shortage_yuan", "waste_yuan"]
    assert np.isfinite(z[numeric_cols].to_numpy(float)).all()
    z["error"] = z["demand_point_units"] - z["demand_units"]
    z["abs_error"] = z["error"].abs()
    z["sq_error"] = z["error"] ** 2
    z["covered"] = (z["lower90_units"] <= z["demand_units"]) & (z["demand_units"] <= z["upper90_units"])
    z["below"] = z["demand_units"] < z["lower90_units"]
    z["above"] = z["demand_units"] > z["upper90_units"]
    z["width"] = z["upper90_units"] - z["lower90_units"]
    z["interval_score"] = z["width"] + 20.0 * np.maximum(z["lower90_units"] - z["demand_units"], 0) + 20.0 * np.maximum(z["demand_units"] - z["upper90_units"], 0)
    z["shortage_loss_yuan"] = z["shortage_yuan"] * np.maximum(z["demand_units"] - z["q_units"], 0)
    z["waste_loss_yuan"] = z["waste_yuan"] * np.maximum(z["q_units"] - z["demand_units"], 0)
    z["two_part_loss_yuan"] = z["shortage_loss_yuan"] + z["waste_loss_yuan"]
    z["procurement_spend_yuan"] = z["procurement_yuan"] * z["q_units"]
    z["horizon_day"] = (pd.to_datetime(z["service_date"]) - pd.Timestamp(decision["future_begin"])).dt.days + 1
    z["horizon_band"] = z["horizon_day"].map(lambda x: f"{((int(x)-1)//7)*7+1:02d}-{min(((int(x)-1)//7+1)*7,42):02d}")
    z["activity_group"] = np.where(z["holiday"].eq(1), "activity", "ordinary")
    z["activity_x_horizon"] = z["activity_group"] + "_" + z["horizon_band"]
    frames.append(z)

all_rows = pd.concat(frames, ignore_index=True)
assert all_rows.groupby("route").size().to_dict() == {r: 4032 for r in ROUTES}
assert all_rows["interval_level"].sub(.9).abs().max() <= 1e-12
assert (all_rows["demand_point_units"] >= 0).all()
assert (all_rows["lower90_units"] <= all_rows["demand_point_units"]).all()
assert (all_rows["demand_point_units"] <= all_rows["upper90_units"]).all()
assert (all_rows["q_units"] >= 0).all() and (all_rows["q_units"] <= all_rows["daily_max_units"]).all()
assert np.equal(all_rows["q_units"].to_numpy(float), np.floor(all_rows["q_units"].to_numpy(float))).all()
assert (all_rows["horizon_day"].between(1, 42)).all()

daily = all_rows.groupby(["route", "service_date"], as_index=False).agg(
    horizon_day=("horizon_day", "first"), activity=("activity_group", "first"),
    key_count=("item_id", "size"), q_units=("q_units", "sum"),
    procurement_yuan=("procurement_spend_yuan", "sum"), shortage_yuan=("shortage_loss_yuan", "sum"),
    waste_yuan=("waste_loss_yuan", "sum"), loss_yuan=("two_part_loss_yuan", "sum"),
    interval_score_mean=("interval_score", "mean"), coverage=("covered", "mean"),
    below_rate=("below", "mean"), above_rate=("above", "mean"), mean_width=("width", "mean"),
    mae=("abs_error", "mean"), bias=("error", "mean"))
daily["units_within_limit"] = daily["q_units"] <= decision["capacity_units_per_day"]
daily["procurement_within_limit"] = daily["procurement_yuan"] <= decision["procurement_budget_yuan_per_day"] + 1e-9
daily["all_96_keys_present"] = daily["key_count"] == 96
daily["day_feasible"] = daily[["units_within_limit", "procurement_within_limit", "all_96_keys_present"]].all(axis=1)

def metric_record(df: pd.DataFrame, route: str, dimension: str, group: str) -> dict:
    dates = df["service_date"].nunique()
    day_agg = df.groupby("service_date").agg(loss=("two_part_loss_yuan", "sum"), shortage=("shortage_loss_yuan", "sum"), waste=("waste_loss_yuan", "sum"), q=("q_units", "sum"), spend=("procurement_spend_yuan", "sum"))
    return {
        "route": route, "dimension": dimension, "group": group,
        "date_count": int(dates), "key_count": int(len(df)),
        "mae": float(df["abs_error"].mean()), "rmse": float(np.sqrt(df["sq_error"].mean())),
        "bias_pred_minus_truth": float(df["error"].mean()),
        "coverage": float(df["covered"].mean()), "below_rate": float(df["below"].mean()), "above_rate": float(df["above"].mean()),
        "mean_interval_width": float(df["width"].mean()), "mean_interval_score": float(df["interval_score"].mean()),
        "shortage_yuan_per_day": float(day_agg["shortage"].mean()), "waste_yuan_per_day": float(day_agg["waste"].mean()),
        "two_part_loss_yuan_per_day": float(day_agg["loss"].mean()), "q_units_per_day": float(day_agg["q"].mean()),
        "procurement_yuan_per_day": float(day_agg["spend"].mean()),
    }

group_rows = []
for route in ROUTES:
    d = all_rows[all_rows.route == route]
    group_rows.append(metric_record(d, route, "overall", "all_42_days"))
    dimensions = [
        ("date", "service_date"), ("activity", "activity_group"), ("horizon_band", "horizon_band"),
        ("activity_x_horizon", "activity_x_horizon"), ("store", "store_id"), ("item", "item_id"),
    ]
    for dimension, col in dimensions:
        for group, g in d.groupby(col, sort=True):
            group_rows.append(metric_record(g, route, dimension, str(group)))
groups = pd.DataFrame(group_rows)

overall = {}
for route in ROUTES:
    g = all_rows[all_rows.route == route]
    d = daily[daily.route == route]
    overall[route] = {
        "key_count": int(len(g)), "date_count": int(g.service_date.nunique()), "mae": float(g.abs_error.mean()),
        "rmse": float(np.sqrt(g.sq_error.mean())), "bias_pred_minus_truth": float(g.error.mean()),
        "coverage": float(g.covered.mean()), "below_rate": float(g.below.mean()), "above_rate": float(g.above.mean()),
        "mean_interval_width": float(g.width.mean()), "mean_interval_score": float(g.interval_score.mean()),
        "shortage_yuan": float(g.shortage_loss_yuan.sum()), "waste_yuan": float(g.waste_loss_yuan.sum()),
        "two_part_loss_yuan": float(g.two_part_loss_yuan.sum()), "two_part_loss_yuan_per_day": float(d.loss_yuan.mean()),
        "procurement_yuan": float(g.procurement_spend_yuan.sum()), "q_units": float(g.q_units.sum()),
        "all_predictions_intervals_and_plans_finite": bool(np.isfinite(g[["demand_point_units", "lower90_units", "upper90_units", "q_units"]].to_numpy(float)).all()),
        "all_prediction_and_interval_bounds_valid": bool((g.demand_point_units.ge(0) & g.lower90_units.le(g.demand_point_units) & g.demand_point_units.le(g.upper90_units) & g.interval_level.sub(.9).abs().le(1e-12)).all()),
        "all_q_integer_and_item_bounded": bool((g.q_units.mod(1).eq(0) & g.q_units.ge(0) & g.q_units.le(g.daily_max_units)).all()),
        "all_dates_96_unique_keys": bool(d.key_count.eq(96).all()),
        "all_daily_capacity_limits_valid": bool(d.units_within_limit.all()),
        "all_daily_budget_limits_valid": bool(d.procurement_within_limit.all()),
        "max_daily_units": int(d.q_units.max()), "max_daily_procurement_yuan": float(d.procurement_yuan.max()),
        "capacity_full_days": int(d.q_units.eq(decision["capacity_units_per_day"]).sum()),
        "budget_full_days": int(d.procurement_yuan.ge(decision["procurement_budget_yuan_per_day"] - 1e-9).sum()),
    }

daily_wide = daily.pivot(index="service_date", columns="route", values=["loss_yuan", "interval_score_mean", "shortage_yuan", "waste_yuan", "coverage", "q_units", "procurement_yuan"])
daily_wide.columns = [f"{metric}_{route}" for metric, route in daily_wide.columns]
daily_wide = daily_wide.reset_index()
for metric in ("loss_yuan", "interval_score_mean", "shortage_yuan", "waste_yuan", "coverage", "q_units", "procurement_yuan"):
    daily_wide[f"{metric}_delta_weekly_minus_ridge"] = daily_wide[f"{metric}_weekly_mean56"] - daily_wide[f"{metric}_shared_ridge10"]

pair_summary = {
    "daily_loss_difference_weekly_minus_ridge": {
        "mean_yuan_per_day": float(daily_wide["loss_yuan_delta_weekly_minus_ridge"].mean()),
        "days_weekly_lower": int((daily_wide["loss_yuan_delta_weekly_minus_ridge"] < 0).sum()),
        "days_equal": int((daily_wide["loss_yuan_delta_weekly_minus_ridge"] == 0).sum()),
        "days_weekly_higher": int((daily_wide["loss_yuan_delta_weekly_minus_ridge"] > 0).sum()),
    },
    "daily_interval_score_difference_weekly_minus_ridge": {
        "mean_score_per_key_day": float(daily_wide["interval_score_mean_delta_weekly_minus_ridge"].mean()),
        "days_weekly_lower": int((daily_wide["interval_score_mean_delta_weekly_minus_ridge"] < 0).sum()),
        "days_equal": int((daily_wide["interval_score_mean_delta_weekly_minus_ridge"] == 0).sum()),
        "days_weekly_higher": int((daily_wide["interval_score_mean_delta_weekly_minus_ridge"] > 0).sum()),
    },
}

truth_duplicate_count = int(truth.duplicated(KEY).sum())
validation = {
    "schema": "r21-holdout-independent-validation/1", "passed": True,
    "truth_rows": len(truth), "truth_duplicate_keys": truth_duplicate_count,
    "route_rows": {r: len(all_rows[all_rows.route == r]) for r in ROUTES},
    "route_key_uniqueness": {r: bool(not all_rows[all_rows.route == r][KEY].duplicated().any()) for r in ROUTES},
    "route_metrics_finite": {r: all(np.isfinite(v) for k, v in overall[r].items() if isinstance(v, float)) for r in ROUTES},
    "all_route_dates_96_keys": {r: overall[r]["all_dates_96_unique_keys"] for r in ROUTES},
    "all_route_resource_limits_valid": {r: overall[r]["all_daily_capacity_limits_valid"] and overall[r]["all_daily_budget_limits_valid"] for r in ROUTES},
    "all_route_actions_integer_and_bounded": {r: overall[r]["all_q_integer_and_item_bounded"] for r in ROUTES},
    "all_route_intervals_valid": {r: overall[r]["all_prediction_and_interval_bounds_valid"] for r in ROUTES},
    "first_truth_open_utc": first_open["first_open_utc"],
    "first_truth_open_receipt": "runs/R21/review/holdout/03-first-truth-open-command.json",
    "truth_identity_sha256": sha_bytes(truth_b), "truth_lock_sha256": evaluation_lock_sha,
    "initial_lock_sha256": initial_lock_sha, "execution_lock_sha256": execution_lock_sha,
}
validation["passed"] = (
    truth_duplicate_count == 0 and len(truth) == 4032
    and all(validation["route_key_uniqueness"].values()) and all(validation["route_metrics_finite"].values())
    and all(validation["all_route_dates_96_keys"].values()) and all(validation["all_route_resource_limits_valid"].values())
    and all(validation["all_route_actions_integer_and_bounded"].values()) and all(validation["all_route_intervals_valid"].values())
)

cols = KEY + ["route", "demand_units", "demand_point_units", "lower90_units", "upper90_units", "interval_level", "q_units", "error", "abs_error", "covered", "below", "above", "width", "interval_score", "shortage_loss_yuan", "waste_loss_yuan", "two_part_loss_yuan", "procurement_spend_yuan", "holiday", "activity_group", "horizon_day", "horizon_band"]
all_rows[cols].to_csv(OUT / "key_metrics.csv", index=False, float_format="%.12g")
daily.sort_values(["service_date", "route"]).to_csv(OUT / "daily_route_metrics.csv", index=False, float_format="%.12g")
daily_wide.sort_values("service_date").to_csv(OUT / "daily_route_differences.csv", index=False, float_format="%.12g")
groups.to_csv(OUT / "group_metrics.csv", index=False, float_format="%.12g")
(OUT / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
metrics = {
    "schema": "r21-independent-holdout-metrics/1", "validation": validation,
    "metric_definitions": {"bias": "mean(prediction - truth)", "coverage": "fraction with lower90 <= truth <= upper90",
        "below_rate": "fraction with truth < lower90", "above_rate": "fraction with truth > upper90",
        "interval_score": "width + 20*(lower-truth) below lower + 20*(truth-upper) above upper; width only in interval",
        "two_part_loss": "shortage_yuan*max(truth-q,0) + waste_yuan*max(q-truth,0)",
        "procurement": "sum procurement_yuan*integer q; constraint only, not added to two-part objective"},
    "route_source_hashes": route_source_hashes, "route_metrics": overall, "daily_pair_summary": pair_summary,
    "group_dimensions": {d: int(groups[groups.dimension == d].group.nunique()) for d in groups.dimension.unique()},
    "group_metrics_rows": len(groups),
    "no_model_selection_or_parameter_change": True,
    "no_significance_or_causal_test": True,
    "4032_keys_are_not_treated_as_independent_replicates": True,
}
(OUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"schema": metrics["schema"], "validation_passed": validation["passed"], "rows_per_route": validation["route_rows"],
                  "metrics": {r: {k: v for k, v in overall[r].items() if k in ("mae", "rmse", "bias_pred_minus_truth", "coverage", "below_rate", "above_rate", "mean_interval_width", "mean_interval_score", "shortage_yuan", "waste_yuan", "two_part_loss_yuan", "procurement_yuan", "q_units", "capacity_full_days", "budget_full_days")} for r in ROUTES},
                  "group_dimensions": metrics["group_dimensions"], "daily_pair_summary": pair_summary}, ensure_ascii=False, indent=2))
assert validation["passed"]
