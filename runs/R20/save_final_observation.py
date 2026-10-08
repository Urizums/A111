"""Append terminal CI evidence; retain the earlier handback observation."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl

with ctl.locked(ROOT):
    receipt = json.loads((ROOT / 'runs/R20/source-ci-observation-2-command.json').read_text(encoding='utf-8'))
    assert receipt['state'] == 'finished' and receipt['exit_code'] == 0
    ci = json.loads(receipt['stdout'])
    assert ci['headSha'] == 'ca282442b11d63cf14d4fe8128c8cb552581e040'
    assert ci['status'] == 'completed' and ci['conclusion'] == 'success'
    assert len(ci['jobs']) == 3 and all(job['conclusion'] == 'success' for job in ci['jobs'])
    state = ctl.load(ROOT)
    assert state['execution']['current_frontier_task'] == 'R20-01'
    assert not state['execution']['current_native_pending']
    previous = json.loads((ROOT / 'runs/R20/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in previous.items())
    state['execution']['final_source_ci_observation'] = ci
    state['events'].append(dict(at=ctl.stamp(), command='R20_terminal_source_ci_observation',
        evidence='runs/R20/source-ci-observation-2-command.json'))
    ctl.write_json(ROOT / 'state/continuation.json', state)
    ctl.synchronize(ROOT, state)
    cp_path = ROOT / 'state/checkpoint.json'
    cp = json.loads(cp_path.read_text(encoding='utf-8'))
    cp['final_source_ci_observation'] = ci
    cp['terminal_source_ci_receipt'] = 'runs/R20/source-ci-observation-2-command.json'
    ctl.write_json(cp_path, cp)
    assert not ctl.validate(state, ROOT)
print(json.dumps(dict(source_ci='completed/success', jobs=3, previous_tasks_preserved=60,
    frontier='R20-01', historical_handback_unchanged=True)))
