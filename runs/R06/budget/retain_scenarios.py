"""Retain raw bounded-run scenarios; fixture failures are deliberate original regression inputs."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent/'scenarios';BASE.mkdir(exist_ok=False)
CLI=ROOT/'runs/R06/candidate/C5/forge-agent-flow/scripts/bounded_run.py';calls=[]
def call(expected,*args):
 r=subprocess.run([sys.executable,str(CLI),*map(str,args)],capture_output=True,text=True)
 calls.append(dict(argv=[sys.executable,str(CLI),*map(str,args)],expected_exit=expected,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
 (BASE/'commands.json').write_text(json.dumps(calls,indent=2)+'\n');assert r.returncode==expected,r.stdout+r.stderr
 return json.loads(r.stdout or r.stderr)
source=BASE/'original-failure-classes';source.mkdir();input=source/'material.json';input.write_text('{"source":"original three distinct failure classes"}\n');candidate=source/'harness.py';journal=source/'journal'
versions=['broken = {"a":}\n','def submit(): pass\nsubmit(expectation=True)\n','import json\njson.dumps({"predicate": lambda x: x})\n']
for n,text in enumerate(versions):
 (source/f'original-version-{n}.py').write_text(text);candidate.write_text(text)
 if n==0:call(0,'init','--state',journal,'--actor','root-regression-original','--candidate',candidate,'--input',input)
 else:call(0,'repair','--state',journal,'--reason','Separate preserved failure-driven fixture change '+str(n))
 call(1,'run','--state',journal,'--',sys.executable,candidate)
call(2,'repair','--state',journal,'--reason','Forbidden third correction');call(2,'run','--state',journal,'--',sys.executable,candidate)
new=BASE/'new-material';new.mkdir();input=new/'measurements.json';input.write_text('{"samples":[3,5,8]}\n');candidate=new/'analysis.py';journal=new/'journal';candidate.write_text('import json,sys\ndata=json.load(open(sys.argv[1])); print(sum(data["values"]))\n')
call(0,'init','--state',journal,'--actor','root-regression-new','--candidate',candidate,'--input',input);call(1,'run','--state',journal,'--',sys.executable,candidate,input)
candidate.write_text('import json,sys\ndata=json.load(open(sys.argv[1])); print(sum(data["samples"]))\n');call(0,'repair','--state',journal,'--reason','Use original samples field; preserve failure and unchanged original material');call(0,'run','--state',journal,'--',sys.executable,candidate,input)
last=json.loads((journal/'attempt-2.json').read_text());assert last['stdout']=='16\n'
summary={'original_sequence':'3 distinct failed attempts, 2 repairs, third repair and fourth run refused','new_case':'Failure preserved, one correction, actual source sum 16','commands':len(calls),'no_original_worker_rerun':True,'scope':'Local direct-process enforcement, not host/provider-global resource proof'}
(BASE/'report.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
