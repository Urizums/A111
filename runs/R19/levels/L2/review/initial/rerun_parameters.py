from pathlib import Path
import sys,json,csv,datetime,subprocess,time
B=Path.cwd();O=B/'runs/R19/levels/L2/review/initial';sys.path.insert(0,str(O));from audit_frozen import expected,readcsv
from run_reproductions import run
E=B/'runs/R19/levels/L2/execution';cases={r['case']:r for r in readcsv(E/'experiments/experiments.csv')}
selected=['24_baseline','25_fragile_fixed','32_fragile_floor','08_cost_v1','26_quantity','02_vehicle_width','20_pressure','13_cargo_size','35_seed','27_vehicle_height']
for name in selected:
 items,vs,cfg=expected(cases[name]);folder=O/'parameter_inputs'/name;folder.mkdir(parents=True,exist_ok=True)
 rows=[{'item_id':i,'cargo_type':a['cargo'],'category':{'standard':'标准件','fragile':'易碎件','directional':'定向件'}[a['category']],'canonical_l_mm':a['dims'][0],'canonical_w_mm':a['dims'][1],'canonical_h_mm':a['dims'][2],'weight_kg':a['weight'],'source_ref':'reviewer independently derived from official DOCX '+name} for i,a in items.items()]
 with (folder/'items.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 vehicles=[{'type_id':k,'dims':[int(x) for x in a['dims']],'payload_kg':a['payload'],'cost_yuan_per_trip':a['cost'],'clearance_mm':a['clearance'],'source_ref':'reviewer official DOCX + declared perturbation'} for k,a in vs.items()]
 (folder/'vehicles.json').write_text(json.dumps(vehicles,ensure_ascii=False),encoding='utf-8');(folder/'config.json').write_text(json.dumps(cfg,ensure_ascii=False),encoding='utf-8')
 args=['py','-3.12','-X','utf8','-B',str(O/'staged/code/main.py'),'--items',str(folder/'items.csv'),'--vehicles',str(folder/'vehicles.json'),'--config',str(folder/'config.json'),'--scenario','q2_cost','--output',str(O/'parameter_replays_integer'/name)]
 run('parameter_'+name+'_integer_schema',args,B,60)
