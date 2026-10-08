import json
from pathlib import Path
root=Path('runs/R20/review/source-recheck')
exclude={'command-final-status.json'}
rows=[]
for p in sorted(root.glob('command-*.json')):
 if p.name in exclude: continue
 d=json.loads(p.read_text(encoding='utf-8-sig'))
 rows.append({'record':p.name,'state':d.get('state'),'exit_code':d.get('exit_code'),'begin_utc':(d.get('begin') or {}).get('utc'),'end_utc':(d.get('end') or {}).get('utc')})
assert len(rows)==3 and all(x['state']=='finished' for x in rows),rows
print(json.dumps({'checked_commands':len(rows),'all_terminal':True,'records':rows},ensure_ascii=False,indent=2))
