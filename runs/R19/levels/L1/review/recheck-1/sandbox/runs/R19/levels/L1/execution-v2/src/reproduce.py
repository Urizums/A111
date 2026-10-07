"""Raw source -> deterministic selected recipes -> independent check -> metrics.
Does not replay MILP heuristics under wall-clock variance. Use --search for full
candidate exploration separately (solve.py + module sweep + finalize.py).
"""
import argparse,json,copy,time,csv,os
from pathlib import Path
from normalize import normalize
from solve import ROOT,fleet_module,Truck,pack,canonicalize,stats,strategy_list
from check import check_fleet

def reproduce(out):
    if out.exists() and any(out.iterdir()):raise ValueError('Reproduction output must be absent/empty; preserve previous records')
    out.mkdir(parents=True,exist_ok=True);tic=time.perf_counter();cfg=normalize();produced={}
    for vid,variant in [('T1',1),('T2',0)]:
      v=next(v for v in cfg['vehicles'] if v['id']==vid);f=fleet_module(v,cfg,variant);produced[f'fixed_{vid}']={'config':cfg,'fleet':f,'statistics':stats(f,cfg)}
    for name in ['count','cost']:produced[f'mixed_{name}']=copy.deepcopy(produced['fixed_T2'])
    for vid in ['T1','T2']:
      v=next(v for v in cfg['vehicles'] if v['id']==vid)
      if vid=='T1':
        rem={c['id']:c['quantity'] for c in cfg['cargo']};tr=pack(v,cfg,rem,strategy_list()[6]);f=canonicalize([{'vehicle_type':vid,'vehicle':v,'items':tr.items}],cfg);produced['single_T1_0']={'config':cfg,'fleet':f,'statistics':stats(f,cfg)}
      order=['G2','G1','G5','G4','G3'] if vid=='T1' else ['G5','G1','G2','G4','G3'];tr=Truck(v,cfg);rem={c['id']:c['quantity'] for c in cfg['cargo']};ser=dict.fromkeys(rem,0)
      for t in order:
        c=next(c for c in cfg['cargo'] if c['id']==t)
        while rem[t]>0:
          p=tr.find(c,v['dims'][2]-cfg['clearance'],'compact')
          if p is None:break
          rem[t]-=1;ser[t]+=1;tr.add(c,p,ser[t])
      f=canonicalize([{'vehicle_type':vid,'vehicle':v,'items':tr.items}],cfg);produced['single_T1_1' if vid=='T1' else 'single_T2_0']={'config':cfg,'fleet':f,'statistics':stats(f,cfg)}
    comparisons=[]
    for name,d in produced.items():
      complete=not name.startswith('single');r=check_fleet(d['fleet'],cfg,complete)
      reference=json.loads((ROOT/f'results/final/{name}.json').read_text());target=reference['statistics'];actual=d['statistics'];metric_match=all(abs(actual[k]-target[k])<1e-8 for k in ['vehicles','cost','volume_cm3','weight_kg','volume_rate','load_rate']);geometry_match=d['fleet']==reference['fleet']
      comparisons.append({'task':name,'feasible':r['valid'],'metrics_match':metric_match,'geometry_match':geometry_match,'counts':r['counts']});(out/f'{name}.json').write_text(json.dumps(d,ensure_ascii=False),encoding='utf8')
      with (out/f'{name}_placements.csv').open('w',encoding='utf-8-sig',newline='') as f:
        keys=['truck_id','vehicle_type','item_id','type_id','x','y','z','dx','dy','dz','orientation','weight','category'];writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
        for t in d['fleet']:
          for i in t['items']:writer.writerow({**i,'vehicle_type':t['vehicle_type']})
      if not(r['valid'] and metric_match and geometry_match):raise RuntimeError(comparisons[-1])
    with (out/'summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
      keys=['task','vehicles','cost','volume_rate','load_rate','volume_cm3','weight_kg'];writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');writer.writeheader();writer.writerows({'task':n,**d['statistics']} for n,d in produced.items())
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'logs/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    names=list(produced);fig,ax=plt.subplots(figsize=(9,4));xx=range(len(names));ax.plot(xx,[d['statistics']['volume_rate']*100 for d in produced.values()],'o-',label='Volume utilization');ax.plot(xx,[d['statistics']['load_rate']*100 for d in produced.values()],'s-',label='Weight utilization');ax.set_xticks(list(xx),names,rotation=35,ha='right');ax.set_ylabel('Utilization (%)');ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'reproduced_metrics.png',dpi=180);plt.close(fig)
    report={'comparisons':comparisons,'seconds':time.perf_counter()-tic,'from':'official original DOCX/XLSX','independence':'author fresh output, not independent acceptance','search_optimality_claim':False};(out/'reproduction_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();reproduce(a.out)
