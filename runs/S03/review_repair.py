"""Independent Root source and recorded-protocol checks for the fresh S03 run."""
import base64,csv,hashlib,json,shlex
from decimal import Decimal
from pathlib import Path
root=Path(__file__).resolve().parents[2];run=root/'runs/S03/repair-1';worker=run/'worker';checks=[]
def read(p):return json.loads(p.read_text())
def check(id,condition,evidence):checks.append({'id':id,'pass':bool(condition),'evidence':evidence})
rows=list(csv.DictReader((run/'expenses.csv').open()));groups={}
for row in rows:
 group=groups.setdefault(row['category'],{'category':row['category'],'total_fen':0,'ids':[]})
 group['total_fen']+=int(Decimal(row['amount'])*100);group['ids'].append(row['id'])
expected={'row_count':len(rows),'total_fen':sum(g['total_fen'] for g in groups.values()),'categories':[groups[k] for k in sorted(groups)]}
actual=read(worker/'totals.json');check('source_exact_integer_fen_and_ids',actual==expected,['expenses.csv','worker/totals.json'])
check('chinese_explanation_present',all(k in (worker/'totals.md').read_text() for k in groups),['worker/totals.md'])
reply=read(worker/'reply.json')
check('reply_done',reply['outcome']=='done' and reply['reason'] is None,['worker/reply.json'])
check('artifact_hashes',all(hashlib.sha256(Path(a['path']).read_bytes()).hexdigest()==a['sha256'] and Path(a['path']).resolve().is_relative_to(worker.resolve()) for a in reply['artifacts']),['worker/reply.json'])
records=[];markers=[]
for p in sorted(worker.rglob('*')):
 if not p.is_file() or p.suffix not in ['.json','.jsonl']:continue
 try:v=read(p)
 except (ValueError,UnicodeError):continue
 if not isinstance(v,dict):continue
 if v.get('schema')=='forge-comparison-cli/1':records.append((p,v))
 if v.get('schema')=='forge-comparison-marker/1':markers.append((p,v))
records.sort(key=lambda t:t[1]['begin']['monotonic_ns'])
work=read(run/'work.json');bootstrap=shlex.split(work['prompt'].splitlines()[1]);target=bootstrap[bootstrap.index('--')+1:]
check('first_target_exact_bootstrap',records[0][1]['argv']==target and records[0][0].name=='000-bootstrap.json',[str(records[0][0].relative_to(run))])
check('target_budget',len(records)<=40,[f'{len(records)} targets / 40'])
raw_ok=True
for p,v in records:
 for key in ['stdout','stderr']:
  raw_ok &= base64.b64decode(v[key+'_base64'],validate=True).decode(errors='replace')==v[key]
 raw_ok &= v['actor']=='worker' and v['begin']['boot_id']==v['end']['boot_id'] and v['end']['monotonic_ns']>=v['begin']['monotonic_ns']
check('raw_streams_actor_boot_order',raw_ok,[str(p.relative_to(run)) for p,v in records])
stages={}
for stage in ['worker_work','worker_reply']:
 b=[(p,v) for p,v in markers if v['stage']==stage and v['event']=='begin'];e=[(p,v) for p,v in markers if v['stage']==stage and v['event']=='end']
 okay=len(b)==len(e)==1
 if okay:okay=b[0][1]['boot_id']==e[0][1]['boot_id'] and b[0][1]['monotonic_ns']<e[0][1]['monotonic_ns']
 check(stage+'_markers',okay,[str(p.relative_to(run)) for p,v in b+e])
 stages[stage]={'begin':b[0][1] if b else None,'end':e[0][1] if e else None,'elapsed_seconds':(e[0][1]['monotonic_ns']-b[0][1]['monotonic_ns'])/1e9 if okay else None}
marker_targets=[v for p,v in records if 'mark' in v['argv']]
check('all_markers_are_captured_targets',len(marker_targets)==len(markers)==4,[str(p.relative_to(run)) for p,v in markers])
preflight=[v for p,v in records if 'check-reply' in v['argv']]
check('preflight_before_worker_reply_end',bool(preflight) and preflight[-1]['exit_code']==0 and preflight[-1]['end']['monotonic_ns']<stages['worker_reply']['end']['monotonic_ns'],['worker/logs/'])
drafts=[]
for p in worker.glob('*.json'):
 try:v=read(p)
 except ValueError:continue
 if v.get('schema_version')=='forge-host-reply/1' and v.get('outcome') is None:drafts.append(p)
check('incomplete_draft_retained',bool(drafts),[str(p.relative_to(run)) for p in drafts])
operations=read(worker/'operations.json')
check('operations_disclosure',isinstance(operations,dict) and bool(operations),['worker/operations.json'])
for name in ['create-return.json','query-1-return.json','query-2-return.json']:
 check('actual_receipt_'+name,(run/name).is_file(),[name])
result={'schema':'forge-native-source-review/1','checks':checks,'passed':all(c['pass'] for c in checks),'expected':expected,'worker_stages':stages,'captured_worker_targets':len(records),'failed_worker_targets':[str(p.relative_to(run)) for p,v in records if v['exit_code']!=0],'drafts':[str(p.relative_to(run)) for p in drafts],'scope':'Root source recomputation and recorded-conformance audit. Instruction-only tool/scope restrictions; no full host trace, security containment or performance claim.','operations':operations,'provider_tokens':None,'provider_cost':None}
(run/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':[c for c in checks if not c['pass']],'captured_worker_targets':len(records)},ensure_ascii=False))
raise SystemExit(not result['passed'])
