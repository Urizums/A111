"""Version the export manifest after current entry documents change; old locks remain frozen."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

root=Path(__file__).resolve().parents[3]
old=root/'artifact-manifest.json'
saved=root/'runs/R10/resumption/entry-before/artifact-manifest.json'
with saved.open('xb') as stream:stream.write(old.read_bytes())
result=subprocess.run([sys.executable,'scripts/freeze_release.py'],cwd=root,capture_output=True,text=True)
print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
assert result.returncode==0
prior=json.loads(saved.read_text(encoding='utf-8'));current=json.loads(old.read_text(encoding='utf-8'))
before={e['path']:e for e in prior['entries']};after={e['path']:e for e in current['entries']}
assert set(before)==set(after)
changed=[p for p in sorted(before) if before[p]!=after[p]]
assert changed==['CODEX_HANDOFF.md','START_HERE.md']
assert saved.read_bytes()==subprocess.run(['git','show','11e5ce90864e73a3f600df066cfbb469c6428a18:artifact-manifest.json'],cwd=root,capture_output=True,check=True).stdout
report=dict(ok=True,old_manifest=saved.relative_to(root).as_posix(),old_manifest_sha256=hashlib.sha256(saved.read_bytes()).hexdigest(),new_manifest_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),files=len(after),changed_entries=changed,old_immutable_source_and_cutoff_checked=True,prior_failed_check_retained='runs/R10/publication/final-handoff-command.json',candidate_or_budget_changed=False,scope='New export manifest for updated entry documents; no original source/input lock or verdict changed')
with (root/'runs/R10/publication/release-manifest-result.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(report,stream,indent=2,ensure_ascii=False);stream.write('\n')
print(json.dumps(report))
