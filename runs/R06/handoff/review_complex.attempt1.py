"""Root's read-only source and retained-result review; does not rerun worker effects."""
import hashlib,json,sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
run=ROOT/'runs/R06/handoff/complex';worker=run/'worker'
def read(p):return json.loads(p.read_text())
def db(name):
    con=sqlite3.connect((worker/'outputs/databases'/name).as_uri()+'?mode=ro',uri=True)
    con.row_factory=sqlite3.Row
    return con
material=read(ROOT/'runs/R06/handoff/materials/complex.json')
policy=read(ROOT/'runs/R06/approval/policy.json')
reply=read(worker/'reply.json')
for ref in reply['artifacts']:
    assert hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest()==ref['sha256'],ref['path']
for ref in read(ROOT/'runs/R06/candidate/C5-lock.json')['files']:
    assert hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest()==ref['sha256'],ref['path']
expected=['sample_rule_match','category_review','amount_unknown','risk_review','self_review','evidence_missing','amount_review']
with db('original-batch.sqlite3') as con:
    rows=[dict(x) for x in con.execute('SELECT * FROM tickets ORDER BY ticket_id')]
    audit=[dict(x) for x in con.execute('SELECT * FROM audit ORDER BY id')]
    requests=[dict(x) for x in con.execute('SELECT * FROM requests ORDER BY request_id')]
assert len(rows)==len(audit)==len(requests)==len(material['requests'])==7
for i,(source,row,event,saved,reason) in enumerate(zip(material['requests'],rows,audit,requests,expected)):
    assert read(worker/f'input/original/request-{i+1}.json')==source
    assert row['ticket_id']==source['ticket_id'] and row['version']==1 and row['reason']==reason
    assert row['decision']==('approved' if i==0 else 'manual')
    assert event['previous_version']==0 and event['new_version']==1
    assert event['request_id']==source['request_id'] and event['reason']==reason
    assert event['policy_version']==policy['version']
    payload=json.loads(saved['payload'])
    assert payload['request']==source and payload['policy']==policy
logs=[json.loads(s) for s in (worker/'outputs/attempts/attempt-1-repair-0/processes.jsonl').read_text().splitlines()]
def phase(name):return [r for r in logs if r['phase']==name]
assert phase('recovery_controlled_crash')[0]['exit_code']==75
assert json.loads(phase('recovery_inspect_after_crash')[0]['stdout'])=={'ticket':None,'audit':[]}
assert phase('recovery_same_request_retry')[0]['exit_code']==0
assert json.loads(phase('idempotency_identical_retry')[0]['stdout'])['reused'] is True
assert phase('idempotency_before_retry')[0]['stdout']==phase('idempotency_after_retry')[0]['stdout']
assert sorted(r['exit_code'] for r in phase('concurrency_decide'))==[0,3]
assert all(r['exit_code']==3 for r in logs if r['phase'].startswith('conflict_conflict-'))
for filename in ['concurrency.sqlite3','recovery.sqlite3']:
    with db(filename) as con:
        assert con.execute('SELECT count(*) FROM tickets').fetchone()[0]==1
        assert con.execute('SELECT count(*) FROM audit').fetchone()[0]==1
successor=read(worker/'outputs/manual-review-task.json')
assert phase('successor_manual_review_start')[0]['exit_code']==0
assert successor['status']=='started' and successor['external_effects'] is False
assert [x['ticket_id'] for x in successor['items']]==[r['ticket_id'] for r in material['requests'][1:]]
assert [x['reason'] for x in successor['items']]==expected[1:]
assert all(x['needed_material'] for x in successor['items'])
ledger=read(worker/'validation/journal/ledger.json')
assert ledger['phase']=='passed' and ledger['repairs_used']==0 and len(ledger['attempts'])==1
result={'status':'pass_in_frozen_local_pilot_scope','source_rows':7,'retained_process_results':len(logs),'real_concurrency':[0,3],
        'controlled_crash':75,'successor':successor['task_id'],'actor':'Root','native_subdelegations':0,
        'guidance_scope':'Worker decomposed local validation into source processing, recovery, concurrency and successor command programs; no autonomous native multi-agent organization was demonstrated.',
        'budget':{'guarded_runs':1,'guarded_failures':0,'guarded_repairs':0,'reported_pre_freeze_source_corrections':1,'reported_reply_artifact_refresh':1,'limit':2},
        'limits':['Initial reads/help were not fully command-captured; no full C2 timing conformance','No matched A/B efficiency comparison; no provider-global recovery','Fresh worker execution and Root source review, not worker-to-worker independent peer review','Native multi-agent decomposition/assignment remains unverified; do not infer it from subprocesses']}
with (run/'root-review.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False))
