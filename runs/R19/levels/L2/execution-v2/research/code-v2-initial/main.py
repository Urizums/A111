"""Offline orthogonal column-packing and exact-inventory pattern MILP. mm/kg/yuan."""
from pathlib import Path
import argparse,csv,json,itertools,time,hashlib,math,platform,re,datetime
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
ROOT=Path(__file__).resolve().parents[1]
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def csvwrite(p,rows):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 if not rows:return
 with p.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def normalize(raw,out):
 from docx import Document
 from openpyxl import load_workbook
 raw=Path(raw);out=Path(out);d=Document(raw/'附件1.docx'); rows=[];types=[]
 for rr in d.tables[0].rows[1:]:
  a=[c.text for c in rr.cells];dims=[int(x)*10 for x in a[2].split('×')]
  t={'cargo_type':a[0],'category':a[1],'dims':dims,'weight':float(a[3]),'count':int(a[4]),'source_ref':'附件1表1/'+a[0]};types.append(t)
  for i in range(t['count']):rows.append({'item_id':f"{a[0]}-{i+1:04d}",'cargo_type':a[0],'category':a[1],'canonical_l_mm':dims[0],'canonical_w_mm':dims[1],'canonical_h_mm':dims[2],'weight_kg':t['weight'],'source_ref':t['source_ref']})
 vs=[]
 for idx,offset in enumerate([3,7]):
  dims=[int(x)*10 for x in re.findall(r'(\d+)cm',d.paragraphs[offset].text)];assert len(dims)==3
  vs.append({'type_id':f'V{idx+1}','dims':dims,'payload_kg':int(re.search(r'(\d+)kg',d.paragraphs[offset+1].text).group(1)),'cost_yuan_per_trip':int(re.search(r'(\d+)\s*元',d.paragraphs[offset+2].text).group(1)),'clearance_mm':30,'source_ref':f'附件1段{offset+1}-{offset+3}'})
 csvwrite(out/'items.csv',rows);dump(out/'types.json',types);dump(out/'vehicles.json',vs)
 wb=load_workbook(raw/'附件2：验证数据集.xlsx',data_only=False)
 dump(out/'attachment2_audit.json',{'status':'dimensions_only_not_full_orders','missing':['quantity','weight','category','payload'],'sheets':{s.title:{c.coordinate:c.value for r in s for c in r if c.value is not None} for s in wb}})
 return types,vs
def orientations(t,strict=False):
 if t['category']=='定向件' or strict and t['category']=='易碎件':ps=[(0,1,2)]
 elif t['category']=='易碎件':ps=[(0,1,2),(1,0,2)]
 else:ps=list(itertools.permutations(range(3)))
 seen=set();out=[]
 for p in ps:
  ds=tuple(t['dims'][i] for i in p)
  if ds not in seen:out.append((ds,''.join(str(i) for i in p)));seen.add(ds)
 return out
