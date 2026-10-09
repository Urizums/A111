import hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "runs/R21/inputs/raw"
EX = ROOT / "runs/R23/execution/v2"
KEY = ["service_date", "store_id", "item_id"]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def make_x(keys, tables, promo, origin, impute):
    x = keys.merge(tables["calendar"], on="service_date", validate="many_to_one")
    x = x.merge(tables["stores"], on="store_id", validate="many_to_one")
    x = x.merge(promo[KEY+["discount_fraction","announced_at"]], on=KEY, how="left", validate="one_to_one")
    x["promo_known"] = x.discount_fraction.notna()
    x["discount_fraction"] = x.discount_fraction.fillna(x.item_id.map(impute)).fillna(0.)
    x["time30"] = (pd.to_datetime(x.service_date)-pd.Timestamp("2026-05-01")).dt.days/30.
    assert len(x)==len(keys) and not x.duplicated(KEY).any()
    assert x.announced_at.dropna().le(origin).all()
    return x

def mat(x):
    s=x.store_id.str[1:].astype(int).to_numpy()-1
    k=x.item_id.str[1:].astype(int).to_numpy()-1
    a=np.zeros((len(x),169)); r=np.arange(len(x))
    a[r,s*8+k]=1.
    a[r,96+k*7+x.weekday_monday_zero.to_numpy(dtype=int)]=1.
    a[r,152+k]=x.time30.to_numpy()
    a[r,160+k]=x.discount_fraction.to_numpy()
    a[:,168]=x.holiday.to_numpy()*0.3
    return a

