from pathlib import Path
import sys,json,csv
from run_calls import run,dump,B,O,E
from audit_independent import a,ITEMS,VS
Z=O/'zip_staged'
if __name__=='__main__':
 for method in ('A','B'):
  cfg={'seed':19,'starts':22,'time_limit':45,'pressure':500,'geometry':method,'platforms':method!='A'};p=O/('config_'+method+'.json');dump(p,cfg)
  run('method_'+method+'_seed19',[sys.executable,'-X','utf8','-B',str(Z/'code/main.py'),'--items',str(Z/'data/items.csv'),'--vehicles',str(Z/'data/vehicles.json'),'--config',str(p),'--output',str(O/'method_replay'/method)],300)
 cases={r['case']:r for r in a.readcsv(E/'experiments/experiments.csv')}
 for case in ('24_baseline','25_fragile_fixed','32_fragile_floor','20_pressure','13_cargo_size','35_seed','27_vehicle_height'):
  c=cases[case];items,vs,cfg=a.expected(c);cfg['geometry']='C'
  if c['parameter']=='fragile_floor':cfg['fragile_floor']=True
  d=O/'parameter_inputs'/case;d.mkdir(parents=True,exist_ok=True)
  cmap={'standard':'标准件','fragile':'易碎件','directional':'定向件'}
  rows=[{'item_id':k,'cargo_type':i['cargo'],'category':cmap[i['category']],'canonical_l_mm':int(i['dims'][0]),'canonical_w_mm':int(i['dims'][1]),'canonical_h_mm':int(i['dims'][2]),'weight_kg':i['weight']} for k,i in items.items()]
  with (d/'items.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
  dump(d/'vehicles.json',[{'type_id':k,'dims':list(map(int,v['dims'])),'payload_kg':v['payload'],'cost_yuan_per_trip':v['cost'],'clearance_mm':v['clearance']} for k,v in vs.items()]);dump(d/'config.json',cfg)
  run('parameter_'+case,[sys.executable,'-X','utf8','-B',str(Z/'code/main.py'),'--items',str(d/'items.csv'),'--vehicles',str(d/'vehicles.json'),'--config',str(d/'config.json'),'--scenario','q2_cost','--output',str(O/'parameter_replay'/case)],120)
