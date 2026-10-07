from pathlib import Path
import sys,copy,json,itertools,importlib.util,csv,subprocess,datetime
B=Path.cwd();O=B/'runs/R19/levels/L2/review/initial';P=B/'runs/R19/levels/L2/review/preparation';sys.path.insert(0,str(P))
ns={'__file__':str(O/'controlled_inputs.py')};src=(P/'check_method_controls.py').read_text(encoding='utf-8-sig');exec(src.split('results=[]')[0],ns)
spec=importlib.util.spec_from_file_location('producer_validation_target',O/'staged/code/validate.py');target=importlib.util.module_from_spec(spec);spec.loader.exec_module(target)
results=[];fixtures={};cmap={'standard':'标准件','fragile':'易碎件','directional':'定向件'}
for name,it,ps,want,rule,opts in ns['C']:
 items=[{'item_id':k,'cargo_type':a['cargo'],'category':cmap[a['category']],'canonical_l_mm':a['dims'][0],'canonical_w_mm':a['dims'][1],'canonical_h_mm':a['dims'][2],'weight_kg':a['weight'],'source_ref':'reviewer synthetic control'} for k,a in it.items()]
 vehicles=[{'type_id':'V1','dims':[1000,1000,1000],'clearance_mm':30,'payload_kg':10000,'cost_yuan_per_trip':450}];rows=[]
 for p in ps:
  a=it[p['item_id']];ori=next((''.join(map(str,q)) for q in itertools.permutations(range(3)) if [a['dims'][k] for k in q]==p['dims']),'999')
  rows.append({'vehicle_id':'T001','vehicle_type':'V1','item_id':p['item_id'],'cargo_type':a['cargo'],'x_mm':p['xyz'][0],'y_mm':p['xyz'][1],'z_mm':p['xyz'][2],'dx_mm':p['dims'][0],'dy_mm':p['dims'][1],'dz_mm':p['dims'][2],'orientation_id':ori})
 try:
  z=target.validate(rows,items,vehicles,full=opts.get('full',True),fragile_fixed=opts.get('fragile_fixed',False));passed=z['valid']==want;error=None
 except Exception as e:z=None;passed=not want;error=type(e).__name__+': '+str(e)
 results.append({'case':name,'expected_valid':want,'target_valid':z['valid'] if z else None,'passed':passed,'target_errors':z['errors'] if z else [],'exception':error,'scope':'producer validator run on reviewer analytical input, not used as oracle'});fixtures[name]=(items,vehicles,rows,opts,want)
cli=[]
for name in ['legal_contact_pressure_equality','reject_cumulative_chain_not_only_direct_load','reject_missing_weight']:
 it,v,rows,opts,want=fixtures[name];f=O/'control_inputs'/name;f.mkdir(parents=True,exist_ok=True)
 for fn,data in [('items.csv',it),('placements.csv',rows)]:
  with (f/fn).open('w',encoding='utf-8-sig',newline='') as fh:w=csv.DictWriter(fh,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 (f/'vehicles.json').write_text(json.dumps(v),encoding='utf-8')
 argv=['py','-3.12','-X','utf8','-B',str(O/'staged/code/validate.py'),'--placements',str(f/'placements.csv'),'--items',str(f/'items.csv'),'--vehicles',str(f/'vehicles.json'),'--output',str(f/'actual.json')];p=subprocess.run(argv,cwd=B,capture_output=True,text=True,encoding='utf-8',timeout=20)
 (f/'stdout.txt').write_text(p.stdout+p.stderr,encoding='utf-8');cli.append({'case':name,'argv':argv,'exit_code':p.returncode,'expected_valid':want,'correct_code':p.returncode==(0 if want else 2),'actual':json.loads((f/'actual.json').read_text(encoding='utf-8'))})
# Source-based small oracle: at least one vehicle for nonempty 15-source-item subset, one feasible V1 at450=>optimal count1/cost450.
allpassed=all(r['passed'] for r in results) and all(r['correct_code'] for r in cli)
(O/'producer-checker-controls.json').write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'analytical_cases':results,'cli_controls':cli,'all_passed':allpassed,'target_not_oracle':True,'small_oracle_proof':'nonempty items requires >=1 vehicle; all costs >=450/trip; zip15 layout independently feasible in V1 gives count1/cost450 achieving both lower bounds'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'controls':len(results),'all_passed':allpassed,'failed':[r['case'] for r in results if not r['passed']],'cli_codes':[{k:r[k] for k in ['case','exit_code','correct_code']} for r in cli]},ensure_ascii=False))
