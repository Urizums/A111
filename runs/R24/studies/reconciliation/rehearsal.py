#!/usr/bin/env python3
"""R24 research: generate and grade a natural-language workflow handoff trial.

This does not invoke an Agent, secure files, or judge workflow prose.
Its source/grader boundary must be enforced by the real execution host.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
import tempfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

FILES = ('brief.md','consumer.md','invoices.json','amendments.json','payments.json')
LEDGER = ('invoice_id','vendor','total_cents','paid_cents','outstanding_cents')
SUPPLIERS = ('vendor','outstanding_cents')


def put(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value,str):
        path.write_text(value,encoding='utf-8')
    else:
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def public_hash(folder: Path) -> dict:
    return {p:hashlib.sha256((folder/p).read_bytes()).hexdigest() for p in FILES}


def compute(invoices: list, amendments: list, payments: list, cutoff: str) -> tuple[list, list]:
    amended=defaultdict(list)
    for a in amendments:
        if a['state']=='approved' and a['approved_at']<=cutoff:
            amended[a['invoice_id']].append(a)
    paid=defaultdict(int)
    for p in payments:
        if p['state']=='posted' and p['posted_at']<=cutoff:
            paid[p['invoice_id']]+=p['cents']
    ledger=[]; totals=defaultdict(int)
    for i in invoices:
        changes=sorted(amended[i['invoice_id']],key=lambda a:(a['approved_at'],a['change_id']))
        total=changes[-1]['revised_total_cents'] if changes else i['total_cents']
        row=dict(invoice_id=i['invoice_id'],vendor=i['vendor'],total_cents=total,
                 paid_cents=paid[i['invoice_id']],outstanding_cents=total-paid[i['invoice_id']])
        ledger.append(row)
        totals[i['vendor']]+=row['outstanding_cents']
    return sorted(ledger,key=lambda r:r['invoice_id']), sorted(
        (dict(vendor=k,outstanding_cents=v) for k,v in totals.items()),key=lambda r:r['vendor'])


def generate(seed: int, destination: Path) -> dict:
    if destination.exists():
        raise FileExistsError('Refusing to overwrite an existing study')
    rng=random.Random(seed)
    destination.mkdir(parents=True)
    pub=destination/'producer'; pub.mkdir()
    secret=destination/'private';secret.mkdir()
    day=date(2027,4,1)+timedelta(days=rng.randrange(60))
    cutoff=day.isoformat()+'T18:00:00Z'
    vendors=['Arbor','Beacon','Cedar']
    invoices=[]; amendments=[];payments=[]
    for idx in range(1,7):
        inv=f'I{idx:03d}'; vendor=vendors[(idx-1)%len(vendors)]
        amount=rng.randint(900,7200)
        invoices.append(dict(invoice_id=inv,vendor=vendor,total_cents=amount))
        # A future amendment is a deliberate canary for as-of leakage.
        if idx in (1,4):
            amendments.append(dict(change_id=f'A{idx}x',invoice_id=inv,state='approved',
                approved_at=(day+timedelta(days=1)).isoformat()+'T09:00:00Z',
                revised_total_cents=amount+930))
        if idx in (2,5):
            amendments.append(dict(change_id=f'A{idx}a',invoice_id=inv,state='approved',
                approved_at=(day-timedelta(days=1)).isoformat()+'T09:00:00Z',
                revised_total_cents=amount+470))
        if idx==3:
            amendments.append(dict(change_id=f'A{idx}p',invoice_id=inv,state='pending',
                approved_at=(day-timedelta(days=1)).isoformat()+'T09:00:00Z',
                revised_total_cents=amount+2000))
        payments.append(dict(payment_id=f'P{idx}a',invoice_id=inv,state='posted',
            posted_at=(day-timedelta(days=2)).isoformat()+'T09:00:00Z',cents=rng.randint(300,800)))
        if idx in (1,2,6):
            payments.append(dict(payment_id=f'P{idx}b',invoice_id=inv,state='posted',
                posted_at=(day+timedelta(days=1)).isoformat()+'T09:00:00Z',cents=1500))
        if idx==4:
            payments.append(dict(payment_id=f'P{idx}v',invoice_id=inv,state='void',
                posted_at=(day-timedelta(days=1)).isoformat()+'T09:00:00Z',cents=2200))
    brief=(f'Operations needs a repeatable reconciliation handoff as of {cutoff}. '
           'Show the status of every invoice and a separate summary for every supplier, '
           'including suppliers with no exceptions. Take payment posting time and approval '
           'of corrections into account. Another teammate should be able to repeat your '
           'method on a later data extract. Please do the work on the attached data, '
           'not only describe how someone else might do it.\n')
    consumer=('The downstream finance importer reads ledger.csv and suppliers.csv. '
              'ledger.csv columns in order: invoice_id,vendor,total_cents,paid_cents,outstanding_cents. '
              'suppliers.csv columns: vendor,outstanding_cents. Amounts are signed integer cents, '
              'not floating-point money. Rows can be in any order. '
              'Provide workflow.md in ordinary prose so a colleague can repeat the job. '
              'Use only approved amendments effective at or before the as-of timestamp; '
              'for each invoice the latest effective approved amendment replaces the base total. '
              'Include payments only when state is posted and posted_at is no later than as-of. '
              'Outstanding is effective total minus included payments; negative balances may be valid.\n')
    put(pub/'brief.md',brief);put(pub/'consumer.md',consumer)
    for name,value in [('invoices.json',invoices),('amendments.json',amendments),('payments.json',payments)]:put(pub/name,value)
    ledger,suppliers=compute(invoices,amendments,payments,cutoff)
    put(secret/'oracle.json',dict(seed=seed,source_hash=public_hash(pub),ledger=ledger,suppliers=suppliers))
    return dict(kind='reconciliation',seed=seed,producer=str(pub),private=str(secret),
                note='Do not expose private/ to the tested agent; subfolders are not isolation')


def load_csv(path: Path, columns: tuple) -> list:
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f)
        if r.fieldnames!=list(columns):raise ValueError(f'{path.name}: invalid headers')
        result=[]
        for row in r:
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f'{path.name}: malformed row')
            for field in columns:
                if field.endswith('_cents'):
                    value=row[field]
                    if not value.lstrip('-').isascii() or not value.lstrip('-').isdecimal() or value in ('-',''):
                        raise ValueError(f'{path.name}: invalid integer cents')
                    row[field]=int(value)
            result.append(row)
        return result


def compare(rows: list, expected: list, key: str, label: str) -> list:
    problems=[]; seen={}
    for r in rows:
        k=r[key]
        if k in seen:problems.append(f'{label}: duplicate {k}')
        seen[k]=r
    original={r[key]:r for r in expected}
    for k in sorted(original.keys()-seen.keys()):problems.append(f'{label}: missing {k}')
    for k in sorted(seen.keys()-original.keys()):problems.append(f'{label}: unexpected {k}')
    for k in sorted(original.keys()&seen.keys()):
        if original[k]!=seen[k]:problems.append(f'{label}: mismatched {k}')
    return problems


def grade(case: Path, submission: Path) -> dict:
    oracle=json.loads((case/'private/oracle.json').read_text(encoding='utf-8'))
    errors=[];public=case/'producer'
    try:
        for name,digest in oracle['source_hash'].items():
            if hashlib.sha256((public/name).read_bytes()).hexdigest()!=digest:
                errors.append(f'case material changed: {name}')
    except (KeyError,OSError,TypeError) as exc:errors.append(f'source identity unverified: {exc}')
    for name,columns,kind,key in [('ledger.csv',LEDGER,'ledger','invoice_id'),
                                   ('suppliers.csv',SUPPLIERS,'suppliers','vendor')]:
        try:errors.extend(compare(load_csv(submission/name,columns),oracle[kind],key,name))
        except (ValueError,OSError,UnicodeError,csv.Error) as exc:errors.append(f'{name}: {exc}')
    flow=submission/'workflow.md'; workflow_present=flow.is_file() and bool(flow.read_text(encoding='utf-8').strip()) if flow.is_file() else False
    # No lexical prose rule: effectiveness of workflow description needs a human/actor consumer.
    return dict(schema='forge-r24-handoff-check/1',data_artifacts_passed=not errors,
                errors=errors,workflow_present=workflow_present,
                workflow_usability='unverified' if workflow_present else 'missing',
                overall_accepted=False,
                limitation='automated check covers data outputs; operational handoff usability needs a separate genuine consumer')


def write_csv(path:Path,columns:tuple,rows:list):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(columns));writer.writeheader();writer.writerows(rows)


def selftest()->dict:
    tests=[]
    def record(name,valid):tests.append(dict(name=name,passed=bool(valid)))
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);base=tmp/'case';generate(44,base)
        oracle=json.loads((base/'private/oracle.json').read_text(encoding='utf-8'))
        sub=tmp/'submission';sub.mkdir()
        write_csv(sub/'ledger.csv',LEDGER,oracle['ledger']);write_csv(sub/'suppliers.csv',SUPPLIERS,oracle['suppliers'])
        put(sub/'workflow.md','Use source data, approval and posting cutoff, aggregate, then validate.\n')
        a=grade(base,sub)
        record('complete data passes while workflow review remains unverified',a['data_artifacts_passed'] and not a['overall_accepted'] and a['workflow_usability']=='unverified')
        rows=oracle['ledger']
        write_csv(sub/'ledger.csv',LEDGER,[r for r in rows if r['vendor']!='Cedar'])
        record('omitted vendor invoices fail',not grade(base,sub)['data_artifacts_passed'])
        write_csv(sub/'ledger.csv',LEDGER,rows)
        tampered=[dict(row) for row in rows];tampered[0]['paid_cents']+=1500
        write_csv(sub/'ledger.csv',LEDGER,tampered)
        record('late payment leakage fails',not grade(base,sub)['data_artifacts_passed'])
        write_csv(sub/'ledger.csv',LEDGER,rows)
        tampered=[dict(row) for row in rows];tampered[0]['total_cents']+=930
        write_csv(sub/'ledger.csv',LEDGER,tampered)
        record('future amendment leakage fails',not grade(base,sub)['data_artifacts_passed'])
        write_csv(sub/'ledger.csv',LEDGER,rows)
        write_csv(sub/'suppliers.csv',SUPPLIERS,oracle['suppliers'][1:])
        record('missing supplier summary fails',not grade(base,sub)['data_artifacts_passed'])
        write_csv(sub/'suppliers.csv',SUPPLIERS,oracle['suppliers'])
        (sub/'ledger.csv').write_text('invoice_id,vendor,total_cents,paid_cents,outstanding_cents\n'+
              f'{rows[0]["invoice_id"]},{rows[0]["vendor"]},1.5,0,1.5\n',encoding='utf-8')
        record('fractional cents fail',not grade(base,sub)['data_artifacts_passed'])
        write_csv(sub/'ledger.csv',LEDGER,rows)
        src=base/'producer/payments.json';raw=src.read_bytes();src.write_bytes(raw+b' ')
        record('mutated public source fails',not grade(base,sub)['data_artifacts_passed'])
        src.write_bytes(raw)
        record('restored public source passes',grade(base,sub)['data_artifacts_passed'])
        (sub/'workflow.md').unlink()
        record('missing workflow not called accepted',grade(base,sub)['workflow_usability']=='missing' and not grade(base,sub)['overall_accepted'])
        try:generate(44,base);record('frozen cases refuse overwrite',False)
        except FileExistsError:record('frozen cases refuse overwrite',True)
    return {'passed':all(x['passed'] for x in tests),'checks':tests,
            'scope':'generator/checker fixtures only; no autonomous or blind Agent test'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='cmd',required=True)
    g=sub.add_parser('generate');g.add_argument('--seed',type=int,required=True);g.add_argument('--out',type=Path,required=True)
    q=sub.add_parser('grade');q.add_argument('--case',type=Path,required=True);q.add_argument('--submission',type=Path,required=True)
    sub.add_parser('selftest')
    args=p.parse_args()
    try:
        result=generate(args.seed,args.out) if args.cmd=='generate' else grade(args.case,args.submission) if args.cmd=='grade' else selftest()
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,json.JSONDecodeError) as e:
        result={'error':f'{type(e).__name__}: {e}','passed':False}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result.get('passed') is False or (args.cmd=='grade' and not result.get('data_artifacts_passed')) else 0

if __name__=='__main__':sys.exit(main())
