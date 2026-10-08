"""Research improvement: exact-demand minimum-area column library + 2D best-fit."""
import numpy as np,time,random,math,copy,json
from scipy.optimize import milp,Bounds,LinearConstraint
from solver import E,instance,catalogue,split_rects,expand,metrics,bounds,write_plan,save
from checker import validate_dir
def planar_swap(col,cargo):
 if any(cargo[a]['category']=='directional' for a,_,_ in col['stack']):return None
 c=copy.deepcopy(col);c['dx'],c['dy']=c['dy'],c['dx'];c['stack']=[(a,(d[1],d[0],d[2]),o[1]+o[0]+o[2]) for a,d,o in c['stack']];return c
def pack_columns(cargo,v,columns,seed,sortmode):
 rng=random.Random(seed)
 cols=list(columns)
 if sortmode==0:cols.sort(key=lambda c:(max(c['dx'],c['dy']),c['dx']*c['dy']),reverse=True)
 elif sortmode==1:cols.sort(key=lambda c:(c['dx']*c['dy'],max(c['dx'],c['dy'])),reverse=True)
 elif sortmode==2:cols.sort(key=lambda c:(c['dy'],c['dx']),reverse=True)
 else:cols.sort(key=lambda c:c['dx']*c['dy']*rng.uniform(.6,1.4),reverse=True)
 trucks=[];rectlists=[];weights=[]
 for col in cols:
  options=[col];sw=planar_swap(col,cargo)
  if sw:options.append(sw)
  best=None
  for k,rects in enumerate(rectlists):
   for r in rects:
    x,y,w,h=r
    for c in options:
     if c['dx']<=w and c['dy']<=h and weights[k]+c['weight']<=v['capacity_kg']+1e-8:
      key=(min(w-c['dx'],h-c['dy']),max(w-c['dx'],h-c['dy']),k,y,x)
      if best is None or key<best[0]:best=(key,k,x,y,c)
  if best is None:
   candidates=[c for c in options if c['dx']<=v['l_cm'] and c['dy']<=v['w_cm'] and c['weight']<=v['capacity_kg']]
   if not candidates:raise ValueError('column cannot fit a vehicle')
   c=min(candidates,key=lambda c:(v['w_cm']-c['dy'],v['l_cm']-c['dx']));k=len(trucks);trucks.append([]);rectlists.append([(0,0,v['l_cm'],v['w_cm'])]);weights.append(0);x=y=0
  else:_,k,x,y,c=best
  trucks[k].append((x,y,c));weights[k]+=c['weight'];rectlists[k]=split_rects(rectlists[k],(x,y,c['dx'],c['dy']))
 return [(v,t) for t in trucks]
def main():
 data=instance();cargo=data['cargo'];cfg={'gap':3,'pressure':500,'run_seconds':120,'milp_seconds':30,'memory_target_MB':1800,'phase_window_seconds':600};results=[]
 for v in data['vehicles']:
  start=time.perf_counter();cat=catalogue(cargo,v,cfg);A=np.array([c['counts'] for c in cat]).T.astype(float);q=np.array([c['quantity'] for c in cargo]);cost=np.array([c['dx']*c['dy'] for c in cat],dtype=float)
  res=milp(cost,integrality=np.ones(len(cat)),bounds=Bounds(0,np.inf),constraints=LinearConstraint(A,q,q),options={'time_limit':30,'mip_rel_gap':0})
  save(E/f'column_milp/{v["vehicle_type"]}/solver_receipt.json',{'status':res.status,'message':res.message,'objective_cm2':res.fun,'mip_gap':getattr(res,'mip_gap',None),'mip_dual_bound':getattr(res,'mip_dual_bound',None),'mip_node_count':getattr(res,'mip_node_count',None),'seconds':time.perf_counter()-start,'optimality_scope':'minimum floor area in this restricted column library, not original 3D problem','time_limit_seconds':30})
  if res.x is None:continue
  x=np.rint(res.x).astype(int);assert np.all(A@x==q);columns=[c for c,n in zip(cat,x) for _ in range(n)]
  save(E/f'column_milp/{v["vehicle_type"]}/selected_columns.json',[{'index':i,'multiplicity':int(n),'counts':c['counts'],'dx':c['dx'],'dy':c['dy'],'height':c['height'],'stack':c['stack']} for i,(c,n) in enumerate(zip(cat,x)) if n])
  task='Q1-F1' if v['vehicle_type']=='T1' else 'Q1-F2';best=None
  for seed in [0,11,23,37,51,79]:
   for mode in [0,1,2,3]:
    t=time.perf_counter();loads=pack_columns(cargo,v,columns,seed,mode);rows=expand(cargo,loads,task);m=metrics(cargo,data['vehicles'],rows);m.update({'runtime_seconds':time.perf_counter()-t,'method':'minimum-area-column-MILP + 2D best-fit','seed':seed,'sortmode':mode,'alpha_mass_preference':0,'stop_reason':'all library columns packed','optimality':'original global unproved; restricted column area MILP status '+str(res.status),'bounds':bounds(cargo,data['vehicles'],cfg,[v['vehicle_type']]),'unloaded_counts':{c['cargo_type']:0 for c in cargo},'restricted_min_area_m2':float(res.fun/10000)})
    out=E/f'column_milp/{task}/s{seed}-m{mode}';write_plan(out,rows,m,cfg,data);vr=validate_dir(out);assert vr['passed'],vr['errors'];results.append({'task':task,'seed':seed,'sortmode':mode,'N':m['N'],'C':m['C'],'Uv':m['Uv'],'Uw':m['Uw'],'runtime_seconds':m['runtime_seconds'],'path':str(out.relative_to(E)),'passed':True})
    if best is None or (m['N'],m['C'])<best[0]:best=((m['N'],m['C']),out)
  save(E/f'column_milp/{task}/best.json',{'path':str(best[1].relative_to(E)),'N':best[0][0]});print(task,'minimum library area m2',res.fun/10000,'bestN',best[0][0],flush=True)
 save(E/'column_milp/comparison.json',results)
if __name__=='__main__':main()
