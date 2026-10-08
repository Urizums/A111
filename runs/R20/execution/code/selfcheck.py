"""Author receiving checks, separately reconstruct key raw quantities and compare clean run."""
from pathlib import Path
import json, hashlib, itertools, argparse
from decimal import Decimal
import numpy as np
import pandas as pd
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent; EXEC=HERE.parent; REPO=HERE.parents[3]
KEY=['service_date','store_id','item_id']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def timestamp(x): return pd.Timestamp(x).tz_localize('Asia/Shanghai') if pd.Timestamp(x).tzinfo is None else pd.Timestamp(x).tz_convert('Asia/Shanghai')
def require_asof(df,col,origin):
    assert pd.to_datetime(df[col]).dropna().le(timestamp(origin)).all(),'future input rejected'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--compare'); a=ap.parse_args(); out=Path(a.out); raw=REPO/'runs/R20/inputs/raw'
    config=json.loads((EXEC/'config/experiment.json').read_text()); decision=json.loads((raw/'decision.json').read_text()); origin=decision['origin']
    reports=pd.read_csv(raw/'demand_reports.csv').drop_duplicates(); reports.available_at=pd.to_datetime(reports.available_at).dt.tz_localize('Asia/Shanghai')
    available=reports[reports.available_at<=timestamp(origin)].sort_values(KEY+['revision']).drop_duplicates(KEY,keep='last').sort_values(KEY)
    snap=pd.read_csv(out/'data/final_snapshot.csv')
    assert available[KEY].reset_index(drop=True).equals(snap[KEY])
    np.testing.assert_array_equal(available.demand_units.to_numpy(),snap.demand_units)
    pred=pd.read_csv(out/'results/future_predictions.csv'); q=pd.read_csv(out/'results/future_replenishment.csv')
    items=pd.read_csv(raw/'items.csv'); stores=pd.read_csv(raw/'stores.csv'); dates=pd.date_range(decision['future_begin'],decision['future_end']).strftime('%Y-%m-%d').tolist()
    expected=pd.DataFrame(itertools.product(dates,sorted(stores.store_id),sorted(items.item_id)),columns=KEY)
    assert len(pred)==1344 and len(q)==1344 and not pred.duplicated(KEY).any() and not q.duplicated(KEY).any()
    assert expected.equals(pred[KEY]) and expected.equals(q[KEY]); assert q.q_units.dtype.kind in 'iu' and q.q_units.dtype.kind!='b'
    assert np.isfinite(pred.drop(columns=KEY)).all().all() and (pred.demand_point_units>=0).all()
    assert (pred.lower90_units>=0).all() and (pred.lower90_units<=pred.upper90_units).all() and (pred.interval_level==.9).all()
    jq=q.merge(items,on='item_id',validate='many_to_one'); assert (jq.q_units>=0).all() and (jq.q_units<=jq.daily_max_units).all()
    day=[]
    for d,g in jq.groupby('service_date'):
        count=int(g.q_units.sum()); cost=sum(Decimal(str(r.procurement_yuan))*int(r.q_units) for r in g.itertuples(index=False))
        assert count<=decision['capacity_units_per_day'] and cost<=Decimal(str(decision['procurement_budget_yuan_per_day']))
        day.append({'date':d,'q':count,'cost_decimal':str(cost)})
    scenarios=pd.read_csv(out/'uncertainty/future_scenarios.csv'); weights=scenarios.groupby('scenario_id').weight.first(); assert (weights>=0).all() and abs(weights.sum()-1)<1e-7
    stored_weight_sum=float(weights.sum())
    # CSV stores ten decimals; the declared equal-weight empirical measure is normalized.
    # This reconstructs that measure without weakening the target-value tolerance.
    weights=weights/weights.sum()
    assert np.isfinite(scenarios[['weight','demand_units']]).all().all() and (scenarios.demand_units>=0).all()
    for _,g in scenarios.groupby('scenario_id'): assert expected.equals(g[KEY].reset_index(drop=True))
    js=scenarios.merge(jq,on=KEY,validate='many_to_one'); js['sh']=js.shortage_yuan*np.maximum(js.demand_units-js.q_units,0); js['wa']=js.waste_yuan*np.maximum(js.q_units-js.demand_units,0)
    ds=pd.read_csv(out/'results/decision_summary.csv'); objective=[]
    for d,g in js.groupby('service_date'):
        sl=g.groupby('scenario_id')[['sh','wa']].sum(); value=float((sl.sum(axis=1)*weights).sum()); objective.append(value)
    np.testing.assert_allclose(objective,ds.scenario_mean_loss_yuan,atol=1e-6,rtol=0)
    solver=pd.read_csv(out/'results/solver_evidence_future.csv'); assert (solver.status==0).all() and (solver.gap<=1e-9).all(); np.testing.assert_allclose(solver.objective,ds.scenario_mean_loss_yuan,atol=1e-7,rtol=0)
    late=reports[reports.service_date=='2026-09-30']; rejection=[]
    try: require_asof(late,'available_at',origin)
    except AssertionError: rejection.append('actual 96 late September30 rows')
    else: raise AssertionError('late labels accepted')
    hist_origin=config['holdout_origin']; hs=pd.read_csv(out/'data/snapshot_2026-09-16.csv'); require_asof(hs,'available_at',hist_origin)
    hr=reports[(reports.service_date<=hs.service_date.max())&(reports.available_at>timestamp(hist_origin))]
    assert len(hr)>0
    try: require_asof(hr,'available_at',hist_origin)
    except AssertionError: rejection.append('actual later revisions at historical origin')
    else: raise AssertionError('late revisions accepted')
    for file in sorted((out/'data').glob('calibration_lineage_*.csv')):
        d=pd.read_csv(file); daystr=file.name[len('calibration_lineage_'):len('calibration_lineage_')+10]; require_asof(d,'ready',daystr+'T18:00:00')
    require_asof(pd.read_csv(out/'uncertainty/residual_lineage.csv'),'ready',origin)
    feature_files=sorted((out/'data').glob('feature_lineage_*.csv'))+[out/'data/final_feature_lineage.csv']
    for file in feature_files:
        z=pd.read_csv(file); o=z.origin.iloc[0]; require_asof(z,'announced_at',o); require_asof(z,'weather_available_at',o)
        assert 'settlement_yuan' not in z
    historical=pd.read_csv(out/'results/historical_predictions_plans.csv'); truthcut=reports[reports.available_at<=timestamp(config['evaluation_label_cutoff'])].sort_values(KEY+['revision']).drop_duplicates(KEY,keep='last')
    hh=historical.merge(truthcut[KEY+['demand_units']],on=KEY,validate='many_to_one').merge(items,on='item_id',validate='many_to_one')
    np.testing.assert_array_equal(hh.actual,hh.demand_units)
    recalculated=[]
    for (stage,ori,model,policy),g in hh.groupby(['stage','origin','model','policy']):
        sh=g.shortage_yuan_y*np.maximum(g.actual-g.q_units,0); wa=g.waste_yuan_y*np.maximum(g.q_units-g.actual,0)
        np.testing.assert_allclose(sh,g.shortage_yuan_x,atol=1e-7,rtol=0); np.testing.assert_allclose(wa,g.waste_yuan_x,atol=1e-7,rtol=0)
        row={'stage':stage,'origin':ori,'model':model,'policy':policy,'mae':float(abs(g.actual-g.point).mean()),'loss_yuan_per_day':float((sh+wa).sum()/14),'coverage90':float(((g.actual>=g.lower90)&(g.actual<=g.upper90)).mean())}; recalculated.append(row)
    metric=pd.read_csv(out/'results/backtest_metrics.csv'); mm=pd.DataFrame(recalculated).merge(metric,on=['stage','origin','model','policy'],suffixes=('_new','_old'),validate='one_to_one')
    for col in ['mae','loss_yuan_per_day','coverage90']: np.testing.assert_allclose(mm[col+'_new'],mm[col+'_old'],atol=1e-7,rtol=0)
    selection=metric[(metric.stage=='selection')&(metric.policy=='stochastic')].groupby('model').loss_yuan_per_day.mean(); chosen=json.loads((out/'results/selection.json').read_text())['selected_model']; assert selection.idxmin()==chosen
    comparisons=[]
    if a.compare:
        old=Path(a.compare)
        for p in sorted(out.rglob('*.csv')):
            rel=p.relative_to(out); other=old/rel
            if not other.exists(): continue
            x=pd.read_csv(p); y=pd.read_csv(other); assert list(x.columns)==list(y.columns) and x.shape==y.shape
            ignored=['seconds'] if 'seconds' in x else []
            for col in x:
                if col in ignored: continue
                if x[col].dtype.kind in 'iuf' and y[col].dtype.kind in 'iuf': np.testing.assert_allclose(x[col],y[col],atol=1e-7,rtol=0,equal_nan=True)
                else: assert x[col].fillna('').equals(y[col].fillna('')),(str(rel),col)
            comparisons.append({'path':str(rel),'rows':len(x),'ignored_columns':ignored})
    reader=PdfReader(out/'paper/paper.pdf'); text='\n'.join(p.extract_text() for p in reader.pages); md=(out/'paper/paper.md').read_text(encoding='utf-8')
    assert len(reader.pages)>=1 and all(p.extract_text().strip() for p in reader.pages)
    for x in ['78851','22400','14592','1344','原创','预算','未来真实需求']:
        assert x in md.replace(' ','') and x in text.replace(' ','').replace('\n',''),x
    checks={'schema':'freshfood-author-selfcheck/1','scope':'author recomputation; not independent acceptance','pass':True,'raw_snapshot_rows':len(snap),'future_prediction_rows':len(pred),'future_plan_rows':len(q),'daily_exact_money_checks':day,'actual_availability_rejections':rejection,'scenario_objective_recomputed_all_days':True,'stored_scenario_weight_sum':stored_weight_sum,'weight_reconstruction':'normalize stored 10-decimal equal weights before expectation; raw sum must pass frozen 1e-7 tolerance','historical_metric_groups_recomputed':len(mm),'feature_lineage_files_checked':len(feature_files),'clean_rerun_csv_comparison':comparisons,'pdf_pages':len(reader.pages),'pdf_text_key_values_checked':True,'visual_review':'separately recorded after latest render','unknowns':{'model':None,'tokens':None,'cost':None,'future_true_demand':None},'limits':['future performance/coverage not observable','full independent receiving review pending','stress multipliers assumed; long weather migration unverified','not a universal proof of every software branch']}
    (EXEC/'evidence/selfcheck.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({k:v for k,v in checks.items() if k not in ['daily_exact_money_checks','clean_rerun_csv_comparison']},ensure_ascii=False,indent=2)); print('clean CSV comparisons:',len(comparisons))

if __name__=='__main__': main()
