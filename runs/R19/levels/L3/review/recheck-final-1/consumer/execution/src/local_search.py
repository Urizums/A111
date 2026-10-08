import csv,json,copy,time,itertools
from collections import Counter
from solver import E,instance,solve,write_plan,metrics,bounds,save
from checker import check,validate_dir
def canonical(rows,task):
 ids=Counter();vs={};mapping={};out=[]
 for r in rows:
  key=(r['vehicle_id'],r['item_id']);t=r['cargo_type'];ids[t]+=1;mapping[key]=f'{t}-{ids[t]:04d}';vs.setdefault(r['vehicle_id'],f'V{len(vs)+1:03d}')
 for r in rows:
  s=dict(r);s['item_id']=mapping[(r['vehicle_id'],r['item_id'])];s['support_ids']=mapping[(r['vehicle_id'],r['support_ids'])] if r['support_ids'] else '';s['vehicle_id']=vs[r['vehicle_id']];s['task_id']=task;out.append(s)
 return out
def run(task,initial):
 d=instance();rows=list(csv.DictReader((initial/'placements.csv').open(encoding='utf-8-sig')));cfg={'gap':3,'pressure':500,'run_seconds':120,'reserve_support':True,'phase_window_seconds':600,'memory_target_MB':1800};start=time.perf_counter();calls=[];history=[]
 old=metrics(d['cargo'],d['vehicles'],rows)
 for iteration in range(4):
  groups={}
  for r in rows:groups.setdefault(r['vehicle_id'],[]).append(r)
  best=None
  for keys in itertools.combinations(groups,2):
   subrows=[r for k in keys for r in groups[k]];sd=copy.deepcopy(d);ct=Counter(r['cargo_type'] for r in subrows)
   for c in sd['cargo']:c['quantity']=ct[c['cargo_type']]
   origN=2;origC=sum(next(v['cost_yuan'] for v in d['vehicles'] if v['vehicle_type']==groups[k][0]['vehicle_type']) for k in keys)
   vol=sum(c['quantity']*c['l_cm']*c['w_cm']*c['h_cm'] for c in sd['cargo'])
   if task=='Q1-F1' and vol>420*210*217+1e-7:continue
   if task=='Q1-F2' and vol>680*245*247+1e-7:continue
   for seed in [0,11,23]:
    for alpha in [0,.5,1]:
     for fp in [1,3]:
      cc={**cfg,'fragile_priority':fp};rr,m=solve(sd,task,'maxrect',seed,alpha,cc);v=check(rr,sd,cc,task);record={'task':task,'iteration':iteration,'vehicles':keys,'seed':seed,'alpha':alpha,'fragile_priority':fp,'N':m['N'],'C':m['C'],'runtime_seconds':m['runtime_seconds'],'passed':v['passed']};calls.append(record)
      if not v['passed']:save(E/f'local_search/{task}/invalid-{len(calls)}.json',{'call':record,'errors':v['errors']});continue
      improves=(m['N'],m['C'])<(origN,origC) if task!='Q2-C' else (m['C'],m['N'])<(origC,origN)
      if improves:
       gain=(origN-m['N'],origC-m['C']) if task!='Q2-C' else (origC-m['C'],origN-m['N'])
       if best is None or gain>best[0]:best=(gain,keys,rr,m,cc)
   if time.perf_counter()-start>600:break
  if best is None:break
  gain,keys,rr,m,cc=best
  retained=[r for r in rows if r['vehicle_id'] not in keys]
  for r in rr:r['vehicle_id']='new-'+r['vehicle_id']
  rows=canonical(retained+rr,task);full=check(rows,d,cc,task);assert full['passed'],full['errors'];new=metrics(d['cargo'],d['vehicles'],rows)
  history.append({'iteration':iteration,'replaced':keys,'gain':gain,'N':new['N'],'C':new['C'],'subsolve_metrics':m,'new_config':cc});old=new
  print(task,'local improvement',new['N'],new['C'],flush=True)
  if time.perf_counter()-start>600:break
 m=metrics(d['cargo'],d['vehicles'],rows);m.update({'runtime_seconds':time.perf_counter()-start,'method':'column multi-start + pair repacking','seed':0,'alpha_mass_preference':0,'stop_reason':'no improving examined pair or four iterations','optimality':'heuristic feasible, global unproved','bounds':bounds(d['cargo'],d['vehicles'],cfg,['T1'] if task=='Q1-F1' else ['T2'] if task=='Q1-F2' else ['T1','T2']),'unloaded_counts':{c['cargo_type']:0 for c in d['cargo']}})
 out=E/f'local_search/{task}/final';write_plan(out,rows,m,cfg,d);validate_dir(out);save(E/f'local_search/{task}/calls.json',calls);save(E/f'local_search/{task}/history.json',history);return out,m
def main():
 import shutil
 for task in ['Q1-F1','Q1-F2','Q2-N','Q2-C']:
  initial=E/f'plans/{task}/selected'
  if task=='Q1-F1':initial=E/json.loads((E/f'column_milp/{task}/best.json').read_text(encoding='utf-8'))['path']
  out,m=run(task,initial);old=json.loads((E/f'plans/{task}/selected/metrics.json').read_text(encoding='utf-8'))
  key=(m['C'],m['N']) if task=='Q2-C' else (m['N'],m['C']);oldkey=(old['C'],old['N']) if task=='Q2-C' else (old['N'],old['C'])
  if key<oldkey:shutil.copytree(out,E/f'plans/{task}/selected',dirs_exist_ok=True)
  print(task,'final',m['N'],m['C'],'calls',len(json.loads((E/f'local_search/{task}/calls.json').read_text(encoding='utf-8'))),flush=True)
if __name__=='__main__':main()
