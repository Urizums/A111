"""Controlled Q3 reruns; synthetic perturbations are explicitly identified."""
from pathlib import Path
import json,copy,time,csv
import numpy as np
from solve import columns,pack,greedy,master,save_scenario,bounds

def experiment(instance,config,out,name):
    start=time.perf_counter();vs=instance['vehicles'];gs=instance['cargo'];opts={v['id']:columns(instance,v,config) for v in vs};q=np.array([g['quantity'] for g in gs]);volumes=np.array([np.prod(g['dims']) for g in gs],float);pool=[];portfolio=[]
    for v in vs:
        for s in range(config['pattern_count_per_vehicle']):
            rng=np.random.default_rng(config['seed']+s);weights=volumes/volumes.max()*np.exp(rng.normal(0,.7,len(gs)))
            if s%3:weights[2]*=(4 if s%3==1 else 12)
            pool.append(pack(instance,v,config,opts[v['id']],q,weights,'improved',config['seed']+s))
        for s in range(config['inventory_restarts']):
            weights=volumes/volumes.max();weights=weights.copy();weights[2]*=[1,4,12,6][s%4]
            ps=greedy(instance,config,[v],opts,'improved',weights,config['seed']+s);portfolio.append(ps);pool.extend(ps)
        for i in range(len(gs)):
            a=np.zeros(len(gs),dtype=int);a[i]=1;pool.append(pack(instance,v,config,opts[v['id']],a,volumes,'improved',0))
    costs={v['id']:v['cost'] for v in vs};incumbent=min(portfolio,key=lambda ps:sum(costs[p['vehicle_type']] for p in ps));ps,meta=master(instance,config,pool,vs,'cost',incumbent)
    summary=save_scenario(out,name,instance,config,ps,time.perf_counter()-start,{'candidate':'parameter_budget_improved','objective':'cost','bounds':bounds(instance,vs),'synthetic_scenario':name!='base','experiment_window':'24 preference modes + 4 full-inventory starts per vehicle + 8-second master',**meta})
    (Path(out)/name/'input.json').write_text(json.dumps(instance,ensure_ascii=False,indent=2),encoding='utf8')
    return {k:summary[k] for k in ['truck_count','cost','UV','UW','elapsed_seconds','valid']}|{'scenario':name,'inventory_items':sum(q),'seed':config['seed'],'restricted_status':summary['restricted_status'],'peak_memory_bytes':None}

def main():
    E=Path(__file__).resolve().parents[1];base=json.loads((E/'data/instance.json').read_text(encoding='utf8'));cfg=json.loads((E/'configs/experiments.json').read_text(encoding='utf8'));cases=[]
    def add(name,mutate):
        data=copy.deepcopy(base);c=copy.deepcopy(cfg);mutate(data,c);cases.append((name,data,c))
    add('base',lambda d,c:None)
    for value in [.5,1.5]:add(f'payload_{value}',lambda d,c,v=value:[t.update(capacity=t['capacity']*v) for t in d['vehicles']])
    for value in [10,30]:add(f'gap_{value}',lambda d,c,v=value:c.update(gap_cm=v))
    for value in [250,750]:add(f'pressure_{value}',lambda d,c,v=value:c.update(pressure_kg_m2=v))
    for value in [.95,1.05]:add(f'dimensions_{value}',lambda d,c,v=value:[g.update(dims=[round(x*v,4) for x in g['dims']]) for g in d['cargo']])
    add('fragile_original_height',lambda d,c:c.update(fragile_orientation='original_height'))
    for value in [315,585]:add(f'T1_cost_{value}',lambda d,c,v=value:d['vehicles'][0].update(cost=v))
    for value in [.25,.5,2]:add(f'scale_{value}',lambda d,c,v=value:[g.update(quantity=max(1,round(g['quantity']*v))) for g in d['cargo']])
    for value in [1905,1906]:add(f'seed_{value}',lambda d,c,v=value:c.update(seed=v))
    previous=E/'results/parameter_results.csv';records=list(csv.DictReader(previous.open(encoding='utf-8-sig',newline=''))) if previous.exists() else []
    completed={r['scenario'] for r in records}
    for name,data,c in cases:
        if name in completed:continue
        row=experiment(data,c,E/'results/experiments',name);records.append(row)
        with (E/'results/parameter_results.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerows(records)
        print(row,flush=True)
    (E/'checks/experiments.json').write_text(json.dumps({'cases':len(records),'all_valid':all(r['valid'] in [True,'True'] for r in records),'base_budget':cfg,'status':'completed','claim':'synthetic controlled changes; no causal population guarantee'},ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
