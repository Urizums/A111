"""Recompute all six formal plans in a clean supplied output directory."""
import argparse,json,time,hashlib,math,numpy as np
from pathlib import Path
from scipy.optimize import milp,Bounds,LinearConstraint
from solver import E,instance,solve,write_plan,save,catalogue,expand,metrics,bounds
from column_milp import pack_columns
from checker import validate_dir
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=Path(a.out).resolve()
 if out.exists():raise ValueError('replay output must be new; preserve earlier receipt')
 out.mkdir(parents=True);data=instance();receipts=[];start=time.perf_counter()
 for task in ['Q1-S1','Q1-S2','Q1-F1','Q1-F2','Q2-N','Q2-C']:
  selected=E/f'plans/{task}/selected';old=json.loads((selected/'metrics.json').read_text(encoding='utf-8'));cfg=json.loads((selected/'config.json').read_text(encoding='utf-8'));t=time.perf_counter()
  if task=='Q1-F1':
   v=data['vehicles'][0];cat=catalogue(data['cargo'],v,cfg);A=np.array([c['counts'] for c in cat],dtype=float).T;q=np.array([c['quantity'] for c in data['cargo']]);areas=np.array([c['dx']*c['dy'] for c in cat],float)
   res=milp(areas,integrality=np.ones(len(cat)),bounds=Bounds(0,np.inf),constraints=LinearConstraint(A,q,q),options={'time_limit':30,'mip_rel_gap':0});assert res.x is not None;x=np.rint(res.x).astype(int);assert np.all(A@x==q);cols=[c for c,n in zip(cat,x) for _ in range(n)];loads=pack_columns(data['cargo'],v,cols,0,0);rows=expand(data['cargo'],loads,task);m=metrics(data['cargo'],data['vehicles'],rows);m.update({'runtime_seconds':time.perf_counter()-t,'method':'minimum-area-column-MILP + 2D best-fit (recomputed)','seed':0,'alpha_mass_preference':0,'stop_reason':'fresh MILP/packing complete','optimality':'global unproved; library area solver status '+str(res.status),'bounds':bounds(data['cargo'],data['vehicles'],cfg,['T1']),'unloaded_counts':{c['cargo_type']:0 for c in data['cargo']},'restricted_min_area_m2':float(res.fun/10000)})
  else:rows,m=solve(data,task,cfg['method'],cfg['seed'],cfg['alpha'],cfg)
  dest=out/task;write_plan(dest,rows,m,cfg,data);vr=validate_dir(dest);assert vr['passed'],vr['errors']
  fields=['N','n1','n2','C','Uv','Uw','volume_m3','weight_kg'];deltas={k:m[k]-old[k] for k in fields};match=all(abs(x)<1e-7 for x in deltas.values()) and m['loaded_counts']==old['loaded_counts'];assert match,deltas
  h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();receipts.append({'task':task,'status':'complete','coordinate_self_check_passed':vr['passed'],'metric_deltas':deltas,'inventory_equal':m['loaded_counts']==old['loaded_counts'],'coordinate_bytes_equal':h(dest/'placements.csv')==h(selected/'placements.csv'),'placements_sha256':h(dest/'placements.csv'),'seconds':time.perf_counter()-t});print(task,'fresh replay',m['N'],m['C'],flush=True)
 save(out/'receipt.json',{'status':'six tasks freshly recomputed','not_using_preloaded_placements':True,'seconds':time.perf_counter()-start,'receipts':receipts,'code_binding':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [E/'src/solver.py',E/'src/checker.py',E/'src/column_milp.py',E/'src/reproduce.py']},'selected_config_binding':{t:hashlib.sha256((E/f'plans/{t}/selected/config.json').read_bytes()).hexdigest() for t in ['Q1-S1','Q1-S2','Q1-F1','Q1-F2','Q2-N','Q2-C']},'input_sha256':hashlib.sha256((E/'data/instance.json').read_bytes()).hexdigest(),'unknown_model':None,'unknown_token':None,'unknown_cost':None})
if __name__=='__main__':main()
