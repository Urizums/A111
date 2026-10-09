"""Retain two harmless frozen EOF findings without rewriting first evidence."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
pairs=[('runs/R20/forward-case/review/initial/receiver_audit.py','runs/R20/forward-case/review/initial-lock.json'),
    ('runs/R20/forward-case/review/preparation/reconstruct_raw.py','runs/R20/forward-case/review/preparation-lock.json')]
rows=[]
for rel,lock in pairs:
    b=(ROOT/rel).read_bytes()
    entry=next(r for r in json.loads((ROOT/lock).read_text(encoding='utf-8'))['files'] if r['path']==rel)
    assert (len(b),hashlib.sha256(b).hexdigest())==(entry['size_bytes'],entry['sha256'])
    assert b.replace(b'\r\n',b'\n').endswith(b'\n\n')
    rows.append(dict(path=rel,lock=lock,size_bytes=len(b),sha256=entry['sha256'],finding='Extra blank EOF, nonfunctional formatting in frozen first receiving source.'))
with (ROOT/'runs/R20/coordination/frozen-style-classification.json').open('x',encoding='utf-8') as f:
    json.dump(dict(original_failure='runs/R20/coordination/source-accepted-style-command.json',exceptions=rows,
        scope='Only these two exact frozen EOF findings classified. Preserve raw bytes and original failure; all remaining index files checked without relaxing global or scientific acceptance.'),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(frozen_EOF_findings=2,first_evidence_unchanged=True)))
