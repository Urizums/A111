import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
PROD=ROOT/'runs/R19/final/forward/production'
RAW=ROOT/'runs/R19/final/forward/inputs/raw.json'
steps=[['solve.py','--input',str(RAW),'--output',str(HERE/'consumer-solution.json')],
       ['verify.py','--input',str(RAW),'--solution',str(HERE/'consumer-solution.json'),'--output',str(HERE/'consumer-checks.json')],
       ['tests.py','--input',str(RAW),'--solution',str(HERE/'consumer-solution.json'),'--output',str(HERE/'consumer-tests.json')],
       ['experiments.py','--input',str(RAW),'--output',str(HERE/'consumer-experiments.json')]]
receipts=[]
for step in steps:
    started=time.perf_counter()
    command=[sys.executable,'-B','-X','pycache_prefix='+str(HERE/'bytecode-not-used'),*step]
    r=subprocess.run(command,cwd=PROD,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,encoding='utf-8',errors='replace')
    receipts.append(dict(command=command,working_directory=str(PROD),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,
                         elapsed_seconds=time.perf_counter()-started,state='finished'))
    print(step[0],r.returncode,r.stdout.strip())
    if r.returncode:
        break
(HERE/'workflow-receipts.json').write_text(json.dumps(dict(commands=receipts,all_started_commands_terminal=True,
    all_four_completed=len(receipts)==4 and all(c['exit_code']==0 for c in receipts)),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if len(receipts)==4 and all(c['exit_code']==0 for c in receipts) else 1)
