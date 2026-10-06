"""Coordinator-only progress checkpoint; development evidence outside the skill."""
from pathlib import Path
import json
import sys

root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'scripts'))
import continuation as ctl

with ctl.locked(root):
    state=ctl.load(root)
    state['execution'].update(current_coordinator='root-codex-meta-workflow', session_state='R10_independent_evaluation_running', current_native_pending=[dict(worker='/root/r09_independent', task='R09-02', creation='runs/R09/independent/creation-return.json'),dict(worker='/root/c8_workflow_trial',task='R10-02',creation='runs/R10/validation/creation-return.json')], native_pending=['/root/r09_independent','/root/c8_workflow_trial'], next_plan='runs/R10/PLAN.md', latest_scope_decision='runs/R10/scope-decision.json')
    start=root/'runs/R10/validation/independent/first-command.json'
    task=ctl.task_map(state)['R10-02']
    if start.is_file() and task['status']=='planned':
        record=json.loads(start.read_text(encoding='utf-8'))
        if record.get('state')=='finished':
            actual=ctl.begin(state,root,'R10-02',start.relative_to(root).as_posix())
            state['events'].append(dict(at=ctl.stamp(),command='start',result=actual))
    ctl.write_json(root/'state/continuation.json',state)
    for name in ['R09','R10']:
        path=root/f'state/phases/{name}.json'
        phase=json.loads(path.read_text(encoding='utf-8'))
        ctl.write_json(path,ctl.phase_view(phase,state))
    project=json.loads((root/'state/project-todo.json').read_text(encoding='utf-8'))
    project['meta_workflow_scope_R10'].update(current_frontier='R10-02',authoring='done',independent_evaluation='running')
    project['updated_at']=ctl.stamp()
    ctl.write_json(root/'state/project-todo.json',project)
    ctl.synchronize(root,state)
    cp=json.loads((root/'state/checkpoint.json').read_text(encoding='utf-8'))
    cp.update(current_validation='C8 document-only authoring/structure passed; fresh independent workflow batch in progress; R08 failures unchanged',meta_workflow_R10=dict(scope='runs/R10/scope-decision.json',candidate='runs/R10/candidate/C8-lock.json',plan='runs/R10/PLAN.md'),current_native_pending=state['execution']['current_native_pending'])
    ctl.write_json(root/'state/checkpoint.json',cp)
print(json.dumps(dict(R10_02=task['status'],active_phase='R08',pending=state['execution']['native_pending'])))
