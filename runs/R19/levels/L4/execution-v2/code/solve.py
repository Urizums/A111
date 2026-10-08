"""Offline column construction, 2D shelf/MaxRects, verified pattern MILP."""
import argparse,json,csv,time,itertools,math,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import csc_matrix
from validator import validate
from numeric_contract import input_errors,InvalidInputError,InfeasibleInputError

def orientations(g,config):
    if g['class']=='oriented':return [(tuple(g['dims']),'LWH')]
    permutations=list(itertools.permutations(range(3))); result={}
    for p in permutations:
        d=tuple(g['dims'][i] for i in p)
        if g['class']=='fragile' and config.get('fragile_orientation')=='original_height' and d[2]!=g['dims'][2]:continue
        result.setdefault(d,''.join('LWH'[i] for i in p))
    return list(result.items())

def columns(instance,v,config):
    gs=instance['cargo']; height=v['dims'][2]-config['gap_cm']; pressure=config['pressure_kg_m2'];options=[];seen=set()
    os=[[(i,d,o) for d,o in orientations(g,config)] for i,g in enumerate(gs)]
    def add(seq):
        key=tuple((i,d) for i,d,o in seq)
        if key in seen:return
        seen.add(key)
        z=sum(d[2] for i,d,o in seq)
        if z>height:return
        above=0
        for k in range(len(seq)-1,-1,-1):
            i,d,o=seq[k]
            if above>pressure*d[0]*d[1]/10000+1e-9:return
            if k and above+gs[i]['mass']>pressure*d[0]*d[1]/10000+1e-9:return
            above+=gs[i]['mass']
        count=np.bincount([i for i,d,o in seq],minlength=len(gs))
        if any(count[i]>gs[i]['quantity'] for i in range(len(gs))):return
        options.append({'seq':seq,'l':seq[0][1][0],'w':seq[0][1][1],'height':z,'counts':count,'mass':sum(gs[i]['mass'] for i,d,o in seq),'volume':sum(math.prod(d) for i,d,o in seq)})
    for i,g in enumerate(gs):
        for lower in os[i]:
            d=lower[1];maxn=min(int(height//d[2]),g['quantity'],1 if g['class']=='fragile' else 100)
            for n in range(1,maxn+1):
                add([lower]*n)
                if g['class']=='fragile':continue
                for j,gg in enumerate(gs):
                    if gg['class']=='fragile' and g['class']!='standard':continue
                    for upper in os[j]:
                        du=upper[1]
                        if du[0]>d[0] or du[1]>d[1]:continue
                        maxu=min(int((height-n*d[2])//du[2]),gg['quantity'],1 if gg['class']=='fragile' else 100)
                        for m in range(1,maxu+1):add([lower]*n+[upper]*m)
    return options

def split_free(free,box):
    x,y,l,w=box;out=[]
    for fx,fy,fl,fw in free:
        if x>=fx+fl or x+l<=fx or y>=fy+fw or y+w<=fy:out.append((fx,fy,fl,fw));continue
        if x>fx:out.append((fx,fy,x-fx,fw))
        if x+l<fx+fl:out.append((x+l,fy,fx+fl-x-l,fw))
        if y>fy:out.append((fx,fy,fl,y-fy))
        if y+w<fy+fw:out.append((fx,y+w,fl,fy+fw-y-w))
    unique=list(dict.fromkeys(out));return [r for i,r in enumerate(unique) if not any(i!=j and r[0]>=s[0] and r[1]>=s[1] and r[0]+r[2]<=s[0]+s[2] and r[1]+r[3]<=s[1]+s[3] for j,s in enumerate(unique))]

def pack(instance,v,config,options,available,weights,method='maxrects',seed=0):
    # A column occupies one floor rectangle and all vertical load is on one full support.
    gs=instance['cargo'];left=np.array(available,dtype=int).copy();counts=np.array([c['counts'] for c in options]);ls=np.array([c['l'] for c in options]);ws=np.array([c['w'] for c in options]);mass=np.array([c['mass'] for c in options]);volume=np.array([c['volume'] for c in options]);height=np.array([c['height'] for c in options])
    rng=np.random.default_rng(seed);value=counts@np.array(weights);base=value/(ls*ws);noise=rng.uniform(.96,1.04,len(options)) if method=='improved' else np.ones(len(options));base*=noise
    free=[(0,0,v['dims'][0],v['dims'][1])];chosen=[];totalmass=0; shelf_x=shelf_y=shelf_h=0
    while True:
        feasible=np.all(counts<=left,axis=1)&(mass+totalmass<=v['capacity']+1e-9)
        if not feasible.any():break
        best=None
        if method=='shelf':
            # first row fit, deterministic preference for vertical fill then objective density
            for newrow in [False,True]:
                x=0 if newrow else shelf_x;y=shelf_y+shelf_h if newrow else shelf_y
                fits=feasible&(ls<=v['dims'][0]-x)&(ws<=v['dims'][1]-y)
                if not newrow and shelf_x and shelf_h:fits&=ws<=shelf_h
                if fits.any():
                    ids=np.flatnonzero(fits);ci=int(ids[np.argmax(base[ids])]);best=(ci,x,y,newrow);break
        else:
            for fx,fy,fl,fw in free:
                ids=np.flatnonzero(feasible&(ls<=fl)&(ws<=fw))
                if not len(ids):continue
                score=base[ids]*(1+.035*(ls[ids]/fl+ws[ids]/fw))
                ci=int(ids[np.argmax(score)]);s=float(score.max())
                if best is None or s>best[0]:best=(s,ci,fx,fy)
        if best is None:break
        if method=='shelf':
            ci,x,y,nr=best
            if nr:shelf_y=y;shelf_h=0
            shelf_x=x+ls[ci];shelf_h=max(shelf_h,ws[ci])
        else:
            score,ci,x,y=best;free=split_free(free,(x,y,float(ls[ci]),float(ws[ci])))
        chosen.append((float(x),float(y),ci));left-=counts[ci];totalmass+=mass[ci]
    rows=[];ct=np.zeros(len(gs),dtype=int)
    for colid,(x,y,ci) in enumerate(chosen):
        z=0;parent='FLOOR'
        for i,d,ori in options[ci]['seq']:
            ct[i]+=1;identity=f'{gs[i]["id"]}-{ct[i]:04d}'
            rows.append({'truck_id':'TR0001','vehicle_type':v['id'],'item_id':identity,'cargo_type':gs[i]['id'],'x':x,'y':y,'z':z,'l':d[0],'w':d[1],'h':d[2],'orientation':ori,'support_ids':parent,'column_id':colid});parent=identity;z+=d[2]
    return {'vehicle_type':v['id'],'counts':(np.array(available)-left).tolist(),'rows':rows,'volume':sum(math.prod([r[k] for k in ['l','w','h']]) for r in rows),'mass':float(totalmass),'method':method,'seed':seed}

def greedy(instance,config,allowed,options,method,weights,seed=0):
    left=np.array([g['quantity'] for g in instance['cargo']]);patterns=[]
    while left.sum():
        choices=[pack(instance,v,config,options[v['id']],left,weights,method,seed+len(patterns)) for v in allowed]
        p=max(choices,key=lambda p:p['volume'])
        if not sum(p['counts']):raise ValueError('No feasible new vehicle for remaining inventory')
        patterns.append(p);left-=p['counts']
    return patterns

def instantiate(instance,patterns):
    running=Counter();rows=[]
    for ti,p in enumerate(patterns,1):
        mapping={}
        for r in p['rows']:
            running[r['cargo_type']]+=1;mapping[r['item_id']]=f'{r["cargo_type"]}-{running[r["cargo_type"]]:04d}'
        for r in p['rows']:
            nr=dict(r);nr['truck_id']=f'TR{ti:04d}';nr['item_id']=mapping[r['item_id']];nr['support_ids']='FLOOR' if r['support_ids']=='FLOOR' else mapping[r['support_ids']];rows.append(nr)
    return rows

def bounds(instance,allowed):
    volume=sum(math.prod(g['dims'])*g['quantity'] for g in instance['cargo']);mass=sum(g['mass']*g['quantity'] for g in instance['cargo']);bestn=10**9;bestc=10**9;combos=[]
    for ns in itertools.product(range(100),repeat=len(allowed)):
        if sum(ns)==0:continue
        if sum(n*math.prod(v['dims']) for n,v in zip(ns,allowed))+1e-7>=volume and sum(n*v['capacity'] for n,v in zip(ns,allowed))>=mass:
            count=sum(ns);cost=sum(n*v['cost'] for n,v in zip(ns,allowed));bestn=min(bestn,count);bestc=min(bestc,cost);combos.append((count,cost,ns))
    return {'volume_cm3':volume,'mass_kg':mass,'vehicle_lower_bound':bestn,'cost_lower_bound':bestc,'scope':'total physical volume and weight relaxation; ignores all geometry/support'}

def master(instance,config,pool,allowed,objective,incumbent):
    ps=[p for p in pool if p['vehicle_type'] in [v['id'] for v in allowed] and sum(p['counts'])];q=np.array([g['quantity'] for g in instance['cargo']]);A=np.array([p['counts'] for p in ps],dtype=float).T
    vm={v['id']:v for v in allowed};c=np.array([vm[p['vehicle_type']]['cost'] for p in ps],dtype=float)
    objective_values=c if objective=='cost' else np.ones(len(ps))
    incumbent_value=sum(vm[p['vehicle_type']]['cost'] for p in incumbent) if objective=='cost' else len(incumbent)
    constraints=[LinearConstraint(csc_matrix(A),q,q),LinearConstraint(csc_matrix(objective_values.reshape(1,-1)),0,incumbent_value)]
    result=milp(objective_values,integrality=np.ones(len(ps)),bounds=Bounds(np.zeros(len(ps)),np.full(len(ps),np.inf)),constraints=constraints,options={'time_limit':config['master_time_limit_seconds'],'mip_rel_gap':0})
    if result.x is None:return incumbent,{'restricted_status':int(result.status),'restricted_message':result.message,'restricted_gap':None,'pattern_count':len(ps),'claim':'no solver incumbent; retain verified constructive portfolio'}
    z=np.rint(result.x).astype(int)
    if not np.array_equal(A@z,q):raise RuntimeError('integer master demand mismatch')
    best=[p for p,n in zip(ps,z) for _ in range(n)]
    def key(pp):
        cst=sum(vm[p['vehicle_type']]['cost'] for p in pp)
        return (cst,len(pp)) if objective=='cost' else (len(pp),cst)
    if key(incumbent)<key(best):best=incumbent
    if objective=='vehicles':
        nopt=sum(z)
        secondary=milp(c,integrality=np.ones(len(ps)),bounds=Bounds(np.zeros(len(ps)),np.full(len(ps),np.inf)),constraints=[LinearConstraint(csc_matrix(A),q,q),LinearConstraint(csc_matrix(np.ones((1,len(ps)))),nopt,nopt)],options={'time_limit':config['master_time_limit_seconds'],'mip_rel_gap':0})
        if secondary.x is not None:
            zz=np.rint(secondary.x).astype(int)
            if np.array_equal(A@zz,q) and sum(zz)==nopt:best=[p for p,n in zip(ps,zz) for _ in range(n)]
    if key(incumbent)<key(best):best=incumbent
    return best,{'restricted_status':int(result.status),'restricted_message':result.message,'restricted_gap':float(result.mip_gap) if result.mip_gap is not None else None,'pattern_count':len(ps),'claim':'optimality/status only within generated pattern pool; retain best known complete incumbent'}

def save_scenario(out,name,instance,config,patterns,elapsed,meta,complete=True):
    path=out/name;path.mkdir(parents=True,exist_ok=True);rows=instantiate(instance,patterns);check=validate(instance,config,rows,complete)
    if not check['valid']:
        (path/'rejected_check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf8')
        with (path/'rejected_placements.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        raise AssertionError(name+str(check['errors']))
    keys=list(rows[0])
    with (path/'placements.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    loads=check.pop('support_loads');
    with (path/'support_loads.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(loads[0]));w.writeheader();w.writerows(loads)
    summary={**check,'status':'feasible','elapsed_seconds':elapsed,**meta,'source_hashes':instance.get('source_hashes',{}),'config':config}
    (path/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');return summary

def solve(instance,config,out,method='improved'):
    errors=input_errors(instance,config)
    if errors:raise InvalidInputError(errors)
    for g in instance['cargo']:
        if g['quantity']<=0:continue
        fits=any(g['mass']<=v['capacity'] and any(all(d[i]<=v['dims'][i]-(config['gap_cm'] if i==2 else 0) for i in range(3)) for d,ori in orientations(g,config)) for v in instance['vehicles'])
        if not fits:
            raise InfeasibleInputError(f"Cargo {g['id']} (dimensions_cm={g['dims']}, mass_kg={g['mass']}) cannot fit any allowed vehicle with its permitted orientation, gap_cm={config['gap_cm']} and payload limits. No transport solution exists for this input.")
    out=Path(out);out.mkdir(parents=True,exist_ok=True);start=time.perf_counter();gs=instance['cargo'];q=np.array([g['quantity'] for g in gs]);vs=instance['vehicles'];options={v['id']:columns(instance,v,config) for v in vs}
    volumes=np.array([math.prod(g['dims']) for g in gs],float);masses=np.array([g['mass'] for g in gs],float);pool=[];allsummary=[];pareto={};portfolio=[]
    print('catalog', {k:len(v) for k,v in options.items()},flush=True)
    for v in vs:
        candidates=[]
        for s in range(config['pattern_count_per_vehicle']):
            rng=np.random.default_rng(config['seed']+s)
            alpha=(s%11)/10; weights=alpha*volumes/volumes.max()+(1-alpha)*masses/masses.max()
            if s>=11:weights*=np.exp(rng.normal(0,.8,len(gs)))
            available=q if s%4 else np.maximum(1,np.rint(q*rng.uniform(.025,.3)).astype(int))
            p=pack(instance,v,config,options[v['id']],available,weights,method,config['seed']+s)
            if sum(p['counts']):pool.append(p);candidates.append(p)
        # pure modes plus singleton provide exact-demand feasibility for the restricted master
        for i in range(len(gs)):
            available=np.zeros(len(gs),dtype=int);available[i]=q[i];p=pack(instance,v,config,options[v['id']],available,volumes,method,0);pool.append(p);candidates.append(p)
            for count in [1,2,3,5,10,20,40,80]:
                available[i]=min(count,q[i]);pool.append(pack(instance,v,config,options[v['id']],available,volumes,method,0))
        front=[p for p in candidates if not any(pp['volume']>=p['volume'] and pp['mass']>=p['mass'] and (pp['volume']>p['volume'] or pp['mass']>p['mass']) for pp in candidates)]
        uniq={tuple(p['counts']):p for p in front};front=list(uniq.values());pareto[v['id']]=[]
        for k,p in enumerate(sorted(front,key=lambda p:p['volume'])):
            sm=save_scenario(out,f'Q1_single_{v["id"]}_P{k:02d}',instance,config,[p],time.perf_counter()-start,{'candidate':method,'objective':'Pareto_archive','complete_frontier':False},False);pareto[v['id']].append({'scenario':f'Q1_single_{v["id"]}_P{k:02d}','counts':p['counts'],'UV':sm['UV'],'UW':sm['UW']})
    for v in vs:
        greedyps=greedy(instance,config,[v],options,method,volumes,config['seed']);pool.extend(greedyps);portfolio.append(greedyps)
        save_scenario(out,'greedy_'+v['id'],instance,config,greedyps,time.perf_counter()-start,{'candidate':method,'objective':'greedy_baseline','bounds':bounds(instance,[v])})
        for restart in range(config.get('inventory_restarts',0)):
            rng=np.random.default_rng(config['seed']+1000+restart)
            weights=volumes/volumes.max()*np.exp(rng.normal(0,.55,len(gs)))
            if restart%3!=2:
                for gi,g in enumerate(gs):
                    if g['class']=='fragile':weights[gi]*=(4 if restart%3==0 else 12)
            fresh=greedy(instance,config,[v],options,method,weights,config['seed']+1000+restart);pool.extend(fresh);portfolio.append(fresh)
        print('inventory restarts complete',v['id'],flush=True)
    for name,allowed,obj in [('Q1_fleet_T1',[vs[0]],'vehicles'),('Q1_fleet_T2',[vs[1]],'vehicles'),('Q2_min_vehicles',vs,'vehicles'),('Q2_min_cost',vs,'cost')]:
        ts=time.perf_counter();vm={v['id']:v for v in allowed};full=[pp for pp in portfolio if all(p['vehicle_type'] in vm for p in pp)]
        def objective_key(pp):
            cc=sum(vm[p['vehicle_type']]['cost'] for p in pp)
            return (cc,len(pp)) if obj=='cost' else (len(pp),cc)
        incumbent=min(full,key=objective_key);ps,meta=master(instance,config,pool,allowed,obj,incumbent);portfolio.append(ps)
        sm=save_scenario(out,name,instance,config,ps,time.perf_counter()-ts,{'candidate':method,'objective':obj,'bounds':bounds(instance,allowed),**meta});allsummary.append({'scenario':name,**{k:sm[k] for k in ['truck_count','cost','UV','UW','elapsed_seconds','valid']}});print(name,allsummary[-1],flush=True)
    (out/'pareto.json').write_text(json.dumps(pareto,ensure_ascii=False,indent=2),encoding='utf8');(out/'run_summary.json').write_text(json.dumps({'method':method,'elapsed_seconds':time.perf_counter()-start,'scenarios':allsummary,'catalog_sizes':{k:len(v) for k,v in options.items()},'patterns':len(pool)},ensure_ascii=False,indent=2),encoding='utf8')
    return allsummary

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data',required=True);parser.add_argument('--config',required=True);parser.add_argument('--out',required=True);parser.add_argument('--method',choices=['shelf','maxrects','improved'],default='improved');args=parser.parse_args()
    try:
        solve(json.loads(Path(args.data).read_text(encoding='utf8')),json.loads(Path(args.config).read_text(encoding='utf8')),args.out,args.method)
    except (InvalidInputError,InfeasibleInputError) as error:
        status='invalid_input' if isinstance(error,InvalidInputError) else 'infeasible_input'
        receipt={'status':status,'valid':False,'message':str(error),'errors':error.errors if isinstance(error,InvalidInputError) else [str(error)],'successful_summary_created':False}
        path=Path(args.out);path.mkdir(parents=True,exist_ok=True);(path/'failure.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
        print(status.upper()+': '+str(error));return 2 if status=='invalid_input' else 3
    return 0
if __name__=='__main__':raise SystemExit(main())
