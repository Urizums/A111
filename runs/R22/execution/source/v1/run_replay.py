"""Frozen fixed-policy replay. Explicit raw/config/newout; no previous results read."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, json, hashlib, sys, platform, importlib.metadata, time, itertools
import numpy as np
import pandas as pd
from reference_policy import Data, predict, matrix, optimize, verify_q, losses, ts
KEY=['service_date','store_id','item_id']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=2,default=str);f.write('\n')
def csv(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='') as f:x.to_csv(f,index=False,float_format='%.10f')
def ready_day(v,origin):
    return len(v)==96 and not v.duplicated(KEY).any() and v.service_date.nunique()==1 and v.service_date.iloc[0]<origin[:10] and ts(v.source_origin.iloc[0])<ts(origin) and pd.to_datetime(v.available_at).max()<=ts(origin)
def valid_forecast(point,lo,hi):
    assert all(np.isfinite(v).all() and (v>=0).all() for v in [point,lo,hi])
    assert (lo<=hi).all()
def metrics(z):
    if not len(z):return {'rows':0,'days':0,'status':'not_estimable',**{k:None for k in ['mae','rmse','bias','coverage','below','above','width','interval_score','shortage_per_day','waste_per_day','loss_per_day','procurement_per_day','q_per_day']}}
    n=z.service_date.nunique()
    return dict(rows=len(z),days=n,status='estimated',mae=float(z.abs_error.mean()),rmse=float(np.sqrt(z.sq_error.mean())),bias=float((z.point-z.actual).mean()),coverage=float(z.covered.mean()),below=float((z.actual<z.lower90).mean()),above=float((z.actual>z.upper90).mean()),width=float((z.upper90-z.lower90).mean()),interval_score=float(z.interval_score.mean()),shortage_per_day=float(z.shortage_yuan.sum()/n),waste_per_day=float(z.waste_yuan.sum()/n),loss_per_day=float((z.shortage_yuan+z.waste_yuan).sum()/n),procurement_per_day=float(z.procurement_yuan.sum()/n),q_per_day=float(z.q_units.sum()/n))
def tests(data,interface):
    s=np.zeros((3,96));s[:,:3]=[[1.25,3,2],[2,2.5,4],[3,1,0]]
    q,e=optimize(data,s,4,14)
    possibilities=[z for z in itertools.product(range(5),repeat=3) if sum(z)<=4 and np.dot(z,data.cost[:3])<=14]
    vals=[float(sum(losses(np.array(z),s[:,:3],data.a[:3],data.b[:3])).mean()) for z in possibilities]
    assert abs(e['objective']-min(vals))<1e-7
    rejected=[]
    for name,v in [('fraction',np.ones(96)*.5),('negative',np.ones(96)*-1),('upper',np.ones(96)*56),('nan',np.ones(96)*np.nan),('inf',np.ones(96)*np.inf),('capacity',np.ones(96)*20),('budget',np.array([55 if k in ['K03','K07'] else 0 for _,k in data.pairs]))]:
        try:verify_q(v,data,1600,6000)
        except AssertionError:rejected.append(name)
        else:raise AssertionError('accepted '+name)
    for name,v in [('nan',np.full((1,96),np.nan)),('inf',np.full((1,96),np.inf)),('negative',np.ones((1,96))*-1),('95coords',np.zeros((1,95)))]:
        try:optimize(data,v)
        except AssertionError:rejected.append('scenario_'+name)
        else:raise AssertionError('accepted scenario '+name)
    for bad in [np.array([np.nan]),np.array([np.inf]),np.array([-1.])]:
        try:valid_forecast(bad,np.array([0.]),np.array([1.]))
        except AssertionError:pass
        else:raise AssertionError('invalid prediction accepted')
    valid_forecast(np.array([10.]),np.array([1.25]),np.array([2.75]))
    assert optimize(data,np.zeros((1,96)))[0].sum()==0
    assert optimize(data,np.ones((1,96)),0,0)[0].sum()==0
    v=interface.iloc[:96].copy();v['service_date']='2026-07-09';v['source_origin']='2026-07-08T18:00:00';v['available_at']=ts('2026-07-22T18:00:00')
    o='2026-07-22T18:00:00';assert ready_day(v,o);assert not ready_day(v.iloc[:95],o)
    late=v.copy();late.loc[late.index[-1],'available_at']=ts(o)+pd.Timedelta(seconds=1);assert not ready_day(late,o)
    equal=v.copy();equal['source_origin']=o;assert not ready_day(equal,o)
    notended=v.copy();notended['service_date']=o[:10];assert not ready_day(notended,o)
    # Same source window: one fully ready day survives another not-ready day.
    other=late.copy();other['service_date']='2026-07-10';both=pd.concat([v,other]);kept=[d for d,g in both.groupby('service_date') if ready_day(g,o)];assert kept==['2026-07-09']
    r=data.tables['demand_reports']; revised=r[r.revision>1].iloc[0];arrival=revised.available_at;prior=data.snapshot(arrival-pd.Timedelta(seconds=1),'evaluation');at=data.snapshot(arrival,'evaluation')
    key=tuple(revised[k] for k in KEY)
    p=prior.set_index(KEY);a=at.set_index(KEY);assert key not in p.index or p.loc[key,'revision']<revised.revision;assert a.loc[key,'revision']==revised.revision
    return dict(oracle_count=len(vals),oracle_min=min(vals),solver=e,actual_objective=float(sum(losses(q,s,data.a,data.b)).mean()),invalid_rejected=rejected,published_precision=10,fractional_scenarios_accepted=True,point_outside_interval_accepted=True,revision_late_one_second_actual_key=key,readiness={'at_arrival':True,'95of96_rejected':True,'late_one_second_rejected':True,'equal_source_rejected':True,'unended_rejected':True,'partial_window_accepted_day':kept})
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw',required=True);ap.add_argument('--config',required=True);ap.add_argument('--newout',required=True);args=ap.parse_args()
    raw=Path(args.raw).resolve();cp=Path(args.config).resolve();out=Path(args.newout).resolve();out.mkdir(parents=True,exist_ok=False)
    conf=json.loads(cp.read_text('utf-8'));repo=Path.cwd();src=repo/conf['source_science'];begin=time.perf_counter()
    dump(out/'run_identity.json',{'begin_utc':datetime.now(timezone.utc).isoformat(),'argv':sys.argv,'raw_hashes':{p.name:sha(p) for p in raw.iterdir() if p.is_file()},'config_sha256':sha(cp),'source_hashes':{p.name:sha(p) for p in Path(__file__).parent.iterdir() if p.is_file()},'model':None,'tokens':None,'cost':None})
    dump(out/'environment.json',{'python':sys.version,'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn']},'model':None,'tokens':None,'cost':None})
    data=Data(raw,out);evals=data.snapshot(conf['evaluation_label_cutoff'],'evaluation');evals=evals[evals.service_date<=conf['last_service_date']];csv(out/'data/evaluation_labels.csv',evals)
    lines=[]
    for tab in data.tables:
        for i,line in enumerate((raw/(tab+'.csv')).read_bytes().splitlines(keepends=True)[1:],2):lines.append({'table':tab,'raw_row':i,'raw_line_sha256':hashlib.sha256(line).hexdigest()})
    csv(out/'data/raw_row_identity.csv',pd.DataFrame(lines))
    # Interface values are source identifiers and published point only; error/demand ignored.
    interface=pd.read_csv(src/'uncertainty/residual_coordinates_all.csv',dtype={'point':str})
    allowed=['service_date','store_id','item_id','revision','available_at','raw_row','raw_hash','method_id','source_origin','train_snapshot_sha256','point']
    interface=interface[allowed];assert not interface.duplicated(['source_origin','method_id']+KEY).any()
    dump(out/'validation/boundaries.json',tests(data,interface))
    source_rows=[];source_checks=[]
    for origin,gall in interface.groupby('source_origin',sort=True):
        if ts(origin)>=max(ts(o) for o in conf['origins']):continue
        tag=origin[:10];tr=data.snapshot(origin);csv(out/f'source_backtrace/train_{tag}.csv',tr)
        assert sha(out/f'source_backtrace/train_{tag}.csv')==sha(src/f'data/train_{tag}.csv')
        assert set(gall.train_snapshot_sha256)=={sha(src/f'data/train_{tag}.csv')}
        tf=data.features(tr[KEY],origin,tr);csv(out/f'source_backtrace/train_features_{tag}.csv',tf)
        assert sha(out/f'source_backtrace/train_features_{tag}.csv')==sha(src/f'data/train_features_{tag}.csv')
        recent=tr[tr.service_date>=(ts(origin)-pd.Timedelta(days=56)).strftime('%Y-%m-%d')][KEY];known=data.tables['promotions'];known=known[known.announced_at<=ts(origin)];imp=recent.merge(known,on=KEY,validate='one_to_one');csv(out/f'source_backtrace/promotion_imputation_sources_{tag}.csv',imp)
        assert sha(out/f'source_backtrace/promotion_imputation_sources_{tag}.csv')==sha(src/f'data/promotion_imputation_sources_{tag}.csv')
        for cand in conf['candidates']:
            name=cand['name'];g=gall[gall.method_id==name].sort_values(KEY).copy();grid=g[KEY];feat=data.features(grid,origin,tr);csv(out/f'source_backtrace/predict_features_{tag}_{name}.csv',feat)
            assert sha(out/f'source_backtrace/predict_features_{tag}_{name}.csv')==sha(src/f'data/predict_features_{tag}_{name}.csv')
            if cand['kind']=='ridge':
                coef=np.array(json.loads((src/f'models/coefficients_{tag}_{name}.json').read_text())['coefficients']);repoint=np.maximum(matrix(feat,cand['holiday_scale'])@coef,0)
            else:repoint=predict(data,origin,cand,tr,grid)[0].ravel()
            pub=g.point.astype(float).to_numpy();err=np.abs(repoint-pub);assert err.max()<1e-9,'source published precision mismatch'
            lab=grid.merge(evals,on=KEY,validate='one_to_one');assert (lab.revision.to_numpy()==g.revision.to_numpy()).all();assert (lab.raw_row.to_numpy()==g.raw_row.to_numpy()).all();assert (lab.raw_hash.to_numpy()==g.raw_hash.to_numpy()).all();assert (lab.available_at.astype(str).to_numpy()==g.available_at.to_numpy()).all()
            r=g.copy();r['mature_actual']=lab.demand_units.to_numpy();r['available_at']=lab.available_at.to_numpy();r['recomputed_point']=repoint;r['point']=pub;r['error_recomputed']=r.mature_actual-pub;source_rows.append(r)
            source_checks.append({'source_origin':origin,'method_id':name,'rows':len(g),'train_sha256':sha(src/f'data/train_{tag}.csv'),'max_published_rounding_difference':float(err.max())})
    rr=pd.concat(source_rows,ignore_index=True);csv(out/'uncertainty/source_coordinates_rebuilt.csv',rr);csv(out/'source_backtrace/checks.csv',pd.DataFrame(source_checks))
    allhist=[];poolrows=[];solvers=[];boundaries=[]
    for origin in conf['origins']:
        tag=origin[:10];train=data.snapshot(origin);csv(out/f'data/train_{tag}.csv',train);tf=data.features(train[KEY],origin,train);csv(out/f'data/train_features_{tag}.csv',tf)
        recent=train[train.service_date>=(ts(origin)-pd.Timedelta(days=56)).strftime('%Y-%m-%d')][KEY];known=data.tables['promotions'];known=known[known.announced_at<=ts(origin)];csv(out/f'data/promotion_imputation_sources_{tag}.csv',recent.merge(known,on=KEY,validate='one_to_one'))
        dates=pd.date_range(ts(origin).date()+pd.Timedelta(days=1),periods=conf['horizon_days']).strftime('%Y-%m-%d').tolist();grid=data.grid(dates);lab=grid.merge(evals,on=KEY,validate='one_to_one');assert len(lab)==4032 and lab.demand_units.notna().all();csv(out/f'data/target_labels_{tag}.csv',lab);y=lab.demand_units.to_numpy().reshape(42,96)
        boundaries.append({'origin':origin,'train_rows':len(train),'train_days':train.service_date.nunique(),'max_train_service':train.service_date.max(),'max_train_arrival':train.available_at.max(),'first_target':dates[0],'last_target':dates[-1],'activity_days':int(data.tables['calendar'].set_index('service_date').loc[dates,'holiday'].sum())})
        for cand in conf['candidates']:
            name=cand['name'];point,feat,coef=predict(data,origin,cand,train,grid);point=np.round(point,10);csv(out/f'data/predict_features_{tag}_{name}.csv',feat)
            if coef is not None:dump(out/f'models/coefficients_{tag}_{name}.json',{'coefficients':coef.tolist(),'train_sha256':sha(out/f'data/train_{tag}.csv')})
            ready=[];member=[]
            for (so,day),v in rr[rr.method_id==name].groupby(['source_origin','service_date'],sort=True):
                ok=ready_day(v,origin);rec={'origin':origin,'method_id':name,'source_origin':so,'service_date':day,'coordinates':len(v),'ready_at':v.available_at.max(),'eligible':bool(ok),'reason':'exact mature 96-coordinate day ready' if ok else 'source not earlier, day not ended, or used revision unavailable'};poolrows.append(rec)
                if ok:ready.append(v.sort_values(KEY).error_recomputed.to_numpy());member.append(rec)
            assert ready;assert len({r['service_date'] for r in member})==len(member)
            errors=np.array(ready);csv(out/f'uncertainty/pool_{tag}_{name}.csv',pd.DataFrame(member));csv(out/f'uncertainty/vectors_{tag}_{name}.csv',pd.DataFrame(errors,columns=[s+'_'+k for s,k in data.pairs]))
            sc=np.maximum(point[None,:,:]+errors[:,None,:],0);lo=np.round(np.quantile(sc,.05,axis=0,method='linear'),10);hi=np.round(np.quantile(sc,.95,axis=0,method='linear'),10);valid_forecast(point,lo,hi)
            np.savez_compressed(out/f'uncertainty/scenarios_{tag}_{name}.npz',demand_units=sc,residual_dates=np.array([r['service_date'] for r in member]),service_dates=np.array(dates),weights=np.ones(len(ready))/len(ready))
            qs=[]
            for j,day in enumerate(dates):
                q,e=optimize(data,sc[:,j,:],conf['capacity'],conf['budget']);qs.append(q);sh,wa=losses(q,sc[:,j,:],data.a,data.b);actual=float((sh+wa).mean());assert abs(actual-e['objective'])<1e-6;solvers.append(dict(origin=origin,method_id=name,service_date=day,objective_recomputed=actual,q_units=int(q.sum()),procurement_yuan=float(q@data.cost),capacity_slack=int(conf['capacity']-q.sum()),budget_slack=float(conf['budget']-q@data.cost),pool_days=len(ready),**e))
            qq=np.array(qs);z=feat[KEY+['holiday','promo_known','weather_known']].copy();z['origin']=origin;z['method_id']=name;z['horizon']=np.repeat(np.arange(1,43),96);z['stage']=np.where(z.horizon<=14,'1-14','15-42');z['band']=((z.horizon-1)//7+1).astype(int);z['point']=point.ravel();z['actual']=y.ravel();z['actual_revision']=lab.revision.to_numpy();z['actual_available_at']=lab.available_at.to_numpy();z['actual_raw_row']=lab.raw_row.to_numpy();z['lower90']=lo.ravel();z['upper90']=hi.ravel();z['interval_level']=.9;z['covered']=((y>=lo)&(y<=hi)).ravel();z['q_units']=qq.ravel();z['shortage_yuan']=(np.maximum(y-qq,0)*data.a).ravel();z['waste_yuan']=(np.maximum(qq-y,0)*data.b).ravel();z['procurement_yuan']=(qq*data.cost).ravel();z['abs_error']=abs(z.point-z.actual);z['sq_error']=(z.point-z.actual)**2;z['interval_score']=z.upper90-z.lower90+20*np.maximum(z.lower90-z.actual,0)+20*np.maximum(z.actual-z.upper90,0);z['pool_days']=len(ready);allhist.append(z)
            pred=grid.copy();pred['method_id']=name;pred['demand_point_units']=point.ravel();pred['lower90_units']=lo.ravel();pred['upper90_units']=hi.ravel();pred['interval_level']=.9;csv(out/f'predictions/{tag}_{name}.csv',pred);plan=grid.copy();plan['method_id']=name;plan['q_units']=qq.ravel();csv(out/f'plans/{tag}_{name}.csv',plan)
            print('completed',origin,name,'pool',len(ready),flush=True)
    hist=pd.concat(allhist,ignore_index=True);assert not hist.duplicated(['origin','method_id']+KEY).any();csv(out/'results/keys.csv',hist);csv(out/'uncertainty/membership.csv',pd.DataFrame(poolrows));csv(out/'results/solver_daily.csv',pd.DataFrame(solvers));csv(out/'data/boundaries.csv',pd.DataFrame(boundaries))
    # Explicit Cartesian group cells, including absent activity-by-horizon cells.
    specs={'overall':{},'stage':{'stage':['1-14','15-42']},'band':{'band':list(range(1,7))},'activity':{'holiday':[0,1]},'activity_stage':{'holiday':[0,1],'stage':['1-14','15-42']},'activity_band':{'holiday':[0,1],'band':list(range(1,7))},'activity_horizon':{'holiday':[0,1],'horizon':list(range(1,43))},'store':{'store_id':data.stores},'item':{'item_id':data.items},'horizon':{'horizon':list(range(1,43))}}
    for title,spec in specs.items():
        rows=[]
        for (o,m),g in hist.groupby(['origin','method_id']):
            for vals in itertools.product(*spec.values()):
                z=g
                for k,v in zip(spec,vals):z=z[z[k]==v]
                rows.append(dict(origin=o,method_id=m,**dict(zip(spec,vals)),**metrics(z)))
        csv(out/f'results/group_{title}.csv',pd.DataFrame(rows))
    daily=[]
    for (o,m,d),g in hist.groupby(['origin','method_id','service_date']):daily.append(dict(origin=o,method_id=m,service_date=d,holiday=int(g.holiday.iloc[0]),horizon=int(g.horizon.iloc[0]),**metrics(g)))
    daily=pd.DataFrame(daily);csv(out/'results/daily.csv',daily);paired=daily.pivot(index=['origin','service_date','holiday','horizon'],columns='method_id',values=['loss_per_day','interval_score']);paired.columns=['_'.join(t) for t in paired.columns];paired=paired.reset_index();paired['loss_W_minus_R']=paired.loss_per_day_weekly_mean56-paired.loss_per_day_shared_ridge10;paired['score_W_minus_R']=paired.interval_score_weekly_mean56-paired.interval_score_shared_ridge10;csv(out/'results/paired_daily.csv',paired)
    firsttwo=hist[hist.origin.isin(conf['origins'][:2])];assert firsttwo.service_date.nunique()==84
    csv(out/'results/combined_first_two.csv',pd.DataFrame([dict(method_id=m,**metrics(g)) for m,g in firsttwo.groupby('method_id')]))
    dump(out/'results/completion.json',{'all_keys':len(hist),'route_origin_rows':4032,'first_two_unique_days':84,'third_window_overlap_days':25,'runtime_seconds':time.perf_counter()-begin,'author_selfcheck_only':True,'actual_model':None,'tokens':None,'cost':None})
    print(pd.read_csv(out/'results/group_overall.csv').to_string(index=False),flush=True)
if __name__=='__main__':main()
