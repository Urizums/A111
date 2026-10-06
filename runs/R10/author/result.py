from pathlib import Path
import json

root=Path(__file__).resolve().parents[3]
state=json.loads((root/'state/continuation.json').read_text(encoding='utf-8'))
task=next(t for t in state['tasks'] if t['id']=='R10-01')
attempt=task['attempts'][-1]
result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],criteria=[
    dict(id='a1',status='pass',evidence=['runs/R10/scope-decision.json','runs/R10/candidate/C8-lock.json','runs/R10/author/provenance.json','runs/R10/candidate/C8/forge-agent-flow/SKILL.md']),
    dict(id='a2',status='pass',evidence=['runs/R10/author/quick-validate-command.json','runs/R10/author/inspection.json','runs/R10/author/inspect-command.json'])
],effect=dict(target='document-only meta-workflow candidate',hypothesis='Method guidance can be delivered without the execution platform; behavior awaits independent evaluation',baseline='C7 contained93 files including49 executable/test scripts',conditions='same repo, new user scope, immutable old versions and budget history',observations='C8 contains five Markdown files; structure valid;4051 inherited files and31 task records retained',limits='Author inspection and source integrity only; no performance, generality or full product acceptance claim',metrics=dict(files=5,script_files=0,test_files=0,tokens=None,cost=None)),next_action='R10-02 fresh context executes frozen feedback workflow request')
with (root/'runs/R10/R10-01-result.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')
print(json.dumps(dict(task_id=task['id'],criteria=[c['status'] for c in result['criteria']])))
