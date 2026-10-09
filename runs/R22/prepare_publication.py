"""Retain the failed integration source; refresh only mutable entry hashes."""
import hashlib
import json
import runpy
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    old=json.loads((ROOT/'runs/R22/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items() if k!='R21-next')
    rel='runs/R22/coordination-lock.json'; assert not (ROOT/rel).exists()
    files=[]
    for f in sorted((ROOT/'runs/R22/coordination').iterdir()):
        assert f.is_file(); b=f.read_bytes()
        files.append(dict(path=f.relative_to(ROOT).as_posix(),size_bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    ctl.write_json(ROOT/rel,dict(schema='forge-revision-lock/1',revision='R22 failed integration and informed recovery',
        frozen_at=ctl.stamp(),files=files,claim='Original failed metadata source retained, no scientific result changed.'))
    index=json.loads((ROOT/'state/revision-locks.json').read_text(encoding='utf-8'))
    index['locks'].append(rel); ctl.write_json(ROOT/'state/revision-locks.json',index)
runpy.run_path(str(ROOT/'runs/R19/refresh_integrity.py'),run_name='__main__')
print(json.dumps(dict(old69_preserved=True,failed_integration_retained=True,mutable_entry_catalog_refreshed=True)))
