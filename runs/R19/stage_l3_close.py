"""Stage completed L3 evidence and L4 dispatch, excluding live L4 work."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
paths = set()
for relative in ['START_HERE.md', 'CODEX_HANDOFF.md', 'artifact-manifest.json',
                 'state/checkpoint.json', 'state/continuation.json', 'state/revision-locks.json',
                 'runs/R19/TODO.md', 'runs/R19/REPORT.md', 'runs/R19/coordinator-attempts.md',
                 'runs/R19/integrate_l3_diagnosis_l4_start.py', 'runs/R19/integrate_l4_preparation.py',
                 'runs/R19/stage_l3_close.py']:
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
    assert not relative.startswith('runs/R19/levels/L4/execution/')
    if relative.startswith('runs/R19/levels/L4/review/'):
        assert relative == 'runs/R19/levels/L4/review/preparation-lock.json' or relative.startswith('runs/R19/levels/L4/review/preparation/')
tracked = set(subprocess.check_output(['git', '-c', 'core.longpaths=true', 'ls-files', '-z'],
                                     cwd=ROOT, encoding='utf-8').split('\0'))
index = json.loads((ROOT / 'state/revision-locks.json').read_text(encoding='utf-8'))
for relative in index['locks']:
    assert relative in tracked, ('Unstaged revision lock', relative)
    for entry in json.loads((ROOT / relative).read_text(encoding='utf-8'))['files']:
        assert entry['path'] in tracked, ('Unstaged frozen file', entry['path'])
print(json.dumps({'selected_files': len(ordered), 'staged_changes': len(staged),
                  'live_L4_and_lease_excluded': True, 'revision_index_paths_present': True}))
