import json,csv,copy,math,time,sys,itertools
from pathlib import Path
from collections import Counter
from independent_review import H,E,R,BASE,review,read_rows,catalogue

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,value):(H/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def semantic_coordinates(a,b):
 aa,ar=read_rows(a);bb,br=read_rows(b);errors=[]
 if len(aa)!=len(bb):return ['row_count']
 for i,(x,y) in enumerate(zip(aa,bb)):
  for k in x:
   eq=float(x[k])==float(y[k]) if k.endswith('_cm') else x[k]==y[k]
   if not eq:errors.append((i,k,x[k],y[k]))
 return errors
def scenario_data(base,name):
 d=copy.deepcopy(base);extras={}
 if name.startswith('vehicle_'):
  _,axis,f=name.split('_');f=float(f)
  for v in d['vehicles']:v[axis+'_cm']*=f
 elif name.startswith('gap_'):extras['gap']=float(name[4:])
 elif name.startswith('capacity_'):
  for v in d['vehicles']:v['capacity_kg']*=float(name[9:])
 elif name.startswith('item_mass_'):
  for c in d['cargo']:c['weight_kg']*=float(name[10:])
 elif name.startswith('pressure_'):extras['pressure']=float(name[9:])
 elif name.startswith('cargo_dimension_') or name.startswith('fixed_density_'):
  f=float(name.rsplit('_',1)[1])
  for c in d['cargo']:
   for a in ['l','w','h']:c[a+'_cm']*=f
   if name.startswith('fixed_density_'):c['weight_kg']*=f**3
 elif name.startswith('demand_'):
  for c in d['cargo']:c['quantity']=int(c['quantity']*float(name[7:]))
 elif name.startswith('fragile_count_'):d['cargo'][2]['quantity']=int(d['cargo'][2]['quantity']*float(name[14:]))
 elif name.startswith('T2_cost_'):d['vehicles'][1]['cost_yuan']=float(name[8:])
 elif name=='fragile_upright':extras['fragile_upright']=True
 elif name=='fragile_floor':extras['fragile_floor']=True
 elif name=='own_mass_pressure':extras['own_mass']=True
 elif name!='base':raise ValueError(name)
 return d,extras
def main():
 start=time.perf_counter();base=load(H/'sandbox/data/instance.json');errors=[];cases=[]
 for task in ['Q1-S1','Q1-S2','Q1-F1','Q1-F2','Q2-N','Q2-C']:
  diff=semantic_coordinates(E/f'plans/{task}/selected',H/f'replay_raw/{task}')
  if diff:errors.append({'type':'formal_numeric_coordinate_difference','task':task,'differences':diff[:5]})
 source=load(E/'experiments/summary.json');fresh=load(H/'sandbox/experiments/summary.json')
 assert len(source)==len(fresh)==168
 for a,b in zip(source,fresh):
  for k in ['task','candidate','method','seed','alpha','fragile_priority','N','C','Uv','Uw']:
   if a[k]!=b[k]:errors.append({'type':'comparison_replay_difference','candidate':a['candidate'],'task':a['task'],'field':k})
  diff=semantic_coordinates(E/a['path'],H/'sandbox'/b['path'])
  if diff:errors.append({'type':'candidate_coordinate_difference','path':a['path'],'differences':diff[:5]})
  got=review(E/a['path'],a['task']);cases.append({'path':a['path'],'task':a['task'],'pass':got['independent_pass_under_declared_model'],
       'N':got['N'],'C':got['C'],'Uv':got['Uv'],'Uw':got['Uw'],'seconds':got['elapsed_seconds'],'errors':got['violations']+got['adapter_errors']})
  if not cases[-1]['pass']:errors.append(cases[-1])
  if a['candidate']=='C027':print('independently checked all 28 candidates',a['task'],flush=True)
 nd={}
 for task in ['Q1-S1','Q1-S2']:
  pool=[r for r in source if r['task']==task]
  pts=[r for r in pool if not any(s['Uv']>=r['Uv'] and s['Uw']>=r['Uw'] and (s['Uv']>r['Uv'] or s['Uw']>r['Uw']) for s in pool)]
  nd[task]=len({(r['Uv'],r['Uw']) for r in pts})
 selected=load(E/'sensitivity/results.json');new=load(H/'sandbox/sensitivity/results.json');assert len(selected)==len(new)==116
 scen=[]
 for a,b in zip(selected,new):
  expected,extras=scenario_data(base,a['scenario']);cfg=load(E/a['path']/'config.json')
  if cfg['instance']!=expected or any(cfg.get(k)!=v for k,v in extras.items()):errors.append({'type':'scenario_source_transform','path':a['path']})
  for k in ['scenario','task','N','n1','n2','C','Uv','Uw','volume_m3','weight_kg']:
   if a[k]!=b[k]:errors.append({'type':'sensitivity_replay_difference','scenario':a['scenario'],'task':a['task'],'field':k})
  diff=semantic_coordinates(E/a['path'],H/'sandbox'/b['path'])
  if diff:errors.append({'type':'scenario_coordinate_difference','path':a['path'],'differences':diff[:5]})
  got=review(E/a['path'],a['task'],scenario=True);scen.append({'scenario':a['scenario'],'task':a['task'],'pass':got['independent_pass_under_declared_model'],'N':got['N'],'C':got['C'],'seconds':got['elapsed_seconds'],'errors':got['violations']+got['adapter_errors']})
  if not scen[-1]['pass']:errors.append(scen[-1])
  if a['task']=='Q2-C':print('independently checked all four selected scenarios',a['scenario'],flush=True)
 cg,vg=BASE;V=sum(math.prod(x['dims'])*x['count'] for x in cg.values());W=sum(x['mass']*x['count'] for x in cg.values())
 pairs=[(i+j,vg['T1']['cost']*i+vg['T2']['cost']*j,i,j) for i in range(21) for j in range(21)
        if i*math.prod(vg['T1']['dims'][:2])*(vg['T1']['dims'][2]-3)+j*math.prod(vg['T2']['dims'][:2])*(vg['T2']['dims'][2]-3)>=V and i*vg['T1']['payload']+j*vg['T2']['payload']>=W]
 bounds={'source_total_volume_m3':V/1e6,'source_total_weight_kg':W,'same_T1':math.ceil(max(V/(420*210*217),W/6000)),
         'same_T2':math.ceil(max(V/(680*245*247),W/10000)),'mixed_count':min(x[0] for x in pairs),'mixed_cost':min(x[1] for x in pairs),
         'finite_enum_sufficient_for_lower_N_C':'Counts above20 imply N>20 or cost>=9450>known mixed feasible7000; cannot improve queried minima',
         'max_density':max(x['mass']/(math.prod(x['dims'])/1e6) for x in cg.values()),'sampled_nd_points':nd}
 out={'declared_review_window_seconds':900,'comparison_actual_rerun_calls':168,'comparison_independent_cases':cases,
      'sensitivity_actual_rerun_calls':348,'sensitivity_independent_selected':scen,'bounds_independent':bounds,
      'original_vs_fresh_formal_coordinate_numeric_equal':not any(x.get('type')=='formal_numeric_coordinate_difference' for x in errors),
      'byte_difference_reason':'raw parser normalizes integers to floats; original coordinate CSV 60 vs new 60.0; numeric/ID/orientation/support semantics separately checked',
      'errors':errors,'all_checks_pass':not errors,'elapsed_seconds':time.perf_counter()-start,
      'limits':'Expanded library64 packing and 1674 local repack calls not independently rerun; inspected source/receipts/artifacts only. Original global minima remain unproved.'}
 write('experiment-audit.json',out);print(json.dumps({'all_checks_pass':not errors,'errors':len(errors),'seconds':out['elapsed_seconds'],'bounds':bounds},ensure_ascii=False));assert not errors
if __name__=='__main__':main()
