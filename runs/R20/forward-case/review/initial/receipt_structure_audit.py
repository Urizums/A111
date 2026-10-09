#!/usr/bin/env python3
"""Structural-only validator for specifically authorized frozen call receipts.
Never emits or interprets stdout/stderr meaning or author verdict content.
"""
import base64, hashlib, json
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
LOCK=ROOT/'runs/R20/forward-case/production-lock.json'
RECEIPTS=[
'runs/R20/forward-case/production/evidence/001-preflight.json',
'runs/R20/forward-case/production/evidence/002-original-run.json',
'runs/R20/forward-case/production/evidence/003-author-receiving-check.json',
'runs/R20/forward-case/production/evidence/004-build-rejection-fixtures.json',
'runs/R20/forward-case/production/evidence/005-raw-conflict-rejection.json',
'runs/R20/forward-case/production/evidence/006-future-label-rejection.json',
'runs/R20/forward-case/production/evidence/007-clean-rerun.json',
'runs/R20/forward-case/production/evidence/008-clean-comparison.json',
'runs/R20/forward-case/production/evidence/009-shipped-helper-reproduction.json',
'runs/R20/forward-case/production/evidence/010-final-source-recheck.json',
'runs/R20/forward-case/production/evidence/011-final-readiness.json',
]
lock=json.loads(LOCK.read_text(encoding='utf-8'))
entries={e['path']:e for e in lock['files']}
out=[]
for rel in RECEIPTS:
    problems=[]
    e=entries.get(rel)
    path=ROOT/rel
    if e is None: problems.append('lock_entry')
    try: raw=path.read_bytes()
    except OSError: raw=b''; problems.append('readable')
    digest=hashlib.sha256(raw).hexdigest()
    lock_ok=bool(e and len(raw)==e['size_bytes'] and digest==e['sha256'])
    if e and not lock_ok: problems.append('locked_identity')
    try: record=json.loads(raw.decode('utf-8'))
    except Exception: record={}; problems.append('json_parse')
    schema=record.get('schema') if isinstance(record,dict) else None
    if schema!='forge-command-record/1': problems.append('schema')
    argv=record.get('argv') if isinstance(record,dict) else None
    cwd=record.get('cwd') if isinstance(record,dict) else None
    begin=record.get('begin') if isinstance(record,dict) else None
    end=record.get('end') if isinstance(record,dict) else None
    state=record.get('state') if isinstance(record,dict) else None
    code=record.get('exit_code') if isinstance(record,dict) else None
    if not isinstance(argv,list) or not argv or not all(isinstance(x,str) for x in argv): problems.append('argv')
    if not isinstance(cwd,str) or not cwd: problems.append('cwd')
    def valid_stamp(x):
        if not isinstance(x,dict) or not isinstance(x.get('utc'),str) or not isinstance(x.get('monotonic_ns'),int): return False
        try: datetime.fromisoformat(x['utc'])
        except Exception: return False
        return True
    stamps_ok=valid_stamp(begin) and valid_stamp(end)
    if not stamps_ok: problems.append('begin_end')
    if stamps_ok and end['monotonic_ns'] < begin['monotonic_ns']: problems.append('time_order')
    if state!='finished': problems.append('terminal_state')
    if not isinstance(code,int): problems.append('exit_code')
    logs={}
    for name in ('stdout','stderr'):
        txt=record.get(name) if isinstance(record,dict) else None
        b64=record.get(name+'_base64') if isinstance(record,dict) else None
        if not isinstance(txt,str) or not isinstance(b64,str):
            problems.append(name+'_fields'); data=b''; consistent=False
        else:
            try: data=base64.b64decode(b64,validate=True)
            except Exception: data=b''; problems.append(name+'_base64'); consistent=False
            else: consistent=(data.decode('utf-8',errors='replace')==txt)
            if not consistent: problems.append(name+'_text_base64_consistency')
        logs[name]={'byte_length':len(data),'sha256':hashlib.sha256(data).hexdigest(),'base64_matches_text':consistent}
    out.append({'path':rel,'locked_size_bytes':e.get('size_bytes') if e else None,'observed_size_bytes':len(raw),'locked_sha256':e.get('sha256') if e else None,'observed_sha256':digest,'locked_identity_matches':lock_ok,'schema':schema,'argv_count':len(argv) if isinstance(argv,list) else None,'cwd_present':isinstance(cwd,str) and bool(cwd),'begin_utc':begin.get('utc') if isinstance(begin,dict) else None,'end_utc':end.get('utc') if isinstance(end,dict) else None,'state':state,'exit_code':code,'logs':logs,'structural_check':'pass' if not problems else 'fail','failed_checks':problems})
summary={'schema':'authorized-command-receipt-structure-audit/1','semantic_log_content_read_or_emitted':False,'author_verdict_or_diagnosis_interpreted':False,'receipt_count':len(out),'all_structural_checks_pass':all(r['structural_check']=='pass' for r in out),'receipts':out}
print(json.dumps(summary,ensure_ascii=False,indent=2))
if not summary['all_structural_checks_pass']: raise SystemExit(1)
