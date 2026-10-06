"""Verify stop/rollback integrity only, without retrying adoption acceptance."""
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
from verify_handoff import validate_phase,validate_checkpoint

state=ctl.load(ROOT)
errors=ctl.validate(state,ROOT)
phases={}
for pid in ['R12','R13']:
    phase=json.loads((ROOT/f'state/phases/{pid}.json').read_text(encoding='utf-8'))
    errors+=validate_phase(phase,ROOT)
    phases[pid]={t['id']:t['status'] for t in phase['tasks']}
cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
phase=json.loads((ROOT/'state/phase-todo.json').read_text(encoding='utf-8'))
errors+=validate_checkpoint(cp,phase)
assert ctl.task_map(state)['R13-01']['status']=='blocked'
assert ctl.task_map(state)['R13-01']['repairs_used']==2
assert ctl.task_map(state)['R10-02']['repairs_used']==3
assert cp['active_phase']=='R08' and cp['next_queue_task_id'] is None
assert not state['execution']['current_native_pending'] and not state['execution']['native_pending']
result=dict(ok=not errors,errors=errors,phases=phases,queue_tasks=len(state['tasks']),
            next_queue_task_id=ctl.summary(state)['next_task_id'],active_phase='R08',
            limits='Stopped-case graph and preserved queue integrity only; R13 adoption remains failed')
print(json.dumps(result))
raise SystemExit(0 if result['ok'] else 1)
