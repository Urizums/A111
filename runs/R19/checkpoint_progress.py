"""Root-only snapshot of actually observed trial progress, with old task guard."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
p=argparse.ArgumentParser();p.add_argument('--level',type=int,choices=range(1,5),required=True)
p.add_argument('--stage',required=True);p.add_argument('--next-action',required=True)
a=p.parse_args()
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    old=json.loads((ROOT/'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items())
    state['execution'].update(current_frontier_task=f'R19-L{a.level}',current_paper_level=a.level,
        current_report='runs/R19/REPORT.md',current_task_process_state=a.stage)
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
    cp.update(current_report='runs/R19/REPORT.md',current_frontier_task=f'R19-L{a.level}',
        R19_status=a.stage,current_validation=a.stage,next_action=a.next_action,termination=None,
        current_native_pending=state['execution']['current_native_pending'],unpublished_work=True)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(paper_level=a.level,stage=a.stage,old_tasks_unchanged=len(old))))
