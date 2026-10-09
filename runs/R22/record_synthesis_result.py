import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=json.loads((ROOT/'state/continuation.json').read_text(encoding='utf-8'))
t=next(t for t in s['tasks'] if t['id']=='R22-03');a=t['attempts'][-1]
assert a['status']=='in_progress'
result=dict(task_id=t['id'],attempt_id=a['id'],requirements_hash=a['requirements_hash'],criteria=[dict(id='t1',status='pass',evidence=['runs/R22/final-lock.json','runs/R22/final/SYNTHESIS.md','runs/R22/final/source-decision.json','runs/R22/final/source-basis.json','runs/R22/synthesis-command.json'])],
    effect=dict(target=t['title'],hypothesis='Only source-bound general gaps warrant a new pure-document revision.',baseline='C13 nine Markdown files and prior results retained.',conditions='Actual initial science and informed document reception complete; root traces ten existing exact source clauses.',observations='C13 retained: observed display/derived-money defects already covered. Autonomous evidence derivation without root protocol remains untested.',metrics=dict(source_clauses=10,candidate_files=9,product_scripts=0,product_tests=0,model=None,tokens=None,cost=None),limits='Not proof of general skill sufficiency, causal improvement, four-level rerun, prize or formalOctober compliance.'),next_action='R22-next: freeze R23 neutral role inputs and reception rubric, execute actual original-CSV audit first step.')
with (ROOT/'runs/R22/R22-03-result.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(task=t['id'],C13_retained=True)))
