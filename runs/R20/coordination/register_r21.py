"""Register the actual planned diagnostic and preserve all earlier task identities."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl

def read(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def freeze(scope, relative):
    assert not (ROOT/relative).exists()
    rows=[]
    for f in sorted((ROOT/scope).rglob('*')):
        if f.is_file() and '__pycache__' not in f.parts:
            b=f.read_bytes(); rows.append(dict(path=f.relative_to(ROOT).as_posix(),size_bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    ctl.write_json(ROOT/relative,dict(schema='forge-revision-lock/1',revision=scope,frozen_at=ctl.stamp(),files=rows,
        claim='Exact source-bound descriptive diagnostic and plan; no unseen performance or independent receiving claim.'))
    index=read('state/revision-locks.json');index['locks'].append(relative);ctl.write_json(ROOT/'state/revision-locks.json',index)
with ctl.locked(ROOT):
    state=ctl.load(ROOT);tasks=ctl.task_map(state)
    old=read('runs/R20/before/task-identities.json')
    assert all(ctl.identity(tasks[k])==v for k,v in old.items())
    assert tasks['R20-05']['status']=='done' and not state['execution']['current_native_pending']
    assert 'R21-01' not in tasks
    receipt='runs/R21/first-step-command.json'
    assert read(receipt)['state']=='finished' and read(receipt)['exit_code']==0
    first=read('runs/R21/diagnostic/result.json')
    assert first['reference_metrics_match'] and first['source_identity_verified'] and not first['model_tuned'] and not first['new_unseen_test']
    before={t['id']:ctl.identity(t) for t in state['tasks'] if t['id']!='R20-next'}
    def finish(ident, rel, evidence, target, observations, limits, next_action):
        task=ctl.task_map(state)[ident];attempt=task['attempts'][-1]
        assert not (ROOT/rel).exists()
        ctl.write_json(ROOT/rel,dict(task_id=ident,attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
            criteria=[dict(id='t1',status='pass',evidence=evidence)],effect=dict(target=target,
                hypothesis='Observed interval reliability limits justify a source-bound diagnostic before a new untouched measurement.',
                baseline='R20 original accepted paper/version and once-observed holdout retained.',
                conditions='Frozen inputs and already observed synthetic truth; no fitting, threshold retrofitting or model selection.',
                observations=observations,limits=limits,metrics=dict(tokens=None,cost=None)),next_action=next_action))
        ctl.finish(state,ROOT,ident,rel)
    ctl.begin(state,ROOT,'R20-next',receipt)
    finish('R20-next','runs/R21/transition-result.json',['runs/R21/PLAN.md','runs/R21/source-inputs.json',receipt,
        'runs/R21/diagnostic/result.json','runs/R21/diagnostic/REPORT.md'], 'Justified R21 actual first step',
        dict(first_task='R21-01',actual_step='Source-to-subgroup diagnostic executed',aggregate=first['aggregate']),
        'First diagnostic only; not new blind evaluation, improved model or formal contest evidence.',
        'R21-02: freeze a new untouched original measurement protocol before model variants or future truth.')
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in before.items())
    ctl.write_json(ROOT/'runs/R21/before/task-identities.json',{t['id']:ctl.identity(t) for t in state['tasks']})
    def make(ident,title,deps,paths,assertion):
        return dict(id=ident,title=title,queue='challenges',category='interval_reliability_transfer',complexity=3,priority=21,
            depends_on=deps,owner='root',write_paths=paths,inputs=['runs/R21/PLAN.md','runs/R21/source-inputs.json'],
            acceptance=[dict(id='t1',assertion=assertion)],status='planned',evidence=[],attempts=[],repairs_used=0,repair_limit=None,
            blocker=None,next_action=title,execution_policy=dict(mode='progress_guard',source=ctl.ref(ROOT,'runs/R21/PLAN.md'),
                stop_conditions=['actual host or permission boundary','user stop','completion','persistent unchanged path without new evidence'],progress_state='ready',deadline_utc=None))
    for definition in [
        ('R21-01','冻结旧版本的已见真值可靠性诊断',['R20-next'],['runs/R21/diagnostic/'],
            'Raw locked sources recomputed per key and subgroup; first metrics agree, coverage/tails/bias/loss and date dependence/confounding explained in Chinese; no fitting or unseen/independent claim.'),
        ('R21-02','冻结尚未见真值的新测量协议和原创原件',['R21-01'],['runs/R21/protocol/','runs/R21/inputs/','runs/R21/evaluation/'],
            'Diagnostic motivates a fair as-of-time source-bound protocol and explicitly original new case before production; untouched truth withheld, baselines/criteria reflect uncertainty and business loss, zero improvement allowed.'),
        ('R21-03','新方案执行及独立接收真实新测量',['R21-02'],['runs/R21/execution/','runs/R21/review/','runs/R21/final/'],
            'Actual execution, scientific Chinese consumer and new independent source-bound receiving completed; new truth only after first freeze, failures and informed repairs separate; any source change is document-only with relevant forward reception.'),
        ('R21-next','根据实测边界决定并启动合理下一阶段',['R21-03'],['runs/R22/'],
            'A meaningful successor has source-bound plan and actual first step; completed goals or real boundaries permit explicit end/cancellation, no invented infinite tasks.')]:
        state['tasks'].append(make(*definition))
    ctl.begin(state,ROOT,'R21-01',receipt)
    finish('R21-01','runs/R21/R21-01-result.json',['runs/R21/source-inputs.json',receipt,'runs/R21/diagnostic/result.json',
        'runs/R21/diagnostic/groups.csv','runs/R21/diagnostic/REPORT.md'],'Known-truth diagnostic only',first,
        'Root descriptive diagnostic, no fresh independent reception. Fourteen correlated dates; holiday and horizon confounded; no cause or improvement claim.',
        'R21-02: design new original measurement with untouched truth and fair prospective comparison.')
    freeze('runs/R21','runs/R21/first-diagnostic-lock.json')
    for k,v in read('runs/R21/before/task-identities.json').items():assert ctl.identity(ctl.task_map(state)[k])==v
    assert not ctl.validate(state,ROOT)
    state['execution'].update(current_frontier_task='R21-02',current_report='runs/R21/REPORT.md',
        current_candidate='runs/R20/final/candidate/C13-lock.json',candidate_status='C13_targeted_forward_reception_pass_scoped',
        R20_status='source_synthesis_closed_successor_actually_started',R21_status='first_diagnostic_done_new_protocol_ready',
        current_task_process_state='All actors terminal; R21-01 actual diagnostic done, R21-02 ready and not yet started.')
    state['events'].append(dict(at=ctl.stamp(),command='R20_actual_successor_transfer',evidence='runs/R21/transition-result.json',
        note='Same actual diagnostic receipt bridges transition and first task; one execution, not multiple runs.'))
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=read('state/checkpoint.json');cp.update(current_frontier_task='R21-02',current_report='runs/R21/REPORT.md',
        current_candidate='runs/R20/final/candidate/C13-lock.json',current_native_pending=[],unpublished_work=True,termination=None,
        next_action='R21-02: freeze a genuinely new original case and fair measurement protocol before production; known R20 truth cannot serve as a new blind test.',
        R20_status=state['execution']['R20_status'],R21_status=state['execution']['R21_status'])
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
    project=read('state/project-todo.json')
    entry=next(t for t in project['todo'] if t['id']=='R20-data-workflow')
    entry.update(status='done',next_action=cp['next_action'])
    entry['evidence']+=['runs/R20/R20-05-result.json','runs/R20/final-lock.json','runs/R21/transition-result.json']
    project['todo'].append(dict(id='R21-interval-reliability',owner='root',status='in_progress',write_scope=['runs/R21/'],
        acceptance='Source-bound reliability diagnosis followed by genuinely new fair measurement; not tuning on previously seen truth.',
        evidence=['runs/R21/PLAN.md','runs/R21/first-diagnostic-lock.json','runs/R21/R21-01-result.json'],next_action=cp['next_action']))
    project['updated_at']=ctl.stamp();ctl.write_json(ROOT/'state/project-todo.json',project)
print(json.dumps(dict(R20_next='done_actual_first_step',R21_01='done_descriptive_diagnostic',frontier='R21-02_ready',previous_tasks_preserved=66,new_tasks=4)))
