from independent_audit import raw_config,EXEC,OUT
import json,time
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
cfg=raw_config();pool=json.loads((EXEC/'results/final/pattern_pool.json').read_text(encoding='utf-8'))
A=np.array([[sum(i['type_id']==c['id'] for i in p['items']) for p in pool] for c in cfg['cargo']],dtype=float);q=np.array([c['quantity'] for c in cfg['cargo']]);v={v['id']:v for v in cfg['vehicles']};cost=np.array([v[p['vehicle_type']]['cost'] for p in pool])
own=json.loads((OUT/'frozen-final-independent-audit.json').read_text(encoding='utf-8'));upper=min(r['metrics']['cost'] for r in own['reports'] if r['complete'] and r['valid'])
tic=time.perf_counter();r=milp(cost,integrality=np.ones(len(pool)),bounds=Bounds(np.zeros(len(pool)),np.full(len(pool),np.inf)),constraints=[LinearConstraint(A,q,q),LinearConstraint(cost,-np.inf,upper)],options={'time_limit':60,'mip_rel_gap':0})
n=None if r.x is None else np.rint(r.x).astype(int)
report={'status':int(r.status),'message':r.message,'seconds':time.perf_counter()-tic,'limit_seconds':60,'known_feasible_upper':upper,'upper_source':'own raw/frozen-final layout audit, not author certificate','objective':None if n is None else float(cost@n),'dual_bound':getattr(r,'mip_dual_bound',None),'gap':getattr(r,'mip_gap',None),'integer_counts_match':None if n is None else bool(np.array_equal(A@n,q)),'pattern_multiplicities':None if n is None else [{'pattern':int(i),'multiplicity':int(n[i])} for i in np.flatnonzero(n)],'previous_uncut_attempt':'independent-bounds-pool.json retains original 60s unresolved cost attempt','claim_limit':'only finite original 99-pattern pool'}
(OUT/'independent-pool-cost-cut.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
