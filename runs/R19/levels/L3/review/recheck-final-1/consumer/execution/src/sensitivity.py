import copy,json,time,csv,datetime,math
from solver import E,instance,solve,write_plan,save
from checker import validate_dir
def main():
 base=instance();standard={'gap':3,'pressure':500,'run_seconds':120,'reserve_support':True,'fragile_priority':3};sc=[]
 def add(name,group,edit=None,extra=None,description=''):
  d=copy.deepcopy(base);cfg=dict(standard)
  if edit:edit(d)
  if extra:cfg.update(extra)
  sc.append((name,group,d,cfg,description))
 add('base','baseline',description='same fixed scenario comparison; alpha=.2 and three seeds, not selected search above')
 for axis in ['l','w','h']:
  for factor in [.9,1.1]:add(f'vehicle_{axis}_{factor}','geometry',lambda d,a=axis,f=factor:[v.update({a+'_cm':v[a+'_cm']*f}) for v in d['vehicles']],description=f'both vehicle {axis} lengths x{factor}; scenario, cost unchanged')
 for gap in [0,6,10]:add(f'gap_{gap}','geometry',extra={'gap':gap},description='scenario safe gap cm')
 for factor in [.5,1.5]:add(f'capacity_{factor}','load',lambda d,f=factor:[v.update(capacity_kg=v['capacity_kg']*f) for v in d['vehicles']],description='rated payload independently scaled')
 for factor in [.8,1.2]:add(f'item_mass_{factor}','load',lambda d,f=factor:[c.update(weight_kg=c['weight_kg']*f) for c in d['cargo']],description='fixed geometry, independent mass scenario')
 for p in [300,700]:add(f'pressure_{p}','load',extra={'pressure':p},description='stack pressure threshold kg/m²; reoptimize')
 for factor in [.9,1.1]:
  add(f'cargo_dimension_{factor}','cargo_geometry',lambda d,f=factor:[c.update({a+'_cm':c[a+'_cm']*f for a in ['l','w','h']}) for c in d['cargo']],description='all box dimensions scaled, mass held independently')
  def dense(d,f=factor):
   for c in d['cargo']:c.update({a+'_cm':c[a+'_cm']*f for a in ['l','w','h']});c['weight_kg']*=f**3
  add(f'fixed_density_{factor}','cargo_geometry',dense,description='all dimensions xfactor and mass xfactor³, constant density')
 for factor in [.5,1.5]:add(f'demand_{factor}','demand',lambda d,f=factor:[c.update(quantity=int(c['quantity']*f)) for c in d['cargo']],description='all counts scaled')
 for factor in [.5,1.5]:add(f'fragile_count_{factor}','demand',lambda d,f=factor:d['cargo'][2].update(quantity=int(d['cargo'][2]['quantity']*f)),description='fragile demand changes; other types fixed')
 for cost in [450,1000]:add(f'T2_cost_{cost}','cost',lambda d,cost=cost:d['vehicles'][1].update(cost_yuan=cost),description='T1 cost450 fixed; T2 cost scenario')
 add('fragile_upright','interpretation',extra={'fragile_upright':True},description='G3 original height40; only floor legal with one-standard full support')
 add('fragile_floor','interpretation',extra={'fragile_floor':True},description='stricter no-elevation scenario')
 add('own_mass_pressure','interpretation',extra={'own_mass':True},description='include parent own mass in each contact pressure')
 save(E/'logs/sensitivity_declaration.json',{'phase_window_seconds':900,'per_run_seconds':120,'memory_target_MB':1800,'seeds':[0,11,23],'alpha':.2,'fragile_priority':3,'same_heuristic_budget':True,'all_scenarios_are_artificial_except_base':True,'scenarios':[{'name':x[0],'group':x[1],'description':x[4]} for x in sc]})
 results=[];calls=[];start=time.perf_counter()
 for name,group,d,cfg,desc in sc:
  for task in ['Q1-S1','Q1-S2','Q2-N','Q2-C']:
   best=None
   for seed in [0,11,23]:
    out=E/f'sensitivity/{name}/{task}/seed{seed}';rows,m=solve(d,task,'maxrect',seed,.2,cfg);write_plan(out,rows,m,cfg,d);v=validate_dir(out);calls.append({'scenario':name,'task':task,'seed':seed,'status':'complete','passed':v['passed'],'runtime_seconds':m['runtime_seconds']})
    if not v['passed']:raise ValueError((name,task,seed,v['errors'][:5]))
    key=(-m['Uv'],-m['Uw']) if task.startswith('Q1-S') else (m['C'],m['N']) if task=='Q2-C' else (m['N'],m['C'])
    if best is None or key<best[0]:best=(key,m,out,v)
   _,m,out,v=best;results.append({'scenario':name,'group':group,'description':desc,'task':task,'seed':m['seed'],'N':m['N'],'n1':m['n1'],'n2':m['n2'],'C':m['C'],'Uv':m['Uv'],'Uw':m['Uw'],'volume_m3':m['volume_m3'],'weight_kg':m['weight_kg'],'max_pressure':max(r['max_pressure_kg_m2'] for r in v['vehicles']),'path':str(out.relative_to(E)),'feasible':True,'optimality':'heuristic candidate, no global claim'})
  print(name,[(r['task'],r['N'],r['C']) for r in results if r['scenario']==name and r['task'].startswith('Q2')],flush=True)
  if time.perf_counter()-start>900:raise TimeoutError('parameter phase resource boundary')
 save(E/'sensitivity/results.json',results);save(E/'logs/sensitivity_calls.json',calls)
 with (E/'sensitivity/results.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
 print('sensitivity calls',len(calls),'elapsed',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
