#!/usr/bin/env python3
"""Durable, cooperative R&D queue. It selects work; it does not schedule a model."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile

from delivery import read_file

TERMINAL = {'done', 'cancelled'}


def stamp():
    return datetime.now(timezone.utc).isoformat()


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def ref(root, name):
    raw = read_file(root, name)
    return dict(path=name, sha256=hashlib.sha256(raw).hexdigest())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
        temporary = f.name
    os.replace(temporary, path)


@contextmanager
def locked(root):
    path = root/'state/continuation.lock'
    with path.open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


def load(root):
    return json.loads(read_file(root, 'state/continuation.json'))


def task_map(state):
    return {t['id']: t for t in state['tasks']}


def ready(state):
    tasks = task_map(state)
    return sorted((t for t in tasks.values()
                   if t['status'] in {'planned', 'failed'}
                   and (t['status'] == 'planned' or t['repairs_used'] < t['repair_limit'])
                   and all(tasks[d]['status'] == 'done' for d in t['depends_on'])),
                  key=lambda t: (t['priority'], t['id']))


def validate(state, root):
    errors = []
    tasks = task_map(state)
    if len(tasks) != len(state['tasks']):
        errors.append('duplicate task ID')
    visiting, visited = set(), set()
    def visit(key):
        if key in visiting:
            errors.append('dependency cycle: ' + key); return
        if key in visited:
            return
        visiting.add(key)
        for dep in tasks[key]['depends_on']:
            if dep not in tasks:
                errors.append('missing dependency: ' + dep)
            else:
                visit(dep)
        visiting.remove(key); visited.add(key)
    for t in tasks.values():
        visit(t['id'])
        for key in ['queue','category','priority','owner','write_paths','acceptance','inputs',
                    'next_action','evidence','attempts','repairs_used','repair_limit','blocker']:
            if key not in t:
                errors.append(t['id'] + ': missing ' + key)
        if t['queue'] not in {'capabilities','challenges'} or not t['acceptance']:
            errors.append(t['id'] + ': invalid queue or empty acceptance')
        if t['status'] == 'done' and not t['evidence']:
            errors.append(t['id'] + ': no completion evidence')
        if t['status'] == 'blocked' and not t['blocker']:
            errors.append(t['id'] + ': no blocker/recovery condition')
        evidence = list(t['evidence'])
        for attempt in t['attempts']:
            evidence += attempt.get('evidence', []) + attempt.get('inputs', [])
            evidence.append(attempt['start_evidence'])
            if attempt.get('result'):
                evidence.append(attempt['result'])
        for record in evidence:
            try:
                if ref(root,record['path']) != record:
                    errors.append(t['id'] + ': changed evidence ' + record['path'])
            except (OSError, ValueError, KeyError) as exc:
                errors.append(t['id'] + ': ' + str(exc))
        if t['status'] == 'done' and any(tasks[d]['status'] != 'done' for d in t['depends_on'] if d in tasks):
            errors.append(t['id'] + ': completed before dependency')
    if state['project_goal']['status'] == 'completed' and any(t['status'] not in TERMINAL for t in tasks.values()):
        errors.append('project goal cannot be completed while capability/challenge work remains')
    return errors


def summary(state):
    active = [t for t in state['tasks'] if t['status'] == 'in_progress']
    pending = ready(state)
    selected = (active or pending or [None])[0]
    return dict(project_goal=state['project_goal'], delivery_status=state['deliveries'],
                next_task_id=selected['id'] if selected else None,
                next_task=selected, ready_tasks=[t['id'] for t in pending],
                active_tasks=[t['id'] for t in active],
                blocked_tasks=[dict(id=t['id'],blocker=t['blocker'],next_action=t['next_action'])
                               for t in state['tasks'] if t['status']=='blocked'],
                execution=state['execution'],
                boundary='Host-coordinated selection and evidence; no automatic native call or background scheduler')


def begin(state, root, task_id, evidence):
    task = task_map(state)[task_id]
    if task_id not in {t['id'] for t in ready(state)}:
        raise ValueError('Task is not ready: ' + task_id)
    for active in state['tasks']:
        if active['status'] != 'in_progress':
            continue
        for a in active['write_paths']:
            for b in task['write_paths']:
                if Path(a) == Path(b) or Path(a) in Path(b).parents or Path(b) in Path(a).parents:
                    raise ValueError('Write scope overlaps active task: ' + active['id'])
    raw = json.loads(read_file(root, evidence))
    if (raw.get('state') != 'finished' or not raw.get('argv')
            or type(raw.get('exit_code')) is not int or not raw.get('begin') or not raw.get('end')):
        raise ValueError('Start requires an actual finished command record, including failed first steps')
    if task['attempts']:
        if task['repairs_used'] >= task['repair_limit']:
            raise ValueError('Repair budget exhausted')
        task['repairs_used'] += 1
    attempt = dict(id=task_id + '-' + str(len(task['attempts']) + 1), started_at=stamp(),
                   requirements_hash=identity(task['acceptance']),
                   inputs=[ref(root,p) for p in task['inputs']], start_evidence=ref(root,evidence),
                   status='in_progress')
    task['attempts'].append(attempt)
    task.update(status='in_progress', blocker=None)
    return attempt


def finish(state, root, task_id, result_path):
    task = task_map(state)[task_id]
    if task['status'] != 'in_progress':
        raise ValueError('Task has no active attempt')
    attempt = task['attempts'][-1]
    result = json.loads(read_file(root,result_path))
    if (result.get('task_id') != task_id or result.get('attempt_id') != attempt['id']
            or result.get('requirements_hash') != attempt['requirements_hash']
            or identity(task['acceptance']) != attempt['requirements_hash']):
        raise ValueError('Stale result or changed frozen acceptance')
    for source in attempt['inputs']:
        if ref(root,source['path']) != source:
            raise ValueError('Frozen input changed: ' + source['path'])
    criteria = result.get('criteria', [])
    if len({c['id'] for c in criteria}) != len(criteria) or {c['id'] for c in criteria} != {a['id'] for a in task['acceptance']}:
        raise ValueError('Result must cover exactly the frozen acceptance')
    refs = [ref(root,result_path)]
    for c in criteria:
        if c['status'] not in {'pass','fail','blocked'} or not c.get('evidence'):
            raise ValueError('Each criterion needs a verdict and real evidence')
        refs += [ref(root,p) for p in c['evidence']]
    for key in ['target','hypothesis','baseline','conditions','observations','limits','metrics']:
        if key not in result.get('effect', {}):
            raise ValueError('Missing effect-evaluation field: ' + key)
    outcome = 'done' if all(c['status']=='pass' for c in criteria) else 'failed'
    if outcome == 'failed' and task['repairs_used'] >= task['repair_limit']:
        outcome = 'blocked'
    attempt.update(status=outcome, ended_at=stamp(), result=ref(root,result_path), evidence=refs)
    task.update(status=outcome, evidence=refs, next_action=result.get('next_action',task['next_action']))
    if outcome == 'blocked':
        task['blocker'] = 'Repair budget exhausted; original criteria and all attempts retained.'
    return dict(task_id=task_id,status=outcome,repairs_used=task['repairs_used'])


def phase_view(phase, state):
    tasks = task_map(state)
    for row in phase['tasks']:
        if row['id'] not in tasks:
            continue
        task = tasks[row['id']]
        row.update(status=task['status'], blocker=task['blocker'],next_action=task['next_action'])
        row['evidence'] = [r['path'] for r in task['evidence']]
        if task['attempts']:
            row['evidence'].append(task['attempts'][-1]['start_evidence']['path'])
    return phase


def synchronize(root, state):
    """Refresh derived phase/checkpoint views; continuation.json owns queue state."""
    phase_path = root/'state/phase-todo.json'
    if not phase_path.exists():
        return
    phase = phase_view(json.loads(phase_path.read_text()), state)
    write_json(phase_path,phase)
    eligible = [t for t in phase['tasks'] if t['status'] == 'in_progress']
    by_id = {t['id']:t for t in phase['tasks']}
    eligible += [t for t in phase['tasks'] if t['status'] in {'planned','failed'}
                 and all(by_id[d]['status']=='done' for d in t['depends_on'])]
    checkpoint_path = root/'state/checkpoint.json'
    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {}
    selected = eligible[0] if eligible else None
    view = summary(state)
    checkpoint.update(schema='forge-checkpoint/2',updated_at=stamp(),active_phase=phase['phase_id'],
        lifecycle='active',project_goal_status=state['project_goal']['status'],
        delivery_status=state['deliveries'],next_task_id=selected['id'] if selected else None,
        next_queue_task_id=view['next_task_id'],next_action=selected['next_action'] if selected else 'Inspect branch-specific blockers and the independent ready queue.',
        continuation_state='state/continuation.json',execution=state['execution'])
    write_json(checkpoint_path,checkpoint)


def advance(root, state, next_path):
    current = phase_view(json.loads(read_file(root,'state/phase-todo.json')), state)
    if any(t['status'] != 'done' for t in current['tasks'][:-1]):
        raise ValueError('Current phase work has not passed')
    successor = phase_view(json.loads(read_file(root,next_path)), state)
    first = successor['tasks'][0]
    task = task_map(state)[first['id']]
    if task['status'] not in {'in_progress','done'} or not task['attempts']:
        raise ValueError('Next phase first task has no actual start')
    start = task['attempts'][0]['start_evidence']
    if ref(root,start['path']) != start:
        raise ValueError('Next phase start evidence changed')
    transition = current['tasks'][-1]
    transition.update(status='done',evidence=[start['path']],blocker=None,
        next_action='Continue the already started successor task.',
        transition=dict(next_phase_id=successor['phase_id'],todo_path='state/phase-todo.json',
                        first_task_id=first['id'],start_evidence=[start['path']]))
    archive = root/'state/history'/(current['phase_id']+'-todo.json')
    if archive.exists():
        raise ValueError('Archived phase already exists; reconcile without overwriting history')
    write_json(archive,current)
    write_json(root/'state/phase-todo.json',successor)
    return dict(closed_phase=current['phase_id'],active_phase=successor['phase_id'],actual_start=start)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    sub = parser.add_subparsers(dest='command',required=True)
    for name in ['next','status','validate','sync']:
        sub.add_parser(name)
    start = sub.add_parser('start');start.add_argument('task_id');start.add_argument('--evidence',required=True)
    done = sub.add_parser('finish');done.add_argument('task_id');done.add_argument('--result',required=True)
    blocked = sub.add_parser('block');blocked.add_argument('task_id');blocked.add_argument('--reason',required=True);blocked.add_argument('--evidence',required=True);blocked.add_argument('--next-action',required=True)
    delivery = sub.add_parser('delivery');delivery.add_argument('id');delivery.add_argument('--evidence',required=True)
    phase = sub.add_parser('advance');phase.add_argument('--next-phase',required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    mutating = args.command not in {'next','status','validate'}
    def execute():
        state = load(root)
        errors = validate(state,root)
        if errors:
            raise ValueError('; '.join(errors))
        if args.command in {'next','status'}:
            return summary(state)
        if args.command == 'validate':
            return dict(ok=True,tasks=len(state['tasks']),project_status=state['project_goal']['status'])
        if args.command == 'start':
            result = begin(state,root,args.task_id,args.evidence)
        elif args.command == 'finish':
            result = finish(state,root,args.task_id,args.result)
        elif args.command == 'block':
            task = task_map(state)[args.task_id]
            if task['status'] in TERMINAL:
                raise ValueError('Cannot overwrite a completed task')
            task.update(status='blocked',blocker=args.reason,evidence=[ref(root,args.evidence)],next_action=args.next_action)
            if task['attempts'] and task['attempts'][-1]['status']=='in_progress':
                task['attempts'][-1].update(status='blocked',ended_at=stamp(),reason=args.reason,evidence=task['evidence'])
            result = dict(task_id=args.task_id,status='blocked')
        elif args.command == 'advance':
            result = advance(root,state,args.next_phase)
        elif args.command == 'sync':
            result = dict(synchronized=True)
        else:
            state['deliveries'][args.id] = dict(status='delivered',evidence=ref(root,args.evidence),at=stamp())
            result = dict(delivery=args.id,project_status=state['project_goal']['status'])
        state.setdefault('events',[]).append(dict(at=stamp(),command=args.command,result=result))
        write_json(root/'state/continuation.json',state)
        synchronize(root,state)
        return result
    try:
        if mutating:
            with locked(root):result=execute()
        else:result=execute()
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps(dict(error=str(exc)),ensure_ascii=False))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
