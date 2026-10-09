import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
def check_lock(lock_path, allowed=None):
    lock=json.loads((ROOT/lock_path).read_text(encoding='utf-8'))
    checked=[]
    for e in lock['files']:
        rel=e['path']
        if allowed is not None and not allowed(rel): continue
        b=(ROOT/rel).read_bytes()
        h=hashlib.sha256(b).hexdigest()
        if len(b)!=e['size_bytes'] or h!=e['sha256']:
            raise SystemExit(f'LOCK MISMATCH {rel}')
        checked.append(rel)
    return lock,checked
inp,ins=check_lock('runs/R20/forward-case/input-lock.json')
eval_lock,evs=check_lock('runs/R20/forward-case/evaluation-lock.json')
prep,preps=check_lock('runs/R20/forward-case/review/preparation-lock.json')
prod,prods=check_lock('runs/R20/forward-case/production-lock.json',lambda p:p.startswith(('runs/R20/forward-case/production/calibration-flow/','runs/R20/forward-case/production/code/','runs/R20/forward-case/production/results/')))
assert len(prod['files'])==71, f"production lock inventory changed: {len(prod['files'])}"
print(json.dumps({'input_lock_files_verified':len(ins),'evaluation_lock_files_verified':len(evs),'preparation_lock_files_verified':len(preps),'production_lock_inventory':len(prod['files']),'allowed_production_files_verified':len(prods),'verified_production_paths':prods},ensure_ascii=False,indent=2))
