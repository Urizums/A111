from pathlib import Path
import sys,json,csv,collections,math,itertools,datetime,time
B=Path.cwd();O=B/'runs/R19/levels/L2/review/initial';E=B/'runs/R19/levels/L2/execution';sys.path.insert(0,str(O))
from audit_frozen import ITEMS,V,C,readcsv,audit,expected
from independent_checker import validate_layout
records=[];comparisons=[]
for group in ['baseline','selected','single']:
 for f in sorted((O/'staged/results/final'/group).iterdir()):
  if not f.is_dir():continue
  z=audit(f,ITEMS,V,C,group!='single');records.append(z);old=E/'results/final'/group/f.name
  comparisons.append({'scenario':str(f.relative_to(O/'staged/results/final')),'placements_bytes_equal':(f/'placements.csv').read_bytes()==(old/'placements.csv').read_bytes(),'semantic_metrics_equal':{k:json.loads((old/'run.json').read_text(encoding='utf-8-sig'))[k]==z['metrics'][k] for k in ['vehicle_count','cost_yuan','volume_utilization','weight_utilization']}})
zi={r['item_id']:ITEMS[r['item_id']] for r in readcsv(O/'zip_staged/data/smoke_items.csv')};zv=json.loads((O/'zip_staged/data/vehicles.json').read_text(encoding='utf-8-sig'));zipcheck=audit(O/'zip_staged/reviewer_smoke',zi,V,C,True)
P=json.loads((E/'results/final/pattern_library.json').read_text(encoding='utf-8-sig'));patterns=[]
for ix,p in enumerate(P):
 counters=collections.Counter();rows=[];errors=[]
 for r in p['placements']:
  t=r['cargo_type'];counters[t]+=1;i=f'{t}-{counters[t]:04d}';rows.append({'item_id':i,'vehicle_id':'v','xyz':[r[k] for k in ['x_mm','y_mm','z_mm']],'dims':[r[k] for k in ['dx_mm','dy_mm','dz_mm']],'cargo':t})
  a=ITEMS.get(i)
  if not a:errors.append('pattern exceeds inventory')
  elif [a['dims'][int(k)] for k in r['orientation_id']]!=rows[-1]['dims']:errors.append('orientation mapping')
 z=validate_layout(ITEMS,{'v':V[p['vehicle_type']]},rows,full=False,full_support_all=True)
 expected_counts=[counters[t] for t in ['G1','G2','G3','G4','G5']]
 if expected_counts!=p['counts']:errors.append('counts vector')
 patterns.append({'pattern':ix,'vehicle_type':p['vehicle_type'],'items':len(rows),'valid':z['valid'] and not errors,'errors':z['errors'][:3]+errors,'counts':expected_counts})
report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reproduced_layouts':records,'comparisons':comparisons,'zip_smoke':zipcheck,'patterns':patterns,'pattern_count':len(patterns),'all_patterns_valid':all(x['valid'] for x in patterns)}
(O/'reproduction-independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'reproduced_layouts':len(records),'all_valid':all(x['valid'] for x in records),'all_placements_equal':all(x['placements_bytes_equal'] for x in comparisons),'zip_valid':zipcheck['valid'],'patterns':len(patterns),'all_patterns_valid':report['all_patterns_valid']},ensure_ascii=False),flush=True)
