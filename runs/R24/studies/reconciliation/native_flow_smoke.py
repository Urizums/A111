#!/usr/bin/env python3
"""Execute a bounded R24 Flow IR slice with the existing repo flowctl runtime.

Requires a real checkout of Urizums/A111. A missing runtime is BLOCKED, not PASS.
This drives two nodes with local deterministic receipts, not an actual Agent.
"""
from __future__ import annotations
import argparse
import csv
import importlib
import json
import sys
import tempfile
from pathlib import Path


def run(repo: Path) -> dict:
    repo = repo.resolve()
    runtime = repo / 'skills/forge-agent-flow/scripts'
    if not (runtime/'flowctl.py').is_file():
        return {'status': 'blocked', 'reason': 'Existing flowctl.py is not present in this checkout',
                'performed_native_check': False}
    sys.path.insert(0,str(runtime))
    import flowctl
    study = Path(__file__).resolve().parent
    sys.path.insert(0,str(study))
    from flow_builder import make_flow
    from rehearsal import generate, compute, grade, LEDGER, SUPPLIERS
    with tempfile.TemporaryDirectory(prefix='forge-r24-ir-') as tmp:
        root=Path(tmp);case=root/'study'
        generate(7211,case)
        public=case/'producer'
        spec,inputs=make_flow(public)
        formal=flowctl.validate(spec)
        if not formal['valid']:
            return {'status':'fail','where':'flowctl.validate','errors':formal['errors']}
        compiled=flowctl.compile_flow(spec,root/'compiled')
        blocked_initial=flowctl.pending(spec,flowctl.start(spec,inputs))
        if blocked_initial.get('status')!='blocked' or 'workspace' not in blocked_initial.get('reason',''):
            return {'status':'fail','where':'workspace not blocked without evidence', 'observed':blocked_initial}
        # In this fixture alone, local-file execution is witnessed by this very Python run.
        spec,inputs=make_flow(public,workspace_receipt='local Python execution on generated temporary inputs')
        if not flowctl.validate(spec)['valid']:
            return {'status':'fail','where':'workspace-attested flow validation'}
        state=flowctl.start(spec,inputs)
        issued=flowctl.pending(spec,state)
        if issued['status']!='ready' or issued['node']!='produce':
            return {'status':'fail','where':'produce is not ready','observed':issued}
        # The following producer is deterministic author code. It does not demonstrate LLM autonomy.
        invoices=json.loads((public/'invoices.json').read_text(encoding='utf-8'))
        amendments=json.loads((public/'amendments.json').read_text(encoding='utf-8'))
        payments=json.loads((public/'payments.json').read_text(encoding='utf-8'))
        brief=(public/'brief.md').read_text(encoding='utf-8')
        cutoff=brief.split('as of ',1)[1].split('.',1)[0]
        ledger,suppliers=compute(invoices,amendments,payments,cutoff)
        submitted=root/'submission';submitted.mkdir()
        for filename,cols,rows in [('ledger.csv',LEDGER,ledger),('suppliers.csv',SUPPLIERS,suppliers)]:
            with (submitted/filename).open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(cols));writer.writeheader();writer.writerows(rows)
        (submitted/'workflow.md').write_text('Read the business cutoff. Take only approved effective revisions and posted in-window payments. Compute every invoice; sum each supplier, including zero balances. Export and verify both CSVs.\n',encoding='utf-8')
        reply={'invocation_id':issued['invocation_id'],'outcome':'ok',
               'artifacts':{'tables':{name:str(submitted/name) for name in ('ledger.csv','suppliers.csv','workflow.md')}},
               'evidence':['Actual two CSV and workflow files written locally from public data']}
        wrong=dict(reply,invocation_id='stale-or-fake')
        try:
            flowctl.advance(spec,state,wrong)
            return {'status':'fail','where':'stale invocation accepted'}
        except flowctl.FlowError:
            pass
        state=flowctl.advance(spec,state,reply)
        issued=flowctl.pending(spec,state)
        if issued['status']!='ready' or issued['node']!='audit_data':
            return {'status':'fail','where':'audit is not ready','observed':issued}
        check=grade(case,submitted)
        if not check['data_artifacts_passed'] or check['overall_accepted']:
            return {'status':'fail','where':'data gate or handoff overclaim','observed':check}
        state=flowctl.advance(spec,state,{'invocation_id':issued['invocation_id'],'outcome':'ok',
                             'artifacts':{'audit':{'data_artifacts_passed':True,'workflow_usability':'unverified'}},
                             'evidence':['Recomputed against private deterministic oracle for researcher only']})
        after=flowctl.pending(spec,state)
        if after['status']!='blocked' or 'receiver' not in after.get('reason',''):
            return {'status':'fail','where':'independent receiving capability not enforced','observed':after}
        return {'status':'pass','performed_native_check':True,'native_valid':True,
                'compiled_nodes':compiled['nodes'],'locally_replayed_nodes':2,
                'pending_receiver':'blocked', 'terminal_business_acceptance':False,
                'wrong_invocation_rejected':True,
                'limitation':'Local author-coded producer/audit; no independent Agent or real receiver' }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[4])
    args=p.parse_args()
    try:out=run(args.repo)
    except (OSError,ValueError,KeyError,ImportError,TypeError) as e:
        out={'status':'fail','error':f'{type(e).__name__}: {e}'}
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out['status']=='pass' else 2

if __name__=='__main__':raise SystemExit(main())
