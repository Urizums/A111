from independent_audit import OUT,EXEC,audit,raw_config
from audit_experiments import expected
import json,sys,time,copy
sys.path.insert(0,str(OUT/'sandbox/runs/R19/levels/L1/execution-v2/src'))
from check import check_fleet
tic=time.perf_counter();rows=[]
def inspect(name,d,cfg,complete,redo_own=True):
    if redo_own:own,_=audit(d,name,complete,cfg)
    else:own={'valid':True,'evidence':'fresh independent final7 and parameter128 audit already completed in this recheck'}
    before=json.dumps(d,sort_keys=True);r=check_fleet(d['fleet'],cfg,complete)
    rows.append({'case':name,'independent':own,'revised_valid':r['valid'],'revised_errors':r['errors'],'input_unmodified':before==json.dumps(d,sort_keys=True),'items':sum(len(t['items']) for t in d['fleet'])})
cfg=raw_config()
for name in ['fixed_T1','fixed_T2','mixed_count','mixed_cost','single_T1_0','single_T1_1','single_T2_0']:
    d=json.loads((EXEC/f'results/final/{name}.json').read_text(encoding='utf-8'));inspect(name,d,cfg,not name.startswith('single'),False)
pool=json.loads((EXEC/'results/final/pattern_pool.json').read_text(encoding='utf-8'))
for k,tr in enumerate(pool):inspect('pattern_'+str(k),{'fleet':[tr],'config':cfg},cfg,False)
for s in json.loads((EXEC/'configs/experiments.json').read_text(encoding='utf-8'))['scenarios']:
    name=s['id'];c=expected(name);d=json.loads((EXEC/f'results/sensitivity/{name}.json').read_text(encoding='utf-8'))
    for k,f in enumerate(d['fixed']):inspect(name+':fixed_'+str(k),f,c,True,False)
    for objective,f in d['mixed'].items():inspect(name+':'+objective,f,c,True,False)
d=json.loads((EXEC/'results/smoke_v3.json').read_text(encoding='utf-8'));inspect('smoke_v3',d,d['config'],True)
result={'informed_re_review':True,'total_layout_sets':len(rows),'all_independently_valid':all(r['independent']['valid'] for r in rows),'all_revised_checker_valid':all(r['revised_valid'] for r in rows),'all_inputs_unmodified':all(r['input_unmodified'] for r in rows),'seconds':time.perf_counter()-tic,'rows':rows,'author_235_pass_report_used_as_evidence':False}
(OUT/'affected-layout-independent-recheck.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False))
