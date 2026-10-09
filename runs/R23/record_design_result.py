"""Record actual fresh design delivery, not later independent j1-j4 reception."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R23'
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
s=read('state/continuation.json');task=next(t for t in s['tasks'] if t['id']=='R23-02');a=task['attempts'][-1]
assert a['status']=='in_progress' and task['repairs_used']==0
lock=read('runs/R23/design-lock.json')
for row in lock['files']:
    b=(ROOT/row['path']).read_bytes();assert len(b)==row['size_bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
workflow=(BASE/'design/WORKFLOW.md').read_text(encoding='utf-8')
for token in ['Delivery contract','Roles and work boundaries','Ordered stages and branches','Shared artifact interfaces','Acceptance gates','4,032','42','independent']:assert token in workflow,token
status=read('runs/R23/design/COMPLETION-STATE.json');assert not status['production_complete'] and not status['paper_complete']
commands=[]
for p in sorted((BASE/'design/receipts').glob('*.json')):
    j=json.loads(p.read_text(encoding='utf-8'))
    if j.get('schema')!='forge-command-record/1':continue
    assert j['state']=='finished';commands.append(dict(path=p.relative_to(ROOT).as_posix(),exit_code=j['exit_code']))
assert len(commands)==25
result=dict(task_id=task['id'],attempt_id=a['id'],requirements_hash=a['requirements_hash'],
    criteria=[dict(id='t1',status='pass',evidence=['runs/R23/design-lock.json','runs/R23/design/WORKFLOW.md','runs/R23/design/READ-DOMAIN.md','runs/R23/design/COMPLETION-STATE.json','runs/R23/design/receipts/20261009_initial_authorized_read.json'])],
    effect=dict(target=task['title'],hypothesis='A fresh workflow designer can derive an operational workflow from C13, neutral business task and original sources, without coordinator experiment answers.',baseline='Same known original raw inputs; prior root detailed protocol and outcomes withheld.',conditions='Actual fresh-context design and one bounded author probe; source packet/reception criteria frozen beforehand.',
        observations='Workflow maps42-day fixed delivery, as-of information, model/uncertainty/optimization/comparison/paper responsibilities, artifacts/gates/branches. Author one-day96-key probe explicitly leaves full production, coverage and independent acceptance pending.',
        metrics=dict(designed_delivery_days=42,designed_delivery_keys=4032,author_probe_days=1,author_probe_keys=96,commands=len(commands),nonzero_commands=sum(c['exit_code']!=0 for c in commands),actual_model=None,tokens=None,cost=None),
        limits='Task is design delivery, not independent substantive j1-j4 judgment, consumer execution, full paper, new blind performance or causal source improvement.'),
    next_action='R23-03: a different fresh consumer operates a meaningful designed slice from raw sources; prepared independent receiver checks design/slice and actual scope.')
with (BASE/'R23-02-result.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(task=task['id'],artifact_delivered=True,independent_reception='pending',commands=25,nonzero=sum(c['exit_code']!=0 for c in commands))))
