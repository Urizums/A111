"""Prepare one explicitly authorized Luna task using the original host bridge."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument('--run', required=True)
p.add_argument('--prompt', required=True)
p.add_argument('--title', required=True)
a = p.parse_args()
run = root / a.run
worker = run / 'worker'
worker.mkdir(parents=True, exist_ok=True)
public = root / 'skills/forge-agent-flow/scripts'
def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
prompt = (root/a.prompt).read_text()
prompt += f'''\nWrite only {worker}. You may author/run benign analysis and validation scripts there; do not modify core, skill, shared TODO/state or historical evidence. Record actual commands/results and all failed attempts, corrections, parent questions, and unavailable measurements (tokens/cost/model-active-time null). Do not spawn/delegate, inspect siblings or query unrelated workers. This is a new task, never execute old native IDs. Before returning, use {public}/hostdraft.py reply with your supplied NEW job/request.json to create a separate incomplete draft. Fill final {worker}/reply.json with the actual task result and hashes of final artifacts. Capture check-reply output before returning. Reply preflight is not semantic acceptance; Root will review. At most two corrective rounds; retain first failures. Do not change referenced outputs after final preflight.'''
plan = dict(schema_version='forge-project-plan/1', id=run.name,
            goal=a.title, deliverable_kind='scoped_change',
            requirements=[dict(id='req_work',text=a.title,origin='explicit',basis=a.prompt,acceptance_ids=['a_work'])],
            acceptance=[dict(id='a_work',assertion='Assigned original requirements are covered by actual source and runtime evidence with limits disclosed.',required=True,level='review')],
            tasks=[dict(id='work',title=a.title,depends_on=[],owner='gpt-6-luna',write_paths=['worker/'],acceptance_ids=['a_work'])])
save(run/'plan.json',plan)
save(run/'work.json',dict(prompt=prompt,inputs=dict(brief=str(root/a.prompt)),
    input_files=[dict(path=str(root/a.prompt),sha256=hashlib.sha256((root/a.prompt).read_bytes()).hexdigest())],
    write_paths=[str(worker)],reply_path=str(worker/'reply.json')))
for name, argv in [('init',['projectctl.py','init',str(run/'plan.json'),'--state',str(run/'state.json')]),
                   ('prepare',['hostbridge.py','prepare','--kind','project','--state',str(run/'state.json'),'--task','work','--work',str(run/'work.json'),'--job',str(run/'job'),'--parent','/root']),
                   ('issue',['hostbridge.py','issue','--job',str(run/'job')])]:
    r = subprocess.run([sys.executable,str(public/argv[0]),*argv[1:]],capture_output=True,text=True)
    save(run/(name+'-command.json'),dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
    if r.returncode: raise SystemExit(r.stderr or r.stdout)
    if name=='issue':
        save(run/'issue.json',json.loads(r.stdout))
        print(r.stdout)
