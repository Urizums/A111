"""Neutral hash check only: no model advice or expected answer."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
level=int(sys.argv[1])
for lock in ['runs/R19/candidate/C11-lock.json','runs/R19/inputs/raw-lock.json']:
    rows=json.loads((ROOT/lock).read_text(encoding='utf-8'))['files']
    for row in rows:
        data=(ROOT/row['path']).read_bytes()
        assert len(data)==row['size_bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
request=(ROOT/f'runs/R19/inputs/L{level}.md').read_bytes()
print(json.dumps(dict(level=level,request_sha256=hashlib.sha256(request).hexdigest(),frozen_skill_and_raw_bytes_match=True,computed_answer=False)))
