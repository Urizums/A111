"""Run checks on a byte-verified staged Git export on the local Linux filesystem."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

p=argparse.ArgumentParser()
p.add_argument("--archive",type=Path,required=True)
p.add_argument("--manifest",type=Path,required=True)
a=p.parse_args()
expected=json.loads(a.manifest.read_text(encoding="utf-8"))
assert hashlib.sha256(a.archive.read_bytes()).hexdigest()==expected["archive_sha256"]
with tempfile.TemporaryDirectory(prefix="forge-c10-regression-") as tmp:
    root=Path(tmp)/"checkout"
    root.mkdir()
    with tarfile.open(a.archive) as archive:
        for member in archive.getmembers():
            assert not member.issym() and not member.islnk(),member.name
            assert (root/member.name).resolve().is_relative_to(root)
        archive.extractall(root,filter="data")
    rows=expected["files"]
    for row in rows:
        raw=(root/row["path"]).read_bytes()
        assert len(raw)==row["size_bytes"]
        assert hashlib.sha256(raw).hexdigest()==row["sha256"],row["path"]
    (root/"delivery-manifest.json").write_text(json.dumps(dict(schema="forge-delivery/1",files=rows))+"\n")
    print(json.dumps(dict(staged_tree=expected["staged_tree"],byte_verified_files=len(rows),
        temporary_export=str(root),scope="development regression only; no C10 bundled runtime")),flush=True)
    for argv in [
        ["python3","-B","scripts/verify_handoff.py","--json"],
        ["python3","-B","-m","unittest","discover","-s","scripts","-p","test_*.py"]
    ]:
        result=subprocess.run(argv,cwd=root)
        if result.returncode:
            raise SystemExit(result.returncode)
