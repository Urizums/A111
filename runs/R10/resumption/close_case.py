from pathlib import Path
import hashlib
import json
import sys

root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'scripts'))
import continuation as ctl

with ctl.locked(root):
    state=ctl.load(root)
    task=ctl.task_map(state)['R10-02'];attempt=task['attempts'][-1]
    terminal=json.loads((root/'runs/R10/resumption/native-terminal.json').read_text(encoding='utf-8'))
    source=root/'runs/R10/validation/independent/evidence/first-command.json'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==terminal['original_record_current_sha256']
    result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],criteria=[dict(id='a1',status='fail',evidence=['runs/R10/validation/request.json','runs/R10/validation/packet.json','runs/R10/validation/independent/weekly-triage-workflow.md','runs/R10/validation/independent/next-week-handoff-template.md','runs/R10/validation/independent/batch-triage.md','runs/R10/resumption/artifact-review.md']),dict(id='a2',status='fail',evidence=['runs/R10/resumption/native-terminal.json','runs/R10/resumption/first-command-terminal.json','runs/R10/resumption/decision.json'])],effect=dict(target='Fresh-context workflow design and actual feedback batch',hypothesis='A pure method skill can guide a portable workflow and checked batch without its inherited execution platform',baseline='Frozen C8 and feedback-2026-w40; original user meta-workflow scope',conditions='Same fresh Luna-requested context resumed after quota interruption, original input and output directory, correction_limit2',observations='Three method/handoff/batch drafts exist. Input snapshot contains8 rows. No raw-input verification or worker result. Known F3 wording defect; drafts self-label finished despite unverified outcome. Three recording/orchestration corrections exceed2.',limits='Partial artifact observations only, no independent behavioral pass, performance/generalization or product acceptance; raw path-lookup error text unavailable on disk and reported as such; requested model is not authenticated exact provider telemetry',metrics=dict(draft_artifacts=3,input_rows=8,actor_corrections_used=3,actor_limit=2,coordinator_corrections_used=2,coordinator_limit=2,candidate_source_repairs=0,tokens=None,cost=None)),next_action='Retain exhausted original case and drafts; do not retry or substitute. Distribution exists as C8 development candidate only.')
    target=root/'runs/R10/R10-02-result.json'
    with target.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    # This is the observed internal correction count, not a new task restart.
    task['repairs_used']=terminal['actor_corrections_used']
    outcome=ctl.finish(state,root,'R10-02','runs/R10/R10-02-result.json')
    state['events'].append(dict(at=ctl.stamp(),command='finish',result=outcome))
    task['blocker']='Original actor used3 corrections against limit2; three drafts remain unverified. Same-case retry/substitute forbidden.'
    planned=ctl.task_map(state)['R11-02']
    planned.update(status='blocked',blocker='Required accepted R10 batch/checkpoint is unavailable because the original R10-02 case exhausted its budget',evidence=[ctl.ref(root,'runs/R10/R10-02-result.json')],next_action='Retain planned acceptance and zero attempts; do not fabricate accepted checkpoint or replace failed batch')
    state['execution'].update(session_state='checkpoint_for_C8_development_candidate',native_pending=[],current_native_pending=[],current_report='runs/R10/REPORT.md',next_plan='runs/R11/PLAN.md',checkpoint_reason='R09 independent pass integrated; C8 pure-document authoring/package done; R10 original actor failed3/2 with unchecked drafts; dependent continuation blocked',coordinator_heartbeat=ctl.stamp())
    state['execution'].setdefault('completed_native_R10',[]).append(dict(worker='/root/c8_workflow_trial',state='terminal_failure_received_budget_exceeded',evidence='runs/R10/resumption/native-terminal.json'))
    assert not ctl.validate(state,root)
    ctl.write_json(root/'state/continuation.json',state)
    for pid in ['R10','R11']:
        path=root/f'state/phases/{pid}.json'
        phase=ctl.phase_view(json.loads(path.read_text(encoding='utf-8')),state)
        last=phase['tasks'][-1]
        last.update(status='blocked',blocker='Required behavioral predecessor failed its frozen bounded acceptance',evidence=['runs/R10/R10-02-result.json'],next_action='Preserve branch history and unmet acceptance; no fabricated stage transition')
        ctl.write_json(path,phase)
    ctl.synchronize(root,state)
    project=json.loads((root/'state/project-todo.json').read_text(encoding='utf-8'))
    project['meta_workflow_scope_R10'].update(current_frontier='blocked_original_behavior_case',authoring='done',independent_evaluation='failed3_over2_unverified_drafts',report='runs/R10/REPORT.md',R10_next='blocked',no_budget_reset=True)
    project['standalone_method_R11'].update(R11_02='blocked_dependency_on_R10_02',R11_next='blocked')
    project['updated_at']=ctl.stamp()
    ctl.write_json(root/'state/project-todo.json',project)
    cp=json.loads((root/'state/checkpoint.json').read_text(encoding='utf-8'))
    cp.update(current_validation='C8 authoring/structure and R11 actual independent packaging passed; R09 fresh-checkout checks passed; R10 original actor failed3/2 and raw-input check absent; R10/R11 dependent transitions blocked',current_native_pending=[],R10_current_budget=dict(actor_used=3,actor_limit=2,coordinator_used=2,coordinator_limit=2,candidate_source_repairs=0,evidence='runs/R10/resumption/native-terminal.json'),R11_actual_first_step='runs/R11/package/first-command.json',unpublished_work=True)
    ctl.write_json(root/'state/checkpoint.json',cp)
print(json.dumps(dict(R10_02=outcome['status'],observed_actor_budget='3/2',R11_01='done',R11_02='blocked',native_pending=[])))
