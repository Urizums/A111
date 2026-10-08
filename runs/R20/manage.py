"""Serial coordinator bookkeeping using the existing continuation controller."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl
parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['prepare', 'actor', 'freeze', 'start', 'finish'])
parser.add_argument('--actor')
parser.add_argument('--status', choices=['running', 'completed', 'interrupted'])
parser.add_argument('--scope')
parser.add_argument('--lock')
parser.add_argument('--task')
parser.add_argument('--receipt')
parser.add_argument('--result')
args = parser.parse_args()

def read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))

def freeze(scope, relative):
    directory = (ROOT / scope).resolve()
    path = (ROOT / relative).resolve()
    allowed = (ROOT / 'runs/R20').resolve()
    assert directory.is_relative_to(allowed) and path.is_relative_to(allowed) and not path.exists()
    rows = []
    for f in sorted(directory.rglob('*')):
        if f.is_file() and '__pycache__' not in f.parts:
            b = f.read_bytes()
            rows.append(dict(path=f.relative_to(ROOT).as_posix(), size_bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
    assert rows
    ctl.write_json(path, dict(schema='forge-revision-lock/1', revision=scope,
        frozen_at=ctl.stamp(), files=rows, claim='Exact terminal bytes; not substantive acceptance.'))
    index = read('state/revision-locks.json')
    index['locks'].append(relative)
    ctl.write_json(ROOT / 'state/revision-locks.json', index)
    return len(rows)

def finish_one(state, ident, evidence, observations, next_action):
    task = ctl.task_map(state)[ident]
    attempt = task['attempts'][-1]
    path = f'runs/R20/{ident}-result.json'
    assert not (ROOT / path).exists()
    ctl.write_json(ROOT / path, dict(task_id=ident, attempt_id=attempt['id'],
        requirements_hash=attempt['requirements_hash'], criteria=[dict(id='t1', status='pass', evidence=evidence)],
        effect=dict(target=task['title'], hypothesis='Source-bound preparation supports the next actual workflow step.',
            baseline='Previous scoped spring/C12 reception and immutable history retained.',
            conditions='Offline original data; source policy unknowns do not imply participation permission.',
            observations=observations, limits='Preparation acceptance only; not paper quality, formal compliance, prize or future performance.',
            metrics=dict(tokens=None, cost=None)), next_action=next_action))
    ctl.finish(state, ROOT, ident, path)

with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    old = read('runs/R20/before/task-identities.json')
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
    if args.action == 'prepare':
        assert not state['execution']['current_native_pending']
        assert read('runs/R20/coordination/data-generation-command.json')['exit_code'] == 0
        sizes = dict(audit=freeze('runs/R20/research/supplement-audit-2', 'runs/R20/supplement-audit-2-lock.json'),
            inputs=freeze('runs/R20/inputs', 'runs/R20/input-lock.json'),
            evaluation=freeze('runs/R20/evaluation', 'runs/R20/evaluation-lock.json'))
        finish_one(state, 'R20-01', ['runs/R20/first-audit-lock.json', 'runs/R20/supplement-audit-1-lock.json',
            'runs/R20/supplement-audit-2-lock.json', 'runs/R20/research/supplement-audit-2/DECISION.md'],
            dict(current_platform_link_verified=True, current_platform_body='unavailable in actual read',
                exact_supplements='unresolved', current_contest_data='not acquired', offline_original_trial_allowed=True),
            'R20-02: freeze explicitly original data and external acceptance, then fresh builder.')
        ctl.begin(state, ROOT, 'R20-02', 'runs/R20/coordination/data-generation-command.json')
        finish_one(state, 'R20-02', ['runs/R20/input-lock.json','runs/R20/evaluation-lock.json',
            'runs/R20/coordination/data-generation-command.json'], dict(frozen=sizes,
                raw_history_report_rows=17577, holdout_rows=1344, independent_criteria=5,
                future_truth_withheld_from_production=True, request='single sparse request, not new Level5–8 trial'),
            'R20-03: fresh builder consumes only C12/request/problem/raw/input lock.')
        ctl.begin(state, ROOT, 'R20-03', 'runs/R20/coordination/data-generation-command.json')
        # One generation effect supports adjacent preparation/start records, never counted as multiple executions.
        state['execution']['R20_preparation_bridge'] = 'One actual data generation, not separate solver runs.'
    elif args.action == 'actor':
        assert args.actor.startswith('/root/r20_') and args.status
        serial = 1
        path = f'runs/R20/coordination/{args.actor.rsplit("/",1)[-1]}-{args.status}-{serial}.json'
        while (ROOT / path).exists():
            serial += 1
            path = f'runs/R20/coordination/{args.actor.rsplit("/",1)[-1]}-{args.status}-{serial}.json'
        ctl.write_json(ROOT / path, dict(actor=args.actor, status=args.status, observed_at=ctl.stamp(),
            provenance='Actual parent collaboration tool identity/status; not provider telemetry', model=None,tokens=None,cost=None))
        pending = [row for row in state['execution']['current_native_pending'] if row['worker'] != args.actor]
        row = dict(worker=args.actor,state=args.status,evidence=path,actual_model=None)
        if args.status == 'running':
            pending.append(row)
        else:
            state['execution'].setdefault('completed_native_R20', []).append(row)
        state['execution'].update(current_native_pending=pending,native_pending_current=pending)
    elif args.action == 'freeze':
        print(json.dumps(dict(files=freeze(args.scope,args.lock))))
    elif args.action == 'start':
        ctl.begin(state, ROOT, args.task, args.receipt)
    elif args.action == 'finish':
        ctl.finish(state, ROOT, args.task, args.result)
    active = [t['id'] for t in state['tasks'] if t['id'].startswith('R20-') and t['status'] == 'in_progress']
    frontier = active[0] if active else 'R20-next'
    state['execution'].update(current_frontier_task=frontier,current_report='runs/R20/REPORT.md',
        current_task_process_state='R20 original data trial; actual pending actors recorded separately.',
        R20_status=('original_data_paper_independently_accepted_scoped'
            if ctl.task_map(state)['R20-04']['status']=='done'
            else 'current-source-audit-closed-with-unknowns_original-data-trial'))
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
    errors = ctl.validate(state, ROOT)
    assert not errors, errors
    ctl.write_json(ROOT / 'state/continuation.json', state)
    ctl.synchronize(ROOT, state)
    cp = read('state/checkpoint.json')
    cp.update(current_frontier_task=frontier,current_report='runs/R20/REPORT.md',
        current_native_pending=state['execution']['current_native_pending'],
        next_action=f'{frontier}: continue original data workflow to independent reception; retain policy unknowns and old failures.',
        termination=None,unpublished_work=True,R20_status=state['execution']['R20_status'])
    ctl.write_json(ROOT / 'state/checkpoint.json', cp)
print(json.dumps(dict(action=args.action,frontier=frontier,previous_tasks_preserved=len(old),queue_valid=True)))
