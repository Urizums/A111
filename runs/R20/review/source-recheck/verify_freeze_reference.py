import hashlib,json
from pathlib import Path
p=Path('runs/R20/coordination/production-freeze-command.json')
b=p.read_bytes(); d=json.loads(b)
wrong=Path('runs/R20/execution/evidence/production-freeze-command.json')
print(json.dumps({'mistaken_path_in_initial_first_result':'runs/R20/execution/evidence/production-freeze-command.json','mistaken_path_exists':wrong.exists(),'correct_path':p.as_posix(),'correct_bytes':len(b),'correct_sha256':hashlib.sha256(b).hexdigest(),'state':d['state'],'exit_code':d['exit_code'],'begin_utc':d['begin']['utc'],'end_utc':d['end']['utc'],'argv':d['argv'],'stdout':d['stdout'],'execution_lock_target':'runs/R20/execution-lock.json','result':'The initial first-result path field was wrong; the freeze receipt itself is valid finished/0. This is a provenance-reference correction only.'},ensure_ascii=False,indent=2))
