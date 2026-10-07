"""Declared deterministic one-at-a-time management scenarios, all rechecked."""
import copy,json,time,csv,math,argparse,datetime
from solve import ROOT,fleet_fixed,fleet_module,stats,patterns_master,canonicalize
from check import check_fleet

def scenarios(base):
    out=[('base',copy.deepcopy(base),{'parameter':'baseline','change':0})]
    def add(name,parameter,change,fn):
      c=copy.deepcopy(base);fn(c);out.append((name,c,{'parameter':parameter,'change':change}))
    for axis,label in enumerate(['length','width','height']):
      for delta in [-10,10]:
        add(f'vehicle_{label}_{delta:+}',f'vehicle_{label}',delta,lambda c,a=axis,d=delta:[v['dims'].__setitem__(a,v['dims'][a]+d) for v in c['vehicles']])
    for delta in [0,6]:add(f'clearance_{delta}','clearance',delta,lambda c,d=delta:c.update(clearance=d))
    for fac in [.5,1.2]:add(f'payload_{fac}','payload_factor',fac,lambda c,f=fac:[v.update(payload=v['payload']*f) for v in c['vehicles']])
    for cost in [500,900]:add(f'T2_cost_{cost}','T2_cost',cost,lambda c,d=cost:c['vehicles'][1].update(cost=d))
    for cost in [300,600]:add(f'T1_cost_{cost}','T1_cost',cost,lambda c,d=cost:c['vehicles'][0].update(cost=d))
    for b in [250,750]:add(f'bearing_{b}','bearing',b,lambda c,d=b:c.update(bearing=d))
    for axis,label in enumerate(['length','width','height']):
      for delta in [-5,5]:add(f'cargo_{label}_{delta:+}',f'cargo_{label}',delta,lambda c,a=axis,d=delta:[x['dims'].__setitem__(a,x['dims'][a]+d) for x in c['cargo']])
    for fac in [.8,1.2]:add(f'mass_{fac}','mass_factor',fac,lambda c,f=fac:[x.update(weight=x['weight']*f) for x in c['cargo']])
    for fac in [.8,1.2]:add(f'quantity_{fac}','quantity_factor',fac,lambda c,f=fac:[x.update(quantity=round(x['quantity']*f)) for x in c['cargo']])
    for fac in [.5,1.5]:add(f'fragile_quantity_{fac}','fragile_quantity_factor',fac,lambda c,f=fac:c['cargo'][2].update(quantity=round(c['cargo'][2]['quantity']*f)))
    add('fragile_horizontal_rotation','fragile_rotation',True,lambda c:c.update(fragile_rotation=True))
    add('fragile_floor_only','fragile_support', 'floor only',lambda c:c.update(fragile_floor_only=True))
    add('directional_union_resultant','directional_center_each',False,lambda c:c.update(directional_center_each=False))
    return out

