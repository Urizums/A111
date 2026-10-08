from pathlib import Path
import hashlib,json,datetime
B=Path.cwd();O=B/'runs/R19/levels/L2/review/recheck-1';O.mkdir(parents=True,exist_ok=True)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for name in ('execution-lock.json','execution-v2-lock.json'):
 p=B/'runs/R19/levels/L2'/name;l=json.loads(p.read_text(encoding='utf-8'));rows=[]
 for f in l['files']:
  q=B/f['path'];rows.append({**f,'matches':q.is_file() and q.stat().st_size==f['size_bytes'] and h(q)==f['sha256']})
 records.append({'lock':p.relative_to(B).as_posix(),'sha256':h(p),'count':len(rows),'all_match':all(x['matches'] for x in rows),'files':rows})
assert all(x['all_match'] for x in records)
old={x['path'].split('/execution/')[1]:x for x in records[0]['files']}
diff=[]
for x in records[1]['files']:
 rel=x['path'].split('/execution-v2/')[1]; y=old.get(rel);diff.append({'path':rel,'state':'added' if y is None else 'unchanged' if y['sha256']==x['sha256'] else 'changed','sha256':x['sha256']})
(O/'received-locks.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'informed_re_review':True,'records':records},ensure_ascii=False,indent=2),encoding='utf-8')
(O/'changed-inventory.json').write_text(json.dumps(diff,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'counts':[(r['count'],r['all_match']) for r in records],'states':{s:sum(x['state']==s for x in diff) for s in ('added','changed','unchanged')},'changed_core':[x['path'] for x in diff if x['state']!='unchanged' and (x['path'].startswith(('code/','paper/','research/')) or '/' not in x['path'])]},ensure_ascii=False))
