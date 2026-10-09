from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
import json,csv,hashlib
root=Path('runs/R22/execution');e=root/'correction-v3';sc=root/'science-v1';tables=[];current=[]
for line in (e/'report/REPORT.md').read_text('utf-8').splitlines()+['']:
    if line.startswith('|'):current.append(line.strip('|').split('|'))
    elif current:tables.append(current[2:]);current=[]
assert [len(t) for t in tables]==[3,6,6,12,12,3,2,6,12,12,12,8,8,8,12]
def read(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
ledger=[]
def cell(t,r,c,v,source):
    assert tables[t][r][c]==str(v),(t,r,c,tables[t][r][c],v)
    ledger.append({'table':t+1,'row':r+1,'column':c+1,'expected':str(v),'source':source})
for i,r in enumerate(read(sc/'data/boundaries.csv')):
    for c,v in enumerate([r['origin'][:10],r['train_days']+'/'+r['train_rows'],r['max_train_service'],r['first_target']+' 至 '+r['last_target'],r['activity_days']]):cell(0,i,c,v,'boundaries.csv')
for t,name in [(1,'group_overall.csv'),(2,'group_overall.csv'),(3,'group_stage.csv'),(4,'group_activity.csv')]:
    for i,r in enumerate(read(sc/'results'/name)):
        route=r['origin'][5:10]+'/'+('R' if r['method_id']=='shared_ridge10' else 'W');cell(t,i,0,route,name)
        if t==3:cell(t,i,1,r['stage'],name);cell(t,i,2,r['days']+'/'+r['rows'],name)
        if t==4:cell(t,i,1,'普通' if r['holiday']=='0' else '活动',name);cell(t,i,2,r['days'],name)
bands=read(sc/'results/group_activity_band.csv')
for i,row in enumerate(tables[5]):
    origin=row[0]
    candidates=[r for r in bands if r['origin'][:10]==origin and r['method_id']=='shared_ridge10' and r['holiday']=='1']
    assert len(candidates)==6
    for j,r in enumerate(candidates,1):
        val=r['days']+'日/'+r['rows']+'键'+('<br>不可估计' if r['days']=='0' else '')
        cell(5,i,j,val,'group_activity_band.csv')
for i,r in enumerate(read(sc/'results/combined_first_two.csv')):cell(6,i,0,'R' if r['method_id']=='shared_ridge10' else 'W','combined_first_two.csv');cell(6,i,1,r['days']+'/'+r['rows'],'combined_first_two.csv')
groups={}
for r in read(sc/'results/solver_daily.csv'):groups.setdefault((r['origin'],r['method_id']),[]).append(r)
for i,(key,rs) in enumerate(sorted(groups.items())):
    cell(7,i,0,key[0][5:10]+'/'+('R' if key[1]=='shared_ridge10' else 'W'),'solver_daily.csv')
    vals=[Decimal(r['capacity_slack']) for r in rs]
    cell(7,i,1,int(min(vals)),'solver_daily.csv');cell(7,i,2,int(max(vals)),'solver_daily.csv');cell(7,i,5,sum(v==0 for v in vals),'solver_daily.csv')
for start,name,dim in [(8,'group_store.csv','store_id'),(11,'group_item.csv','item_id')]:
    rows=read(sc/'results'/name)
    for oi,o in enumerate(sorted(set(r['origin'] for r in rows))):
        for i,d in enumerate(sorted(set(r[dim] for r in rows))):cell(start+oi,i,0,o[:10],name);cell(start+oi,i,1,d,name)
for i,r in enumerate(r for r in read(sc/'results/group_activity_stage.csv') if r['holiday']=='1'):
    cell(14,i,0,r['origin'][5:10]+'/'+('R' if r['method_id']=='shared_ridge10' else 'W'),'group_activity_stage.csv');cell(14,i,1,r['stage'],'group_activity_stage.csv');cell(14,i,2,r['days']+'/'+r['rows'],'group_activity_stage.csv')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,count in [('execution-lock.json',268),('document-correction-v2-lock.json',38)]:
    lock=json.loads((Path('runs/R22')/name).read_text('utf-8'));assert len(lock['files'])==count
    for f in lock['files']:assert sha(Path(f['path']))==f['sha256'] and Path(f['path']).stat().st_size==f['size_bytes']
freeze=json.loads((e/'source-freeze.json').read_text('utf-8'))
for f in freeze['identities']:assert sha(Path(f['path']))==f['sha256'] and Path(f['path']).stat().st_size==f['size_bytes']
receipts=[]
for p in sorted((e/'receipts').glob('*.json')):
    if p.name.startswith('0012-'):continue
    r=json.loads(p.read_text('utf-8'));assert r['state']=='finished' and 'end' in r and r['exit_code']==(1 if p.name.startswith('0008-') else 0)
    receipts.append({'path':str(p),'begin':r['begin'],'end':r['end'],'state':r['state'],'exit_code':r['exit_code'],'argv':r['argv'],'sha256':sha(p)})
assert len(receipts)==11
f=json.loads((e/'receipts/0001-freeze-v3-source.json').read_text('utf-8'));m=json.loads((e/'receipts/0002-artifact-marker.json').read_text('utf-8'));b=json.loads((e/'receipts/0003-build-v3-report.json').read_text('utf-8'))
assert f['end']['utc']<m['begin']['utc']<m['end']['utc']<b['begin']['utc']
author=json.loads((e/'author-selfcheck-v3.json').read_text('utf-8'));assert author['verdict']=='pass' and author['independent'] is False
status={'schema':'r22-known-document-attempt-status/1','attempt':3,'repairs_used':2,'repair_limit':None,'author_verdict':'pass','independent_verdict':None,'actual_finalization_utc':datetime.now(timezone.utc).isoformat(),'additional_all_table_metadata_checks':len(ledger),'additional_table_ledger':ledger,'author_selfcheck':'author-selfcheck-v3.json','actual_page_qa':'visual-qa-final.json','pdf_pages':author['actual_pdf_pages'],'primary_md':'report/REPORT.md','primary_pdf':'report/REPORT.pdf','renderer_sha256':author['source_sha256'],'pdf_sha256':author['pdf_sha256'],'markdown_sha256':author['markdown_sha256'],'original_268_unchanged':True,'v2_38_unchanged':True,'source_freeze_verified':True,'scientific_rerun':False,'renderer_modified_by_executor':False,'context_exposure':'Accidental agent-list tool summary exposure during v2 is retained in final report; process is informed re-review, not whole-context blind. No other actor result files opened.','retained_failures':[{'path':'receipts/0008-full-v3-author-selfcheck.json','exit_code':1,'category':'author checker implementation wording assertion','detail':'expected CSV文本 but report expresses CSV十进制文本运算; successor checker changes only this assertion; not a new document repair or scientific failure'},{'path':'../correction-v2/receipts/0006-full-document-selfcheck.json','category':'attempt 2 document consistency failure; immutable'},{'category':'original first reception h6 fail; immutable'},{'category':'original author read-path recovery and expected existing-output refusal retained separately'},{'category':'independent receiver 12 errors retained by receiver, not author regraded'}],'known_reception':'subsequent independent work must be informed re-review','commands_through_previous_terminal':receipts,'finalization_receipt':'receipts/0012-finalize-v3-delivery.json','finalization_receipt_note':'This command receipt is written by record_command only when this process finishes; no terminal state fabricated.','model':None,'tokens':None,'cost':None}
with (e/'ATTEMPT_STATUS.json').open('x',encoding='utf-8') as f:json.dump(status,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'additional_table_checks':len(ledger),'author_verdict':status['author_verdict'],'attempt':3,'repairs_used':2,'old_files_unchanged':306,'previous_terminal_receipts':len(receipts),'retained_checker_exit1':'0008','all_final_pages_actually_viewed':author['actual_pdf_pages']},ensure_ascii=False,indent=2))
