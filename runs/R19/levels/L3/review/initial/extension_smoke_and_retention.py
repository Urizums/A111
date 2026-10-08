import json,csv,math,re,itertools,copy,hashlib,shutil,subprocess,sys
from pathlib import Path
from independent_review import H,E,review,read_rows,catalogue
import independent_checker as ic
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(name,value):(H/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
audit=load(H/'independent-source-audit.json');sheets={s['sheet']:{c['address']:c['value'] for c in s['cells']} for s in audit['xlsx']}
def interval(value,scale):
 if value is None:return None
 values=[float(v) for v in re.findall(r'\d+(?:\.\d+)?',str(value))]
 return [scale*values[0],scale*values[1] if len(values)>1 else scale*values[0]]
products=[];trucks=[]
for i in range(3,11):
 cell=sheets['箱装产品尺寸'];wh=[interval(cell.get(a+str(i)),.1) for a in 'CEG'];lab=[interval(cell.get(a+str(i)),.1) for a in 'BDF']
 products.append({'row':i,'warehouse':wh,'laboratory':lab,'upper':[v[1] for v in wh]})
for i in range(7,12):
 cell=sheets['车型尺寸'];ds=[interval(cell.get(a+str(i)),100) for a in 'BCD'];trucks.append({'row':i,'interval':ds,'lower':[v[0] for v in ds],'fee':cell.get('E'+str(i))})
official=load(E/'extension/attachment2_normalized.json');errors=[]
for got in official['products']:
 truth=next(x for x in products if x['row']==got['row'])
 if got['warehouse_interval_cm']!=truth['warehouse'] or got['lab_interval_cm']!=truth['laboratory'] or got['upper_cm']!=truth['upper'] or any(got[x] is not None for x in ['weight_kg','quantity','category']):errors.append(('product',got['row']))
for got in official['vehicles']:
 truth=next(x for x in trucks if x['row']==got['row'])
 if got['interval_cm']!=truth['interval'] or got['robust_cm']!=truth['lower'] or got['cost_raw']!=truth['fee'] or got['capacity_kg'] is not None or got['cost_unit']!='yuan/1000km':errors.append(('truck',got['row']))
fits=[]
for p in products:
 for v in trucks:
  allowed=list(v['lower']);allowed[2]-=3;can=any(all(x<=y for x,y in zip(d,allowed)) for d in set(itertools.permutations(p['upper'])))
  matches=[f for f in official['fits'] if f['product_row']==p['row'] and f['vehicle_row']==v['row']]
  if len(matches)!=1 or matches[0]['fits']!=can:errors.append(('fit',p['row'],v['row']))
  fits.append({'product_row':p['row'],'truck_row':v['row'],'fits_under_stated_artificial_orientation':can})
smoke=review(H/'sandbox/smoke/valid','Q1-F1',scenario=True);assert smoke['independent_pass_under_declared_model']
raw,rows=read_rows(H/'sandbox/smoke/valid');cfg=load(H/'sandbox/smoke/valid/config.json');cat=catalogue(cfg['instance']);ic.source_catalog=lambda:cat
bad=copy.deepcopy(rows);bad[0]['x']=9999;b=ic.check(bad,full_batch=True,fragile_support='single');pressure=ic.check(rows,full_batch=True,fragile_support='single',pressure_limit=1)
assert not b['valid_under_declared_model'] and any(v['code']=='bounds_or_clearance' for v in b['violations'])
assert not pressure['valid_under_declared_model'] and any(v['code']=='cumulative_pressure' for v in pressure['violations'])
assert any(r['cargo_type']=='G3' and r['support_ids'] for r in raw)
save('smoke-independent.json',{'valid':smoke,'invalid_boundary':b,'artificial_pressure1':pressure,'fragile_on_standard_observed':True,'scope':'28-source-dimension small batch only; separate from full acceptance'})
save('extension-independent.json',{'products':products,'enclosed_road_vehicles':trucks,'fits':fits,'errors':errors,'source':'direct raw XLSX re-read','scope':'40 single-item geometric fit checks only, no official complete transportation batch or broad algorithm generality'});assert not errors
prep=H.parent/'preparation';m=load(prep/'preparation-manifest.json');matches=[]
for row in m['files']:
 p=prep/row['path'];matches.append(hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'])
assert all(matches)
shutil.copy2(prep/'run_method_controls.py',H/'run_method_controls.py')
child=subprocess.run([sys.executable,'-X','utf8','-B',str(H/'run_method_controls.py')],capture_output=True,text=True,encoding='utf-8',timeout=60)
assert child.returncode==0
retention={'prepared_payload_hashes_unchanged':all(matches),'prepared_payload_count':len(matches),'adapted_checker_controls_rerun_exit':child.returncode,'adapted_controls_stdout':child.stdout,
           'producer_history_gap':{'source':'execution/logs/failures.json boundary-retention; logs/invocations.json first three subprocess entries','observed':'first boundary summary overwritten, original first three PIDs/stdout unavailable; known counts/status transcribed with null IDs, not retrospectively reconstructed by this reviewer'},
           'resource_deviations':{'source':'execution/logs/resource_final.json and failures.json','declared_peak_solver_processes':1,'reported_actual_peak':2,'reported_deviations':2,'scope':'historical full-task peak/missing call details cannot be independently observed now; no altered history or whole-task two-error stop'},
           'reviewer_overlap':{'observation':'Shared-selection script session21738 returned pending before audit session80015 started; own copied sensitivity/results read only after 168-candidate audit; both reconciled exit0 before further solvers','scope':'known check/selection overlap, not repeated unknown invocation; no original production writes; not used for timing fairness claims'},
           'pending_calls':[],'model':None,'token':None,'cost':None}
save('retention-and-method-check.json',retention)
print(json.dumps({'attachment2_fits':len(fits),'data_errors':errors,'smoke_independent':True,'prepared_hashes_unchanged':True,'adapted_control_rerun':child.stdout.strip()},ensure_ascii=False))
