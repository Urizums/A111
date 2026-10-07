from pathlib import Path
import sys,json,csv,math,copy,collections,hashlib,datetime,time,ast,itertools
B=Path.cwd();O=B/'runs/R19/levels/L2/review/initial';E=B/'runs/R19/levels/L2/execution';P=B/'runs/R19/levels/L2/review/preparation';sys.path.insert(0,str(P))
from read_official_data import official
from independent_checker import validate_layout
D=official(B/'runs/R19/inputs/raw/附件1.docx');CAT=D['catalog'];RAW_V={f'V{k}':v for k,v in D['vehicle_types'].items()}
def readcsv(p):
 with Path(p).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def expected(case=None):
 cat=copy.deepcopy(CAT);v=copy.deepcopy(RAW_V);cfg={'pressure':500,'fragile_fixed':False,'platforms':True,'seed':19,'starts':22 if case is None else 5,'time_limit':60 if case is None else 8}
 counts={k:t['count'] for k,t in cat.items()};digits=4
 if case:
  k=case['parameter'];x=ast.literal_eval(case['factor'])
  if k.startswith('vehicle_'):
   ix={'vehicle_length':0,'vehicle_width':1,'vehicle_height':2}[k]
   for a in v.values():a['dims'][ix]=int(round(a['dims'][ix]*x))
  elif k=='payload':
   for a in v.values():a['payload']*=x
  elif k in ['cost_v1','cost_v2']:v['V1' if k=='cost_v1' else 'V2']['cost']*=x
  elif k=='cargo_size':
   for a in cat.values():a['dims']=tuple(int(round(n*x)) for n in a['dims'])
  elif k=='cargo_weight':
   for a in cat.values():a['weight']*=x
  elif k in ['quantity','dense_share']:
   digits=5;counts={t:int(round(n*(x if k=='quantity' or t in ['G1','G2','G5'] else 2-x))) for t,n in counts.items()}
  elif k=='pressure':cfg['pressure']*=x
  elif k=='clearance':
   for a in v.values():a['clearance']*=x
  elif k=='fragile_fixed':cfg['fragile_fixed']=True
  elif k=='fragile_floor':cfg['platforms']=False
  elif k=='seed':cfg['seed']=int(x)
  elif k=='interaction':
   for a in v.values():a['dims'][1]=int(round(a['dims'][1]*x[0]))
   v['V1']['cost']*=x[1]
  elif k!='baseline':raise ValueError(k)
 items={f'{t}-{i+1:0{digits}d}':{'dims':list(a['dims']),'weight':a['weight'],'category':a['category'],'cargo':t} for t,a in cat.items() for i in range(counts[t])}
 return items,v,cfg
ITEMS,V,C=expected()
def input_match(folder,items,vs,cfg,checkcfg=True):
 errors=[];actual=readcsv(folder/'items.csv')
 if {r['item_id'] for r in actual}!=set(items) or len(actual)!=len(items):errors.append('inventory input differs from independently derived official/perturbed IDs')
 cmap={'standard':'标准件','fragile':'易碎件','directional':'定向件'}
 for r in actual:
  a=items.get(r['item_id'])
  if a is None:continue
  if r['cargo_type']!=a['cargo'] or r['category']!=cmap[a['category']] or [float(r['canonical_'+k+'_mm']) for k in ['l','w','h']]!=a['dims'] or abs(float(r['weight_kg'])-a['weight'])>1e-9:errors.append('input row mismatch '+r['item_id'])
 actualv=json.loads((folder/'vehicles.json').read_text(encoding='utf-8-sig'))
 for r in actualv:
  a=vs.get(r['type_id'])
  if a is None or r['dims']!=a['dims'] or r['payload_kg']!=a['payload'] or r['cost_yuan_per_trip']!=a['cost'] or r['clearance_mm']!=a['clearance']:errors.append('vehicle input mismatch '+r['type_id'])
 if set(r['type_id'] for r in actualv)!=set(vs):errors.append('vehicle type set')
 if checkcfg:
  actualc=json.loads((folder/'config.json').read_text(encoding='utf-8-sig'))
  for k,z in cfg.items():
   if actualc.get(k,False if k=='fragile_fixed' else None)!=z:errors.append('config mismatch '+k)
 return {'matched':not errors,'errors':errors[:20],'items':len(actual)}
