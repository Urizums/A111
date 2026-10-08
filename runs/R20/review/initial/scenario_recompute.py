import json
from pathlib import Path
import numpy as np,pandas as pd
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix
ROOT=Path(__file__).resolve().parents[4]; D=ROOT/'runs/R20/execution/delivery'; RAW=ROOT/'runs/R20/inputs/raw'
items=pd.read_csv(RAW/'items.csv').set_index('item_id'); stores=sorted(pd.read_csv(RAW/'stores.csv').store_id.unique()); itemids=sorted(items.index)
pairs=[(s,k) for s in stores for k in itemids];
sc=pd.read_csv(D/'uncertainty/future_scenarios.csv'); pred=pd.read_csv(D/'results/future_predictions.csv'); plan=pd.read_csv(D/'results/future_replenishment.csv'); summary=pd.read_csv(D/'results/decision_summary.csv')
keys=['service_date','store_id','item_id']; dates=sorted(pred.service_date.unique()); expected={(d,s,k) for d in dates for s in stores for k in itemids}
# Full scenario and weight integrity, then independent uncertainty and loss calculations.
scenario_keys=sc.groupby(['service_date','scenario_id'])[keys].size()
weights=sc.groupby('scenario_id').weight.agg(['min','max','first'])
all_scenario_keys=True
for d in dates:
 g=sc[sc.service_date==d]
 for sid,x in g.groupby('scenario_id'):
  ks=list(zip(x.service_date,x.store_id,x.item_id))
  all_scenario_keys &= len(ks)==96 and len(set(ks))==96 and {(d,s,k) for s,k in pairs}==set(ks)
sc_count=sc.scenario_id.nunique(); weight_sum=float(weights['first'].sum())
interval_diffs=[]; loss_diffs=[]; opt_diffs=[]; daily=[]; solver_states=[]
for d in dates:
 g=sc[sc.service_date==d]
 mat=g.pivot(index='scenario_id',columns=['store_id','item_id'],values='demand_units').reindex(columns=pairs).sort_index()
 scen=mat.to_numpy(float)
 qrows=plan[plan.service_date==d].set_index(['store_id','item_id']).reindex(pairs)
 q=qrows.q_units.to_numpy(float)
 pday=pred[pred.service_date==d].set_index(['store_id','item_id']).reindex(pairs)
 ypoint=pday.demand_point_units.to_numpy(float)
 lo=np.quantile(scen,.05,axis=0); hi=np.quantile(scen,.95,axis=0)
 interval_diffs.append(float(max(np.max(np.abs(lo-pday.lower90_units.to_numpy(float))),np.max(np.abs(hi-pday.upper90_units.to_numpy(float))))))
 c=items.loc[[k for s,k in pairs]].procurement_yuan.to_numpy(float); a=items.loc[[k for s,k in pairs]].shortage_yuan.to_numpy(float); b=items.loc[[k for s,k in pairs]].waste_yuan.to_numpy(float); mx=items.loc[[k for s,k in pairs]].daily_max_units.to_numpy(int)
 short=np.maximum(scen-q[None,:],0)*a[None,:]; waste=np.maximum(q[None,:]-scen,0)*b[None,:]; sl=(short+waste).sum(axis=1)
 rep=summary[summary.service_date==d].iloc[0]
 diffs={'scenario_mean_loss':float(sl.mean()-rep.scenario_mean_loss_yuan),'scenario_shortage':float(short.sum(axis=1).mean()-rep.scenario_shortage_yuan),'scenario_waste':float(waste.sum(axis=1).mean()-rep.scenario_waste_yuan),'p90_loss':float(np.quantile(sl,.9)-rep.scenario_p90_daily_loss_yuan),'q_units':float(q.sum()-rep.q_units),'procurement':float(q@c-rep.procurement_yuan),'point_forecast_sum':float(ypoint.sum()-rep.predicted_units)}
 loss_diffs.append(diffs)
 # Independent one-hot q-level integer program, not the production marginal-prefix construction.
 choices=[]; obj=[]; row=[]; col=[]; val=[]
 for i in range(96):
  for n in range(int(mx[i])+1):
   idx=len(choices); choices.append((i,n))
   obj.append(float((np.maximum(scen[:,i]-n,0)*a[i]+np.maximum(n-scen[:,i],0)*b[i]).mean()))
   row.append(i);col.append(idx);val.append(1.)
   row.append(96);col.append(idx);val.append(float(n))
   row.append(97);col.append(idx);val.append(float(c[i]*n))
 A=coo_matrix((val,(row,col)),shape=(98,len(choices))).tocsr()
 lb=np.r_[np.ones(96),[-np.inf,-np.inf]]; ub=np.r_[np.ones(96),[1600.,6000.]]
 res=milp(np.asarray(obj),integrality=np.ones(len(obj)),bounds=Bounds(0,1),constraints=LinearConstraint(A,lb,ub),options={'mip_rel_gap':1e-9})
 assert res.x is not None and res.success, f'independent one-hot solver failed {d}: {res.message}'
 indobj=float(res.fun); delivered=float(sum(obj[j] for j,(i,n) in enumerate(choices) if int(round(q[i]))==n))
 opt_diffs.append({'date':d,'independent_onehot_objective':indobj,'delivered_objective':delivered,'difference':delivered-indobj,'gap':float(res.mip_gap),'solver_status':int(res.status)})
 solver_states.append({'date':d,'status':int(res.status),'gap':float(res.mip_gap)})
 daily.append({'date':d,'q_units':int(q.sum()),'source_procurement_yuan':float(q@c),'scenario_mean_loss_yuan':float(sl.mean()),'scenario_shortage_yuan':float(short.sum(axis=1).mean()),'scenario_waste_yuan':float(waste.sum(axis=1).mean()),'scenario_p90_daily_loss_yuan':float(np.quantile(sl,.9)),'max_q_bound_violations':int(np.sum(q>mx))})
output={'future_scenario_count':int(sc_count),'scenario_rows':len(sc),'all_14x96_scenario_keys_complete_unique':bool(all_scenario_keys),'weights_each_consistent':bool(np.allclose(weights['min'],weights['max'])),'scenario_weight_sum':weight_sum,'all_scenario_demands_finite_nonnegative':bool(np.isfinite(sc.demand_units).all() and (sc.demand_units>=0).all()),'max_pointwise_interval_difference_from_empirical_quantile':max(interval_diffs),'max_absolute_recomputed_decision_summary_difference':{k:max(abs(x[k]) for x in loss_diffs) for k in loss_diffs[0]},'independent_onehot_milp_vs_delivered':opt_diffs,'all_delivered_plans_match_independent_onehot_optimum':all(x['difference']<=1e-6 and x['difference']>=-1e-5 for x in opt_diffs),'solver_states':solver_states,'daily_recomputation':daily,'future_truth_opened':False}
print(json.dumps(output,ensure_ascii=False,indent=2))
