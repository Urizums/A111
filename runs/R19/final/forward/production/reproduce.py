"""Clean-process reproduction of semantic numerical outputs (not timing)."""
import json, os, subprocess, sys, time
from pathlib import Path
from common import write_json

base=Path(__file__).resolve().parent
out=base/'reproduction'
out.mkdir(exist_ok=True)
raw=base.parent/'inputs'/'raw.json'
commands=[['solve.py','--input',str(raw),'--output',str(out/'solution.json')],
    ['verify.py','--input',str(raw),'--solution',str(out/'solution.json'),'--output',str(out/'checks.json')],
    ['tests.py','--input',str(raw),'--solution',str(out/'solution.json'),'--output',str(out/'test_results.json')],
    ['experiments.py','--input',str(raw),'--output',str(out/'experiments.json')]]
receipts=[]
for command in commands:
    start=time.perf_counter()
    r=subprocess.run([sys.executable,'-B',*command],cwd=base,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,encoding='utf-8',errors='replace')
    receipts.append({'command':[sys.executable,'-B',*command],'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'elapsed_seconds':time.perf_counter()-start})
    if r.returncode:
        write_json(out/'receipt.json',{'commands':receipts,'all_commands_finished':True,'semantic_match':False})
        raise SystemExit(r.returncode)
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
original=load(base/'solution.json'); rerun=load(out/'solution.json')
semantic_keys=['schema','source_sha256','vehicle_type_id','placements','objective','optimality']
solution_match=all(original[k]==rerun[k] for k in semantic_keys)
checks_match=load(base/'checks.json')==load(out/'checks.json')
test_passes_match=[(x['case'],x['accepted'],x['assertion_passed'],x['errors']) for x in load(base/'test_results.json')['cases']]==[(x['case'],x['accepted'],x['assertion_passed'],x['errors']) for x in load(out/'test_results.json')['cases']]
e1=load(base/'experiments.json'); e2=load(out/'experiments.json')
for e in [e1,e2]:
    for case in e['parameter_variants']: case['search'].pop('elapsed_seconds',None)
experiments_match=e1==e2
r={'commands':receipts,'all_commands_finished':True,'solution_semantic_match':solution_match,'checks_match':checks_match,
    'test_verdicts_match':test_passes_match,'experiments_semantic_match':experiments_match,'excluded_comparison':'elapsed_seconds only',
    'semantic_match':all([solution_match,checks_match,test_passes_match,experiments_match])}
write_json(out/'receipt.json',r)
print('Clean reproduction:',r['semantic_match'])
raise SystemExit(0 if r['semantic_match'] else 1)
