from pathlib import Path
import argparse,json,hashlib
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge
KEY=['service_date','store_id','item_id']
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def asof(r,o):
    return r[(r.available_at<=o)&(r.service_date<o[:10])].sort_values(KEY+['revision']).drop_duplicates(KEY,keep='last').sort_values(KEY)
def build_matrix(x):
    n=len(x);X=np.zeros((n,169));ii=np.arange(n);s=x.store_id.str[1:].astype(int).to_numpy()-1;k=x.item_id.str[1:].astype(int).to_numpy()-1
    X[ii,s*8+k]=1;X[ii,96+k*7+x.weekday_monday_zero.to_numpy().astype(int)]=1;X[ii,152+k]=x.time30;X[ii,160+k]=x.discount_fraction;X[:,168]=.3*x.holiday;return X
ap=argparse.ArgumentParser();ap.add_argument('--raw',required=True);ap.add_argument('--science',required=True);ap.add_argument('--config',required=True);ap.add_argument('--newout',required=True);a=ap.parse_args()
out=Path(a.newout);out.mkdir(parents=True,exist_ok=False);sc=Path(a.science);raw=Path(a.raw);conf=json.loads(Path(a.config).read_text('utf-8'))
r=pd.read_csv(raw/'demand_reports.csv');r=r.drop_duplicates();r=r.sort_values(KEY+['revision']);items=pd.read_csv(raw/'items.csv').set_index('item_id');st=sorted(pd.read_csv(raw/'stores.csv').store_id);it=sorted(items.index);pairs=[(s,k) for s in st for k in it]
cost=np.array([items.loc[k,'procurement_yuan'] for s,k in pairs]);aa=np.array([items.loc[k,'shortage_yuan'] for s,k in pairs]);bb=np.array([items.loc[k,'waste_yuan'] for s,k in pairs])
checks=[];defect=[]
def check(n,ok,detail):
    checks.append({'name':n,'passed':bool(ok),'detail':detail})
    if not ok:defect.append(n)
origins=[conf['precalibration_origin']]+conf['selection_origins']+[conf['calibration_origin']]+conf['validation_origins']
maxpointdiff=0.
for o in origins:
    tr=pd.read_csv(sc/f'data/train_{o[:10]}.csv');expected=asof(r,o)
    joined=tr.merge(expected,on=KEY,suffixes=('_saved','_expected'),validate='one_to_one')
    check('snapshot-'+o,len(joined)==len(expected)==len(tr) and np.array_equal(joined.revision_saved,joined.revision_expected) and np.array_equal(joined.demand_units_saved,joined.demand_units_expected),'independent highest revision raw recomputation')
evals=r[r.available_at<=conf['evaluation_label_cutoff']].drop_duplicates(KEY,keep='last');ev=pd.read_csv(sc/'data/evaluation_labels_fixed.csv');j=ev.merge(evals,on=KEY,suffixes=('_saved','_expected'),validate='one_to_one')
check('fixed-mature-evaluation',len(j)==len(ev)==len(evals) and np.array_equal(j.revision_saved,j.revision_expected) and np.array_equal(j.demand_units_saved,j.demand_units_expected),'Nov4 fixed used versions; historical only')
rc=pd.read_csv(sc/'uncertainty/residual_coordinates_all.csv');pools=pd.read_csv(sc/'uncertainty/pool_membership_all_origins.csv')
daycount=rc.groupby(['method_id','source_origin','service_date']).size();check('full96-vectors',(daycount==96).all() and not rc.duplicated(['method_id','source_origin']+KEY).any(),'complete unique store-item coordinates per service day')
j=rc.merge(evals,on=KEY,suffixes=('_saved','_expected'),validate='many_to_one');check('residual-label-version',np.array_equal(j.revision_saved,j.revision_expected) and np.array_equal(j.demand_units_saved,j.demand_units_expected),'same fixed mature source versions for every residual')
check('residual-arithmetic',np.max(abs(rc.error-(rc.demand_units-rc.point)))<1e-8,'saved residual equals label minus old point')
ready=rc.groupby(['method_id','source_origin','service_date']).available_at.max()
poolok=True
for row in pools.itertuples():
    ra=ready.loc[(row.method_id,row.source_origin,row.residual_day)]
    cutoff=pd.Timestamp(row.calibration_origin).tz_localize('Asia/Shanghai');rtime=pd.Timestamp(ra);ok=rtime<=cutoff and row.residual_day<row.calibration_origin[:10] and pd.Timestamp(row.source_origin)<pd.Timestamp(row.calibration_origin)
    poolok=poolok and bool(ok)==bool(row.eligible) and pd.Timestamp(row.ready_at)==rtime
