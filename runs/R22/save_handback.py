"""Save actual lease release and the completed successor first step."""
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
def read(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
lease=read('state/coordinator-lease.json')
assert lease['owner']=='root-codex-r21-prospective' and lease['pid']==367 and lease.get('released_at')
probe=json.loads(subprocess.check_output([sys.executable,'scripts/coordinator_lease.py','probe','--root',str(ROOT)],cwd=ROOT,text=True))
assert not probe['busy']
check=read('runs/R22/final-handoff-check-command.json')
assert check['state']=='finished' and check['exit_code']==0 and json.loads(check['stdout'])['ok']
with ctl.locked(ROOT):
    state=ctl.load(ROOT); tasks=ctl.task_map(state)
    old=read('runs/R22/before/task-identities.json')
    assert all(ctl.identity(tasks[k])==v for k,v in old.items() if k!='R21-next')
    assert tasks['R21-next']['status']=='done' and tasks['R22-01']['status']=='done' and tasks['R22-02']['status']=='planned'
    assert not state['execution']['current_native_pending']
    path='runs/R22/handback.json'; assert not (ROOT/path).exists()
    note=dict(saved_at=ctl.stamp(),current_frontier_task='R22-02',task_status='ready_not_started',report='runs/R22/REPORT.md',
        R21='Complete first 13-page Chinese scientific consumer, independent g1-g4, then frozen g5; below nominal coverage retained.',
        R22_01='Actual 42-day historical availability audit done; no model fitted or future truth read.',
        C13='Nine pure Markdown unchanged; scripts/tests remain R&D only.',
        current_lease_release=lease,actual_lease_session=20564,probe=probe,actors_pending=[],
        previous_tasks=70,unchanged_tasks=69,sole_changed_previous_task='R21-next authorized actual transition',
        R16_count=tasks['R16-02']['repairs_used'],old_failures_and_budgets_preserved=True,
        next_action=tasks['R22-02']['next_action'],full_handoff_identity_command='runs/R22/final-handoff-check-command.json',
        metadata_check='Unchanged real POSIX queue controller validates this final metadata; no task semantics changed after full identity check.',
        publication='Ready for authorized main commit; exact committed bytes and CI observations recorded separately afterwards.',
        last_observed_source_commit=state['execution'].get('current_source_commit'),
        last_observed_source_ci=state['execution'].get('current_source_ci'),
        limits='One synthetic case, known-history follow-up; no causal skill/prize/real-business claims. Official October AI/submission supplements still unknown.',
        unresolved_historical_call=read('state/checkpoint.json').get('unresolved_historical_call'),
        background_schedule=False,model=None,tokens=None,cost=None)
    ctl.write_json(ROOT/path,note)
    prior={k:state['execution'].get(k) for k in ['current_coordinator','coordinator_heartbeat','final_lease_release','coordinator_release_evidence']}
    state['execution'].setdefault('historical_coordinator_snapshots',[]).append(dict(at=ctl.stamp(),fields=prior,
        note='Actual R21 owner released after R21 closure and R22 real first step; prior aliases retained.'))
    state['execution'].update(current_coordinator=lease['owner'],coordinator_heartbeat=ctl.stamp(),
        final_lease_release=path,coordinator_release_evidence=path,current_frontier_task='R22-02',current_report='runs/R22/REPORT.md',
        current_task_process_state='R22-02 ready; no current worker or background scheduler; actual coordinator lease released.')
    assert not ctl.validate(state,ROOT)
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json'); cp.update(current_frontier_task='R22-02',current_report='runs/R22/REPORT.md',
        current_native_pending=[],next_action=note['next_action'],handback=path,actual_lease_release=path,
        termination='stage_result_and_actual_successor_first_step_saved_no_live_actor',unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(frontier='R22-02_ready',lease_released_probe_free=True,previous69_tasks_unchanged=True,queue_valid=True)))
