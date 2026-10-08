"""Independent coordinate-based self-check. Does not import construction code."""
import csv,json,math,argparse,itertools
from pathlib import Path
from collections import Counter
import numpy as np
TOL=1e-7
def check(rows,data,cfg,task):
 cs={c['cargo_type']:c for c in data['cargo']};vs={v['vehicle_type']:v for v in data['vehicles']};errors=[];reports=[];ids=set();counts=Counter()
 def err(rule,vehicle,items,detail):errors.append({'rule':rule,'vehicle':vehicle,'items':items,'detail':detail})
 groups={}
 for r in rows:
  groups.setdefault(r['vehicle_id'],[]).append(r);counts[r['cargo_type']]+=1
  if r['item_id'] in ids:err('unique_id',r['vehicle_id'],[r['item_id']],'duplicate')
  ids.add(r['item_id'])
 for k,rs in groups.items():
  vt=rs[0]['vehicle_type'];v=vs[vt];n=len(rs);lo=np.array([[float(r[f'{a}_cm']) for a in 'xyz'] for r in rs]);dim=np.array([[float(r[f'd{a}_cm']) for a in 'xyz'] for r in rs]);hi=lo+dim
  masses=np.array([cs[r['cargo_type']]['weight_kg'] for r in rs]);max_pressure=0;parents=[None]*n;load=masses.copy();support_count=0
  if not np.all(np.isfinite(lo)) or not np.all(np.isfinite(dim)) or np.any(dim<=0):err('finite_positive_geometry',k,[],'nonfinite coordinate or nonpositive dimension')
  for i,r in enumerate(rs):
   c=cs[r['cargo_type']];p=r['orientation'];orig=[c['l_cm'],c['w_cm'],c['h_cm']]
   if sorted(p)!=['x','y','z'] or any(abs(dim[i,j]-orig['xyz'.index(p[j])])>TOL for j in range(3)):err('orientation_dimensions',k,[r['item_id']],'invalid axis mapping/dimensions')
   if c['category']=='directional' and p!='xyz':err('directional_orientation',k,[r['item_id']],p)
   if c['category']=='fragile' and cfg.get('fragile_upright') and p[2]!='z':err('fragile_upright',k,[r['item_id']],p)
   if np.any(lo[i]<-TOL) or hi[i,0]>v['l_cm']+TOL or hi[i,1]>v['w_cm']+TOL or hi[i,2]>v['h_cm']-cfg.get('gap',3)+TOL:err('boundary_top_gap',k,[r['item_id']],{'low':lo[i].tolist(),'high':hi[i].tolist()})
   if r['vehicle_type']!=vt:err('vehicle_type',k,[r['item_id']],'mixed identity')
   if lo[i,2]>TOL:
    touching=[j for j in range(n) if j!=i and abs(hi[j,2]-lo[i,2])<=TOL and lo[j,0]<=lo[i,0]+TOL and lo[j,1]<=lo[i,1]+TOL and hi[j,0]>=hi[i,0]-TOL and hi[j,1]>=hi[i,1]-TOL]
    if len(touching)!=1:err('single_full_support',k,[r['item_id']],touching)
    else:
     j=touching[0];parents[i]=j;support_count+=1;lower=cs[rs[j]['cargo_type']]
     if lower['category']=='fragile':err('nothing_above_fragile',k,[rs[j]['item_id'],r['item_id']],'fragile bears load')
     if c['category']=='fragile' and lower['category']!='standard':err('fragile_standard_support',k,[r['item_id'],rs[j]['item_id']],lower['category'])
     center=(lo[i,:2]+hi[i,:2])/2
     if lower['category']=='directional' and (np.any(center<lo[j,:2]-TOL) or np.any(center>hi[j,:2]+TOL)):err('directional_center',k,[r['item_id'],rs[j]['item_id']],center.tolist())
     if r['support_ids']!=rs[j]['item_id']:err('support_id_trace',k,[r['item_id']],{'computed':rs[j]['item_id'],'declared':r['support_ids']})
    if c['category']=='fragile' and cfg.get('fragile_floor'):err('fragile_floor',k,[r['item_id']],lo[i,2])
   elif r['support_ids']:err('floor_support_trace',k,[r['item_id']],r['support_ids'])
  for i in range(n):
   overlap=np.minimum(hi[i],hi[i+1:])-np.maximum(lo[i],lo[i+1:]);bad=np.where(np.all(overlap>TOL,axis=1))[0]
   for j0 in bad:err('nonoverlap',k,[rs[i]['item_id'],rs[i+1+int(j0)]['item_id']],overlap[j0].tolist())
  if masses.sum()>v['capacity_kg']+TOL:err('vehicle_mass',k,[],float(masses.sum()))
  # Descending z reconstructs subtree load, independent of declared support_ids.
  for i in np.argsort(-lo[:,2]):
   j=parents[i]
   if j is not None:
    pressure=(load[i]+(masses[j] if cfg.get('own_mass') else 0))/(dim[i,0]*dim[i,1]/10000);max_pressure=max(max_pressure,float(pressure))
    if pressure>cfg.get('pressure',500)+1e-6:err('cumulative_pressure',k,[rs[j]['item_id'],rs[i]['item_id']],{'actual_kg_m2':float(pressure),'limit':cfg.get('pressure',500),'upper_subtree_kg':float(load[i]),'contact_m2':dim[i,0]*dim[i,1]/10000})
    load[j]+=load[i]
  ground=sum(load[i] for i in range(n) if parents[i] is None and lo[i,2]<=TOL);mass=float(masses.sum())
  if abs(ground-mass)>1e-6:err('load_conservation',k,[],{'ground_kg':ground,'mass_kg':mass})
  volume=float(np.prod(dim,axis=1).sum());reports.append({'vehicle_id':k,'vehicle_type':vt,'items':n,'volume_m3':volume/1e6,'weight_kg':mass,'Uv':volume/(v['l_cm']*v['w_cm']*v['h_cm']),'Uw':mass/v['capacity_kg'],'max_pressure_kg_m2':max_pressure,'min_top_gap_cm':float(v['h_cm']-hi[:,2].max()),'support_relations':support_count,'floor_load_kg':float(ground),'pair_count':n*(n-1)//2})
 for c in data['cargo']:
  actual=counts[c['cargo_type']];q=c['quantity']
  if actual>q or (not task.startswith('Q1-S') and actual!=q):err('inventory','all',[c['cargo_type']],{'actual':actual,'required':q})
  expected={f"{c['cargo_type']}-{i:04d}" for i in range(1,actual+1)}
  if not expected.issubset(ids):err('id_inventory','all',[c['cargo_type']],'IDs not canonical unique range')
 allowed={'Q1-S1':{'T1'},'Q1-S2':{'T2'},'Q1-F1':{'T1'},'Q1-F2':{'T2'},'Q2-N':{'T1','T2'},'Q2-C':{'T1','T2'}}.get(task,{'T1','T2'})
 if any(s['vehicle_type'] not in allowed for s in reports):err('task_vehicle_types','all',[],allowed)
 if task.startswith('Q1-S') and len(groups)!=1:err('single_vehicle','all',[],len(groups))
 cv=sum(vs[s['vehicle_type']]['l_cm']*vs[s['vehicle_type']]['w_cm']*vs[s['vehicle_type']]['h_cm']/1e6 for s in reports);cw=sum(vs[s['vehicle_type']]['capacity_kg'] for s in reports)
 return {'checker_version':'coordinate-chain-v1','role':'producer self-check; not independent acceptance','passed':not errors,'tolerance_cm':TOL,'checks':['unique ID','inventory','orientation','boundary and 3cm','all pairs overlap','full single support','fragile conditions','directional center','cumulative contact pressure','mass capacity','ground mass conservation','support trace','objective recomputation'],'errors':errors,'counts':dict(counts),'N':len(reports),'n1':sum(s['vehicle_type']=='T1' for s in reports),'n2':sum(s['vehicle_type']=='T2' for s in reports),'C':sum(vs[s['vehicle_type']]['cost_yuan'] for s in reports),'Uv':sum(s['volume_m3'] for s in reports)/cv if cv else 0,'Uw':sum(s['weight_kg'] for s in reports)/cw if cw else 0,'vehicles':reports}
def validate_dir(path):
 path=Path(path);cfg=json.loads((path/'config.json').read_text(encoding='utf-8'));data=cfg['instance'];rows=list(csv.DictReader((path/'placements.csv').open(encoding='utf-8-sig')));r=check(rows,data,cfg,rows[0]['task_id']);m=json.loads((path/'metrics.json').read_text(encoding='utf-8'))
 for k in ['N','n1','n2','C','Uv','Uw']:
  if abs(r[k]-m[k])>1e-7:r['errors'].append({'rule':'metrics_trace','field':k,'computed':r[k],'declared':m[k]});r['passed']=False
 (path/'validation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2,default=lambda y:y.item() if isinstance(y,np.generic) else list(y) if isinstance(y,set) else str(y)),encoding='utf-8');return r
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('path');a=ap.parse_args();r=validate_dir(a.path);print(json.dumps({k:v for k,v in r.items() if k!='vehicles'},ensure_ascii=False));raise SystemExit(0 if r['passed'] else 2)
