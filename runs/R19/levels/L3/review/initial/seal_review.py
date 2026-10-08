import json,hashlib,ast,time,os
from pathlib import Path
from datetime import datetime,timezone
H=Path(__file__).resolve().parent;R=H.parents[5];start=time.perf_counter()
def load(p):return json.loads(p.read_text(encoding='utf-8'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
input_checks=[]
for lock in ['runs/R19/candidate/C11-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/levels/L3/design-lock.json','runs/R19/evaluation-lock.json']:
 obj=load(R/lock)
 for item in obj['files']:
  b=(R/item['path']).read_bytes();ok=hashlib.sha256(b).hexdigest()==item['sha256'] and len(b)==item.get('size_bytes',len(b));input_checks.append({'lock':lock,'path':item['path'],'matches':ok})
assert len(input_checks)==23 and all(x['matches'] for x in input_checks)
(H/'input-lock-final.json').write_text(json.dumps(input_checks,ensure_ascii=False,indent=2),encoding='utf-8')
result=load(H/'result.json');assert [x['id'] for x in result['a1_a6']]==['a1','a2','a3','a4','a5','a6'] and len(result['quality_diagnosis'])==6
assert not result['pending_calls'] and not result['active_self_started_processes'] and not result['child_agents']
assert result['status']=='not_accepted_repair_required' and next(x for x in result['a1_a6'] if x['id']=='a5')['status']=='fail'
assert load(H/'lock-start.json')['lock_sha256']==load(H/'lock-end.json')['lock_sha256']
assert load(H/'lock-end.json')['all_bytes_match'] and load(H/'retention-and-method-check.json')['prepared_payload_hashes_unchanged']
assert load(H/'experiment-audit.json')['all_checks_pass'] and load(H/'figure-paper-audit.json')['data_and_markdown_trace_pass']
scripts=0;jsons=0
for p in H.rglob('*'):
 if not p.is_file():continue
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'),filename=str(p));scripts+=1
 if p.suffix=='.json' and p.name not in ['manifest.json','final-check.json']:load(p);jsons+=1
final={'utc':datetime.now(timezone.utc).isoformat(),'status':'initial_review_writes_terminal_after_manifest','source_locks_final':23,'source_matches':True,
       'execution_start_end_match':True,'prepared_payload_unchanged':True,'script_syntax_checked':scripts,'strict_json_checked':jsons,
       'a1_a6_count':6,'quality_count':6,'all_own_commands_reconciled':True,'pending_calls':[],'active_self_started_processes':[],
       'child_agents':[],'known_finalizer_process':os.getpid(),'finalizer_exits_synchronously':True,'model':None,'token_usage':None,'cost':None,
       'elapsed_seconds':time.perf_counter()-start}
(H/'final-check.json').write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
files=[]
for p in sorted(H.rglob('*')):
 if not p.is_file() or p==H/'manifest.json':continue
 b=p.read_bytes();files.append({'path':str(p.relative_to(H)).replace('\\','/'),'size_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
m={'schema':'independent-initial-review-manifest/1','task':'R19-C11-L3','utc':datetime.now(timezone.utc).isoformat(),
   'scope':'runs/R19/levels/L3/review/initial/','files':files,'status':'not_accepted_repair_required',
   'terminal':'all own known script/CLI sessions exit; no background/agent/pending; finalizer completes synchronously before notification',
   'limits':'Source scientific and historical limitations are in report/result; this manifest is byte identity only','model':None,'token_usage':None,'cost':None}
(H/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'files':len(files),'bytes':sum(x['size_bytes'] for x in files),'source_locks23_match':True,
                  'strict_json':jsons,'scripts':scripts,'pending_calls':0,'manifest_sha256':hashlib.sha256((H/'manifest.json').read_bytes()).hexdigest()},ensure_ascii=False))
