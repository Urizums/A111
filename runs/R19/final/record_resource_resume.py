"""Preserve actual host interruption/resume observations without account identifiers."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl

with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    old = json.loads((ROOT / 'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
    path = ROOT / 'runs/R19/final/resource-resume-observation-1.json'
    assert not path.exists()
    ctl.write_json(path, dict(observed_at=ctl.stamp(),
        interrupted_actor='/root/r19_c12_producer',
        interruption='Actual collaboration final: usage limit; producer not terminal-delivered.',
        current_host=dict(ordinaryUsageAllowed=True, primary_used_percent=0,
                          secondary_used_percent=95, spendControlReached=False),
        resumed='Actual followup_task to the same original producer; keep identity, inputs and pending-call reconciliation.',
        provenance='Actual parent tool return/status transcribed; not provider per-call authenticated telemetry.',
        reset_credit_used=False, purchase=False, actor_or_model_replaced=False,
        old_failure_or_budget_reset=False, current_forward_verdict='not_yet_reviewed',
        model=None, tokens=None, cost=None))
    state['events'].append(dict(at=ctl.stamp(), command='C12_same_actor_resource_resume',
        evidence=path.relative_to(ROOT).as_posix()))
    ctl.write_json(ROOT / 'state/continuation.json', state)
    ctl.synchronize(ROOT, state)
print(json.dumps(dict(actual_resource_event_preserved=True, old_tasks_unchanged=len(old))))
