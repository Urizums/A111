"""Root-only serial registration; retains every previous task object verbatim."""
import copy
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl

with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    old={t['id']:ctl.identity(t) for t in state['tasks']}
    before=ROOT/'runs/R19/before/task-identities.json'
    if before.exists():
        assert json.loads(before.read_text(encoding='utf-8'))==old
    else:
        ctl.write_json(before,old)
    def task(ident,title,dependencies,scope,inputs,acceptance):
        return dict(id=ident,title=title,queue='challenges',category='prospective_workflow_transfer_trial',complexity=3,
            priority=20,depends_on=dependencies,owner='root',write_paths=scope,inputs=inputs,acceptance=acceptance,
            status='planned',evidence=[],attempts=[],repairs_used=0,repair_limit=None,blocker=None,next_action=title,
            execution_policy=dict(mode='progress_guard',source=ctl.ref(ROOT,'runs/R19/PLAN.md'),
                stop_conditions=['actual host or permission boundary','user stop','completion','persistent unchanged path without new evidence'],
                progress_state='ready',deadline_utc=None))
    state['tasks'].append(task('R19-01','冻结四层原始输入、纯文档C11和独立验收',[],['runs/R19/candidate/','runs/R19/inputs/'],
        ['runs/R19/PLAN.md'],[dict(id='t1',assertion='Exact level inputs, same official raw materials, same document-only candidate and independent acceptance frozen before dispatch; old trials unchanged.')]))
    ctl.begin(state,ROOT,'R19-01','runs/R19/prepare-command.json')
    prep=ROOT/'runs/R19/preparation-result-v2.json'
    ctl.write_json(prep,dict(task_id='R19-01',attempt_id='R19-01-1',requirements_hash=ctl.identity(ctl.task_map(state)['R19-01']['acceptance']),
        criteria=[dict(id='t1',status='pass',evidence=['runs/R19/candidate/C11-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/acceptance.json'])],
        evidence=['runs/R19/candidate/C11-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/acceptance.json'],
        effect=dict(target='Prospective fair workflow transfer trial',hypothesis='Evidence-first paper decisions support sparse-input workflows; untested.',
            baseline='Frozen C10 and historical trials retained',conditions='Same C11 and raw question, exact L1-4',
            observations='9 Markdown files and 4 prompt files prepared; not behavior acceptance',limits='Preparation only',metrics=dict(documents=9,levels=4,papers=0)),
        next_action='L1 original-input workflow construction, fresh execution through paper, independent review.'))
    ctl.finish(state,ROOT,'R19-01','runs/R19/preparation-result-v2.json')
    for level in range(1,5):
        state['tasks'].append(task(f'R19-L{level}',f'Level{level}完整工作流转交执行及论文诊断',
            ['R19-01'] if level==1 else [f'R19-L{level-1}'],[f'runs/R19/levels/L{level}/'],
            [f'runs/R19/inputs/L{level}.md','runs/R19/candidate/C11-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/acceptance.json'],
            [dict(id='t1',assertion='Fresh builder produced transferable workflow from this level request/skill/raw input only, and a different fresh executor actually used it.'),
             dict(id='t2',assertion='Execution produced actual code/results/figures and a complete paper attempt covering original questions, with all missing or unsupported outcomes explicit.'),
             dict(id='t3',assertion='Fresh reviewer performed source/numerical/paper checks and returned original a1-a6 and quality verdicts; failed acceptance is retained, not equated with diagnostic task completion.')]))
    state['tasks'].append(task('R19-05','汇总四层行为并按证据检查源头设计',['R19-L4'],['runs/R19/final/'],
        ['runs/R19/acceptance.json'],[dict(id='t1',assertion='Four actual trials compared with original verdicts/failures and limits; any source revision has distinct identity and relevant forward check.')]))
    state['tasks'].append(task('R19-next','启动下一阶段任务',['R19-05'],['runs/R20/'],
        ['runs/R19/PLAN.md'],[dict(id='t1',assertion='A justified successor has a plan and actual task-relevant first step; a plan alone is not completion.')]))
    state['execution'].update(current_user_steering='Level1-4 only, sequential workflow construction/fresh execution through paper/independent substantive quality diagnosis.',
        current_candidate='runs/R19/candidate/C11-lock.json',current_report='runs/R19/PLAN.md',
        current_native_pending=[dict(worker='/root/r19_l1_builder',state='created_tool_return_received',actual_model=None)],
        native_pending_current=[dict(worker='/root/r19_l1_builder',state='created_tool_return_received',actual_model=None)],
        current_task_process_state='L1 workflow builder actually dispatched; real papers and independent reviews pending.',
        R19_scope='Four new prospective trials, not replacement acceptance or reset for R14/R16/R18; historical regular-contest practice, no prize claim.')
    assert all(ctl.identity(ctl.task_map(state)[ident])==digest for ident,digest in old.items())
    state['events'].append(dict(at=ctl.stamp(),command='register_user_four_level_trial',old_tasks_preserved=len(old)))
    ctl.write_json(ROOT/'state/continuation.json',state)
    ctl.synchronize(ROOT,state)
    cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
    cp.update(current_candidate='runs/R19/candidate/C11-lock.json',current_report='runs/R19/PLAN.md',
        current_native_pending=state['execution']['current_native_pending'],R19_status='L1_design_actually_started',
        next_action='Finish L1 workflow, transfer to fresh executor through paper, then fresh independent quality review. Levels2-4 follow sequentially; old R08 gate still unpassed.',unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
    project=json.loads((ROOT/'state/project-todo.json').read_text(encoding='utf-8'))
    project.setdefault('todo',[]).append(dict(id='R19-level1-4',owner='root',status='in_progress',write_scope=['runs/R19/'],
        acceptance='Independent sequential L1-4 workflow transfer through actual paper and evidence-backed quality review; diagnostic completion differs from quality pass.',
        evidence=['runs/R19/PLAN.md','runs/R19/candidate/C11-lock.json','runs/R19/acceptance.json'],
        next_action='L1 fresh builder→fresh executor→fresh reviewer.'))
    project['updated_at']=ctl.stamp()
    ctl.write_json(ROOT/'state/project-todo.json',project)
    errors=ctl.validate(state,ROOT)
    assert not errors,errors
print(json.dumps(dict(old_tasks_preserved=len(old),new_tasks=7,main_phase='R08_unpassed',R19='prepared_and_L1_builder_dispatched')))
