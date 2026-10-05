"""Root review gates each actual criterion and full source rows, not exit code alone."""
import hashlib,json,sqlite3
from pathlib import Path
root=Path(__file__).resolve().parents[3];run=Path(__file__).parent;clone=run/'worker/checkout'
read=lambda p:json.loads(p.read_text())
checks=[]
snap=read(run/'snapshot.json');allowed={'state/continuation.json','state/phase-todo.json','state/checkpoint.json'}
for row in snap['files']:
 if row['path'] not in allowed:assert hashlib.sha256((clone/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
checks.append('unchanged_original_source_and_history')
for row in read(run/'export-manifest.json')['files']:assert hashlib.sha256((root/row['export']).read_bytes()).hexdigest()==row['sha256']
checks.append('portable_export_hashes')
p=root/'runs/R02/worker-recovery';result=read(p/'task-result.json');assert {c['id'] for c in result['criteria']}=={'a1','a2','a3'} and all(c['status']=='pass' for c in result['criteria']);checks.append('all_criteria_not_exit_code_only')
crash=read(p/'04-crash-command.json');assert crash['exit_code']==73;actual=json.loads(crash['stdout']);assert actual['transaction_active'] and actual['uncommitted_mutations']==6
post=read(p/'post-crash-result.json');assert post['passed'] and post['baseline_database_sha256']==post['after_crash_database_sha256'];checks.append('real_exit_73_and_byte_exact_rollback')
source=read(root/'runs/R02/materials/recovery-batch.json')
with sqlite3.connect(p/'recovery.sqlite3') as c:
 for a in source['assets']:
  assert c.execute('SELECT * FROM assets WHERE asset_id=?',(a['asset_id'],)).fetchone()==tuple(a[k] for k in ['asset_id','label','serial','location','condition'])
  for e in a['service']:assert c.execute('SELECT * FROM service_events WHERE event_id=?',(e['event_id'],)).fetchone()==(e['event_id'],a['asset_id'],e['date'],e['note'])
 assert c.execute('PRAGMA integrity_check').fetchone()==('ok',)
checks.append('full_original_rows_and_relationships')
assert json.loads(read(p/'08-retry-identical-command.json')['stdout'])['status']=='reused';checks.append('identical_retry_reused')
state=read(clone/'state/continuation.json');tasks={t['id']:t for t in state['tasks']};assert tasks['R02-01']['status']=='done' and tasks['R02-02']['status']=='in_progress';assert state['project_goal']['status']=='active';assert read(clone/'state/history/R01-todo.json')['tasks'][-1]['status']=='done';checks.append('real_successor_started_and_phase_archived')
report=dict(status='pass',reviewer='Root',checks=checks,limits=['Worker task-result has a manual hash transcription error in its prose table; reply/export hashes verified above are authoritative.','The worker evaluator exit status alone omits successor_ok; this review checks every criterion plus actual successor state and command. No false passing criterion was observed.','One status reminder from Root, no expected answer supplied; zero user questions.','Worker evidence-placement correction=1; early exploratory cat errors lack numeric exit capture and remain disclosed.','Root prepared the separate production flow and app while the isolated handoff ran. Command timestamps, not later state-registration timestamps, define chronology.','One controlled command-process failure; no native-model/provider/network recovery claim.'],source_result_sha256=hashlib.sha256((p/'task-result.json').read_bytes()).hexdigest())
(run/'root-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
