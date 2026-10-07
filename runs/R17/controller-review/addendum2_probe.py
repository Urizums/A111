import json, subprocess, sys
from pathlib import Path
repo, out = Path(sys.argv[1]), Path(sys.argv[2])
shim = out/'shim'; shim.mkdir(parents=True, exist_ok=True)
(shim/'delivery.py').write_text("from pathlib import Path\ndef read_file(root, name): return (Path(root)/name).read_bytes()\n")
sys.path[:0] = [str(shim), str(repo/'scripts')]
from continuation import begin, finish, identity, ready, ref, validate, write_json

root = out / 'fixture'
root.mkdir(parents=True, exist_ok=True)
(root/'policy.txt').write_text('authorized prospective policy')
(root/'input.txt').write_text('frozen input')
recorder = repo/'scripts'/'record_command.py'

def receipt(name, text):
    p = subprocess.run([sys.executable, '-B', str(recorder), '--out', str(root/name), '--',
        sys.executable, '-B', '-c', 'print('+repr(text)+')'], capture_output=True, text=True)
    assert p.returncode == 0, (p.returncode,p.stderr)
    return name

def task(progress=True, limit=1):
    t=dict(id='t',queue='capabilities',category='review',priority=1,owner='reviewer',write_paths=['t/'],
        acceptance=[dict(id='result',assertion='original frozen criterion')],inputs=['input.txt'],depends_on=[],
        status='planned',next_action='continue',evidence=[],attempts=[],repairs_used=0,
        repair_limit=None if progress else limit,blocker=None)
    if progress:
        t['execution_policy']=dict(mode='progress_guard',source=ref(root,'policy.txt'),progress_state='ready',
            deadline_utc=None,stop_conditions=['resource boundary','stalled path'])
    return t

def state(t): return dict(project_goal=dict(id='probe',status='active'),deliveries={},tasks=[t],execution={})

def result(s,name='result.json',verdict='pass'):
    t=s['tasks'][0]
    value=dict(task_id='t',attempt_id=t['attempts'][-1]['id'],requirements_hash=identity(t['acceptance']),
        criteria=[dict(id='result',status=verdict,evidence=['input.txt'])],
        effect=dict(target='criterion',hypothesis='probe',baseline='before',conditions='local',observations='recorded',limits='local',metrics={}))
    write_json(root/name,value); return name

# Terminal requirement hash, for both opt-in progress and legacy fixed mode.
completion={}
for mode in ['progress_guard','legacy_fixed']:
    t=task(progress=(mode=='progress_guard')); s=state(t); ev=receipt(mode+'-complete.json',mode+' success')
    begin(s,root,'t',ev); finish(s,root,'t',result(s,mode+'-result.json'))
    t['acceptance'][0]['assertion']='weakened after completion'
    completion[mode]=validate(s,root)

# Invalid deadline payloads must both validate as errors and be absent from ready work.
malformed={}
for i,value in enumerate(['',123,False,[],{}]):
    t=task(); t['execution_policy']['deadline_utc']=value; s=state(t)
    errs=validate(s,root)
    malformed[repr(value)]={'errors':errs,'ready':[x['id'] for x in ready(s)]}

# Full policy terms are frozen at attempt start; progress_state is intentionally mutable.
t=task(); s=state(t); ev=receipt('policy-active.json','active action'); begin(s,root,'t',ev)
t['execution_policy']['deadline_utc']='2099-01-01T00:00:00+00:00'
try:
    finish(s,root,'t',result(s,'policy-drift-result.json'))
    policy_drift='accepted'
except ValueError as e: policy_drift=str(e)
t['execution_policy']['deadline_utc']=None
t['execution_policy']['progress_state']='stalled'
stalled_errors=validate(s,root)
stalled_finish=finish(s,root,'t',result(s,'stalled-result.json'))

# Legacy fixed cap remains independent of progress guard behavior.
t=task(progress=False,limit=1); s=state(t); ev=receipt('legacy-cap.json','legacy action')
begin(s,root,'t',ev); finish(s,root,'t',result(s,'legacy-fail1.json','fail'))
begin(s,root,'t',ev); finish(s,root,'t',result(s,'legacy-fail2.json','fail'))
legacy_cap={'status':t['status'],'repairs_used':t['repairs_used'],'attempts':len(t['attempts']),
            'ready':[x['id'] for x in ready(s)]}

print(json.dumps(dict(completion_hash_drift=completion,malformed_deadlines=malformed,
    frozen_policy_change=policy_drift,stalled_validate_errors=stalled_errors,
    stalled_finish=stalled_finish,legacy_cap=legacy_cap),ensure_ascii=False))
