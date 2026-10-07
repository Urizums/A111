"""Freeze a terminal actor's actual artifact bytes before a receiving handoff."""
import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
level=int(sys.argv[1]);role=sys.argv[2]
base=ROOT/f'runs/R19/levels/L{level}'
scope=base/role
paths=sorted(p for p in scope.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
assert paths,'no artifacts'
rows=[]
for p in paths:
    data=p.read_bytes()
    rows.append(dict(path=p.relative_to(ROOT).as_posix(),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
lock=base/f'{role}-lock.json'
with lock.open('x',encoding='utf-8') as f:
    json.dump(dict(schema='forge-trial-artifact-lock/1',frozen_at=datetime.now(timezone.utc).isoformat(),level=level,scope=role,files=rows,
        claim='Actual bytes frozen after terminal notification; not correctness or independent acceptance.'),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(level=level,scope=role,files=len(rows))))
