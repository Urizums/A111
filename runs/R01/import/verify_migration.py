"""Frozen source comparisons and late-failure/retry cases using the actual CLI."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[3]
source=root/'runs/R01/import/legacy.json'
data=json.loads(source.read_text());database=out/'inventory.sqlite3';checks=[]

def run(name,input,expected):
    argv=[sys.executable,str(root/'challenges/inventory/import_inventory.py'),'--input',str(input),'--database',str(database)]
    before=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(argv,capture_output=True,text=True)
    record=dict(argv=argv,begin=before,end=datetime.now(timezone.utc).isoformat(),exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr)
    (out/(name+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    assert result.returncode==expected,record
    return json.loads(result.stdout)

def rows():
    with sqlite3.connect(database) as db:
        return {t:db.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in ['locations','assets','service_events','import_batches']}

first=run('01-import',source,0);assert first['status']=='applied'
actual=rows()
assert actual['locations']==sorted((x['code'],x['name']) for x in data['locations'])
assert actual['assets']==sorted(tuple(x[k] for k in ['asset_id','label','serial','location','condition']) for x in data['assets'])
assert actual['service_events']==sorted((e['event_id'],x['asset_id'],e['date'],e['note']) for x in data['assets'] for e in x['service'])
checks.append('source_rows_and_relationships')
baseline=database.read_bytes()
second=run('02-retry',source,0);assert second['status']=='reused'
assert rows()==actual and database.read_bytes()==baseline
checks.append('idempotent_retry_no_write')
drift=copy.deepcopy(data);drift['assets'][0]['label']='changed harmless fixture'
file=out/'same-batch-drift.json';file.write_text(json.dumps(drift,ensure_ascii=False))
run('03-content-conflict',file,2);assert rows()==actual and database.read_bytes()==baseline
checks.append('same_batch_drift_rejected')
for index,defect in enumerate(['foreign_key','duplicate_serial'],4):
    bad=copy.deepcopy(data);bad['batch_id']='bad-'+defect
    bad['locations']=[dict(code='NEW',name='临时库')]
    for i,asset in enumerate(bad['assets']):
        asset.update(asset_id='NEW-'+str(i),serial='NEW-SERIAL-'+str(i),location='NEW',service=[])
    if defect=='foreign_key':bad['assets'][-1]['location']='MISSING'
    else:bad['assets'][-1]['serial']=data['assets'][0]['serial']
    file=out/(defect+'.json');file.write_text(json.dumps(bad,ensure_ascii=False))
    run(str(index)+'-'+defect,file,2)
    assert rows()==actual and database.read_bytes()==baseline
    checks.append('late_'+defect+'_rolls_back_all_rows')
with sqlite3.connect(database) as db:
    assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
checks.append('persistent_database_integrity')
report=dict(passed=True,checks=checks,database=str(database),baseline_sha256=hashlib.sha256(baseline).hexdigest(),
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),python=sys.version,
            sqlite=sqlite3.sqlite_version,limits=['Controlled local CLI/SQLite cases; no provider, network or production effect guarantee.'])
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