def pack(types,v,remaining,weights,config):
 """Guillotine floor partition; each cell holds an identical upright column."""
 if config.get('geometry')=='C':
  from blocks import pack as blockpack
  return blockpack(types,v,remaining,weights,config,orientations)
 L,W,H=v['dims'];H-=v['clearance_mm'];free=[(0,0,L,W)];parts=[];cnt=np.zeros(len(types),int);mass=0.
 pressure=config.get('pressure',500);strict=config.get('fragile_fixed',False)
 while free:
  best=None
  for fi,(x,y,fl,fw) in enumerate(free):
   for ti,t in enumerate(types):
    if remaining[ti]-cnt[ti]<=0:continue
    for (dx,dy,dz),ori in orientations(t,strict):
     if dx>fl or dy>fw or dz>H:continue
     cap=1 if t['category']=='易碎件' else min(H//dz,1+int(pressure*dx*dy/1e6/t['weight']+1e-9))
     k=min(cap,int(remaining[ti]-cnt[ti]),int((v['payload_kg']-mass+1e-8)//t['weight']))
     if k<1:continue
     score=weights[ti]*k/(dx*dy)
     key=(score,k*dx*dy*dz,-fl*fw,-dz,-fi,-ti)
     if best is None or key>best[0]:best=(key,fi,ti,dx,dy,dz,ori,k,x,y,fl,fw)
  platform_best=None
  # Complete standard grid platform with fragile goods on its top. Geometry
  # is explicitly emitted; the separate checker reconstructs all load paths.
  if config.get('platforms',False):
   fi_frag=next((i for i,t in enumerate(types) if t['category']=='易碎件'),None)
   if fi_frag is not None and remaining[fi_frag]>cnt[fi_frag]:
    frag=types[fi_frag]
    for ti,t in enumerate(types):
     if t['category']!='标准件':continue
     nx,ny=(2,3) if t['cargo_type']=='G1' else (4,2)
     sx,sy,sz=t['dims'];bw,bh=nx*sx,ny*sy
     for (fx,fy,fz),fo in orientations(frag,strict):
      nf=min((bw//fx)*(bh//fy),int(remaining[fi_frag]-cnt[fi_frag]))
      if nf<1:continue
      top_pressure=frag['weight']/(fx*fy/1e6)
      cap=min((H-fz)//sz,1+int(max(0,pressure-top_pressure)*sx*sy/1e6/t['weight']))
      k=min(cap,int((remaining[ti]-cnt[ti])//(nx*ny)))
      if k<1 or mass+k*nx*ny*t['weight']+nf*frag['weight']>v['payload_kg']+1e-8:continue
      for fi,(x,y,fl,fw) in enumerate(free):
       if bw>fl or bh>fw:continue
       score=(weights[ti]*k*nx*ny+weights[fi_frag]*nf)/(bw*bh)
       key=(score,k*nx*ny*bw*bh*sz,-fl*fw,-sz,-fi,-ti)
       if (best is None or key>best[0]) and (platform_best is None or key>platform_best[0]):platform_best=(key,fi,ti,fi_frag,bw,bh,k,nx,ny,sx,sy,sz,fx,fy,fz,fo,nf,x,y,fl,fw)
  if platform_best is not None:
   _,fi,ti,tf,dx,dy,k,nx,ny,sx,sy,sz,fx,fy,fz,fo,nf,x,y,fl,fw=platform_best;free.pop(fi)
   for h in range(k):
    for ix in range(nx):
     for iy in range(ny):parts.append({'cargo_type':types[ti]['cargo_type'],'x_mm':x+ix*sx,'y_mm':y+iy*sy,'z_mm':h*sz,'dx_mm':sx,'dy_mm':sy,'dz_mm':sz,'orientation_id':'012'})
   for j in range(nf):parts.append({'cargo_type':types[tf]['cargo_type'],'x_mm':x+(j%(dx//fx))*fx,'y_mm':y+(j//(dx//fx))*fy,'z_mm':k*sz,'dx_mm':fx,'dy_mm':fy,'dz_mm':fz,'orientation_id':fo})
   cnt[ti]+=k*nx*ny;cnt[tf]+=nf;mass+=k*nx*ny*types[ti]['weight']+nf*types[tf]['weight']
   if fl>dx:free.append((x+dx,y,fl-dx,fw))
   if fw>dy:free.append((x,y+dy,dx,fw-dy))
   continue
  if best is None:break
  _,fi,ti,dx,dy,dz,ori,k,x,y,fl,fw=best;free.pop(fi)
  for h in range(k):parts.append({'cargo_type':types[ti]['cargo_type'],'x_mm':x,'y_mm':y,'z_mm':h*dz,'dx_mm':dx,'dy_mm':dy,'dz_mm':dz,'orientation_id':ori})
  cnt[ti]+=k;mass+=k*types[ti]['weight']
  # Two disjoint remaining floor rectangles, split along the longer slack.
  if fl-dx>=fw-dy:
   if fl>dx:free.append((x+dx,y,fl-dx,fw))
   if fw>dy:free.append((x,y+dy,dx,fw-dy))
  else:
   if fw>dy:free.append((x,y+dy,fl,fw-dy))
   if fl>dx:free.append((x+dx,y,fl-dx,dy))
 return {'vehicle_type':v['type_id'],'counts':cnt.tolist(),'placements':parts}
def fleet(types,vehicles,counts,weights,config,mode='mixed'):
 rem=np.array(counts,int);out=[]
 while rem.sum():
  choices=[pack(types,v,rem,weights,config) for v in vehicles];choices=[p for p in choices if sum(p['counts'])]
  if not choices:raise ValueError('heuristic_no_fit_not_mathematical_infeasibility: '+str(rem.tolist()))
  def score(p):
   val=sum(weights[i]*c for i,c in enumerate(p['counts']));v=next(v for v in vehicles if v['type_id']==p['vehicle_type'])
   return val/(v['cost_yuan_per_trip'] if mode=='cost' else 1)
  p=max(choices,key=score);out.append(p);rem-=p['counts']
 return out
def library(types,vs,counts,config):
 rng=np.random.default_rng(config.get('seed',19));patterns=[];seen=set();fleets=[]
 volumes=np.array([math.prod(t['dims']) for t in types],float);masses=np.array([t['weight'] for t in types]);
 weightslist=[np.ones(len(types)),volumes/volumes.mean(),masses/masses.mean()]
 weightslist.extend(np.exp(rng.uniform(-1.8,1.8,len(types))) for _ in range(config.get('starts',22)))
 for vs0 in [[vs[0]],[vs[1]],vs]:
  for w in weightslist:
   f=fleet(types,vs0,counts,w,{**config,'platforms':config.get('platforms',True)});fleets.append(f)
   for p in f:
    key=(p['vehicle_type'],tuple(p['counts']))
    if key not in seen:patterns.append(p);seen.add(key)
 return patterns,fleets
def bounds(types,vs,counts,objective):
 g=math.gcd(*(ds[2] for t in types for ds,ori in orientations(t)))
 volume=sum(math.prod(t['dims'])*c for t,c in zip(types,counts));mass=sum(t['weight']*c for t,c in zip(types,counts));best=1e20;bestpair=None
 for a in range(101):
  for b in range(101):
   if len(vs)==1 and ((vs[0]['type_id']=='V1' and b) or (vs[0]['type_id']=='V2' and a)):continue
   vv={v['type_id']:v for v in vs};capvol=sum(n*math.prod([v['dims'][0],v['dims'][1],g*((v['dims'][2]-v['clearance_mm'])//g)]) for n,v in [(a,vv.get('V1')),(b,vv.get('V2'))] if v)
   capmass=sum(n*v['payload_kg'] for n,v in [(a,vv.get('V1')),(b,vv.get('V2'))] if v)
   if capvol+1e-6>=volume and capmass+1e-6>=mass:
    value=a+b if objective=='vehicles' else a*vv.get('V1',{'cost_yuan_per_trip':0})['cost_yuan_per_trip']+b*vv.get('V2',{'cost_yuan_per_trip':0})['cost_yuan_per_trip']
    if value<best:best=value;bestpair=[a,b]
 return {'volume_mm3':volume,'weight_kg':mass,'lower_bound':best,'relaxation_pair':bestpair,'height_quantum_mm':g,'bound_model':'vertical_line_integral_height_quantization'}
def select(patterns,vs,counts,objective,limit):
 lookup={v['type_id']:v for v in vs};ps=[p for p in patterns if p['vehicle_type'] in lookup];A=np.array([p['counts'] for p in ps],float).T
 costs=np.array([lookup[p['vehicle_type']]['cost_yuan_per_trip'] for p in ps]);epsilon=1/(10*max(1,sum(counts))*max(1,float(costs.max())));c=np.ones(len(ps))+costs*epsilon if objective=='vehicles' else costs+epsilon
 start=time.perf_counter();res=milp(c,integrality=np.ones(len(ps)),bounds=Bounds(np.zeros(len(ps)),np.repeat(100,len(ps))),constraints=LinearConstraint(A,counts,counts),options={'time_limit':limit,'mip_rel_gap':0.000001})
 if res.x is None:raise ValueError('pattern MILP has no incumbent: '+res.message)
 f=[]
 for p,n in zip(ps,np.rint(res.x).astype(int)):
  f.extend([p]*n)
 return f,{'status':int(res.status),'message':res.message,'pattern_count':len(ps),'seconds':time.perf_counter()-start,'restricted_mip_gap':float(res.mip_gap),'restricted_dual_bound':float(res.mip_dual_bound)}
def export(f,types,vs,items,output,scenario,meta,full=True):
 from validate import validate
 ids={t['cargo_type']:[a['item_id'] for a in items if a['cargo_type']==t['cargo_type']] for t in types};idx={t:0 for t in ids};rows=[]
 for vi,p in enumerate(f):
  for q in p['placements']:
   t=q['cargo_type'];r={'run_id':scenario,'scenario_id':scenario,'vehicle_id':f'T{vi+1:03d}','vehicle_type':p['vehicle_type'],'item_id':ids[t][idx[t]],**q};idx[t]+=1;rows.append(r)
 output=Path(output);csvwrite(output/'placements.csv',rows);dump(output/'vehicles.json',vs)
 valid=validate(rows,items,vs,full=full,pressure=meta.get('config',{}).get('pressure',500),fragile_fixed=meta.get('config',{}).get('fragile_fixed',False));dump(output/'validation.json',valid);csvwrite(output/'vehicles_summary.csv',valid['vehicles']);csvwrite(output/'supports.csv',valid['supports'])
 run={'scenario':scenario,'objective':meta.get('objective'),'full_inventory':full,'validation_status':valid['valid'],'unplaced_items':[] if valid['valid'] else valid['errors'],'vehicle_count':len(f),'cost_yuan':sum(x['cost_yuan'] for x in valid['vehicles']),'volume_utilization':sum(x['volume_mm3'] for x in valid['vehicles'])/sum(math.prod(next(v for v in vs if v['type_id']==x['vehicle_type'])['dims']) for x in valid['vehicles']),'weight_utilization':sum(x['weight_kg'] for x in valid['vehicles'])/sum(next(v for v in vs if v['type_id']==x['vehicle_type'])['payload_kg'] for x in valid['vehicles']),'model':None,'tokens':None,'cost':None,**meta};dump(output/'run.json',run)
 if not valid['valid']:raise ValueError('independent validator rejected '+str(valid['errors'][:5]))
 return run
def readitems(p):
 with Path(p).open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 for r in rows:
  for k in ['canonical_l_mm','canonical_w_mm','canonical_h_mm','weight_kg']:
   if r.get(k) in ['',None]:raise ValueError('missing required '+k)
   r[k]=float(r[k]);
   if r[k]<=0:raise ValueError('nonpositive '+k)
 return rows
def typesfrom(items):
 out=[]
 for t in dict.fromkeys(r['cargo_type'] for r in items):
  rr=[r for r in items if r['cargo_type']==t];a=rr[0];out.append({'cargo_type':t,'category':a['category'],'dims':[int(a['canonical_'+k+'_mm']) for k in ['l','w','h']],'weight':a['weight_kg'],'count':len(rr)})
  if any([r['canonical_'+k+'_mm'] for k in ['l','w','h']]!=out[-1]['dims'] or r['weight_kg']!=a['weight_kg'] or r['category']!=a['category'] for r in rr):raise ValueError('cargo_type must have homogeneous dimensions/weight/category')
 return out
def solve(items,vs,config,output):
 types=typesfrom(items);counts=[t['count'] for t in types];output=Path(output);start=time.perf_counter();utcstart=datetime.datetime.now(datetime.timezone.utc).isoformat();patterns,fs=library(types,vs,counts,config);dump(output/'pattern_library.json',patterns);runs=[]
 scenarios=[('q1_all_v1',[vs[0]],'vehicles'),('q1_all_v2',[vs[1]],'vehicles'),('q2_vehicles',vs,'vehicles'),('q2_cost',vs,'cost')]
 for name,vv,obj in scenarios:
  b=fleet(types,vv,counts,np.ones(len(types)),{**config,'platforms':False,'geometry':'A'},mode=obj);bb=bounds(types,vv,counts,obj)
  runs.append(export(b,types,vv,items,output/'baseline'/name,name,{'method':'equal_priority_columns','objective':obj,'bounds':bb,'config':config}))
  f,info=select(patterns,vv,counts,obj,config.get('time_limit',60));runs.append(export(f,types,vv,items,output/'selected'/name,name,{'method':'column_patterns_MILP','objective':obj,'bounds':bb,'solver':info,'config':config}))
 # Single vehicle: scan weighted sum of normalized volume and weight; filter nondominated feasible modes.
 singles=[]
 for v in vs:
  candidates=[]
  for alpha in np.linspace(0,1,11):
   w=np.array([alpha*math.prod(t['dims'])/math.prod(v['dims'])+(1-alpha)*t['weight']/v['payload_kg'] for t in types]);p=pack(types,v,counts,w,config);candidates.append(p)
  candidates.extend(p for p in patterns if p['vehicle_type']==v['type_id'])
  unique={tuple(p['counts']):p for p in candidates};pts=[]
  for p in unique.values():
   u=sum(c*math.prod(t['dims']) for c,t in zip(p['counts'],types))/math.prod(v['dims']);w=sum(c*t['weight'] for c,t in zip(p['counts'],types))/v['payload_kg'];pts.append((u,w,p))
  nd=[a for a in pts if not any(b[0]>=a[0]-1e-10 and b[1]>=a[1]-1e-10 and (b[0]>a[0]+1e-10 or b[1]>a[1]+1e-10) for b in pts)]
  for i,(u,w,p) in enumerate(sorted(nd,key=lambda a:a[0])):
   rr=export([p],types,[v],items,output/'single'/f"{v['type_id']}_{i:02d}",f"single_{v['type_id']}_{i:02d}",{'method':'search_nondominated','objective':'volume_weight','config':config,'counts':p['counts']},full=False);singles.append(rr)
 dump(output/'summary.json',{'runs':runs,'singles':singles,'library_size':len(patterns),'seconds':time.perf_counter()-start,'instance_count':len(items),'utc_start':utcstart,'utc_finish':datetime.datetime.now(datetime.timezone.utc).isoformat(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()});return runs,singles
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path);ap.add_argument('--items',type=Path,default=ROOT/'data/items.csv');ap.add_argument('--vehicles',type=Path,default=ROOT/'data/vehicles.json');ap.add_argument('--config',type=Path);ap.add_argument('--scenario',default='all',choices=['all','q1_all_v1','q1_all_v2','q2_vehicles','q2_cost']);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 if a.raw:normalize(a.raw,ROOT/'data')
 cfg=json.loads(a.config.read_text(encoding='utf8')) if a.config else {'seed':19,'starts':22,'time_limit':60,'pressure':500}
 items=readitems(a.items);vs=json.loads(a.vehicles.read_text(encoding='utf8'))
 if a.scenario=='all':solve(items,vs,cfg,a.output)
 else:
  ts=typesfrom(items);cs=[t['count'] for t in ts];vv=[vs[0]] if a.scenario.endswith('v1') else [vs[1]] if a.scenario.endswith('v2') else vs;obj='cost' if a.scenario=='q2_cost' else 'vehicles';ps,_=library(ts,vs,cs,cfg);f,info=select(ps,vv,cs,obj,cfg.get('time_limit',60));export(f,ts,vv,items,a.output,a.scenario,{'objective':obj,'bounds':bounds(ts,vv,cs,obj),'solver':info,'config':cfg})
