"""Keep the original mandatory rejection under its actual task/attempt identity."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R22'
state=json.loads((ROOT/'state/continuation.json').read_text(encoding='utf-8'))
task=next(t for t in state['tasks'] if t['id']=='R22-02');attempt=task['attempts'][-1]
review=json.loads((BASE/'review/initial/result.json').read_text(encoding='utf-8'))
assert review['criterion_statuses']==dict(h1='pass',h2='pass',h3='pass',h4='pass',h5='pass',h6='fail')
result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
    criteria=[dict(id='t1',status='fail',evidence=['runs/R22/execution-lock.json','runs/R22/initial-reception-lock.json',
        'runs/R22/review/initial/result.json','runs/R22/review/initial/REVIEW.md','runs/R22/root-metrics-command.json'])],
    effect=dict(target=task['title'],hypothesis='Full independent numerical reception can still reject inconsistent displayed paper values.',
        baseline='Frozen R/W policy under the same fixed42-day protocol.',conditions='First complete production and independent reception, known historical data.',
        observations=review['criterion_statuses'],metrics=dict(scored_keys=24192,pdf_pages=13,actual_model=None,tokens=None,cost=None),
        limits='h1-h5 pass, mandatory h6 fails; not full delivery acceptance. Original first failure preserved.'),
    next_action='Same R22-02: new document-only ROUND_HALF_UP renderer and informed full MD/PDF recheck; original science and first rejection unchanged.')
with (BASE/'R22-02-first-result.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(task_id=task['id'],attempt=attempt['id'],verdict='fail',failed='h6',science_source_change=False)))
