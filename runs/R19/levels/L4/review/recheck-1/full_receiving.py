from pathlib import Path
import json,subprocess,time
O=Path(__file__).resolve().parent;R=O.parents[5];N=R/'runs/R19/levels/L4/execution-v2';C=O/'consumer';records=[];sel=json.loads((N/'results/selected.json').read_text(encoding='utf8'))
for name,s in sel['scenarios'].items():
    out=O/f'full-cli-{name}.json';cmd=['py','-3.12','-X','utf8','-B','code/validator.py','--data','data/raw_rebuilt.json','--config','configs/refined.json','--placements',str(N/s['root']/'placements.csv'),'--out',str(out)]
    t=time.perf_counter();p=subprocess.run(cmd,cwd=C,capture_output=True,text=True,encoding='utf8');elapsed=time.perf_counter()-t;observed=json.loads(out.read_text(encoding='utf8'))
    rec={'scenario':name,'command':cmd,'cwd':str(C),'elapsed_seconds':elapsed,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'valid':observed.get('valid'),'errors':observed.get('errors'),'process_state':'finished','assertion_passed':p.returncode==0 and observed.get('valid') is True};records.append(rec)
    (O/'full-cli-receipts.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8');print(name,rec['assertion_passed'])
