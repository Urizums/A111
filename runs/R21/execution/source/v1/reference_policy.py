"""Raw -> availability audit -> time-ordered experiments -> integer plan -> figures/paper.
Only inputs/locks and this execution code/config are read. No design smoke is consumed.
"""
from pathlib import Path
import argparse, hashlib, json, sys, platform, time, itertools, importlib.metadata
import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import csr_matrix
from sklearn.linear_model import Ridge

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
EXEC=HERE.parent
KEY=['service_date','store_id','item_id']

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def csv(p,x):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    x.to_csv(p,index=False,encoding='utf-8',float_format='%.10f')
def ts(s):
    z=pd.Timestamp(s)
    return z.tz_localize('Asia/Shanghai') if z.tzinfo is None else z.tz_convert('Asia/Shanghai')

class Data:
    def __init__(self,raw,out):
        self.raw=Path(raw); self.out=Path(out)
        self.tables={}
        for name in ['demand_reports','stores','items','calendar','promotions','weather']:
            d=pd.read_csv(self.raw/(name+'.csv')); d['raw_row']=np.arange(2,len(d)+2)
            d['raw_hash']=[hashlib.sha256(str(t).encode()).hexdigest() for t in d.drop(columns='raw_row').itertuples(index=False,name=None)]
            for col in ['available_at','announced_at']:
                if col in d: d[col]=pd.to_datetime(d[col],format='%Y-%m-%dT%H:%M:%S',errors='raise').dt.tz_localize('Asia/Shanghai')
            self.tables[name]=d
        self.decision=json.loads((self.raw/'decision.json').read_text())
        self.stores=sorted(self.tables['stores'].store_id); self.items=sorted(self.tables['items'].item_id)
        self.pairs=[(s,k) for s in self.stores for k in self.items]
        self.par=self.tables['items'].set_index('item_id')
        self.cost=np.array([self.par.loc[k,'procurement_yuan'] for s,k in self.pairs])
        self.a=np.array([self.par.loc[k,'shortage_yuan'] for s,k in self.pairs])
        self.b=np.array([self.par.loc[k,'waste_yuan'] for s,k in self.pairs])
        self.maxq=np.array([self.par.loc[k,'daily_max_units'] for s,k in self.pairs],dtype=int)
        self.audit()

    def audit(self):
        r=self.tables['demand_reports']; clean=r.drop_duplicates(subset=[c for c in r if c not in ['raw_row','raw_hash']])
        assert clean.groupby(KEY+['revision']).size().max()==1,'conflicting same-key revision'
        assert ((clean['revision']%1)==0).all() and (clean.revision>=1).all()
        assert clean.groupby(KEY).apply(lambda g:g.sort_values('revision').available_at.is_monotonic_increasing,include_groups=False).all()
        self.tables['demand_reports']=clean
        for name,keys in [('stores',['store_id']),('items',['item_id']),('calendar',['service_date']),('promotions',KEY),('weather',['service_date','zone_id','kind','available_at'])]:
            assert not self.tables[name].duplicated(keys).any(),f'duplicate {name}'
        for name,cols in [('demand_reports',['demand_units','settlement_yuan']),('items',['procurement_yuan','shortage_yuan','waste_yuan','daily_max_units']),('promotions',['discount_fraction']),('calendar',['weekday_monday_zero','holiday'])]:
            for c in cols: assert np.isfinite(self.tables[name][c]).all() and (self.tables[name][c]>=0).all(),(name,c)
        assert (clean.demand_units%1==0).all()
        assert (self.tables['promotions'].discount_fraction<=1).all()
        assert (self.tables['calendar'].holiday.isin([0,1])).all()
        assert (self.tables['calendar'].weekday_monday_zero==pd.to_datetime(self.tables['calendar'].service_date).dt.weekday).all()
        w=self.tables['weather']; assert set(w.kind)=={'forecast','observed'}
        assert np.isfinite(w.rain_mm.dropna()).all() and (w.rain_mm.dropna()>=0).all()
        for n in ['demand_reports','promotions']:
            assert set(self.tables[n].store_id)<=set(self.stores) and set(self.tables[n].item_id)<=set(self.items)
            assert set(self.tables[n].service_date)<=set(self.tables['calendar'].service_date)
        assert set(w.zone_id)<=set(self.tables['stores'].zone_id)
        self.audit_result={'raw_rows':{n:len(d) for n,d in self.tables.items()},'demand_original_rows':len(r),'complete_duplicates_removed':len(r)-len(clean),'demand_unique_keys':len(clean[KEY].drop_duplicates()),'weather_missing_rain':int(w.rain_mm.isna().sum()),'unit_checks':'finite nonnegative numeric fields; integral demand/revision; promotion in [0,1]; weekday/date; unique dimensions and joins; monotone revisions','timezone':'Asia/Shanghai','raw_hashes':{p.name:digest(p) for p in sorted(self.raw.iterdir()) if p.is_file()}}
        dump(self.out/'data/audit.json',self.audit_result)

    def snapshot(self,origin,purpose='train'):
        o=ts(origin); r=self.tables['demand_reports']
        x=r[r.available_at<=o].sort_values(KEY+['revision']).drop_duplicates(KEY,keep='last').sort_values(KEY).copy()
        if purpose=='train': x=x[x.service_date<o.strftime('%Y-%m-%d')]
        x['origin']=o.isoformat(); x['purpose']=purpose
        assert x.available_at.le(o).all()
        return x

    def grid(self,dates):
        return pd.DataFrame([(d,s,k) for d in dates for s,k in self.pairs],columns=KEY)

    def features(self,g,origin,train):
        o=ts(origin); p=self.tables['promotions']; known=p[p.announced_at<=o]
        x=g.merge(self.tables['calendar'].drop(columns=['raw_row','raw_hash']),on='service_date',validate='many_to_one')
        x=x.merge(self.tables['stores'][['store_id','zone_id']],on='store_id',validate='many_to_one')
        x=x.merge(known[KEY+['discount_fraction','announced_at','raw_row','raw_hash']].rename(columns={'raw_row':'promo_raw_row','raw_hash':'promo_raw_hash'}),on=KEY,how='left',validate='one_to_one')
        x['promo_known']=x.discount_fraction.notna().astype(int)
        recent=train[train.service_date>=(o-pd.Timedelta(days=56)).strftime('%Y-%m-%d')][KEY]
        means=recent.merge(known[KEY+['discount_fraction']],on=KEY,validate='one_to_one').groupby('item_id').discount_fraction.mean()
        x['discount_fraction']=x.discount_fraction.fillna(x.item_id.map(means)).fillna(0)
        w=self.tables['weather']; f=w[(w.kind=='forecast')&(w.available_at<=o)].sort_values('available_at').drop_duplicates(['service_date','zone_id'],keep='last')
        x=x.merge(f[['service_date','zone_id','rain_mm','available_at','raw_row']].rename(columns={'available_at':'weather_available_at','raw_row':'weather_raw_row'}),on=['service_date','zone_id'],how='left',validate='many_to_one')
        x['weather_known']=x.weather_available_at.notna().astype(int)
        x['time30']=(pd.to_datetime(x.service_date)-pd.Timestamp('2026-05-01')).dt.days/30
        x['origin']=o.isoformat()
        assert len(x)==len(g) and not x.duplicated(KEY).any()
        assert x.announced_at.dropna().le(o).all() and x.weather_available_at.dropna().le(o).all()
        return x

