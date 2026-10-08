import subprocess,sys,json,time,copy,math,itertools,csv
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from independent_review import H,E,BASE,review,catalogue
import independent_checker as ic
SRC=H/'sandbox/src';sys.path.insert(0,str(SRC))
import solver,deep_columns
def save(name,x):(H/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 start=time.perf_counter();d=json.loads((H/'sandbox/data/instance.json').read_text(encoding='utf-8'));out=H/'boundary';out.mkdir();calls=[]
 def cli(name,data,expected,task='Q1-F1'):
  p=out/name;p.mkdir();(p/'input.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
  cmd=[sys.executable,'-X','utf8','-B',str(SRC/'solver.py'),'--task',task,'--input',str(p/'input.json'),'--out',str(p/'plan')]
  t=time.perf_counter();child=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8');stdout,stderr=child.communicate(timeout=60)
  rec={'name':name,'argv':cmd,'pid':child.pid,'returncode':child.returncode,'expected':expected,'stdout':stdout,'stderr':stderr,'seconds':time.perf_counter()-t,'terminal':child.poll() is not None}
  calls.append(rec);save('cli-receipts.json',calls);assert child.returncode==expected
  if expected==0:
   val=review(p/'plan',task,scenario=True);assert val['independent_pass_under_declared_model'];save(f'boundary/{name}/independent.json',val)
  return p
 small=copy.deepcopy(d)
 for c in small['cargo']:c['quantity']=12 if c['cargo_type']=='G1' else 0
 cli('generic_new_quantity',small,0)
 invalid=copy.deepcopy(small);invalid['cargo'][0]['l_cm']=-60;cli('negative_dimension',invalid,2)
 oversized=copy.deepcopy(small);oversized['cargo'][0].update(l_cm=10000,w_cm=10000,h_cm=10000,quantity=1);cli('no_fitting_column',oversized,2)
 tiny=copy.deepcopy(small);tiny['cargo'][0]['quantity']=4;tiny['vehicles'][0].update(l_cm=60,w_cm=40,h_cm=63);p=cli('tiny_volume_oracle',tiny,0,task='Q1-S1')
 count=sum(1 for _ in csv.DictReader((p/'plan/placements.csv').open(encoding='utf-8-sig')));assert count==2
 tiny_proof={'effective_volume_cm3':60*40*(63-3),'raw_G1_volume_cm3':math.prod(BASE[0]['G1']['dims']),'volume_upper_count':2,'actual_count':count,'scope':'artificial homogeneous tiny instance only'}
 libs=[];cfg={'gap':3,'pressure':500}
 for vehicle in d['vehicles']:
  for name in ['initial','expanded']:
   t=time.perf_counter();cat=solver.catalogue(d['cargo'],vehicle,cfg) if name=='initial' else deep_columns.deepen(d['cargo'],vehicle,cfg)[0]
   # Independent static inspection of every admitted column, not author's validator.
   catalogues=catalogue(d);ic.source_catalog=lambda:catalogues
   for j,col in enumerate(cat):
    records=[];z=0
    for i,(typ,dims,o) in enumerate(col['stack']):
     records.append(dict(item_id=str(i),cargo_type=d['cargo'][typ]['cargo_type'],vehicle_id='column',vehicle_type=vehicle['vehicle_type'],x=0,y=0,z=z,dx=dims[0],dy=dims[1],dz=dims[2]));z+=dims[2]
    result=ic.check(records,fragile_support='single');assert result['valid_under_declared_model'],(name,j,result['violations'])
   A=np.array([c['counts'] for c in cat],dtype=float).T;q=np.array([c['quantity'] for c in d['cargo']]);area=np.array([c['dx']*c['dy'] for c in cat],float)
   res=milp(area,integrality=np.ones(len(cat)),bounds=Bounds(0,np.inf),constraints=LinearConstraint(A,q,q),options={'time_limit':60,'mip_rel_gap':0})
   assert res.status==0 and res.x is not None;counts=np.rint(res.x).astype(int);assert np.all(A@counts==q)
   libs.append({'vehicle':vehicle['vehicle_type'],'library':name,'patterns_independently_feasible':len(cat),'status':int(res.status),'area_cm2':res.fun,'dual_bound_cm2':float(res.mip_dual_bound),'mip_gap':res.mip_gap,'restricted_floor_area_vehicle_lower_bound':math.ceil(res.fun/(vehicle['l_cm']*vehicle['w_cm'])),'seconds':time.perf_counter()-t,'limit_seconds':60,'scope':'restricted library area only, not original continuous 3D minimum'})
 save('cli-and-restricted-model.json',{'declared_window_seconds':900,'cli_calls':calls,'tiny_proof':tiny_proof,'libraries':libs,'pending_calls':[],'seconds':time.perf_counter()-start,'failure_semantics':'No legal column is constructive failure, not a general infeasibility certificate','model':None,'token':None,'cost':None});print(json.dumps({'cli_calls':len(calls),'tiny':tiny_proof,'libraries':libs,'seconds':time.perf_counter()-start},ensure_ascii=False))
if __name__=='__main__':main()
