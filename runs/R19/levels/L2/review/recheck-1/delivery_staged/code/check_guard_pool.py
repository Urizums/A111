"""Reconcile unchanged nine postprocessors with final shared-pool correction."""
import json,time
import main
from guard_comparison import rows_to_fleet
R=main.ROOT;items=main.readitems(R/'data/items.csv');types=main.typesfrom(items);cs=[t['count'] for t in types];vs=json.loads((R/'data/vehicles.json').read_text());records=[];start=time.perf_counter()
for a in json.loads((R/'research/comparison/guarded_summary.json').read_text()):
 d=R/'research/comparison'/a['case'];fs=json.loads((d/'guarded/generated_fleets.json').read_text());candidates=fs+[rows_to_fleet(d/'selected'/n,types) for n in ['q1_all_v1','q1_all_v2','q2_vehicles','q2_cost']]
 for name,vv,obj in [('q1_all_v1',[vs[0]],'vehicles'),('q1_all_v2',[vs[1]],'vehicles'),('q2_vehicles',vs,'vehicles'),('q2_cost',vs,'cost')]:
  f,identity=main.best_known(candidates,vv,cs,obj);r=json.loads((d/'guarded/selected'/name/'run.json').read_text());lookup={v['type_id']:v for v in vv};cost=sum(lookup[p['vehicle_type']]['cost_yuan_per_trip'] for p in f)
  assert len(f)==r['vehicle_count'] and cost==r['cost_yuan']
  records.append({'case':a['case'],'scenario':name,'candidates_include_all_four_raw_selected':True,'all_generated_fleets_retained':True,'current_best_known_matches_saved_guard':True,'vehicles':len(f),'cost':cost})
main.dump(R/'checks/guard_pool_reconciliation.json',{'records':records,'seconds':time.perf_counter()-start,'why_unaffected':'postprocessor pooled every raw selected fleet before evaluating any objective; it never called select or discarded raw incumbent. Only first main.solve serial select needed correction.'})
print('36 guard objective pool reconciliations passed')
