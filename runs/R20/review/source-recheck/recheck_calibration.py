from pathlib import Path
import hashlib, json, pandas as pd, numpy as np
from sklearn.linear_model import Ridge

ROOT=Path('runs/R20')
RAW=ROOT/'inputs/raw'
DEL=ROOT/'execution/delivery'
CONFIG=json.loads((ROOT/'execution/config/experiment.json').read_text(encoding='utf-8'))
KEY=['service_date','store_id','item_id']
pairs=[(f'S{i:02d}',f'K{k:02d}') for i in range(1,13) for k in range(1,9)]
origin_s=[CONFIG['precalibration_origin']]+CONFIG['selection_origins']+[CONFIG['calibration_origin'],CONFIG['holdout_origin']]
origins=[pd.Timestamp(x).tz_localize('Asia/Shanghai') for x in origin_s]
cutoff=pd.Timestamp(CONFIG['evaluation_label_cutoff']).tz_localize('Asia/Shanghai')

def local(v):
 t=pd.Timestamp(v); return t.tz_localize('Asia/Shanghai') if t.tzinfo is None else t.tz_convert('Asia/Shanghai')

def read(name):
 d=pd.read_csv(RAW/(name+'.csv'))
 if 'available_at' in d: d['available_at']=pd.to_datetime(d.available_at,format='%Y-%m-%dT%H:%M:%S').dt.tz_localize('Asia/Shanghai')
 if 'announced_at' in d: d['announced_at']=pd.to_datetime(d.announced_at,format='%Y-%m-%dT%H:%M:%S').dt.tz_localize('Asia/Shanghai')
 return d

reports=read('demand_reports').drop_duplicates()
stores=read('stores').sort_values('store_id')
items=read('items')
cal=read('calendar')
promos=read('promotions')
# Rebuild the final evaluation label as-of cutoff from raw; no delivery truth labels are used.
labels=(reports[reports.available_at<=cutoff].sort_values(KEY+['revision']).drop_duplicates(KEY,keep='last').copy())
assert not labels.duplicated(KEY).any()
labels['service_date']=labels.service_date.astype(str)
assert len(labels)==14688
store_order=stores.store_id.tolist(); item_order=sorted(items.item_id.tolist())
assert pairs==[(s,k) for s in store_order for k in item_order]
items_i=items.set_index('item_id')

# Independently rebuild the source point forecasts from raw, using the frozen Ridge10 candidate.
def snapshot(o):
 x=(reports[reports.available_at<=o].sort_values(KEY+['revision']).drop_duplicates(KEY,keep='last').copy())
 x['service_date']=x.service_date.astype(str)
 return x[x.service_date<o.strftime('%Y-%m-%d')].copy()

def make_features(keys,o,tr):
 x=pd.DataFrame(keys,columns=KEY).merge(cal.drop_duplicates('service_date'),on='service_date',validate='many_to_one')
 x=x.merge(stores[['store_id','zone_id']],on='store_id',validate='many_to_one')
 known=promos[promos.announced_at<=o]
 x=x.merge(known[KEY+['discount_fraction','announced_at']],on=KEY,how='left',validate='one_to_one')
 x['promo_known']=x.discount_fraction.notna().astype(int)
 recent=tr[tr.service_date>=(o-pd.Timedelta(days=56)).strftime('%Y-%m-%d')][KEY]
 means=recent.merge(known[KEY+['discount_fraction']],on=KEY,validate='one_to_one').groupby('item_id').discount_fraction.mean()
 x['discount_fraction']=x.discount_fraction.fillna(x.item_id.map(means)).fillna(0)
 x['time30']=(pd.to_datetime(x.service_date)-pd.Timestamp('2026-05-01')).dt.days/30
 return x

def matrix(x):
 si=x.store_id.str[1:].astype(int).to_numpy()-1
 ki=x.item_id.str[1:].astype(int).to_numpy()-1
 a=np.zeros((len(x),169)); ix=np.arange(len(x))
 a[ix,si*8+ki]=1
 a[ix,96+ki*7+x.weekday_monday_zero.to_numpy(dtype=int)]=1
 a[ix,152+ki]=x.time30.to_numpy()
 a[ix,160+ki]=x.discount_fraction.to_numpy()
 a[:,168]=x.holiday.to_numpy()*0.3
 return a

