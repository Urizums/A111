from pathlib import Path
import sys,json,time,datetime,collections,itertools,math,importlib.util
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
B=Path.cwd();O=B/'runs/R19/levels/L2/review/initial';E=B/'runs/R19/levels/L2/execution';sys.path.insert(0,str(O));from audit_frozen import ITEMS,V,C,CAT
from independent_checker import validate_layout
patterns=json.loads((E/'results/final/pattern_library.json').read_text(encoding='utf-8'));qty=np.array([CAT[t]['count'] for t in CAT],float);allA=np.array([[sum(r['cargo_type']==t for r in p['placements']) for p in patterns] for t in CAT],float)
records=[]
for name,allowed,primary in [('q1_all_v1',['V1'],'vehicles'),('q1_all_v2',['V2'],'vehicles'),('q2_vehicles',['V1','V2'],'vehicles'),('q2_cost',['V1','V2'],'cost')]:
 indices=[j for j,p in enumerate(patterns) if p['vehicle_type'] in allowed];A=allA[:,indices];cost=np.array([V[patterns[j]['vehicle_type']]['cost'] for j in indices]);ones=np.ones(len(indices));ub=np.array([min(qty[i]/A[i,j] for i in range(len(qty)) if A[i,j]>0) for j in range(len(indices))]);c=ones if primary=='vehicles' else cost;t=time.perf_counter();start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 res=milp(c,integrality=ones,bounds=Bounds(np.zeros(len(indices)),ub),constraints=LinearConstraint(A,qty,qty),options={'time_limit':40,'mip_rel_gap':0})
 rec={'scenario':name,'primary':primary,'status':int(res.status),'message':res.message,'seconds':time.perf_counter()-t,'utc_start':start,'limit_seconds':40,'recomputed_counts_constraint':bool(res.x is not None and np.max(np.abs(A@np.rint(res.x)-qty))<1e-7),'primary_objective':float(c@np.rint(res.x)) if res.x is not None else None,'primary_dual':float(res.mip_dual_bound) if res.x is not None else None,'primary_gap':float(res.mip_gap) if res.x is not None else None}
 if res.status==0:
  # Exact second solve with primary fixed; no epsilon tie-breaking is trusted.
  secondary=cost if primary=='vehicles' else ones;t2=time.perf_counter();s=milp(secondary,integrality=ones,bounds=Bounds(np.zeros(len(indices)),ub),constraints=[LinearConstraint(A,qty,qty),LinearConstraint(c[None,:],rec['primary_objective'],rec['primary_objective'])],options={'time_limit':40,'mip_rel_gap':0})
  rec['secondary']={'status':int(s.status),'seconds':time.perf_counter()-t2,'objective':float(secondary@np.rint(s.x)) if s.x is not None else None,'gap':float(s.mip_gap) if s.x is not None else None}
 records.append(rec);print(json.dumps(rec,ensure_ascii=False),flush=True)
# Independent nondominance calculation over raw-bound counts plus actual 11 alpha constructors,
# then revalidate every additional geometry. Constructor is target; it never supplies truth values.
spec=importlib.util.spec_from_file_location('producer_constructor_target',O/'staged/code/main.py');target=importlib.util.module_from_spec(spec);spec.loader.exec_module(target)
ts=[{'cargo_type':t,'category':{'standard':'标准件','fragile':'易碎件','directional':'定向件'}[a['category']],'dims':list(a['dims']),'weight':a['weight'],'count':a['count']} for t,a in CAT.items()];cfg={'seed':19,'starts':22,'time_limit':60,'pressure':500};front=[]
for vt,v in V.items():
 pv={'type_id':vt,'dims':[int(x) for x in v['dims']],'payload_kg':v['payload'],'cost_yuan_per_trip':v['cost'],'clearance_mm':v['clearance']};pts=[];scanvalid=[]
 for alpha in np.linspace(0,1,11):
  w=np.array([alpha*math.prod(a['dims'])/math.prod(v['dims'])+(1-alpha)*a['weight']/v['payload'] for a in CAT.values()]);p=target.pack(ts,pv,[a['count'] for a in CAT.values()],w,cfg);counters=collections.Counter();rows=[]
  for r in p['placements']:
   t=r['cargo_type'];counters[t]+=1;rows.append({'item_id':f'{t}-{counters[t]:04d}','vehicle_id':'v','cargo':t,'xyz':[r[k] for k in ['x_mm','y_mm','z_mm']],'dims':[r[k] for k in ['dx_mm','dy_mm','dz_mm']]})
  z=validate_layout(ITEMS,{'v':v},rows,full=False,full_support_all=True);scanvalid.append({'alpha':float(alpha),'valid':z['valid'],'counts':[counters[t] for t in CAT]});pts.append(scanvalid[-1]['counts'])
 pts.extend([sum(r['cargo_type']==t for r in p['placements']) for t in CAT] for p in patterns if p['vehicle_type']==vt);pts=list({tuple(p) for p in pts});quant=[(sum(c*math.prod(a['dims']) for c,a in zip(p,CAT.values()))/math.prod(v['dims']),sum(c*a['weight'] for c,a in zip(p,CAT.values()))/v['payload'],p) for p in pts];nd=[p for p in quant if not any(q[0]>=p[0]-1e-10 and q[1]>=p[1]-1e-10 and(q[0]>p[0]+1e-10 or q[1]>p[1]+1e-10) for q in quant)]
 emitted=[tuple(r['counts']) for r in json.loads((E/'results/final/summary.json').read_text(encoding='utf-8'))['singles'] if vt in r['scenario']]
 front.append({'vehicle':vt,'candidate_count_vectors':len(pts),'actual_scanned_layouts':scanvalid,'independently_nondominated':[{'volume':u,'weight':w,'counts':list(p)} for u,w,p in sorted(nd)],'emitted_counts_match':set(p for u,w,p in nd)==set(emitted),'claim_scope':'only tested candidate library/weighted construction, not full Pareto optimality'})
(O/'independent-objective-frontier.json').write_text(json.dumps({'milp':records,'frontier':front,'independence':'A recounted from actual placements, costs/demand original DOCX, primary/secondary separate exact solve; constructors used only as target for candidate generation'},ensure_ascii=False,indent=2),encoding='utf-8');print('Objective/frontier audit finished',flush=True)
