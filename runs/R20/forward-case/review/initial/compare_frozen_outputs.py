import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--frozen',type=Path,required=True);p.add_argument('--rerun',type=Path,required=True);a=p.parse_args()
expected={'results.json','coordinates.csv','days.csv','vectors.csv','selection-events.csv','说明.md'}
def hashes(d): return {x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in d.iterdir() if x.is_file()}
f,r=hashes(a.frozen),hashes(a.rerun)
print(json.dumps({'frozen_files':f,'rerun_files':r,'same_names':set(f)==set(r)==expected,'byte_identical':f==r},ensure_ascii=False,indent=2))
if set(f)!=expected or set(r)!=expected or f!=r: raise SystemExit(1)
