"""Stage frozen actor bytes and completed root records; never active actor files."""
import json
import runpy
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT/'runs/R19/stage_l3_close.py'), run_name='__main__')
paths = []
for relative in ['.gitattributes', 'runs/R20/forward-case/PLAN.json', 'runs/R20/final/candidate/C13-change.json']:
    if (ROOT/relative).is_file():
        paths.append(relative)
for f in sorted((ROOT/'runs/R20/coordination').glob('*')):
    if not f.is_file() or f.suffix not in {'.py','.json','.md'}:
        continue
    if f.name.endswith('command.json') and json.loads(f.read_text(encoding='utf-8')).get('state') == 'started':
        continue
    paths.append(f.relative_to(ROOT).as_posix())
if paths:
    subprocess.run(['git','-c','core.longpaths=true','add','--',*paths],cwd=ROOT,check=True)
index = json.loads((ROOT/'state/revision-locks.json').read_text(encoding='utf-8'))
frozen = set()
for relative in index['locks']:
    frozen.add(relative)
    frozen.update(row['path'] for row in json.loads((ROOT/relative).read_text(encoding='utf-8'))['files'])
staged = subprocess.check_output(['git','-c','core.longpaths=true','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
for relative in staged:
    if relative.startswith(('runs/R20/design/','runs/R20/execution/','runs/R20/review/','runs/R20/research/',
        'runs/R20/forward-case/production/','runs/R20/forward-case/review/')):
        assert relative in frozen, ('Unfrozen actor/research file',relative)
    assert relative != 'state/coordinator-lease.json'
print(json.dumps(dict(root_records_selected=len(paths), frozen_actor_only=True, staged_changes=len(staged))))
