import json,hashlib,math
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[4]; RAW=ROOT/'runs/R20/inputs/raw'; DEL=ROOT/'runs/R20/execution/delivery'; OWN=ROOT/'runs/R20/review/initial/rerun'
with (RAW/'decision.json').open(encoding='utf-8-sig') as f: decision=json.load(f)
with (ROOT/'runs/R20/execution/config/experiment.json').open(encoding='utf-8') as f: config=json.load(f)
tz=ZoneInfo(decision['timezone'])
def dt(s):
 d=pd.Timestamp(s); return d.tz_localize(tz) if d.tzinfo is None else d.tz_convert(tz)
def local_ts(s):
 d=pd.Timestamp(s); return d.tz_localize(tz) if d.tzinfo is None else d.tz_convert(tz)
def load(name):return pd.read_csv(RAW/name,encoding='utf-8-sig')
demand=load('demand_reports.csv').drop_duplicates().copy(); demand['available_at']=pd.to_datetime(demand.available_at).dt.tz_localize(tz); demand['revision']=pd.to_numeric(demand.revision,errors='raise').astype(int); demand['demand_units']=pd.to_numeric(demand.demand_units,errors='raise')
label_cut=dt(config['evaluation_label_cutoff']); visible=demand[demand.available_at<=label_cut].copy()
# Label choice from raw at the frozen evaluation-label cutoff, keeping late target labels strictly separate from forecast features.
key=['service_date','store_id','item_id']; gr=visible.groupby(key,sort=False)
maxrev=gr.revision.transform('max'); tops=visible[visible.revision==maxrev].copy()
conflict=tops.groupby(key).demand_units.nunique(); conflict_keys=int((conflict>1).sum())
labels=tops.sort_values('available_at').drop_duplicates(key,keep='last')[key+['revision','available_at','demand_units']]
y=labels.set_index(key).demand_units.to_dict(); yinfo=labels.set_index(key)
items=load('items.csv').set_index('item_id'); a=items.shortage_yuan.to_dict(); b=items.waste_yuan.to_dict(); c=items.procurement_yuan.to_dict(); maxq=items.daily_max_units.astype(int).to_dict()
hist=pd.read_csv(DEL/'results/historical_predictions_plans.csv')
reported=pd.read_csv(DEL/'results/backtest_metrics.csv')
metrics=[]; truth_mismatch=0; missing_truth=0
for (stage,origin,model,policy),g in hist.groupby(['stage','origin','model','policy'],sort=False):
    actual=[]
    for r in g.itertuples():
        k=(r.service_date,r.store_id,r.item_id)
        if k not in y: missing_truth+=1; actual.append(np.nan)
        else:
            actual.append(float(y[k]))
            if not np.isclose(float(r.actual),float(y[k]),atol=0,rtol=0):truth_mismatch+=1
    actual=np.asarray(actual); point=g.point.to_numpy(float); q=g.q_units.to_numpy(float)
    sh=np.zeros(len(g)); wa=np.zeros(len(g)); pc=np.zeros(len(g))
    for j,r in enumerate(g.itertuples()):
        it=r.item_id; sh[j]=a[it]*max(actual[j]-q[j],0); wa[j]=b[it]*max(q[j]-actual[j],0); pc[j]=c[it]*q[j]
    day_loss=pd.DataFrame({'date':g.service_date.to_numpy(),'loss':sh+wa,'units_err':point-actual}).groupby('date').agg(loss=('loss','sum'),bias=('units_err','sum'))
    m={'stage':stage,'origin':origin,'model':model,'policy':policy,'rows':len(g),'days':int(g.service_date.nunique()),'mae':float(np.mean(np.abs(point-actual))),'rmse':float(np.sqrt(np.mean((point-actual)**2))),'total_bias_units_per_day':float(day_loss.bias.mean()),'loss_yuan_per_day':float(day_loss.loss.mean()),'shortage_yuan_per_day':float(sh.sum()/g.service_date.nunique()),'waste_yuan_per_day':float(wa.sum()/g.service_date.nunique()),'coverage90':float(np.mean((actual>=g.lower90.to_numpy(float))&(actual<=g.upper90.to_numpy(float)))),'interval_width_units':float(np.mean(g.upper90.to_numpy(float)-g.lower90.to_numpy(float))),'q_units_per_day':float(g.groupby('service_date').q_units.sum().mean()),'procurement_yuan_per_day':float(pd.Series(pc).groupby(g.service_date.to_numpy()).sum().mean())}
    metrics.append(m)
