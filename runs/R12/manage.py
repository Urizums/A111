"""Development ledger integration only; never part of the distributed skill."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))


def digest(path):
    raw = path.read_bytes()
    return dict(size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def save(name, value):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def inventory():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    allowed = {'AGENTS.md', 'START_HERE.md', 'CODEX_HANDOFF.md', 'artifact-manifest.json',
               'state/continuation.json', 'state/checkpoint.json', 'state/project-todo.json',
               'state/phase-todo.json', 'state/coordinator-lease.json'}
    files = [dict(path=name, **digest(ROOT / name)) for name in names if name and name not in allowed]
    save('runs/R12/baseline/files.json', dict(source_commit=head, allowed_mutable=sorted(allowed), files=files))
    for name in ['state/continuation.json', 'state/checkpoint.json', 'artifact-manifest.json',
                 'AGENTS.md', 'START_HERE.md', 'CODEX_HANDOFF.md']:
        target = ROOT / 'runs/R12/baseline' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write((ROOT / name).read_bytes())
    request = json.loads((ROOT / 'runs/R12/review/request.json').read_text(encoding='utf-8'))
    locked = request['allowed_reads']
    files = [dict(path=name, **digest(ROOT / name)) for name in locked
             if name != 'runs/R12/review/frozen-lock.json']
    save('runs/R12/review/frozen-lock.json', dict(schema='forge-design-review-lock/1',
         review_task='R12-02', files=files, repair_limit=2,
         limits='New protocol design review only, never a replacement R10 business verdict'))
    print(json.dumps(dict(source_commit=head, historical_files=len(files),
                         protected_files=len(json.loads((ROOT/'runs/R12/baseline/files.json').read_text())['files']),
                         source_inventory_done=True)))


def phase(tasks, pid, goal):
    keys = ['id', 'title', 'owner', 'write_paths', 'status', 'evidence', 'blocker', 'next_action']
    rows = [{k: t[k] for k in keys} | dict(depends_on=[d for d in t['depends_on'] if d.startswith(pid+'-')],
             acceptance=[a['assertion'] for a in t['acceptance']]) for t in tasks]
    rows.append(dict(id=pid+'-next', title='启动下一阶段任务', owner='root',
                depends_on=[t['id'] for t in tasks], write_paths=['state/', 'runs/'],
                acceptance=['依据实际结果选择有价值后继并完成真实首步；没有后继时如实停止'],
                status='planned', evidence=[], blocker=None, next_action='Inspect results before choosing successor'))
    return dict(schema='forge-phase-todo/1', phase_id=pid, goal=goal, tasks=rows)


def register():
    import continuation as ctl
    with ctl.locked(ROOT):
        state = ctl.load(ROOT)
        assert not ctl.validate(state, ROOT)
        assert not state['execution'].get('current_native_pending')
        assert not state['execution'].get('native_pending')
        assert ctl.task_map(state)['R10-02']['repairs_used'] == 3
        definitions = [
            dict(id='R12-01', title='诊断记录故障并设计轻量评估规程', category='evaluation_protocol_design',
                 owner='root', depends_on=[], write_paths=['runs/R12/protocol/', 'runs/R12/diagnosis.md'],
                 inputs=['runs/R12/PLAN.md', 'runs/R12/baseline/state/continuation.json',
                         'runs/R10/resumption/native-terminal.json'],
                 acceptance=[dict(id='a1', assertion='以原记录诊断实际故障，区分事实/假设，交付轻量评估规程且不添加产品执行依赖'),
                             dict(id='a2', assertion='保留旧案例、全部历史输入/验收/预算与冻结C8，规程不追溯重判')],
                 next_action='Review captured inventory and protocol design'),
            dict(id='R12-02', title='独立审查评估规程的可用性与约束', category='independent_protocol_design_review',
                 owner='independent_available_luna', depends_on=['R12-01'], write_paths=['runs/R12/review/independent/'],
                 inputs=['runs/R12/review/request.json', 'runs/R12/review/frozen-lock.json',
                         'runs/R12/protocol/evaluation-protocol.md'],
                 acceptance=[dict(id='a1', assertion='新上下文在冻结最小原材料上产出完整有依据的设计审查和明确采用建议'),
                             dict(id='a2', assertion='原案例不执行/修正/重判，独立规程审查不得宣称业务验收或性能提升')],
                 next_action='Dispatch prospective protocol review using frozen raw inputs')]
        for index, task in enumerate(definitions):
            assert task['id'] not in ctl.task_map(state)
            task.update(queue='capabilities', complexity=2, priority=20+index, status='planned',
                        evidence=[], attempts=[], repairs_used=0, repair_limit=2, blocker=None)
            state['tasks'].append(task)
        ctl.begin(state, ROOT, 'R12-01', 'runs/R12/inventory-command.json')
        state['events'].append(dict(at=ctl.stamp(), command='register_independent_protocol_design',
             result=dict(plan='runs/R12/PLAN.md', replaces_old_acceptance=False, old_repairs_reset=False)))
        ctl.write_json(ROOT/'state/phases/R12.json', phase(definitions, 'R12', '轻量研发评估规程设计与独立审查'))
        state['execution'].update(session_state='R12_protocol_design_active', current_report='runs/R12/REPORT.md',
                                  coordinator_heartbeat=ctl.stamp())
        ctl.write_json(ROOT/'state/continuation.json', state)
        ctl.synchronize(ROOT, state)
        project = json.loads((ROOT/'state/project-todo.json').read_text(encoding='utf-8'))
        project['evaluation_protocol_R12'] = dict(plan='runs/R12/PLAN.md', stage='design_in_progress',
             scope='Independent prospective protocol, not C8 business replay', historical_budgets_preserved=True)
        ctl.write_json(ROOT/'state/project-todo.json', project)
        cp = json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
        cp.update(unpublished_work=True, R12_current_plan='runs/R12/PLAN.md')
        ctl.write_json(ROOT/'state/checkpoint.json', cp)
    print(json.dumps(dict(registered=['R12-01', 'R12-02'], started='R12-01', active_phase='R08')))


def audit():
    base = json.loads((ROOT/'runs/R12/baseline/files.json').read_text(encoding='utf-8'))
    changed = [row['path'] for row in base['files'] if not (ROOT/row['path']).is_file()
               or digest(ROOT/row['path']) != {k: row[k] for k in ['size_bytes', 'sha256']}]
    old = json.loads((ROOT/'runs/R12/baseline/state/continuation.json').read_text(encoding='utf-8'))
    current = json.loads((ROOT/'state/continuation.json').read_text(encoding='utf-8'))
    tasks = {t['id']: t for t in current['tasks']}
    task_changes = [t['id'] for t in old['tasks'] if tasks.get(t['id']) != t]
    result = dict(ok=not changed and not task_changes, protected_files=len(base['files']),
                  changed_files=changed, historical_tasks=len(old['tasks']), changed_tasks=task_changes,
                  limits='Byte/task preservation only, not a new behavioral verdict')
    print(json.dumps(result))
    return result


def close_author():
    import continuation as ctl
    observation = audit()
    assert observation['ok']
    save('runs/R12/author-preservation.json', observation)
    with ctl.locked(ROOT):
        state = ctl.load(ROOT)
        task = ctl.task_map(state)['R12-01']; attempt = task['attempts'][-1]
        result = dict(task_id=task['id'], attempt_id=attempt['id'], requirements_hash=attempt['requirements_hash'],
           criteria=[dict(id='a1', status='pass', evidence=['runs/R12/diagnosis.md','runs/R12/protocol/evaluation-protocol.md']),
                     dict(id='a2', status='pass', evidence=['runs/R12/author-preservation.json','runs/R12/PLAN.md'])],
           effect=dict(target='Prospective repository evaluation protocol', hypothesis='Explicit minimal evidence ownership can reduce needless bespoke recording',
             baseline='Historical recording failures and incomplete source check', conditions='Root documentation design, original records retained',
             observations='Protocol authored with preparation, responsibilities, interruptions, limits and truthful handoff',
             limits='Author design only; no measured improvement or C8/historical business acceptance',
             metrics=dict(repairs_used=0, tokens=None, cost=None)), next_action='R12-02 independent design review')
        save('runs/R12/R12-01-result.json', result)
        outcome = ctl.finish(state, ROOT, task['id'], 'runs/R12/R12-01-result.json')
        state['events'].append(dict(at=ctl.stamp(), command='finish', result=outcome))
        ctl.write_json(ROOT/'state/continuation.json', state)
        path = ROOT/'state/phases/R12.json'
        ctl.write_json(path, ctl.phase_view(json.loads(path.read_text()), state))
        ctl.synchronize(ROOT, state)
    print(json.dumps(outcome))


def prepare_review():
    lock = json.loads((ROOT/'runs/R12/review/frozen-lock.json').read_text(encoding='utf-8'))
    for row in lock['files']:
        assert digest(ROOT/row['path']) == {k: row[k] for k in ['size_bytes', 'sha256']}
    import datetime
    save('runs/R12/review/native-dispatch.json', dict(
        observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        tool='collaboration.spawn_agent', returned=dict(task_name='/root/r12_protocol_review'),
        fork_turns='none', requested_model='gpt-6-luna', authenticated_exact_model=None,
        supplied_request='runs/R12/review/request.json', output_boundary='runs/R12/review/independent/',
        author_diagnosis_supplied=False, evidence='Actual spawn tool returned this task identity',
        tokens=None, cost=None))
    print(json.dumps(dict(frozen_files_verified=len(lock['files']), native_actor='/root/r12_protocol_review',
                         limits='Input/dispatch check only, not independent review completion')))


def start_review():
    import continuation as ctl
    with ctl.locked(ROOT):
        state=ctl.load(ROOT)
        attempt=ctl.begin(state, ROOT, 'R12-02', 'runs/R12/review/prepare-command.json')
        state['execution'].update(session_state='R12_independent_protocol_review_active',
            native_pending=[dict(worker='/root/r12_protocol_review', request='runs/R12/review/request.json', state='created')],
            current_native_pending=[dict(worker='/root/r12_protocol_review', request='runs/R12/review/request.json', state='created')])
        state['events'].append(dict(at=ctl.stamp(), command='start', result=attempt))
        ctl.write_json(ROOT/'state/continuation.json',state)
        p=ROOT/'state/phases/R12.json'
        ctl.write_json(p,ctl.phase_view(json.loads(p.read_text()),state))
        ctl.synchronize(ROOT,state)
    print(json.dumps(dict(task='R12-02',status='in_progress')))


def close_review():
    import continuation as ctl
    raw=json.loads((ROOT/'runs/R12/review/independent/result.json').read_text(encoding='utf-8'))
    save('runs/R12/review/native-terminal.json',dict(worker='/root/r12_protocol_review',
         state='final_return_received',result='runs/R12/review/independent/result.json',
         authenticated_exact_model=None,tokens=None,cost=None))
    with ctl.locked(ROOT):
        state=ctl.load(ROOT); task=ctl.task_map(state)['R12-02']; attempt=task['attempts'][-1]
        # The coordinator records its actual inspection in adoption-review.json before closing.
        adoption=json.loads((ROOT/'runs/R12/review/adoption-review.json').read_text(encoding='utf-8'))
        assert adoption['review_complete'] and adoption['no_old_case_replay']
        verdict='pass' if adoption['adoptable'] else 'fail'
        repairs=adoption['observed_repairs_used']
        task['repairs_used']=repairs
        paths=['runs/R12/review/independent/result.json','runs/R12/review/independent/review.md',
               'runs/R12/review/adoption-review.json','runs/R12/review/native-terminal.json']
        result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
            criteria=[dict(id='a1',status=verdict,evidence=paths),dict(id='a2',status='pass',evidence=paths+['runs/R12/author-preservation.json'])],
            effect=dict(target='Independent prospective protocol design review',hypothesis='The new protocol is usable within inherited constraints',
             baseline='Frozen protocol and minimal original command/final records',conditions='Actual fresh requested-Luna context, no author diagnosis, no old business execution',
             observations=adoption['observation'],limits='Design review only; no empirical recording improvement, performance or skill behavior claim',
             metrics=dict(repairs_used=repairs,repair_limit=2,tokens=None,cost=None)),
            next_action='R13-01 actual repository adoption if this protocol passes')
        save('runs/R12/R12-02-result.json',result)
        outcome=ctl.finish(state,ROOT,task['id'],'runs/R12/R12-02-result.json')
        state['execution'].update(native_pending=[],current_native_pending=[],session_state='R12_protocol_review_terminal_received')
        state['execution'].setdefault('completed_native_R12',[]).append(dict(worker='/root/r12_protocol_review',evidence='runs/R12/review/native-terminal.json'))
        state['events'].append(dict(at=ctl.stamp(),command='finish',result=outcome))
        ctl.write_json(ROOT/'state/continuation.json',state)
        p=ROOT/'state/phases/R12.json'
        ctl.write_json(p,ctl.phase_view(json.loads(p.read_text()),state))
        ctl.synchronize(ROOT,state)
    print(json.dumps(outcome))


if __name__ == '__main__':
    actions = dict(inventory=inventory, register=register, audit=audit, close_author=close_author,
                   prepare_review=prepare_review,start_review=start_review,close_review=close_review)
    actions[sys.argv[1]]()
