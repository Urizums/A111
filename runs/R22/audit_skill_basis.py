"""Record exact source clauses before the R22 source-design judgment."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R22'
source=ROOT/'runs/R20/final/candidate/C13/forge-agent-flow'
lock=json.loads((source.parent.parent/'C13-lock.json').read_text(encoding='utf-8'))
for r in lock['files']:
    b=(ROOT/r['path']).read_bytes()
    assert len(b)==r['size_bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],r['path']
clauses={
    'references/workflow-design.md':[
        'When the user gives only a high-level goal, infer sensible domain duties and state',
        'then identify necessary evidence, decisions, work and dependencies.',
        'the executor can begin from raw inputs, branch on results,'],
    'references/modeling.md':[
        'Compare on the same admissible data, split, constraints, resources and relevant',
        'After the first feasible result identify the material weakness that could change',
        'Language that',
        'Correct source text does not establish a correct exported document.'],
    'references/evaluation.md':[
        'Make the case activate the condition named in its selected assertion:',
        'mandatory acceptance.',
        'Each required failure needs the exact violated source clause or justified derived'],
}
entries=[]
for rel,needles in clauses.items():
    text=(source/rel).read_text(encoding='utf-8');lines=text.splitlines()
    for needle in needles:
        hits=[i for i,line in enumerate(lines) if needle in line]
        assert len(hits)==1,(rel,needle,hits)
        i=hits[0];entries.append(dict(path=(source/rel).relative_to(ROOT).as_posix(),line=i+1,
            excerpt='\n'.join(lines[max(0,i-1):min(len(lines),i+5)]),source_sha256=hashlib.sha256((source/rel).read_bytes()).hexdigest()))
out=BASE/'final/source-basis.json'
with out.open('x',encoding='utf-8') as f:json.dump(dict(clauses=entries,C13_files=len(lock['files']),
    source_verified=True,claim='Actual source clauses only; policy sufficiency and gap judgment are a separate human-readable synthesis.',
    model=None,tokens=None,cost=None),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(source_verified=True,source_files=len(lock['files']),bound_clauses=len(entries))))
