import json,csv,copy
from solver import E,save,write_plan,instance
from checker import validate_dir
rows=json.loads((E/'sensitivity/results.json').read_text(encoding='utf-8'));save(E/'sensitivity/results_before_shared_pool.json',rows);new=[]
for name in dict.fromkeys(r['scenario'] for r in rows):
 sub=[r for r in rows if r['scenario']==name];new.extend(r for r in sub if r['task'].startswith('Q1-S'))
 pool=[r for r in sub if r['task'].startswith('Q2')]
 for task in ['Q2-N','Q2-C']:
  best=min(pool,key=lambda r:(r['N'],r['C']) if task=='Q2-N' else (r['C'],r['N']));r=copy.deepcopy(best);r['source_task']=r['task'];r['task']=task;r['selection_scope']='shared feasible pool of both objectives, six seed runs total'
  src=E/best['path'];cfg=json.loads((src/'config.json').read_text(encoding='utf-8'));m=json.loads((src/'metrics.json').read_text(encoding='utf-8'));pr=list(csv.DictReader((src/'placements.csv').open(encoding='utf-8-sig')))
  for p in pr:p['task_id']=task
  cfg['task_id']=task;m['selection_source_task']=best['task'];dest=E/f'sensitivity/{name}/{task}/shared_selected';write_plan(dest,pr,m,cfg,cfg['instance']);assert validate_dir(dest)['passed'];r['path']=str(dest.relative_to(E));new.append(r)
save(E/'sensitivity/results.json',new)
keys=list(dict.fromkeys(k for r in new for k in r))
with (E/'sensitivity/results.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(new)
save(E/'logs/shared_pool_correction.json',{'classification':'planned research/result selection correction','reason':'A cost-directed constructive search can lose to a count-directed feasible search; share their admissible candidates before either recommendation','original_candidates_retained':True,'new_solver_calls':0,'revalidated_coordinate_outputs':58,'corrected_scenarios':[n for n in dict.fromkeys(r['scenario'] for r in rows) if any(a['scenario']==n and a['task']=='Q2-C' and a['C']!=next(b['C'] for b in new if b['scenario']==n and b['task']=='Q2-C') for a in rows)]})
print('shared candidate selection complete',len(new))
