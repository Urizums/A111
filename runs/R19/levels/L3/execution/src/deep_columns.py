"""Targeted third-type nested stacks to address remaining restricted column gap."""
import math,time,json,copy,numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from solver import E,instance,catalogue,orientations,expand,metrics,bounds,save,write_plan
from column_milp import pack_columns
from checker import validate_dir
def key(c):return (c['dx'],c['dy'],c['height'],c['counts'],c['stack'][-1][1])
def deepen(cargo,v,cfg):
 cat=catalogue(cargo,v,cfg);found={key(c):c for c in cat};front=cat;iterations=[]
 for depth in range(4):
  new=[]
  for col in front:
   a,d,o=col['stack'][-1]
   if cargo[a]['category']=='fragile':continue
   for b,t in enumerate(cargo):
    if t['category']=='fragile' and cargo[a]['category']!='standard':continue
    for dt,ot in orientations(t):
     if dt[0]>d[0] or dt[1]>d[1] or col['height']+dt[2]>v['h_cm']-3:continue
     stack=col['stack']+[(b,dt,ot)];load=0;legal=True
     for j in range(len(stack)-1,0,-1):
      load+=cargo[stack[j][0]]['weight_kg'];area=stack[j][1][0]*stack[j][1][1]/10000
      if load/area>500+1e-8:legal=False;break
     if not legal:continue
     cc=copy.copy(col);cc['stack']=stack;counts=list(col['counts']);counts[b]+=1;cc['counts']=tuple(counts);cc['height']+=dt[2];cc['volume']+=math.prod(dt);cc['weight']+=t['weight_kg'];k=key(cc)
     if k in found:continue
     found[k]=cc;new.append(cc)
     if len(found)>=30000:break
    if len(found)>=30000:break
   if len(found)>=30000:break
  iterations.append({'round':depth,'new_patterns':len(new),'total':len(found)});front=new
  if not new or len(found)>=30000:break
 return list(found.values()),iterations
def main():
 data=instance();cargo=data['cargo'];cfg={'gap':3,'pressure':500,'milp_seconds':60,'phase_window_seconds':600,'memory_target_MB':1800,'state_cap':30000};summary=[]
 for v in data['vehicles']:
  start=time.perf_counter();cat,its=deepen(cargo,v,cfg);A=np.array([c['counts'] for c in cat],dtype=float).T;q=np.array([c['quantity'] for c in cargo]);areas=np.array([c['dx']*c['dy'] for c in cat],float)
  res=milp(areas,integrality=np.ones(len(cat)),bounds=Bounds(0,np.inf),constraints=LinearConstraint(A,q,q),options={'time_limit':60,'mip_rel_gap':0})
  save(E/f'deep_columns/{v["vehicle_type"]}/receipt.json',{'library_size':len(cat),'expansion':its,'status':res.status,'message':res.message,'objective_cm2':res.fun,'gap':getattr(res,'mip_gap',None),'dual_bound':getattr(res,'mip_dual_bound',None),'seconds':time.perf_counter()-start,'scope':'restricted expanded library; no global 3D optimality'})
  if res.x is None:continue
  x=np.rint(res.x).astype(int);assert np.all(A@x==q);cols=[c for c,n in zip(cat,x) for _ in range(n)];save(E/f'deep_columns/{v["vehicle_type"]}/columns.json',[{'multiplicity':int(n),**c} for n,c in zip(x,cat) if n]);task='Q1-F1' if v['vehicle_type']=='T1' else 'Q1-F2';best=None
  for seed in [0,11,23,37,51,79,97,113]:
   for mode in [0,1,2,3]:
    t=time.perf_counter();loads=pack_columns(cargo,v,cols,seed,mode);rows=expand(cargo,loads,task);m=metrics(cargo,data['vehicles'],rows);m.update({'runtime_seconds':time.perf_counter()-t,'method':'expanded nested-stack minimum-area MILP + best-fit','seed':seed,'sortmode':mode,'alpha_mass_preference':0,'stop_reason':'expanded library packed','optimality':'global original unproved; library MILP status'+str(res.status),'bounds':bounds(cargo,data['vehicles'],cfg,[v['vehicle_type']]),'unloaded_counts':{c['cargo_type']:0 for c in cargo}});out=E/f'deep_columns/{task}/s{seed}-m{mode}';write_plan(out,rows,m,cfg,data);vr=validate_dir(out);assert vr['passed'],vr['errors'];summary.append({'task':task,'seed':seed,'sortmode':mode,'N':m['N'],'C':m['C'],'runtime_seconds':m['runtime_seconds'],'path':str(out.relative_to(E)),'passed':True})
    if best is None or (m['N'],m['C'])<best[0]:best=((m['N'],m['C']),out)
  save(E/f'deep_columns/{task}/best.json',{'path':str(best[1].relative_to(E)),'N':best[0][0]});print(task,'area',res.fun/10000,'best',best[0],flush=True)
 save(E/'deep_columns/comparison.json',summary)
if __name__=='__main__':main()
