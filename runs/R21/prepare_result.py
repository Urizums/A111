"""Verify the actual preparation; no private demand values are read."""
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R21'
def read(rel):
    return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def save(name,obj):
    with (BASE/name).open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')
for rel in ['runs/R21/protocol-lock.json','runs/R21/input-lock.json','runs/R21/evaluation-lock.json']:
    for row in read(rel)['files']:
        b=(ROOT/row['path']).read_bytes()
        assert len(b)==row['size_bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
generation=read('runs/R21/data-generation-after-freeze-command.json')
assert generation['state']=='finished' and generation['exit_code']==0
assert datetime.fromisoformat(read('runs/R21/protocol-lock.json')['frozen_at'])<datetime.fromisoformat(generation['begin']['utc'])
failure=read('runs/R21/data-generation-command.json')
assert failure['state']=='finished' and failure['exit_code']==1 and 'protocol-lock.json' in failure['stderr']
original={r['path']:r for r in read('runs/R20/execution-lock.json')['files']}
copies=[('runs/R21/inputs/reference/run.py','runs/R20/execution/code/run.py'),
    ('runs/R21/inputs/reference/experiment.json','runs/R20/execution/config/experiment.json')]
for new,old in copies:
    b=(ROOT/new).read_bytes(); r=original[old]
    assert len(b)==r['size_bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
with (BASE/'inputs/raw/calendar.csv').open(encoding='utf-8',newline='') as f:
    future=[r for r in csv.DictReader(f) if r['service_date']>='2026-11-01']
assert len(future)==42
groups=[]
for band in range(6):
    rows=future[band*7:(band+1)*7]
    activity=sum(int(r['holiday']) for r in rows)
    assert activity==2
    groups.append(dict(horizon_band=f'{band*7+1}-{band*7+7}',dates=7,activity_dates=activity,ordinary_dates=7-activity))
with (BASE/'inputs/raw/demand_reports.csv').open(encoding='utf-8',newline='') as f:
    reports=list(csv.DictReader(f))
assert len(reports)==21609 and max(r['service_date'] for r in reports)=='2026-10-31'
assert not (BASE/'design').exists() and not (BASE/'execution').exists()
summary=dict(protocol_frozen_before_realized_generation=True,realized_samples=1,initial_generator_invocation='failed before generation: freeze command had not yet completed',
    recovery='Waited for exact original native/WSL sessions to finish; same fixed seed and code then generated once; original exit1 retained.',
    public_files=12,future_rows=4032,future_dates=42,groups=groups,current_policy_source_copies_byte_exact=True,
    private_truth='Hashed for frozen identity only; semantic contents not read or used for choosing model.',
    author_started=False,independent_acceptance=False,zero_improvement_allowed=True,model=None,tokens=None,cost=None)
save('preparation-summary.json',summary)
state=read('state/continuation.json'); task=next(t for t in state['tasks'] if t['id']=='R21-02'); attempt=task['attempts'][-1]
save('R21-02-result.json',dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
    criteria=[dict(id='t1',status='pass',evidence=['runs/R21/protocol-lock.json','runs/R21/input-lock.json',
        'runs/R21/evaluation-lock.json','runs/R21/data-generation-after-freeze-command.json','runs/R21/preparation-summary.json'])],
    effect=dict(target=task['title'],hypothesis='Prospective measurement with activity distributed across horizons resolves old complete overlap without promising better models.',
        baseline='Frozen R20 current-policy algorithm refitted on new history; old results retained.',
        conditions='One original synthetic sample, source/time-bound fairness, before production; future truth held in private evaluation domain.',
        observations=summary,limits='Preparation only; not independent scientific acceptance, future performance, causal skill superiority, formal compliance or prize.',
        metrics=dict(model=None,tokens=None,cost=None)),next_action='R21-03: fresh C13 workflow builder, different executor, independent receiver; freeze first production before truth.'))
print(json.dumps(summary,ensure_ascii=False))