def matrix(x,holiday_scale):
    si=x.store_id.str[1:].astype(int).to_numpy()-1; ki=x.item_id.str[1:].astype(int).to_numpy()-1
    n=len(x); a=np.zeros((n,96+56+8+8+1)); idx=np.arange(n)
    a[idx,si*8+ki]=1; a[idx,96+ki*7+x.weekday_monday_zero.to_numpy().astype(int)]=1
    a[idx,152+ki]=x.time30.to_numpy(); a[idx,160+ki]=x.discount_fraction.to_numpy()
    a[:,168]=x.holiday.to_numpy()*holiday_scale
    return a

def predict(data,origin,cand,train,test):
    tr=data.features(train[KEY],origin,train); te=data.features(test,origin,train)
    if cand['kind']=='weekly':
        recent=train[train.service_date>=(ts(origin)-pd.Timedelta(days=cand['window'])).strftime('%Y-%m-%d')].copy()
        recent['wd']=pd.to_datetime(recent.service_date).dt.weekday
        grouped=recent.groupby(['store_id','item_id','wd']).demand_units.agg(cand['stat'])
        pred=np.array([grouped.get((s,k,w),train[(train.store_id==s)&(train.item_id==k)].demand_units.mean()) for s,k,w in te[['store_id','item_id','weekday_monday_zero']].itertuples(index=False,name=None)])
        coeff=None
    else:
        model=Ridge(alpha=cand['alpha'],fit_intercept=False,solver='cholesky')
        model.fit(matrix(tr,cand['holiday_scale']),train.demand_units.to_numpy())
        pred=model.predict(matrix(te,cand['holiday_scale'])); coeff=model.coef_
    return np.maximum(pred,0).reshape(-1,96),te,coeff

