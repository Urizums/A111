"""Explicit raw/config/newout reproducible entry; no future actuals or external state."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,time,sys,platform,importlib.metadata,itertools
import numpy as np,pandas as pd
from reference_policy import Data,predict,optimize,losses,verify_q,ts,matrix
KEY=['service_date','store_id','item_id']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,default=str);f.write('\n')
def csv(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='') as f:d.to_csv(f,index=False,float_format='%.10f')
def metrics(z):
    sh=z.shortage_yuan.sum();wa=z.waste_yuan.sum();days=z.service_date.nunique()
    return dict(rows=len(z),days=days,mae=float(z.abs_error.mean()),rmse=float(np.sqrt(z.sq_error.mean())),bias_units_per_key=float((z.point-z.actual).mean()),coverage90=float(z.covered.mean()),below90=float((z.actual<z.lower90).mean()),above90=float((z.actual>z.upper90).mean()),width_units=float((z.upper90-z.lower90).mean()),loss_yuan_per_day=float((sh+wa)/days),shortage_yuan_per_day=float(sh/days),waste_yuan_per_day=float(wa/days),q_units_per_day=float(z.q_units.sum()/days),procurement_yuan_per_day=float(z.procurement_yuan.sum()/days))
def optimizer_tests(data):
    s=np.zeros((3,96));s[:,:3]=[[1.25,3,2],[2,2.5,4],[3,1,0]]
    q,e=optimize(data,s,4,14)
    ps=[z for z in itertools.product(range(5),repeat=3) if sum(z)<=4 and np.dot(z,data.cost[:3])<=14]
    vals=[float(sum(losses(np.array(z),s[:,:3],data.a[:3],data.b[:3])).mean()) for z in ps]
    assert abs(e['objective']-min(vals))<1e-7
    rejected=[]
    for name,sc in [('negative',np.full((2,96),-1)),('nan',np.full((2,96),np.nan)),('inf',np.full((2,96),np.inf)),('missing-coordinate',np.zeros((2,95)))]:
        try:optimize(data,sc)
        except AssertionError:rejected.append(name)
        else:raise AssertionError('accepted '+name)
    for name,v in [('q_fraction',np.ones(96)*.5),('q_negative',np.ones(96)*-1),('q_upper',np.ones(96)*56),('q_nan',np.ones(96)*np.nan),('capacity',np.ones(96)*20),('budget',np.array([55 if k in ['K03','K07'] else 0 for s,k in data.pairs]))]:
        try:verify_q(v,data,1600,6000)
        except AssertionError:rejected.append(name)
        else:raise AssertionError('accepted '+name)
    assert optimize(data,np.zeros((1,96)))[0].sum()==0
    assert optimize(data,np.ones((1,96)),0,0)[0].sum()==0
    try:optimize(data,np.ones((1,96)),-1,-1)
    except AssertionError:rejected.append('infeasible-resources')
    else:raise AssertionError('infeasible accepted')
    return {'enumerated_count':len(ps),'enumerated_min':min(vals),'milp_objective':e['objective'],'solver':e,'rejected':rejected,'finite_nonnegative_fraction_scenarios_accepted':True,'zero_demand_and_resource_tests':True}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw',required=True);ap.add_argument('--config',required=True);ap.add_argument('--newout',required=True);a=ap.parse_args()
    raw=Path(a.raw).resolve();cp=Path(a.config).resolve();out=Path(a.newout).resolve();out.mkdir(parents=True,exist_ok=False)
    conf=json.loads(cp.read_text('utf-8'));begin=time.perf_counter()
    dump(out/'run_identity.json',{'begin_utc':datetime.now(timezone.utc).isoformat(),'argv':sys.argv,'raw_hashes':{q.name:sha(q) for q in sorted(raw.iterdir()) if q.is_file()},'config_sha256':sha(cp),'source_hashes':{q.name:sha(q) for q in Path(__file__).parent.glob('*.py')},'model':None,'tokens':None,'cost':None})
    dump(out/'environment.json',{'python':sys.version,'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','matplotlib','reportlab','pypdf']},'method_resources':'CPU sequential same process, no candidate-specific budget; runtimes measured separately','model':None,'tokens':None,'cost':None})
    data=Data(raw,out)
    # Bind parsed row identities to original CSV line bytes, before duplicate collapse.
    row_identity=[]
    for tab in data.tables:
        lines=(raw/(tab+'.csv')).read_bytes().splitlines(keepends=True)
        for j,line in enumerate(lines[1:],2):row_identity.append({'table':tab,'raw_row':j,'raw_line_sha256':hashlib.sha256(line).hexdigest()})
    csv(out/'data/raw_row_identities.csv',pd.DataFrame(row_identity))
    r=data.tables['demand_reports'];assert r.service_date.max()<data.decision['future_begin'],'future actual in input'
    evals=data.snapshot(conf['evaluation_label_cutoff'],'evaluation');evals=evals[evals.service_date<=data.decision['origin'][:10]]
    csv(out/'data/evaluation_labels_fixed.csv',evals)
    final=data.snapshot(data.decision['origin']);csv(out/'data/final_train_snapshot.csv',final)
    unavailable=r[r.available_at>ts(data.decision['origin'])].copy();csv(out/'data/reports_unavailable_final_origin.csv',unavailable)
    tests=optimizer_tests(data);dump(out/'validation/optimizer_tests.json',tests)
    cs=conf['candidates'];origins=[conf['precalibration_origin']]+conf['selection_origins']+[conf['calibration_origin']]+conf['validation_origins']
    residuals={c['name']:[] for c in cs};hist=[];solvers=[];boundary=[];fit_times=[];pools=[];allres=[];interval_diag=[];selected=None
    for origin in origins:
        stage='precalibration' if origin==conf['precalibration_origin'] else 'selection' if origin in conf['selection_origins'] else 'calibration' if origin==conf['calibration_origin'] else 'validation'
        tag=origin[:10];train=data.snapshot(origin);csv(out/f'data/train_{tag}.csv',train)
        dates=pd.date_range(ts(origin).date()+pd.Timedelta(days=1),periods=conf['historical_horizon_days']).strftime('%Y-%m-%d').tolist();grid=data.grid(dates)
        labels=grid.merge(evals,on=KEY,how='left',validate='one_to_one');assert len(labels)==1344 and labels.demand_units.notna().all()
        y=labels.demand_units.to_numpy().reshape(-1,96)
        trfeat=data.features(train[KEY],origin,train);csv(out/f'data/train_features_{tag}.csv',trfeat)
        recent=train[train.service_date>=(ts(origin)-pd.Timedelta(days=56)).strftime('%Y-%m-%d')][KEY]
        known=data.tables['promotions'];known=known[known.announced_at<=ts(origin)]
        imp=recent.merge(known,on=KEY,validate='one_to_one');csv(out/f'data/promotion_imputation_sources_{tag}.csv',imp)
        changed=train.merge(evals[KEY+['demand_units','revision']],on=KEY,suffixes=('_asof','_mature'),validate='one_to_one')
        boundary.append({'origin':origin,'stage':stage,'train_rows':len(train),'train_complete_days':int((train.groupby('service_date').size()==96).sum()),'max_train_service_date':train.service_date.max(),'max_train_available_at':train.available_at.max(),'changed_label_count':int((changed.demand_units_asof!=changed.demand_units_mature).sum()),'changed_revision_count':int((changed.revision_asof!=changed.revision_mature).sum()),'snapshot_sha256':sha(out/f'data/train_{tag}.csv')})
        for c in cs:
            name=c['name'];t=time.perf_counter();point,feat,coef=predict(data,origin,c,train,grid)
            fit_times.append({'origin':origin,'method_id':name,'fit_predict_seconds':time.perf_counter()-t,'train_rows':len(train),'prediction_rows':len(grid)})
            csv(out/f'data/predict_features_{tag}_{name}.csv',feat)
            if coef is not None:dump(out/f'models/coefficients_{tag}_{name}.json',{'method_id':name,'coefficients':coef.tolist(),'columns':'96 pair,56 item-weekday,8 item-time30,8 item-discount,1 global holiday*0.3'})
            ready=[]
            for v in residuals[name]:
                ok=v['ready']<=ts(origin) and v['date']<origin[:10] and ts(v['source_origin'])<ts(origin)
                pools.append({'calibration_origin':origin,'method_id':name,'residual_day':v['date'],'source_origin':v['source_origin'],'ready_at':v['ready'],'coordinates':96,'eligible':ok,'reason':'accepted exact mature versions complete96' if ok else 'exact mature used versions unavailable or day not ended'})
                if ok:ready.append(v)
            if stage!='precalibration':
                assert ready,'empty calibration pool'
                errs=np.array([v['error'] for v in ready]);scen=np.maximum(point[None,:,:]+errs[:,None,:],0)
                lo=np.round(np.quantile(scen,.05,axis=0,method='linear'),10);hi=np.round(np.quantile(scen,.95,axis=0,method='linear'),10)
                for lev in conf['diagnostics']['central_interval_levels']:
                    l=np.quantile(scen,(1-lev)/2,axis=0);u=np.quantile(scen,1-(1-lev)/2,axis=0)
                    interval_diag.append({'stage':stage,'origin':origin,'method_id':name,'nominal_level':lev,'coverage':float(((y>=l)&(y<=u)).mean()),'width_units':float((u-l).mean()),'pool_days':len(errs)})
                for policy in ['stochastic','point_only']:
                    qq=[]
                    for j,d in enumerate(dates):
                        q,e=optimize(data,scen[:,j,:] if policy=='stochastic' else point[j][None,:]);qq.append(q)
                        solvers.append(dict(origin=origin,method_id=name,policy=policy,service_date=d,**e))
                    qq=np.array(qq);z=feat[KEY+['holiday','promo_known','weather_known']].copy()
                    z['origin']=origin;z['stage']=stage;z['method_id']=name;z['policy']=policy;z['horizon']=np.repeat(np.arange(1,15),96)
                    z['point']=point.ravel();z['actual']=y.ravel();z['actual_revision']=labels.revision.to_numpy();z['actual_available_at']=labels.available_at.to_numpy();z['actual_raw_row']=labels.raw_row.to_numpy()
                    z['lower90']=lo.ravel();z['upper90']=hi.ravel();z['covered']=((y>=lo)&(y<=hi)).ravel();z['q_units']=qq.ravel();z['shortage_yuan']=(np.maximum(y-qq,0)*data.a).ravel();z['waste_yuan']=(np.maximum(qq-y,0)*data.b).ravel();z['procurement_yuan']=(qq*data.cost).ravel();z['abs_error']=abs(z.point-z.actual);z['sq_error']=(z.point-z.actual)**2;z['pool_days']=len(errs);hist.append(z)
            for j,d in enumerate(dates):
                lab=labels[labels.service_date==d];assert len(lab)==96 and not lab.duplicated(KEY).any()
                v={'date':d,'ready':lab.available_at.max(),'error':y[j]-point[j],'source_origin':origin};residuals[name].append(v)
                rr=lab[KEY+['revision','available_at','raw_row','raw_hash','demand_units']].copy();rr['method_id']=name;rr['source_origin']=origin;rr['train_snapshot_sha256']=sha(out/f'data/train_{tag}.csv');rr['point']=point[j];rr['error']=v['error'];rr['full_day_ready_at']=v['ready'];rr['coordinates']=96;allres.append(rr)
        print('completed',stage,origin,flush=True)
        if origin==conf['selection_origins'][-1]:
            hh=pd.concat(hist);sel=hh[(hh.stage=='selection')&(hh.policy=='stochastic')];ranks={c['name']:metrics(sel[sel.method_id==c['name']])['loss_yuan_per_day'] for c in cs}
            selected=min(cs,key=lambda c:(ranks[c['name']],cs.index(c)))['name']
            dump(out/'results/selection.json',{'selected_method':selected,'actual_selected_at_utc':datetime.now(timezone.utc).isoformat(),'criterion':conf['selection_criterion'],'selection_losses_yuan_per_day':ranks,'selection_service_dates':[sel.service_date.min(),sel.service_date.max()],'validation_seen':False,'future_truth_seen':False,'config_sha256':sha(cp)})
            print('selection locked:',selected,ranks,flush=True)
    hist=pd.concat(hist,ignore_index=True);csv(out/'results/historical_predictions_plans.csv',hist);csv(out/'data/snapshot_boundaries.csv',pd.DataFrame(boundary));csv(out/'uncertainty/residual_coordinates_all.csv',pd.concat(allres,ignore_index=True));csv(out/'results/solver_history.csv',pd.DataFrame(solvers));csv(out/'results/fit_runtime.csv',pd.DataFrame(fit_times));csv(out/'results/interval_tradeoff.csv',pd.DataFrame(interval_diag))
    tables=[]
    for keys in [['stage','method_id','policy'],['origin','stage','method_id','policy'],['stage','method_id','policy','holiday'],['stage','method_id','policy','horizon'],['stage','method_id','policy','store_id'],['stage','method_id','policy','item_id']]:
        rows=[]
        for kval,g in hist.groupby(keys):rows.append(dict(zip(keys,kval),**metrics(g)))
        fn='group_'+'_'.join(keys)+'.csv';csv(out/'results'/fn,pd.DataFrame(rows));tables.append(fn)
    daily=hist.groupby(['stage','origin','service_date','method_id','policy']).agg(loss_yuan=('shortage_yuan','sum'),waste_yuan=('waste_yuan','sum'),q_units=('q_units','sum'),procurement_yuan=('procurement_yuan','sum')).reset_index();daily['loss_yuan']+=daily.waste_yuan;csv(out/'results/daily_history.csv',daily)
    paired=daily[(daily.stage=='validation')&(daily.policy=='stochastic')].pivot(index='service_date',columns='method_id',values='loss_yuan');diff=(paired['weekly_mean56']-paired['shared_ridge10']).to_numpy();rng=np.random.default_rng(conf['diagnostics']['bootstrap_seed']);boot=rng.choice(diff,(conf['diagnostics']['paired_bootstrap_day_replicates'],len(diff)),replace=True).mean(axis=1)
    dump(out/'results/paired_loss_diagnostic.json',{'definition':'weekly_mean56 minus shared_ridge10 validation daily realized loss','n_days':len(diff),'mean_difference_yuan':float(diff.mean()),'iid_day_bootstrap95':np.quantile(boot,[.025,.975]).tolist(),'limitations':'descriptive interval only: shared training/calibration and temporal dependence invalidate independence assumption; no route retuning','seed':conf['diagnostics']['bootstrap_seed']})
    finaldates=pd.date_range(data.decision['future_begin'],data.decision['future_end']).strftime('%Y-%m-%d').tolist();grid=data.grid(finaldates);assert len(grid)==4032
    future_summ=[];future_solv=[];future_mem={}
    finalfeatures=data.features(final[KEY],data.decision['origin'],final);csv(out/'data/final_train_features.csv',finalfeatures)
    for c in cs:
        name=c['name'];point,feat,coef=predict(data,data.decision['origin'],c,final,grid);csv(out/f'data/final_prediction_features_{name}.csv',feat)
        ready=[]
        for v in residuals[name]:
            ok=v['ready']<=ts(data.decision['origin']) and v['date']<data.decision['origin'][:10]
            pools.append({'calibration_origin':data.decision['origin'],'method_id':name,'residual_day':v['date'],'source_origin':v['source_origin'],'ready_at':v['ready'],'coordinates':96,'eligible':ok,'reason':'accepted exact mature versions complete96' if ok else 'exact mature used versions unavailable or day not ended'})
            if ok:ready.append(v)
        errs=np.array([v['error'] for v in ready]);sc=np.maximum(point[None,:,:]+errs[:,None,:],0);lo=np.round(np.quantile(sc,.05,axis=0,method='linear'),10);hi=np.round(np.quantile(sc,.95,axis=0,method='linear'),10)
        csv(out/f'uncertainty/residual_vectors_final_{name}.csv',pd.DataFrame(errs,columns=[s+'_'+k for s,k in data.pairs]));csv(out/f'uncertainty/residual_days_final_{name}.csv',pd.DataFrame([{k:v[k] for k in ['date','ready','source_origin']} for v in ready]))
        np.savez_compressed(out/f'uncertainty/scenarios_final_{name}.npz',demand_units=sc,service_dates=np.array(finaldates),coordinate_store=np.array([s for s,k in data.pairs]),coordinate_item=np.array([k for s,k in data.pairs]),residual_dates=np.array([v['date'] for v in ready]),weights=np.ones(len(ready))/len(ready))
        pp=grid.copy();pp['method_id']=name;pp['demand_point_units']=point.ravel();pp['lower90_units']=lo.ravel();pp['upper90_units']=hi.ravel();pp['interval_level']=.9;csv(out/f'future/{name}/predictions.csv',pp)
        qs=[]
        for j,d in enumerate(finaldates):
            q,e=optimize(data,sc[:,j,:]);qs.append(q);future_solv.append(dict(method_id=name,service_date=d,**e));sh,wa=losses(q,sc[:,j,:],data.a,data.b)
            future_summ.append({'method_id':name,'service_date':d,'holiday':int(feat.loc[feat.service_date==d,'holiday'].iloc[0]),'point_total_units':float(point[j].sum()),'q_units':int(q.sum()),'procurement_yuan':float(q@data.cost),'capacity_slack':int(1600-q.sum()),'budget_slack_yuan':float(6000-q@data.cost),'scenario_shortage_yuan':float(sh.mean()),'scenario_waste_yuan':float(wa.mean()),'scenario_loss_yuan':float((sh+wa).mean()),'pool_days':len(errs),'interval_mean_width':float((hi[j]-lo[j]).mean())})
        qs=np.array(qs);pl=grid.copy();pl['method_id']=name;pl['q_units']=qs.ravel();csv(out/f'future/{name}/replenishment.csv',pl)
        future_mem[name]=(point,sc,qs,feat)
        dump(out/f'models/final_{name}.json',{'method_id':name,'coefficients':None if coef is None else coef.tolist(),'train_snapshot_sha256':sha(out/'data/final_train_snapshot.csv'),'pool_days':len(errs),'final_origin':data.decision['origin'],'actual_future_performance':'unknown'})
    csv(out/'uncertainty/pool_membership_all_origins.csv',pd.DataFrame(pools));csv(out/'results/future_daily_summary.csv',pd.DataFrame(future_summ));csv(out/'results/solver_future.csv',pd.DataFrame(future_solv))
    # Sensitivity is conditional scenario evaluation, not observed future accuracy; declared diagnostics only.
    point,sc,qq,feat=future_mem[selected];stress=[];stress_solver=[]
    cases=[(f'resource_{cap}_{bud}',sc,cap,bud) for cap,bud in conf['diagnostics']['resource_pairs']]
    hol=feat.holiday.to_numpy().reshape(42,96)
    cases += [(f'activity_{m}',sc*np.where(hol,m,1),1600,6000) for m in conf['diagnostics']['activity_multipliers']]
    cases += [(f'all_demand_{m}',sc*m,1600,6000) for m in conf['diagnostics']['prediction_scale_multipliers']]
    for label,s,cap,bud in cases:
        aq=[];fixed=[];new=[]
        for j,d in enumerate(finaldates):
            q,e=optimize(data,s[:,j,:],cap,bud);aq.append(q);fixed.append(float(sum(losses(qq[j],s[:,j,:],data.a,data.b)).mean()));new.append(float(sum(losses(q,s[:,j,:],data.a,data.b)).mean()));stress_solver.append(dict(case=label,service_date=d,**e))
        aq=np.array(aq);pl=grid.copy();pl['q_units']=aq.ravel();pl['method_id']=selected;csv(out/f'diagnostics/plans_{label}.csv',pl)
        stress.append({'case':label,'method_id':selected,'capacity':cap,'budget':bud,'fixed_original_plan_feasible':bool((qq.sum(axis=1)<=cap).all() and ((qq*data.cost).sum(axis=1)<=bud).all()),'fixed_plan_scenario_loss_yuan_per_day':np.mean(fixed),'reoptimized_scenario_loss_yuan_per_day':np.mean(new),'q_l1_change_total':int(abs(aq-qq).sum()),'q_units_per_day':float(aq.sum(axis=1).mean()),'procurement_yuan_per_day':float((aq*data.cost).sum(axis=1).mean())})
    csv(out/'results/sensitivity.csv',pd.DataFrame(stress));csv(out/'results/solver_sensitivity.csv',pd.DataFrame(stress_solver))
    desc=finalfeatures.copy();desc['demand_units']=final.demand_units.to_numpy();csv(out/'data/descriptive_panel.csv',desc)
    for col in ['service_date','item_id','store_id','holiday','weekday_monday_zero']:
        csv(out/f'results/descriptive_{col}.csv',desc.groupby(col).demand_units.agg(['count','sum','mean','std']).reset_index())
    af=data.features(grid,data.decision['origin'],final)
    audit={'raw_rows':data.audit_result,'historical_services':[r.service_date.min(),r.service_date.max()],'final_train_rows':len(final),'final_train_days':final.service_date.nunique(),'final_partial_days':final.groupby('service_date').size().loc[lambda s:s!=96].to_dict(),'evaluation_rows':len(evals),'future_keys':len(grid),'future_promotion_known_rows':int(af.promo_known.sum()),'future_weather_known_rows':int(af.weather_known.sum()),'future_weather_missing_rain_rows':int(af.rain_mm.isna().sum()),'future_activity_dates':af.loc[af.holiday==1,'service_date'].unique().tolist(),'historical_activity_dates':desc.loc[desc.holiday==1,'service_date'].unique().tolist(),'demand_range':[int(r.demand_units.min()),int(r.demand_units.max())],'training_feature_matrix_rank_final':int(np.linalg.matrix_rank(matrix(finalfeatures,.3))),'training_feature_columns':169}
    dump(out/'data/audit_extended.json',audit)
    agg=hist.groupby(['stage','method_id','policy']).apply(metrics,include_groups=False).to_dict();sci={'selected_method':selected,'historical_stage_metrics':{'|'.join(k):v for k,v in agg.items()},'future_summary':pd.DataFrame(future_summ).groupby('method_id').agg(total_q_units=('q_units','sum'),total_procurement_yuan=('procurement_yuan','sum'),mean_scenario_loss_yuan=('scenario_loss_yuan','mean'),mean_interval_width=('interval_mean_width','mean'),pool_days=('pool_days','min')).to_dict('index'),'runtime_seconds':time.perf_counter()-begin,'future_actuals_seen':False,'actual_model':None,'tokens':None,'cost':None}
    dump(out/'results/science_summary.json',sci)
    print(json.dumps(sci,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
