"""Verify actual frozen identities and existing references, not scientific quality."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
checked=0
for lock in ['runs/R19/candidate/C11-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/evaluation-lock.json']:
    for row in json.loads((ROOT/lock).read_text(encoding='utf-8'))['files']:
        data=(ROOT/row['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
        if 'size_bytes' in row:assert len(data)==row['size_bytes']
        checked+=1
skill=ROOT/'runs/R19/candidate/C11/forge-agent-flow'
files=[p for p in skill.rglob('*') if p.is_file()]
assert len(files)==9 and all(p.suffix=='.md' for p in files)
links=0
for p in files:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' in target:continue
        assert (p.parent/target.split('#')[0]).exists(),(p,target)
        links+=1
old=json.loads((ROOT/'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
state=json.loads((ROOT/'state/continuation.json').read_text(encoding='utf-8'))
# Exactly match continuation.identity, including its JSON spacing and Unicode policy.
def identity(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
current={t['id']:identity(t) for t in state['tasks']}
assert all(current[ident]==digest for ident,digest in old.items()),'historical task changed'
print(json.dumps(dict(frozen_files=checked,markdown_files=len(files),local_links=links,old_tasks_unchanged=len(old),behavior_acceptance=False)))
