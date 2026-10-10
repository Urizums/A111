#!/usr/bin/env python3
"""Execute a bounded R24 Flow IR slice with the existing repo flowctl runtime.

Requires a real checkout of Urizums/A111. A missing runtime is BLOCKED, not PASS.
This drives two nodes with local deterministic receipts, not an actual Agent.
"""
from __future__ import annotations
import argparse
import json
import subprocess
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
    from flow_builder import make_flow, verify_public_source
    from rehearsal import generate, grade
    from receiver_packet import build as make_receiver_packet, verify as verify_receiver_packet
    with tempfile.TemporaryDirectory(prefix='forge-r24-ir-') as tmp:
        root=Path(tmp);case=root/'study'
        generate(7211,case)
        public=case/'producer'
        spec,inputs=make_flow(public)
        if not verify_public_source(inputs['source_bundle'])['passed']:
            return {'status':'fail','where':'initial frozen public input identity'}
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
        # Producer is a separate public-input-only author program.  It never
        # imports the private oracle or the grader, but is not an LLM Agent.
        if not verify_public_source(inputs['source_bundle'])['passed']:
            return {'status':'fail','where':'source changed before dispatch'}
        submitted=root/'submission'
        proc=subprocess.run([sys.executable,str(study/'public_producer.py'),
                             '--producer',str(public),'--out',str(submitted)],
                            text=True,capture_output=True,check=False)
        if proc.returncode:
            return {'status':'fail','where':'public input producer','returncode':proc.returncode,
                    'stderr':proc.stderr[-1000:]}
        if not verify_public_source(inputs['source_bundle'])['passed']:
            return {'status':'fail','where':'source changed during production'}
        first_check=grade(case,submitted)
        if not first_check['data_artifacts_passed']:
            return {'status':'fail','where':'produced CSV failed first gate','errors':first_check['errors']}
        reply={'invocation_id':issued['invocation_id'],'outcome':'ok',
               'artifacts':{'tables':{name:str(submitted/name) for name in ('ledger.csv','suppliers.csv','workflow.md')}},
               'evidence':['Actual two CSV and workflow files written locally from public data']}
        wrong=dict(reply,invocation_id='stale-or-fake')
        try:
            flowctl.advance(spec,state,wrong)
            return {'status':'fail','where':'stale invocation accepted'}
        except flowctl.FlowError:
            pass
        previous=state
        state=flowctl.advance(spec,state,reply)
        try:
            flowctl.advance(spec,state,reply)
            return {'status':'fail','where':'duplicate old invocation accepted'}
        except flowctl.FlowError:
            pass
        issued=flowctl.pending(spec,state)
        if issued['status']!='ready' or issued['node']!='audit_data':
            return {'status':'fail','where':'audit is not ready','observed':issued}
        check=grade(case,submitted)
        if not verify_public_source(inputs['source_bundle'])['passed']:
            return {'status':'fail','where':'source changed during review'}
        if not check['data_artifacts_passed'] or check['overall_accepted']:
            return {'status':'fail','where':'data gate or handoff overclaim','observed':check}
        # Transfer only required originals and actual deliverables. Review is still blocked.
        receiver_packet = root / 'receiver_packet'
        packet_created = make_receiver_packet(public, submitted, receiver_packet,
                                               inputs['source_bundle'])
        packet_check = verify_receiver_packet(receiver_packet)
        if not packet_created['passed'] or not packet_check['passed']:
            return {'status':'fail','where':'receiver packet integrity','observed':packet_check}
        # A new interpreter reads only the sanitized receiver packet, not case/private.
        # This is a distinct deterministic algorithm, not an independent AI consumer.
        cold_receipt = root / 'cold_receiver_receipt.json'
        cold = subprocess.run([sys.executable, '-I', str(study / 'cold_receiver.py'),
                               '--packet', str(receiver_packet), '--receipt', str(cold_receipt)],
                              cwd=root, capture_output=True, text=True, check=False)
        if cold.returncode:
            return {'status':'fail','where':'packet-only cold data replay',
                    'returncode':cold.returncode, 'stderr':cold.stderr[-1200:],
                    'stdout':cold.stdout[-1200:]}
        replay = json.loads(cold_receipt.read_text(encoding='utf-8'))
        if not replay.get('receiving_checks_passed') or replay.get('business_acceptance') != 'unverified':
            return {'status':'fail','where':'cold replay falsely accepted or rejected',
                    'observed':replay}
        state=flowctl.advance(spec,state,{'invocation_id':issued['invocation_id'],'outcome':'ok',
                             'artifacts':{'audit':{'data_artifacts_passed':True,'workflow_usability':'unverified',
                                                    'receiver_packet':str(receiver_packet),
                                                    'packet_integrity_passed':True,
                                                    'cold_data_replay_passed':True,
                                                    'workflow_semantic_usability':'unverified'}},
                             'evidence':['Recomputed against private deterministic oracle for researcher only']})
        after=flowctl.pending(spec,state)
        if after['status']!='blocked' or 'receiver' not in after.get('reason',''):
            return {'status':'fail','where':'independent receiving capability not enforced','observed':after}
        return {'status':'pass','performed_native_check':True,'native_valid':True,
                'compiled_nodes':compiled['nodes'],'locally_replayed_nodes':2,
                'pending_receiver':'blocked', 'terminal_business_acceptance':False,
                'wrong_invocation_rejected':True, 'duplicate_invocation_rejected':True,
                'separate_public_source_producer':True, 'source_guard_observed':True,
                'sanitized_receiver_packet_verified': True, 'receiver_files': packet_check['files_checked'],
                'cold_packet_replay_passed': True, 'cold_workflow_usability': 'unverified',
                'limitation':'Local public-source-only author producer and researcher grader; no independent Agent or real receiver' }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3])
    args=p.parse_args()
    try:out=run(args.repo)
    except (OSError,ValueError,KeyError,ImportError,TypeError) as e:
        out={'status':'fail','error':f'{type(e).__name__}: {e}'}
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out['status']=='pass' else 2

if __name__=='__main__':raise SystemExit(main())