check('per-day-exact-version-pool',poolok,'all accepted and excluded days independently reconstructed, no whole-window completion restriction')
def points_for(name,o,tr,features):
    if name=='shared_ridge10':
        co=json.loads((sc/(f'models/coefficients_{o[:10]}_{name}.json' if o!= '2026-10-31T18:00:00' else f'models/final_{name}.json')).read_text('utf-8'))['coefficients'];p=np.maximum(build_matrix(features)@np.array(co),0)
    else:
        cut=(pd.Timestamp(o)-pd.Timedelta(days=56)).strftime('%Y-%m-%d');recent=tr[tr.service_date>=cut].copy();recent['wd']=pd.to_datetime(recent.service_date).dt.weekday;means=recent.groupby(['store_id','item_id','wd']).demand_units.mean();fallback=tr.groupby(['store_id','item_id']).demand_units.mean();p=np.array([means.get((s,k,w),fallback.get((s,k))) for s,k,w in features[['store_id','item_id','weekday_monday_zero']].itertuples(index=False,name=None)])
    return p
for o in origins:
    tr=pd.read_csv(sc/f'data/train_{o[:10]}.csv')
    for name in ['shared_ridge10','weekly_mean56']:
        ff=pd.read_csv(sc/f'data/predict_features_{o[:10]}_{name}.csv');p=points_for(name,o,tr,ff);v=rc[(rc.method_id==name)&(rc.source_origin==o)].sort_values(KEY);maxpointdiff=max(maxpointdiff,float(np.max(abs(p-v.point.to_numpy()))))
