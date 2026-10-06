"""Retain actual Git and GitHub receipts for the already published source commit."""
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess

root=Path(__file__).resolve().parents[3]
records=[]
def command(argv):
    result=subprocess.run(argv,cwd=root,capture_output=True,text=True,encoding='utf-8')
    records.append(dict(argv=argv,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr))
    assert result.returncode==0
    return result.stdout.strip()

head=command(['git','rev-parse','HEAD'])
remote=command(['git','ls-remote','origin','refs/heads/main']).split()[0]
assert head==remote=='d08cd5f99f809df1f21e8cb55cbe0e24d8532508'
ci=json.loads(command(['gh','run','view','37426876905','--repo','Urizums/A111','--json','status,conclusion,jobs,url']))
assert ci['status']=='completed' and ci['conclusion']=='success'
report=dict(schema='forge-published-source-receipt/1',at=datetime.now(timezone.utc).isoformat(),repository='Urizums/A111',branch='main',source_commit=head,remote_commit=remote,actual_push_return=dict(exit_code=0,stdout='11e5ce9..d08cd5f main -> main'),ci=dict(id=37426876905,status=ci['status'],conclusion=ci['conclusion'],url=ci['url'],jobs=[{k:j[k] for k in ['name','status','conclusion']} for j in ci['jobs']]),commands=records,behavior_passed=False,full_product_passed=False,limits='Source payload was published and CI passed; original exhausted workflow case remains failed. Receipt metadata is committed subsequently.',tokens=None,cost=None)
with (root/'runs/R10/publication/source-push-receipt.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(commit=head,remote=head,ci=ci['conclusion'],behavior_passed=False)))
