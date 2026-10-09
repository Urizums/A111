"""Save actual current lease release; do not overwrite the previous R21 handback."""
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
lease=read('state/coordinator-lease.json')
assert lease['owner']=='root-codex-r22-horizon' and lease['pid']==267 and lease.get('released_at')
probe=json.loads(subprocess.check_output([sys.executable,'scripts/coordinator_lease.py','probe','--root',str(ROOT)],cwd=ROOT,text=True))
assert not probe['busy']
check=read('runs/R22/closure-handoff-check-command.json')
assert check['state']=='finished' and check['exit_code']==0 and json.loads(check['stdout'])['ok']
with ctl.locked(ROOT):
    state=ctl.load(ROOT);tasks=ctl.task_map(state)
    before=read('runs/R22/before-execution/task-identities.json')
    assert all(ctl.identity(tasks[k])==v for k,v in before.items() if k not in ['R22-02','R22-03','R22-next'])
    assert all(tasks[k]['status']=='done' for k in ['R22-02','R22-03','R22-next','R23-01'])
    assert tasks['R23-02']['status']=='planned' and not state['execution']['current_native_pending']
    path='runs/R22/handback2.json';assert not (ROOT/path).exists()
    note=dict(saved_at=ctl.stamp(),current_frontier_task='R23-02',task_status='ready_not_started',report='runs/R23/REPORT.md',
        R22='Original fresh independent h1-h5 pass; first h6 fail; v2 author-only failure; actual informed v3 h6 reception passed. All reports/verdicts unchanged, scientific bytes unchanged.',
        R22_repairs=tasks['R22-02']['repairs_used'],R22_repair_limit=tasks['R22-02']['repair_limit'],
        R23_01='Actual source-frozen original-CSV audit complete; no new workflow constructed, model fitted, consumer slice or independent design verdict.',
        C13='Nine pure Markdown unchanged; scripts/tests R&D only; source decision bound to ten actual clauses.',
        current_lease_release=lease,actual_lease_session=43407,probe=probe,actors_pending=[],
        protected_tasks=71,old_failures_budgets_preserved=True,R16_count=tasks['R16-02']['repairs_used'],
        next_action=tasks['R23-02']['next_action'],full_handoff_identity_command='runs/R22/closure-handoff-check-command.json',
        limits='Known synthetic replay; no causal skill gain, four-level rerun, award, real-business or formalOctober compliance claim. Document context exposure disclosed.',
        last_observed_source_commit=state['execution'].get('current_source_commit'),last_observed_source_ci=state['execution'].get('current_source_ci'),
        unresolved_historical_call=read('state/checkpoint.json').get('unresolved_historical_call'),background_schedule=False,model=None,tokens=None,cost=None)
    ctl.write_json(ROOT/path,note)
    state['execution'].update(final_lease_release=path,coordinator_release_evidence=path,current_frontier_task='R23-02',current_report='runs/R23/REPORT.md',
        coordinator_heartbeat=ctl.stamp(),current_task_process_state='R23-02 ready; no current actor or background scheduler; actual R22 coordinator lease released.')
    assert not ctl.validate(state,ROOT)
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json');cp.update(current_frontier_task='R23-02',current_report='runs/R23/REPORT.md',current_native_pending=[],
        next_action=note['next_action'],handback=path,actual_lease_release=path,termination='stage_result_and_actual_successor_first_step_saved_no_live_actor',unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(frontier='R23-02_ready',lease_released_probe_free=True,old71_preserved=True,R22_repairs=note['R22_repairs'],queue_valid=True)))
