"""Compare the frozen independent reconstruction with permitted R22 artifacts."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[5]
REBUILD = ROOT / "runs/R22/review/initial/rebuild-v5"
PRODUCTION = ROOT / "runs/R22/execution/science-v1"
REPORT = ROOT / "runs/R22/review/initial"
KEY = ["origin", "method_id", "service_date", "store_id", "item_id"]


def read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def same_values(left: pd.Series, right: pd.Series, tol=1e-8) -> tuple[bool, float | None]:
    if len(left) != len(right):
        return False, None
    if pd.api.types.is_numeric_dtype(left) or pd.api.types.is_numeric_dtype(right):
        a, b = pd.to_numeric(left, errors="coerce").to_numpy(dtype=float), pd.to_numeric(right, errors="coerce").to_numpy(dtype=float)
        if np.isnan(a).all() and np.isnan(b).all():
            return True, 0.0
        ok = np.allclose(a, b, rtol=0, atol=tol, equal_nan=True)
        delta = np.abs(a - b)
        return bool(ok), float(np.nanmax(delta)) if np.isfinite(delta).any() else 0.0
    if pd.api.types.is_datetime64_any_dtype(left) or pd.api.types.is_datetime64_any_dtype(right) or any(x in str(left.name).lower() for x in ("available_at", "ready_at", "announced_at")):
        a = pd.to_datetime(left, utc=True, errors="coerce").astype("int64").to_numpy()
        b = pd.to_datetime(right, utc=True, errors="coerce").astype("int64").to_numpy()
        return bool(np.array_equal(a, b)), float(np.max(np.abs(a - b))) if len(a) else 0.0
    a = left.fillna("<NULL>").astype(str).to_numpy()
    b = right.fillna("<NULL>").astype(str).to_numpy()
    return bool(np.array_equal(a, b)), None


def compare_tables(left: pd.DataFrame, right: pd.DataFrame, keys: list[str], pairs: list[tuple[str, str]], label: str, tol=1e-8) -> dict:
    if len(left) != len(right) or left.duplicated(keys).any() or right.duplicated(keys).any():
        return {"label": label, "rows_left": int(len(left)), "rows_right": int(len(right)), "unique_key_match": False, "fields": {}}
    a = left.sort_values(keys).reset_index(drop=True)
    b = right.sort_values(keys).reset_index(drop=True)
    key_ok = True
    for key in keys:
        field_ok, _ = same_values(a[key], b[key], tol=tol)
        key_ok &= field_ok
    fields = {}
    for lcol, rcol in pairs:
        if lcol not in a or rcol not in b:
            fields[f"{lcol}={rcol}"] = {"equal": False, "reason": "missing column"}
            continue
        equal, max_delta = same_values(a[lcol], b[rcol], tol=tol)
        fields[f"{lcol}={rcol}"] = {"equal": equal, "max_abs_delta": max_delta}
    return {"label": label, "rows": int(len(a)), "unique_key_match": bool(key_ok), "fields": fields}


def main():
    own = read_csv(REBUILD / "results/keys.csv").rename(columns={"method": "method_id", "squared_error": "sq_error"})
    prod = read_csv(PRODUCTION / "results/keys.csv")
    all_pairs = [(field, field) for field in ("holiday", "promo_known", "weather_known", "horizon", "stage", "band", "actual", "actual_revision", "actual_available_at", "actual_raw_row", "point", "lower90", "upper90", "interval_level", "covered", "q_units", "shortage_yuan", "waste_yuan", "procurement_yuan", "abs_error", "sq_error", "interval_score", "pool_days")]
    key_cmp = compare_tables(own, prod, KEY, all_pairs, "full_key_reconstruction", tol=1e-7)
    comparisons = [key_cmp]

    # Author's separate forecast and action deliveries are checked against the raw reconstruction.
    for origin in ("2026-07-22", "2026-09-02", "2026-09-19"):
        for method in ("shared_ridge10", "weekly_mean56"):
            own_pred = read_csv(REBUILD / f"predictions/{origin}_{method}.csv")
            prod_pred = read_csv(PRODUCTION / f"predictions/{origin}_{method}.csv")
            comparisons.append(compare_tables(own_pred, prod_pred, ["service_date", "store_id", "item_id"], [(c, c) for c in ("method_id", "demand_point_units", "lower90_units", "upper90_units", "interval_level")], f"prediction_{origin}_{method}", tol=1e-8))
            own_q = read_csv(REBUILD / f"plans/{origin}_{method}.csv")
            prod_q = read_csv(PRODUCTION / f"plans/{origin}_{method}.csv")
            comparisons.append(compare_tables(own_q, prod_q, ["service_date", "store_id", "item_id"], [("method", "method_id"), ("q_units", "q_units")], f"action_{origin}_{method}", tol=0))

    # Independently rebuild source- and target-origin feature lineage for all permitted cached snapshots.
    recon_path = ROOT / "runs/R22/review/initial/source/independent_rebuild_v5.py"
    spec = importlib.util.spec_from_file_location("independent_rebuild_v5", recon_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    panel = module.RawPanel()
    for origin in ("2026-07-22T18:00:00", "2026-09-02T18:00:00", "2026-09-19T18:00:00"):
        tag = origin[:10]
        train = panel.snapshot(origin)
        cached_train = read_csv(PRODUCTION / f"data/train_{tag}.csv")
        comparisons.append(compare_tables(train, cached_train, module.KEY, [(c, c) for c in train.columns if c not in module.KEY], f"train_snapshot_{tag}", tol=0))
        train_features = panel.features(train[module.KEY], origin, train)
        cached_train_features = read_csv(PRODUCTION / f"data/train_features_{tag}.csv")
        comparisons.append(compare_tables(train_features, cached_train_features, module.KEY, [(c, c) for c in train_features.columns if c not in module.KEY], f"train_features_{tag}", tol=1e-12))
        lower = (module.timestamp(origin) - pd.Timedelta(days=56)).strftime("%Y-%m-%d")
        recent = train[train.service_date >= lower][module.KEY]
        known = panel.tables["promotions"]
        known = known[known.announced_at <= module.timestamp(origin)]
        promo_sources = recent.merge(known, on=module.KEY, validate="one_to_one")
        cached_promo = read_csv(PRODUCTION / f"data/promotion_imputation_sources_{tag}.csv")
        comparisons.append(compare_tables(promo_sources, cached_promo, module.KEY, [(c, c) for c in promo_sources.columns if c not in module.KEY], f"promotion_sources_{tag}", tol=1e-12))
        dates = pd.date_range(module.timestamp(origin).date() + pd.Timedelta(days=1), periods=42).strftime("%Y-%m-%d").tolist()
        grid = panel.grid(dates)
        target_features = panel.features(grid, origin, train)
        for method in ("shared_ridge10", "weekly_mean56"):
            cached_features = read_csv(PRODUCTION / f"data/predict_features_{tag}_{method}.csv")
            comparisons.append(compare_tables(target_features, cached_features, module.KEY, [(c, c) for c in target_features.columns if c not in module.KEY], f"predict_features_{tag}_{method}", tol=1e-12))

    # The production group matrices include all zero-activity cells; compare every declared category.
    group_map = {
        "overall": "overall", "early_late": "stage", "seven_day_band": "band", "activity": "activity",
        "activity_by_band": "activity_band", "activity_by_stage": "activity_stage", "horizon": "horizon",
        "store": "store", "item": "item",
    }
    metric_pairs = [(l, r) for l, r in (("n_keys", "rows"), ("n_days", "days"), ("status", "status"), ("mae", "mae"), ("rmse", "rmse"), ("bias", "bias"), ("coverage", "coverage"), ("below", "below"), ("above", "above"), ("mean_width", "width"), ("interval_score", "interval_score"), ("shortage_yuan_per_day", "shortage_per_day"), ("waste_yuan_per_day", "waste_per_day"), ("loss_yuan_per_day", "loss_per_day"), ("procurement_yuan_per_day", "procurement_per_day"), ("units_per_day", "q_per_day"))]
    for own_name, prod_name in group_map.items():
        own_group = read_csv(REBUILD / f"results/group_{own_name}.csv").rename(columns={"method": "method_id"})
        prod_group = read_csv(PRODUCTION / f"results/group_{prod_name}.csv")
        group_keys = ["origin", "method_id"] + [c for c in own_group.columns if c in {"stage", "band", "holiday", "horizon", "store_id", "item_id"}]
        comparisons.append(compare_tables(own_group, prod_group, group_keys, metric_pairs, f"groups_{own_name}", tol=1e-6))

    own_daily = read_csv(REBUILD / "results/daily.csv").rename(columns={"method": "method_id"})
    prod_daily = read_csv(PRODUCTION / "results/daily.csv")
    daily_pairs = [(l, r) for l, r in (("n_keys", "rows"), ("status", "status"), ("loss_yuan_per_day", "loss_per_day"), ("shortage_yuan_per_day", "shortage_per_day"), ("waste_yuan_per_day", "waste_per_day"), ("procurement_yuan_per_day", "procurement_per_day"), ("units_per_day", "q_per_day"), ("interval_score", "interval_score"))]
    comparisons.append(compare_tables(own_daily, prod_daily, ["origin", "method_id", "service_date"], daily_pairs, "daily_comparisons", tol=1e-6))
    own_solver = read_csv(REBUILD / "results/daily_solver.csv").rename(columns={"method": "method_id"})
    prod_solver = read_csv(PRODUCTION / "results/solver_daily.csv")
    solver_pairs = [(c, c) for c in ("objective_recomputed", "q_units", "procurement_yuan", "capacity_slack", "budget_slack_yuan", "status", "gap", "objective", "bound")]
    comparisons.append(compare_tables(own_solver, prod_solver, ["origin", "method_id", "service_date"], solver_pairs, "daily_solver_evidence", tol=1e-6))
    own_pair = read_csv(REBUILD / "results/paired_daily.csv")
    prod_pair = read_csv(PRODUCTION / "results/paired_daily.csv")
    pair_fields = [(c, c) for c in ("holiday", "horizon", "loss_per_day_shared_ridge10", "loss_per_day_weekly_mean56", "interval_score_shared_ridge10", "interval_score_weekly_mean56", "loss_W_minus_R", "score_W_minus_R")]
    comparisons.append(compare_tables(own_pair, prod_pair, ["origin", "service_date"], pair_fields, "paired_daily", tol=1e-6))

    # Independently regenerated entire scenario tensors and source-day memberships.
    own_membership = read_csv(REBUILD / "uncertainty/pool_membership.csv").rename(columns={"target_origin": "origin", "method": "method_id"})
    prod_membership = read_csv(PRODUCTION / "uncertainty/membership.csv")
    comparisons.append(compare_tables(own_membership, prod_membership, ["origin", "method_id", "source_origin", "service_date"], [(c, c) for c in ("coordinates", "ready_at", "eligible")], "all_residual_day_membership", tol=0))
    own_trace = read_csv(REBUILD / "source_rebuild/residual_coordinates_rebuilt.csv")
    prod_trace = read_csv(PRODUCTION / "uncertainty/source_coordinates_rebuilt.csv")
    prod_trace = prod_trace.rename(columns={"mature_actual": "mature_demand", "recomputed_point": "published_point", "error_recomputed": "error_rebuilt"})
    comparisons.append(compare_tables(own_trace, prod_trace, ["source_origin", "method_id"] + ["service_date", "store_id", "item_id"], [(l, r) for l, r in (("revision", "revision"), ("available_at", "available_at"), ("raw_row", "raw_row"), ("raw_hash", "raw_hash"), ("train_snapshot_sha256", "train_snapshot_sha256"), ("published_point", "published_point"), ("mature_demand", "mature_demand"), ("error_rebuilt", "error_rebuilt"))], "all_rebuilt_source_coordinates", tol=1e-8))
    scenario_comparisons = []
    for origin in ("2026-07-22", "2026-09-02", "2026-09-19"):
        for method in ("shared_ridge10", "weekly_mean56"):
            ours = np.load(REBUILD / f"uncertainty/scenarios_{origin}_{method}.npz")
            theirs = np.load(PRODUCTION / f"uncertainty/scenarios_{origin}_{method}.npz")
            a, b = ours["demand_units"], theirs["demand_units"]
            scenario_comparisons.append({"origin": origin, "method": method, "shape_ours": list(a.shape), "shape_production": list(b.shape), "same_shape": a.shape == b.shape, "same_service_dates": np.array_equal(ours["service_dates"], theirs["service_dates"]), "same_residual_dates": np.array_equal(ours["residual_dates"], theirs["residual_dates"]), "max_abs_delta": float(np.max(np.abs(a - b))) if a.shape == b.shape else None})

    all_ok = all(comp.get("unique_key_match", False) and all(field.get("equal", False) for field in comp.get("fields", {}).values()) for comp in comparisons)
    all_scenarios_ok = all(x["same_shape"] and x["same_service_dates"] and x["same_residual_dates"] and x["max_abs_delta"] <= 1e-8 for x in scenario_comparisons)
    result = {
        "schema": "r22-independent-production-comparison/1",
        "comparisons": comparisons,
        "scenario_comparisons": scenario_comparisons,
        "all_table_comparisons_pass": bool(all_ok),
        "all_scenario_comparisons_pass": bool(all_scenarios_ok),
        "method": "row-level raw rebuild compared to permitted production data artifacts; no author summary/self-check used",
        "actual_model": None, "tokens": None, "cost": None,
    }
    out = REPORT / "comparison.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"comparison": str(out), "all_table_comparisons_pass": all_ok, "all_scenario_comparisons_pass": all_scenarios_ok}, ensure_ascii=False))


if __name__ == "__main__":
    main()
