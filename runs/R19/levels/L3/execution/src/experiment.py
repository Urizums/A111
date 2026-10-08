import time,json,csv,copy,traceback,datetime
from pathlib import Path
from solver import E,instance,solve,write_plan,save
from checker import validate_dir
TASKS=['Q1-S1','Q1-S2','Q1-F1','Q1-F2','Q2-N','Q2-C']
def main():
 start=time.perf_counter();d=instance();cfg0={'gap':3,'pressure':500,'run_seconds':120,'declared_phase_window_seconds':900,'memory_target_MB':1800,'reserve_support':True}
 save(E/'logs/comparison_declaration.json',{'created':datetime.datetime.now(datetime.UTC).isoformat(),'phase_window_seconds':900,'per_run_seconds':120,'methods':['baseline guillotine','maxrect column priority'],'seeds':[0,11,23],'mass_preference':[0,.5,1],'fragile_priority':[1,3,6],'single_selection':'nondominated union of all checked candidates; recommend max Uv then Uw','fleet_selection':'min N then C for F/N; min C then N for C','all_runs_retained':True})
 experiments=[];best={};pareto={};calls=[]
 candidates=[('baseline',0,.2,1.7)]+[('maxrect',seed,alpha,fp) for seed in [0,11,23] for alpha in [0,.5,1] for fp in [1,3,6]]
 for task in TASKS:
  for j,(method,seed,alpha,fp) in enumerate(candidates):
   cfg={**cfg0,'fragile_priority':fp};out=E/f'experiments/{task}/C{j:03d}';call={'task':task,'candidate':j,'method':method,'seed':seed,'alpha':alpha,'fragile_priority':fp,'start_utc':datetime.datetime.now(datetime.UTC).isoformat()}
   try:
    rows,m=solve(d,task,method,seed,alpha,cfg);write_plan(out,rows,m,cfg,d);v=validate_dir(out);call.update({'status':'completed','feasible':v['passed'],'runtime_seconds':m['runtime_seconds']})
    if not v['passed']:raise ValueError('coordinate validation rejected candidate')
    rec={'task':task,'candidate':f'C{j:03d}','method':method,'seed':seed,'alpha':alpha,'fragile_priority':fp,'N':m['N'],'C':m['C'],'Uv':m['Uv'],'Uw':m['Uw'],'runtime_seconds':m['runtime_seconds'],'valid':True,'path':str(out.relative_to(E))};experiments.append(rec)
    if task.startswith('Q1-S'):pareto.setdefault(task,[]).append(rec);key=(-m['Uv'],-m['Uw'])
    elif task=='Q2-C':key=(m['C'],m['N'],-m['Uv'])
    else:key=(m['N'],m['C'],-m['Uv'])
    if task not in best or key<best[task][0]:best[task]=(key,out)
   except Exception as ex:
    call.update({'status':'failed','exception':repr(ex),'traceback':traceback.format_exc()});save(out/'failure.json',call)
   calls.append(call)
   if time.perf_counter()-start>900:raise TimeoutError('comparison phase exhausted; results retained')
  print(task,[(r['method'],r['N'],r['C'],round(r['Uv'],4),round(r['Uw'],4)) for r in experiments if r['task']==task][:1], 'best',str(best[task][1].relative_to(E)),flush=True)
 for task,records in pareto.items():
  nd=[r for r in records if not any(s['Uv']>=r['Uv']-1e-12 and s['Uw']>=r['Uw']-1e-12 and (s['Uv']>r['Uv']+1e-12 or s['Uw']>r['Uw']+1e-12) for s in records)]
  unique={ (round(r['Uv'],12),round(r['Uw'],12)):r for r in nd };save(E/f'plans/{task}/pareto.json',{'scope':'sampled algorithm candidates; global Pareto frontier unproved','points':list(unique.values()),'recommended':'max volume utilization, then mass utilization','unattainable_full_mass_bound':'mass density bound in paper'})
 import shutil
 for task,(_,p) in best.items():
  dest=E/f'plans/{task}/selected';shutil.copytree(p,dest,dirs_exist_ok=True)
 save(E/'logs/actual_solver_calls.json',calls);save(E/'experiments/summary.json',experiments)
 with (E/'experiments/summary.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(experiments[0]));w.writeheader();w.writerows(experiments)
 save(E/'plans/selection.json',{t:str(p.relative_to(E)) for t,(_,p) in best.items()});print('completed',len(calls),'calls',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
