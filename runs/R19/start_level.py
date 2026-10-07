"""Root-only serial start, anchored by actual neutral input inspection receipt."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
level=int(sys.argv[1])
design=len(sys.argv)>2 and sys.argv[2]=='design'
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    task=ctl.task_map(state)[f"R19-{'D' if design else 'L'}{level}"]
    assert task['status']=='planned' and not task['attempts']
    assert all(ctl.task_map(state)[d]['status']=='done' for d in task['depends_on'])
    ctl.begin(state,ROOT,task['id'],f"runs/R19/levels/L{level}/{'design-' if design else ''}input-inspection-command.json")
    state['execution']['R19_current_level']=level
    state['events'].append(dict(at=ctl.stamp(),command='start_level',level=level))
    ctl.write_json(ROOT/'state/continuation.json',state)
    ctl.synchronize(ROOT,state)
print(json.dumps(dict(task=task['id'],status=task['status'],repairs_used=task['repairs_used'])))
