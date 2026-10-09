"""Record actual R23 lease release after bounded closure and full handoff check."""
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
lease=read('state/coordinator-lease.json')
assert lease['owner']=='root-codex-r23-design' and lease['pid']==355 and lease.get('released_at')
probe=json.loads(subprocess.check_output([sys.executable,'scripts/coordinator_lease.py','probe','--root',str(ROOT)],cwd=ROOT,text=True))
assert not probe['busy']
check=read('runs/R23/closure-handoff-command.json')
assert check['state']=='finished' and check['exit_code']==0 and json.loads(check['stdout'])['ok']
with ctl.locked(ROOT):
    state=ctl.load(ROOT);tasks=ctl.task_map(state)
    before=read('runs/R23/before-execution/task-identities.json');protected={k:v for k,v in before.items() if k not in ['R23-02','R23-03','R23-04','R23-next']}
    assert all(ctl.identity(tasks[k])==v for k,v in protected.items())
    assert all(tasks[k]['status']=='done' for k in ['R23-01','R23-02','R23-03','R23-04']) and tasks['R23-next']['status']=='cancelled'
    assert not state['execution']['current_native_pending']
    note=dict(saved_at=ctl.stamp(),current_frontier_task='R23-next',task_status='cancelled_bounded_probe_complete',report='runs/R23/REPORT.md',
        original_attempt='R23-03-1 remains failed: j1 source-contract omission, j4 strict diagnosis-withholding unverified. First independent verdict and root receiving composition remain original.',
        current_attempt=tasks['R23-03']['attempts'][-1]['id'],R23_repairs=tasks['R23-03']['repairs_used'],R23_repair_limit=tasks['R23-03']['repair_limit'],
        evidence=['runs/R23/final/SYNTHESIS.md','runs/R23/clean-reception-lock.json','runs/R23/closure.json'],
        C13='Nine pure Markdown unchanged; all computation/receipt/control scripts remain R&D only.',current_lease_release=lease,actual_lease_session=93759,probe=probe,actors_pending=[],
        protected_tasks=len(protected),old_failures_budgets_preserved=True,R16_count=tasks['R16-02']['repairs_used'],next_action=tasks['R23-next']['next_action'],
        full_handoff_identity_command='runs/R23/closure-handoff-command.json',
        limits='Known synthetic data; one-day consumer point slice only; no new full42-day production/paper,reliability,award,causal skill gain,four-level rerun or formalOctober compliance.',
        last_observed_source_commit=state['execution'].get('current_source_commit'),last_observed_source_ci=state['execution'].get('current_source_ci'),
        unresolved_historical_call=read('state/checkpoint.json').get('unresolved_historical_call'),background_schedule=False,model=None,tokens=None,cost=None)
    path='runs/R23/handback.json';assert not (ROOT/path).exists();ctl.write_json(ROOT/path,note)
    state['execution'].update(final_lease_release=path,coordinator_release_evidence=path,current_report='runs/R23/REPORT.md',coordinator_heartbeat=ctl.stamp(),
        current_task_process_state='Bounded R23 probe complete, successor cancelled; no current actor/background scheduler, actual lease released.')
    assert not ctl.validate(state,ROOT)
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json');cp.update(current_report='runs/R23/REPORT.md',current_native_pending=[],next_action=note['next_action'],handback=path,actual_lease_release=path,
        termination='bounded_probe_complete_no_successor_no_live_actor',unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(frontier='R23-next_cancelled',lease_released_probe_free=True,protected_tasks=len(protected),R23_repairs=note['R23_repairs'],queue_valid=True)))
