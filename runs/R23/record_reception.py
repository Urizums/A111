"""Record actual receiving result with its original task/attempt requirements."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--verdict',required=True);p.add_argument('--lock',required=True);p.add_argument('--out',required=True);p.add_argument('--composition');a=p.parse_args()
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
state=read('state/continuation.json');task=next(t for t in state['tasks'] if t['id']=='R23-03');attempt=task['attempts'][-1]
assert attempt['status']=='in_progress'
lock=read(a.lock)
for row in lock['files']:
    b=(ROOT/row['path']).read_bytes();assert len(b)==row['size_bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
v=read(a.verdict);assert set(v['criteria'])=={'j1','j2','j3','j4'}
statuses={k:r['status'] for k,r in v['criteria'].items()};evidence=[a.verdict,a.lock,'runs/R23/execution-lock.json','runs/R23/execution/v2/consumer-point-slice.csv','runs/R23/execution/receipts/r23-consumer-30-compute-v2-final.txt']
if a.composition:
    composition=read(a.composition);statuses.update(composition['coordinator_received_statuses']);evidence.append(a.composition)
assert set(statuses)=={'j1','j2','j3','j4'} and all(x in ['pass','fail','unverified'] for x in statuses.values())
outcome='pass' if all(x=='pass' for x in statuses.values()) else 'fail'
result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],criteria=[dict(id='t1',status=outcome,evidence=evidence)],
    effect=dict(target=task['title'],hypothesis='A different consumer can operate a meaningful proposed slice and a fresh receiver can check design/source/interfaces/scope without author diagnosis.',baseline='Same known synthetic raw inputs; no causal or new blind scientific comparison.',conditions='Original frozen j1-j4; actual terminal consumer and versioned raw-source reception; packet provenance separately audited.',observations='Actual criterion statuses: '+json.dumps(statuses)+'. Original scientific and failed process records remain unchanged.',metrics=dict(criteria=statuses,consumer_methods=2,consumer_point_rows=192,consumer_days=1,actual_model=None,tokens=None,cost=None),limits='One historical date point forecasts only; no interval, optimization,42-day production/paper,reliability,award or source causal-gain claim.'),
    next_action='R23-04: source-bound synthesis and bounded closure.' if outcome=='pass' else 'Repair the original source-bound design/receiving-packet defects prospectively; preserve this failed verdict and attempt.')
with (ROOT/a.out).open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(task=task['id'],attempt=attempt['id'],result=outcome,criteria=statuses)))
