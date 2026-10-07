"""Observe the authorized main publication and its exact CI run; no quality inference."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import continuation as ctl
p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--gh',default='gh');a=p.parse_args()
def command(args):return subprocess.check_output(args,cwd=ROOT,text=True,encoding='utf-8').strip()
remote=command(['git','ls-remote','origin','refs/heads/main']).split()[0]
assert remote==a.commit,'Remote main differs; do not claim this source is the current remote head.'
runs=json.loads(command([a.gh,'run','list','--repo','Urizums/A111','--commit',a.commit,'--limit','3','--json','databaseId,status,conclusion,url,headSha,workflowName']))
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    old=json.loads((ROOT/'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k])==v for k,v in old.items())
    serial=1
    while (ROOT/f'runs/R19/publication/observation-{serial}.json').exists():serial+=1
    evidence=f'runs/R19/publication/observation-{serial}.json'
    ctl.write_json(ROOT/evidence,dict(observed_at=ctl.stamp(),source_commit=a.commit,remote_main=remote,
        commit_url=f'https://github.com/Urizums/A111/commit/{a.commit}',ci=runs,
        scope='Source/artifact checks only; independent paper verdict still separate.'))
    state['execution'].update(current_source_commit=a.commit,current_source_ci=runs,
        current_source_ci_observed=ctl.stamp(),current_publication=evidence,R19_publication_status='source_pushed_observed')
    state['events'].append(dict(at=ctl.stamp(),command='observe_R19_main_publication',evidence=evidence))
    ctl.write_json(ROOT/'state/continuation.json',state);ctl.synchronize(ROOT,state)
    cp=json.loads((ROOT/'state/checkpoint.json').read_text(encoding='utf-8'))
    cp.update(current_report='runs/R19/REPORT.md',publication_evidence=evidence,current_source_commit=a.commit,
        current_source_ci=runs)
    # Publishing a snapshot does not change the actual trial frontier or next action.
    ctl.write_json(ROOT/'state/checkpoint.json',cp)
print(json.dumps(dict(remote_main=remote,ci=runs,evidence=evidence)))
