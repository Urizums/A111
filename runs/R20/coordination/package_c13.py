"""Package only the nine locked Markdown files and verify archive bytes in memory."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
source = ROOT / 'runs/R20/final/candidate/C13/forge-agent-flow'
lock = json.loads((ROOT / 'runs/R20/final/candidate/C13-lock.json').read_text(encoding='utf-8'))
files = sorted(p for p in source.rglob('*') if p.is_file())
assert len(files) == 9 and all(p.suffix == '.md' for p in files)
expected = {r['path']:r for r in lock['files']}
for p in files:
    b = p.read_bytes(); row = expected[p.relative_to(ROOT).as_posix()]
    assert (len(b), hashlib.sha256(b).hexdigest()) == (row['size_bytes'], row['sha256'])
dest = ROOT / 'runs/R20/final/package/Forge-C13-meta-workflow-candidate.zip'
assert not dest.exists()
dest.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(dest, 'x', compression=zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, 'forge-agent-flow/' + p.relative_to(source).as_posix())
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == 9
    for p in files:
        assert z.read('forge-agent-flow/' + p.relative_to(source).as_posix()) == p.read_bytes()
b = dest.read_bytes()
summary = dict(path=dest.relative_to(ROOT).as_posix(), bytes=len(b), sha256=hashlib.sha256(b).hexdigest(),
    markdown_files=9, scripts_tests_runners=0, archive_readback_exact=True,
    interpretation='Packaging identity only; forward behavior is accepted separately. No personal skill installation.')
path = dest.parent / 'package-identity.json'
with path.open('x', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2); f.write('\n')
print(json.dumps(summary))
