"""Independent R21 historical/final-route reconstruction from raw inputs."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csr_matrix

ROOT = Path("runs/R21")
EXEC = ROOT / "execution"
OUT = ROOT / "review/initial"
RAW = ROOT / "inputs/raw"
KEY = ["service_date", "store_id", "item_id"]
ORIGIN_FINAL = pd.Timestamp("2026-10-31 18:00:00", tz="Asia/Shanghai")
LABEL_CUTOFF = pd.Timestamp("2026-11-04 18:00:00", tz="Asia/Shanghai")


def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_csv(name):
    return pd.read_csv(RAW / f"{name}.csv", keep_default_na=True)


tables = {n: load_csv(n) for n in ["demand_reports", "stores", "items", "calendar", "promotions", "weather"]}
for frame in tables.values():
    for col in ["available_at", "announced_at"]:
        if col in frame:
            frame[col] = pd.to_datetime(frame[col], format="%Y-%m-%dT%H:%M:%S", errors="raise").dt.tz_localize("Asia/Shanghai")
decision = json.loads((RAW / "decision.json").read_text(encoding="utf-8"))
conf = json.loads((EXEC / "source/v1/config.json").read_text(encoding="utf-8"))
stores = sorted(tables["stores"].store_id.tolist())
items = sorted(tables["items"].item_id.tolist())
pairs = [(s, k) for s in stores for k in items]
coords = [(s, k) for s, k in pairs]
par = tables["items"].set_index("item_id")
cost = np.array([par.loc[k, "procurement_yuan"] for s, k in pairs], dtype=float)
shortage = np.array([par.loc[k, "shortage_yuan"] for s, k in pairs], dtype=float)
waste = np.array([par.loc[k, "waste_yuan"] for s, k in pairs], dtype=float)
maxq = np.array([par.loc[k, "daily_max_units"] for s, k in pairs], dtype=int)

reports = tables["demand_reports"].copy()
reports["_receiver_raw_row"] = np.arange(2, len(reports) + 2)
dedup_cols = [c for c in reports.columns if c != "_receiver_raw_row"]
exact_dupes = int(reports.duplicated(subset=dedup_cols).sum())
reports = reports.drop_duplicates(subset=dedup_cols).copy()
conflicts = []
for k, g in reports.groupby(KEY + ["revision"], sort=False):
    if len(g) > 1:
        conflicts.append(list(k))
assert not conflicts


def latest_at(frame, cutoff, *, exclude_day=None):
    x = frame[frame.available_at <= cutoff].copy()
    if exclude_day is not None:
        x = x[x.service_date < exclude_day]
    x = x.sort_values(KEY + ["revision", "available_at"])
    return x.drop_duplicates(KEY, keep="last").sort_values(KEY).reset_index(drop=True)


eval_labels = latest_at(reports, LABEL_CUTOFF)
eval_labels = eval_labels[eval_labels.service_date <= decision["origin"][:10]].copy().sort_values(KEY).reset_index(drop=True)
assert len(eval_labels) == 184 * 96 and not eval_labels.duplicated(KEY).any()


def snapshot(origin):
    return latest_at(reports, origin, exclude_day=origin.strftime("%Y-%m-%d"))


def grid(dates):
    return pd.DataFrame([(d, s, k) for d in dates for s, k in pairs], columns=KEY)


def feature_frame(g, origin, train):
    promo = tables["promotions"]
    promo_known = promo[promo.announced_at <= origin]
    x = g.merge(tables["calendar"], on="service_date", how="left", validate="many_to_one")
    x = x.merge(tables["stores"], on="store_id", how="left", validate="many_to_one")
    x = x.merge(promo_known[KEY + ["discount_fraction", "announced_at"]], on=KEY, how="left", validate="one_to_one")
    x["promo_known"] = x.discount_fraction.notna().astype(int)
    recent = train[train.service_date >= (origin - pd.Timedelta(days=56)).strftime("%Y-%m-%d")][KEY]
    recent = recent.merge(promo_known[KEY + ["discount_fraction"]], on=KEY, how="inner", validate="one_to_one")
    means = recent.groupby("item_id").discount_fraction.mean()
    x["discount_fraction"] = x.discount_fraction.fillna(x.item_id.map(means)).fillna(0.0)
    weather = tables["weather"]
    forecasts = weather[(weather.kind == "forecast") & (weather.available_at <= origin)].sort_values("available_at")
    forecasts = forecasts.drop_duplicates(["service_date", "zone_id"], keep="last")
    x = x.merge(forecasts[["service_date", "zone_id", "rain_mm", "available_at"]].rename(columns={"available_at": "weather_available_at"}), on=["service_date", "zone_id"], how="left", validate="many_to_one")
    x["weather_known"] = x.weather_available_at.notna().astype(int)
    x["time30"] = (pd.to_datetime(x.service_date) - pd.Timestamp("2026-05-01")).dt.days / 30.0
    x["origin"] = origin.isoformat()
    assert len(x) == len(g) and not x.duplicated(KEY).any()
    assert x.announced_at.dropna().le(origin).all() and x.weather_available_at.dropna().le(origin).all()
    return x


def matrix(x):
    m = np.zeros((len(x), 169), dtype=float)
    si = x.store_id.str[1:].astype(int).to_numpy() - 1
    ki = x.item_id.str[1:].astype(int).to_numpy() - 1
    ix = np.arange(len(x))
    m[ix, si * 8 + ki] = 1.0
    m[ix, 96 + ki * 7 + x.weekday_monday_zero.to_numpy(dtype=int)] = 1.0
    m[ix, 152 + ki] = x.time30.to_numpy(float)
    m[ix, 160 + ki] = x.discount_fraction.to_numpy(float)
    m[:, 168] = x.holiday.to_numpy(float) * 0.3
    return m


def forecast(origin, train, g, candidate):
    feats = feature_frame(g, origin, train)
    if candidate["kind"] == "ridge":
        X = matrix(feature_frame(train[KEY], origin, train))
        y = train.demand_units.to_numpy(float)
        beta = np.linalg.solve(X.T @ X + 10.0 * np.eye(169), X.T @ y)
        p = np.maximum(matrix(feats) @ beta, 0.0)
    else:
        recent = train[train.service_date >= (origin - pd.Timedelta(days=candidate["window"])).strftime("%Y-%m-%d")].copy()
        recent["weekday"] = pd.to_datetime(recent.service_date).dt.weekday
        by_week = recent.groupby(["store_id", "item_id", "weekday"]).demand_units.mean()
        fallback = train.groupby(["store_id", "item_id"]).demand_units.mean()
        day = pd.to_datetime(feats.service_date).dt.weekday.to_numpy()
        p = np.array([by_week.get((s, k, wd), fallback.get((s, k), np.nan)) for s, k, wd in zip(feats.store_id, feats.item_id, day)], dtype=float)
        p = np.maximum(p, 0.0)
    return p.reshape(-1, 96), feats


def optimize(scenarios, cap=1600, budget=6000):
    s = np.asarray(scenarios, dtype=float)
    assert s.ndim == 2 and s.shape[1] == 96 and np.isfinite(s).all() and (s >= 0).all()
    qgrid = np.arange(56, dtype=float)
    g = (np.maximum(s[:, :, None] - qgrid, 0) * shortage[None, :, None] + np.maximum(qgrid - s[:, :, None], 0) * waste[None, :, None]).mean(axis=0)
    gains = g[:, :-1] - g[:, 1:]
    assert (np.diff(gains, axis=1) <= 1e-7).all()
    inds = np.array([(i, j) for i in range(96) for j in range(int(maxq[i])) if gains[i, j] > 1e-10], dtype=int)
    if len(inds) == 0:
        return np.zeros(96, dtype=int), float(g[:, 0].sum()), {"capacity": 0, "budget": 0}
    c = -gains[inds[:, 0], inds[:, 1]]
    cons = csr_matrix(np.vstack([np.ones(len(inds)), cost[inds[:, 0]]]))
    result = milp(c, integrality=np.ones(len(c)), bounds=Bounds(0, 1), constraints=LinearConstraint(cons, [-np.inf, -np.inf], [cap, budget]), options={"mip_rel_gap": 1e-9})
    assert result.x is not None and result.success
    q = np.bincount(inds[:, 0], weights=np.rint(result.x), minlength=96).astype(int)
    assert (q >= 0).all() and (q <= maxq).all() and int(q.sum()) <= cap and float(q @ cost) <= budget
    objective = float(g[np.arange(96), q].sum())
    assert abs(objective - (g[:, 0].sum() + result.fun)) < 1e-6
    return q, objective, {"capacity": int(q.sum()), "budget": float(q @ cost), "solver_status": int(result.status), "mip_gap": float(result.mip_gap)}


def quantiles(point, errors):
    scenarios = np.maximum(point[None, :, :] + errors[:, None, :], 0.0)
    lo = np.round(np.quantile(scenarios, 0.05, axis=0, method="linear"), 10)
    hi = np.round(np.quantile(scenarios, 0.95, axis=0, method="linear"), 10)
    return scenarios, lo, hi


def day_loss(q, y):
    sh = np.maximum(y - q, 0) * shortage
    wa = np.maximum(q - y, 0) * waste
    return sh, wa


def summarize(point, lo, hi, y, q, dates, route, stage, origin, features):
    out = []
    keys = []
    for i, d in enumerate(dates):
        sh, wa = day_loss(q[i], y[i])
        hol = int(tables["calendar"].loc[tables["calendar"].service_date == d, "holiday"].iloc[0])
        out.append({"stage": stage, "origin": origin.isoformat(), "service_date": d, "method_id": route, "mae": float(np.abs(point[i] - y[i]).mean()), "rmse": float(np.sqrt(np.square(point[i] - y[i]).mean())), "bias": float((point[i] - y[i]).mean()), "coverage": float(((y[i] >= lo[i]) & (y[i] <= hi[i])).mean()), "below": float((y[i] < lo[i]).mean()), "above": float((y[i] > hi[i]).mean()), "width": float((hi[i] - lo[i]).mean()), "shortage": float(sh.sum()), "waste": float(wa.sum()), "loss": float(sh.sum() + wa.sum()), "q_units": int(q[i].sum()), "procurement": float(q[i] @ cost), "holiday": hol})
        for j, (store_id, item_id) in enumerate(pairs):
            lower_miss = float(y[i, j] < lo[i, j])
            upper_miss = float(y[i, j] > hi[i, j])
            width = float(hi[i, j] - lo[i, j])
            keys.append({"stage": stage, "origin": origin.isoformat(), "service_date": d, "method_id": route, "holiday": hol, "horizon": i + 1, "step_band": "1-7" if i < 7 else "8-14", "store_id": store_id, "item_id": item_id, "point": float(point[i, j]), "actual": float(y[i, j]), "lower": float(lo[i, j]), "upper": float(hi[i, j]), "q_units": int(q[i, j]), "abs_error": float(abs(point[i, j] - y[i, j])), "sq_error": float((point[i, j] - y[i, j]) ** 2), "bias": float(point[i, j] - y[i, j]), "covered": float(lo[i, j] <= y[i, j] <= hi[i, j]), "below": lower_miss, "above": upper_miss, "width": width, "interval_score": width + 20.0 * (lo[i, j] - y[i, j]) * lower_miss + 20.0 * (y[i, j] - hi[i, j]) * upper_miss, "shortage": float(sh[j]), "waste": float(wa[j]), "loss": float(sh[j] + wa[j]), "procurement": float(q[i, j] * cost[j])})
    return out, keys


candidates = conf["candidates"]
origins = [conf["precalibration_origin"]] + conf["selection_origins"] + [conf["calibration_origin"]] + conf["validation_origins"]
residual_pool = {c["name"]: [] for c in candidates}
historical_rows = []
historical_key_rows = []
residual_audit = []
residual_coordinate_rows = []
pool_checks = []
train_audit = []
snapshot_comparisons = []
feature_comparisons = []
fit_audit = []
selection_rows = []
for origin_s in origins:
    origin = pd.Timestamp(origin_s).tz_localize("Asia/Shanghai")
    stage = "precalibration" if origin_s == conf["precalibration_origin"] else "selection" if origin_s in conf["selection_origins"] else "calibration" if origin_s == conf["calibration_origin"] else "validation"
    train = snapshot(origin)
    production_snapshot = pd.read_csv(EXEC / "science-v1" / "data" / f"train_{origin.strftime('%Y-%m-%d')}.csv")
    train_join = train.merge(production_snapshot, on=KEY, how="outer", suffixes=("_ind", "_prod"), indicator=True, validate="one_to_one")
    snap_equal = bool((train_join._merge == "both").all() and np.array_equal(train_join.demand_units_ind.to_numpy(), train_join.demand_units_prod.to_numpy()) and np.array_equal(train_join.revision_ind.to_numpy(), train_join.revision_prod.to_numpy()) and (pd.to_datetime(train_join.available_at_ind) == pd.to_datetime(train_join.available_at_prod)).all())
    snapshot_comparisons.append({"origin": origin_s, "independent_rows": len(train), "production_rows": len(production_snapshot), "keys_and_demand_revision_timestamps_equal": snap_equal, "max_service_date": train.service_date.max(), "max_available_at": train.available_at.max().isoformat()})
    dates = pd.date_range(origin.date() + pd.Timedelta(days=1), periods=14).strftime("%Y-%m-%d").tolist()
    g = grid(dates)
    labs = g.merge(eval_labels, on=KEY, how="left", validate="one_to_one")
    assert len(labs) == 1344 and labs.demand_units.notna().all()
    y = labs.demand_units.to_numpy(float).reshape(14, 96)
    train_audit.append({"origin": origin_s, "stage": stage, "train_rows": len(train), "train_unique_keys": int(train[KEY].drop_duplicates().shape[0]), "max_service_date": train.service_date.max(), "max_available_at": train.available_at.max().isoformat(), "late_labels_corrected_count": int((train.merge(eval_labels[KEY + ["demand_units"]], on=KEY, suffixes=("_asof", "_mature"), validate="one_to_one").eval("demand_units_asof != demand_units_mature")).sum())})
    for cand in candidates:
        name = cand["name"]
        point, feat = forecast(origin, train, g, cand)
        production_features = pd.read_csv(EXEC / "science-v1" / "data" / f"predict_features_{origin.strftime('%Y-%m-%d')}_{cand['name']}.csv")
        fjoin = feat.merge(production_features, on=KEY, how="outer", suffixes=("_ind", "_prod"), indicator=True, validate="one_to_one")
        fcols = ["weekday_monday_zero", "holiday", "promo_known", "discount_fraction", "time30", "weather_known", "rain_mm"]
        feq = (fjoin._merge == "both").all()
        fmax = {}
        for col in fcols:
            left, right = fjoin[f"{col}_ind"].to_numpy(float), fjoin[f"{col}_prod"].to_numpy(float)
            fmax[col] = float(np.nanmax(np.abs(left - right))) if np.isfinite(left - right).any() else 0.0
            feq = feq and bool(np.allclose(left, right, atol=1e-9, rtol=0, equal_nan=True))
        feature_comparisons.append({"origin": origin_s, "method_id": name, "key_and_feature_values_match": bool(feq), "max_abs_difference": fmax, "late_promo_or_weather_records_present": bool((feat.announced_at.notna() & (feat.announced_at > origin)).any() or (feat.weather_available_at.notna() & (feat.weather_available_at > origin)).any())})
        fit_audit.append({"origin": origin_s, "method_id": name, "prediction_keys": len(feat), "features_promo_known": int(feat.promo_known.sum()), "features_weather_known": int(feat.weather_known.sum()), "features_late_promo": int((feat.announced_at.notna() & (feat.announced_at > origin)).sum()), "features_late_weather": int((feat.weather_available_at.notna() & (feat.weather_available_at > origin)).sum())})
        ready = []
        for r in residual_pool[name]:
            eligible = r["service_date"] < origin.strftime("%Y-%m-%d") and r["ready_at"] <= origin and r["source_origin"] < origin
            pool_checks.append({"calibration_origin": origin_s, "method_id": name, "residual_day": r["service_date"], "source_origin": r["source_origin"].strftime("%Y-%m-%dT%H:%M:%S"), "ready_at": r["ready_at"].isoformat(), "coordinates": 96, "eligible": bool(eligible)})
            residual_audit.append({"calibration_origin": origin_s, "method_id": name, "service_date": r["service_date"], "source_origin": r["source_origin"], "ready_at": r["ready_at"].isoformat(), "coordinates": 96, "eligible": bool(eligible), "reason": "full exact mature version vector ready and day ended" if eligible else "mature version(s) not ready or service day not ended"})
            if eligible:
                ready.append(r)
        if stage != "precalibration":
            assert ready
            errors = np.stack([r["error"] for r in ready])
            scenarios, lo, hi = quantiles(point, errors)
            qarr = []
            for j in range(14):
                q, obj, resources = optimize(scenarios[:, j, :])
                qarr.append(q)
                if stage == "selection":
                    sh, wa = day_loss(q, y[j])
                    selection_rows.append({"origin": origin_s, "date": dates[j], "method_id": name, "loss": float(sh.sum() + wa.sum())})
            qarr = np.asarray(qarr)
            day_rows, key_rows = summarize(point, lo, hi, y, qarr, dates, name, stage, origin, feat)
            historical_rows.extend(day_rows)
            historical_key_rows.extend(key_rows)
        for j, d in enumerate(dates):
            day_labels = labs[labs.service_date == d]
            assert len(day_labels) == 96 and not day_labels.duplicated(KEY).any()
            versions = tuple((row.store_id, row.item_id, int(row.revision), row.available_at.isoformat()) for row in day_labels.itertuples())
            for coord_idx, row in enumerate(day_labels.to_dict("records")):
                day_index = dates.index(d)
                residual_coordinate_rows.append({"service_date": d, "store_id": row["store_id"], "item_id": row["item_id"], "revision": int(row["revision"]), "available_at": row["available_at"].isoformat(), "raw_row": int(row["_receiver_raw_row"]), "demand_units": int(row["demand_units"]), "method_id": name, "source_origin": origin_s, "point": float(point[day_index, coord_idx]), "error": float(y[day_index, coord_idx] - point[day_index, coord_idx]), "full_day_ready_at": day_labels.available_at.max().isoformat(), "coordinates": 96})
            residual_pool[name].append({"service_date": d, "source_origin": origin, "ready_at": day_labels.available_at.max(), "error": y[j] - point[j], "version_identity": versions})
            residual_audit.append({"source_origin": origin_s, "method_id": name, "service_date": d, "ready_at": day_labels.available_at.max().isoformat(), "coordinates": len(versions), "versions_sha256": hashlib.sha256(repr(versions).encode()).hexdigest(), "point_sha256": hashlib.sha256(point[j].astype("<f8").tobytes()).hexdigest(), "error_sha256": hashlib.sha256((y[j] - point[j]).astype("<f8").tobytes()).hexdigest()})

selection = pd.DataFrame(selection_rows)
selection_summary = selection.groupby("method_id").loss.mean().to_dict()
selected = min(candidates, key=lambda c: (selection_summary[c["name"]], candidates.index(c)))["name"]

# Refit each candidate on the final origin, using the same strict as-of snapshot.
final_train = snapshot(ORIGIN_FINAL)
production_final_snapshot = pd.read_csv(EXEC / "science-v1/data/final_train_snapshot.csv")
final_join = final_train.merge(production_final_snapshot, on=KEY, how="outer", suffixes=("_ind", "_prod"), indicator=True, validate="one_to_one")
final_snapshot_equal = bool((final_join._merge == "both").all() and np.array_equal(final_join.demand_units_ind.to_numpy(), final_join.demand_units_prod.to_numpy()) and np.array_equal(final_join.revision_ind.to_numpy(), final_join.revision_prod.to_numpy()) and (pd.to_datetime(final_join.available_at_ind) == pd.to_datetime(final_join.available_at_prod)).all())
snapshot_comparisons.append({"origin": ORIGIN_FINAL.isoformat(), "independent_rows": len(final_train), "production_rows": len(production_final_snapshot), "keys_and_demand_revision_timestamps_equal": final_snapshot_equal, "max_service_date": final_train.service_date.max(), "max_available_at": final_train.available_at.max().isoformat()})
final_dates = pd.date_range(decision["future_begin"], decision["future_end"]).strftime("%Y-%m-%d").tolist()
future_grid = grid(final_dates)
final_features = feature_frame(future_grid, ORIGIN_FINAL, final_train)
future_results = {}
for cand in candidates:
    name = cand["name"]
    point, feat = forecast(ORIGIN_FINAL, final_train, future_grid, cand)
    production_features = pd.read_csv(EXEC / "science-v1/data" / f"final_prediction_features_{name}.csv")
    fjoin = feat.merge(production_features, on=KEY, how="outer", suffixes=("_ind", "_prod"), indicator=True, validate="one_to_one")
    fcols = ["weekday_monday_zero", "holiday", "promo_known", "discount_fraction", "time30", "weather_known", "rain_mm"]
    feq = (fjoin._merge == "both").all()
    fmax = {}
    for col in fcols:
        left, right = fjoin[f"{col}_ind"].to_numpy(float), fjoin[f"{col}_prod"].to_numpy(float)
        fmax[col] = float(np.nanmax(np.abs(left - right))) if np.isfinite(left - right).any() else 0.0
        feq = feq and bool(np.allclose(left, right, atol=1e-9, rtol=0, equal_nan=True))
    feature_comparisons.append({"origin": ORIGIN_FINAL.isoformat(), "method_id": name, "key_and_feature_values_match": bool(feq), "max_abs_difference": fmax, "late_promo_or_weather_records_present": bool((feat.announced_at.notna() & (feat.announced_at > ORIGIN_FINAL)).any() or (feat.weather_available_at.notna() & (feat.weather_available_at > ORIGIN_FINAL)).any())})
    ready = [r for r in residual_pool[name] if r["source_origin"] < ORIGIN_FINAL and r["service_date"] < ORIGIN_FINAL.strftime("%Y-%m-%d") and r["ready_at"] <= ORIGIN_FINAL]
    for r in residual_pool[name]:
        eligible = r["source_origin"] < ORIGIN_FINAL and r["service_date"] < ORIGIN_FINAL.strftime("%Y-%m-%d") and r["ready_at"] <= ORIGIN_FINAL
        pool_checks.append({"calibration_origin": ORIGIN_FINAL.strftime("%Y-%m-%dT%H:%M:%S"), "method_id": name, "residual_day": r["service_date"], "source_origin": r["source_origin"].strftime("%Y-%m-%dT%H:%M:%S"), "ready_at": r["ready_at"].isoformat(), "coordinates": 96, "eligible": bool(eligible)})
    errors = np.stack([r["error"] for r in ready])
    scenarios, lo, hi = quantiles(point, errors)
    qdays = []
    objectives = []
    resources = []
    for j in range(42):
        q, obj, res = optimize(scenarios[:, j, :])
        qdays.append(q)
        objectives.append(obj)
        resources.append(res)
    qdays = np.asarray(qdays)
    future_results[name] = {"point": point, "lower": lo, "upper": hi, "q": qdays, "scenarios": scenarios, "residual_days": [r["service_date"] for r in ready], "objectives": objectives, "resources": resources}

# Compare direct reconstruction with frozen production outputs (never future actuals).
prod_comparison = {}
for name, independent in future_results.items():
    pdir = EXEC / "science-v1" / "future" / name
    p = pd.read_csv(pdir / "predictions.csv")
    q = pd.read_csv(pdir / "replenishment.csv")
    want = future_grid.copy()
    want["method_id"] = name
    want["demand_point_units"] = independent["point"].ravel()
    want["lower90_units"] = independent["lower"].ravel()
    want["upper90_units"] = independent["upper"].ravel()
    want["interval_level"] = .9
    wantq = future_grid.copy()
    wantq["method_id"] = name
    wantq["q_units"] = independent["q"].ravel()
    merged = want.merge(p, on=KEY + ["method_id"], suffixes=("_ind", "_prod"), validate="one_to_one")
    qmerged = wantq.merge(q, on=KEY + ["method_id"], suffixes=("_ind", "_prod"), validate="one_to_one")
    prod_comparison[name] = {"prediction_rows": len(p), "plan_rows": len(q), "prediction_keyset_equal": set(map(tuple, p[KEY].itertuples(index=False, name=None))) == set(map(tuple, future_grid[KEY].itertuples(index=False, name=None))), "max_abs_point_difference": float(np.max(np.abs(merged.demand_point_units_ind - merged.demand_point_units_prod))), "max_abs_lower_difference": float(np.max(np.abs(merged.lower90_units_ind - merged.lower90_units_prod))), "max_abs_upper_difference": float(np.max(np.abs(merged.upper90_units_ind - merged.upper90_units_prod))), "max_abs_interval_level_difference": float(np.max(np.abs(merged.interval_level_ind - merged.interval_level_prod))), "plan_exactly_equal": bool(np.array_equal(qmerged.q_units_ind.to_numpy(), qmerged.q_units_prod.to_numpy())), "independent_daily_resource_valid": bool(all(x["capacity"] <= 1600 and x["budget"] <= 6000 for x in independent["resources"])), "residual_pool_days": len(independent["residual_days"]), "first_last_residual_day": [independent["residual_days"][0], independent["residual_days"][-1]]}
    plan_integral = bool(np.isfinite(q.q_units).all() and np.equal(q.q_units, np.floor(q.q_units)).all() and q.q_units.min() >= 0 and q.q_units.max() <= 55)
    daily_plan = q.groupby("service_date").agg(q_units=("q_units", "sum"), budget=("q_units", lambda z: float((z.to_numpy() * cost).sum())))
    row_valid = bool(len(p) == 4032 and len(q) == 4032 and not p.duplicated(KEY).any() and not q.duplicated(KEY).any())
    point_order_valid = bool(np.isfinite(merged[["demand_point_units_prod", "lower90_units_prod", "upper90_units_prod", "interval_level_prod"]].to_numpy()).all() and (merged.lower90_units_prod <= merged.demand_point_units_prod).all() and (merged.demand_point_units_prod <= merged.upper90_units_prod).all() and np.allclose(merged.interval_level_prod, .9, atol=1e-12))
    prod_comparison[name].update({"rows_and_unique_keys_valid": row_valid, "plan_integral_and_bounds_valid": plan_integral, "daily_resource_limits_valid": bool((daily_plan.q_units <= 1600).all() and (daily_plan.budget <= 6000).all()), "finite_ordered_nominal90_output_valid": point_order_valid})

ind_coords = pd.DataFrame(residual_coordinate_rows)
prod_coords = pd.read_csv(EXEC / "science-v1/uncertainty/residual_coordinates_all.csv")
res_keys = ["service_date", "store_id", "item_id", "method_id", "source_origin"]
res_join = ind_coords.merge(prod_coords, on=res_keys, how="outer", suffixes=("_ind", "_prod"), indicator=True, validate="one_to_one")
res_eq = (res_join._merge == "both").all()
res_fields = {}
for col in ["revision", "raw_row", "demand_units", "coordinates"]:
    res_fields[col] = bool(np.array_equal(res_join[f"{col}_ind"].to_numpy(), res_join[f"{col}_prod"].to_numpy()))
for col in ["point", "error"]:
    res_fields[col] = bool(np.allclose(res_join[f"{col}_ind"].to_numpy(float), res_join[f"{col}_prod"].to_numpy(float), atol=1e-8, rtol=0))
for col in ["available_at", "full_day_ready_at"]:
    res_fields[col] = bool((pd.to_datetime(res_join[f"{col}_ind"]) == pd.to_datetime(res_join[f"{col}_prod"])).all())
expected_snapshot_hashes = {o[:10]: sha(EXEC / "science-v1/data" / f"train_{o[:10]}.csv") for o in origins}
res_join["source_date"] = res_join.source_origin.str[:10]
res_fields["source_snapshot_hash_bound"] = bool((res_join.train_snapshot_sha256 == res_join.source_date.map(expected_snapshot_hashes)).all())
residual_coordinate_comparison = {"independent_rows": len(ind_coords), "production_rows": len(prod_coords), "keyset_equal": bool(res_eq), "field_matches": res_fields, "all_exact_source_version_and_prediction_fields_match": bool(res_eq and all(res_fields.values()))}

prod_pools = pd.read_csv(EXEC / "science-v1/uncertainty/pool_membership_all_origins.csv")
ind_pools = pd.DataFrame(pool_checks)
pool_keys = ["calibration_origin", "method_id", "residual_day", "source_origin"]
pool_join = ind_pools.merge(prod_pools, on=pool_keys, how="outer", suffixes=("_ind", "_prod"), indicator=True, validate="one_to_one")
pool_ready_match = (pd.to_datetime(pool_join.ready_at_ind) == pd.to_datetime(pool_join.ready_at_prod)).all()
pool_comp = {"independent_rows": len(ind_pools), "production_rows": len(prod_pools), "keyset_equal": bool((pool_join._merge == "both").all()), "eligible_match": bool(np.array_equal(pool_join.eligible_ind.astype(bool), pool_join.eligible_prod.astype(bool))), "coordinates_match": bool(np.array_equal(pool_join.coordinates_ind.to_numpy(), pool_join.coordinates_prod.to_numpy())), "ready_timestamps_match": bool(pool_ready_match)}
pool_comp["all_fields_match"] = all([pool_comp["keyset_equal"], pool_comp["eligible_match"], pool_comp["coordinates_match"], pool_comp["ready_timestamps_match"]])

hist = pd.DataFrame(historical_rows)
hist_keys = pd.DataFrame(historical_key_rows)
hist_metrics = []
for (stage, method), g in hist.groupby(["stage", "method_id"]):
    dcount = g.service_date.nunique()
    z = hist_keys[(hist_keys.stage == stage) & (hist_keys.method_id == method)]
    hist_metrics.append({"stage": stage, "method_id": method, "date_count": dcount, "key_rows": len(z), "mae": float(z.abs_error.mean()), "rmse": float(np.sqrt(z.sq_error.mean())), "bias_key_mean": float(z.bias.mean()), "coverage": float(z.covered.mean()), "below": float(z.below.mean()), "above": float(z.above.mean()), "width": float(z.width.mean()), "interval_score": float(z.interval_score.mean()), "shortage_yuan_per_day": float(z.shortage.sum() / dcount), "waste_yuan_per_day": float(z.waste.sum() / dcount), "loss_yuan_per_day": float(z.loss.sum() / dcount), "q_units_per_day": float(z.q_units.sum() / dcount), "procurement_yuan_per_day": float(z.procurement.sum() / dcount)})

# Full-key metric tables for required historical groupings.
historical_detail = []
for group_cols, gtype in [(["holiday"], "holiday"), (["step_band"], "step_band"), (["holiday", "step_band"], "holiday_x_step_band"), (["store_id"], "store_id"), (["item_id"], "item_id"), (["horizon"], "horizon")]:
    for keys, g in hist_keys.groupby(["stage", "method_id"] + group_cols):
        prefix = keys[:2]
        vals = keys[2:] if len(group_cols) > 1 else (keys[2],)
        dcount = g.service_date.nunique()
        date_key_count = g[["origin", "service_date"]].drop_duplicates().shape[0]
        historical_detail.append({"group_type": gtype, "stage": prefix[0], "method_id": prefix[1], "group": list(vals), "date_count": dcount, "origin_date_count": date_key_count, "key_rows": len(g), "mae": float(g.abs_error.mean()), "rmse": float(np.sqrt(g.sq_error.mean())), "bias": float(g.bias.mean()), "coverage": float(g.covered.mean()), "below": float(g.below.mean()), "above": float(g.above.mean()), "width": float(g.width.mean()), "interval_score": float(g.interval_score.mean()), "shortage_yuan_per_day": float(g.shortage.sum() / date_key_count), "waste_yuan_per_day": float(g.waste.sum() / date_key_count), "loss_yuan_per_day": float(g.loss.sum() / date_key_count)})

result = {
    "schema": "r21-independent-scientific-reception/1",
    "scope": "independent historical and future-output reconstruction; private future actuals never read",
    "model": None, "tokens": None, "cost": None,
    "raw_audit": {"report_rows_original": int(len(tables["demand_reports"])), "exact_duplicate_rows": exact_dupes, "conflicting_same_revision_groups": conflicts, "mature_eval_label_keys": int(len(eval_labels)), "final_train_rows": int(len(final_train)), "final_train_unique_days": int(final_train.service_date.nunique()), "final_train_max_service_date": final_train.service_date.max(), "final_train_labels": int(len(final_train)), "asof_origin": ORIGIN_FINAL.isoformat(), "late_promotions_after_origin": int((tables["promotions"].announced_at > ORIGIN_FINAL).sum()), "late_weather_after_origin": int(((tables["weather"].kind == "forecast") & (tables["weather"].available_at > ORIGIN_FINAL)).sum())},
    "source_origin_training": train_audit,
    "source_snapshot_reconstruction_comparisons": snapshot_comparisons,
    "feature_lineage": fit_audit,
    "feature_reconstruction_comparisons": feature_comparisons,
    "selection_mean_daily_realized_loss": {k: float(v) for k, v in selection_summary.items()},
    "independently_selected_method": selected,
    "historical_metrics_by_stage": hist_metrics,
    "historical_group_metrics": historical_detail,
    "residual_coordinate_reconstruction_comparison": residual_coordinate_comparison,
    "residual_pool_membership_comparison": pool_comp,
    "residual_day_lineage_audit_rows": residual_audit,
    "final_route_output_comparison": prod_comparison,
    "future_route_files_used": ["science-v1/future/<method_id>/predictions.csv", "science-v1/future/<method_id>/replenishment.csv"],
    "future_actuals_read": False
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "independent-science-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
hist.to_csv(OUT / "independent-historical-day-metrics.csv", index=False, encoding="utf-8", float_format="%.10f")
hist_keys.to_csv(OUT / "independent-historical-key-metrics.csv", index=False, encoding="utf-8", float_format="%.10f")
pd.DataFrame(residual_audit).to_csv(OUT / "independent-residual-day-lineage.csv", index=False, encoding="utf-8")
pd.DataFrame(pool_checks).to_csv(OUT / "independent-pool-checks.csv", index=False, encoding="utf-8")
ind_coords.to_csv(OUT / "independent-residual-coordinates.csv", index=False, encoding="utf-8", float_format="%.10f")
print(json.dumps({"audit": str(OUT / "independent-science-audit.json"), "raw_audit": result["raw_audit"], "selection": result["selection_mean_daily_realized_loss"], "selected": selected, "historical": hist_metrics, "future_comparison": prod_comparison}, ensure_ascii=False, indent=2, default=str))
