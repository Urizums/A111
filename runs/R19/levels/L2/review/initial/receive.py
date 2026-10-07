from pathlib import Path
import json,hashlib,datetime,collections
b=Path.cwd();o=b/'runs/R19/levels/L2/review/initial';records=[]
for lp in ['runs/R19/levels/L2/review/preparation-lock.json','runs/R19/levels/L2/execution-lock.json']:
 d=json.loads((b/lp).read_text(encoding='utf-8-sig'));checks=[]
 for f in d['files']:
  p=b/f['path'];raw=p.read_bytes();checks.append({'path':f['path'],'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'matches':len(raw)==f.get('size_bytes',len(raw)) and hashlib.sha256(raw).hexdigest()==f['sha256']})
 records.append({'lock':lp,'lock_sha256':hashlib.sha256((b/lp).read_bytes()).hexdigest(),'frozen_at':d.get('frozen_at'),'count':len(checks),'all_match':all(c['matches'] for c in checks),'checks':checks})
files=[p for p in (b/'runs/R19/levels/L2/execution').rglob('*') if p.is_file()]
inv=collections.Counter(str(p.relative_to(b/'runs/R19/levels/L2/execution')).split('\\')[0] for p in files)
(o/'received-locks.json').write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':records,'inventory':dict(inv),'count':len(files)},ensure_ascii=False,indent=2),encoding='utf-8')
(o/'execution-inventory.txt').write_text('\n'.join(str(p.relative_to(b)) for p in files),encoding='utf-8')
print(json.dumps({'locks':[{k:v for k,v in x.items() if k!='checks'} for x in records],'inventory':dict(inv),'count':len(files)},ensure_ascii=False,indent=2))