def experiment_all(budget_seconds=900,resume=False):
    base=json.loads((ROOT/'configs/base.json').read_text());cases=scenarios(base);o=ROOT/'results/sensitivity';o.mkdir(exist_ok=True)
    frozen={'budget_seconds_total':900,'solver_seconds_per_master':5,'scenarios':[{'id':n,'config':c,**m} for n,c,m in cases],'method':'fixed height-map strategy 4 plus module variant 1; reject any invalid module; exact count/cost pattern masters separately; deterministic'}
    if not resume:(ROOT/'configs/experiments.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2),encoding='utf8')
    rows=[]
    if resume:
      prior=json.loads((o/'experiments.json').read_text());(o/'experiments_before_resume.json').write_text(json.dumps(prior,ensure_ascii=False,indent=2),encoding='utf8');rows=[r for r in prior if r.get('status')=='checked']
      (ROOT/'configs/experiment_resume.json').write_text(json.dumps({'original_window_seconds':900,'additional_window_seconds':budget_seconds,'reason':'finish remaining frozen parameter cases after observed per-case runtime; no original counter reset','already_checked':len(rows)},ensure_ascii=False,indent=2),encoding='utf8')
    start=time.perf_counter();done={r['scenario'] for r in rows}
    original_pool=json.loads((ROOT/'results/final/pattern_pool.json').read_text())
    for name,cfg,meta in cases:
      if name in done:continue
      if time.perf_counter()-start>budget_seconds:
        rows.append({'scenario':name,**meta,'status':'not_run_budget_exhausted'});continue
      tic=time.perf_counter();pool=[];rejected=[];fixed=[]
      if meta['parameter'] in ['T1_cost','T2_cost','baseline']:
        for p in original_pool:
          p=copy.deepcopy(p);p['vehicle']=copy.deepcopy(next(v for v in cfg['vehicles'] if v['id']==p['vehicle_type']));pool.append(p)
        for v in cfg['vehicles']:
          d=json.loads((ROOT/f'results/final/fixed_{v["id"]}.json').read_text());f=d['fleet']
          for t in f:t['vehicle']=copy.deepcopy(v)
          fixed.append({'vehicle_type':v['id'],'fleet':f,'statistics':stats(f,cfg)})
      else:
        for v in cfg['vehicles']:
          choices=[];generic=fleet_fixed(v,cfg,{'dirfirst':True,'mode':'low','fraction':.8,'standard_order':['G2','G1']});generic=canonicalize(generic,cfg);r=check_fleet(generic,cfg,True)
          if not r['valid']:raise RuntimeError((name,r['errors']))
          choices.append(generic);pool+=generic
          if not cfg.get('fragile_floor_only') and [c['dims'] for c in cfg['cargo']]==[c['dims'] for c in base['cargo']]:
            mod=fleet_module(v,cfg,1);r=check_fleet(mod,cfg,True)
            if r['valid']:choices.append(mod);pool+=mod
            else:rejected.append({'vehicle':v['id'],'module_errors':r['errors']})
          f=min(choices,key=lambda f:len(f));fixed.append({'vehicle_type':v['id'],'fleet':f,'statistics':stats(f,cfg)})
      # Every master pattern is physically valid; constraint equality prevents leftovers.
      uniq={}
      for p in pool:uniq.setdefault((p['vehicle_type'],tuple(sum(i['type_id']==c['id'] for i in p['items']) for c in cfg['cargo'])),p)
      mixed={}
      for objective in ['count','cost']:
        f,receipt=patterns_master(list(uniq.values()),cfg,objective,5)
        choices=[d['fleet'] for d in fixed]+([f] if f else [])+([mixed['count']['fleet']] if objective=='cost' else [])
        f=canonicalize(min(choices,key=lambda f:(len(f),stats(f,cfg)['cost']) if objective=='count' else (stats(f,cfg)['cost'],len(f))),cfg)
        r=check_fleet(f,cfg,True)
        if not r['valid']:raise RuntimeError((name,r['errors']))
        mixed[objective]={'fleet':f,'statistics':stats(f,cfg),'master':receipt}
      dt=time.perf_counter()-tic;row={'scenario':name,**meta,'status':'checked','seconds':dt,'peak_memory_mb':None,'N_count':mixed['count']['statistics']['vehicles'],'C_count':mixed['count']['statistics']['cost'],'N_cost':mixed['cost']['statistics']['vehicles'],'C_cost':mixed['cost']['statistics']['cost'],'volume_rate':mixed['cost']['statistics']['volume_rate'],'load_rate':mixed['cost']['statistics']['load_rate'],'T1_count':mixed['cost']['statistics']['vehicle_counts']['T1'],'T2_count':mixed['cost']['statistics']['vehicle_counts']['T2'],'feasible':True,'rejected_module_candidates':len(rejected)};rows.append(row)
      (o/f'{name}.json').write_text(json.dumps({'config':cfg,'metadata':meta,'fixed':fixed,'mixed':mixed,'rejected_module_candidates':rejected,'seconds':dt},ensure_ascii=False),encoding='utf8')
      (o/'experiments.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8');print(name,row['N_cost'],row['C_cost'],round(dt,2),flush=True)
    fields=sorted(set(k for r in rows for k in r))
    with (o/'experiments.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    elapsed=time.perf_counter()-start
    (o/'experiments.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
    with (o/'invocations.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps({'resume':resume,'window_seconds':budget_seconds,'actual_seconds':elapsed,'checked_after':sum(r.get('status')=='checked' for r in rows),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False)+'\n')
    print('TOTAL',elapsed,'seconds',len(rows),'scenarios');return rows

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--resume',action='store_true');p.add_argument('--budget-seconds',type=int,default=900);a=p.parse_args();experiment_all(a.budget_seconds,a.resume)
