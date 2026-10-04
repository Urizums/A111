#!/usr/bin/env python3
"""Read-only portable integrity checks. This does not validate live host behavior."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MUTABLE = {'state', 'runs', 'validation', '.git', '__pycache__'}
MANIFEST_NAMES = {'artifact-manifest.json', 'delivery-manifest.json'}
STATUSES = {'planned', 'in_progress', 'partial', 'done', 'blocked', 'cancelled'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def safe_path(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError('expected a nonempty repository-relative path')
    resolved = (root / value).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError('path escapes repository: ' + value)
    return resolved


def verify_entries(root, entries, prefix=''):
    errors = []
    for row in entries:
        rel = prefix + row.get('path', row.get('relative_path', ''))
        try:
            path = safe_path(root, rel)
            raw = path.read_bytes()
            if len(raw) != row['size_bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                errors.append('hash or size mismatch: ' + rel)
        except (OSError, ValueError, KeyError) as exc:
            errors.append(rel + ': ' + str(exc))
    return errors


def validate_phase(phase, root):
    errors = []
    tasks = phase.get('tasks', [])
    if phase.get('schema') != 'forge-phase-todo/1' or len(tasks) < 2:
        return ['phase schema or tasks invalid']
    ids = [t.get('id') for t in tasks]
    if len(set(ids)) != len(ids) or any(not isinstance(x, str) or not x for x in ids):
        return ['task IDs must be unique nonempty strings']
    by_id = dict(zip(ids, tasks))
    for t in tasks:
        for key in ['title', 'owner', 'depends_on', 'write_paths', 'acceptance', 'status', 'evidence', 'blocker', 'next_action']:
            if key not in t:
                errors.append(t['id'] + ': missing ' + key)
        if t.get('status') not in STATUSES:
            errors.append(t['id'] + ': invalid status')
        if not t.get('acceptance') or not t.get('write_paths'):
            errors.append(t['id'] + ': missing acceptance or write scope')
        for dep in t.get('depends_on', []):
            if dep not in by_id:
                errors.append(t['id'] + ': unknown dependency ' + dep)
            elif t.get('status') == 'done' and by_id[dep].get('status') != 'done':
                errors.append(t['id'] + ': done before dependency ' + dep)
        for rel in t.get('write_paths', []) + t.get('evidence', []):
            try:
                p = safe_path(root, rel)
                if rel in t.get('evidence', []) and not p.is_file():
                    errors.append(t['id'] + ': missing evidence ' + rel)
            except ValueError as exc:
                errors.append(t['id'] + ': ' + str(exc))
        if t.get('status') == 'done' and not t.get('evidence'):
            errors.append(t['id'] + ': done without evidence')
    visiting, visited = set(), set()

    def visit(node):
        if node in visiting:
            errors.append('dependency cycle at ' + node)
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in by_id[node].get('depends_on', []):
            if dep in by_id:
                visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in ids:
        visit(node)
    final = tasks[-1]
    if final.get('title') != '启动下一阶段任务':
        errors.append('last task must launch next phase')
    if set(final.get('depends_on', [])) != set(ids[:-1]):
        errors.append('transition must depend on every earlier phase task')
    if final.get('status') == 'done':
        trans = final.get('transition', {})
        if not trans.get('start_evidence'):
            errors.append('transition done without actual-start evidence')
        try:
            nxt = read(safe_path(root, trans.get('todo_path')))
            # The active frontier moves; a historical transition still binds its
            # original successor, whose completed graph is archived unchanged.
            if (trans.get('todo_path') == 'state/phase-todo.json'
                    and nxt['phase_id'] != trans.get('next_phase_id')):
                nxt = read(safe_path(root, 'state/history/' + trans['next_phase_id'] + '-todo.json'))
            first = nxt['tasks'][0]
            if nxt['phase_id'] != trans.get('next_phase_id') or first['id'] != trans.get('first_task_id'):
                errors.append('transition next phase/first task mismatch')
            started = first['status'] in {'in_progress', 'partial', 'done'}
            if first['status'] == 'blocked':
                # A real successor may fail after the transition. Require its
                # retained original attempt, not merely a new blocked label.
                queue = read(safe_path(root, 'state/continuation.json'))
                task = next((t for t in queue['tasks'] if t['id'] == first['id']), {})
                for attempt in task.get('attempts', []):
                    ref = attempt.get('start_evidence', {})
                    path = ref.get('path')
                    if path in trans.get('start_evidence', []) and path in first.get('evidence', []):
                        raw = safe_path(root, path).read_bytes()
                        if hashlib.sha256(raw).hexdigest() == ref.get('sha256'):
                            started = True
            if not started or not first.get('evidence'):
                errors.append('next first task has not actually started with evidence')
            for rel in trans.get('start_evidence', []):
                if not safe_path(root, rel).is_file():
                    errors.append('missing start evidence: ' + rel)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append('transition: ' + str(exc))
    return errors


def validate_checkpoint(checkpoint, phase):
    errors = []
    if checkpoint['active_phase'] != phase['phase_id']:
        errors.append('checkpoint phase mismatch')
    tasks = {t['id']: t for t in phase['tasks']}
    if checkpoint.get('lifecycle') == 'delivered':
        if checkpoint.get('next_task_id') is not None:
            errors.append('delivered checkpoint must not select another task')
        if any(t['status'] not in {'done', 'cancelled'} for t in tasks.values()):
            errors.append('delivered checkpoint has unfinished phase work')
        if not checkpoint.get('delivery_evidence'):
            errors.append('delivered checkpoint requires delivery evidence')
    else:
        selected = tasks.get(checkpoint['next_task_id'])
        executable = [t for t in tasks.values()
                      if t['status'] not in {'done', 'cancelled', 'blocked'}
                      and all(tasks[d]['status'] == 'done' for d in t['depends_on'])]
        blocked_frontier = (checkpoint.get('next_task_id') is None
                            and checkpoint.get('project_goal_status') == 'active'
                            and any(t['status'] == 'blocked' for t in tasks.values())
                            and not executable)
        if blocked_frontier:
            pass
        elif not selected or selected['status'] in {'done', 'cancelled'}:
            errors.append('checkpoint next task is absent or terminal')
        elif any(tasks[x]['status'] != 'done' for x in selected['depends_on']):
            errors.append('checkpoint next task dependencies not ready')
    return errors


def validate_continuation(checkpoint, state, root):
    from continuation import summary, validate
    errors = validate(state, root)
    frontier = summary(state)
    if checkpoint.get('project_goal_status') != state['project_goal']['status']:
        errors.append('checkpoint project goal differs from continuation queue')
    if checkpoint.get('next_queue_task_id') != frontier['next_task_id']:
        errors.append('checkpoint next queue task differs from ready/active work')
    if checkpoint.get('lifecycle') == 'delivered' and state['project_goal']['status'] == 'active':
        errors.append('delivery milestone must not terminate active project')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    errors = []
    try:
        lock = read(ROOT / 'state/source-lock.json')
        errors += verify_entries(ROOT, lock['entries'])
        cutoff = read(ROOT / 'evidence/c1/Snapshot_Manifest.json')
        errors += verify_entries(ROOT, cutoff['entries'], 'evidence/c1/')
        manifest = read(ROOT / 'artifact-manifest.json')
        errors += verify_entries(ROOT, manifest['entries'])
        expected = {r['path'] for r in manifest['entries']}
        actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()
                  and not any(x in MUTABLE for x in p.relative_to(ROOT).parts)
                  and p.name not in MANIFEST_NAMES and p.suffix not in {'.pyc','.bundle','.gz'}}
        if actual != expected:
            errors.append('release manifest coverage differs: ' + repr(sorted(actual ^ expected)))
        phase = read(ROOT / 'state/phase-todo.json')
        errors += validate_phase(phase, ROOT)
        for history in sorted((ROOT / 'state/history').glob('*-todo.json')):
            errors += validate_phase(read(history), ROOT)
        revision_files_checked = 0
        revision_index = ROOT / 'state/revision-locks.json'
        if revision_index.exists():
            for rel in read(revision_index)['locks']:
                entries = read(safe_path(ROOT, rel))['files']
                errors += verify_entries(ROOT, entries)
                revision_files_checked += len(entries)
        checkpoint = read(ROOT / 'state/checkpoint.json')
        errors += validate_checkpoint(checkpoint, phase)
        if (ROOT / 'state/continuation.json').exists():
            errors += validate_continuation(checkpoint, read(ROOT / 'state/continuation.json'), ROOT)
        for rel in checkpoint.get('delivery_evidence', []):
            if not safe_path(ROOT, rel).is_file():
                errors.append('missing delivery evidence: ' + rel)
        for p in [ROOT/'README.md', ROOT/'START_HERE.md', *sorted((ROOT/'prompts').glob('*.md'))]:
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', p.read_text()):
                if '://' not in target and not target.startswith('#'):
                    link = (p.parent / target.split('#')[0]).resolve()
                    if not link.is_relative_to(ROOT) or not link.exists():
                        errors.append('broken entry link: ' + target)
        summary = {'schema':'forge-handoff-check/1','ok':not errors,'errors':errors,
                   'skill_files_checked':len(lock['entries']), 'cutoff_files_checked':len(cutoff['entries']),
                   'release_files_checked':len(manifest['entries']), 'revision_files_checked':revision_files_checked,
                   'active_phase':phase['phase_id'],
                   'next_task_id':checkpoint['next_task_id'],
                   'scope':'read-only hashes, paths, phase dependency/transition invariants; not live or semantic acceptance'}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        summary = {'ok':False,'errors':errors+[str(exc)]}
    print(json.dumps(summary, ensure_ascii=False, indent=2) if args.json else
          ('PASS' if summary['ok'] else 'FAIL') + '\n' + json.dumps(summary, ensure_ascii=False))
    return 0 if summary['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