def losses(q,d,a,b):
    sh=np.maximum(d-q,0)*a; wa=np.maximum(q-d,0)*b
    return sh.sum(axis=-1),wa.sum(axis=-1)

def verify_q(q,data,capacity,budget):
    q=np.asarray(q)
    assert q.dtype!=np.bool_ and np.isfinite(q).all() and (q>=0).all() and (q==np.floor(q)).all(),'invalid q'
    assert (q<=data.maxq).all(),'upper bound'
    assert q.sum()<=capacity,'capacity'
    assert np.dot(q,data.cost)<=budget,'budget'

def optimize(data,scenarios,capacity=1600,budget=6000):
    s=np.asarray(scenarios); assert s.ndim==2 and s.shape[1]==96 and np.isfinite(s).all() and (s>=0).all()
    maxj=int(data.maxq.max()); qgrid=np.arange(maxj+1)
    g=(np.maximum(s[:,:,None]-qgrid,0)*data.a[None,:,None]+np.maximum(qgrid-s[:,:,None],0)*data.b[None,:,None]).mean(axis=0)
    gains=g[:,:-1]-g[:,1:]
    assert (np.diff(gains,axis=1)<=1e-7).all(),'nonconvex marginal costs'
    inds=np.array([(i,j) for i in range(96) for j in range(data.maxq[i]) if gains[i,j]>1e-10],dtype=int)
    if len(inds)==0: return np.zeros(96,dtype=int),{'status':0,'gap':0,'objective':float(g[:,0].sum()),'bound':float(g[:,0].sum()),'seconds':0}
    c=-gains[inds[:,0],inds[:,1]]
    cons=csr_matrix(np.vstack([np.ones(len(inds)),data.cost[inds[:,0]]]))
    begin=time.perf_counter()
    res=milp(c,integrality=np.ones(len(c)),bounds=Bounds(0,1),constraints=LinearConstraint(cons,[-np.inf,-np.inf],[capacity,budget]),options={'mip_rel_gap':1e-9})
    assert res.x is not None,f'no solver solution: {res.message}'
    q=np.bincount(inds[:,0],weights=np.rint(res.x),minlength=96).astype(int)
    verify_q(q,data,capacity,budget)
    actual=float(g[np.arange(96),q].sum())
    assert abs(actual-(g[:,0].sum()+res.fun))<1e-6,'prefix aggregation mismatch'
    return q,{'status':int(res.status),'message':res.message,'gap':float(res.mip_gap),'objective':actual,'bound':float(g[:,0].sum()+res.mip_dual_bound),'seconds':time.perf_counter()-begin,'nodes':int(res.mip_node_count)}

def greedy_point(data,point,capacity=1600,budget=6000):
    q=np.zeros(96,dtype=int)
    while True:
        gains=data.a*(np.maximum(point-q,0)-np.maximum(point-q-1,0))+data.b*(np.maximum(q-point,0)-np.maximum(q+1-point,0))
        valid=(q<data.maxq)&(q.sum()+1<=capacity)&(np.dot(q,data.cost)+data.cost<=budget)
        gains=np.where(valid,gains,0)
        if gains.max()<=1e-9: break
        q[np.argmax(gains/data.cost)]+=1
    verify_q(q,data,capacity,budget); return q

