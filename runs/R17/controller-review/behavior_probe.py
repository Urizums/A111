import json, os, subprocess, sys, tempfile
from pathlib import Path

repo = Path(sys.argv[1])
out = Path(sys.argv[2])
shim = out / 'shim'
shim.mkdir(parents=True, exist_ok=True)
(shim / 'delivery.py').write_text("from pathlib import Path\ndef read_file(root, name): return (Path(root) / name).read_bytes()\n")
sys.path[:0] = [str(shim), str(repo / 'scripts')]
from continuation import begin, finish, identity, ready, ref, validate, write_json

root = out / 'fixture'
root.mkdir(parents=True, exist_ok=True)
step = root / 'step.json'
cmd = [sys.executable, '-B', str(repo / 'scripts' / 'record_command.py'), '--out', str(step), '--', sys.executable, '-B', '-c', "print('observed command')"]
r = subprocess.run(cmd, capture_output=True, text=True)
assert r.returncode == 0, (r.returncode, r.stderr)

(root / 'policy.txt').write_text('user-authorized prospective progress policy')
(root / 'input.txt').write_text('frozen input')
task = dict(id='x', queue='capabilities', category='probe', priority=1, owner='reviewer',
    write_paths=['x/'], acceptance=[dict(id='result', assertion='original criterion')], inputs=['input.txt'],
    depends_on=[], status='planned', next_action='run', evidence=[], attempts=[], repairs_used=0,
    repair_limit=None, blocker=None, recovery_note=None,
    execution_policy=dict(mode='progress_guard', source=ref(root,'policy.txt'), progress_state='ready',
      deadline_utc='2099-01-01T00:00:00+00:00', stop_conditions=['resource deadline reached', 'unsupported repeated path']))
state = dict(project_goal=dict(id='probe',status='active'), deliveries={}, tasks=[task], execution={})
start = begin(state, root, 'x', 'step.json')
# Simulate an attempt whose configured deadline elapses before its successful result is recorded.
task['execution_policy']['deadline_utc'] = '2000-01-01T00:00:00+00:00'
result = dict(task_id='x', attempt_id=start['id'], requirements_hash=identity(task['acceptance']),
    criteria=[dict(id='result', status='pass', evidence=['step.json'])],
    effect=dict(target='criterion', hypothesis='probe', baseline='before', conditions='local', observations='recorded', limits='local', metrics={}))
write_json(root / 'result.json', result)
finished = finish(state, root, 'x', 'result.json')
task['acceptance'][0]['assertion'] = 'weakened after completion'
drift_errors = validate(state, root)
print(json.dumps(dict(deadline_success=finished['status'], post_done_acceptance_drift_errors=drift_errors, repairs_used=finished['repairs_used'],
    command_record=json.loads(step.read_text()), acceptance_hash=start['requirements_hash']), ensure_ascii=False))
