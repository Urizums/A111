from pathlib import Path
import json
import sys

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'scripts'))
import continuation as ctl

with ctl.locked(root):
    state=ctl.load(root)
    task=ctl.task_map(state)['R11-01'];attempt=task['attempts'][-1]
    observed=json.loads((root/'runs/R11/package/standalone-result.json').read_text(encoding='utf-8'))
    assert observed['ok'] and len(observed['files'])==5 and observed['byte_identical']
    result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],criteria=[dict(id='a1',status='pass',evidence=['runs/R11/package/first-command.json','runs/R11/package/standalone-result.json','runs/R11/package/quick-validate-command.json']),dict(id='a2',status='pass',evidence=['runs/R11/PLAN.md','runs/R11/package/standalone-result.json'])],effect=dict(target='Portable pure-document skill delivery',hypothesis='Frozen method files can be distributed without repository runtime helpers',baseline='C8 locked five Markdown files; R09 tools require Linux APIs',conditions='Windows Python3.12.8 packaging, independent newly extracted directory, same C8 bytes',observations='zip created and extracted; all five source/output/extracted files equal; links stay inside package; standalone frontmatter validation passes',limits='Structure and real packaging only; no personal installation, behavior/performance/generalization claim',metrics=dict(files=5,script_files=0,test_files=0,archive_bytes=observed['archive_size_bytes'],repairs_used=0,tokens=None,cost=None)),next_action='R11-02 requires frozen actual R10 outputs and independent continuation execution')
    p=root/'runs/R11/R11-01-result.json'
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    terminal=ctl.finish(state,root,'R11-01','runs/R11/R11-01-result.json')
    state['events'].append(dict(at=ctl.stamp(),command='finish',result=terminal))
    r09=root/'state/phases/R09.json'
    phase=ctl.phase_view(json.loads(r09.read_text(encoding='utf-8')),state)
    last=phase['tasks'][-1]
    assert all(t['status']=='done' for t in phase['tasks'][:-1])
    last.update(status='done',evidence=['runs/R11/package/first-command.json','runs/R11/PLAN.md'],blocker=None,next_action='Continue already-started standalone method branch',transition=dict(next_phase_id='R11',todo_path='state/phases/R11.json',first_task_id='R11-01',start_evidence=['runs/R11/package/first-command.json']))
    ctl.write_json(r09,phase)
    r11=root/'state/phases/R11.json'
    ctl.write_json(r11,ctl.phase_view(json.loads(r11.read_text(encoding='utf-8')),state))
    state['events'].append(dict(at=ctl.stamp(),command='complete_R09_distinct_branch_successor',result=dict(actual_first_step='runs/R11/package/first-command.json',active_R08_unchanged=True,R10_behavior_pending=True)))
    ctl.write_json(root/'state/continuation.json',state)
    project=json.loads((root/'state/project-todo.json').read_text(encoding='utf-8'))
    project['standalone_method_R11']=dict(plan='runs/R11/PLAN.md',actual_first_step='runs/R11/package/first-command.json',package_result='runs/R11/package/standalone-result.json',R11_01='done',R11_02='planned_pending_R10_02',R09_branch_completed_with_successor=True)
    project['updated_at']=ctl.stamp()
    ctl.write_json(root/'state/project-todo.json',project)
    ctl.synchronize(root,state)
print(json.dumps(dict(R11_01='done',R09_next='done',active_phase='R08',R10_next='pending')))
