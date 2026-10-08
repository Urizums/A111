import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
a=ROOT/'runs/R20/execution/delivery'; b=ROOT/'runs/R20/review/initial/rerun'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[]
for p in sorted(a.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(a); q=b/rel
 files.append({'path':str(rel).replace('\\','/'),'delivery_sha256':sha(p),'rerun_exists':q.exists(),'rerun_sha256':sha(q) if q.exists() else None,'same_bytes':q.exists() and sha(p)==sha(q),'delivery_bytes':p.stat().st_size,'rerun_bytes':q.stat().st_size if q.exists() else None})
extra=[str(p.relative_to(b)).replace('\\','/') for p in b.rglob('*') if p.is_file() and not (a/p.relative_to(b)).exists()]
out={'delivery_file_count':len(files),'rerun_file_count':sum(1 for p in b.rglob('*') if p.is_file()),'exact_same_bytes_count':sum(x['same_bytes'] for x in files),'different_or_missing':[x for x in files if not x['same_bytes']],'extra_rerun_files':extra,'scope':'byte comparison only; scientific numbers separately recomputed'}
print(json.dumps(out,ensure_ascii=False,indent=2))
