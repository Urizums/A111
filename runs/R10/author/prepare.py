"""Register this user-requested branch and freeze its distinct inputs, not a runtime dependency."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl

def write(name, data):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write('\n')

def entry(path):
    raw = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(), size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

candidate = ROOT / 'runs/R10/candidate/C8/forge-agent-flow'
files = [entry(p) for p in sorted(candidate.rglob('*')) if p.is_file()]
write('runs/R10/candidate/C8-lock.json', dict(schema='forge-revision-lock/1', revision='C8', parent='C7', scope_decision='runs/R10/scope-decision.json', files=files, repair_limit=2, repairs_used=0))
write('runs/R10/validation/frozen-lock.json', dict(schema='forge-evaluation-lock/1', files=[entry(ROOT/p) for p in ['runs/R10/validation/request.json', 'runs/R10/validation/packet.json', 'runs/R10/candidate/C8-lock.json']], repair_limit=2, tokens=None, cost=None))
write('runs/R10/author/provenance.json', dict(scope='workflow method, not inherited execution platform', sources=[
    dict(output='SKILL.md', retained='outcome routing, actual task outputs, conditional references', source='runs/R08/candidate/C7/forge-agent-flow/SKILL.md'),
    dict(output='references/workflow-design.md', retained='requirements, roles, dependencies and quality decisions', source='skills/forge-agent-flow/references/architecture.md'),
    dict(output='references/collaboration.md', retained='raw inputs, fresh-context review, cooperative write boundaries and unknown-call reconciliation', source='skills/forge-agent-flow/references/host-execution.md'),
    dict(output='references/evaluation.md', retained='source-derived verdict, frozen criteria, retained failures and budgets', source='skills/forge-agent-flow/references/evaluation-plan.md'),
    dict(output='references/continuation.md', retained='same goal, same ledger, meaningful actual successor and accurate scheduling limits', source='skills/forge-agent-flow/references/continuous-research.md')
], excluded_from_C8=['all inherited executable and test scripts', 'factory/package runtime schemas', 'host-specific operational protocols', 'repository research logs'], copied_old_source=False))
rows = [
    ('R10-01', '制作纯方法 C8 并核对成品边界', 'root', [], ['runs/R10/candidate/', 'runs/R10/author/'], ['runs/R10/PLAN.md', 'runs/R10/scope-decision.json'], [dict(id='a1', assertion='新C8自包含纯方法与必要参考，无执行器或测试依赖，保留来源、新锁和原历史'), dict(id='a2', assertion='结构核验与旧文件/任务/预算核对有实际证据，不能代替行为验收')]),
    ('R10-02', '独立执行反馈分流 meta-workflow 样本', 'independent_codex_or_available_luna', ['R10-01'], ['runs/R10/validation/independent/'], ['runs/R10/validation/request.json', 'runs/R10/validation/packet.json', 'runs/R10/validation/frozen-lock.json', 'runs/R10/candidate/C8-lock.json'], [dict(id='a1', assertion='新上下文仅依据C8和新冻结原材料设计流程并实际完成批次，满足request r1-r5'), dict(id='a2', assertion='保留真实首步、命令、产物、能力限制与累计最多两轮纠正；不改判旧样本')])
]
with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    for index, (tid, title, owner, deps, paths, inputs, acceptance) in enumerate(rows):
        if tid in ctl.task_map(state):
            raise ValueError('Task already exists; do not reset')
        state['tasks'].append(dict(id=tid, title=title, queue='capabilities' if index == 0 else 'challenges', category='meta_workflow_scope' if index == 0 else 'meta_workflow_behavior', complexity=2, priority=10+index, depends_on=deps, owner=owner, write_paths=paths, inputs=inputs, acceptance=acceptance, status='planned', evidence=[], attempts=[], repairs_used=0, repair_limit=2, blocker=None, next_action=title))
    state['events'].append(dict(at=ctl.stamp(), command='user_requested_meta_workflow_branch', result=dict(decision='runs/R10/scope-decision.json', old_acceptance_changed=False, old_budgets_changed=False, active_phase_unchanged='R08')))
    ctl.write_json(ROOT/'state/continuation.json', state)
    phase = dict(schema='forge-phase-todo/1', phase_id='R10', goal='交付自包含Forge meta-workflow并观察真实使用', tasks=[dict(id=t['id'], title=t['title'], owner=t['owner'], write_paths=t['write_paths'], depends_on=t['depends_on'], acceptance=[a['assertion'] for a in t['acceptance']], status='planned', evidence=[], blocker=None, next_action=t['next_action']) for t in state['tasks'] if t['id'] in {'R10-01','R10-02'}])
    phase['tasks'].append(dict(id='R10-next', title='启动下一阶段任务', owner='root', depends_on=['R10-01','R10-02'], write_paths=['state/','runs/'], acceptance=['从实际行为观察形成有价值后继并执行真实首步'], status='planned', evidence=[], blocker=None, next_action='Inspect observed gaps after R10-02'))
    ctl.write_json(ROOT/'state/phases/R10.json', phase)
    project = json.loads((ROOT/'state/project-todo.json').read_text(encoding='utf-8'))
    project['updated_at'] = ctl.stamp()
    project['meta_workflow_scope_R10'] = dict(decision='runs/R10/scope-decision.json', plan='runs/R10/PLAN.md', candidate='runs/R10/candidate/C8-lock.json', historical_goal_and_budgets_retained=True, current_frontier='R10-01', tasks=['R10-01','R10-02','R10-next'])
    ctl.write_json(ROOT/'state/project-todo.json',project)
    ctl.synchronize(ROOT,state)
print(json.dumps(dict(frozen_C8_files=len(files), registered=['R10-01','R10-02'], old_history_preserved=True)))
