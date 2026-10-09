from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "runs/R23/execution/v2"
RAW = ROOT / "runs/R21/inputs/raw"
CONFIG_PATH = OUT / "consumer-slice-config.json"
FREEZE_PATH = OUT / "consumer-slice-freeze.json"
KEY = ["service_date", "store_id", "item_id"]
TABLES = ["demand_reports.csv", "stores.csv", "items.csv", "calendar.csv", "promotions.csv", "weather.csv", "decision.json"]
EXPECTED_RAW_HASHES = {
    "calendar.csv": "1676e38b047d96b7b66d294d85673f86f876826e96c03b29200c340cad24fbfd",
    "decision.json": "7540cf7083f0163f60e431e8a75f552baa86ed174869f3c55aac69f904056753",
    "demand_reports.csv": "80a3a994b8285caa0b48bf433724d476693509656b32cff99b8a6798eebd666b",
    "items.csv": "bc81cb9ad6c28e108bbd4e1fcd682c4c8aa71e40c22e7ff8411b545a4fe65167",
    "promotions.csv": "580c15bc827a8d86113c8ceb47edce2bfa94b317f4d88ff3a45b3e7c0c55bb45",
    "stores.csv": "65ce636c8d7f6c72df3d06a1e84e59d122f33dab1c223d4e9963982c9bf54220",
    "weather.csv": "8dd38ca926ba59b0de292e0b57a3e07cb4353d892cc3dd242aea8cc6f56c8403",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    if sha(CONFIG_PATH) != freeze["config_sha256"] or sha(Path(__file__)) != freeze["code_sha256"]:
        raise RuntimeError("frozen code/config hash mismatch")
    raw_hashes = {name: sha(RAW / name) for name in TABLES}
    if any(raw_hashes[k] != v for k, v in EXPECTED_RAW_HASHES.items()):
        raise RuntimeError("raw source identity differs from recorded R21 input identity")

    t = {name[:-4]: pd.read_csv(RAW / name) for name in TABLES if name.endswith(".csv")}
    t["decision"] = json.loads((RAW / "decision.json").read_text(encoding="utf-8"))
    origin = pd.Timestamp(config["origin"])
    cutoff = pd.Timestamp(config["evaluation_label_cutoff"])
    target = config["target_service_date"]
    origin_utc_naive = origin.tz_localize(None)
    for name, col in [("demand_reports", "available_at"), ("promotions", "announced_at")]:
        t[name][col] = pd.to_datetime(t[name][col], format="%Y-%m-%dT%H:%M:%S").dt.tz_localize("Asia/Shanghai")

    demand = t["demand_reports"]
    eligible_train = demand[(demand.service_date < origin.strftime('%Y-%m-%d')) & (demand.available_at <= origin)]
    train = eligible_train.sort_values(KEY + ["revision", "available_at"]).drop_duplicates(KEY, keep="last").copy()
    if train.empty or not train.available_at.le(origin).all() or not train.service_date.lt(origin.strftime('%Y-%m-%d')).all():
        raise AssertionError("point-in-time training snapshot contains an ineligible row")
    if train.duplicated(KEY).any():
        raise AssertionError("training snapshot keys are duplicated")

    # Ensure the selected real source case exercises the late-revision boundary.
    later = demand[(demand.service_date < target) & (demand.available_at > origin)]
    later_keys = set(map(tuple, later[KEY].drop_duplicates().to_numpy()))
    boundary_rows = train[train[KEY].apply(tuple, axis=1).isin(later_keys)]
    if boundary_rows.empty:
        raise AssertionError("no actual later-published training revision activated the boundary")
    if not boundary_rows.available_at.le(origin).all():
        raise AssertionError("late-published report entered the origin snapshot")

    stores = sorted(t["stores"].store_id)
    items = sorted(t["items"].item_id)
    target_keys = pd.DataFrame([(target, s, k) for s in stores for k in items], columns=KEY)
    if len(target_keys) != 96 or target_keys.duplicated(KEY).any():
        raise AssertionError("target key construction did not produce exactly 96 unique pairs")

    promo = t["promotions"]
    promo = promo[promo.announced_at <= origin].sort_values(["announced_at"])
    promo = promo.drop_duplicates(KEY, keep="last")
    recent_start = (origin - pd.Timedelta(days=56)).strftime("%Y-%m-%d")
    recent_train = train[train.service_date >= recent_start]
    recent_promo = recent_train[KEY].merge(
        promo[KEY + ["discount_fraction"]], on=KEY, how="inner", validate="one_to_one"
    )
    item_impute = recent_promo.groupby("item_id").discount_fraction.mean()

    def feature_frame(keys: pd.DataFrame) -> pd.DataFrame:
        x = keys.merge(t["calendar"], on="service_date", how="left", validate="many_to_one")
        x = x.merge(t["stores"], on="store_id", how="left", validate="many_to_one")
        x = x.merge(
            promo[KEY + ["discount_fraction", "announced_at"]], on=KEY, how="left", validate="one_to_one"
        )
        x["promo_known"] = x.discount_fraction.notna()
        x["discount_fraction"] = x.discount_fraction.fillna(x.item_id.map(item_impute)).fillna(0.0)
        x["time30"] = (pd.to_datetime(x.service_date) - pd.Timestamp("2026-05-01")).dt.days / 30.0
        if len(x) != len(keys) or x.duplicated(KEY).any():
            raise AssertionError("feature joins changed key cardinality")
        if not x.announced_at.dropna().le(origin).all():
            raise AssertionError("future promotion announcement leaked into feature rows")
        return x

    train_x = feature_frame(train[KEY])
    target_x = feature_frame(target_keys)

    def matrix(x: pd.DataFrame) -> np.ndarray:
        s = x.store_id.str[1:].astype(int).to_numpy() - 1
        k = x.item_id.str[1:].astype(int).to_numpy() - 1
        a = np.zeros((len(x), 169), dtype=float)
        row = np.arange(len(x))
        a[row, s * 8 + k] = 1.0
        a[row, 96 + k * 7 + x.weekday_monday_zero.to_numpy(dtype=int)] = 1.0
        a[row, 152 + k] = x.time30.to_numpy()
        a[row, 160 + k] = x.discount_fraction.to_numpy()
        a[:, 168] = x.holiday.to_numpy() * 0.3
        return a

    ridge = Ridge(alpha=10, fit_intercept=False, solver="cholesky")
    ridge.fit(matrix(train_x), train.demand_units.to_numpy(dtype=float))
    ridge_point = np.maximum(ridge.predict(matrix(target_x)), 0.0)

    window_start = (origin - pd.Timedelta(days=56)).strftime("%Y-%m-%d")
    window = train[(train.service_date >= window_start) & (train.service_date < target)].copy()
    weekday = int(target_x.weekday_monday_zero.iloc[0])
    grouped = window.assign(weekday=pd.to_datetime(window.service_date).dt.weekday).groupby(
        ["store_id", "item_id", "weekday"]
    ).demand_units.median()
    pair_median = window.groupby(["store_id", "item_id"]).demand_units.median()
    item_weekday = window.assign(weekday=pd.to_datetime(window.service_date).dt.weekday).groupby(
        ["item_id", "weekday"]
    ).demand_units.median()
    weekly = []
    fallback_counts = {"store_item": 0, "item_weekday": 0}
    for row in target_keys.itertuples(index=False):
        key = (row.store_id, row.item_id, weekday)
        if key in grouped.index:
            value = grouped.loc[key]
        elif (row.store_id, row.item_id) in pair_median.index:
            value = pair_median.loc[(row.store_id, row.item_id)]
            fallback_counts["store_item"] += 1
        elif (row.item_id, weekday) in item_weekday.index:
            value = item_weekday.loc[(row.item_id, weekday)]
            fallback_counts["item_weekday"] += 1
        else:
            raise AssertionError("weekly_median56 has no frozen fallback for a target key")
        weekly.append(float(value))

    labels = demand[(demand.service_date == target) & (demand.available_at <= cutoff)]
    labels = labels.sort_values(KEY + ["revision", "available_at"]).drop_duplicates(KEY, keep="last").copy()
    actual = target_keys.merge(labels[KEY + ["demand_units", "revision", "available_at"]], on=KEY, how="left", validate="one_to_one")
    if len(actual) != 96 or actual.demand_units.isna().any():
        raise AssertionError("target labels are incomplete at the frozen evaluation cutoff")
    if actual["available_at"].le(origin).any():
        # This is data leakage for an outcome label; score labels must be post-origin.
        raise AssertionError("unexpected target outcome label available by forecast origin")

    rows = []
    score = {}
    for method, pred in [("shared_ridge10_consumer", ridge_point), ("weekly_median56_consumer", np.asarray(weekly))]:
        err = pred - actual.demand_units.to_numpy(dtype=float)
        score[method] = {
            "mae_units_per_pair": float(np.mean(np.abs(err))),
            "rmse_units_per_pair": float(np.sqrt(np.mean(err ** 2))),
            "mean_signed_error_units_per_pair": float(np.mean(err)),
        }
        for i, key in enumerate(target_keys.itertuples(index=False)):
            rows.append({
                "service_date": key.service_date,
                "store_id": key.store_id,
                "item_id": key.item_id,
                "method_id": method,
                "demand_point_units": float(pred[i]),
                "actual_demand_units": int(actual.demand_units.iloc[i]),
                "actual_revision": int(actual.revision.iloc[i]),
                "actual_available_at": actual.available_at.iloc[i].isoformat(),
            })
    output = pd.DataFrame(rows)
    output.to_csv(OUT / "consumer-point-slice.csv", index=False, encoding="utf-8", float_format="%.10f")
    report = {
        "state": "computed one-day consumer slice; not accepted",
        "slice_id": config["slice_id"],
        "origin": config["origin"],
        "target_service_date": target,
        "evaluation_label_cutoff": config["evaluation_label_cutoff"],
        "source_sha256": raw_hashes,
        "config_sha256": sha(CONFIG_PATH),
        "code_sha256": sha(Path(__file__)),
        "input_rows": {
            "training_snapshot": int(len(train)),
            "training_window_56d": int(len(window)),
            "target_pairs": int(len(actual)),
            "later_published_training_rows_excluded": int(len(later)),
            "visible_training_keys_with_later_after_origin_rows": int(len(boundary_rows)),
            "target_labels_post_origin": int(actual.available_at.gt(origin).sum()),
            "target_promotion_known_at_origin": int(target_x.promo_known.sum()),
            "target_promotion_unknown_at_origin": int((~target_x.promo_known).sum()),
        },
        "weekly_fallback_counts": fallback_counts,
        "metrics": score,
        "assertions": {
            "96_unique_target_keys": True,
            "all_training_labels_visible_by_origin": True,
            "training_service_dates_precede_target": True,
            "later_revision_boundary_activated_and_excluded": True,
            "target_labels_scored_only_after_origin_at_cutoff": True,
            "promotion_announcements_at_or_before_origin": True,
            "weather_and_settlement_excluded": True,
        },
        "excluded_claims": config["scope_limits"],
        "runtime": {"python": "3.12", "pandas": pd.__version__, "numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "telemetry": {"actual_model": None, "tokens": None, "cost": None},
    }
    (OUT / "consumer-point-slice-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
