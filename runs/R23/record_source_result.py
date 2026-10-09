"""Bind actual frozen source adjudication to original R23-04 acceptance."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
s=read('state/continuation.json');task=next(t for t in s['tasks'] if t['id']=='R23-04');a=task['attempts'][-1];assert a['status']=='in_progress'
lock=read('runs/R23/final-lock.json')
for row in lock['files']:
    b=(ROOT/row['path']).read_bytes();assert len(b)==row['size_bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
d=read('runs/R23/final/source-decision.json');assert d['decision']=='retain_C13' and d['new_candidate'] is None and d['source_files']==9
result=dict(task_id=task['id'],attempt_id=a['id'],requirements_hash=a['requirements_hash'],criteria=[dict(id='t1',status='pass',evidence=['runs/R23/final-lock.json','runs/R23/final/SYNTHESIS.md','runs/R23/final/source-decision.json','runs/R23/final/source-basis.json','runs/R23/clean-reception-lock.json','runs/R23/initial-reception-composition.json'])],
    effect=dict(target=task['title'],hypothesis='Actual defects can be traced to absent source principles or failure to apply existing obligations, avoiding redundant source revisions.',baseline='Frozen C13 nine pure Markdown; same known raw data.',conditions='Original first failed attempt and root strict-withholding gap retained; informed design correction and fresh narrow-packet receiving complete.',observations='Per-method contract omission and receipt-argument diagnosis exposure violate existing source obligations. Root retains C13, keeps repaired workflow and receiving packet in R&D, and explicitly closes the bounded probe.',metrics=dict(source_files=9,new_candidates=0,informed_task_restarts=1,actual_model=None,tokens=None,cost=None),limits='Source sufficiency judgment is bounded, not a guarantee/causal skill improvement; no full42-day current production/paper, award or formalOctober claim.'),next_action='R23-next: cancel successor on verified bounded-goal completion; preserve all other unfinished branches.')
with (ROOT/'runs/R23/R23-04-result.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(task='R23-04',source='retain_C13',new_candidate=None,bounded_probe_complete=True)))
