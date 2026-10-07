from pathlib import Path
import json,time,csv,sys,math
from solve import ROOT,stats,patterns_master,canonicalize
from check import check_fleet

def finalize():
    cfg=json.loads((ROOT/'configs/base.json').read_text());out=ROOT/'results/final';out.mkdir(exist_ok=True);pool=[];best={};records=[]
    for v in cfg['vehicles']:
      files=[ROOT/f'results/v2/fixed_{v["id"]}.json']+sorted((ROOT/'results/modules_v3').glob(v['id']+'_*.json'));candidates=[]
      for p in files:
        d=json.loads(p.read_text());r=check_fleet(d['fleet'],cfg,True)
        if not r['valid']:records.append({'file':str(p.relative_to(ROOT)),'valid':False,'errors':r['errors']});continue
        ss=stats(d['fleet'],cfg);candidates.append((ss['vehicles'],str(p),d['fleet']));pool+=d['fleet'];records.append({'file':str(p.relative_to(ROOT)),'valid':True,'statistics':ss})
      winner=min(candidates,key=lambda x:x[:2]);f=winner[2];best[v['id']]={'config':cfg,'fleet':f,'statistics':stats(f,cfg),'chosen_source':str(Path(winner[1]).relative_to(ROOT))}
      (out/f'fixed_{v["id"]}.json').write_text(json.dumps(best[v['id']],ensure_ascii=False),encoding='utf8')
    single=json.loads((ROOT/'results/v2/single_pareto.json').read_text());validsingle={}
    for v,ps in single['solutions'].items():
      validsingle[v]=[]
      for p in ps:
        r=check_fleet(p['fleet'],cfg,False)
        if r['valid']:validsingle[v].append(p);pool+=p['fleet']
        else:records.append({'single_strategy':p['strategy_id'],'valid':False,'errors':r['errors']})
    (out/'single_pareto.json').write_text(json.dumps({'config':cfg,'solutions':validsingle},ensure_ascii=False),encoding='utf8')
    uniq={}
    for p in pool:
      key=(p['vehicle_type'],tuple(sum(i['type_id']==c['id'] for i in p['items']) for c in cfg['cargo']));uniq.setdefault(key,p)
    pool=list(uniq.values());mixed={}
    for obj in ['count','cost']:
      upper=min(d['statistics']['vehicles'] if obj=='count' else d['statistics']['cost'] for d in best.values())
      tic=time.perf_counter();f,receipt=patterns_master(pool,cfg,obj,60,upper);seconds=time.perf_counter()-tic
      choices=[d['fleet'] for d in best.values()]+([f] if f else [])+([mixed['count']['fleet']] if obj=='cost' else [])
      key=lambda f:(len(f),stats(f,cfg)['cost']) if obj=='count' else (stats(f,cfg)['cost'],len(f))
      picked=min(choices,key=key)
      receipt['solver_incumbent_statistics']=stats(f,cfg) if f else None;receipt['selected_known_incumbent']=picked is not f
      f=canonicalize(picked,cfg)
      r=check_fleet(f,cfg,True)
      if not r['valid']:raise RuntimeError(r['errors'])
      mixed[obj]={'config':cfg,'fleet':f,'statistics':stats(f,cfg),'master':receipt,'seconds':seconds};(out/f'mixed_{obj}.json').write_text(json.dumps(mixed[obj],ensure_ascii=False),encoding='utf8')
    (out/'pattern_pool.json').write_text(json.dumps(pool,ensure_ascii=False),encoding='utf8');(ROOT/'review/selected_candidates.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
    allsol={**{f'fixed_{k}':d for k,d in best.items()},**{f'mixed_{k}':d for k,d in mixed.items()}}
    checkreports={}
    for name,d in allsol.items():
      r=check_fleet(d['fleet'],cfg,True);checkreports[name]=r
      with (out/f'{name}_placements.csv').open('w',encoding='utf-8-sig',newline='') as h:
        fields=['truck_id','vehicle_type','item_id','type_id','x','y','z','dx','dy','dz','orientation','weight','category'];w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
        for t in d['fleet']:
          for i in t['items']:w.writerow({**i,'vehicle_type':t['vehicle_type']})
    for v,ps in validsingle.items():
      for k,p in enumerate(ps):
        checkreports[f'single_{v}_{k}']=check_fleet(p['fleet'],cfg,False)
        (out/f'single_{v}_{k}.json').write_text(json.dumps({'config':cfg,**p},ensure_ascii=False),encoding='utf8')
    (ROOT/'review/full_check.json').write_text(json.dumps(checkreports,ensure_ascii=False),encoding='utf8')
    with (out/'fleet_summary.csv').open('w',encoding='utf-8-sig',newline='') as h:
      fields=['task','truck_id','vehicle_type','G1','G2','G3','G4','G5','volume_rate','load_rate','weight_kg','cost'];w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
      for name,d in allsol.items():
        for t in d['fleet']:
          s=stats([t],cfg);w.writerow({'task':name,'truck_id':t['truck_id'],'vehicle_type':t['vehicle_type'],**{c['id']:sum(i['type_id']==c['id'] for i in t['items']) for c in cfg['cargo']},'volume_rate':s['volume_rate'],'load_rate':s['load_rate'],'weight_kg':s['weight_kg'],'cost':s['cost']})
    print(json.dumps({k:d['statistics'] for k,d in allsol.items()},ensure_ascii=False,indent=2));return allsol

if __name__=='__main__':finalize()
