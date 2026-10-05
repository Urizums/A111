"""Coordinator-only result binding; continuation CLI performs state transitions."""
import json
from pathlib import Path
import hashlib
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[3]
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def write(name,value):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def result(task_id,evidence,observations,limits,metrics=None,status='pass'):
    t=next(t for t in read('state/continuation.json')['tasks'] if t['id']==task_id)
    a=t['attempts'][-1]
    return dict(task_id=task_id,attempt_id=a['id'],requirements_hash=a['requirements_hash'],criteria=[dict(id=c['id'],status=status,evidence=evidence) for c in t['acceptance']],effect=dict(target=t['title'],hypothesis='New scoped work can advance without changing historical acceptance or budgets',baseline='Preserved C6 and R07 evidence',conditions='Codex desktop on Windows; actual execution on Ubuntu WSL Python 3.12.3',observations=observations,limits=limits,metrics=metrics or {'tokens':None,'cost':None}),next_action=t['next_action'])
def main():
    write('runs/R08/R08-02-result.json', result('R08-02',['runs/R08/design/build-c7.json','runs/R08/design/change.json','runs/R08/candidate/C7-lock.json','runs/R08/candidate/C7/forge-agent-flow/SKILL.md','runs/R07/candidate/C6-lock.json'],['C7 entry routes one-time tasks directly; program and explicit reusable flows have distinct loading paths','Mandatory entry reduced from 17498 to 7139 bytes; all C6 executable files preserved','Independent checks, exact-byte handoff and bounded repairs remain conditional contracts'],['Byte reduction is structural, not a speed result','No installation promotion; inherited Linux restore limitation remains']))
    s=read('state/continuation.json');t=next(t for t in s['tasks'] if t['id']=='R08-03')
    assert t['status']=='planned' and not t['attempts']
    t['inputs'] += ['runs/R08/validation/frozen-lock.json','runs/R08/candidate/C7-lock.json']
    s['events'].append(dict(at=datetime.now(timezone.utc).isoformat(),command='freeze_R08_new_samples',result=dict(lock='runs/R08/validation/frozen-lock.json',acceptance_unchanged=True,old_budgets_unchanged=True)))
    write('state/continuation.json',s)
    write('runs/R08/validation/native-intents.json',dict(created_at=datetime.now(timezone.utc).isoformat(),host='Codex collaboration tools',contexts='fork_turns=none',model='gpt-6-luna',reasoning_effort='max',cases=['simple','complex'],read_scope=['own request/raw inputs','C7 skill/references/scripts'],write_scope=['runs/R08/validation/simple/','runs/R08/validation/complex/'],auth_basis='AGENTS.md independent fresh context and available Luna; complex request requires separate verifier',global_limits='4 actual host slots; disjoint instruction-level write paths',tokens=None,cost=None))

if __name__=='__main__':main()
