import pandas as pd, numpy as np, hashlib, json
from pathlib import Path
root=Path('runs/R20')
truth_path=root/'evaluation/holdout_truth.csv'
lock=json.loads((root/'evaluation-lock.json').read_text(encoding='utf-8'))
expected=next(x for x in lock['files'] if x['path']=='runs/R20/evaluation/holdout_truth.csv')
b=truth_path.read_bytes(); sha=hashlib.sha256(b).hexdigest()
assert len(b)==expected['size_bytes'] and sha==expected['sha256'], 'holdout identity mismatch'
pred=pd.read_csv(root/'execution/delivery/results/future_predictions.csv')
plan=pd.read_csv(root/'execution/delivery/results/future_replenishment.csv')
truth=pd.read_csv(truth_path)
items=pd.read_csv(root/'inputs/raw/items.csv')
keys=['service_date','store_id','item_id']
for name,df in [('pred',pred),('plan',plan),('truth',truth)]:
 assert not df.duplicated(keys).any(), f'{name} duplicate keys'
 assert len(df)==1344, f'{name} row count {len(df)}'
base=pred.merge(plan,on=keys,validate='one_to_one').merge(truth,on=keys,validate='one_to_one').merge(items,on='item_id',validate='many_to_one')
assert len(base)==1344 and not base['demand_units'].isna().any()
assert set(pred[keys].itertuples(index=False,name=None))==set(truth[keys].itertuples(index=False,name=None))
assert np.isfinite(base[['demand_point_units','lower90_units','upper90_units','q_units','demand_units']].to_numpy()).all()
assert (base.demand_units>=0).all() and np.equal(base.demand_units,np.floor(base.demand_units)).all()
assert (base.lower90_units<=base.demand_point_units).all() and (base.demand_point_units<=base.upper90_units).all()
assert np.equal(base.q_units,np.floor(base.q_units)).all() and (base.q_units>=0).all() and (base.q_units<=base.daily_max_units).all()
base['err']=base.demand_point_units-base.demand_units
base['abs_err']=base.err.abs()
base['sq_err']=base.err**2
base['covered']=(base.demand_units>=base.lower90_units)&(base.demand_units<=base.upper90_units)
base['shortage_units']=(base.demand_units-base.q_units).clip(lower=0)
base['waste_units']=(base.q_units-base.demand_units).clip(lower=0)
base['shortage_loss']=base.shortage_units*base.shortage_yuan
base['waste_loss']=base.waste_units*base.waste_yuan
base['purchase']=base.q_units*base.procurement_yuan
base['loss']=base.shortage_loss+base.waste_loss
# aggregate after only frozen-plan evaluation; no tuning or selection
byday=base.groupby('service_date').agg(rows=('item_id','size'),actual_units=('demand_units','sum'),predicted_units=('demand_point_units','sum'),q_units=('q_units','sum'),purchase_yuan=('purchase','sum'),loss_yuan=('loss','sum'),shortage_yuan=('shortage_loss','sum'),waste_yuan=('waste_loss','sum'),abs_error=('abs_err','mean'),covered=('covered','mean'))
metrics={'truth_sha256':sha,'truth_bytes':len(b),'keys_exact':True,'rows':len(base),'days':len(byday),'MAE_units_per_store_item_day':float(base.abs_err.mean()),'RMSE_units_per_store_item_day':float(np.sqrt(base.sq_err.mean())),'bias_pred_minus_truth_units_per_store_item_day':float(base.err.mean()),'90_interval_coverage_fraction':float(base.covered.mean()),'mean_interval_width_units':float((base.upper90_units-base.lower90_units).mean()),'total_actual_demand_units':int(base.demand_units.sum()),'total_point_prediction_units':float(base.demand_point_units.sum()),'total_q_units':int(base.q_units.sum()),'total_purchase_yuan':float(base.purchase.sum()),'total_shortage_units':int(base.shortage_units.sum()),'total_waste_units':int(base.waste_units.sum()),'total_shortage_loss_yuan':float(base.shortage_loss.sum()),'total_waste_loss_yuan':float(base.waste_loss.sum()),'total_two_part_loss_yuan':float(base.loss.sum()),'mean_daily_two_part_loss_yuan':float(byday.loss_yuan.mean()),'daily_q_min_max':[int(byday.q_units.min()),int(byday.q_units.max())],'daily_purchase_min_max':[float(byday.purchase_yuan.min()),float(byday.purchase_yuan.max())],'all_days_capacity_ok':bool((byday.q_units<=1600).all()),'all_days_budget_ok':bool((byday.purchase_yuan<=6000).all()),'all_item_caps_ok':bool((base.q_units<=base.daily_max_units).all()),'holdout_used_for_tuning':False,'interpretation':'Evaluation of the already frozen synthetic future against its sealed truth; not real-world evidence and not used for selection.'}
out=Path('runs/R20/review/initial/holdout_independent_result.json')
out.write_text(json.dumps({'metrics':metrics,'by_day':byday.reset_index().to_dict(orient='records')},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metrics,ensure_ascii=False,indent=2))
