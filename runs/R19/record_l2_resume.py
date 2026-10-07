"""Preserve the second real resource interruption without replacing the first."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    old=json.loads((ROOT/'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items())
    path=ROOT/'runs/R19/levels/L2/resource-resume-observation.json'
    assert not path.exists()
    ctl.write_json(path,dict(observed_at=ctl.stamp(),provenance='Parent tool outputs and actor reports, not full provider telemetry.',
        original_executor_error='Agent errored: usage limit; suggested try again at 10:28 PM; original timezone unverified.',
        reviewer_interruption='No parent terminal error received; same actor resumed to reconcile unfinished preparation.',
        usage_query=dict(ordinaryUsageAllowed=True,primaryUsedPercent=0,secondaryUsedPercent=32,rateLimitReachedType=None),
        same_actors_resumed=['/root/r19_l2_executor','/root/r19_l2_reviewer'],model_switched=False,tasks_or_budgets_reset=False,
        executor_report='Old sessions unknown, no matching solver process; 13/32 parameter cases complete. Resume only unfinished cases, reported session56913. Full paper not yet delivered.',
        reviewer_report='Existing source controls/scripts terminal; no matching Python process. Plans/result incomplete; no execution access.',
        lease=dict(old_probe_busy=False,old_explicit_release_unobserved=True,new_owner='root-codex-r19-levels-resume-l2',pid=398,session=30116,acquired_at='2026-10-07T15:19:20.726160+00:00'),
        actual_model=None,tokens=None,cost=None))
    state['events'].append(dict(at=ctl.stamp(),command='reconcile_and_resume_same_L2_actors',evidence=path.relative_to(ROOT).as_posix()))
    state['execution']['R19_resource_observation']=path.relative_to(ROOT).as_posix()
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
print(json.dumps(dict(old_tasks_unchanged=len(old),same_actors=True,resource_observation=path.relative_to(ROOT).as_posix())))
