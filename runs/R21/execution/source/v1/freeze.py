from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,time,argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--execution',required=True);a=p.parse_args()
repo=Path(a.repo); ex=Path(a.execution); src=ex/'source/v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
for name in ['input-lock.json','design-lock.json','clarification-lock.json']:
    lock=repo/'runs/R21'/name; obj=json.loads(lock.read_text('utf-8'))
    for f in obj['files']:
        # Identity metadata can contain restricted files: verify only authorized input/content bytes.
        if name=='design-lock.json' and f['path']!='runs/R21/design/WORKFLOW.md':continue
        q=repo/f['path'];assert q.stat().st_size==f['size_bytes'] and sha(q)==f['sha256']
        checks.append({'path':f['path'],'sha256':sha(q)})
target=src/'reference_policy.py'
assert not target.exists()
shutil.copyfile(repo/'runs/R21/inputs/reference/run.py',target)
obj={'schema':'prospective-freeze/1','actual_frozen_at_utc':datetime.now(timezone.utc).isoformat(),'monotonic_ns':time.monotonic_ns(),'input_and_workflow_identities_checked':checks,'source_hashes':{q.name:sha(q) for q in sorted(src.iterdir()) if q.is_file()},'claim':'before any model fit or candidate performance; author protocol, not independent acceptance','model':None,'tokens':None,'cost':None}
with (ex/'prospective-freeze.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
with (ex/'recovery-log.json').open('x',encoding='utf-8') as f:json.dump([{'phase':'read-only tool recovery','observed':'initial nested lock paths missing','action':'root supplied canonical sibling R21 locks; no fit occurred','scientific_failure':False}],f,ensure_ascii=False,indent=2)
print(json.dumps(obj,ensure_ascii=False,indent=2))