def relaxed_bound(items,vv,obj):
 volume=sum(math.prod(a['dims']) for a in items.values());weight=sum(a['weight'] for a in items.values());arr=list(vv.items());best=math.inf;pair=None
 # Audit domain 3000/6000 orders; no bound from a truncated search: incumbent-derived maxima encompass any cheaper feasible pair.
 upper=sum(a['cost'] for a in vv.values())*len(items) if obj=='cost' else len(items)
 maxn=math.ceil(volume/min(a['dims'][0]*a['dims'][1]*(a['dims'][2]-a['clearance']) for a in vv.values()))+math.ceil(weight/min(a['payload'] for a in vv.values()))+2
 for ns in itertools.product(range(maxn+1),repeat=len(arr)):
  cv=sum(n*a['dims'][0]*a['dims'][1]*(a['dims'][2]-a['clearance']) for n,(_,a) in zip(ns,arr));cw=sum(n*a['payload'] for n,(_,a) in zip(ns,arr))
  if cv+1e-5<volume or cw+1e-7<weight:continue
  val=sum(ns) if obj=='vehicles' else sum(n*a['cost'] for n,(_,a) in zip(ns,arr))
  if val<best:best=val;pair={k:n for n,(k,a) in zip(ns,arr)}
 return {'volume_mm3':volume,'mass_kg':weight,'lower_bound':best,'pair':pair,'enumeration_limit':maxn,'proof':'maxn is sum of sufficient volume and mass ceilings using smallest capacity, so some all-one-type feasible relaxed pair is within range; any smaller positive objective can be searched with this range here'}
def audit(folder,items,vs,cfg,full=True,case=None):
 rows=readcsv(folder/'placements.csv');vehicles={};ps=[];errors=[]
 for r in rows:
  if r['vehicle_type'] not in vs:errors.append('unknown vehicle type');continue
  if r['vehicle_id'] in vehicles and vehicles[r['vehicle_id']]!=vs[r['vehicle_type']]:errors.append('inconsistent vehicle ID type')
  vehicles[r['vehicle_id']]=vs[r['vehicle_type']]
  ps.append({'item_id':r['item_id'],'vehicle_id':r['vehicle_id'],'xyz':[float(r[k]) for k in ['x_mm','y_mm','z_mm']],'dims':[float(r[k]) for k in ['dx_mm','dy_mm','dz_mm']],'cargo':r['cargo_type']})
  a=items.get(r['item_id'])
  if a and r['cargo_type']!=a['cargo']:errors.append('cargo label mismatch '+r['item_id'])
  try:
   ori=list(map(int,r['orientation_id']));canonical=a['dims'];allowed=set(itertools.permutations(range(3))) if a['category']=='standard' else {(0,1,2),(1,0,2)} if a['category']=='fragile' and not cfg['fragile_fixed'] else {(0,1,2)}
   if tuple(ori) not in allowed or [canonical[i] for i in ori]!=ps[-1]['dims']:errors.append('orientation ID mapping '+r['item_id'])
  except Exception:errors.append('malformed orientation '+r['item_id'])
 z=validate_layout(items,vehicles,ps,full=full,fragile_fixed=cfg['fragile_fixed'],full_support_all=True,pressure_limit=cfg['pressure'])
 z['errors'].extend({'rule':e} for e in errors);z['valid']=not z['errors']
 volume=sum(m['volume_mm3'] for m in z['metrics'].values());weight=sum(m['weight'] for m in z['metrics'].values())
 metrics={'vehicle_count':len(vehicles),'cost_yuan':z['total_cost'],'volume_utilization':volume/sum(math.prod(v['dims']) for v in vehicles.values()),'weight_utilization':weight/sum(v['payload'] for v in vehicles.values()),'item_count':len(rows),'fleet':dict(collections.Counter(r['vehicle_type'] for r in {r['vehicle_id']:r for r in rows}.values()))}
 run=json.loads((folder/'run.json').read_text(encoding='utf-8-sig'));matches={k:abs(run[k]-v)<1e-8 for k,v in metrics.items() if k in run and isinstance(v,(int,float))}
 summary=readcsv(folder/'vehicles_summary.csv');tableerrors=[]
 for r in summary:
  m=z['metrics'].get(r['vehicle_id']);
  if m is None:tableerrors.append('unknown summary vehicle');continue
  for k,mk in [('weight_kg','weight'),('volume_mm3','volume_mm3'),('volume_utilization','volume_utilization'),('weight_utilization','weight_utilization'),('cost_yuan','cost')]:
   if abs(float(r[k])-m[mk])>1e-7:tableerrors.append(r['vehicle_id']+'/'+k)
  for t,n in m['counts'].items():
   if int(r[t])!=n:tableerrors.append(r['vehicle_id']+'/'+t)
 pressure=[]
 for e in z['contacts']:
  allarea=sum(q['area_mm2'] for q in z['contacts'] if q['upper']==e['upper']);force=z['loads'][e['upper']]['self_plus_transmitted_kg']*e['area_mm2']/allarea
  pressure.append(force/(e['area_mm2']/1e6))
 minclear=min(vehicles[p['vehicle_id']]['dims'][2]-p['xyz'][2]-p['dims'][2] for p in ps)
 out={'folder':str(folder.relative_to(B)),'full':full,'valid':z['valid'],'errors':z['errors'][:30],'warning_count':len(z['warnings']),'metrics':metrics,'reported_metric_matches':matches,'summary_errors':tableerrors,'max_pressure':max(pressure,default=0),'min_clearance_mm':minclear,'counts':z['inventory'],'per_vehicle':z['metrics'],'case':case,'placements_sha256':hashlib.sha256((folder/'placements.csv').read_bytes()).hexdigest()}
 if full:
  use={k:v for k,v in vs.items() if k=='V1'} if run.get('scenario')=='q1_all_v1' else {k:v for k,v in vs.items() if k=='V2'} if run.get('scenario')=='q1_all_v2' else vs
  bd=relaxed_bound(items,use,run.get('objective','cost'));out['independent_relaxation']=bd
  out['reported_bound_matches']=abs(bd['lower_bound']-run['bounds']['lower_bound'])<1e-7
 return out
