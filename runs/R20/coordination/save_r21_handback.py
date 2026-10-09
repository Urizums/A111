"""Save actual released coordinator and ready frontier without old-owner aliases."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
lease=read('state/coordinator-lease.json')
assert lease['owner']=='root-codex-r20-data-transfer' and lease.get('released_at')
probe=json.loads(subprocess.check_output([sys.executable,'scripts/coordinator_lease.py','probe','--root',str(ROOT)],cwd=ROOT,text=True))
assert not probe['busy']
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    old=read('runs/R21/before/task-identities.json')
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items())
    assert not state['execution']['current_native_pending']
    assert ctl.task_map(state)['R21-01']['status']=='done' and ctl.task_map(state)['R21-02']['status']=='planned'
    command=read('runs/R20/coordination/r21-complete-composed-check-command.json')
    assert command['state']=='finished' and command['exit_code']==0 and json.loads(command['stdout'])['ok']
    relative='runs/R21/handback.json'
    assert not (ROOT/relative).exists()
    observation=dict(saved_at=ctl.stamp(),current_frontier_task='R21-02',task_status='ready_not_started',
        report='runs/R21/REPORT.md',R20='full_paper_and_source_synthesis_closed_successor_actual_first_step',
        C13='nine_Markdown_one_conditional_paragraph_first_forward_f1_f3_accepted',
        R21_01='known_truth_descriptive_diagnostic_done',old_L3_a6='partial_preserved',
        current_lease_release=lease,probe=probe,actors_pending=[],old_task_identities_preserved=len(old),
        next_action='R21-02: freeze new original inputs and prospective fair protocol; never reuse known R20 truth as a new blind test.',
        publication='New source/artifacts ready for authorized main commit; actual commit and CI observations follow separately.',
        last_observed_source_commit=state['execution'].get('current_source_commit'),
        last_observed_source_ci=state['execution'].get('current_source_ci'),
        full_handoff_identity_command='runs/R20/coordination/r21-complete-composed-check-command.json',
        native_windows_full_check='Original fcntl unsupported and slow WSL receipts retained; every original checker predicate performed, file checks native and real POSIX queue delegated with same snapshot hashes. Controller unchanged.',
        frozen_style='Two exact locked EOF blank findings retained and classified; all other index files checked.',
        budgets_reset=False,background_schedule=False,model=None,tokens=None,cost=None)
    ctl.write_json(ROOT/relative,observation)
    previous={k:state['execution'].get(k) for k in ['current_coordinator','coordinator_heartbeat','final_lease_release','coordinator_release_evidence']}
    state['execution'].setdefault('historical_coordinator_snapshots',[]).append(dict(at=ctl.stamp(),fields=previous,
        note='Retained inherited aliases; current release now binds the actual R20 owner and current handback.'))
    state['execution'].update(current_coordinator='root-codex-r20-data-transfer',coordinator_heartbeat=ctl.stamp(),
        final_lease_release=relative,coordinator_release_evidence=relative,
        current_task_process_state='No live actors/processes; R21-02 ready, no background scheduler.',
        current_frontier_task='R21-02',current_report='runs/R21/REPORT.md')
    assert not ctl.validate(state,ROOT)
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json');cp.update(current_frontier_task='R21-02',current_report='runs/R21/REPORT.md',
        current_native_pending=[],next_action=observation['next_action'],handback=relative,actual_lease_release=relative,
        termination='stage_result_and_actual_successor_first_step_saved_no_live_actor',unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(frontier='R21-02_ready',lease_released_probe_free=True,previous_task_identities_preserved=66,queue_valid=True)))
