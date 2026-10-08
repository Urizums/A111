import json
from pathlib import Path
root=Path('runs/R20/review/initial')
commands=sorted(p for p in root.glob('command-*.json') if p.name not in {'command-final-status.json','command-final-status-retry.json'})
rows=[]
for p in commands:
 d=json.loads(p.read_text(encoding='utf-8-sig'))
 rows.append({'record':p.name,'state':d.get('state'),'exit_code':d.get('exit_code'),'begin_utc':(d.get('begin') or {}).get('utc'),'end_utc':(d.get('end') or {}).get('utc')})
print(json.dumps({'command_records_checked':len(rows),'all_checked_commands_terminal':all(r['state']=='finished' for r in rows),'records':rows},ensure_ascii=False,indent=2))
