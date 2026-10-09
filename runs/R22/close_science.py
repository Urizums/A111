"""Compose source-bound reception only after terminal independent recheck."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R22'
def read(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def exclusive(rel,obj):
    with (ROOT/rel).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def check_lock(rel):
    lock=read(rel)
    for item in lock['files']:
        b=(ROOT/item['path']).read_bytes()
        assert len(b)==item['size_bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],item['path']
    return len(lock['files'])
first=read('runs/R22/review/initial/result.json')
review=read('runs/R22/review/recheck-v3/result.json')
assert first['criterion_statuses']==dict(h1='pass',h2='pass',h3='pass',h4='pass',h5='pass',h6='fail')
assert review['criterion_statuses']==dict(h1='pass',h2='pass',h3='pass',h4='pass',h5='pass',h6='pass')
assert review['informed_recheck'] is True and review['first_judgment_h6']=='fail'
assert review['first_judgment_sha256']==hashlib.sha256((ROOT/review['first_judgment_path']).read_bytes()).hexdigest()
assert review['criteria']['h6']['tables']['exact_cell_comparisons_passed']
locks=['runs/R22/execution-lock.json','runs/R22/initial-reception-lock.json','runs/R22/document-correction-v2-lock.json','runs/R22/document-correction-v3-lock.json','runs/R22/document-recheck-v3-lock.json','runs/R20/final/candidate/C13-lock.json']
counts={r:check_lock(r) for r in locks}
state=read('state/continuation.json');task=next(t for t in state['tasks'] if t['id']=='R22-02');attempt=task['attempts'][-1]
assert task['repairs_used']==2 and task['repair_limit'] is None
assert [a['status'] for a in task['attempts']]==['failed','failed','in_progress']
receipt_audit=[]
for domain in ['execution/receipts','review/initial/receipts','execution/correction-v2/receipts','execution/correction-v3/receipts','review/recheck-v3/receipts']:
    folder=BASE/domain;assert folder.exists(),domain
    rows=[]
    for p in sorted(folder.glob('*.json')):
        r=json.loads(p.read_text(encoding='utf-8'));assert r['schema']=='forge-command-record/1' and r['state']=='finished'
        assert r['begin']['utc'] and r['end']['utc'] and r['begin']['utc']<=r['end']['utc']
        assert all(k in r for k in ['argv','cwd','stdout','stderr','stdout_base64','stderr_base64','exit_code'])
        rows.append(dict(path=p.relative_to(ROOT).as_posix(),exit_code=r['exit_code'],begin=r['begin']['utc'],end=r['end']['utc']))
    receipt_audit.append(dict(domain=domain,count=len(rows),nonzero=sum(r['exit_code']!=0 for r in rows),records=rows))
exclusive('runs/R22/final/reception-composition.json',dict(first_verdict=first['criterion_statuses'],current_verdict=review['criterion_statuses'],
    scientific_gates='Original fresh independent h1-h5 retained, byte identity reverified; no scientific rerun during repair.',
    document_gate='Actual informed independent v3 h6 recheck; original h6 failure and v2 author-only failure immutable.',locks_checked=counts,
    repairs_used=2,repair_limit=None,exposure='v2 author actual tool-summary exposure retained; new document reception is informed, no all-context blind claim.',model=None,tokens=None,cost=None))
exclusive('runs/R22/final/receipt-audit.json',dict(domains=receipt_audit,claim='Actual terminal command records; nonzero exits preserved by role and attempt, no fabricated successful replacement.'))
result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
    criteria=[dict(id='t1',status='pass',evidence=locks+['runs/R22/review/recheck-v3/result.json','runs/R22/final/reception-composition.json','runs/R22/final/receipt-audit.json','runs/R22/root-metrics-command.json'])],
    effect=dict(target=task['title'],hypothesis='Fixed-horizon claims require actual matching evidence plus independent reception of numbers and complete exported language.',baseline='Original 14-day historical evidence and first two failed document attempts retained.',conditions='Three fixed same-origin historical42-day windows; unchanged R/W policies; known data; initial independent science plus informed repaired-document receiving.',
        observations=dict(first=first['criterion_statuses'],current=review['criterion_statuses']),metrics=dict(scored_keys=24192,unique_dates=101,nonoverlapping_combined_dates=84,root_arithmetic_checks=185384,repair_count=2,actual_model=None,tokens=None,cost=None),
        limits='Synthetic known historical replay, windows overlap25dates; 4activity dates per window, unsupported activity cells and below nominal coverage retained. Not independent126dates, prize, real-business/formal-October compliance or causal skill gain.'),
    next_action='R22-03: source-bound synthesis; retain C13 unless a general source gap is actually demonstrated.')
exclusive('runs/R22/R22-02-result.json',result)
print(json.dumps(dict(current_verdict=review['criterion_statuses'],locks_checked=counts,repairs_used=2),ensure_ascii=False))
