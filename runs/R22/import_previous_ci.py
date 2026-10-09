"""Append the already completed actual CLI observation, without inventing a query."""
import base64
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
receipt='runs/R22/resume-ci-command.json'
r=json.loads((ROOT/receipt).read_text(encoding='utf-8'))
assert r['state']=='finished' and r['exit_code']==0
assert r['argv'][1:4]==['run','view','37884838207']
assert base64.b64decode(r['stdout_base64']).decode('utf-8',errors='replace')==r['stdout']
ci=json.loads(r['stdout']); commit=ci['headSha']
assert commit=='eb8d217a4e6eb8d6f815f2735e6a38a60e9c4467'
assert ci['status']=='completed' and ci['conclusion']=='success'
assert len(ci['jobs'])==3 and all(j['status']=='completed' and j['conclusion']=='success' for j in ci['jobs'])
with ctl.locked(ROOT):
    state=ctl.load(ROOT); cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
    serial=1
    while (ROOT/f'runs/R19/publication/observation-{serial}.json').exists():serial+=1
    evidence=f'runs/R19/publication/observation-{serial}.json'
    observation=dict(recorded_at=ctl.stamp(),observed_at=r['end']['utc'],source_commit=commit,
        commit_url=f'https://github.com/Urizums/A111/commit/{commit}',ci=[ci],actual_query=ctl.ref(ROOT,receipt),
        scope='Completed previous-commit CLI query retained verbatim; no new remote-head or new-work CI assertion.',
        later_query_failure='runs/R22/previous-ci-terminal-observation-command.json')
    ctl.write_json(ROOT/evidence,observation)
    state['execution'].update(current_source_commit=commit,current_source_ci=[ci],
        current_source_ci_observed=r['end']['utc'],current_publication=evidence)
    state['events'].append(dict(at=ctl.stamp(),command='import_actual_completed_CI_receipt',evidence=evidence))
    assert not ctl.validate(state,ROOT)
    ctl.write_json(ROOT/'state/continuation.json',state)
    cp.update(current_source_commit=commit,current_source_ci=[ci],publication_evidence=evidence)
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(evidence=evidence,previous_source_commit=commit,ci='completed/success',new_work_ci=None)))
