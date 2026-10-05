"""Read actual resumption capabilities; only write the allocated probe artifact."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

root = Path('/workspace/A111')
out = Path(__file__).resolve().parent
def command(argv):
    try:
        r = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=20)
        return dict(argv=argv, exit_code=r.returncode, stdout=r.stdout, stderr=r.stderr)
    except (OSError, subprocess.TimeoutExpired) as e:
        return dict(argv=argv, unavailable=type(e).__name__, error=str(e))

payload = b'A111 post-release scheduled resumption read/write probe\n'
probe = out/'checkout-write-probe.txt'
with probe.open('xb') as f:
    f.write(payload); f.flush(); os.fsync(f.fileno())
read_write = probe.read_bytes() == payload
versions = [command([name, '--version']) for name in ('python3', 'python3.10', 'python3.12', 'git', 'chromium', 'node')]
candidate = json.loads((root/'runs/R06/final/source-candidate.json').read_text())
changed = [row['path'] for row in candidate['files'] if hashlib.sha256((root/row['path']).read_bytes()).hexdigest() != row['sha256']]
state = json.loads((root/'state/continuation.json').read_text())
by_id = {t['id']:t for t in state['tasks']}
ready = [t['id'] for t in state['tasks'] if t['status'] in ('planned','failed') and t.get('repairs_used',0) < t.get('repair_limit',2) and all(by_id[d]['status']=='done' for d in t.get('depends_on',[]))]
try:
    playwright = importlib.metadata.version('playwright')
except importlib.metadata.PackageNotFoundError:
    playwright = None
result = dict(schema='forge-resumption-host-observation/1', observed_at=datetime.now(timezone.utc).isoformat(),
    cwd=str(root), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
    interpreter=sys.executable, read_write=read_write, write_probe=str(probe.relative_to(root)),
    command_execution=True, versions=versions, playwright_distribution=playwright,
    head=command(['git','rev-parse','HEAD']),
    git_status_counts=command(['git','status','--porcelain=v1','--untracked-files=normal']),
    candidate=dict(sha256=candidate['sha256'],files=len(candidate['files']),changed=changed),
    ready_tasks=ready,
    task_counts={s:sum(t['status']==s for t in state['tasks']) for s in sorted({t['status'] for t in state['tasks']})},
    limits=['Tool --version verifies executability, not a new complete browser or smoke acceptance.',
            'No provider credentials read or network service called.',
            'Same kernel boot does not establish an independent cold-start execution.',
            'No task attempt, worker creation, publication, or external business effect performed.'])
with (out/'host-observation.json').open('x') as f:
    json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')
result['git_status_counts'] = {'exit_code':result['git_status_counts']['exit_code'],'entries':len(result['git_status_counts']['stdout'].splitlines())}
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if read_write and not changed and all(v.get('exit_code')==0 for v in versions) else 2)
