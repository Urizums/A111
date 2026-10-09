"""Stage the bounded R23 probe only after actors terminate and scopes freeze."""
import json
import runpy
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT/'runs/R22/stage_current.py'),run_name='__main__')
state=json.loads((ROOT/'state/continuation.json').read_text(encoding='utf-8'))
assert not state['execution']['current_native_pending']
extra=[]
for directory in ['runs/R23/before-execution','runs/R23/coordination']:
    extra.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).glob('*') if p.is_file())
if extra:subprocess.run(['git','-c','core.longpaths=true','add','--',*extra],cwd=ROOT,check=True)
staged=subprocess.check_output(['git','-c','core.longpaths=true','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
invalid=[];commands=0
for rel in staged:
    assert rel!='state/coordinator-lease.json'
    p=ROOT/rel
    if p.suffix not in {'.json','.txt'}:continue
    try:j=json.loads(p.read_bytes())
    except (ValueError,UnicodeDecodeError):
        assert not {'receipts','records'}.intersection(p.parts),('Invalid command receipt',rel)
        if p.suffix=='.json':invalid.append(rel)
        continue
    if isinstance(j,dict) and j.get('schema')=='forge-command-record/1':
        assert j['state']=='finished' and isinstance(j['exit_code'],int) and j.get('end'),rel
        commands+=1
print(json.dumps(dict(staged_changes=len(staged),terminal_records_by_content=commands,preserved_invalid_nonreceipt_json=invalid,lease_excluded=True)))
