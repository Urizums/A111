"""Record the actual informed-review interruption and same-actor resumption."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl
with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    old = json.loads((ROOT / 'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
    relative = 'runs/R19/levels/L2/resource-recheck-interruption-1.json'
    assert not (ROOT / relative).exists()
    ctl.write_json(ROOT / relative, dict(
        observed_at=ctl.stamp(), provenance='Actual parent collaboration error, account tool response and list_agents; not complete provider telemetry.',
        actor='/root/r19_l2_reviewer', original_error='Agent errored: usage limit; try again at 4:18 AM. Original hint timezone unknown.',
        ordinaryUsageAllowed=True, primaryUsedPercent=0, secondaryUsedPercent=47, rateLimitReachedType=None,
        same_actor_followup_dispatched=True, actual_parent_observed_status='running',
        known_command_terminal='review/recheck-1/zip_full_raw.receipt.json: exit0, 119.81420939999953 seconds, UTC finish 2026-10-07T17:37:07.251360+00:00',
        process_reconciliation='Requested same actor to inspect actual pending calls/processes before any new invocation; not yet reported.',
        purchased_credits=False, consumed_reset_credit=False, model_switched=False, tasks_or_budgets_reset=False,
        actual_model=None, tokens=None, cost=None,
        inference_limit='Account ordinary usage availability does not itself prove actor capability or a scientific review verdict.'))
    state['events'].append(dict(at=ctl.stamp(), command='resume_same_L2_informed_reviewer_after_actual_usage_observation', evidence=relative))
    state['execution']['R19_resource_observation'] = relative
    ctl.write_json(ROOT / 'state/continuation.json', state)
    ctl.synchronize(ROOT, state)
print(json.dumps(dict(old_tasks_unchanged=len(old), evidence=relative)))
