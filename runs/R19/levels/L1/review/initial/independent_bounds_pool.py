from independent_audit import raw_config,audit,EXEC,OUT
import json,math,time,collections
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
def main():
    cfg=raw_config();V=sum(math.prod(c['dims'])*c['quantity'] for c in cfg['cargo']);W=sum(c['weight']*c['quantity'] for c in cfg['cargo']);fa=sum(c['dims'][0]*c['dims'][1]*c['quantity'] for c in cfg['cargo'] if c['category']=='fragile')
    density=max(c['weight']/(math.prod(c['dims'])/1e6) for c in cfg['cargo'])
    bounds={v['id']:{'volume_vehicle_lb':math.ceil(V/(v['dims'][0]*v['dims'][1]*(v['dims'][2]-cfg['clearance']))),'payload_vehicle_lb':math.ceil(W/v['payload']),'fragile_area_vehicle_lb':math.ceil(fa/(v['dims'][0]*v['dims'][1])),'single_load_rate_upper':density*(v['dims'][0]*v['dims'][1]*(v['dims'][2]-cfg['clearance'])/1e6)/v['payload']} for v in cfg['vehicles']}
    relaxed=[]
    for n1 in range(31):
        for n2 in range(31):
            ns=[n1,n2]
            if sum(n*v['dims'][0]*v['dims'][1]*(v['dims'][2]-cfg['clearance']) for n,v in zip(ns,cfg['vehicles']))+1e-6<V:continue
            if sum(n*v['payload'] for n,v in zip(ns,cfg['vehicles']))+1e-6<W:continue
            if sum(n*v['dims'][0]*v['dims'][1] for n,v in zip(ns,cfg['vehicles']))+1e-6<fa:continue
            relaxed.append({'n1':n1,'n2':n2,'N':sum(ns),'C':sum(n*v['cost'] for n,v in zip(ns,cfg['vehicles']))})
    costbest=min(relaxed,key=lambda x:(x['C'],x['N']));countbest=min(relaxed,key=lambda x:(x['N'],x['C']))
    # This enumeration is sufficient for the minimum: n1>30 already costs>9000;
    # n2>30 costs>21000, both above the constructed relaxation feasible candidate.
    pool=json.loads((EXEC/'results/final/pattern_pool.json').read_text(encoding='utf-8'));poolchecks=[]
    for k,p in enumerate(pool):
        pp=dict(p);pp['truck_id']='review-pattern'
        r,_=audit({'fleet':[pp]},f'pattern-{k}',False,cfg);poolchecks.append({'pattern':k,'valid':r['valid'],'violations':r['violations']})
    A=np.array([[sum(i['type_id']==c['id'] for i in p['items']) for p in pool] for c in cfg['cargo']],dtype=float)
    q=np.array([c['quantity'] for c in cfg['cargo']],dtype=float);vs={v['id']:v for v in cfg['vehicles']};cs=np.array([vs[p['vehicle_type']]['cost'] for p in pool]);masters={}
    for label,cost in [('count',np.ones(len(pool))),('cost',cs)]:
        tic=time.perf_counter();r=milp(cost,integrality=np.ones(len(pool)),bounds=Bounds(np.zeros(len(pool)),np.full(len(pool),np.inf)),constraints=LinearConstraint(A,q,q),options={'time_limit':60,'mip_rel_gap':0})
        n=None if r.x is None else np.rint(r.x).astype(int)
        masters[label]={'status':int(r.status),'message':r.message,'seconds':time.perf_counter()-tic,'limit_seconds':60,'objective':None if n is None else float(cost@n),'dual_bound':getattr(r,'mip_dual_bound',None),'gap':getattr(r,'mip_gap',None),'integer_counts_match':None if n is None else bool(np.array_equal(A@n,q)),'pattern_multiplicities':None if n is None else [{'pattern':int(i),'multiplicity':int(n[i])} for i in np.flatnonzero(n)],'source':'independent count matrix and SciPy MILP, no author patterns_master/check imported'}
    result={'raw_V_cm3':V,'raw_W_kg':W,'fragile_floor_projection_cm2':fa,'maximum_density_kg_m3':density,'fixed_bounds':bounds,'relaxation_count_min':countbest,'relaxation_cost_min':costbest,'pool_size':len(pool),'all_patterns_independently_feasible':all(x['valid'] for x in poolchecks),'pattern_checks':poolchecks,'independent_restricted_pool_masters':masters,'claim_limit':'integer proof only for this finite pool; no original continuous geometry optimality claim'}
    (OUT/'independent-bounds-pool.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['fixed_bounds','relaxation_count_min','relaxation_cost_min','pool_size','all_patterns_independently_feasible','independent_restricted_pool_masters']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
