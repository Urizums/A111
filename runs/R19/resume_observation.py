"""Preserve the actual interrupted actor observations and current resource query."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl
with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    before = json.loads((ROOT/'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k,v in before.items())
    evidence = 'runs/R19/resource-interruption-and-resume.json'
    ctl.write_json(ROOT/evidence, dict(
        observed_at=ctl.stamp(), provenance='Parent collaboration error notifications, account usage query, followup returns and subsequent list_agents snapshot; not raw provider telemetry.',
        interrupted_actors=['/root/r19_l1_executor','/root/r19_l1_reviewer','/root/r19_l4_builder'],
        error='You have hit your usage limit; original notifications suggested trying again at 4:50 PM. No timezone inferred.',
        current_usage_query=dict(ordinaryUsageAllowed=True,primaryUsedPercent=1,secondaryUsedPercent=16,rateLimitReachedType=None),
        resume_observation='Same three actors received a continuation message and list_agents reported all three running. No model switch, replacement actor or task/budget reset.',
        actual_model=None,tokens=None,cost=None))
    state['events'].append(dict(at=ctl.stamp(),command='resume_same_R19_actors_after_observed_resource_availability',evidence=evidence))
    state['execution']['R19_resource_observation']=evidence
    ctl.write_json(ROOT/'state/continuation.json',state)
    ctl.synchronize(ROOT,state)
print(json.dumps(dict(old_tasks_unchanged=len(before),resource_observation=evidence)))