if __name__=='__main__':
 t=time.perf_counter();records=[];inputs={'official_data':input_match(E/'data',ITEMS,V,C,False)}
 for group in ['baseline','selected','single']:
  for f in sorted((E/'results/final'/group).iterdir()):
   if f.is_dir():records.append(audit(f,ITEMS,V,C,group!='single'))
 print('Frozen final '+str(len(records))+' layouts independently checked',flush=True)
 exps=[]
 for c in readcsv(E/'experiments/experiments.csv'):
  f=E/'experiments'/c['case'];i,v,cfg=expected(c);im=input_match(f,i,v,cfg)
  if c['status']=='failed':
   reasons={name:{vt:all(d[2]>v0['dims'][2]-v0['clearance'] for d in set(itertools.permutations(a['dims'])) if a['category']=='standard') if a['category']=='standard' else a['dims'][2]>v0['dims'][2]-v0['clearance'] for vt,v0 in v.items()} for name,a in CAT.items()}
   exps.append({'case':c['case'],'input_check':im,'failed_case_source_necessary_height_check':reasons,'preserved_failure':json.loads((f/'failure.json').read_text(encoding='utf-8-sig'))})
  else:
   z=audit(f,i,v,cfg,True,c['case']);z['input_check']=im;z['csv_metric_matches']={k:abs(float(c[k])-z['metrics'][k])<1e-7 for k in ['vehicles' if False else 'cost_yuan','volume_utilization','weight_utilization']};z['csv_metric_matches']['vehicles']=int(c['vehicles'])==z['metrics']['vehicle_count'];exps.append(z)
 print('All '+str(len(exps))+' experiment records independently checked',flush=True)
 rho=max(a['weight']/(math.prod(a['dims'])/1e9) for a in CAT.values());density={'max_density_kg_m3':rho,'upper_load_fractions':{k:rho*a['dims'][0]*a['dims'][1]*(a['dims'][2]-a['clearance'])/1e9/a['payload'] for k,a in V.items()}}
 report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_docx_hash':D['raw_sha256'],'independent_code':'audit_frozen.py + frozen preparation/independent_checker.py + read_official_data.py; no producer geometry imported','input_checks':inputs,'layouts':records,'experiments':exps,'density_bound':density,'seconds':time.perf_counter()-t}
 (O/'independent-frozen-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'final_layouts':len(records),'experiments':len(exps),'layout_errors':[z['folder'] for z in records if not z['valid']],'experiment_errors':[z.get('case') for z in exps if z.get('valid') is False or not z['input_check']['matched']],'seconds':report['seconds']},ensure_ascii=False),flush=True)
