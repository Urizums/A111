"""Close the actual R19 transition and start its justified successor; preserve history."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl

def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def row(path):
    data = (ROOT / path).read_bytes()
    return dict(path=path, size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    old = read('runs/R19/before/task-identities.json')
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
    assert ctl.task_map(state)['R19-05']['status'] == 'done'
    assert not state['execution']['current_native_pending']
    assert 'R20-01' not in ctl.task_map(state)
    assert read('runs/R20/research/first-step-command.json')['exit_code'] == 0
    before = {t['id']: ctl.identity(t) for t in state['tasks'] if t['id'] != 'R19-next'}
    ctl.begin(state, ROOT, 'R19-next', 'runs/R20/research/first-step-command.json')
    task = ctl.task_map(state)['R19-next']
    result_path = 'runs/R20/transition-result.json'
    ctl.write_json(ROOT / result_path, dict(task_id='R19-next', attempt_id=task['attempts'][-1]['id'],
        requirements_hash=task['attempts'][-1]['requirements_hash'],
        criteria=[dict(id='t1', status='pass', evidence=['runs/R20/PLAN.md',
            'runs/R20/research/first-step-command.json', 'runs/R20/research/acquisition.json',
            'runs/R20/research/FACTS.json', 'runs/R20/research/REPORT.md'])],
        effect=dict(target='October data-workflow successor actual start',
            hypothesis='Current official source audit precedes a new data-semantic workflow trial; not yet behavior evaluated.',
            baseline='Spring four-level C11 diagnostics and scoped C12 forward reception retained.',
            conditions='Primary current 2026 organizer notices, actual downloaded combined seven-page PDF, full visual reading and source-bound unknowns.',
            observations=dict(plan='runs/R20/PLAN.md', first_task='R20-01',
                actual_first_step='Two official links downloaded/read; same bytes, one distinct combined document.',
                rules_complete=False, actual_contest_data_acquired=False),
            limits='First official audit only; no new data solution or formal participation compliance, score/prize or future performance.',
            metrics=dict(distinct_official_documents=1, pages_actually_viewed=7, tokens=None, cost=None)),
        next_action='R20-01: resolve current submission/assistance supplement and actual raw-data status; then freeze original data-workflow trial.'))
    ctl.finish(state, ROOT, 'R19-next', result_path)
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in before.items())
    before_path = ROOT / 'runs/R20/before/task-identities.json'
    ctl.write_json(before_path, {t['id']: ctl.identity(t) for t in state['tasks']})

    def make(ident, title, dependencies, paths, inputs, assertion):
        return dict(id=ident, title=title, queue='challenges', category='prospective_workflow_transfer_trial',
            complexity=3, priority=20, depends_on=dependencies, owner='root', write_paths=paths,
            inputs=inputs, acceptance=[dict(id='t1', assertion=assertion)], status='planned',
            evidence=[], attempts=[], repairs_used=0, repair_limit=None, blocker=None, next_action=title,
            execution_policy=dict(mode='progress_guard', source=ctl.ref(ROOT, 'runs/R20/PLAN.md'),
                stop_conditions=['actual host or permission boundary', 'user stop', 'completion',
                                 'persistent unchanged path without new evidence'],
                progress_state='ready', deadline_utc=None))
    plan_input = ['runs/R20/PLAN.md', 'runs/R19/final/candidate/C12-lock.json']
    definitions = [
        ('R20-01', '核实当前官方赛事、规则与原始数据状态', ['R19-next'], ['runs/R20/research/'],
         'Current official edition/rules/delivery/assistance and actual data-source status checked; facts, conflicts and unresolved policy have source identity and concrete next action, not old-edition substitution or a plan-only check.'),
        ('R20-02', '冻结原创数据任务、稀疏请求和独立验收', ['R20-01'], ['runs/R20/inputs/', 'runs/R20/evaluation/'],
         'Explicitly original task/data, sparse request and external domain-derived acceptance frozen before agents; exact goal, available information, relevant split/metric and physical/business constraints justified.'),
        ('R20-03', '新上下文构建可交接数据工作流', ['R20-02'], ['runs/R20/design/'],
         'Fresh builder uses only specified candidate/own request/raw; produces usable handoff covering data, research, baseline, justified methods, actual experiments, receiving checks and full Chinese paper.'),
        ('R20-04', '新执行至论文及独立实质接收', ['R20-03'], ['runs/R20/execution/', 'runs/R20/review/'],
         'Different fresh executor consumes frozen workflow to code/results/complete Chinese paper and final PDF; fresh reviewer actually checks original goal/data/metrics, leakage/fair comparison where relevant, scientific explanation and output fidelity; first failures and informed revisions separate.'),
        ('R20-05', '综合新数据任务证据与源头缺口', ['R20-04'], ['runs/R20/final/'],
         'Actual new task evidence source-bound; any document-only source revision has separate identity and relevant forward reception, with original failures and limits preserved.'),
        ('R20-next', '启动有依据的下一阶段任务', ['R20-05'], ['runs/R21/'],
         'Justified successor has actual plan and task-relevant first step; no invented continuation if goal is complete or actual boundary persists.'),
    ]
    for ident, title, dependencies, paths, assertion in definitions:
        state['tasks'].append(make(ident, title, dependencies, paths, plan_input, assertion))
    ctl.begin(state, ROOT, 'R20-01', 'runs/R20/research/first-step-command.json')
    state['execution'].update(current_frontier_task='R20-01', current_report='runs/R20/REPORT.md',
        current_task_process_state='Actual primary-source first audit complete; R20-01 remains in progress for current supplements/data status, no active background actor.',
        candidate_status='C12_targeted_forward_first_reception_pass_scoped',
        R19_status='four_diagnostics_and_source_synthesis_done_successor_actually_started',
        R20_plan='runs/R20/PLAN.md')
    state['events'].append(dict(at=ctl.stamp(), command='R19_actual_successor_transfer',
        evidence=result_path, note='Same real first-step receipt is a transition/start bridge, not two executions.'))
    errors = ctl.validate(state, ROOT)
    assert not errors, errors
    ctl.write_json(ROOT / 'state/continuation.json', state)
    ctl.synchronize(ROOT, state)
    cp_path = ROOT / 'state/checkpoint.json'
    cp = read('state/checkpoint.json')
    cp.update(current_frontier_task='R20-01', current_report='runs/R20/REPORT.md',
        current_candidate='runs/R19/final/candidate/C12-lock.json',
        R19_status=state['execution']['R19_status'], R20_status='actual_official_first_audit_in_progress',
        next_action='R20-01: acquire exact current submission and AI/assistance supplements; preserve actual unknown data status, then freeze original data-workflow trial.',
        current_native_pending=[], unpublished_work=True, termination=None)
    ctl.write_json(cp_path, cp)
    project = read('state/project-todo.json')
    for item in project.get('todo', []):
        if item.get('id') == 'R19-level1-4':
            item.update(status='done', evidence=['runs/R19/final/result.json', result_path],
                next_action='R20-01 actual official first audit; original scientific verdicts unchanged.')
    project.setdefault('todo', []).append(dict(id='R20-data-workflow', owner='root', status='in_progress',
        write_scope=['runs/R20/'], acceptance='Current-source audit followed by original data-semantic sparse-request transfer through independently reviewed complete Chinese paper.',
        evidence=['runs/R20/PLAN.md', 'runs/R20/research/first-step-command.json'],
        next_action=cp['next_action']))
    project['updated_at'] = ctl.stamp()
    ctl.write_json(ROOT / 'state/project-todo.json', project)

    lock_path = 'runs/R20/first-audit-lock.json'
    files = [row(p.relative_to(ROOT).as_posix()) for p in sorted((ROOT / 'runs/R20/research').rglob('*'))
             if p.is_file() and '__pycache__' not in p.parts]
    files += [row(p) for p in ['runs/R20/PLAN.md', result_path, 'runs/R20/before/task-identities.json']]
    ctl.write_json(ROOT / lock_path, dict(schema='forge-revision-lock/1', revision='R20-actual-first-official-audit',
        frozen_at=ctl.stamp(), files=files,
        claim='Immutable original first audit and plan; unresolved rules/data remain. Later audits append, never overwrite this bridge evidence.'))
    index = read('state/revision-locks.json')
    index['locks'].append(lock_path)
    ctl.write_json(ROOT / 'state/revision-locks.json', index)
print(json.dumps(dict(R19_next='done_actual_successor_first_step', R20_01='in_progress',
    old_tasks_unchanged=len(old), previous_tasks_preserved_after_transition=len(before),
    new_tasks=6, frozen_first_audit_files=len(files), queue_valid=True)))
