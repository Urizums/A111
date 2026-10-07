"""Recheck all retained published geometries after source-binding repair.

Static rerun of the revised checker, not a repeat of heuristic search or MILP.
"""
import json,time
from solve import ROOT
from check import check_fleet


def run():
    tic=time.perf_counter();cfg=json.loads((ROOT/'configs/base.json').read_text(encoding='utf8'));checks={};rows=[]
    def inspect(name,f,c,complete):
        r=check_fleet(f,c,complete);rows.append({'case':name,'valid':r['valid'],'trucks':len(f),'items':sum(len(t['items']) for t in f),'errors':r['errors']})
        if not r['valid']:raise RuntimeError(rows[-1])
        return r
    for name in ['fixed_T1','fixed_T2','mixed_count','mixed_cost','single_T1_0','single_T1_1','single_T2_0']:
        d=json.loads((ROOT/f'results/final/{name}.json').read_text(encoding='utf8'));checks[name]=inspect(name,d['fleet'],cfg,not name.startswith('single'))
    (ROOT/'review/full_check.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
    pool=json.loads((ROOT/'results/final/pattern_pool.json').read_text(encoding='utf8'))
    for k,tr in enumerate(pool):inspect(f'pool_{k}',[tr],cfg,False)
    summary=json.loads((ROOT/'results/sensitivity/experiments.json').read_text(encoding='utf8'))
    scenarios=[]
    for row in summary:
        if row.get('status')!='checked':raise RuntimeError('unfinished prior scenario: '+row['scenario'])
        name=row['scenario'];d=json.loads((ROOT/f'results/sensitivity/{name}.json').read_text(encoding='utf8'));c=d['config']
        for k,sol in enumerate(d['fixed']):inspect(f'{name}:fixed_{k}',sol['fleet'],c,True)
        for obj in ['count','cost']:inspect(f'{name}:mixed_{obj}',d['mixed'][obj]['fleet'],c,True)
        scenarios.append(name)
    smoke=json.loads((ROOT/'results/smoke_v3.json').read_text(encoding='utf8'));r=inspect('smoke_v3',smoke['fleet'],smoke['config'],True)
    (ROOT/'review/smoke_v3_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
    report={'kind':'informed author self-check; independent re-review pending','method':'revised source-bound checker on every retained layout; no new optimization claim','main_tasks':7,'pattern_pool':len(pool),'parameter_scenarios':len(scenarios),'parameter_fleets':4*len(scenarios),'smoke_tasks':1,'total_fleets':len(rows),'passed':sum(r['valid'] for r in rows),'seconds':time.perf_counter()-tic,'cases':rows}
    (ROOT/'review/affected_layout_recheck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},ensure_ascii=False))


if __name__=='__main__':run()
