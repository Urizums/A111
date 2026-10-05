"""Freeze an indexed source tree for tests, without changing any historical input."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import sys

ROOT=Path(__file__).resolve().parents[3]
def build():
    tree=subprocess.check_output(['git','write-tree'],cwd=ROOT).decode().strip()
    raw=subprocess.check_output(['git','archive','--format=tar',tree],cwd=ROOT)
    target=ROOT.parent/'r08-stable-source.tar'
    target.write_bytes(raw)
    record=dict(schema='forge-stable-source/1',tree=tree,sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw),archive=str(target),scope='staged Git tree fixed before one test retry; original paths and inputs preserved',restore_root='/tmp/a111-r08-stable')
    (ROOT/'runs/R08/design/stable-source.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(record))

def restore():
    target=Path('/tmp/a111-r08-stable')
    if target.exists():raise SystemExit('Refuse to overwrite a previous test tree')
    archive=ROOT.parent/'r08-stable-source.tar'
    record=json.loads((ROOT/'runs/R08/design/stable-source.json').read_text(encoding='utf-8'))
    raw=archive.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==record['sha256']
    target.mkdir()
    rows=[]
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        for m in tar:
            if m.isdir():continue
            if not m.isfile():raise ValueError('Only regular files allowed: '+m.name)
            p=target/m.name
            if not p.resolve().is_relative_to(target):raise ValueError(m.name)
            data=tar.extractfile(m).read()
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(m.mode)
            rows.append(dict(path=m.name,size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    (target/'delivery-manifest.json').write_text(json.dumps(dict(files=rows),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(restored=str(target),files=len(rows),archive_sha256=record['sha256'],manifest='delivery-manifest.json',limits='Explicit local test export; no native worker/provider replay')))

if __name__=='__main__':
    {'build':build,'restore':restore}[sys.argv[1]]()
