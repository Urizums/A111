"""Make a byte-verified snapshot of staged paths for local Linux regression."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
tree=subprocess.check_output(["git","write-tree"],cwd=ROOT,text=True).strip()
raw=subprocess.check_output(["git","archive","--format=tar",tree],cwd=ROOT)
target=ROOT.parents[1]/"outputs"/"C10-development-regression-export.tar"
assert not target.exists()
rows=[]
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
    for member in archive.getmembers():
        if member.isdir():continue
        assert member.isfile() and (ROOT/member.name).resolve().is_relative_to(ROOT)
        body=archive.extractfile(member).read()
        assert (ROOT/member.name).read_bytes()==body,member.name
        rows.append(dict(path=member.name,size_bytes=len(body),sha256=hashlib.sha256(body).hexdigest()))
target.write_bytes(raw)
report=dict(staged_tree=tree,archive=str(target),archive_sha256=hashlib.sha256(raw).hexdigest(),
    files=rows,limits="Staged development snapshot; not distributable C10 skill and not original live host.")
(HERE/"export-manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(staged_tree=tree,byte_identical_files=len(rows),archive=str(target))))
