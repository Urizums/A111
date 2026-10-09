"""Project real command provenance without exposing producer diagnostic arguments."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--workflow',required=True);p.add_argument('--workflow-lock',required=True);a=p.parse_args()
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def identity(rel):
    b=(ROOT/rel).read_bytes();return dict(path=rel,size_bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
exlock=read('runs/R23/execution-lock.json');rows=[]
for f in exlock['files']:
    if '/receipts/' not in f['path']:continue
    assert identity(f['path'])==f
    j=read(f['path']);assert j['schema']=='forge-command-record/1' and j['state']=='finished' and isinstance(j['exit_code'],int)
    rows.append(dict(source=f,**{k:j[k] for k in ['schema','state','begin','end','exit_code']}))
assert len(rows)==34
designlock=read(a.workflow_lock);entry=next(r for r in designlock['files'] if r['path']==a.workflow);assert identity(a.workflow)==entry
base=ROOT/'runs/R23/receiving-packet';base.mkdir(exist_ok=True)
with (base/'process-terminals.json').open('x',encoding='utf-8') as f:
    json.dump(dict(schema='r23-source-bound-terminal-projection/1',source_execution_lock=identity('runs/R23/execution-lock.json'),records=rows,projection='Only original byte identity and real schema/state/begin/end/exit fields. No argv, output streams, producer diagnosis or expected result.',claim='Process provenance, not numerical or acceptance verdict.'),f,ensure_ascii=False,indent=2)
allowed=[a.workflow,a.workflow_lock,'runs/R23/brief/TASK.md','runs/R23/brief/INPUTS.json','runs/R23/acceptance.json','runs/R20/final/candidate/C13-lock.json','runs/R21/input-lock.json','runs/R23/execution-lock.json','runs/R23/execution/v2/consumer_slice.py','runs/R23/execution/v2/consumer-slice-config.json','runs/R23/execution/v2/consumer-slice-freeze.json','runs/R23/execution/v2/consumer-point-slice.csv','runs/R23/execution/v2/consumer-point-slice-report.json','runs/R23/execution/receipts/r23-consumer-30-compute-v2-final.txt','runs/R23/receiving-packet/process-terminals.json']
interface=(ROOT/a.workflow).with_name('METHOD-OUTPUT-INTERFACE.md')
if interface.exists():
    rel=interface.relative_to(ROOT).as_posix()
    assert identity(rel)==next(r for r in designlock['files'] if r['path']==rel)
    allowed.append(rel)
allowed.append('runs/R23/design/probe.py')
with (base/'manifest.json').open('x',encoding='utf-8') as f:
    json.dump(dict(schema='r23-narrow-receiving-packet/1',actual_artifacts=[identity(r) for r in allowed],raw_and_reference='Original R21 raw/reference files and C13 nine Markdown remain permitted.',forbidden='Other producer reports/manifests/selfchecks/diagnoses, historical argv/streams, old workflow/reviews/results and root findings. Lock metadata is identity only.',scope='Original j1-j4 receiving of this versioned workflow and actual one-date consumer slice; no intended answers or prior verdicts.'),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(command_projections=len(rows),actual_artifacts=len(allowed),no_diagnostic_arguments=True)))