def main():
    cfgp=EX/"consumer-slice-config.json"; cfg=json.loads(cfgp.read_text(encoding="utf-8"))
    origin=pd.Timestamp(cfg["origin"]); cutoff=pd.Timestamp(cfg["evaluation_label_cutoff"]); target=cfg["target_service_date"]
    assert origin.tz is not None and cutoff.tz is not None and cfg["timezone"]=="Asia/Shanghai"
    files=["demand_reports","stores","items","calendar","promotions","weather"]
    t={n:pd.read_csv(RAW/f"{n}.csv") for n in files}
    for n,c in [("demand_reports","available_at"),("promotions","announced_at")]:
        t[n][c]=pd.to_datetime(t[n][c],format="%Y-%m-%dT%H:%M:%S",errors="raise").dt.tz_localize("Asia/Shanghai")
    rawhash={f"{n}.csv":sha(RAW/f"{n}.csv") for n in files}
    rawhash["decision.json"]=sha(RAW/"decision.json")
    lock=json.loads((ROOT/"runs/R21/input-lock.json").read_text(encoding="utf-8"))
    li={Path(f["path"]).name:f for f in lock["files"] if f["path"].startswith(("runs/R21/inputs/raw/","runs/R21/inputs/reference/"))}
    assert all(n in li and li[n]["sha256"]==h and li[n]["size_bytes"]==(RAW/n).stat().st_size for n,h in rawhash.items())
    d=t["demand_reports"]
    train0=d[(d.service_date<origin.strftime("%Y-%m-%d"))&(d.available_at<=origin)]
    train=train0.sort_values(KEY+["revision","available_at"]).drop_duplicates(KEY,keep="last").copy()
    assert len(train)>0 and not train.duplicated(KEY).any()
    assert train.available_at.le(origin).all() and train.service_date.lt(origin.strftime("%Y-%m-%d")).all()
    later=d[(d.service_date<target)&(d.available_at>origin)]
    laterkeys=set(map(tuple,later[KEY].drop_duplicates().to_numpy()))
    keys_in_train=train[KEY].apply(tuple,axis=1).isin(laterkeys)
    boundary=train[keys_in_train].sort_values(KEY)
    assert len(boundary)>0
    first=boundary.iloc[0]; k0=tuple(first[k] for k in KEY)
    nextrev=later[later[KEY].apply(tuple,axis=1)==k0].sort_values(["revision","available_at"]).iloc[-1]
    assert first.available_at<=origin<nextrev.available_at and int(first.revision)<int(nextrev.revision)
    p=t["promotions"]
    promo=p[p.announced_at<=origin].sort_values("announced_at").drop_duplicates(KEY,keep="last")
    start=(origin-pd.Timedelta(days=56)).strftime("%Y-%m-%d")
    recent=train[train.service_date>=start]
    rp=recent[KEY].merge(promo[KEY+["discount_fraction"]],on=KEY,how="inner",validate="one_to_one")
    impute=rp.groupby("item_id").discount_fraction.mean()
    tx=make_x(train[KEY],t,promo,origin,impute)
    stores=sorted(t["stores"].store_id); items=sorted(t["items"].item_id)
    targetkeys=pd.DataFrame([(target,s,i) for s in stores for i in items],columns=KEY)
    assert len(targetkeys)==96 and not targetkeys.duplicated(KEY).any()
    fx=make_x(targetkeys,t,promo,origin,impute)
    spec=cfg["methods"]["shared_ridge10_consumer"]
    assert spec["alpha"]==10 and spec["fit_intercept"] is False
    model=Ridge(alpha=10,fit_intercept=False,solver="cholesky").fit(mat(tx),train.demand_units.to_numpy(float))
    ridge=np.maximum(model.predict(mat(fx)),0.)
    wspec=cfg["methods"]["weekly_median56_consumer"]
    assert "56 calendar days" in wspec["window"] and "median demand" in wspec["statistic"] and wspec["fallback_order"]==["store-item median in same window","item-weekday median across stores in same window"]
    win=train[(train.service_date>=start)&(train.service_date<target)].copy()
    wd=win.assign(weekday=pd.to_datetime(win.service_date).dt.weekday)
    g=wd.groupby(["store_id","item_id","weekday"]).demand_units.median()
    pair=win.groupby(["store_id","item_id"]).demand_units.median()
    iw=wd.groupby(["item_id","weekday"]).demand_units.median()
    weekday=int(fx.weekday_monday_zero.iloc[0]); weekly=[]; fb={"store_item":0,"item_weekday":0}
    for row in targetkeys.itertuples(index=False):
        key=(row.store_id,row.item_id,weekday)
        if key in g.index: value=g.loc[key]
        elif (row.store_id,row.item_id) in pair.index: value=pair.loc[(row.store_id,row.item_id)];fb["store_item"]+=1
        elif (row.item_id,weekday) in iw.index: value=iw.loc[(row.item_id,weekday)];fb["item_weekday"]+=1
        else: raise AssertionError("no weekly fallback")
        weekly.append(float(value))
    labels=d[(d.service_date==target)&(d.available_at<=cutoff)].sort_values(KEY+["revision","available_at"]).drop_duplicates(KEY,keep="last")
    actual=targetkeys.merge(labels[KEY+["demand_units","revision","available_at"]],on=KEY,how="left",validate="one_to_one")
    assert len(actual)==96 and actual.demand_units.notna().all()
    assert actual.available_at.gt(origin).all() and actual.available_at.le(cutoff).all()
    out=pd.read_csv(EX/"consumer-point-slice.csv")
    expectedcols=KEY+["method_id","demand_point_units","actual_demand_units","actual_revision","actual_available_at"]
    assert list(out.columns)==expectedcols and len(out)==192 and not out.duplicated(KEY+["method_id"]).any()
    metrics={}; compare={}
    for name,pred in [("shared_ridge10_consumer",ridge),("weekly_median56_consumer",np.array(weekly))]:
        z=out[out.method_id==name].sort_values(KEY).reset_index(drop=True)
        grid=targetkeys.sort_values(KEY).reset_index(drop=True)
        assert len(z)==96 and z[KEY].equals(grid[KEY])
        assert np.allclose(z.demand_point_units.to_numpy(),pred,atol=5.1e-10,rtol=0)
        truth=actual.sort_values(KEY).reset_index(drop=True)
        assert np.array_equal(z.actual_demand_units.to_numpy(),truth.demand_units.to_numpy())
        assert np.array_equal(z.actual_revision.to_numpy(),truth.revision.to_numpy())
        assert pd.to_datetime(z.actual_available_at,utc=True).equals(pd.to_datetime(truth.available_at,utc=True))
        err=pred-truth.demand_units.to_numpy(float)
        metrics[name]={"mae_units_per_pair":float(np.abs(err).mean()),"rmse_units_per_pair":float(np.sqrt(np.mean(err**2))),"mean_signed_error_units_per_pair":float(err.mean())}
        compare[name]={"rows":len(z),"max_abs_output_difference":float(np.max(np.abs(z.demand_point_units.to_numpy()-pred))),"recomputed_metrics":metrics[name]}
    report=json.loads((EX/"consumer-point-slice-report.json").read_text(encoding="utf-8"))
    reportchecks={"train_rows":len(train)==report["input_rows"]["training_snapshot"],"window_rows":len(win)==report["input_rows"]["training_window_56d"],"late_rows":len(later)==report["input_rows"]["later_published_training_rows_excluded"],"boundary_keys":len(boundary)==report["input_rows"]["visible_training_keys_with_later_after_origin_rows"],"target_labels":int(actual.available_at.gt(origin).sum())==report["input_rows"]["target_labels_post_origin"],"known_promos":int(fx.promo_known.sum())==report["input_rows"]["target_promotion_known_at_origin"],"fallbacks":fb==report["weekly_fallback_counts"]}
    for method,vals in metrics.items():
        for k,v in vals.items(): reportchecks[method+"."+k]=math.isclose(v,float(report["metrics"][method][k]),rel_tol=0,abs_tol=1e-11)
    assert all(reportchecks.values()),reportchecks
    locks=[]
    for lockname,paths in [("runs/R23/design-lock.json",["runs/R23/design/WORKFLOW.md","runs/R23/design/probe.py"]),("runs/R23/execution-lock.json",["runs/R23/execution/v2/consumer_slice.py","runs/R23/execution/v2/consumer-slice-config.json","runs/R23/execution/v2/consumer-slice-freeze.json","runs/R23/execution/v2/consumer-point-slice.csv","runs/R23/execution/v2/consumer-point-slice-report.json"])]:
        ld=json.loads((ROOT/lockname).read_text(encoding="utf-8"))
        for name in paths:
            x=next(i for i in ld["files"] if i["path"]==name); pp=ROOT/name
            locks.append({"path":name,"matches_identity":pp.stat().st_size==x["size_bytes"] and sha(pp)==x["sha256"]})
    assert all(x["matches_identity"] for x in locks),locks
    result={"schema":"r23-independent-recomputation/1","state":"source recomputation complete","slice_id":cfg["slice_id"],"origin":origin.isoformat(),"target":target,"cutoff":cutoff.isoformat(),"raw_identity_matches_lock":True,"locked_artifact_identity":locks,"training_rows":len(train),"56_day_rows":len(win),"late_rows_excluded":len(later),"training_keys_with_later_reports":len(boundary),"activated_boundary_example":{"key":dict(zip(KEY,[first[k] for k in KEY])),"visible_revision":int(first.revision),"visible_time":first.available_at.isoformat(),"later_revision":int(nextrev.revision),"later_time":nextrev.available_at.isoformat()},"target_labels":{"keys":len(actual),"post_origin":int(actual.available_at.gt(origin).sum()),"by_cutoff":int(actual.available_at.le(cutoff).sum()),"revision_counts":{str(k):int(v) for k,v in actual.revision.value_counts().sort_index().items()}},"target_promotions_known":int(fx.promo_known.sum()),"weekly_fallbacks":fb,"output_comparison":compare,"report_crosschecks":reportchecks,"scope_limit":"One historical date and point forecasts only; no interval calibration, replenishment optimization, full 42-day output, or future reliability claim.","telemetry":{"actual_model":None,"tokens":None,"cost":None},"raw_source_sha256":rawhash}
    (HERE/"independent-recomputation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
