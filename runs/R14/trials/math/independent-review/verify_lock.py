import hashlib,json
from pathlib import Path
lock=json.loads(Path('runs/R14/math-output-lock.json').read_text(encoding='utf-8'))
entries=lock.get('files',[])
check=[]
for e in entries:
 p=Path(e['path'])
 if not str(p).replace('\\','/').startswith('runs/R14/trials/math/L'):
  continue
 nbytes=p.stat().st_size if p.is_file() else None
 digest=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
 check.append({'path':str(p).replace('\\','/'),'exists':p.is_file(),'size_matches':nbytes==e.get('size_bytes'),'sha256_matches':digest==e.get('sha256'),'observed_size_bytes':nbytes,'observed_sha256':digest})
result={'schema':'independent-locked-output-check/1','lock_file':'runs/R14/math-output-lock.json','checked_files':len(check),'all_match':all(x['exists'] and x['size_matches'] and x['sha256_matches'] for x in check),'files':check}
out=Path('runs/R14/trials/math/independent-review/lock-audit.json')
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checked_files':len(check),'all_match':result['all_match'],'mismatches':[x for x in check if not(x['exists'] and x['size_matches'] and x['sha256_matches'])]},ensure_ascii=False))
