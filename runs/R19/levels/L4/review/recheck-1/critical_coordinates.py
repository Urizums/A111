from coordinate_review import *
NEW=ROOT/'runs/R19/levels/L4/execution-v2'; sel=json.loads((NEW/'results/selected.json').read_text(encoding='utf8'));res=[];start=time.perf_counter()
for name,s in sel['scenarios'].items():
    r=check(NEW/s['root'],run_frozen=True);r.update(origin='new_frozen_selected',scenario=name);res.append(r);print(name,r['valid'],r['metrics'],flush=True)
for p in sorted((NEW/'results/selected_single').glob('T*/summary.json')):
    r=check(p.parent,single=True);r.update(origin='new_frozen_single',scenario=p.parent.name);res.append(r)
for name in sel['scenarios']:
    r=check(OUT/'consumer/reviewer_new_run'/name,run_frozen=True);r.update(origin='new_archive_clean_rerun',scenario=name);res.append(r);print('fresh',name,r['valid'],r['metrics'],flush=True)
for p in sorted((OUT/'consumer/reviewer_new_run').glob('Q1_single_*/summary.json')):
    r=check(p.parent,single=True);r.update(origin='new_archive_clean_single',scenario=p.parent.name);res.append(r)
changed=OUT/'controls/solver_valid_changed_inventory'
if changed.exists():
    data=json.loads((changed/'data.json').read_text(encoding='utf8'))
    for name in sel['scenarios']:
        r=check(changed/'run'/name,data=data);r.update(origin='changed_inventory_consumer',scenario=name);res.append(r)
contract=json.loads((OUT/'source-contract.json').read_text(encoding='utf8'));matches=[]
for a,b in zip(BASE['vehicles'],contract['vehicles']):matches.append(a['id']=='T'+b['type_id'] and a['dims']==b['dims_cm'] and a['capacity']==b['capacity_kg'] and a['cost']==b['cost_per_trip_yuan'])
cl={'标准件':'standard','易碎件':'fragile','定向件':'oriented'}
for a,b in zip(BASE['cargo'],contract['cargo']):matches.append(a['id']==b['type_id'] and a['dims']==b['dims_cm'] and a['mass']==b['mass_kg'] and a['quantity']==b['quantity'] and a['class']==cl[b['class']])
def normalize(p):
    rr=list(csv.DictReader((p/'placements.csv').open(encoding='utf-8-sig',newline='')))
    return sorted(tuple(float(r[k]) if k in ['x','y','z','l','w','h'] else r[k] for k in sorted(r)) for r in rr)
comparison=[]
for name,s in sel['scenarios'].items():
    a=NEW/s['root'];b=OUT/'consumer/reviewer_new_run'/name
    ra=next(x for x in res if x['origin']=='new_frozen_selected' and x['scenario']==name);rb=next(x for x in res if x['origin']=='new_archive_clean_rerun' and x['scenario']==name)
    comparison.append({'scenario':name,'raw_csv_byte_equal':(a/'placements.csv').read_bytes()==(b/'placements.csv').read_bytes(),'normalized_full_rows_equal':normalize(a)==normalize(b),'all_metrics_equal':all(close(ra['metrics'][k],rb['metrics'][k]) for k in ra['metrics'])})
out={'results':res,'all_valid':all(r['valid'] for r in res),'all_summary_metrics_match':all(r['all_summary_metrics_match'] for r in res),'source_rebuilt_fields_match_fresh_raw_contract':all(matches),'source_matches':matches,'fresh_comparisons':comparison,'elapsed_seconds':time.perf_counter()-start,'scope':'all frozen selected fleet/singles and all fresh full-route fleet/singles, plus changed inventory four goals; old17 experiments not rerun'}
(OUT/'critical-coordinate-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('ALL',out['all_valid'],out['all_summary_metrics_match'],len(res),flush=True)
