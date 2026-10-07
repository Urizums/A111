"""Package frozen pure-document C10; development helper stays outside the ZIP."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
candidate = ROOT / "runs/R17/candidate/C10/forge-agent-flow"
lock = json.loads((ROOT / "runs/R17/candidate/C10-lock.json").read_text(encoding="utf-8"))
assert len(lock["files"]) == 9
payload = {}
for item in lock["files"]:
    source = ROOT / item["path"]
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item["sha256"], item["path"]
    name = "forge-agent-flow/" + source.relative_to(candidate).as_posix()
    assert name.endswith(".md")
    payload[name] = raw

archive = HERE / "Forge-C10-meta-workflow.zip"
assert not archive.exists()
with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
    for name, raw in sorted(payload.items()):
        z.writestr(name, raw)
unpacked = HERE / "unpacked"
assert not unpacked.exists()
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist()) == set(payload)
    for name in z.namelist():
        target = unpacked / name
        assert target.resolve().is_relative_to(unpacked.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(z.read(name))
        assert target.read_bytes() == payload[name]

deliveries = ROOT.parents[1] / "outputs"
user_folder = deliveries / "Forge-C10-meta-workflow"
user_archive = deliveries / archive.name
assert not user_folder.exists() and not user_archive.exists()
shutil.copytree(unpacked, user_folder)
shutil.copyfile(archive, user_archive)
assert user_archive.read_bytes() == archive.read_bytes()
for name, raw in payload.items():
    assert (user_folder / name).read_bytes() == raw

files = [archive, *sorted(unpacked.rglob("*.md"))]
package_lock = dict(schema="forge-revision-lock/1", revision="C10-package", files=[
    dict(path=p.relative_to(ROOT).as_posix(), size_bytes=p.stat().st_size,
         sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files
])
(HERE / "package-lock.json").write_text(json.dumps(package_lock, indent=2) + "\n", encoding="utf-8")
report = dict(
    candidate_lock="runs/R17/candidate/C10-lock.json", document_files=9,
    scripts=0, tests=0, runtime_dependencies=0,
    byte_identical=True, fresh_unpack_verified=True,
    user_folder=str(user_folder), user_archive=str(user_archive),
    candidate_author_policy="classified progress; C9 frozen 2/2 unchanged",
    limits="Packaging identity only; no behavioral acceptance, personal installation or contest-quality claim."
)
(HERE / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