# Compare independently recomputed outcomes to machine-reported metrics.
metric_fields=['mae','rmse','total_bias_units_per_day','loss_yuan_per_day','shortage_yuan_per_day','waste_yuan_per_day','coverage90','interval_width_units','q_units_per_day','procurement_yuan_per_day']
recomputed=pd.DataFrame(metrics); compare=[]
for r in reported.itertuples(index=False):
    m=recomputed[(recomputed.stage==r.stage)&(recomputed.origin==r.origin)&(recomputed.model==r.model)&(recomputed.policy==r.policy)]
    if len(m)!=1: compare.append({'stage':r.stage,'origin':r.origin,'model':r.model,'policy':r.policy,'match':False,'reason':'group missing or duplicated'}); continue
    diffs={f:float(m.iloc[0][f])-float(getattr(r,f)) for f in metric_fields}
    compare.append({'stage':r.stage,'origin':r.origin,'model':r.model,'policy':r.policy,'max_abs_diff':max(abs(v) for v in diffs.values()),'matches_at_1e-6':max(abs(v) for v in diffs.values())<=1e-6,'diffs':diffs})
order=[x['name'] for x in config['candidates']]
sel=recomputed[(recomputed.stage=='selection')&(recomputed.policy=='stochastic')].groupby('model').loss_yuan_per_day.mean().to_dict()
ranked=sorted(order,key=lambda m:(sel[m],order.index(m))); chosen=ranked[0]
# Current final tables and origin snapshot, independent source-derived checks.
pred=pd.read_csv(DEL/'results/future_predictions.csv'); plan=pd.read_csv(DEL/'results/future_replenishment.csv')
future_dates=pd.date_range(decision['future_begin'],decision['future_end']).strftime('%Y-%m-%d').tolist()
stores=set(load('stores.csv').store_id); itemids=set(items.index)
expected={(d,s,k) for d in future_dates for s in stores for k in itemids}
def check_grid(g):
 ks=list(zip(g.service_date,g.store_id,g.item_id)); return {'rows':len(g),'unique':len(set(ks)),'matches_all_1344_keys':len(ks)==1344 and len(set(ks))==1344 and set(ks)==expected}
future_q=plan.q_units.to_numpy(float); q_integral=bool(np.all(np.isfinite(future_q)) and np.all(future_q>=0) and np.all(future_q==np.floor(future_q)))
byday=[]
for d,g in plan.groupby('service_date'):
 q=g.set_index('item_id').join(items[['procurement_yuan','daily_max_units']],on='item_id')
 cost=float((q.q_units*q.procurement_yuan).sum()); units=int(q.q_units.sum()); over=int((q.q_units>q.daily_max_units).sum())
 byday.append({'date':d,'units':units,'cost':cost,'capacity_slack':1600-units,'budget_slack':6000-cost,'per_item_violations':over,'valid':units<=1600 and cost<=6000 and over==0})
