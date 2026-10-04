"""Prepare one bounded project validator; native calls remain with Root."""
import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
candidate=root/'runs/R01/candidate/forge-agent-flow/scripts'
run=root/sys.argv[1];brief=root/sys.argv[2];run.mkdir(parents=True,exist_ok=True);worker=run/'worker';worker.mkdir()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,ensure_ascii=False,indent=2);f.write('\n')
def cmd(label,args):
 r=subprocess.run([sys.executable,str(root/'scripts/record_command.py'),'--out',str(run/(label+'.json')),'--',sys.executable,*map(str,args)],cwd=root,capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 return json.loads(r.stdout)
plan={'schema_version':'forge-project-plan/1','id':'catalog_validation','goal':'Independent target browser validation of three original presets','deliverable_kind':'scoped_change','requirements':[{'id':'req_work','text':'Verify original frozen acceptance in target browser','origin':'explicit','basis':str(brief),'acceptance_ids':['a_work']}],'acceptance':[{'id':'a_work','assertion':'All original required checks have valid runtime evidence within the repair budget','required':True,'level':'review'}],'tasks':[{'id':'work','title':'Verify original preset catalog','depends_on':[],'owner':'gpt-6-luna','write_paths':['worker/'],'acceptance_ids':['a_work']}]}
prompt=brief.read_text()+'\nRead your immutable host request at '+str(run/'job/request.json')+'. Write report/results and final reply only inside '+str(worker)+'. Use the C3 hostdraft reply helper with a separate incomplete draft and run captured check-reply before returning. Loopback to your own scoped server is explicitly allowed; no other network.\n'
work=dict(prompt=prompt,inputs={'brief':str(brief)},input_files=[{'path':str(brief),'sha256':hashlib.sha256(brief.read_bytes()).hexdigest()}],write_paths=[str(worker)],reply_path=str(worker/'reply.json'))
save(run/'plan.json',plan);save(run/'work.json',work)
cmd('init-command',[candidate/'projectctl.py','init',run/'plan.json','--state',run/'state.json'])
cmd('prepare-command',[candidate/'hostbridge.py','prepare','--kind','project','--state',run/'state.json','--task','work','--work',run/'work.json','--job',run/'job','--parent','/root'])
issue=cmd('issue-command',[candidate/'hostbridge.py','issue','--job',run/'job']);save(run/'issue.json',issue)
snapshot=run/'pre-dispatch';snapshot.mkdir()
for name in ['plan.json','work.json','state.json','job/request.json','job/control.json','job/ledger.json','issue.json']:
 p=snapshot/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((run/name).read_bytes())
print(json.dumps(issue['spawn_arguments'],ensure_ascii=False,indent=2))
