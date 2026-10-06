"""Development-only package and historical-preservation inspection."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import re
import subprocess
import tarfile
import sys

root = Path(__file__).resolve().parents[3]
candidate = root/'runs/R10/candidate/C8/forge-agent-flow'
errors = []
files = sorted(p for p in candidate.rglob('*') if p.is_file())
for p in files:
    if p.suffix != '.md' or p.is_symlink():
        errors.append('unexpected non-document or symlink: '+str(p))
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        dest = (p.parent/target.split('#')[0]).resolve()
        if '://' in target or not dest.is_relative_to(candidate.resolve()) or not dest.is_file():
            errors.append('non-self-contained reference: '+target)
lock = json.loads((root/'runs/R10/candidate/C8-lock.json').read_text(encoding='utf-8'))
for row in lock['files']:
    raw = (root/row['path']).read_bytes()
    if len(raw)!=row['size_bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
        errors.append('changed C8 source: '+row['path'])
base = '11e5ce90864e73a3f600df066cfbb469c6428a18'
archive = subprocess.run(['git','archive',base], cwd=root, capture_output=True, check=True).stdout
mutable = {'state/continuation.json','state/checkpoint.json','state/project-todo.json','state/coordinator-lease.json','state/phases/R09.json','state/revision-locks.json','CODEX_HANDOFF.md','START_HERE.md'}
checked = 0
with tarfile.open(fileobj=BytesIO(archive)) as tar:
    prior = json.load(tar.extractfile('state/continuation.json'))
    for member in tar.getmembers():
        if not member.isfile() or member.name in mutable:
            continue
        if (root/member.name).read_bytes()!=tar.extractfile(member).read():
            errors.append('changed inherited file: '+member.name)
        checked += 1
current = json.loads((root/'state/continuation.json').read_text(encoding='utf-8'))
by_id = {t['id']:t for t in current['tasks']}
for old in prior['tasks']:
    now = by_id[old['id']]
    if old['id']!='R09-02':
        if old!=now:
            errors.append('changed inherited task: '+old['id'])
    else:
        for field in ['inputs','acceptance','depends_on','repair_limit']:
            if old[field]!=now[field]:
                errors.append('changed frozen R09 field: '+field)
        if now['repairs_used']<old['repairs_used']:
            errors.append('R09 budget reset')
for key in ['schema','project_goal','deliveries','task_expansion_basis']:
    if current[key]!=prior[key]:
        errors.append('changed historical continuation '+key)
result = dict(ok=not errors, errors=errors, candidate_files=len(files), candidate_script_files=0, candidate_test_files=0, inherited_files_byte_identical=checked if not any('file:' in e for e in errors) else None, inherited_tasks_preserved=len(prior['tasks']), C8_source_repairs=0, old_blocked_ids=[t['id'] for t in prior['tasks'] if t['status']=='blocked'], scope='source structure, references and retained history only; not behavioral acceptance')
output = root/sys.argv[1]
with output.open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(result,stream,indent=2,ensure_ascii=False);stream.write('\n')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(0 if result['ok'] else 1)
