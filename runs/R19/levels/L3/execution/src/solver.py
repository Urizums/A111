"""Offline rectangular column packing; no precomputed solution read by solver."""
import csv,json,math,time,itertools,random,copy,argparse,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
E=Path(__file__).resolve().parents[1]
def jsonsafe(x):
 if isinstance(x,np.generic):return jsonsafe(x.item())
 if isinstance(x,float) and not math.isfinite(x):return str(x)
 if isinstance(x,dict):return {str(k):jsonsafe(v) for k,v in x.items()}
 if isinstance(x,(list,tuple,set)):return [jsonsafe(v) for v in x]
 return x
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(jsonsafe(x),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def instance(p=None):
 data=json.loads(Path(p or E/'data/instance.json').read_text(encoding='utf-8'));validate_instance(data);return data
def validate_instance(data):
 for name,idkey,numeric in [('cargo','cargo_type',['l_cm','w_cm','h_cm','weight_kg']),('vehicles','vehicle_type',['l_cm','w_cm','h_cm','capacity_kg','cost_yuan'])]:
  if not data.get(name):raise ValueError(name+' must contain records')
  seen=set()
  for r in data[name]:
   if r[idkey] in seen:raise ValueError('duplicate '+idkey)
   seen.add(r[idkey])
   for k in numeric:
    if not isinstance(r[k],(int,float)) or not math.isfinite(r[k]) or r[k]<=0:raise ValueError('positive finite '+k+' required')
   if name=='cargo':
    if r['category'] not in ['standard','fragile','directional']:raise ValueError('unsupported cargo category')
    if not isinstance(r['quantity'],int) or r['quantity']<0:raise ValueError('nonnegative integer quantity required')
 if sum(c['quantity'] for c in data['cargo'])==0:raise ValueError('at least one cargo item required')
def orientations(c,fragile_upright=False):
 d=(c['l_cm'],c['w_cm'],c['h_cm']);ps=[(0,1,2)] if c['category']=='directional' else sorted(set(itertools.permutations(range(3))))
 if c['category']=='fragile' and fragile_upright:ps=[p for p in ps if p[2]==2]
 seen=set();out=[]
 for p in ps:
  ds=tuple(d[k] for k in p)
  if ds not in seen:seen.add(ds);out.append((ds,''.join('xyz'[k] for k in p)))
 return out
def catalogue(cargo,v,cfg):
 """One-type stack, or base stack plus one other-type stack. Every footprint nested."""
 H=v['h_cm']-cfg.get('gap',3);pressure=cfg.get('pressure',500);out=[];seen=set()
 for a,c in enumerate(cargo):
  for d,o in orientations(c,cfg.get('fragile_upright',False)):
   if d[0]>v['l_cm'] or d[1]>v['w_cm']:continue
   for n in range(1,int(H//d[2])+1):
    if c['category']=='fragile' and n>1:continue
    if (n-1+(1 if cfg.get('own_mass',False) else 0))*c['weight_kg']/(d[0]*d[1]/10000)>pressure+1e-8:continue
    base=[(a,d,o)]*n
    def emit(stack):
     key=tuple((x[0],x[1]) for x in stack)
     if key in seen:return
     seen.add(key);counts=tuple(sum(x[0]==i for x in stack) for i in range(len(cargo)))
     out.append({'stack':stack,'counts':counts,'dx':d[0],'dy':d[1],'height':sum(x[1][2] for x in stack),'volume':sum(math.prod(x[1]) for x in stack),'weight':sum(cargo[x[0]]['weight_kg'] for x in stack)})
    emit(base)
    if c['category']=='fragile':continue
    for b,t in enumerate(cargo):
     if b==a:continue
     if t['category']=='fragile' and (c['category']!='standard' or cfg.get('fragile_floor',False)):continue
     for dt,ot in orientations(t,cfg.get('fragile_upright',False)):
      if dt[0]>d[0] or dt[1]>d[1]:continue
      for nt in range(1,int((H-n*d[2])//dt[2])+1):
       if t['category']=='fragile' and nt>1:continue
       upper=nt*t['weight_kg'];own=cfg.get('own_mass',False)
       # At base/top interface pressure over actual topper footprint, bottom base over its own.
       if (upper+(c['weight_kg'] if own else 0))/(dt[0]*dt[1]/10000)>pressure+1e-8:continue
       if ((n-1)*c['weight_kg']+upper+(c['weight_kg'] if own else 0))/(d[0]*d[1]/10000)>pressure+1e-8:continue
       if (nt-1+(1 if own else 0))*t['weight_kg']/(dt[0]*dt[1]/10000)>pressure+1e-8:continue
       emit(base+[(b,dt,ot)]*nt)
 return out
def split_rects(rects,box):
 x,y,w,h=box;new=[]
 for rx,ry,rw,rh in rects:
  if x>=rx+rw or x+w<=rx or y>=ry+rh or y+h<=ry:new.append((rx,ry,rw,rh));continue
  if x>rx:new.append((rx,ry,x-rx,rh))
  if x+w<rx+rw:new.append((x+w,ry,rx+rw-x-w,rh))
  if y>ry:new.append((rx,ry,rw,y-ry))
  if y+h<ry+rh:new.append((rx,y+h,rw,ry+rh-y-h))
 uniq=list(dict.fromkeys(new));return [r for i,r in enumerate(uniq) if not any(i!=j and r[0]>=s[0] and r[1]>=s[1] and r[0]+r[2]<=s[0]+s[2] and r[1]+r[3]<=s[1]+s[3] for j,s in enumerate(uniq))]
def pack_vehicle(cargo,v,remaining,cat,method,alpha,seed,cfg):
 rem=list(remaining);mass=0;placed=[];rects=[(0,0,v['l_cm'],v['w_cm'])];rng=random.Random(seed)
 counts=np.array([c['counts'] for c in cat]);dx=np.array([c['dx'] for c in cat]);dy=np.array([c['dy'] for c in cat]);cw=np.array([c['weight'] for c in cat]);cv=np.array([c['volume'] for c in cat]);area=dx*dy
 totalV=sum(c['l_cm']*c['w_cm']*c['h_cm']*r for c,r in zip(cargo,remaining));totalW=sum(c['weight_kg']*r for c,r in zip(cargo,remaining))
 scarcity=np.array([cfg.get('fragile_priority',1.7) if c['category']=='fragile' else 1 for c in cargo]);noise=np.array([rng.uniform(.94,1.06) for _ in cat]) if seed else np.ones(len(cat))
 while rects:
  feasible=np.all(counts<=np.array(rem),axis=1)&(cw+mass<=v['capacity_kg']+1e-8)
  if method!='baseline' and cfg.get('reserve_support',True) and len(cargo)==5 and cargo[0]['cargo_type']=='G1' and cargo[2]['cargo_type']=='G3' and rem[2]>0 and not cfg.get('fragile_upright') and not cfg.get('fragile_floor'):
   reserve=min(2,rem[0]//rem[2]);feasible &= (rem[0]-counts[:,0]>=reserve*(rem[2]-counts[:,2]))
  if not feasible.any():break
  best=None
  for ri,(x,y,w,h) in enumerate(rects):
   inds=np.where(feasible&(dx<=w)&(dy<=h))[0]
   if len(inds)==0:continue
   if method=='baseline':
    # Descending base footprint, then stack height; simple guillotine rectangles.
    score=area[inds]+cv[inds]/1e8
   else:
    benefit=(1-alpha)*cv[inds]/max(totalV,1)+alpha*cw[inds]/max(totalW,1)
    urgency=(counts[inds]*scarcity).sum(axis=1)/np.maximum(counts[inds].sum(axis=1),1)
    fit=(1+.25*np.maximum(dx[inds]/w,dy[inds]/h)+.15*((dx[inds]==w)|(dy[inds]==h)))
    score=benefit/area[inds]*urgency*fit*noise[inds]
   ci=int(inds[np.argmax(score)]);key=(float(score.max()),-y,-x,-ri)
   if best is None or key>best[0]:best=(key,ri,ci)
  if best is None:break
  _,ri,ci=best;x,y,w,h=rects[ri];col=cat[ci];placed.append((x,y,col));rem=[r-c for r,c in zip(rem,col['counts'])];mass+=col['weight']
  if method=='baseline':
   rects.pop(ri)
   if w>col['dx']:rects.append((x+col['dx'],y,w-col['dx'],col['dy']))
   if h>col['dy']:rects.append((x,y+col['dy'],w,h-col['dy']))
  else:rects=split_rects(rects,(x,y,col['dx'],col['dy']))
 return placed,rem
def expand(cargo,loads,task):
 rows=[];ids=Counter()
 for k,(v,cols) in enumerate(loads,1):
  for x,y,col in cols:
   z=0;support=''
   for a,d,o in col['stack']:
    typ=cargo[a]['cargo_type'];ids[typ]+=1;item=f'{typ}-{ids[typ]:04d}'
    rows.append({'task_id':task,'vehicle_id':f'V{k:03d}','vehicle_type':v['vehicle_type'],'item_id':item,'cargo_type':typ,'x_cm':x,'y_cm':y,'z_cm':z,'dx_cm':d[0],'dy_cm':d[1],'dz_cm':d[2],'orientation':o,'support_ids':support});support=item;z+=d[2]
 return rows
def metrics(cargo,vehicles,rows):
 vs={v['vehicle_type']:v for v in vehicles};cs={c['cargo_type']:c for c in cargo};groups={}
 for r in rows:groups.setdefault(r['vehicle_id'],[]).append(r)
 summaries=[]
 for k,rs in groups.items():
  v=vs[rs[0]['vehicle_type']];vol=sum(math.prod([cs[r['cargo_type']][f'{a}_cm'] for a in ['l','w','h']]) for r in rs);weight=sum(cs[r['cargo_type']]['weight_kg'] for r in rs)
  summaries.append({'vehicle_id':k,'vehicle_type':v['vehicle_type'],'items':len(rs),'volume_m3':vol/1e6,'weight_kg':weight,'Uv':vol/(v['l_cm']*v['w_cm']*v['h_cm']),'Uw':weight/v['capacity_kg'],'counts':dict(Counter(r['cargo_type'] for r in rs))})
 totalV=sum(s['volume_m3'] for s in summaries);totalW=sum(s['weight_kg'] for s in summaries);capV=sum(math.prod([vs[s['vehicle_type']][f'{a}_cm'] for a in ['l','w','h']])/1e6 for s in summaries);capW=sum(vs[s['vehicle_type']]['capacity_kg'] for s in summaries)
 return {'N':len(summaries),'n1':sum(s['vehicle_type']=='T1' for s in summaries),'n2':sum(s['vehicle_type']=='T2' for s in summaries),'C':sum(vs[s['vehicle_type']]['cost_yuan'] for s in summaries),'volume_m3':totalV,'weight_kg':totalW,'Uv':totalV/capV if capV else 0,'Uw':totalW/capW if capW else 0,'loaded_counts':dict(Counter(r['cargo_type'] for r in rows)),'vehicles':summaries}
def bounds(cargo,vehicles,cfg,allowed):
 vol=sum(math.prod([c[f'{a}_cm'] for a in ['l','w','h']])*c['quantity'] for c in cargo);wt=sum(c['weight_kg']*c['quantity'] for c in cargo)
 vv=[v for v in vehicles if v['vehicle_type'] in allowed];pairs=[]
 for n1 in range(0,80):
  for n2 in range(0,80):
   nums={'T1':n1,'T2':n2}
   if any(nums[k]>0 and k not in allowed for k in nums):continue
   if sum(nums[v['vehicle_type']]*v['l_cm']*v['w_cm']*(v['h_cm']-cfg.get('gap',3)) for v in vv)+1e-6<vol:continue
   if sum(nums[v['vehicle_type']]*v['capacity_kg'] for v in vv)<wt:continue
   pairs.append((n1+n2,sum(nums[v['vehicle_type']]*v['cost_yuan'] for v in vv),n1,n2))
 return {'count_lower_bound':min(x[0] for x in pairs),'cost_lower_bound':min(x[1] for x in pairs),'basis':'integer nonnegative vehicle combinations; total volume using H-gap and total mass only','count_relaxation_combo':min(pairs),'cost_relaxation_combo':min(pairs,key=lambda x:(x[1],x[0]))}
def solve(data,task,method='maxrect',seed=0,alpha=.2,cfg=None):
 cfg=cfg or {};cargo=data['cargo'];vehicles=data['vehicles'];remaining=[c['quantity'] for c in cargo];cats={v['vehicle_type']:catalogue(cargo,v,cfg) for v in vehicles};loads=[];start=time.perf_counter();deadline=start+cfg.get('run_seconds',120)
 allowed={'Q1-S1':['T1'],'Q1-S2':['T2'],'Q1-F1':['T1'],'Q1-F2':['T2'],'Q2-N':['T1','T2'],'Q2-C':['T1','T2']}[task]
 single=task.startswith('Q1-S')
 while any(remaining):
  options=[]
  for v in vehicles:
   if v['vehicle_type'] not in allowed:continue
   cols,rem=pack_vehicle(cargo,v,remaining,cats[v['vehicle_type']],method,alpha,seed+len(loads)*997,cfg)
   if not cols:continue
   volume=sum(c['volume'] for _,_,c in cols);weight=sum(c['weight'] for _,_,c in cols)
   if task=='Q2-C':key=(volume/v['cost_yuan'],weight/v['cost_yuan'])
   elif task=='Q2-N':key=(volume,weight,-v['cost_yuan'])
   else:key=(volume,weight)
   options.append((key,v,cols,rem))
  if not options:raise ValueError('No legal column can fit remaining cargo; instance not certified infeasible')
  _,v,cols,remaining=max(options,key=lambda x:x[0]);loads.append((v,cols))
  if single:break
  if time.perf_counter()>deadline:raise TimeoutError(f'run deadline after {len(loads)} trucks; incomplete inventory')
 rows=expand(cargo,loads,task);m=metrics(cargo,vehicles,rows);m.update({'runtime_seconds':time.perf_counter()-start,'method':method,'seed':seed,'alpha_mass_preference':alpha,'stop_reason':'finite column constructive completion' if not single else 'no additional catalogue column fits','optimality':'feasible heuristic; global optimum unproved','bounds':None if single else bounds(cargo,vehicles,cfg,allowed),'unloaded_counts':{c['cargo_type']:remaining[i] for i,c in enumerate(cargo)},'catalogue_sizes':{k:len(v) for k,v in cats.items()}});return rows,m
def write_plan(out,rows,m,cfg,data):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 with (out/'placements.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 with (out/'vehicle_summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
  keys=[k for k in m['vehicles'][0] if k!='counts'];w=csv.DictWriter(f,fieldnames=keys+['G1','G2','G3','G4','G5']);w.writeheader()
  for s in m['vehicles']:w.writerow({**{k:s[k] for k in keys},**{k:s['counts'].get(k,0) for k in ['G1','G2','G3','G4','G5']}})
 save(out/'metrics.json',m);save(out/'config.json',{**cfg,'method':m['method'],'seed':m['seed'],'alpha':m['alpha_mass_preference'],'data_sha256':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),'task_id':rows[0]['task_id'],'instance':data,'algorithm_version':'columns-maxrect-v1'})
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--task',required=True,choices=['Q1-S1','Q1-S2','Q1-F1','Q1-F2','Q2-N','Q2-C']);ap.add_argument('--input');ap.add_argument('--out',required=True);ap.add_argument('--method',default='maxrect',choices=['maxrect','baseline']);ap.add_argument('--seed',type=int,default=0);ap.add_argument('--alpha',type=float,default=.2);ap.add_argument('--config');args=ap.parse_args()
 cfg=json.loads(Path(args.config).read_text(encoding='utf-8')) if args.config else {'gap':3,'pressure':500,'run_seconds':120};data=instance(args.input);rows,m=solve(data,args.task,args.method,args.seed,args.alpha,cfg);write_plan(args.out,rows,m,cfg,data);print(json.dumps({k:v for k,v in m.items() if k!='vehicles'},ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except Exception as ex:
  print(json.dumps({'state':'failed','error_type':type(ex).__name__,'message':str(ex),'optimality':None},ensure_ascii=False));raise SystemExit(2)
