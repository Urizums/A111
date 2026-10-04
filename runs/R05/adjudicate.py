"""Serial Root integration of an already received bounded project job."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--review',type=Path,required=True);p.add_argument('--outcome',choices=['done','blocked'],required=True);p.add_argument('--reason');p.add_argument('--candidate',default='runs/R01/candidate/forge-agent-flow');a=p.parse_args();run=(ROOT/a.run).resolve();c=ROOT/a.candidate/'scripts'
def call(label,args):
 r=subprocess.run([sys.executable,ROOT/'scripts/record_command.py','--out',run/(label+'.json'),'--',sys.executable,*map(str,args)],cwd=ROOT,capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 return json.loads(r.stdout)
draft=run/'decision.draft.json';final=run/'decision.json'
call('decision-draft-command',[c/'hostdraft.py','decision','--job',run/'job','--evidence',(ROOT/a.review).resolve(),'--out',draft]);d=json.loads(draft.read_text());d['outcome']=a.outcome
if a.outcome=='done':
 for result in d['results']['acceptance_results'].values():result['status']='pass'
 d['reason']=None
else:
 if not a.reason:raise ValueError('Blocked decision requires actual reason')
 d['results']=None;d['reason']=a.reason
with final.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
call('decision-check-command',[c/'hostdraft.py','check-decision','--job',run/'job','--decision',final]);call('commit-command',[c/'hostbridge.py','commit','--job',run/'job','--decision',final]);r=call('reconcile-command',[c/'hostbridge.py','reconcile','--job',run/'job'])
with (run/'reconcile-final.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r))
