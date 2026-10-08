import copy,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
PROD=ROOT/'runs/R19/final/forward/production'
RAW=ROOT/'runs/R19/final/forward/inputs/raw.json'
data=json.loads(RAW.read_text(encoding='utf-8-sig'))
outdir=HERE/'input-failures';outdir.mkdir(exist_ok=True)
cases=[]
for name,mutate,expected in [
    ('unequal_dimensions',lambda d:d['types'][1].update(length_m=0.9),'identical fixed dimensions'),
    ('multi_vehicle_type',lambda d:d['vehicles'].append({**d['vehicles'][0],'id':'U'}),'exactly one homogeneous vehicle type'),
    ('duplicate_source_id',lambda d:d['types'][1]['item_ids'].append('S1'),'invalid or duplicated item id'),
    ('source_payload_nan',lambda d:d['vehicles'][0].update(payload_kg=float('nan')),'finite numerical value required'),
]:
    variant=copy.deepcopy(data);mutate(variant)
    source=outdir/(name+'-raw.json');output=outdir/(name+'-solution.json')
    source.write_text(json.dumps(variant,ensure_ascii=False,indent=2,allow_nan=True)+'\n',encoding='utf-8')
    command=[sys.executable,'-B','-X','pycache_prefix='+str(HERE/'bytecode-not-used'),str(PROD/'solve.py'),
             '--input',str(source),'--output',str(output)]
    r=subprocess.run(command,cwd=PROD,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,encoding='utf-8',errors='replace')
    cases.append(dict(case=name,expected_rejection=expected,actual_receipt=dict(command=command,exit_code=r.returncode,
        stdout=r.stdout,stderr=r.stderr,state='finished'),result_file_exists=output.exists(),
        rejected_as_expected=r.returncode!=0 and expected in r.stderr and not output.exists()))
report=dict(scope='Actual source-domain/declared unsupported-input routes; copied review inputs only, not original feasibility answers',
    cases=cases,all_reject_as_expected=all(c['rejected_as_expected'] for c in cases),all_started_processes_terminal=True)
(HERE/'input-failure-observations.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(cases=len(cases),all_reject_as_expected=report['all_reject_as_expected'])))
raise SystemExit(0 if report['all_reject_as_expected'] else 1)
