"""Package frozen Markdown only and verify a real unpack, not behavioral quality."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R19/candidate/C11'
OUT=ROOT/'runs/R19/package'
OUT.mkdir(parents=True,exist_ok=True)
zip_path=OUT/'Forge-C11-meta-workflow-candidate.zip'
assert not zip_path.exists()
files=sorted(p for p in BASE.rglob('*') if p.is_file())
assert len(files)==9 and all(p.suffix=='.md' for p in files)
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.relative_to(BASE).as_posix())
unpacked=OUT/'unpacked'
assert not unpacked.exists()
with zipfile.ZipFile(zip_path) as z:z.extractall(unpacked)
for p in files:assert p.read_bytes()==(unpacked/p.relative_to(BASE)).read_bytes()
report=dict(files=9,bundled_scripts=0,zip_sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest(),
    unpacked_bytes_match=True,status='candidate_behavior_trials_in_progress',behavioral_acceptance=False)
(OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
