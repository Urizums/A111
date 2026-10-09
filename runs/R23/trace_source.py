"""Extract actual frozen C13 clauses for later source adjudication, without verdicts."""
import hashlib
import json
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R20/final/candidate/C13/forge-agent-flow'
p=argparse.ArgumentParser();p.add_argument('--out',default='runs/R23/source-basis.json');args=p.parse_args()
lock=json.loads((ROOT/'runs/R20/final/candidate/C13-lock.json').read_text(encoding='utf-8'))
for row in lock['files']:
    b=(ROOT/row['path']).read_bytes()
    assert len(b)==row['size_bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
assert len(lock['files'])==9 and all(r['path'].endswith('.md') for r in lock['files'])
selections=[
    ('workflow-design.md',3,6,'Derive evidence and decisions from the received outcome.'),
    ('workflow-design.md',20,29,'Transferable operating criteria, interfaces and observable branches.'),
    ('workflow-design.md',54,57,'Map mandatory receiving checks before the first slice.'),
    ('evaluation.md',26,33,'Real smoke path, relevant boundary, activated selected condition.'),
    ('evaluation.md',49,62,'Fresh source-based receiver and concrete actual recomputation.'),
    ('evaluation.md',80,98,'Judge the judgment, artifact states, unknowns and retained failures.'),
    ('modeling.md',20,33,'Point-in-time source, exact revisions and grouped arrival boundaries.'),
    ('modeling.md',35,39,'Justified candidates and fair admissible comparison.'),
    ('modeling.md',68,72,'Freeze experiment identities and trace result-to-paper claims.'),
    ('modeling.md',76,95,'Sparse-input research duties and smoke versus completed paper.'),
    ('modeling.md',97,120,'Standalone scientific argument, substantive language and reader format.'),
    ('iteration-and-recovery.md',3,30,'Classified errors, retained history and evidence of further progress.'),
    ('collaboration.md',21,44,'Separate production/reception and actual role state/telemetry.'),
]
rows=[]
for name,start,end,purpose in selections:
    p=BASE/'references'/name;lines=p.read_text(encoding='utf-8').splitlines()
    rows.append(dict(path=p.relative_to(ROOT).as_posix(),start_line=start,end_line=end,purpose=purpose,excerpt='\n'.join(lines[start-1:end]),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
path=ROOT/args.out
with path.open('x',encoding='utf-8') as f:json.dump(dict(C13_files=9,all_bytes_verified=True,clauses=rows,claim='Exact source evidence only; independent reception and source-gap judgment are separate.'),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(C13_files=9,clauses=len(rows),source_bytes_verified=True)))