# Verify lineages by raw time stamps, not report claims.
lineage=[]
for p in sorted((DEL/'data').glob('feature_lineage_*.csv')):
 g=pd.read_csv(p)
 if 'origin' not in g: continue
 origins=g.origin.dropna().unique(); o=dt(origins[0]) if len(origins)==1 else None
 promo_col='announced_at' if 'announced_at' in g else ('promo_announced_at' if 'promo_announced_at' in g else None)
 weather_col='weather_available_at' if 'weather_available_at' in g else None
 p_ok=True; w_ok=True
 if promo_col:
  v=g[promo_col].dropna(); p_ok=all(local_ts(x)<=o for x in v) if o else False
 if weather_col:
  v=g[weather_col].dropna(); w_ok=all(local_ts(x)<=o for x in v) if o else False
 lineage.append({'file':p.name,'rows':len(g),'origin':origins.tolist(),'promo_available_time_ok':p_ok,'weather_available_time_ok':w_ok,'settlement_column_present':'settlement_yuan' in g.columns,'columns':list(g.columns)})
# Final origin snapshot from raw independently.
orig=dt(decision['origin']); final_visible=demand[demand.available_at<=orig].copy(); final_visible=final_visible[final_visible.service_date<orig.strftime('%Y-%m-%d')]
final_visible=final_visible.sort_values(key+['revision']).drop_duplicates(key,keep='last')
late_origin=demand[(demand.service_date=='2026-09-30')&(demand.available_at>orig)]
# Equality of the high-value deterministic deliverables against independent clean rerun.
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
parity=[]
for rel in ['results/future_predictions.csv','results/future_replenishment.csv','results/backtest_metrics.csv','results/historical_predictions_plans.csv','results/decision_summary.csv','results/sensitivity.csv','paper/paper.md','paper/paper.pdf']:
 p=DEL/rel; q=OWN/rel; parity.append({'path':rel,'delivery_sha256':sha(p),'rerun_sha256':sha(q) if q.exists() else None,'same_bytes':q.exists() and sha(p)==sha(q)})
# package figure count and each file hashes summarized later; do not open expected values from manifests.
figs=sorted(p.name for p in (DEL/'figures').glob('*.png'))
result={'raw_label_rebuild':{'label_cutoff':label_cut.isoformat(),'label_keys':len(labels),'highest_revision_content_conflicts':conflict_keys,'missing_hist_truth_rows':missing_truth,'historical_actual_mismatches_vs_raw':truth_mismatch},'independent_metric_recomputation':{'groups':len(metrics),'reported_groups':len(reported),'all_groups_match':len(compare)==len(reported) and all(x.get('matches_at_1e-6',False) for x in compare),'maximum_metric_difference':max([x.get('max_abs_diff',0) for x in compare] or [0]),'selection_losses_by_model':sel,'selection_rank':ranked,'independently_selected_model':chosen,'metric_comparisons':compare},'final_tables':{'predictions':check_grid(pred),'replenishment':check_grid(plan),'forecast_finite_nonnegative':bool(np.isfinite(pred.demand_point_units).all() and (pred.demand_point_units>=0).all()),'interval_valid':bool(np.isfinite(pred[['lower90_units','upper90_units','interval_level']].to_numpy(float)).all() and (pred.lower90_units>=0).all() and (pred.lower90_units<=pred.upper90_units).all()),'q_integral_nonnegative':q_integral,'daily_source_cost_capacity':byday,'all_14_days_valid':len(byday)==14 and all(x['valid'] for x in byday),'total_q':int(plan.q_units.sum()),'total_procurement':float((plan.merge(items[['procurement_yuan']],left_on='item_id',right_index=True).q_units*plan.merge(items[['procurement_yuan']],left_on='item_id',right_index=True).procurement_yuan).sum())},'snapshot_time_check':{'origin':orig.isoformat(),'final_snapshot_rows':len(final_visible),'max_service_date':final_visible.service_date.max(),'late_2026_09_30_rows':len(late_origin),'all_96_late':len(late_origin)==96 and late_origin.available_at.gt(orig).all()},'lineage_checks':lineage,'delivery_rerun_byte_parity':parity,'delivery_figure_count':len(figs),'delivery_figures':figs,'future_truth_opened':False}
print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
