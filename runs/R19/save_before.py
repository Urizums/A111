"""Recover exact clean-start bytes from the unchanged recorded base commit."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'runs/R19/before'
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
assert commit=='135f8c7e2d3a6255847a466d83463a4a9559bb6c'
rows=json.loads((HERE/'history-lock.json').read_text(encoding='utf-8'))['files']
copies=[]
for row in rows:
    data=subprocess.check_output(['git','show',f"{commit}:{row['path']}"],cwd=ROOT)
    assert len(data)==row['size_bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
    saved=HERE/'base'/row['path']
    saved.parent.mkdir(parents=True,exist_ok=True)
    with saved.open('xb') as f:f.write(data)
    copies.append(dict(original_path=row['path'],saved_path=saved.relative_to(ROOT).as_posix(),sha256=row['sha256']))
(HERE/'saved-originals.json').write_text(json.dumps(dict(source_commit=commit,provenance='Git bytes matched original clean-start observed size/hash before saving; not reconstructed state.',files=copies),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(base_commit=commit,matched_saved_original_files=len(copies))))
