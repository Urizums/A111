from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[4]
DOMAIN = ROOT / "runs/R23/review/clean-initial"
RAW = ROOT / "runs/R21/inputs/raw"
V2 = ROOT / "runs/R23/execution/v2"
KEY = ["service_date", "store_id", "item_id"]
TOL = 1e-8


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_hash(path: Path, expected: str) -> dict:
    observed = sha(path)
    return {"path": path.relative_to(ROOT).as_posix(), "size_bytes": path.stat().st_size,
            "sha256": observed, "matches_expected": observed == expected}


def main() -> None:
    cfg = json.loads((DOMAIN / "verifier-config.json").read_text(encoding="utf-8"))
    freeze = json.loads((DOMAIN / "freeze.json").read_text(encoding="utf-8"))
    self_id = assert_hash(Path(__file__), freeze["verifier_sha256"])
    config_id = assert_hash(DOMAIN / "verifier-config.json", freeze["config_sha256"])
    if not self_id["matches_expected"] or not config_id["matches_expected"]:
        raise RuntimeError("independent verifier/config freeze mismatch")

    source_checks = [assert_hash(ROOT / item["path"], item["sha256"])
                     for item in freeze["source_files"]]
    if not all(x["matches_expected"] for x in source_checks):
        raise RuntimeError("a frozen source identity changed")

    raw = {p.stem: pd.read_csv(p) for p in sorted(RAW.glob("*.csv"))}
    raw["decision"] = json.loads((RAW / "decision.json").read_text(encoding="utf-8"))
    demand = raw["demand_reports"].copy()
    demand["available_at"] = pd.to_datetime(
        demand["available_at"], format="%Y-%m-%dT%H:%M:%S"
    ).dt.tz_localize(cfg["timezone"])
    promotions = raw["promotions"].copy()
    promotions["announced_at"] = pd.to_datetime(
        promotions["announced_at"], format="%Y-%m-%dT%H:%M:%S"
    ).dt.tz_localize(cfg["timezone"])
    origin = pd.Timestamp(cfg["origin"])
    if origin.tzinfo is None:
        origin = origin.tz_localize(cfg["timezone"])
    cutoff = pd.Timestamp(cfg["evaluation_label_cutoff"])
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize(cfg["timezone"])
    target = cfg["target_service_date"]

    # Independently select the latest revision visible by the decision origin.
    eligible = demand[
        (demand["service_date"] < origin.strftime("%Y-%m-%d"))
        & (demand["available_at"] <= origin)
    ].copy()
    train = eligible.sort_values(KEY + ["revision", "available_at"]).drop_duplicates(
        KEY, keep="last"
    ).copy()
    if train.empty or train.duplicated(KEY).any():
        raise AssertionError("invalid training snapshot")
    if not train["available_at"].le(origin).all() or not train["service_date"].lt(
        origin.strftime("%Y-%m-%d")
    ).all():
        raise AssertionError("ineligible training label entered the snapshot")

    later = demand[
        (demand["service_date"] < target) & (demand["available_at"] > origin)
    ].copy()
    later_keys = set(map(tuple, later[KEY].drop_duplicates().to_numpy()))
    activated = train[train[KEY].apply(tuple, axis=1).isin(later_keys)].copy()
    if activated.empty or not activated["available_at"].le(origin).all():
        raise AssertionError("late-publication boundary was not activated safely")

    stores = sorted(raw["stores"]["store_id"].astype(str))
    items = sorted(raw["items"]["item_id"].astype(str))
    keys = pd.DataFrame([(target, s, i) for s in stores for i in items], columns=KEY)
    if len(stores) != 12 or len(items) != 8 or len(keys) != 96 or keys.duplicated(KEY).any():
        raise AssertionError("target key grid differs from original source dimensions")

    known_promo = promotions[promotions["announced_at"] <= origin].copy()
    known_promo = known_promo.sort_values("announced_at").drop_duplicates(KEY, keep="last")
    recent_start = (origin - pd.Timedelta(days=56)).strftime("%Y-%m-%d")
    recent_train = train[train["service_date"] >= recent_start]
    promo_means = recent_train[KEY].merge(
        known_promo[KEY + ["discount_fraction"]], on=KEY, how="inner", validate="one_to_one"
    ).groupby("item_id")["discount_fraction"].mean()

    def features(frame: pd.DataFrame) -> pd.DataFrame:
        z = frame.merge(raw["calendar"], on="service_date", validate="many_to_one")
        z = z.merge(raw["stores"], on="store_id", validate="many_to_one")
        z = z.merge(
            known_promo[KEY + ["discount_fraction", "announced_at"]],
            on=KEY, how="left", validate="one_to_one"
        )
        z["discount_fraction"] = z["discount_fraction"].fillna(
            z["item_id"].map(promo_means)
        ).fillna(0.0)
        if len(z) != len(frame) or z.duplicated(KEY).any():
            raise AssertionError("feature joins altered key cardinality")
        if not z["announced_at"].dropna().le(origin).all():
            raise AssertionError("post-origin promotion announcement entered features")
        z["time30"] = (
            pd.to_datetime(z["service_date"]) - pd.Timestamp("2026-05-01")
        ).dt.days / 30.0
        return z

    def matrix(z: pd.DataFrame) -> np.ndarray:
        si = z["store_id"].str[1:].astype(int).to_numpy() - 1
        ki = z["item_id"].str[1:].astype(int).to_numpy() - 1
        a = np.zeros((len(z), 169), dtype=float)
        idx = np.arange(len(z))
        a[idx, si * 8 + ki] = 1.0
        a[idx, 96 + ki * 7 + z["weekday_monday_zero"].to_numpy(dtype=int)] = 1.0
        a[idx, 152 + ki] = z["time30"].to_numpy(dtype=float)
        a[idx, 160 + ki] = z["discount_fraction"].to_numpy(dtype=float)
        a[:, 168] = z["holiday"].to_numpy(dtype=float) * 0.3
        return a

    train_x = features(train[KEY])
    target_x = features(keys)
    ridge = Ridge(alpha=10, fit_intercept=False, solver="cholesky")
    ridge.fit(matrix(train_x), train["demand_units"].to_numpy(dtype=float))
    ridge_pred = np.maximum(ridge.predict(matrix(target_x)), 0.0)

    window = train[
        (train["service_date"] >= recent_start) & (train["service_date"] < target)
    ].copy()
    wd = int(target_x["weekday_monday_zero"].iloc[0])
    with_wd = window.assign(weekday=pd.to_datetime(window["service_date"]).dt.weekday)
    by_pair_day = with_wd.groupby(["store_id", "item_id", "weekday"])["demand_units"].median()
    by_pair = window.groupby(["store_id", "item_id"])["demand_units"].median()
    by_item_day = with_wd.groupby(["item_id", "weekday"])["demand_units"].median()
    weekly_pred = []
    fallback = {"store_item": 0, "item_weekday": 0}
    for r in keys.itertuples(index=False):
        k = (r.store_id, r.item_id, wd)
        if k in by_pair_day.index:
            v = by_pair_day.loc[k]
        elif (r.store_id, r.item_id) in by_pair.index:
            v = by_pair.loc[(r.store_id, r.item_id)]
            fallback["store_item"] += 1
        elif (r.item_id, wd) in by_item_day.index:
            v = by_item_day.loc[(r.item_id, wd)]
            fallback["item_weekday"] += 1
        else:
            raise AssertionError("no weekly method value or fallback")
        weekly_pred.append(float(v))

    labels = demand[
        (demand["service_date"] == target) & (demand["available_at"] <= cutoff)
    ].sort_values(KEY + ["revision", "available_at"]).drop_duplicates(KEY, keep="last")
    actual = keys.merge(
        labels[KEY + ["demand_units", "revision", "available_at"]],
        on=KEY, how="left", validate="one_to_one"
    )
    if len(actual) != 96 or actual["demand_units"].isna().any():
        raise AssertionError("target labels are incomplete at the frozen cutoff")
    if actual["available_at"].le(origin).any():
        raise AssertionError("target outcome label is not strictly post-origin")

    emitted = pd.read_csv(V2 / "consumer-point-slice.csv")
    expected_methods = [m["method_id"] for m in cfg["methods"]]
    if len(emitted) != 192 or set(emitted["method_id"]) != set(expected_methods):
        raise AssertionError("output row count or method set mismatch")
    if emitted.duplicated(["method_id"] + KEY).any():
        raise AssertionError("duplicate method-key output")
    recomputed = {
        "shared_ridge10_consumer": ridge_pred,
        "weekly_median56_consumer": np.asarray(weekly_pred),
    }
    metric_results = {}
    row_checks = []
    for method in expected_methods:
        part = emitted[emitted["method_id"] == method].sort_values(KEY).reset_index(drop=True)
        expect_keys = keys.sort_values(KEY).reset_index(drop=True)
        if not part[KEY].equals(expect_keys):
            raise AssertionError(f"key set/order mismatch for {method}")
        predicted = recomputed[method]
        delta = np.abs(part["demand_point_units"].to_numpy(dtype=float) - predicted)
        if not np.isfinite(delta).all() or delta.max(initial=0.0) > TOL:
            raise AssertionError(f"independent predictions differ for {method}")
        if method == "shared_ridge10_consumer":
            method_output = part
        truth = actual.sort_values(KEY).reset_index(drop=True)
        if not np.array_equal(part["actual_demand_units"].to_numpy(), truth["demand_units"].to_numpy()):
            raise AssertionError(f"actual labels differ from point-in-time cutoff selection for {method}")
        if not np.array_equal(part["actual_revision"].to_numpy(), truth["revision"].to_numpy()):
            raise AssertionError(f"label revisions differ for {method}")
        emitted_time = pd.to_datetime(part["actual_available_at"], utc=True)
        true_time = pd.to_datetime(truth["available_at"], utc=True)
        if not emitted_time.equals(true_time):
            raise AssertionError(f"label availability timestamps differ for {method}")
        err = predicted - truth["demand_units"].to_numpy(dtype=float)
        metric_results[method] = {
            "mae_units_per_pair": float(np.mean(np.abs(err))),
            "rmse_units_per_pair": float(np.sqrt(np.mean(err ** 2))),
            "mean_signed_error_units_per_pair": float(np.mean(err)),
            "max_prediction_abs_diff": float(delta.max(initial=0.0)),
        }
        row_checks.append({"method_id": method, "rows": len(part), "unique_keys": int(part[KEY].drop_duplicates().shape[0]),
                           "prediction_match_within_tolerance": bool(delta.max(initial=0.0) <= TOL),
                           "labels_revision_time_match": True})

    report = json.loads((V2 / "consumer-point-slice-report.json").read_text(encoding="utf-8"))
    metrics_agree = {}
    for method, vals in metric_results.items():
        source_vals = report["metrics"][method]
        metrics_agree[method] = {
            k: abs(vals[k] - float(source_vals[k])) <= TOL
            for k in ["mae_units_per_pair", "rmse_units_per_pair", "mean_signed_error_units_per_pair"]
        }
        if not all(metrics_agree[method].values()):
            raise AssertionError(f"reported metric mismatch for {method}")

    # Verify both the raw file identities and the actual source-driven boundary.
    raw_lock = json.loads((ROOT / "runs/R21/input-lock.json").read_text(encoding="utf-8"))
    raw_expected = {Path(x["path"]).name: x["sha256"] for x in raw_lock["files"]
                    if "/raw/" in x["path"]}
    raw_identities = [assert_hash(RAW / name, expected) for name, expected in sorted(raw_expected.items())]
    if not all(x["matches_expected"] for x in raw_identities):
        raise AssertionError("R21 raw identity mismatch")

    result = {
        "schema": "r23-independent-consumer-recomputation/1",
        "state": "computed_independent_reproduction",
        "reproduction_source": str(Path(__file__).relative_to(ROOT)).replace("\\", "/"),
        "reproduction_code_sha256": sha(Path(__file__)),
        "configuration_sha256": sha(DOMAIN / "verifier-config.json"),
        "slice": {"origin": origin.isoformat(), "target_service_date": target,
                  "evaluation_label_cutoff": cutoff.isoformat(), "method_ids": expected_methods},
        "identity_checks": {"frozen_source_files": source_checks, "raw_lock_files": raw_identities,
                            "verifier": self_id, "config": config_id},
        "observations": {
            "training_snapshot_rows": int(len(train)),
            "training_window_56d_rows": int(len(window)),
            "target_pairs": int(len(keys)),
            "later_published_training_rows": int(len(later)),
            "visible_training_keys_with_later_rows": int(len(activated)),
            "excluded_later_rows_do_not_replace_visible_snapshot": True,
            "target_labels_available_after_origin": int(actual["available_at"].gt(origin).sum()),
            "target_labels_selected_at_cutoff": int(len(actual)),
            "target_promotions_known_at_origin": int(target_x["announced_at"].notna().sum()),
            "target_promotions_published_after_origin": int((target_x["announced_at"] > origin).sum()),
            "weekly_fallback_counts": fallback,
            "output_columns": list(emitted.columns),
            "output_rows_and_predictions": row_checks,
            "recomputed_metrics": metric_results,
            "reported_metrics_match": metrics_agree,
            "interval_columns_present": any(c in emitted.columns for c in ["lower90_units", "upper90_units", "interval_level"]),
            "replenishment_column_present": "q_units" in emitted.columns,
        },
        "independent_limitations": cfg["scope_limits"],
        "runtime": {"python": sys.version.split()[0], "platform": platform.platform(),
                    "pandas": pd.__version__, "numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "telemetry": {"actual_model": None, "tokens": None, "cost": None},
    }
    (DOMAIN / "recomputation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
