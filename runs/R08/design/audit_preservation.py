"""Compare inherited evidence and consumed budgets to this checkout's Git baseline."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[3]

def main():
    baseline = json.loads((ROOT/'runs/R08/windows-preflight/baseline.json').read_text(encoding='utf-8'))['commit']
    archive = subprocess.check_output(['git','archive','--format=tar',baseline],cwd=ROOT)
    errors=[];count=0
    with tarfile.open(fileobj=io.BytesIO(archive)) as t:
        originals={m.name:t.extractfile(m).read() for m in t if m.isfile()}
    for name,raw in originals.items():
        if name.startswith(('runs/','skills/','evidence/','validation/','state/history/')):
            count+=1
            if (ROOT/name).read_bytes()!=raw:errors.append('inherited bytes changed: '+name)
    old=json.loads(originals['state/continuation.json']);new=json.loads((ROOT/'state/continuation.json').read_text(encoding='utf-8'))
    by_id={t['id']:t for t in new['tasks']}
    for task in old['tasks']:
        current=by_id[task['id']]
        for key in ['acceptance','repairs_used','repair_limit']:
            if task[key]!=current[key]:errors.append(task['id']+': changed '+key)
        if current['attempts'][:len(task['attempts'])]!=task['attempts']:
            errors.append(task['id']+': historical attempt changed')
        if task['status']=='blocked' and current['status']!='blocked':
            errors.append(task['id']+': historical blocker removed')
    old_cp=json.loads(originals['state/checkpoint.json']);new_cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
    for key in ['current_delivery_repair_budgets','unresolved_historical_call','full_repair_audit']:
        if old_cp[key]!=new_cp[key]:errors.append('checkpoint history changed: '+key)
    print(json.dumps(dict(ok=not errors,baseline_commit=baseline,inherited_files_checked=count,old_tasks_checked=len(old['tasks']),old_blocked_preserved=sum(t['status']=='blocked' for t in old['tasks']),errors=errors),indent=2))
    return int(bool(errors))

if __name__=='__main__':raise SystemExit(main())
