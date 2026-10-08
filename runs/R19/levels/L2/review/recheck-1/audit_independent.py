from pathlib import Path
import sys,json,csv,math,itertools,hashlib,datetime,time,importlib.util,copy,collections
B=Path.cwd();O=B/'runs/R19/levels/L2/review/recheck-1';E=B/'runs/R19/levels/L2/execution-v2';I=O.parent/'initial'
spec=importlib.util.spec_from_file_location('initial_oracle',I/'audit_frozen.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def allowed_h(i,strict=False):
 return list(i['dims']) if i['category']=='standard' else [i['dims'][2]]
def bound(items,vs,obj):
 q=math.gcd(*(int(d) for i in items.values() for d in allowed_h(i)))
 caps={k:v['dims'][0]*v['dims'][1]*q*math.floor((v['dims'][2]-v['clearance'])/q) for k,v in vs.items()}
 vol=sum(math.prod(i['dims']) for i in items.values());mass=sum(i['weight'] for i in items.values())
 if min(caps.values())<=0:return {'lower_bound':None,'necessary_too_short':True,'height_quantum_mm':q}
 # All-one-type relaxed feasible incumbent bounds both enumeration and cheaper positive-cost combinations.
 ns0={k:max(math.ceil(vol/caps[k]),math.ceil(mass/v['payload'])) for k,v in vs.items()}
 ceiling=min(n*(vs[k]['cost'] if obj=='cost' else 1) for k,n in ns0.items())
 limits={k:math.floor(ceiling/(v['cost'] if obj=='cost' else 1)) for k,v in vs.items()}
 arr=list(vs);best=math.inf;pair=None
 for ns in itertools.product(*(range(limits[k]+1) for k in arr)):
  if sum(n*caps[k] for n,k in zip(ns,arr))+1e-6<vol or sum(n*vs[k]['payload'] for n,k in zip(ns,arr))+1e-7<mass:continue
  value=sum(n*(vs[k]['cost'] if obj=='cost' else 1) for n,k in zip(ns,arr))
  if value<best:best=value;pair=dict(zip(arr,ns))
 return {'lower_bound':best,'height_quantum_mm':q,'capacity_mm3':caps,'pair':pair,'valid_domain':'all original permitted orthogonal layouts; vertical line segments, no grid/support assumption','enumeration_objective_ceiling':ceiling,'volume_mm3':vol,'mass_kg':mass}
a.relaxed_bound=bound
ITEMS,VS,CFG=a.expected();CFG.update(time_limit=45,geometry='C')
cache={};records=[]
def layout(folder,items=ITEMS,vs=VS,cfg=CFG,full=True,tag=None):
 key=hashlib.sha256((folder/'placements.csv').read_bytes()+json.dumps([items,vs,cfg,full],sort_keys=True).encode()).hexdigest()
 if key in cache:
  z=copy.deepcopy(cache[key]);z['folder']=str(folder.relative_to(B));z['shared_geometry_check']=cache[key]['folder']
  r=json.loads((folder/'run.json').read_text(encoding='utf-8-sig'));z['reported_metric_matches']={k:abs(r[k]-v)<1e-8 for k,v in z['metrics'].items() if k in r and isinstance(v,(int,float))}
 else:z=a.audit(folder,items,vs,cfg,full,tag);cache[key]=copy.deepcopy(z)
 if cfg.get('fragile_floor'):
  z['fragile_floor_check']=all(float(r['z_mm'])==0 for r in a.readcsv(folder/'placements.csv') if items[r['item_id']]['category']=='fragile')
 z['tag']=tag;records.append(z);return z
def pat(p,items=ITEMS,vs=VS,cfg=CFG):
 cat={i['cargo']:i for i in items.values()};its={};placements=[];counts=collections.Counter()
 for ix,r in enumerate(p['placements']):
  iid=str(ix);i=cat[r['cargo_type']];its[iid]={**i};counts[i['cargo']]+=1
  placements.append({'item_id':iid,'vehicle_id':'T','xyz':[float(r[k]) for k in ['x_mm','y_mm','z_mm']],'dims':[float(r[k]) for k in ['dx_mm','dy_mm','dz_mm']],'cargo':i['cargo']})
  ori=tuple(map(int,r['orientation_id']));allowed=set(itertools.permutations(range(3))) if i['category']=='standard' else {(0,1,2),(1,0,2)} if i['category']=='fragile' and not cfg.get('fragile_fixed') else {(0,1,2)}
  assert ori in allowed and [i['dims'][j] for j in ori]==placements[-1]['dims']
 z=a.validate_layout(its,{'T':vs[p['vehicle_type']]},placements,full=True,fragile_fixed=cfg.get('fragile_fixed',False),full_support_all=True,pressure_limit=cfg['pressure'])
 return {'valid':z['valid'],'errors':z['errors'][:10],'counts':[counts[t] for t in a.CAT],'reported_counts_match':p.get('counts') is None or p['counts']==[counts[t] for t in a.CAT]}
def fleet_key(f,obj,vs=VS):
 cost=sum(vs[p['vehicle_type']]['cost'] for p in f);return (len(f),cost) if obj=='vehicles' else (cost,len(f))
def physical_fleet(folder):
 gr=collections.defaultdict(list)
 for r in a.readcsv(folder/'placements.csv'):gr[(r['vehicle_id'],r['vehicle_type'])].append(r)
 return [{'vehicle_type':v,'counts':[sum(r['cargo_type']==t for r in rr) for t in a.CAT],'placements':[{k:(int(r[k]) if k.endswith('_mm') else r[k]) for k in ('cargo_type','orientation_id','x_mm','y_mm','z_mm','dx_mm','dy_mm','dz_mm')} for r in rr]} for (_,v),rr in gr.items()]
if __name__=='__main__':
 st=time.perf_counter();input_checks={'official_data':a.input_match(E/'data',ITEMS,VS,CFG,False),'new_zip_normalized':a.input_match(O/'zip_staged/data',ITEMS,VS,CFG,False)}
 for label,root in [('frozen',E/'results/final'),('fresh_zip',O/'zip_staged/results/full')]:
  for group in ('baseline','selected','single'):
   for f in sorted((root/group).iterdir()):
    if f.is_dir():layout(f,full=group!='single',tag=label)
 print('Final and actual ZIP layouts independently checked',flush=True)
 exp=[]
 for c in a.readcsv(E/'experiments/experiments.csv'):
  items,vs,cfg=a.expected(c);cfg.update(geometry='C')
  if c['parameter']=='fragile_floor':cfg['fragile_floor']=True
  f=E/'experiments'/c['case'];im=a.input_match(f,items,vs,cfg)
  if c['status']=='failed':z={'case':c['case'],'input_check':im,'necessary_height_failure':all(all(min(allowed_h(i))>v['dims'][2]-v['clearance'] for v in vs.values()) for i in items.values())}
  else:
   z=layout(f,items,vs,cfg,True,c['case']);z['input_check']=im;z['csv_metric_matches']={k:abs(float(c[k])-z['metrics'][k])<1e-7 for k in ('cost_yuan','volume_utilization','weight_utilization')};z['csv_metric_matches']['vehicles']=int(c['vehicles'])==z['metrics']['vehicle_count']
  exp.append(z)
 print('36 current parameters independently checked',flush=True)
 comp=[];guard=[]
 summary=json.loads((E/'research/comparison/guarded_summary.json').read_text())
 for row in summary:
  d=E/'research/comparison'/row['case'];cfg=json.loads((d/'config.json').read_text());cfg['fragile_fixed']=False
  for sub in ('baseline','selected','guarded/selected'):
   for f in sorted((d/sub).iterdir()):layout(f,cfg=cfg,tag=row['case']+'/'+sub)
  fs=json.loads((d/'guarded/generated_fleets.json').read_text());fs += [physical_fleet(d/'selected'/n) for n in ('q1_all_v1','q1_all_v2','q2_vehicles','q2_cost')]
  total_counts=collections.Counter(i['cargo'] for i in ITEMS.values());checks=[]
  for name,obj,allowed in [('q1_all_v1','vehicles',{'V1'}),('q1_all_v2','vehicles',{'V2'}),('q2_vehicles','vehicles',set(VS)),('q2_cost','cost',set(VS))]:
   good=[f for f in fs if set(p['vehicle_type'] for p in f)<=allowed and [sum(p['counts'][j] for p in f) for j in range(5)]==[total_counts[t] for t in a.CAT]]
   best=min(fleet_key(f,obj) for f in good);observed=fleet_key(physical_fleet(d/'guarded/selected'/name),obj);checks.append({'scenario':name,'independent_best_key':best,'observed_key':observed,'matches':best==observed})
  rawrec=json.loads((d/'receipt.json').read_text());grec=json.loads((d/'guarded/receipt.json').read_text()) if (d/'guarded/receipt.json').exists() else None
  guard.append({'case':row['case'],'checks':checks,'config':cfg,'initial_code_hashes':rawrec['code_hashes'],'raw_actual_seconds':rawrec['outer_seconds'],'reported_total_seconds':row['total_outer_seconds'],'guard_seconds_from_summary':json.loads((d/'guarded/summary.json').read_text())['guard_seconds'],'reported_seconds_sum_match':abs(row['total_outer_seconds']-rawrec['outer_seconds']-json.loads((d/'guarded/summary.json').read_text())['guard_seconds'])<1e-7})
 print('9 raw/guard comparisons and all36 pool choices independently checked',flush=True)
 ps=json.loads((E/'results/final/pattern_library.json').read_text());pr=[pat(p) for p in ps]
 # Validate every unique generated pattern in guard pools, so independent guard count vectors refer to actual valid geometry.
 poolunique={json.dumps(p,sort_keys=True):p for row in summary for f in json.loads((E/'research/comparison'/row['case']/'guarded/generated_fleets.json').read_text()) for p in f}
 poolchecks=[pat(p) for p in poolunique.values()]
 bd={name:bound(ITEMS,vv,obj) for name,vv,obj in [('v1',{'V1':VS['V1']},'vehicles'),('v2',{'V2':VS['V2']},'vehicles'),('mixed',VS,'vehicles'),('cost',VS,'cost')]}
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'independent_method':'reviewer official DOCX XML + frozen independent checker; reviewer-bound adaptation only','input_checks':input_checks,'layouts':records,'parameters':exp,'guard_choices':guard,'main_patterns':pr,'guard_generated_unique_pattern_checks':poolchecks,'bounds':bd,'seconds':time.perf_counter()-st}
 dump(O/'independent-audit.json',result)
 print(json.dumps({'layouts':len(records),'unique_geometry_checks':len(cache),'main_patterns':len(pr),'guard_pool_unique_patterns':len(poolchecks),'invalid_layouts':[x['folder'] for x in records if not x['valid']],'invalid_patterns':sum(not x['valid'] or not x['reported_counts_match'] for x in pr+poolchecks),'parameter_input_errors':[x.get('case',x.get('tag')) for x in exp if not x['input_check']['matched']],'guard_mismatches':[x['case'] for x in guard if not all(y['matches'] for y in x['checks'])],'bounds':bd,'seconds':result['seconds']},ensure_ascii=False),flush=True)
