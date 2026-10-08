"""Persist observed recovery and user steering; never reset historical tasks."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl

with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    old = json.loads((ROOT / 'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[key]) == value for key, value in old.items())
    path = 'runs/R19/levels/L3/resource-language-resumption-1.json'
    assert not (ROOT / path).exists(), 'one-time observation already recorded'
    observation = dict(
        observed_at=ctl.stamp(), actor='/root/r19_l3_executor',
        earlier_interruption=dict(state='errored_usage_limit', reset_label='12:40 PM',
            timezone=None, provenance='Previous parent notification retained in continuation context.'),
        earlier_account_read=dict(tool='mcp__codex_app__get_usage_limits',
            outcome='no_result_cell_1_terminated', remaining_percent=None, allowed=None),
        recovery=dict(tool='collaboration.followup_task', target='/root/r19_l3_executor',
            outcome='same_actor_running_observed',
            corroboration='Unfiltered list_agents returned original actor running; original actor confirmed recoverable and no execution-v2 or pending self-started process before new work.',
            model_changed=False, credits_purchased=False, budgets_reset=False),
        lease=dict(previous_session=30116, previous_session_observation='Unknown process id',
            actual_probe_busy=False, new_session=85253, new_pid=402,
            new_owner='root-codex-r19-l3-language-resume', acquired_at='2026-10-08T05:00:45.085817+00:00'),
        user_steering='Chinese scientific expression and argument quality are important current deliverables even if later AI polishing is planned.',
        acceptance_scope='Existing frozen a5 and scientific-expression dimension; no new retroactive criterion or C11 edit.',
        actual_model=None, tokens=None, cost=None)
    ctl.write_json(ROOT / path, observation)
    rows = [row for row in state['execution'].get('current_native_pending', [])
            if row['worker'] != '/root/r19_l3_executor']
    state['execution'].setdefault('completed_native_R19', []).append(dict(
        worker='/root/r19_l3_executor', state='errored_usage_limit', evidence=path, actual_model=None))
    rows.append(dict(worker='/root/r19_l3_executor', state='running_observed_same_actor_informed_repair',
        evidence=path, actual_model=None))
    stage = 'L3_first_review_4pass_a5fail_a6partial_same_actor_language_repair_running'
    state['execution'].update(current_native_pending=rows, native_pending_current=rows,
        current_frontier_task='R19-L3', current_paper_level=3, R19_current_level=3,
        current_task_process_state=stage, current_user_language_steering=path,
        R19_resource_observation=path, current_coordinator='root-codex-r19-l3-language-resume',
        R19_unpublished_followups=True)
    state['events'].append(dict(at=ctl.stamp(), command='observed_same_actor_language_resume', evidence=path))
    ctl.write_json(ROOT / 'state/continuation.json', state)
    ctl.synchronize(ROOT, state)
    cp = json.loads((ROOT / 'state/checkpoint.json').read_text(encoding='utf-8'))
    cp.update(current_native_pending=rows, R19_status=stage, current_validation=stage,
        current_frontier_task='R19-L3', current_user_language_steering=path,
        next_action='Collect same L3 author scientific-notation and Chinese-language repair; freeze actual terminal output, then same independent reviewer informed recheck. Preserve first 4pass/1fail/1partial and unrecoverable history; L4 paper waits.',
        termination=None, unpublished_work=True)
    ctl.write_json(ROOT / 'state/checkpoint.json', cp)
print(json.dumps(dict(old_tasks_unchanged=len(old), current_actor='/root/r19_l3_executor',
    status=stage, evidence=path)))
