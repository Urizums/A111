"""Freeze two new cases and execution conditions before native dispatch."""
from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'runs/R08/validation'
def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        if isinstance(value,str): f.write(value)
        else: json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    write(BASE/'inputs/payments.csv', '''payment_id,account,amount_cents,status
p01,alpha,1250,settled
p02,beta,340,settled
p01,alpha,1250,settled
p03,alpha,-200,settled
p04,beta,700,pending
p05,gamma,abc,settled
p06,gamma,900,settled
p07,,150,settled
p08,beta,660,settled
''')
    simple = dict(case_id='simple', goal='Produce a one-time payments reconciliation JSON from the supplied CSV; no reusable flow or application is requested.', input='runs/R08/validation/inputs/payments.csv', requirements=[
        'Process rows in source order with physical CSV line numbers including the header as line 1.',
        'Accept only status settled, a nonempty account, an integer amount_cents, and the first occurrence of each payment_id. A negative integer is a valid refund.',
        'Later repeated payment_id rows are duplicate and cannot change totals. A first occurrence is reserved even if invalid; check duplication first, then status, then account, then integer amount.',
        'Write results/reconciliation.json with totals_cents keyed by account and accepted line numbers; report rejected rows with line and one of duplicate, not_settled, missing_account, invalid_amount.',
        'Run a meaningful source/output check; state chosen route and references actually loaded. Do not create a factory, application or project controller for this result.'
    ])
    complex_case = dict(case_id='complex', goal='Build a local persistent approval CLI for document requests, and obtain independent runtime verification before delivery. This is a small software system, not a reusable agent flow.', requirements=[
        'Use Python standard library and SQLite; all business data lives in a caller-supplied database path. No network, messages, accounts or real approvals.',
        'Provide CLI submit, get, decide commands with --db. submit --id --owner stores a pending request at version 1. Duplicate id fails without changing the existing row. get --id returns id, owner, status, version as JSON.',
        'decide --id --actor --expected-version --status approved|rejected succeeds only for actor reviewer, pending row and exact current version. Success atomically changes status and increments version once. Any rejection exits nonzero and changes no business row.',
        'Missing id, empty id/owner and bad status must be rejected. Separate CLI process invocations preserve state. Emit machine-readable JSON on success and a useful error on rejection.',
        'Run two concurrent decide processes using the same pending row and version: exactly one succeeds, final version is 2 and status equals the successful decision. Verify unauthorized, stale and repeated decisions preserve the row.',
        'A fresh independent agent must derive checks from this request and the implementation without expected answers, author test results or diagnoses. It performs actual CLI checks and writes its own evidence under the assigned reviewer directory. Author checks do not replace this requirement.',
        'Keep a short requirements/architecture/TODO record and actually execute a useful successor first step after acceptance, such as running a new invalid-input or concurrent case with retained command evidence; a successor plan alone is insufficient.'
    ])
    for case in (simple, complex_case):
        name=case['case_id'];write(BASE/f'inputs/{name}-request.json',case)
        write(BASE/f'{name}/first_read.py', f'''from pathlib import Path
root=Path(__file__).resolve().parents[4]
for name in ['runs/R08/validation/inputs/{name}-request.json', 'runs/R08/candidate/C7/forge-agent-flow/references/recording-protocol.md', 'runs/R08/candidate/C7/forge-agent-flow/SKILL.md']{ " + ['runs/R08/validation/inputs/payments.csv']" if name=='simple' else ''}:
    print('SOURCE '+name); print((root/name).read_text(encoding='utf-8'))
''')
    spec=dict(schema='forge-r08-validation/1',frozen_at=datetime.now(timezone.utc).isoformat(), candidate='runs/R08/candidate/C7-lock.json',cases=['simple','complex'],requirements=['Execute frozen simple and complex requests in separate fresh native contexts','Record exact first command, first business artifact time, correctness, interventions, native children and successor actual work separately','Independent verification uses original requirements with no answer/diagnosis exposure','Preserve R07 failures and old budgets; no efficiency or generalization conclusion'], repair_limit_per_actor=2,repairs_used=0, first_artifact_definition='First persisted business output (simple JSON or executable CLI source), not intake/probe/TODO',time_origin='Exact first command capture begin on same WSL boot; spawn-to-first-command is separately nullable',deadline='No performance threshold; observe this bounded session. If interrupted, retain unknown/pending and do not duplicate creation.', administrative_exclusions=['WSL command transport and read-only locator assistance, if separately recorded; these are interventions, not source repairs'], status_query_limit=12, wait_seconds_max=45, model='gpt-6-luna',reasoning_effort='max', tokens=None,cost=None,scopes_are_instruction_level=True)
    write(BASE/'spec.json',spec)
    rows=[]
    for p in [ROOT/'runs/R08/candidate/C7-lock.json',BASE/'spec.json',*sorted((BASE/'inputs').glob('*')),BASE/'simple/first_read.py',BASE/'complex/first_read.py']:
        raw=p.read_bytes();rows.append(dict(path=p.relative_to(ROOT).as_posix(),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    write(BASE/'frozen-lock.json',dict(schema='forge-r08-case-lock/1',files=rows))
    print(json.dumps({'frozen_cases':2,'files':len(rows),'repair_limit':2}))

if __name__=='__main__':main()