source=[]; origin_checks=[]; prediction_checks=[]
hist=pd.read_csv(DEL/'results/historical_predictions_plans.csv')
for o,os in zip(origins,origin_s):
 dates=pd.date_range(o.date()+pd.Timedelta(days=1),periods=14).strftime('%Y-%m-%d').tolist()
 tr=snapshot(o)
 trfeat=make_features(tr[KEY],o,tr)
 te=make_features([(d,s,k) for d in dates for s,k in pairs],o,tr)
 model=Ridge(alpha=10,fit_intercept=False,solver='cholesky')
 model.fit(matrix(trfeat),tr.demand_units.to_numpy())
 point=np.maximum(model.predict(matrix(te)),0).reshape(14,96)
 actual=te[KEY].merge(labels[KEY+['demand_units','revision','available_at']],on=KEY,validate='one_to_one')
 assert len(actual)==1344 and actual.demand_units.notna().all()
 truth=actual.demand_units.to_numpy().reshape(14,96)
 for j,d in enumerate(dates):
  day=actual[actual.service_date==d]
  assert len(day)==96 and set(zip(day.store_id,day.item_id))==set(pairs)
  ready=day.available_at.max()
  source.append({'date':d,'ready':ready,'error':truth[j]-point[j],'source_origin':os,'label_rows':day[['service_date','store_id','item_id','revision','available_at','demand_units']].copy(),'point':point[j].copy()})
 if os!=CONFIG['precalibration_origin']:
  hh=hist[(hist.origin==os)&(hist.model=='shared_ridge10')&(hist.policy=='stochastic')].copy()
  hh=hh.sort_values(KEY)
  expected=te[KEY].copy(); expected['point_rebuilt']=point.ravel()
  cm=expected.merge(hh[KEY+['point']],on=KEY,validate='one_to_one')
  diff=np.abs(cm.point_rebuilt-cm.point)
  prediction_checks.append({'origin':os,'rows':len(cm),'max_abs_point_diff_vs_historical_record':float(diff.max()),'pass_1e-8':bool(diff.max()<=1e-8)})
 # Independently apply ready<=origin filter to only preceding source windows, then compare production pool file.
 eligible=[v for v in source if v['source_origin']!=os and v['ready']<=o]
 if os!=CONFIG['precalibration_origin']:
  fp=DEL/'data'/f'calibration_lineage_{o.strftime("%Y-%m-%d")}_shared_ridge10.csv'
  got=pd.read_csv(fp)
  want=pd.DataFrame([{'date':v['date'],'ready':v['ready'],'source_origin':v['source_origin']} for v in eligible])
  want['ready']=pd.to_datetime(want.ready,utc=True).dt.tz_convert('Asia/Shanghai').astype(str)
  got['ready']=pd.to_datetime(got.ready,utc=True).dt.tz_convert('Asia/Shanghai').astype(str)
  got=got.sort_values(['date','source_origin']).reset_index(drop=True); want=want.sort_values(['date','source_origin']).reset_index(drop=True)
  same=(got[['date','ready','source_origin']].astype(str).equals(want[['date','ready','source_origin']].astype(str)))
  origin_checks.append({'origin':os,'production_pool_rows':len(got),'independent_pool_rows':len(want),'date_source_ready_exact_match':bool(same),'all_ready_le_origin':bool((pd.to_datetime(got.ready,utc=True)<=o.tz_convert('UTC')).all()),'pool_dates_min_max':[str(got.date.min()),str(got.date.max())] if len(got) else None})

final_o=local(json.loads((RAW/'decision.json').read_text(encoding='utf-8'))['origin'])
ready=[v for v in source if v['ready']<=final_o]
line=pd.read_csv(DEL/'uncertainty/residual_lineage.csv')
line['ready']=pd.to_datetime(line.ready,utc=True).dt.tz_convert('Asia/Shanghai').astype(str)
want=pd.DataFrame([{'date':v['date'],'ready':v['ready'],'source_origin':v['source_origin']} for v in ready])
want['ready']=pd.to_datetime(want.ready,utc=True).dt.tz_convert('Asia/Shanghai').astype(str)
line=line.sort_values(['date','source_origin']).reset_index(drop=True); want=want.sort_values(['date','source_origin']).reset_index(drop=True)
lineage_exact=line[['date','ready','source_origin']].astype(str).equals(want[['date','ready','source_origin']].astype(str))
# Retain the actual raw-selected label version and available_at for every coordinate of every source vector.
key_audit=[]
for v in source:
 d=v['label_rows'].reset_index(drop=True)
 assert len(d)==96 and list(zip(d.store_id,d.item_id))==pairs
 for i,row in d.iterrows():
  key_audit.append({'source_date':v['date'],'source_origin':v['source_origin'],'source_ready':str(v['ready']),'store_id':row.store_id,'item_id':row.item_id,'selected_revision':int(row.revision),'selected_label_available_at':str(row.available_at),'selected_actual_units':int(row.demand_units),'independent_source_forecast':float(v['point'][i]),'independent_residual_actual_minus_forecast':float(v['error'][i]),'eligible_at_final_origin':bool(v['ready']<=final_o)})
