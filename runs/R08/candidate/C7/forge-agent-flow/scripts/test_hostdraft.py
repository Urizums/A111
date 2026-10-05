"""Local synthetic host fixtures; not native worker or semantic evidence."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import hostbridge as h
import hostdraft as draft
import packagectl
import projectctl
import test_hostbridge as fixtures
import test_projectctl as projects

ROOT = Path(__file__).resolve().parents[1]


class HostDraftTests(unittest.TestCase):
    setUp = fixtures.BridgeTests.setUp
    prepare = fixtures.BridgeTests.prepare
    activate = fixtures.BridgeTests.activate
    snapshot = fixtures.BridgeTests.snapshot
    reply = fixtures.BridgeTests.reply
    receive = fixtures.BridgeTests.receive
    decision = fixtures.BridgeTests.decision

    def bytes(self):
        return {str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file() and not p.name.endswith('.lock')}

    def cli(self, *args):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/hostdraft.py'), *map(str,args)], capture_output=True, text=True)
        self.assertEqual(result.stderr, '')
        return result.returncode, json.loads(result.stdout)

    def package(self):
        package = packagectl.load(ROOT/'assets/example-package.json')
        self.package_path = self.root/'package.json'
        h.save(self.package_path,package)
        h.save(self.state,packagectl.start(package,{'notes':'No new commitments.'}))
        h.prepare('package',self.state,self.work,self.job,package_path=self.package_path)
        issued=h.issue(self.job);self.worker='/root/'+issued['spawn_arguments']['task_name']
        receipt=self.root/'creation.json';h.save(receipt,{'task_name':self.worker});h.accepted(self.job,receipt)

    def package_receive(self):
        self.package();path=self.reply();reply=h.read(path)
        reply['result']={'invocation_id':h.read(self.job/'request.json')['request']['invocation_id'],
            'outcome':'ok','artifacts':{'actions':[]},'evidence':[str(self.out/'result.json')]}
        h.save(path,reply);h.receive(self.job,path,self.snapshot({'completed':'fixture'}))
        return reply

    def test_reply_draft_real_refs_cannot_be_received_unchanged(self):
        self.activate();self.reply()
        source=self.job/'request.json';before=h.sha(source)
        generated=draft.write_reply(source,self.out/'draft.json',[self.out/'result.json'])
        self.assertIsNone(generated['outcome']);self.assertIsNone(generated['result'])
        self.assertEqual(generated['artifacts'],[h.reference(self.out/'result.json')])
        h.save(self.out/'reply.json',generated)
        snapshot=self.snapshot({'completed':'fixture'});prior=self.bytes()
        with self.assertRaisesRegex(h.BridgeError,'Unsupported worker task outcome'):
            h.receive(self.job,self.out/'reply.json',snapshot)
        self.assertEqual(self.bytes(),prior);self.assertEqual(h.sha(source),before)

    def test_package_draft_keeps_inner_identity_and_real_work_unfilled(self):
        self.package();value=draft.reply_draft(self.job/'request.json',flow_outcome='ok')
        self.assertIsNone(value['outcome'])
        self.assertEqual(value['result']['invocation_id'],h.read(self.job/'request.json')['request']['invocation_id'])
        self.assertEqual(value['result']['artifacts'],{'actions':[]});self.assertEqual(value['result']['evidence'],[])
        with self.assertRaises(ValueError): draft.reply_draft(self.job/'request.json',flow_outcome='unknown')

    def test_project_rejects_package_outcome_argument(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError,'only to a package'):
            draft.reply_draft(self.job/'request.json',flow_outcome='ok')

    def test_artifact_missing_outside_symlink_escape_and_self_reference(self):
        self.activate();self.reply();outside=self.root/'outside.txt';outside.write_text('outside')
        link=self.out/'escape.txt';link.symlink_to(outside)
        for path in [outside,link,self.out/'missing.txt',self.out/'reply.json',self.out]:
            with self.subTest(path=path),self.assertRaises((ValueError,OSError)):
                draft.reply_draft(self.job/'request.json',[path])

    def test_atomic_exclusive_writer_retains_existing_file_and_input(self):
        self.prepare();destination=self.out/'draft.json';destination.write_text('retain')
        before=self.bytes()
        with self.assertRaisesRegex(ValueError,'already exists'):
            draft.write_reply(self.job/'request.json',destination)
        with self.assertRaisesRegex(ValueError,'outside worker scope'):
            draft.write_reply(self.job/'request.json',self.state)
        self.assertEqual(self.bytes(),before)

    def test_request_binding_and_bound_inputs_are_not_rehashed_to_hide_drift(self):
        source=self.root/'input.txt';source.write_text('original')
        absent=self.root/'absent.txt';work=h.read(self.work)
        work['input_files']=[h.reference(source),{'path':str(absent),'sha256':None}];h.save(self.work,work)
        self.prepare();request=self.job/'request.json';before=h.sha(request)
        source.write_text('changed')
        with self.assertRaises(ValueError):draft.reply_draft(request)
        source.write_text('original');absent.write_text('appeared')
        with self.assertRaisesRegex(ValueError,'absent input appeared'):draft.reply_draft(request)
        self.assertEqual(h.sha(request),before)

    def test_request_hash_mismatch_rejected_without_output(self):
        self.prepare();path=self.job/'request.json';data=h.read(path);data['request_hash']='0'*64;h.save(path,data)
        before=self.bytes();code,result=self.cli('reply','--request',path,'--out',self.out/'draft.json')
        self.assertEqual(code,2);self.assertEqual(result['status'],'invalid');self.assertEqual(self.bytes(),before)

    def test_strict_duplicate_keys_and_nonfinite_request(self):
        self.prepare();path=self.root/'untrusted.json'
        for content in ['{"request":{},"request":{},"request_hash":"x"}','{"request":1e999,"request_hash":"x"}','{"request":NaN,"request_hash":"x"}']:
            path.write_text(content);before=self.bytes()
            code,result=self.cli('reply','--request',path,'--out',self.out/'draft.json')
            self.assertEqual((code,result['status']),(2,'invalid'));self.assertEqual(self.bytes(),before)

    def test_decision_project_rows_not_run_and_original_controller_rejects(self):
        self.activate();self.receive();prior=self.bytes();generated=draft.decision_draft(self.job,[self.out/'result.json'])
        self.assertEqual(self.bytes(),prior)
        self.assertEqual(generated['results']['acceptance_results'],{'checked':{'status':'not_run','level':'review','evidence':[h.reference(self.out/'result.json')]}})
        path=self.root/'draft.json';h.save(path,generated);before=self.bytes()
        with self.assertRaises(ValueError):draft.check_decision(self.job,path)
        self.assertEqual(self.bytes(),before)
        generated['outcome']='done';h.save(path,generated)
        with self.assertRaisesRegex(ValueError,'status must be pass'):draft.check_decision(self.job,path)

    def test_authoritative_evaluation_lock_copied_when_external_source_drifts(self):
        self.plan['acceptance'][0]['level']='runtime'
        evaluation=projects.ProjectCtlTests.evaluation_plan(self,criterion_id='checked')
        source=self.root/'eval.json';h.save(source,evaluation)
        self.state=self.root/'bound-state.json'
        projectctl.init(self.plan,self.state,evaluation,source)
        self.activate();self.receive()
        state=projectctl.load_state(self.state);expected=state['evaluation_plan_lock']['plan_hash']
        changed=deepcopy(evaluation);changed['cases'][0]['expected']['value']=99;h.save(source,changed)
        generated=draft.decision_draft(self.job)
        self.assertEqual(generated['results']['evaluation_plan_hash'],expected)
        self.assertEqual(generated['results']['acceptance_results']['checked']['level'],'runtime')
        self.assertEqual(generated['results']['acceptance_results']['checked']['status'],'not_run')

    def test_valid_reply_preflight_changes_no_bytes_or_lifecycle(self):
        self.activate();path=self.reply();before=self.bytes()
        result=draft.check_reply(self.job/'request.json',path)
        self.assertEqual(result['status'],'payload_valid');self.assertFalse(result['native_completion_checked'])
        self.assertFalse(result['call_allowed']);self.assertEqual(self.bytes(),before)
        self.assertEqual(h.read(self.job/'control.json')['phase'],'accepted')

    def test_reply_preflight_rejects_wrong_identity_wrong_sha_and_incomplete(self):
        self.activate();path=self.reply();original=h.read(path)
        for update in [{'attempt_id':'old'},{'request_hash':'0'*64},{'outcome':None},{'artifacts':[{'path':str(self.out/'result.json'),'sha256':'0'*64}]}]:
            h.save(path,{**original,**update});before=self.bytes()
            code,result=self.cli('check-reply','--request',self.job/'request.json','--reply',path)
            self.assertEqual((code,result['status']),(2,'invalid'));self.assertEqual(self.bytes(),before)

    def test_unavailable_reply_evidence_is_not_deterministic_invalid(self):
        self.activate();path=self.reply();(self.out/'result.json').unlink();before=self.bytes()
        code,result=self.cli('check-reply','--request',self.job/'request.json','--reply',path)
        self.assertEqual((code,result['status']),(2,'unavailable'));self.assertEqual(self.bytes(),before)

    def test_valid_decision_preflight_does_not_commit_then_original_commit_once(self):
        self.activate();self.receive();path=self.decision();before=self.bytes()
        result=draft.check_decision(self.job,path)
        self.assertEqual(result['status'],'controller_compatible');self.assertFalse(result['committed'])
        self.assertEqual(result['semantic_acceptance'],'not_evaluated');self.assertEqual(self.bytes(),before)
        h.commit(self.job,path);after=h.sha(self.state);h.commit(self.job,path);self.assertEqual(h.sha(self.state),after)

    def test_unreceived_committed_and_pending_journal_are_never_replayed(self):
        self.activate();before=self.bytes()
        with self.assertRaises(ValueError):draft.write_decision(self.job,self.root/'draft.json')
        self.assertEqual(self.bytes(),before)
        self.receive();h.save(self.job/'pending.json',{'fixture':'not a replayable transaction'});before=self.bytes()
        for operation in [lambda:draft.decision_draft(self.job),lambda:draft.check_decision(self.job,self.root/'none.json')]:
            with self.assertRaisesRegex(ValueError,'Pending bridge transaction'):operation()
            self.assertEqual(self.bytes(),before)
        (self.job/'pending.json').unlink();h.commit(self.job,self.decision());before=self.bytes()
        with self.assertRaisesRegex(ValueError,'uncommitted'):draft.decision_draft(self.job)
        self.assertEqual(self.bytes(),before)

    def test_decision_state_drift_and_missing_received_refs_fail_without_mutation(self):
        self.activate();self.receive();path=self.decision()
        target=self.state.read_bytes();self.state.write_text('drift');before=self.bytes()
        with self.assertRaises(ValueError):draft.decision_draft(self.job)
        self.assertEqual(self.bytes(),before);self.state.write_bytes(target)
        (self.out/'result.json').unlink();before=self.bytes()
        code,result=self.cli('check-decision','--job',self.job,'--decision',path)
        self.assertEqual((code,result['status']),(2,'unavailable'));self.assertEqual(self.bytes(),before)

    def test_decision_destination_cannot_create_declared_absent_input_or_metadata(self):
        absent=self.root/'absent.json';work=h.read(self.work);work['input_files']=[{'path':str(absent),'sha256':None}];h.save(self.work,work)
        self.activate();self.receive();before=self.bytes()
        for destination in [absent,self.job/'new-meta.json',self.state]:
            with self.subTest(destination=destination),self.assertRaises(ValueError):draft.write_decision(self.job,destination)
        self.assertEqual(self.bytes(),before)

    def test_package_decision_copies_exact_response_without_accepting_it(self):
        reply=self.package_receive();before=self.bytes();generated=draft.decision_draft(self.job)
        self.assertEqual(generated['results'],reply['result']);self.assertIsNone(generated['outcome'])
        self.assertEqual(self.bytes(),before)
        with self.assertRaises(ValueError):draft.decision_draft(self.job,[self.out/'result.json'])
        path=self.root/'draft.json';h.save(path,generated)
        with self.assertRaises(ValueError):draft.check_decision(self.job,path)

    def test_package_stale_inner_invocation_rejected_by_original_controller(self):
        self.package();path=self.reply();value=h.read(path)
        value['result']={'invocation_id':'0'*32,'outcome':'ok','artifacts':{'actions':[]},'evidence':['fixture']}
        h.save(path,value)
        # Outer preflight deliberately has the same limited scope as receive.
        self.assertEqual(draft.check_reply(self.job/'request.json',path)['status'],'payload_valid')
        h.receive(self.job,path,self.snapshot({'completed':'fixture'}))
        generated=draft.decision_draft(self.job);generated['outcome']='done';decision=self.root/'draft.json';h.save(decision,generated)
        before=self.bytes()
        with self.assertRaisesRegex(ValueError,'Stale or duplicate invocation'):draft.check_decision(self.job,decision)
        self.assertEqual(self.bytes(),before)

    def test_failed_task_cannot_be_upgraded_but_actual_rejection_preflights(self):
        self.activate();self.receive('failed');path=self.decision('done');before=self.bytes()
        with self.assertRaisesRegex(ValueError,'failed task cannot become done'):draft.check_decision(self.job,path)
        self.assertEqual(self.bytes(),before);path=self.decision('failed')
        self.assertEqual(draft.check_decision(self.job,path)['status'],'controller_compatible')


if __name__=='__main__': unittest.main()