def oracle_tests(data):
    # Embed a three-coordinate small instance; remaining q forced by zero demand.
    scenarios=np.zeros((3,96)); scenarios[:,:3]=[[1,3,2],[2,2,4],[3,1,0]]
    q,ev=optimize(data,scenarios,4,14)
    possibilities=[np.array(z) for z in itertools.product(range(5),repeat=3) if sum(z)<=4 and np.dot(z,data.cost[:3])<=14]
    objs=[float(sum(losses(z,scenarios[:,:3],data.a[:3],data.b[:3])).mean()) for z in possibilities]
    assert abs(ev['objective']-min(objs))<1e-7
    assert optimize(data,np.zeros((1,96)))[0].sum()==0
    assert optimize(data,np.ones((1,96))*10,0,0)[0].sum()==0
    rejections=[]
    for label,vec in [('negative',np.full(96,-1)),('fraction',np.full(96,0.5)),('nan',np.full(96,np.nan)),('infinity',np.full(96,np.inf)),('upper',np.full(96,56)),('capacity',np.full(96,20)),('budget',np.array([55 if k in ['K03','K07'] else 0 for s,k in data.pairs]))]:
        try: verify_q(vec,data,1600,6000)
        except AssertionError: rejections.append(label)
        else: raise AssertionError('accepted illegal '+label)
    return {'small_instance_enumerated':len(objs),'oracle_min_loss':min(objs),'solver_loss':ev['objective'],'illegal_q_rejected':rejections,'zero_resources_q':0,'zero_demand_q':0}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--audit-only',action='store_true'); ap.add_argument('--compute-only',action='store_true'); args=ap.parse_args()
    out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    config=json.loads((EXEC/'config/experiment.json').read_text(encoding='utf-8')); raw=REPO/'runs/R20/inputs/raw'
    locked=[]
    for lock in ['input-lock.json','design-lock.json']:
        l=json.loads((REPO/'runs/R20'/lock).read_text())
        for f in l['files']:
            p=REPO/f['path']; assert p.stat().st_size==f['size_bytes'] and digest(p)==f['sha256']; locked.append(f['path'])
    m=json.loads((REPO/'runs/R20/design/manifest.json').read_text())
    for f in m['files']: assert digest(REPO/f['path'])==f['sha256']
    dump(out/'data/identity.json',{'checked_locked_files':locked,'design_manifest_verified':True,'config_sha256':digest(EXEC/'config/experiment.json')})
    data=Data(raw,out)
    final=data.snapshot(data.decision['origin']); csv(out/'data/final_snapshot.csv',final)
    assert len(final)==152*96 and final.service_date.max()=='2026-09-29'
    r=data.tables['demand_reports']; late=r[(r.service_date=='2026-09-30')]
    assert len(late)==96 and late.available_at.gt(ts(data.decision['origin'])).all()
    rejected_future_labels=late[KEY+['available_at','revision']].copy(); rejected_future_labels['reason']='available_at > decision origin'; csv(out/'data/rejected_late_labels.csv',rejected_future_labels)
    env={'python':sys.version,'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','matplotlib','reportlab','pypdf']},'model':None,'tokens':None,'cost':None}
    dump(out/'environment.json',env)
    tests=oracle_tests(data); dump(out/'data/optimizer_tests.json',tests)
    if args.audit_only:
        print(json.dumps({'audit':data.audit_result,'identity_files':len(locked),'snapshot_rows':len(final),'optimizer_tests':tests,'environment':env},ensure_ascii=False,indent=2)); return
    candidates=config['candidates']; origins=[config['precalibration_origin']]+config['selection_origins']+[config['calibration_origin'],config['holdout_origin']]
    label=data.snapshot(config['evaluation_label_cutoff'],'evaluation')
    csv(out/'data/evaluation_labels.csv',label)
    residuals={c['name']:[] for c in candidates}; metrics=[]; hist_rows=[]; solver=[]; boundary=[]; chosen=None; coefficients={}
    for fold,origin in enumerate(origins):
        dates=pd.date_range(ts(origin).date()+pd.Timedelta(days=1),periods=14).strftime('%Y-%m-%d').tolist()
        train=data.snapshot(origin); grid=data.grid(dates)
        actual=grid.merge(label[KEY+['demand_units','revision','available_at']],on=KEY,validate='one_to_one')
        assert len(actual)==1344 and actual.demand_units.notna().all()
        truth=actual.demand_units.to_numpy().reshape(14,96)
        foldname=origin[:10]; csv(out/f'data/snapshot_{foldname}.csv',train)
        changed=train.merge(label[KEY+['demand_units']],on=KEY,suffixes=('_origin','_later'),validate='one_to_one')
        boundary.append({'origin':origin,'train_rows':len(train),'later_changed_train_labels':int((changed.demand_units_origin!=changed.demand_units_later).sum()),'last_train_date':train.service_date.max()})
        stage='precalibration' if fold==0 else ('selection' if origin in config['selection_origins'] else ('calibration' if origin==config['calibration_origin'] else 'holdout'))
        active=candidates if stage in ['precalibration','selection'] else [next(c for c in candidates if c['name']==chosen),candidates[0]]
        active=list({c['name']:c for c in active}.values())
        for cand in active:
            name=cand['name']; point,features,coef=predict(data,origin,cand,train,grid)
            if coef is not None: coefficients[name]=coef.tolist()
            csv(out/f'data/feature_lineage_{foldname}_{name}.csv',features)
            if stage=='precalibration':
                for j,d in enumerate(dates):
                    residuals[name].append({'date':d,'ready':actual.loc[actual.service_date==d,'available_at'].max(),'error':truth[j]-point[j],'source_origin':origin})
                continue
            ready=[v for v in residuals[name] if v['ready']<=ts(origin)]
            errs=np.array([v['error'] for v in ready]); assert len(errs)>=1
            csv(out/f'data/calibration_lineage_{foldname}_{name}.csv',pd.DataFrame([{k:v[k] for k in ['date','ready','source_origin']} for v in ready]))
            assert all(v['ready']<=ts(origin) for v in ready)
            scen=np.maximum(point[None,:,:]+errs[:,None,:],0)
            lower=np.round(np.quantile(scen,0.05,axis=0),10); upper=np.round(np.quantile(scen,0.95,axis=0),10)
            policies=['stochastic','point_greedy'] if name==chosen or stage=='selection' else ['stochastic','point_greedy']
            qs={p:[] for p in policies}
            for day in range(14):
                q,sev=optimize(data,scen[:,day,:]); qs['stochastic'].append(q)
                solver.append(dict(origin=origin,model=name,service_date=dates[day],**sev))
                qs['point_greedy'].append(greedy_point(data,point[day]))
            for policy in policies:
                q=np.array(qs[policy]); sh,wa=losses(q,truth,data.a,data.b)
                metrics.append({'stage':stage,'origin':origin,'model':name,'policy':policy,'mae':float(abs(truth-point).mean()),'rmse':float(np.sqrt(((truth-point)**2).mean())),'total_bias_units_per_day':float((point-truth).sum(axis=1).mean()),'loss_yuan_per_day':float((sh+wa).mean()),'shortage_yuan_per_day':float(sh.mean()),'waste_yuan_per_day':float(wa.mean()),'coverage90':float(((truth>=lower)&(truth<=upper)).mean()),'interval_width_units':float((upper-lower).mean()),'q_units_per_day':float(q.sum(axis=1).mean()),'procurement_yuan_per_day':float((q*data.cost).sum(axis=1).mean()),'calibration_days':len(errs)})
                z=features[KEY+['promo_known','weather_known','holiday']].copy(); z['stage']=stage; z['origin']=origin; z['model']=name; z['policy']=policy
                z['horizon']=np.repeat(np.arange(1,15),96); z['point']=point.ravel(); z['lower90']=lower.ravel(); z['upper90']=upper.ravel(); z['actual']=truth.ravel(); z['q_units']=q.ravel(); z['shortage_yuan']=(np.maximum(truth-q,0)*data.a).ravel(); z['waste_yuan']=(np.maximum(q-truth,0)*data.b).ravel()
                hist_rows.append(z)
            for j,d in enumerate(dates):
                residuals[name].append({'date':d,'ready':actual.loc[actual.service_date==d,'available_at'].max(),'error':truth[j]-point[j],'source_origin':origin})
        print(f'finished {stage} {origin}',flush=True)
        if origin==config['selection_origins'][-1]:
            ms=pd.DataFrame(metrics); rank=ms[(ms.stage=='selection')&(ms.policy=='stochastic')].groupby('model').loss_yuan_per_day.mean()
            chosen=min(candidates,key=lambda c:(rank[c['name']],candidates.index(c)))['name']
            dump(out/'results/selection.json',{'selected_model':chosen,'criterion':config['selection_criterion'],'selection_mean_loss':rank.to_dict(),'holdout_used_for_selection':False})
            print('selected',chosen,flush=True)
    csv(out/'results/backtest_metrics.csv',pd.DataFrame(metrics)); historical=pd.concat(hist_rows,ignore_index=True); csv(out/'results/historical_predictions_plans.csv',historical)
    csv(out/'data/snapshot_boundaries.csv',pd.DataFrame(boundary)); csv(out/'results/solver_evidence_history.csv',pd.DataFrame(solver))
    # No parameter is changed after opening holdout. Final calibration can use completed holdout as historical data.
    dates=pd.date_range(data.decision['future_begin'],data.decision['future_end']).strftime('%Y-%m-%d').tolist(); grid=data.grid(dates)
    cand=next(c for c in candidates if c['name']==chosen); point,features,coef=predict(data,data.decision['origin'],cand,final,grid)
    final_ready=[v for v in residuals[chosen] if v['ready']<=ts(data.decision['origin'])]
    errs=np.array([v['error'] for v in final_ready]); csv(out/'uncertainty/residual_vectors.csv',pd.DataFrame(errs,columns=[s+'_'+k for s,k in data.pairs]))
    csv(out/'uncertainty/residual_lineage.csv',pd.DataFrame([{k:v[k] for k in ['date','ready','source_origin']} for v in final_ready]))
    scen=np.maximum(point[None,:,:]+errs[:,None,:],0); lower=np.round(np.quantile(scen,.05,axis=0),10); upper=np.round(np.quantile(scen,.95,axis=0),10)
    pred=grid.copy(); pred['demand_point_units']=point.ravel(); pred['lower90_units']=lower.ravel(); pred['upper90_units']=upper.ravel(); pred['interval_level']=.9
    csv(out/'results/future_predictions.csv',pred); csv(out/'data/final_feature_lineage.csv',features)
    dump(out/'results/model_coefficients.json',{'model':chosen,'coef':None if coef is None else coef.tolist(),'column_definition':'pair(96), item-weekday(56), item-time30(8), item-discount(8), global-holiday*0.3(1)'})
    scenrows=[]
    for j in range(len(errs)):
        z=grid.copy(); z['scenario_id']=j; z['weight']=1/len(errs); z['demand_units']=scen[j].ravel(); scenrows.append(z)
    csv(out/'uncertainty/future_scenarios.csv',pd.concat(scenrows,ignore_index=True))
    dump(out/'uncertainty/method.json',{'model':chosen,'calibration_vectors':len(errs),'source_origins':origins,'weight':1/len(errs),'generation':'point plus full 96-coordinate same-day error vector, clipped at zero; same vector carried through all 14 future days is a stress dependence convention, not identified interday joint distribution','marginal_interval':'empirical 5th and 95th percentiles','historical_ordering':'each origin calibrated only on earlier fully completed windows','future_coverage':'unknown; synthetic data, limited holidays and absent historical long weather batches preclude finite-sample coverage guarantee'})
    qs=[]; summaries=[]; fs=[]
    for i,d in enumerate(dates):
        q,ev=optimize(data,scen[:,i,:]); qs.append(q); fs.append(dict(service_date=d,**ev))
        sh,wa=losses(q,scen[:,i,:],data.a,data.b)
        summaries.append({'service_date':d,'predicted_units':float(point[i].sum()),'q_units':int(q.sum()),'procurement_yuan':float(q@data.cost),'capacity_slack':int(1600-q.sum()),'budget_slack_yuan':float(6000-q@data.cost),'scenario_mean_loss_yuan':float((sh+wa).mean()),'scenario_shortage_yuan':float(sh.mean()),'scenario_waste_yuan':float(wa.mean()),'scenario_p90_daily_loss_yuan':float(np.quantile(sh+wa,.9))})
    q=np.array(qs); plan=grid.copy(); plan['q_units']=q.ravel(); csv(out/'results/future_replenishment.csv',plan); csv(out/'results/decision_summary.csv',pd.DataFrame(summaries)); csv(out/'results/solver_evidence_future.csv',pd.DataFrame(fs))
    joined=plan.merge(pred,on=KEY,validate='one_to_one').merge(data.tables['items'].drop(columns=['raw_row','raw_hash']),on='item_id',validate='many_to_one')
    joined['procurement_yuan_used']=joined.q_units*joined.procurement_yuan
    for group in ['item_id','store_id']:
        agg=joined.groupby(group).agg(q_units=('q_units','sum'),predicted_units=('demand_point_units','sum'),procurement_yuan=('procurement_yuan_used','sum')).reset_index(); csv(out/f'results/allocation_{group}.csv',agg)
    stress=[]
    future_holiday=features.holiday.to_numpy().reshape(14,96)
    perturb=[('holiday_0.8',np.where(future_holiday,.8,1)),('holiday_1.2',np.where(future_holiday,1.2,1)),('weather_0.9',.9),('weather_1.1',1.1)]
    for label,mul in perturb:
        ss=scen*mul; altered=[]; origloss=[]; newloss=[]
        for i in range(14):
            alt,ev=optimize(data,ss[:,i,:]); altered.append(alt)
            origloss.append(float(sum(losses(q[i],ss[:,i,:],data.a,data.b)).mean())); newloss.append(float(sum(losses(alt,ss[:,i,:],data.a,data.b)).mean()))
        aa=np.array(altered); csv(out/f'results/sensitivity_plan_{label}.csv',pd.concat([grid,pd.DataFrame({'q_units':aa.ravel()})],axis=1))
        stress.append({'case':label,'capacity':1600,'budget':6000,'mean_fixed_plan_loss':np.mean(origloss),'mean_reoptimized_loss':np.mean(newloss),'q_l1_change':int(abs(aa-q).sum()),'mean_q_units':aa.sum(axis=1).mean(),'mean_procurement_yuan':(aa*data.cost).sum(axis=1).mean()})
    for cap,bud in config['sensitivity']['resource_pairs']:
        aa=[]; ll=[]
        for i in range(14):
            z,_=optimize(data,scen[:,i,:],cap,bud); aa.append(z); ll.append(float(sum(losses(z,scen[:,i,:],data.a,data.b)).mean()))
        aa=np.array(aa); stress.append({'case':f'resource_{cap}_{bud}','capacity':cap,'budget':bud,'mean_fixed_plan_loss':np.nan,'mean_reoptimized_loss':np.mean(ll),'q_l1_change':int(abs(aa-q).sum()),'mean_q_units':aa.sum(axis=1).mean(),'mean_procurement_yuan':(aa*data.cost).sum(axis=1).mean()})
    csv(out/'results/sensitivity.csv',pd.DataFrame(stress))
    # Descriptive tables are based on final-origin snapshot, never later labels.
    desc=data.features(final[KEY],data.decision['origin'],final); desc['demand_units']=final.demand_units.to_numpy(); csv(out/'data/descriptive_panel.csv',desc)
    for group in ['service_date','weekday_monday_zero','item_id','store_id','zone_id','holiday']:
        agg=desc.groupby(group).demand_units.agg(['mean','sum','count']).reset_index(); csv(out/f'results/descriptive_{group}.csv',agg)
    w=data.tables['weather']; wcomp=w[w.kind=='forecast'][['service_date','zone_id','rain_mm']].merge(w[w.kind=='observed'][['service_date','zone_id','rain_mm']],on=['service_date','zone_id'],suffixes=('_forecast','_observed'),validate='one_to_one').dropna()
    dump(out/'results/weather_diagnostics.json',{'paired_nonmissing':len(wcomp),'forecast_rain_mae_mm':float(abs(wcomp.rain_mm_forecast-wcomp.rain_mm_observed).mean()),'forecast_rain_bias_mm':float((wcomp.rain_mm_forecast-wcomp.rain_mm_observed).mean()),'future_rain_missing':int(features.drop_duplicates(['service_date','zone_id']).rain_mm.isna().sum()),'weather_excluded_from_prediction':True})
    assert len(pred)==1344 and len(plan)==1344 and pred[KEY].equals(grid) and plan[KEY].equals(grid)
    assert np.isfinite(pred.drop(columns=KEY).to_numpy()).all() and (pred.demand_point_units>=0).all() and (pred.lower90_units<=pred.upper90_units).all()
    for i in range(14): verify_q(q[i],data,1600,6000)
    dump(out/'results/run_summary.json',{'selected_model':chosen,'future_rows':len(pred),'residual_days':len(errs),'total_q_units':int(q.sum()),'total_procurement_yuan':float((q*data.cost).sum()),'author_self_checks':'passed computed scope; independent acceptance pending','holdout_not_tuned':True,'config_sha256':digest(EXEC/'config/experiment.json'),'code_sha256':digest(__file__)})
    if not args.compute_only:
        from report import build_report
        build_report(out,data,config)
    print(json.dumps(json.loads((out/'results/run_summary.json').read_text()),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
