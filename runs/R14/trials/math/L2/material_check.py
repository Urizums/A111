import hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parents[5]
lock=json.loads((root/'runs/R14/candidate/C9-lock.json').read_text(encoding='utf-8'))
checks=[]
for ent in lock['files']:
 p=root/ent['path']; b=p.read_bytes(); actual=hashlib.sha256(b).hexdigest()
 checks.append({'path':ent['path'],'exists':p.is_file(),'size_matches':len(b)==ent['size_bytes'],'sha256_matches':actual==ent['sha256']})
passed=all(x['exists'] and x['size_matches'] and x['sha256_matches'] for x in checks)
print(json.dumps({'revision':lock['revision'],'checks':checks,'all_pass':passed},indent=2))
if not passed: raise SystemExit(1)