check('out-of-origin-forecast-lineage',maxpointdiff<1e-7,{'max_point_recompute_difference':maxpointdiff})
finalorigin='2026-10-31T18:00:00';train=pd.read_csv(sc/'data/final_train_snapshot.csv');ft=pd.read_csv(sc/'data/final_train_features.csv');fit=Ridge(alpha=10,fit_intercept=False,solver='cholesky').fit(build_matrix(ft),train.demand_units);coef=np.array(json.loads((sc/'models/final_shared_ridge10.json').read_text('utf-8'))['coefficients']);check('fixed-ridge-final-refit',np.max(abs(coef-fit.coef_))<1e-7,{'coefficient_difference':float(np.max(abs(coef-fit.coef_))),'alpha':10,'fit_intercept':False,'columns':169})
finals=[]
for name in ['shared_ridge10','weekly_mean56']:
    pred=pd.read_csv(sc/f'future/{name}/predictions.csv');q=pd.read_csv(sc/f'future/{name}/replenishment.csv');ff=pd.read_csv(sc/f'data/final_prediction_features_{name}.csv');z=np.load(sc/f'uncertainty/scenarios_final_{name}.npz');s=z['demand_units'];err=pd.read_csv(sc/f'uncertainty/residual_vectors_final_{name}.csv').to_numpy();p=points_for(name,finalorigin,train,ff);expected=pd.DataFrame([(d,s,k) for d in pd.date_range('2026-11-01','2026-12-12').strftime('%Y-%m-%d') for s,k in pairs],columns=KEY)
    check(name+'-future-grid',len(pred)==len(q)==4032 and pred[KEY].equals(expected) and q[KEY].equals(expected),'42 days *12 stores *8 items, unique ordered grid')
    check(name+'-point',np.max(abs(p-pred.demand_point_units))<1e-7,'from saved asof snapshot and exact frozen method')
    numeric=pred[['demand_point_units','lower90_units','upper90_units','interval_level']].to_numpy();check(name+'-interval-domain',np.isfinite(numeric).all() and (numeric[:,:3]>=0).all() and (numeric[:,1]<=numeric[:,2]).all() and (numeric[:,3]==.9).all(),'finite nonnegative central empirical90')
    check(name+'-scenario-lineage',np.max(abs(s-np.maximum(pred.demand_point_units.to_numpy().reshape(42,96)[None,:,:]+err[:,None,:],0)))<1e-7 and np.allclose(z['weights'],1/len(err)),'equal weights and exact additive residuals')
    lo=np.round(np.quantile(s,.05,axis=0,method='linear'),10);hi=np.round(np.quantile(s,.95,axis=0,method='linear'),10);check(name+'-quantile',np.max(abs(lo.ravel()-pred.lower90_units))<1e-9 and np.max(abs(hi.ravel()-pred.upper90_units))<1e-9,'numpy linear quantile rounded10')
    qq=q.q_units.to_numpy().reshape(42,96);check(name+'-feasibility',np.isfinite(qq).all() and (qq==np.floor(qq)).all() and (qq>=0).all() and (qq<=55).all() and (qq.sum(axis=1)<=1600).all() and ((qq*cost).sum(axis=1)<=6000+1e-8).all(),{'max_daily_units':int(qq.sum(axis=1).max()),'max_daily_procurement':float((qq*cost).sum(axis=1).max())})
    sh=(np.maximum(s-qq[None,:,:],0)*aa).sum(axis=2).mean(axis=0);wa=(np.maximum(qq[None,:,:]-s,0)*bb).sum(axis=2).mean(axis=0);summ=pd.read_csv(sc/'results/future_daily_summary.csv');su=summ[summ.method_id==name];check(name+'-objective',np.max(abs(sh-su.scenario_shortage_yuan))<1e-7 and np.max(abs(wa-su.scenario_waste_yuan))<1e-7,'procurement excluded; shortage+waste raw item coefficients')
    so=pd.read_csv(sc/'results/solver_future.csv');so=so[so.method_id==name];check(name+'-optimality-evidence',(so.status==0).all() and (so.gap<=1e-8).all() and np.max(abs((sh+wa)-so.objective))<1e-7,'solver status0 plus objective re-evaluation, MILP numerical tolerance')
    finals.append({'method_id':name,'rows':len(pred),'total_q':int(qq.sum()),'mean_scenario_loss':float((sh+wa).mean()),'pool_days':len(err)})
hist=pd.read_csv(sc/'results/historical_predictions_plans.csv');h=hist[hist.policy=='stochastic'];ranks={n:float(h[(h.stage=='selection')&(h.method_id==n)][['shortage_yuan','waste_yuan']].sum().sum()/42) for n in ['shared_ridge10','weekly_mean56']};selected=min(conf['candidates'],key=lambda c:(ranks[c['name']],conf['candidates'].index(c)))['name'];saved=json.loads((sc/'results/selection.json').read_text('utf-8'));check('historical-only-selection',selected==saved['selected_method'] and not saved['validation_seen'] and not saved['future_truth_seen'],'same frozen primary criterion independently summed over 42 selection days')
env=json.loads((sc/'environment.json').read_text('utf-8'));check('unknown-resource-fields',all(env.get(k) is None for k in ['model','tokens','cost']),'unknown actual host/model/token/cost preserved null')
report={'scope':'author self-check only, not independent acceptance','checks':checks,'failed':defect,'finals':finals,'selection_recomputed':ranks,'all_passed':not defect}
with (out/'self-check.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2));assert not defect,defect
