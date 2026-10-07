"""Independent geometry/load checker; does not import the constructor."""
import csv,json,argparse,math,itertools
from pathlib import Path
def validate(rows,items,vehicles,full=True,pressure=500,fragile_fixed=False):
 errs=[];source={r['item_id']:r for r in items};vs={v['type_id']:v for v in vehicles};ids=[r['item_id'] for r in rows];summary=[];supports=[];eps=1e-7
 if len(ids)!=len(set(ids)):errs.append('duplicate item_id')
 if any(i not in source for i in ids):errs.append('unknown item_id')
 if full and set(ids)!=set(source):errs.append('inventory omission or extra')
 parsed=[]
 for raw in rows:
  r=dict(raw)
  try:
   for k in ['x_mm','y_mm','z_mm','dx_mm','dy_mm','dz_mm']:r[k]=float(r[k]);assert math.isfinite(r[k])
   s=source[r['item_id']];r['weight']=float(s['weight_kg']);assert r['weight']>0;r['category']=s['category'];r['cargo_type']=s['cargo_type'];assert r['vehicle_type'] in vs
   ds=[float(s['canonical_'+k+'_mm']) for k in ['l','w','h']];ori=tuple(int(x) for x in r['orientation_id']);allowed=[(0,1,2)] if s['category']=='定向件' or fragile_fixed and s['category']=='易碎件' else [(0,1,2),(1,0,2)] if s['category']=='易碎件' else list(itertools.permutations(range(3)))
   if ori not in allowed or [r[k] for k in ['dx_mm','dy_mm','dz_mm']]!=[ds[i] for i in ori]:errs.append(r['item_id']+': orientation')
   v=vs[r['vehicle_type']]
   if any(r[k]<-eps for k in ['x_mm','y_mm','z_mm']) or r['x_mm']+r['dx_mm']>v['dims'][0]+eps or r['y_mm']+r['dy_mm']>v['dims'][1]+eps or r['z_mm']+r['dz_mm']>v['dims'][2]-v['clearance_mm']+eps:errs.append(r['item_id']+': boundary/clearance')
   parsed.append(r)
  except (ValueError,KeyError,AssertionError,TypeError):errs.append(str(raw.get('item_id'))+': invalid or missing input')
 def contact(a,b):
  ox=max(0,min(a['x_mm']+a['dx_mm'],b['x_mm']+b['dx_mm'])-max(a['x_mm'],b['x_mm']));oy=max(0,min(a['y_mm']+a['dy_mm'],b['y_mm']+b['dy_mm'])-max(a['y_mm'],b['y_mm']));return ox*oy
 for vid in dict.fromkeys(r['vehicle_id'] for r in parsed):
  rr=[r for r in parsed if r['vehicle_id']==vid];v=vs[rr[0]['vehicle_type']];n=len(rr);graph=[[] for _ in rr];loads=[r['weight'] for r in rr];incoming=[0.]*n
  if any(r['vehicle_type']!=rr[0]['vehicle_type'] for r in rr):errs.append(vid+': vehicle type inconsistent')
  for i in range(n):
   a=rr[i]
   for j in range(i):
    b=rr[j]
    if all(min(a[k]+a[d],b[k]+b[d])-max(a[k],b[k])>eps for k,d in [('x_mm','dx_mm'),('y_mm','dy_mm'),('z_mm','dz_mm')]):errs.append(a['item_id']+': overlap '+b['item_id'])
   if a['z_mm']>eps:
    for j,b in enumerate(rr):
     ar=contact(a,b)
     if i!=j and abs(b['z_mm']+b['dz_mm']-a['z_mm'])<eps and ar>eps:graph[i].append((j,ar))
    area=sum(ar for _,ar in graph[i])
    if abs(area-a['dx_mm']*a['dy_mm'])>eps:errs.append(a['item_id']+': incomplete support')
    for j,ar in graph[i]:
     b=rr[j]
     if b['category']=='易碎件':errs.append(a['item_id']+': cargo on fragile')
     if a['category']=='易碎件' and b['category']!='标准件':errs.append(a['item_id']+': fragile support not standard')
     if b['category']=='定向件' and not (b['x_mm']-eps<=a['x_mm']+a['dx_mm']/2<=b['x_mm']+b['dx_mm']+eps and b['y_mm']-eps<=a['y_mm']+a['dy_mm']/2<=b['y_mm']+b['dy_mm']+eps):errs.append(a['item_id']+': local center of gravity')
  for i in sorted(range(n),key=lambda i:rr[i]['z_mm'],reverse=True):
   area=sum(ar for _,ar in graph[i])
   for j,ar in graph[i]:
    carried=loads[i]*ar/area;loads[j]+=carried;incoming[j]+=carried;pr=carried/(ar/1e6)
    supports.append({'vehicle_id':vid,'upper':rr[i]['item_id'],'lower':rr[j]['item_id'],'contact_mm2':ar,'transferred_kg':carried,'pressure_kg_m2':pr})
    if pr>pressure+eps:errs.append(rr[j]['item_id']+': cumulative contact pressure')
  for i,r in enumerate(rr):
   if incoming[i]/(r['dx_mm']*r['dy_mm']/1e6)>pressure+eps:errs.append(r['item_id']+': average top pressure')
  mass=sum(r['weight'] for r in rr);vol=sum(r['dx_mm']*r['dy_mm']*r['dz_mm'] for r in rr)
  if mass>v['payload_kg']+eps:errs.append(vid+': payload')
  floorload=sum(loads[i] for i,r in enumerate(rr) if abs(r['z_mm'])<eps)
  if abs(floorload-mass)>eps:errs.append(vid+': load conservation')
  summary.append({'vehicle_id':vid,'vehicle_type':v['type_id'],'item_count':n,**{t:sum(r['cargo_type']==t for r in rr) for t in sorted(set(s['cargo_type'] for s in items))},'weight_kg':mass,'volume_mm3':vol,'volume_utilization':vol/math.prod(v['dims']),'weight_utilization':mass/v['payload_kg'],'cost_yuan':v['cost_yuan_per_trip'],'floor_load_kg':floorload})
 return {'valid':not errs,'errors':errs,'checked_items':len(parsed),'vehicles':summary,'supports':supports,'claim':'author executed separate implementation, not independent agent acceptance'}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--placements',type=Path,required=True);a.add_argument('--items',type=Path,required=True);a.add_argument('--vehicles',type=Path,required=True);a.add_argument('--partial',action='store_true');a.add_argument('--pressure',type=float,default=500);a.add_argument('--output',type=Path,required=True);q=a.parse_args()
 def read(p):
  with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
 z=validate(read(q.placements),read(q.items),json.loads(q.vehicles.read_text(encoding='utf8')),not q.partial,q.pressure);q.output.parent.mkdir(parents=True,exist_ok=True);q.output.write_text(json.dumps(z,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:z[k] for k in ['valid','checked_items','errors']},ensure_ascii=False));raise SystemExit(0 if z['valid'] else 2)
