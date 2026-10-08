from main import *
import copy,traceback,sys
case_filter=int(sys.argv[1]) if len(sys.argv)>1 else None
baseitems=readitems(ROOT/'data/items.csv');basevs=json.loads((ROOT/'data/vehicles.json').read_text(encoding='utf8'));configs=[]
for key in ['vehicle_length','vehicle_width','vehicle_height','payload','cost_v1','cost_v2','cargo_size','cargo_weight','quantity','dense_share','pressure','clearance']:
 values=[0.9,1.1] if key not in ['quantity','dense_share','clearance'] else [0.8,1.2] if key!='clearance' else [0,2]
 for value in values:configs.append((key,value))
configs.extend([('baseline',1),('fragile_fixed',1),('quantity',2),('vehicle_height',0.1)])
configs.extend([('interaction',x) for x in [(0.9,0.9),(0.9,1.1),(1.1,0.9),(1.1,1.1)]])
configs.append(('fragile_floor',1))
configs.extend([('seed',s) for s in [7,29,41]])
records=[]
checkpoint=ROOT/'experiments/experiments.csv'
if checkpoint.exists():
 with checkpoint.open(encoding='utf-8-sig') as f:records=list(csv.DictReader(f))
completed={r['case'] for r in records}
for ix,(key,value) in enumerate(configs):
 if case_filter is not None and ix!=case_filter:continue
 if f'{ix:02d}_{key}' in completed:continue
 name=f'{ix:02d}_{key}';output=ROOT/'experiments'/name;output.mkdir(exist_ok=True);items=copy.deepcopy(baseitems);vs=copy.deepcopy(basevs);cfg={'seed':19,'starts':5,'time_limit':8,'pressure':500,'platforms':True,'geometry':'C'};start=time.perf_counter()
 if key.startswith('vehicle_'):
  k={'vehicle_length':0,'vehicle_width':1,'vehicle_height':2}[key]
  for v in vs:v['dims'][k]=int(round(v['dims'][k]*value))
 if key=='payload':
  for v in vs:v['payload_kg']*=value
 if key.startswith('cost_'):
  vs[0 if key=='cost_v1' else 1]['cost_yuan_per_trip']*=value
 if key=='cargo_size':
  for r in items:
   for k in ['canonical_l_mm','canonical_w_mm','canonical_h_mm']:r[k]=int(round(r[k]*value))
 if key=='cargo_weight':
  for r in items:r['weight_kg']*=value
 if key in ['quantity','dense_share']:
  grouped={t:[r for r in items if r['cargo_type']==t] for t in dict.fromkeys(r['cargo_type'] for r in items)};items=[]
  for t,rr in grouped.items():
   n=int(round(len(rr)*(value if key=='quantity' or t in ['G1','G2','G5'] else 2-value)))
   for i in range(n):r=copy.deepcopy(rr[i%len(rr)]);r['item_id']=f'{t}-{i+1:05d}';items.append(r)
 if key=='pressure':cfg['pressure']*=value
 if key=='clearance':
  for v in vs:v['clearance_mm']*=value
 if key=='fragile_fixed':cfg['fragile_fixed']=True
 if key=='fragile_floor':cfg['platforms']=False;cfg['fragile_floor']=True
 if key=='seed':cfg['seed']=int(value)
 if key=='interaction':
  for v in vs:v['dims'][1]=int(round(v['dims'][1]*value[0]));v['cost_yuan_per_trip']*=value[1] if v['type_id']=='V1' else 1
 csvwrite(output/'items.csv',items);dump(output/'vehicles.json',vs);dump(output/'config.json',cfg)
 try:
  ts=typesfrom(items);cs=[t['count'] for t in ts];ps,fs=library(ts,vs,cs,cfg);dump(output/'patterns.json',ps);f,info=select(ps,vs,cs,'cost',cfg['time_limit'],fs);run=export(f,ts,vs,items,output,'sensitivity_'+name,{'objective':'cost','solver':info,'bounds':bounds(ts,vs,cs,'cost'),'config':cfg})
  rec={'case':name,'parameter':key,'factor':str(value),'items':len(items),'status':'validated','vehicles':run['vehicle_count'],'cost_yuan':run['cost_yuan'],'volume_utilization':run['volume_utilization'],'weight_utilization':run['weight_utilization'],'lower_bound':run['bounds']['lower_bound'],'seconds':time.perf_counter()-start,'solver_status':info['status'],'error':''}
 except Exception as e:
  dump(output/'failure.json',{'exception':str(e),'traceback':traceback.format_exc(),'classification':'research_iteration','not_mathematical_infeasibility':True});rec={'case':name,'parameter':key,'factor':str(value),'items':len(items),'status':'failed','vehicles':None,'cost_yuan':None,'volume_utilization':None,'weight_utilization':None,'lower_bound':None,'seconds':time.perf_counter()-start,'solver_status':None,'error':str(e)}
 records.append(rec);csvwrite(ROOT/'experiments/experiments.csv',records);print(json.dumps(rec,ensure_ascii=False),flush=True)
dump(ROOT/'experiments/manifest.json',{'declared_cases':len(configs),'records':records,'model':None,'tokens':None,'cost':None,'note':'synthetic parameter perturbations; not official attachment2 orders'})
