import json, math
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[5]; out=Path(__file__).resolve().parent
problem=json.loads((root/'runs/R14/cases/math/problem.json').read_text(encoding='utf-8'))
r=json.loads((out/'results.json').read_text(encoding='utf-8')); d=problem['distribution']; stations=['A','B','C']; hist=problem['data']
expected={}
for s in stations:
 x=np.arange(1,len(hist)+1,dtype=float); y=np.array([row[s] for row in hist],dtype=float)
 expected[s]=float(np.polyval(np.polyfit(x,y,1),9))
pred=r['prediction']['values']
forecast_ok=all(math.isclose(pred[s],expected[s],rel_tol=0,abs_tol=1e-10) for s in stations)
# Independent exhaustive optimal value
best=float('inf'); bx=None
for a in range(d['station_caps']['A']+1):
 for b in range(d['station_caps']['B']+1):
  for c in range(d['station_caps']['C']+1):
   if a+b+c>d['total_available_units']: continue
   xs={'A':a,'B':b,'C':c}
   val=sum(d['delivery_cost_per_unit'][s]*xs[s]+d['unmet_prediction_penalty_per_unit'][s]*max(expected[s]-xs[s],0) for s in stations)
   if val<best-1e-10: best,bx=val,xs
allocation_ok=r['allocation']==bx and math.isclose(r['objective']['value_CNY'],best,abs_tol=1e-9)
constraints_ok=sum(r['allocation'].values())<=d['total_available_units'] and all(0<=r['allocation'][s]<=d['station_caps'][s] and isinstance(r['allocation'][s],int) for s in stations)
checks={'forecast_matches_raw_recompute':forecast_ok,'exhaustive_allocation_and_objective_match':allocation_ok,'integer_and_capacity_checks':constraints_ok,'figure_exists':(out/'demand_allocation.png').is_file()}
print(json.dumps({'checks':checks,'expected_forecasts':expected,'best_allocation':bx,'best_objective_CNY':best},indent=2))
if not all(checks.values()): raise SystemExit(1)
