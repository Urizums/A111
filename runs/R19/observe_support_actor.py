"""Record an actually observed supplemental actor without starting a paper level."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
p=argparse.ArgumentParser()
p.add_argument('--actor',required=True)
p.add_argument('--status',choices=['created','running_observed','completed'],required=True)
p.add_argument('--out',required=True)
p.add_argument('--write-boundary',required=True)
a=p.parse_args()
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    old=json.loads((ROOT/'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items())
    path=(ROOT/a.out).resolve()
    assert path.is_relative_to(ROOT) and not path.exists()
    observation=dict(actor=a.actor,state=a.status,observed_at=ctl.stamp(),
        write_boundary=a.write_boundary,provenance='Parent collaboration observation, not provider telemetry.',
        actual_model=None,tokens=None,cost=None)
    with path.open('x',encoding='utf-8') as f:
        json.dump(observation,f,ensure_ascii=False,indent=2);f.write('\n')
    rows=[r for r in state['execution']['current_native_pending'] if r['worker']!=a.actor]
    row=dict(worker=a.actor,state=a.status,evidence=a.out,actual_model=None)
    if a.status in {'created','running_observed'}:rows.append(row)
    else:state['execution'].setdefault('completed_native_R19',[]).append(row)
    state['execution'].update(current_native_pending=rows,native_pending_current=rows)
    state['events'].append(dict(at=ctl.stamp(),command='supplemental_actor_observation',actor=a.actor,status=a.status))
    ctl.write_json(ROOT/'state/continuation.json',state)
    cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
    cp.update(current_native_pending=rows,unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(actor=a.actor,state=a.status,pending=len(rows),old_tasks_unchanged=len(old))))
