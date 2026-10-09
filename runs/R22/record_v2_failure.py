"""Record actual author-rejected repair, without inventing an independent v2 verdict."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R22'
state=json.loads((ROOT/'state/continuation.json').read_text(encoding='utf-8'))
task=next(t for t in state['tasks'] if t['id']=='R22-02');attempt=task['attempts'][-1]
assert task['repairs_used']==1 and attempt['status']=='in_progress'
failed=json.loads((BASE/'execution/correction-v2/receipts/0006-full-document-selfcheck.json').read_text(encoding='utf-8'))
assert failed['state']=='finished' and failed['exit_code']==1
result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
    criteria=[dict(id='t1',status='fail',evidence=['runs/R22/document-correction-v2-lock.json','runs/R22/execution/correction-v2/receipts/0006-full-document-selfcheck.json','runs/R22/execution/correction-v2/derived-monetary-counterexamples.json','runs/R22/execution/correction-v2/ATTEMPT_STATUS.json','runs/R22/initial-reception-lock.json'])],
    effect=dict(target=task['title'],hypothesis='Declared decimal display must also use decimal arithmetic for derived monetary amounts.',baseline='v1 independent h6 rejection retained; v2 formatter-only repair.',conditions='Author full-document selfcheck of repaired paper; not independent v2 reception.',observations='Author selfcheck failed on float-first derived subtraction. No science rerun. Context-summary exposure disclosed.',metrics=dict(pdf_pages=13,repair_number=1,actual_model=None,tokens=None,cost=None),limits='Original h1-h5 and h6 failure retained; v2 has no independent verdict.'),
    next_action='Same original task: new renderer fixes decimal derived monetary arithmetic; preserve old reports, failures, budgets and criteria.')
with (BASE/'R22-02-v2-result.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(attempt=attempt['id'],verdict='fail',author_only=True)))
