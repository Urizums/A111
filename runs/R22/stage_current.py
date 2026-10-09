"""Stage registered immutable artifacts and finished root records; lease stays local."""
import json
import runpy
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT/'runs/R21/stage.py'),run_name='__main__')
paths=[]
for rel in ['runs/R22','runs/R22/before-execution','runs/R22/coordination-current','runs/R23','runs/R23/before']:
    for p in (ROOT/rel).glob('*'):
        if not p.is_file() or p.suffix not in {'.py','.md','.json'}:continue
        if p.suffix=='.json':
            obj=json.loads(p.read_text(encoding='utf-8'))
            if isinstance(obj,dict) and obj.get('schema')=='forge-command-record/1' and obj['state']!='finished':continue
        paths.append(p.relative_to(ROOT).as_posix())
for offset in range(0,len(paths),100):
    subprocess.run(['git','-c','core.longpaths=true','add','--',*paths[offset:offset+100]],cwd=ROOT,check=True)
index=json.loads((ROOT/'state/revision-locks.json').read_text(encoding='utf-8'))
frozen=set(index['locks'])
for rel in index['locks']:frozen.update(r['path'] for r in json.loads((ROOT/rel).read_text(encoding='utf-8'))['files'])
staged=subprocess.check_output(['git','-c','core.longpaths=true','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
scopes=('runs/R22/execution/','runs/R22/review/','runs/R22/protocol/','runs/R22/final/','runs/R22/candidate/',
    'runs/R23/brief/','runs/R23/audit/','runs/R23/design/','runs/R23/execution/','runs/R23/review/','runs/R23/final/','runs/R23/candidate/')
for rel in staged:
    assert rel!='state/coordinator-lease.json'
    if rel.startswith(scopes):assert rel in frozen,('Unfrozen actor/input/result staged',rel)
    p=ROOT/rel
    if p.suffix=='.json':
        obj=json.loads(p.read_text(encoding='utf-8'))
        if isinstance(obj,dict) and obj.get('schema')=='forge-command-record/1':assert obj['state']=='finished',rel
print(json.dumps(dict(staged_changes=len(staged),all_selected_actor_scopes_frozen=True,all_receipts_terminal=True,lease_excluded=True)))
