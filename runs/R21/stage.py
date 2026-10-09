"""Stage ended root records and registered frozen R21 actor scopes only."""
import json
import runpy
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT/'runs/R20/stage.py'),run_name='__main__')
paths=[]
for folder in [ROOT/'runs/R21',ROOT/'runs/R21/coordination',ROOT/'runs/R22',ROOT/'runs/R22/coordination']:
    for f in folder.glob('*'):
        if f.is_file() and f.suffix in {'.py','.md','.json'}:
            if f.name.endswith('command.json') and json.loads(f.read_text(encoding='utf-8')).get('state')=='started':
                continue
            paths.append(f.relative_to(ROOT).as_posix())
if paths:
    subprocess.run(['git','-c','core.longpaths=true','add','--',*paths],cwd=ROOT,check=True)
index=json.loads((ROOT/'state/revision-locks.json').read_text(encoding='utf-8'))
frozen=set()
for rel in index['locks']:
    frozen.add(rel)
    frozen.update(r['path'] for r in json.loads((ROOT/rel).read_text(encoding='utf-8'))['files'])
staged=subprocess.check_output(['git','-c','core.longpaths=true','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
for rel in staged:
    assert rel!='state/coordinator-lease.json'
    if rel.startswith(('runs/R21/design/','runs/R21/execution/','runs/R21/review/','runs/R21/final/',
        'runs/R21/protocol/','runs/R21/inputs/','runs/R21/evaluation/',
        'runs/R21/prospective-clarification/','runs/R22/audit/')):
        assert rel in frozen,('Unfrozen R21 actor/input/measurement',rel)
print(json.dumps(dict(root_records_selected=len(paths),staged_changes=len(staged),all_R21_scopes_frozen=True,lease_excluded=True)))
