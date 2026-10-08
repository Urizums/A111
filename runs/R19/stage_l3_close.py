"""Stage frozen R19 evidence and root integration; exclude active actor scopes."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
paths = set()
for relative in ['START_HERE.md', 'CODEX_HANDOFF.md', 'artifact-manifest.json',
                 'state/checkpoint.json', 'state/continuation.json', 'state/revision-locks.json',
                 'runs/R19/TODO.md', 'runs/R19/REPORT.md', 'runs/R19/coordinator-attempts.md',
                 'runs/R19/integrate_l3_diagnosis_l4_start.py', 'runs/R19/integrate_l4_preparation.py',
                 'runs/R19/stage_l3_close.py', 'runs/R19/refresh_integrity.py']:
    paths.add(relative)
for directory in ['runs/R19/observations', 'runs/R19/integrity-history', 'runs/R19/publication']:
    for path in (ROOT / directory).glob('*'):
        if path.is_file():
            if path.name.endswith('command.json'):
                receipt = json.loads(path.read_text(encoding='utf-8'))
                if receipt.get('state') == 'started':
                    continue
            paths.add(path.relative_to(ROOT).as_posix())
for directory in ['runs/R19/levels/L3', 'runs/R19/levels/L4']:
    for path in (ROOT / directory).glob('*'):
        if path.is_file():
            if path.name.endswith('command.json'):
                receipt = json.loads(path.read_text(encoding='utf-8'))
                if receipt.get('state') == 'started':
                    continue
            paths.add(path.relative_to(ROOT).as_posix())
for path in (ROOT / 'runs/R19/levels/L3/review/recheck-final-1').rglob('*'):
    if path.is_file():
        assert '__pycache__' not in path.parts
        paths.add(path.relative_to(ROOT).as_posix())
paths.add('runs/R19/levels/L3/review/recheck-final-1-lock.json')
preparation_lock = json.loads((ROOT / 'runs/R19/levels/L4/review/preparation-lock.json').read_text(encoding='utf-8'))
for entry in preparation_lock['files']:
    paths.add(entry['path'])
paths.add('runs/R19/levels/L4/review/preparation-lock.json')
frozen_L4_execution = set()
execution_lock_path = ROOT / 'runs/R19/levels/L4/execution-lock.json'
if execution_lock_path.exists():
    execution_lock = json.loads(execution_lock_path.read_text(encoding='utf-8'))
    frozen_L4_execution = {entry['path'] for entry in execution_lock['files']}
    paths.update(frozen_L4_execution)
    paths.add('runs/R19/levels/L4/execution-lock.json')
frozen_L4_followups = set()
for scope in ['review/initial', 'execution-v2', 'review/recheck-1', 'review/recheck-preparation']:
    relative = f'runs/R19/levels/L4/{scope}-lock.json'
    lock_path = ROOT / relative
    if lock_path.exists():
        lock = json.loads(lock_path.read_text(encoding='utf-8'))
        scope_paths = {entry['path'] for entry in lock['files']}
        paths.update(scope_paths)
        paths.add(relative)
        frozen_L4_followups.update(scope_paths)
        frozen_L4_followups.add(relative)
index = json.loads((ROOT / 'state/revision-locks.json').read_text(encoding='utf-8'))
frozen_final = set()
for relative in index['locks']:
    paths.add(relative)
    for entry in json.loads((ROOT / relative).read_text(encoding='utf-8'))['files']:
        paths.add(entry['path'])
        if entry['path'].startswith('runs/R19/final/'):
            frozen_final.add(entry['path'])
for path in (ROOT / 'runs/R19/final').glob('*'):
    if path.is_file() and path.suffix in {'.py', '.json', '.md'}:
        if path.name.endswith('command.json') and json.loads(path.read_text(encoding='utf-8')).get('state') == 'started':
            continue
        paths.add(path.relative_to(ROOT).as_posix())
for path in (ROOT / 'runs/R19/observations/forward-case-preparation').glob('*'):
    if path.is_file():
        paths.add(path.relative_to(ROOT).as_posix())
for relative in paths:
    if relative.endswith('command.json'):
        receipt = json.loads((ROOT / relative).read_text(encoding='utf-8'))
        if receipt.get('schema') == 'forge-command-record/1':
            assert receipt['state'] == 'finished', relative
ordered = sorted(paths)
for offset in range(0, len(ordered), 100):
    subprocess.run(['git', '-c', 'core.longpaths=true', 'add', '--', *ordered[offset:offset + 100]],
                   cwd=ROOT, check=True)
staged = subprocess.check_output(['git', '-c', 'core.longpaths=true', 'diff', '--cached', '--name-only'],
                                cwd=ROOT, encoding='utf-8').splitlines()
for relative in staged:
    assert relative != 'state/coordinator-lease.json'
    if relative.startswith('runs/R19/levels/L4/execution/'):
        assert relative in frozen_L4_execution, ('Unfrozen L4 production', relative)
    if relative.startswith('runs/R19/levels/L4/review/'):
        assert (relative == 'runs/R19/levels/L4/review/preparation-lock.json' or relative.startswith('runs/R19/levels/L4/review/preparation/') or relative in frozen_L4_followups), ('Unfrozen L4 review', relative)
    if relative.startswith('runs/R19/levels/L4/execution-v2/'):
        assert relative in frozen_L4_followups, ('Unfrozen L4 informed production', relative)
    if relative.startswith('runs/R19/final/forward/') and not relative.endswith('-lock.json'):
        assert relative in frozen_final, ('Unfrozen forward actor/input file', relative)
tracked = set(subprocess.check_output(['git', '-c', 'core.longpaths=true', 'ls-files', '-z'],
                                     cwd=ROOT, encoding='utf-8').split('\0'))
index = json.loads((ROOT / 'state/revision-locks.json').read_text(encoding='utf-8'))
for relative in index['locks']:
    assert relative in tracked, ('Unstaged revision lock', relative)
    for entry in json.loads((ROOT / relative).read_text(encoding='utf-8'))['files']:
        assert entry['path'] in tracked, ('Unstaged frozen file', entry['path'])
print(json.dumps({'selected_files': len(ordered), 'staged_changes': len(staged),
                  'live_L4_review_and_lease_excluded': True, 'revision_index_paths_present': True}))