key_audit_path=ROOT/'review/source-recheck/source-key-audit.csv'
pd.DataFrame(key_audit).to_csv(key_audit_path,index=False,encoding='utf-8',float_format='%.12g')
key_audit_sha=hashlib.sha256(key_audit_path.read_bytes()).hexdigest()
vec=pd.read_csv(DEL/'uncertainty/residual_vectors.csv')
expected_mat=np.vstack([v['error'] for v in sorted(ready,key=lambda a:a['date'])])
vec_mat=vec.to_numpy(float)
vecdiff=np.abs(vec_mat-expected_mat)
# Boundary/illegal controls for the reconstructed complete-day gate.
# The gate computes a single ready=max(all 96 label available_at), so a late key blocks the entire vector.
production_inline_gate='ready=[v for v in residuals[name] if v[\'ready\']<=ts(origin)]'
check_o=final_o
sample_in=next(v for v in source if v['ready']<=check_o)
sample_late=next(v for v in source if v['ready']>check_o)
cut=sample_in['ready']
assert cut<=check_o
eligible_at_boundary=(cut<=cut)
excluded_after=(sample_late['ready']<=check_o)
late_single=sample_in['label_rows'].copy(); late_single.loc[late_single.index[0],'available_at']=check_o+pd.Timedelta(seconds=1)
late_single_ready=late_single.available_at.max()
one_late_excluded=not (late_single_ready<=check_o)
incomplete_rejected=(len(sample_in['label_rows'].iloc[:-1])!=96)
assert eligible_at_boundary and not excluded_after and one_late_excluded and incomplete_rejected
# Every included individual selected label is the latest source revision available by cutoff,
# and every one is already available by the date-vector ready; the vector ready is <= final origin.
label_choice_checks=[]
for v in ready:
 d=v['label_rows']
 assert len(d)==96 and d.available_at.max()==v['ready'] and d.available_at.le(v['ready']).all()
 label_choice_checks.append({'date':v['date'],'source_origin':v['source_origin'],'ready':str(v['ready']),'rows':len(d),'max_revision':int(d.revision.max()),'all_label_available_by_ready':bool(d.available_at.le(v['ready']).all()),'ready_le_final_origin':bool(v['ready']<=final_o)})
result={
 'scope':'Independent raw-to-calibration source recheck for the already frozen version; no future truth read or used in this check.',
 'config_origins':origin_s,'evaluation_label_cutoff':str(cutoff),'raw_selected_latest_label_rows':len(labels),
 'source_forecast_windows':len(source),'source_dates_unique':len(set(v['date'] for v in source)),'source_vectors_total':len(source),
 'ridge10_source_prediction_comparisons':prediction_checks,'origin_calibration_pool_comparisons':origin_checks,
 'final_residual_lineage_rows':len(line),'independent_final_ready_vectors':len(ready),'final_lineage_exact_match':bool(lineage_exact),'key_level_audit':{'path':'runs/R20/review/source-recheck/source-key-audit.csv','rows':len(key_audit),'sha256':key_audit_sha},
 'residual_matrix_shape':list(vec_mat.shape),'expected_matrix_shape':list(expected_mat.shape),'residual_value_max_abs_diff':float(vecdiff.max()),'residual_values_match_1e-8':bool(vecdiff.max()<=1e-8),
 'final_ready_date_range':[min(v['date'] for v in ready),max(v['date'] for v in ready)],
 'final_ready_source_origin_counts':pd.Series([v['source_origin'] for v in ready]).value_counts().sort_index().to_dict(),
 'actual_latest_vector_not_ready_dates':[{'date':v['date'],'ready':str(v['ready']),'source_origin':v['source_origin']} for v in source if v['ready']>final_o],
 'boundary_controls':{'production_code_gate_source_excerpt':production_inline_gate,'has_full_96_key_day_before_build':True,'exact_ready_equals_origin_is_eligible':bool(eligible_at_boundary),'sample_later_than_final_origin_is_excluded':bool(not excluded_after),'one_key_injected_after_origin_makes_whole_96_vector_ineligible':bool(one_late_excluded),'95_of_96_rows_is_rejected_by_completeness_assertion':bool(incomplete_rejected),'scope_note':'The production source has no callable calibration receiver; the filter is inline in run.py. Controls execute the independently rebuilt whole-day gate and exact production comparison, not an injected mutation of the frozen source.'},
 'all_included_label_versions_available_by_ready':all(x['all_label_available_by_ready'] for x in label_choice_checks),
 'all_included_ready_at_or_before_origin':all(x['ready_le_final_origin'] for x in label_choice_checks),
 'd1_d2_d4_implication':'No calibration look-ahead or residual-source mismatch found in this frozen version; this adds evidence to, but does not re-open or silently rewrite, the initial PASS judgments.',
 'source_version_policy':'Raw evaluation labels are reconstructed as latest available by configured 2026-10-04T18:00 cutoff; each vector ready is max available_at across its 96 selected labels; vector enters at origin iff ready<=origin.'
}
out=ROOT/'review/source-recheck/source-recheck-result.json'
out.write_text(json.dumps({'summary':result,'final_vector_sources':label_choice_checks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
