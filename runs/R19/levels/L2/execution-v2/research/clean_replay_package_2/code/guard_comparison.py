"""Same correction to all methods; does not repeat MILP or hide raw outputs."""
from pathlib import Path
import json,time,datetime,hashlib
import main,blocks
ROOT=main.ROOT
def rows_to_fleet(folder,types):
 import csv,collections
 with (folder/'placements.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 groups=collections.defaultdict(list)
 for r in rows:
  p={k:r[k] for k in ['cargo_type','orientation_id']}
  for k in ['x_mm','y_mm','z_mm','dx_mm','dy_mm','dz_mm']:p[k]=int(r[k])
  groups[(r['vehicle_id'],r['vehicle_type'])].append(p)
 return [{'vehicle_type':v,'counts':[sum(p['cargo_type']==t['cargo_type'] for p in parts) for t in types],'placements':parts} for (_,v),parts in groups.items()]
if __name__=='__main__':
 items=main.readitems(ROOT/'data/items.csv');types=main.typesfrom(items);counts=[t['count'] for t in types];vs=json.loads((ROOT/'data/vehicles.json').read_text());rows=[]
 for rawrow in json.loads((ROOT/'research/comparison/summary.json').read_text()):
  d=ROOT/'research/comparison'/rawrow['case'];cfg=json.loads((d/'config.json').read_text());out=d/'guarded';start=time.perf_counter();utc=datetime.datetime.now(datetime.timezone.utc).isoformat();blocks.CACHE.clear();blocks.CERTIFICATES.clear()
  ps,fs=main.library(types,vs,counts,cfg);old=json.loads((d/'pattern_library.json').read_text());assert ps==old,'regeneration changed geometry; refuse silently relabel'
  main.dump(out/'generated_fleets.json',fs)
  rawS=json.loads((d/'summary.json').read_text());candidates=fs+[rows_to_fleet(d/'selected'/n,types) for n in ['q1_all_v1','q1_all_v2','q2_vehicles','q2_cost']];runs=[]
  for name,vv,obj in [('q1_all_v1',[vs[0]],'vehicles'),('q1_all_v2',[vs[1]],'vehicles'),('q2_vehicles',vs,'vehicles'),('q2_cost',vs,'cost')]:
   f,identity=main.best_known(candidates,vv,counts,obj);rawr=next(r for r in rawS['runs'] if r['scenario']==name and r['method']=='column_patterns_MILP')
   rr=main.export(f,types,vv,items,out/'selected'/name,name,{**{k:rawr[k] for k in ['method','objective','bounds','config','solver']},'candidate_guard':{'selected_candidate_index':identity,'raw_vehicles':rawr['vehicle_count'],'raw_cost':rawr['cost_yuan'],'raw_solver_status_preserved':True}});runs.append(rr)
  seconds=time.perf_counter()-start;summary={**rawS,'runs':[r for r in rawS['runs'] if r['method']=='equal_priority_columns']+runs,'seconds':rawS['seconds']+seconds,'initial_call_seconds':rawS['seconds'],'guard_seconds':seconds,'utc_guard_start':utc,'utc_guard_finish':datetime.datetime.now(datetime.timezone.utc).isoformat()};main.dump(out/'summary.json',summary);main.dump(out/'block_certificates.json',blocks.CERTIFICATES)
  row={**rawrow,'guard_outer_seconds':seconds,'total_outer_seconds':rawrow['outer_seconds']+seconds}
  for r in runs:row[r['scenario']+'_vehicles']=r['vehicle_count'];row[r['scenario']+'_cost']=r['cost_yuan']
  rows.append(row);main.dump(ROOT/'research/comparison/guarded_progress.json',rows);print(json.dumps(row),flush=True)
 main.dump(ROOT/'research/comparison/guarded_summary.json',rows)
