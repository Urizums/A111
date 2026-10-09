"""Prepare and receive the actual successor audit, retaining every older task."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl

p=argparse.ArgumentParser(); p.add_argument('action',choices=['prepare','integrate']); a=p.parse_args()
def read(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def save(rel,obj):
    assert not (ROOT/rel).exists(),rel
    ctl.write_json(ROOT/rel,obj)
def freeze(rel,paths):
    entries=[]
    for name in paths:
        b=(ROOT/name).read_bytes()
        entries.append(dict(path=name,size_bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    save(rel,dict(schema='forge-revision-lock/1',revision='R22 '+a.action,frozen_at=ctl.stamp(),files=entries,
                  claim='Source/actual audit identity only; not 42-day performance or blind acceptance.'))
    index=read('state/revision-locks.json'); assert rel not in index['locks']; index['locks'].append(rel)
    ctl.write_json(ROOT/'state/revision-locks.json',index)
with ctl.locked(ROOT):
    state=ctl.load(ROOT); tasks=ctl.task_map(state)
    old66=read('runs/R21/before/task-identities.json')
    assert all(ctl.identity(tasks[k])==v for k,v in old66.items())
    assert tasks['R21-03']['status']=='done' and not state['execution']['current_native_pending']
    if a.action=='prepare':
        save('runs/R22/before/task-identities.json',{k:ctl.identity(v) for k,v in tasks.items()})
        save('runs/R22/source-inputs.json',dict(sources=[ctl.ref(ROOT,r) for r in [
            'runs/R21/input-lock.json','runs/R21/execution-lock.json',
            'runs/R20/final/candidate/C13-lock.json','runs/R21/review/initial/result.json']],
            scope='Existing known historical data and independently received horizon limitation; no future truth or new model.'))
        freeze('runs/R22/source-lock.json',['runs/R22/PLAN.md','runs/R22/audit_sources.py',
               'runs/R22/source-inputs.json','runs/R22/before/task-identities.json'])
    else:
        old70=read('runs/R22/before/task-identities.json')
        assert all(ctl.identity(tasks[k])==v for k,v in old70.items())
        receipt='runs/R22/audit/first-step-command.json'
        command=read(receipt); assert command['state']=='finished' and command['exit_code']==0
        probe=read('runs/R22/audit/source-availability.json')
        assert len(probe['windows'])==3 and all(w['dates']==42 and w['mature_label_keys']==4032 for w in probe['windows'])
        assert probe['boundary_control']['complete_window_rejected']
        ctl.begin(state,ROOT,'R21-next',receipt)
        first=dict(id='R22-01',title='42日历史窗口及信息可用性真实审计',depends_on=['R21-next'],write_paths=['runs/R22/audit/'],
            acceptance=[dict(id='t1',assertion='Actual raw historical 42-day availability, versions, full residual day lineage, activity cells and overlap audited; no fitting, future truth or performance claim.')])
        definitions=[first,
            dict(id='R22-02',title='同期限固定策略历史计算与独立实质接收',depends_on=['R22-01'],write_paths=['runs/R22/execution/','runs/R22/review/'],
                acceptance=[dict(id='t1',assertion='Source-bound pre-compute protocol, actual same-origin 42-day fair historical experiment and fresh independent recomputation/consumer receiving; failures/repairs and known-data limits retained.')]),
            dict(id='R22-03',title='同期限证据综合与有依据的纯文档源迭代',depends_on=['R22-02'],write_paths=['runs/R22/final/','runs/R22/candidate/'],
                acceptance=[dict(id='t1',assertion='Actual evidence synthesis; only a demonstrated source gap permits a new pure-document revision with affected prospective reception; otherwise retain C13, no causal/award claims.')]),
            dict(id='R22-next',title='启动下一阶段任务',depends_on=['R22-03'],write_paths=['runs/R23/'],
                acceptance=[dict(id='t1',assertion='A meaningful remaining goal has a source-bound successor plan and real first step; completion/boundary permits explicit end without invented endless work.')])]
        for definition in definitions:
            assert definition['id'] not in tasks
            definition.update(queue='challenges',category='horizon_aligned_validation',complexity=3,priority=22,owner='root',
                inputs=['runs/R22/PLAN.md','runs/R22/source-lock.json'],status='planned',evidence=[],attempts=[],
                repairs_used=0,repair_limit=None,blocker=None,next_action=definition['title'],
                execution_policy=dict(mode='progress_guard',source=ctl.ref(ROOT,'runs/R22/PLAN.md'),
                    stop_conditions=['completion','actual host/resource boundary','user stop','unchanged path without new evidence'],
                    progress_state='ready',deadline_utc=None))
            state['tasks'].append(definition)
        transition=tasks['R21-next']; attempt=transition['attempts'][-1]
        save('runs/R21/successor-transition-result.json',dict(task_id='R21-next',attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
            criteria=[dict(id='t1',status='pass',evidence=['runs/R22/PLAN.md','runs/R22/source-lock.json',receipt,'runs/R22/audit/source-availability.json'])],
            effect=dict(target=transition['title'],hypothesis='Known horizon mismatch warrants evidence feasibility audit before another method.',baseline='R21 actual historical windows are only 14 days.',
                conditions='R21 five-gate reception complete; same historical inputs; no fitting or future measurement.',observations=probe,
                metrics=dict(model=None,tokens=None,cost=None),limits='Audit only; does not establish long-horizon accuracy, causality or source superiority.'),
            next_action='R22-02: freeze same-horizon research protocol and execute with independent receiving.',
            successor=dict(plan='runs/R22/PLAN.md',first_task_id='R22-01',actual_start=receipt)))
        ctl.finish(state,ROOT,'R21-next','runs/R21/successor-transition-result.json')
        ctl.begin(state,ROOT,'R22-01',receipt)
        first=ctl.task_map(state)['R22-01']; attempt=first['attempts'][-1]
        save('runs/R22/R22-01-result.json',dict(task_id='R22-01',attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
            criteria=[dict(id='t1',status='pass',evidence=[receipt,'runs/R22/audit/source-availability.json'])],
            effect=dict(target=first['title'],hypothesis='42-day historical audit can distinguish available data from missing validation.',baseline='First two windows deliberately non-overlapping; last window reaches historical endpoint.',
                conditions='Frozen plan/source; public historical raw and original forecast provenance only.',observations=probe,
                metrics=dict(model=None,tokens=None,cost=None),limits='Root structural audit, not independent scientific receiving or model performance.'),
            next_action='R22-02: first freeze protocol/as-of 42-day reproduction and reviewer task; existing history is known, not blind new truth.'))
        ctl.finish(state,ROOT,'R22-01','runs/R22/R22-01-result.json')
        freeze('runs/R22/audit-lock.json',['runs/R22/audit/source-availability.json',receipt,'runs/R22/R22-01-result.json'])
        assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old70.items() if k!='R21-next')
        save('runs/R22/transition-preservation.json',dict(previous_tasks=70,unchanged_tasks=69,
            sole_changed_previous_task='R21-next: authorized actual successor transition',old66_unchanged=True,
            R16_02_current_count_preserved=ctl.task_map(state)['R16-02']['repairs_used'],
            source_rule='No older acceptance, policy, counter or verdict changed.'))
        state['execution'].update(current_frontier_task='R22-02',current_report='runs/R22/REPORT.md',
            current_task_process_state='R22-01 actual historical audit done; R22-02 ready, no model or background actor started.',
            R21_status='complete_with_first_five_gate_reception_and_below_nominal_coverage',R22_status='first_source_availability_audit_done')
        project=read('state/project-todo.json')
        prior=next(t for t in project['todo'] if t['id']=='R21-interval-reliability')
        prior.update(status='done',next_action='R22-02: same-horizon actual research and independent receiving')
        for rel in ['runs/R21/R21-03-result.json','runs/R21/successor-transition-result.json','runs/R21/final-lock.json']:
            if rel not in prior['evidence']: prior['evidence'].append(rel)
        project['todo'].append(dict(id='R22-horizon-aligned-validation',title='对齐固定42日预测期限的验证证据',status='in_progress',
            owner='root',depends_on=['R21-interval-reliability'],write_paths=['runs/R22/'],
            acceptance=['同期限真实计算及独立接收；确证源缺口才升级纯文档skill'],
            evidence=['runs/R22/PLAN.md','runs/R22/audit-lock.json'],blocker=None,next_action=ctl.task_map(state)['R22-02']['next_action']))
        ctl.write_json(ROOT/'state/project-todo.json',project)
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old66.items())
    assert not ctl.validate(state,ROOT)
    ctl.write_json(ROOT/'state/continuation.json',state); ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json'); frontier=state['execution']['current_frontier_task']
    cp.update(current_frontier_task=frontier,current_report=state['execution']['current_report'],
              next_action=ctl.task_map(state)[frontier]['next_action'],current_native_pending=[],termination=None,unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(action=a.action,frontier=frontier,old66_preserved=True,queue_valid=True)))
