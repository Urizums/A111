"""Install a bounded design probe only after R22 reception and source synthesis."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','integrate']);a=p.parse_args()
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def save(rel,obj):
    assert not (ROOT/rel).exists(),rel
    ctl.write_json(ROOT/rel,obj)
def freeze(rel,paths):
    files=[]
    for name in paths:
        b=(ROOT/name).read_bytes();files.append(dict(path=name,size_bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    save(rel,dict(schema='forge-revision-lock/1',revision='R23 '+a.action,frozen_at=ctl.stamp(),files=files,
        claim='Immutable source/actual first-audit bytes; no independent design or scientific performance claim.'))
    index=read('state/revision-locks.json');assert rel not in index['locks'];index['locks'].append(rel)
    ctl.write_json(ROOT/'state/revision-locks.json',index)
with ctl.locked(ROOT):
    state=ctl.load(ROOT); tasks=ctl.task_map(state)
    assert tasks['R22-02']['status']=='done' and tasks['R22-03']['status']=='done'
    assert not state['execution']['current_native_pending']
    old=read('runs/R22/before-execution/task-identities.json')
    assert all(ctl.identity(tasks[k])==v for k,v in old.items() if k not in ['R22-02','R22-03','R22-next'])
    if a.action=='prepare':
        save('runs/R23/before/task-identities.json',{k:ctl.identity(v) for k,v in tasks.items()})
        save('runs/R23/source-inputs.json',dict(sources=[ctl.ref(ROOT,rel) for rel in [
            'runs/R20/final/candidate/C13-lock.json','runs/R21/input-lock.json','runs/R22/final-lock.json']],
            scope='Known original raw input and current pure-document source; previous outcomes are root rationale only, withheld from new designer.'))
        freeze('runs/R23/source-lock.json',['runs/R23/PLAN.md','runs/R23/acceptance.json','runs/R23/audit_raw.py',
            'runs/R23/brief/TASK.md','runs/R23/brief/INPUTS.json','runs/R23/source-inputs.json','runs/R23/before/task-identities.json'])
    else:
        before=read('runs/R23/before/task-identities.json');assert all(ctl.identity(tasks[k])==v for k,v in before.items())
        receipt='runs/R23/audit/first-step-command.json';command=read(receipt)
        assert command['state']=='finished' and command['exit_code']==0
        probe=read('runs/R23/audit/INPUT_AUDIT.json')
        assert not probe['model_fitted'] and not probe['future_actuals_read'] and not probe['previous_design_results_read']
        assert probe['delivery_dates']==42 and probe['required_future_keys']==4032
        ctl.begin(state,ROOT,'R22-next',receipt)
        definitions=[
            ('R23-01','固定交付范围与中性输入真实审计',['R22-next'],['runs/R23/audit/'],
                'Frozen neutral task/raw identities and actual raw availability audit; no previous design, private truth, fitting or design-acceptance claim.'),
            ('R23-02','新上下文自主制作验证与执行工作流',['R23-01'],['runs/R23/design/'],
                'Actual fresh-context C13 workflow derived from neutral task and original business inputs, with transferable decision/evidence/execution/receiving interfaces; no coordinator detailed protocol or prior diagnoses supplied.'),
            ('R23-03','另一消费者真实切片与独立设计接收',['R23-02'],['runs/R23/execution/','runs/R23/review/'],
                'Actual meaningful designed slice plus fresh source-based j1-j4 reception, including supported scope, relevant boundary and language; slice does not establish full paper or causal performance.'),
            ('R23-04','设计证据综合及受影响源接收',['R23-03'],['runs/R23/final/','runs/R23/candidate/'],
                'Only a confirmed general source gap causes a new pure-document revision and affected forward reception; otherwise preserve C13 and close bounded probe, no award/causal claims.'),
            ('R23-next','启动下一阶段任务',['R23-04'],['runs/R24/'],
                'Close this bounded probe explicitly when complete; only a concrete material remaining goal warrants another source-bound plan and actual first step.')]
        for identity,title,deps,writes,assertion in definitions:
            assert identity not in tasks
            state['tasks'].append(dict(id=identity,title=title,depends_on=deps,write_paths=writes,
                acceptance=[dict(id='t1',assertion=assertion)],queue='challenges',category='autonomous_validation_design',
                complexity=3,priority=23,owner='root',inputs=['runs/R23/PLAN.md','runs/R23/source-lock.json'],
                status='planned',evidence=[],attempts=[],repairs_used=0,repair_limit=None,blocker=None,next_action=title,
                execution_policy=dict(mode='progress_guard',source=ctl.ref(ROOT,'runs/R23/PLAN.md'),
                    stop_conditions=['completion','actual host/resource boundary','user stop','unchanged path without new evidence'],
                    progress_state='ready',deadline_utc=None)))
        transition=tasks['R22-next']; attempt=transition['attempts'][-1]
        result=dict(task_id=transition['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
            criteria=[dict(id='t1',status='pass',evidence=['runs/R23/PLAN.md','runs/R23/source-lock.json',receipt,'runs/R23/audit/INPUT_AUDIT.json'])],
            effect=dict(target=transition['title'],hypothesis='Detailed coordinator protocol does not establish autonomous workflow-design ability.',
                baseline='R22 fixed-policy computation used a detailed prewritten root protocol.',conditions='R22 actual reception and source synthesis complete; bounded known-input design probe.',
                observations=probe,metrics=dict(actual_model=None,tokens=None,cost=None),limits='Actual raw first step only; no workflow constructed, slice executed or new performance/causal claim.'),
            next_action='R23-02: fresh C13 workflow builder receives only neutral business task/raw sources; reception rubric withheld.',
            successor=dict(plan='runs/R23/PLAN.md',first_task_id='R23-01',actual_start=receipt))
        save('runs/R22/successor-transition-result.json',result)
        ctl.finish(state,ROOT,'R22-next','runs/R22/successor-transition-result.json')
        ctl.begin(state,ROOT,'R23-01',receipt)
        first=ctl.task_map(state)['R23-01'];attempt=first['attempts'][-1]
        result.update(task_id='R23-01',attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
            next_action='R23-02: derive workflow without a prewritten experiment protocol or previous solution.',
            effect=dict(target=first['title'],hypothesis='Neutral raw-bound brief permits a bounded autonomous-design probe.',
                baseline='Same original known historical inputs, different role packet; not a new scientific sample.',conditions='Task/reception/source frozen before actual CSV audit.',
                observations=probe,metrics=dict(actual_model=None,tokens=None,cost=None),limits='Root input audit, not independent design acceptance or model execution.'))
        result.pop('successor')
        save('runs/R23/R23-01-result.json',result);ctl.finish(state,ROOT,'R23-01','runs/R23/R23-01-result.json')
        freeze('runs/R23/audit-lock.json',['runs/R23/audit/INPUT_AUDIT.json',receipt,'runs/R23/R23-01-result.json'])
        assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in before.items() if k!='R22-next')
        save('runs/R23/transition-preservation.json',dict(previous_tasks=len(before),unchanged_tasks=len(before)-1,
            sole_changed_task='R22-next authorized actual successor transition',old71_preserved=True,old_failures_budgets_preserved=True))
        project=read('state/project-todo.json');prior=next(t for t in project['todo'] if t['id']=='R22-horizon-aligned-validation')
        prior.update(status='done',next_action='R23-02: bounded autonomous validation-design probe')
        prior['evidence']+=['runs/R22/R22-02-result.json','runs/R22/R22-03-result.json','runs/R22/final-lock.json','runs/R22/successor-transition-result.json']
        project['todo'].append(dict(id='R23-autonomous-validation-design',title='自主推导验证范围的工作流接收探查',
            status='in_progress',owner='root',depends_on=['R22-horizon-aligned-validation'],write_paths=['runs/R23/'],
            acceptance=['真实新设计/消费切片及独立接收；确证源缺口才修纯文档；完成定界支线后结束'],
            evidence=['runs/R23/PLAN.md','runs/R23/source-lock.json','runs/R23/audit-lock.json'],blocker=None,
            next_action=ctl.task_map(state)['R23-02']['next_action']))
        ctl.write_json(ROOT/'state/project-todo.json',project)
        state['execution'].update(current_frontier_task='R23-02',current_report='runs/R23/REPORT.md',
            current_task_process_state='R23 input audit done, workflow design ready; no current actor or background scheduler.',
            R22_status='same_horizon_reception_and_source_synthesis_complete_C13_retained',R23_status='real_raw_first_step_done_design_not_started')
    assert not ctl.validate(state,ROOT)
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json');frontier=state['execution']['current_frontier_task']
    cp.update(current_frontier_task=frontier,current_report=state['execution']['current_report'],current_native_pending=[],
        next_action=ctl.task_map(state)[frontier]['next_action'],termination=None,unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(action=a.action,frontier=frontier,history_preserved=True,queue_valid=True)))
