import json, os, subprocess, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

repo, out = Path(sys.argv[1]), Path(sys.argv[2])
fixture_name = sys.argv[3] if len(sys.argv) > 3 else 'fixture'
sys.path[:0] = [str(out / 'shim'), str(repo / 'scripts')]
from continuation import begin, finish, identity, ready, ref, validate, write_json

root = out / fixture_name
root.mkdir(parents=True, exist_ok=True)
policy_file = root / 'policy.txt'; policy_file.write_text('authorized prospective policy')
input_file = root / 'input.txt'; input_file.write_text('frozen input')
recorder = repo / 'scripts' / 'record_command.py'

def receipt(name, text):
    path = root / name
    p = subprocess.run([sys.executable, '-B', str(recorder), '--out', str(path), '--',
                        sys.executable, '-B', '-c', 'print(' + repr(text) + ')'],
                       capture_output=True, text=True)
    assert p.returncode == 0, (p.returncode, p.stderr)
    return name

def task(progress=True, repair_limit=None):
    t = dict(id='t', queue='capabilities', category='probe', priority=1, owner='reviewer',
        write_paths=['t/'], acceptance=[dict(id='result', assertion='original assertion')], inputs=['input.txt'],
        depends_on=[], status='planned', next_action='continue', evidence=[], attempts=[], repairs_used=0,
        repair_limit=repair_limit if not progress else None, blocker=None)
    if progress:
        t['execution_policy'] = dict(mode='progress_guard', source=ref(root,'policy.txt'), progress_state='ready',
            deadline_utc=None, stop_conditions=['verified outcome', 'actual resource boundary'])
    return t

def state_for(t):
    return dict(project_goal=dict(id='probe',status='active'), deliveries={}, tasks=[t], execution={})

def result(s, name, status='pass'):
    t=s['tasks'][0]
    value=dict(task_id='t', attempt_id=t['attempts'][-1]['id'], requirements_hash=identity(t['acceptance']),
        criteria=[dict(id='result',status=status,evidence=['input.txt'])],
        effect=dict(target='criterion',hypothesis='probe',baseline='before',conditions='local',observations='recorded',limits='local',metrics={}))
    write_json(root/name,value)
    return name

# Real-clock boundary: begin just before a 0.6 s deadline and finish after it.
t=task(); t['execution_policy']['deadline_utc']=(datetime.now(timezone.utc)+timedelta(seconds=0.6)).isoformat()
s=state_for(t); r1=receipt('deadline-start.json','deadline attempt'); begin(s,root,'t',r1)
time.sleep(0.9)
dead=finish(s,root,'t',result(s,'deadline-result.json'))

# Acceptance remains frozen after a completed progress attempt.
t2=task(); s2=state_for(t2); r2=receipt('acceptance-start.json','acceptance attempt'); begin(s2,root,'t',r2)
finish(s2,root,'t',result(s2,'acceptance-result.json'))
t2['acceptance'][0]['assertion']='weakened after done'
acceptance_errors=validate(s2,root)

# A progress retry rejects reused bytes; a new recorded command receipt is accepted.
t3=task(); s3=state_for(t3); r3=receipt('retry-first.json','first attempt'); begin(s3,root,'t',r3)
finish(s3,root,'t',result(s3,'retry-fail.json','fail'))
(root/'observation.txt').write_text('observed failure; changed approach selected')
t3['recovery_note']=dict(observation='observed failure',change_or_new_information='use a different method',
    expected_check='original assertion',evidence=[ref(root,'observation.txt')])
try:
    begin(s3,root,'t',r3); reused='accepted'
except ValueError as exc:
    reused=str(exc)
r4=receipt('retry-second.json','different changed approach')
begin(s3,root,'t',r4)

# Legacy no-policy task remains on its numeric repair cap and accepts its historic receipt reuse.
t4=task(progress=False,repair_limit=1); s4=state_for(t4); r5=receipt('legacy.json','legacy step')
begin(s4,root,'t',r5); finish(s4,root,'t',result(s4,'legacy-fail.json','fail'))
begin(s4,root,'t',r5); finish(s4,root,'t',result(s4,'legacy-fail2.json','fail'))
legacy=dict(status=t4['status'],repairs_used=t4['repairs_used'],attempts=len(t4['attempts']),ready=[x['id'] for x in ready(s4)])
t4d=task(progress=False,repair_limit=1); s4d=state_for(t4d); r5d=receipt('legacy-done.json','legacy successful step')
begin(s4d,root,'t',r5d); finish(s4d,root,'t',result(s4d,'legacy-done-result.json'))
t4d['acceptance'][0]['assertion']='weakened after legacy completion'
legacy_acceptance_errors=validate(s4d,root)

# Runtime stalled state is intentionally mutable; policy terms and source remain frozen.
t5=task(); s5=state_for(t5); r6=receipt('stalled.json','active attempt'); begin(s5,root,'t',r6)
t5['execution_policy']['progress_state']='stalled'
stalled_errors=validate(s5,root)
stalled_finish=finish(s5,root,'t',result(s5,'stalled-result.json'))

# Falsey malformed deadline currently behaves as if no deadline exists.
t6=task(); t6['execution_policy']['deadline_utc']=''
s6=state_for(t6)
empty_deadline=dict(errors=validate(s6,root),ready=[x['id'] for x in ready(s6)])
t6['execution_policy']['deadline_utc']=123
try:
    bad_deadline=dict(errors=validate(s6,root),exception=None)
except Exception as exc:
    bad_deadline=dict(exception=type(exc).__name__+': '+str(exc))

print(json.dumps(dict(real_clock_deadline=dead, real_elapsed_seconds=0.9, acceptance_drift_errors=acceptance_errors,
    reused_retry_receipt=reused, fresh_retry_attempts=len(t3['attempts']), legacy=legacy,
    legacy_acceptance_drift_errors=legacy_acceptance_errors,
    stalled_policy_errors=stalled_errors, stalled_completion=stalled_finish,
    empty_deadline=empty_deadline, numeric_deadline=bad_deadline),ensure_ascii=False))
