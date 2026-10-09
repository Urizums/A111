"""R21 serial bookkeeping; historical tasks and candidate sources are immutable."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl

p = argparse.ArgumentParser()
p.add_argument('action', choices=['start', 'finish', 'freeze', 'actor', 'claim', 'bind'])
p.add_argument('--task')
p.add_argument('--receipt')
p.add_argument('--result')
p.add_argument('--scope')
p.add_argument('--lock')
p.add_argument('--actor')
p.add_argument('--status', choices=['running', 'completed', 'interrupted'])
a = p.parse_args()

def read(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))

with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    old = read('runs/R21/before/task-identities.json')
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
    if a.action == 'claim':
        lease = read('state/coordinator-lease.json')
        assert lease['owner'] == 'root-codex-r21-prospective' and not lease.get('released_at')
        state['execution'].setdefault('historical_coordinator_snapshots', []).append(dict(at=ctl.stamp(),
            fields={k:state['execution'].get(k) for k in ['current_coordinator', 'final_lease_release', 'coordinator_release_evidence']}))
        state['execution'].update(current_coordinator=lease['owner'], coordinator_heartbeat=ctl.stamp(),
            actual_lease_pid=lease['pid'], actual_lease_session=20564, final_lease_release=None,
            coordinator_release_evidence=None)
    elif a.action == 'bind':
        task=ctl.task_map(state)['R21-03']
        assert task['status']=='planned' and not task['attempts']
        for rel in ['runs/R20/final/candidate/C13-lock.json','runs/R21/input-lock.json','runs/R21/protocol-lock.json','runs/R21/evaluation-lock.json']:
            assert (ROOT/rel).is_file()
            if rel not in task['inputs']:
                task['inputs'].append(rel)
        if 'runs/R21/design/' not in task['write_paths']:
            task['write_paths'].append('runs/R21/design/')
        state['execution']['R21_prestart_binding']='New original inputs/protocol/C13 identity and derived workflow scope added before first R21-03 attempt; acceptance and old66 tasks unchanged.'
    elif a.action == 'start':
        ctl.begin(state, ROOT, a.task, a.receipt)
    elif a.action == 'finish':
        ctl.finish(state, ROOT, a.task, a.result)
    elif a.action == 'freeze':
        directory = (ROOT / a.scope).resolve()
        target = (ROOT / a.lock).resolve()
        assert directory.is_relative_to(ROOT / 'runs/R21') and target.is_relative_to(ROOT / 'runs/R21')
        assert not target.exists()
        rows = []
        for f in sorted(directory.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts:
                b = f.read_bytes()
                if f.name.endswith('command.json'):
                    assert json.loads(b)['state'] == 'finished', f
                rows.append(dict(path=f.relative_to(ROOT).as_posix(), size_bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
        assert rows
        ctl.write_json(target, dict(schema='forge-revision-lock/1', revision=a.scope,
            frozen_at=ctl.stamp(), files=rows, claim='Identity of terminal bytes only; scientific receiving separate.'))
        index = read('state/revision-locks.json')
        assert a.lock not in index['locks']
        index['locks'].append(a.lock)
        ctl.write_json(ROOT / 'state/revision-locks.json', index)
        print(json.dumps(dict(frozen_files=len(rows), lock=a.lock)))
    elif a.action == 'actor':
        assert a.actor.startswith('/root/r21_') and a.status
        folder = ROOT / 'runs/R21/coordination'
        folder.mkdir(exist_ok=True)
        n = 1
        while (folder / f'{a.actor.rsplit("/",1)[-1]}-{a.status}-{n}.json').exists():
            n += 1
        f = folder / f'{a.actor.rsplit("/",1)[-1]}-{a.status}-{n}.json'
        rel = f.relative_to(ROOT).as_posix()
        write_scope={'r21_builder':'runs/R21/design/','r21_executor':'runs/R21/execution/','r21_receiver':'runs/R21/review/'}[a.actor.rsplit('/',1)[-1]]
        ctl.write_json(f, dict(actor=a.actor,status=a.status,write_scope=write_scope,observed_at=ctl.stamp(),model=None,tokens=None,cost=None,
            provenance='Actual collaboration tool status; local scopes are not OS isolation.'))
        pending = [r for r in state['execution']['current_native_pending'] if r['worker'] != a.actor]
        row = dict(worker=a.actor,state=a.status,evidence=rel,actual_model=None)
        if a.status == 'running':
            pending.append(row)
        else:
            state['execution'].setdefault('completed_native_R21', []).append(row)
        state['execution'].update(current_native_pending=pending,native_pending_current=pending)
    tasks = ctl.task_map(state)
    frontier = next((i for i in ['R21-02', 'R21-03', 'R21-next'] if tasks[i]['status'] != 'done'), 'R21-next')
    state['execution'].update(current_frontier_task=frontier,current_report='runs/R21/REPORT.md',
        current_task_process_state='R21 prospective new original case; pending actors recorded separately.')
    assert all(ctl.identity(tasks[k]) == v for k,v in old.items())
    assert not ctl.validate(state, ROOT)
    ctl.write_json(ROOT / 'state/continuation.json', state)
    ctl.synchronize(ROOT, state)
    cp = read('state/checkpoint.json')
    cp.update(current_frontier_task=frontier,current_report='runs/R21/REPORT.md',
        current_native_pending=state['execution']['current_native_pending'],next_action=tasks[frontier]['next_action'],
        termination=None,unpublished_work=True)
    ctl.write_json(ROOT / 'state/checkpoint.json', cp)
print(json.dumps(dict(action=a.action,frontier=frontier,previous_tasks_preserved=len(old),queue_valid=True)))
