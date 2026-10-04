"""Controller/CLI fixtures, not live host or provider authentication."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import hostbridge as h
import packagectl
import projectctl

ROOT = Path(__file__).resolve().parents[1]


class BridgeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.out = self.root / 'out'
        self.out.mkdir()
        self.state = self.root / 'state.json'
        self.job = self.root / 'job'
        self.work = self.root / 'work.json'
        self.plan = {
            'schema_version': 'forge-project-plan/1', 'id': 'bridge_test',
            'goal': 'Produce a reviewed local result', 'deliverable_kind': 'scoped_task',
            'requirements': [{'id':'req','text':'Faithful output','origin':'explicit','basis':'Fixture task','acceptance_ids':['checked']}],
            'acceptance': [{'id':'checked','assertion':'Output checked','required':True,'level':'review'}],
            'tasks': [{'id':'task','title':'Produce result','depends_on':[],'owner':None,'write_paths':['out/'],'acceptance_ids':['checked']}],
        }
        projectctl.init(self.plan, self.state)
        h.save(self.work, {'prompt':'Transform supplied data only','inputs':{'value':7},
                           'write_paths':[str(self.out)],'reply_path':str(self.out/'reply.json')})

    def prepare(self, job=None):
        return h.prepare('project', self.state, self.work, job or self.job, task='task')

    def activate(self):
        self.prepare()
        issued = h.issue(self.job)
        self.worker = '/root/' + issued['spawn_arguments']['task_name']
        self.creation = self.root / 'creation.json'
        h.save(self.creation, {'task_name': self.worker})
        h.accepted(self.job, self.creation)

    def snapshot(self, status):
        path = self.root / ('host-' + str(len(list(self.root.glob('host-*.json')))) + '.json')
        h.save(path, {'agents':[{'agent_name':self.worker,'agent_status':status}]})
        return path

    def reply(self, outcome='done'):
        request = h.read(self.job/'request.json')
        output = self.out/'result.json'
        h.save(output, {'value':7})
        reply = {'schema_version':'forge-host-reply/1','job_id':request['request']['job_id'],
                 'attempt_id':request['request']['attempt_id'],'request_hash':request['request_hash'],
                 'outcome':outcome,'result':{'value':7},'artifacts':[h.reference(output)],
                 'reason':None if outcome=='done' else 'Actual fixture task error; inspect input before retry.'}
        path = self.out/'reply.json'
        h.save(path, reply)
        return path

    def receive(self, outcome='done'):
        path = self.reply(outcome)
        h.receive(self.job, path, self.snapshot({'completed':'Actual host final reply fixture'}))
        return path

    def decision(self, outcome='done'):
        c = h.read(self.job/'control.json')
        result = {'acceptance_results':{'checked':{'status':'pass','level':'review','evidence':[h.reference(self.out/'result.json')]}}}
        d = {'schema_version':'forge-host-decision/1','request_hash':c['request_hash'],
             'reply_sha256':c['reply_ref']['sha256'],'outcome':outcome,
             'results':result if outcome=='done' else None,
             'reason':None if outcome=='done' else 'Observed task error; inspect and retry in a new attempt.'}
        path = self.root/'decision.json'
        h.save(path, d)
        return path

    def test_project_completion_and_duplicate_commit_advance_once(self):
        self.activate()
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'running')
        h.observe(self.job, self.snapshot('running'))
        self.receive()
        decision = self.decision()
        h.commit(self.job, decision)
        state_hash = h.sha(self.state)
        self.assertTrue(h.commit(self.job, decision)['duplicate'])
        self.assertEqual(h.sha(self.state), state_hash)
        self.assertEqual(h.reconcile(self.job)['action'],'reuse_record')
        task = projectctl.load_state(self.state)['tasks']['task']
        self.assertEqual((task['status'],len(task['attempts'])),('done',1))

    def test_prepare_is_idempotent_and_issue_is_not_automatically_repeated(self):
        first = self.prepare()
        self.assertTrue(self.prepare()['reused'])
        self.assertEqual(first['attempt_id'],self.prepare()['attempt_id'])
        h.issue(self.job)
        with self.assertRaisesRegex(h.BridgeError,'already have happened'):
            h.issue(self.job)
        self.assertEqual(h.reconcile(self.job)['action'],'reconcile_host_before_any_retry')

    def test_other_job_cannot_own_unresolved_checkpoint(self):
        self.prepare()
        with self.assertRaisesRegex(h.BridgeError,'unresolved host job'):
            self.prepare(self.root/'other-job')
        self.assertEqual(len(projectctl.load_state(self.state)['tasks']['task']['attempts']),1)

    def test_changed_input_cannot_reuse_prepared_job(self):
        self.prepare()
        work = h.read(self.work)
        work['inputs']['value'] = 8
        h.save(self.work, work)
        with self.assertRaisesRegex(h.BridgeError,'inputs changed'):
            self.prepare()

    def test_worker_scope_cannot_include_controller_metadata_or_exceed_plan(self):
        for scope in [self.root,self.root/'unassigned']:
            with self.subTest(scope=scope):
                w=h.read(self.work);w['write_paths']=[str(scope)];w['reply_path']=str(scope/'reply.json');h.save(self.work,w)
                with self.assertRaises(h.BridgeError):
                    self.prepare()
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'todo')

    def test_wrong_creation_worker_does_not_record_acceptance(self):
        self.prepare();h.issue(self.job)
        p=self.root/'wrong.json';h.save(p,{'task_name':'/root/unrelated'})
        with self.assertRaisesRegex(h.BridgeError,'does not bind'):
            h.accepted(self.job,p)
        self.assertEqual(h.reconcile(self.job)['phase'],'dispatching')

    def test_missing_worker_status_is_not_failure(self):
        self.activate()
        p=self.root/'missing.json';h.save(p,{'agents':[]})
        with self.assertRaisesRegex(h.BridgeError,'reconcile rather than infer'):
            h.observe(self.job,p)
        self.assertEqual(h.reconcile(self.job)['phase'],'accepted')

    def test_stale_reply_and_invalid_artifact_are_rejected(self):
        self.activate()
        path=self.reply();original=h.read(path)
        for change in ['attempt','hash','scope']:
            reply=deepcopy(original)
            if change=='attempt':reply['attempt_id']='old_attempt'
            elif change=='hash':reply['artifacts'][0]['sha256']='0'*64
            else:
                outside=self.root/'outside.json';h.save(outside,{'value':7});reply['artifacts']=[h.reference(outside)]
            h.save(path,reply)
            with self.subTest(change=change),self.assertRaises((h.BridgeError, h.runledger.LedgerError)):
                h.receive(self.job,path,self.snapshot({'completed':'finished'}))
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'running')

    def test_actual_completion_observation_required(self):
        self.activate()
        with self.assertRaisesRegex(h.BridgeError,'completion observation'):
            h.receive(self.job,self.reply(),self.snapshot('running'))

    def test_completed_context_without_separate_running_poll_is_supported(self):
        self.activate();self.receive()
        self.assertEqual(h.reconcile(self.job)['ledger']['state'],'completed')

    def test_decision_cannot_bind_to_a_different_reply(self):
        self.activate();self.receive()
        path=self.decision();d=h.read(path);d['reply_sha256']='0'*64;h.save(path,d)
        with self.assertRaisesRegex(h.BridgeError,'binding mismatch'):
            h.commit(self.job,path)
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'running')

    def test_drifted_artifact_prevents_finish(self):
        self.activate();self.receive();decision=self.decision()
        h.save(self.out/'result.json',{'value':8})
        with self.assertRaises(h.runledger.LedgerError):h.commit(self.job,decision)
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'running')

    def test_external_checkpoint_change_is_not_overwritten(self):
        self.activate();self.receive();decision=self.decision()
        state=h.read(self.state);state['revision']+=1;h.save(self.state,state);changed=h.sha(self.state)
        with self.assertRaisesRegex(h.BridgeError,'Checkpoint moved'):h.commit(self.job,decision)
        self.assertEqual(changed,h.sha(self.state))

    def test_interrupted_commit_recovers_exactly_once(self):
        self.activate();self.receive();decision=self.decision()
        original_save=h.save
        def crash_after_target(path,value):
            original_save(path,value)
            if Path(path)==self.state:raise OSError('Controlled crash after checkpoint persisted')
        with mock.patch.object(h,'save',side_effect=crash_after_target):
            with self.assertRaises(OSError):h.commit(self.job,decision)
        self.assertTrue((self.job/'pending.json').exists())
        self.assertEqual(h.reconcile(self.job)['phase'],'committed')
        self.assertFalse((self.job/'pending.json').exists())
        self.assertEqual(len(projectctl.load_state(self.state)['tasks']['task']['attempts']),1)
        self.assertTrue(h.commit(self.job,decision)['duplicate'])

    def test_pending_commit_recovery_rechecks_output_evidence(self):
        self.activate();self.receive();decision=self.decision()
        original_recover=h.recover
        def stop_on_pending(job):
            if (job/'pending.json').exists():raise OSError('Crash before applying journal')
            original_recover(job)
        with mock.patch.object(h,'recover',side_effect=stop_on_pending):
            with self.assertRaises(OSError):h.commit(self.job,decision)
        h.save(self.out/'result.json',{'value':8})
        with self.assertRaises(h.runledger.LedgerError):h.reconcile(self.job)
        self.assertTrue((self.job/'pending.json').exists())
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'running')

    def test_failed_task_is_not_done_and_new_attempt_is_bounded(self):
        self.activate();self.receive('failed')
        with self.assertRaisesRegex(h.BridgeError,'failed task cannot become done'):h.commit(self.job,self.decision())
        h.commit(self.job,self.decision('failed'))
        first=projectctl.load_state(self.state)['tasks']['task']['attempts'][0]['attempt_id']
        next_job=self.root/'retry-job'
        work=h.read(self.work);work['write_paths']=[str(self.out/'retry')];work['reply_path']=str(self.out/'retry/reply.json');h.save(self.work,work)
        prepared=self.prepare(next_job)
        self.assertNotEqual(prepared['attempt_id'],first)
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['repair_attempts'],1)
        with self.assertRaisesRegex(h.BridgeError,'Checkpoint moved'):h.receive(self.job,self.out/'reply.json',self.snapshot({'completed':'late'}))

    def test_fixture_host_interruption_retains_attempt_and_refuses_late_reply(self):
        self.activate();h.observe(self.job,self.snapshot('running'))
        h.terminate(self.job,self.snapshot('interrupted'),'Host interrupted; reconcile files before retry.')
        self.assertEqual(h.reconcile(self.job)['phase'],'terminated')
        with self.assertRaisesRegex(h.BridgeError,'current phase'):
            h.receive(self.job,self.reply(),self.snapshot({'completed':'late'}))
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'failed')

    def test_fixture_creation_rejection_is_local_failed_attempt_not_completion(self):
        self.prepare();h.issue(self.job)
        path=self.root/'rejection.json';h.save(path,{'isError':True,'error':'Fixture unavailable capacity'})
        h.rejected(self.job,path,'Actual creation error receipt required; inspect capacity before retry.')
        self.assertEqual(h.reconcile(self.job)['ledger']['state'],'failed')
        self.assertIsNone(h.read(self.job/'control.json')['worker'])
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'failed')

    def test_ledger_cannot_disagree_with_committed_phase(self):
        self.activate();self.receive();h.commit(self.job,self.decision())
        h.save(self.job/'ledger.json',{'schema_version':h.runledger.SCHEMA,'created_at':h.runledger.now(),'jobs':{}})
        with self.assertRaisesRegex(h.BridgeError,'contradicts'):h.reconcile(self.job)

    def test_package_advance_uses_exact_worker_response_and_preserves_package(self):
        package=packagectl.load(ROOT/'assets/example-package.json')
        package_path=self.root/'package.json';h.save(package_path,package)
        package_hash=h.sha(package_path)
        h.save(self.state,packagectl.start(package,{'notes':'No new commitments.'}))
        h.prepare('package',self.state,self.work,self.job,package_path=package_path)
        issued=h.issue(self.job);self.worker='/root/'+issued['spawn_arguments']['task_name']
        creation=self.root/'creation.json';h.save(creation,{'task_name':self.worker});h.accepted(self.job,creation)
        path=self.reply();reply=h.read(path)
        reply['result']={'invocation_id':h.read(self.job/'request.json')['request']['invocation_id'],
                         'outcome':'ok','artifacts':{'actions':[]},'evidence':[str(self.out/'result.json')]}
        h.save(path,reply);h.receive(self.job,path,self.snapshot({'completed':'finished'}))
        decision=self.decision();d=h.read(decision);d['results']=reply['result'];h.save(decision,d)
        h.commit(self.job,decision)
        self.assertEqual((h.read(self.state)['flow_state']['status'],h.read(self.state)['flow_state']['steps']),('completed',1))
        self.assertEqual(h.sha(package_path),package_hash)

    def package_rejected_context(self):
        package = packagectl.load(ROOT/'assets/example-package.json')
        package_path = self.root/'package.json'; h.save(package_path, package)
        h.save(self.state, packagectl.start(package, {'notes':'No commitments.'}))
        h.prepare('package',self.state,self.work,self.job,package_path=package_path)
        issued=h.issue(self.job); self.worker='/root/'+issued['spawn_arguments']['task_name']
        creation=self.root/'creation.json'; h.save(creation,{'task_name':self.worker}); h.accepted(self.job,creation)
        # Genuine defect class: business object is not a complete Flow response.
        self.receive()
        return package_path, issued

    def test_package_worker_receives_complete_inner_response_contract(self):
        _, issued = self.package_rejected_context()
        request = h.read(self.job/'request.json')['request']
        contract = request['reply_contract']['result']
        self.assertEqual(contract['required_keys'],['invocation_id','outcome','artifacts','evidence'])
        self.assertEqual(contract['invocation_id'],request['invocation_id'])
        self.assertEqual(contract['outcomes'],request['dispatch']['outcomes'])
        self.assertIn(request['invocation_id'],issued['spawn_arguments']['message'])
        self.assertIn('not put a bare business object',issued['spawn_arguments']['message'])

    def test_bad_package_reply_can_close_as_failed_without_advancing_and_retry_is_bounded(self):
        package_path, _ = self.package_rejected_context()
        state_hash = h.sha(self.state)
        good = self.decision(); d=h.read(good); d['results']=h.read(self.out/'reply.json')['result']; h.save(good,d)
        with self.assertRaisesRegex(h.flowctl.FlowError,'Response needs exactly'):h.commit(self.job,good)
        for attempt in range(3):
            decision=self.decision('failed'); committed=h.commit(self.job,decision)
            self.assertEqual(h.sha(self.state),state_hash)
            self.assertFalse(committed['commit']['target_result']['checkpoint_advanced'])
            self.assertEqual(committed['coordinator_outcome'],'failed')
            self.assertTrue(h.commit(self.job,decision)['duplicate'])
            self.assertEqual(h.reconcile(self.job)['action'],'reconcile_effects_before_new_package_attempt')
            next_job=self.root/f'retry-{attempt}'; next_out=self.root/f'out-{attempt}';next_out.mkdir()
            work=h.read(self.work);work['write_paths']=[str(next_out)];work['reply_path']=str(next_out/'reply.json');h.save(self.work,work)
            if attempt==2:
                with self.assertRaisesRegex(h.BridgeError,'retry budget exhausted'):
                    h.prepare('package',self.state,self.work,next_job,package_path=package_path)
                break
            h.prepare('package',self.state,self.work,next_job,package_path=package_path)
            self.job=next_job;self.out=next_out
            issued=h.issue(self.job);self.worker='/root/'+issued['spawn_arguments']['task_name']
            creation=self.root/f'creation-{attempt}.json';h.save(creation,{'task_name':self.worker});h.accepted(self.job,creation);self.receive()
        self.assertEqual(h.sha(self.state),state_hash)
        self.assertEqual(h.read(self.job/'control.json')['repair_attempts'],2)

    def test_package_rejection_requires_null_results_and_actual_reason(self):
        self.package_rejected_context();path=self.decision('failed');original=h.read(path)
        for update in [{'results':{}},{'reason':None},{'outcome':'unknown'}]:
            d={**original,**update};h.save(path,d)
            with self.assertRaisesRegex(h.BridgeError,'Package rejection needs'):h.commit(self.job,path)
        self.assertEqual(h.read(self.job/'control.json')['phase'],'received')

    def _assert_pending_package_commit_guard(self, legacy=False):
        package_path, _ = self.package_rejected_context()
        # Replace the not-yet-committed business-only reply with a valid fixture
        # in a fresh receive context; no saved worker evidence is rewritten.
        self.job=self.root/'valid-job';self.out=self.root/'valid-out';self.out.mkdir()
        rejected=self.root/'rejection.json'
        old_job=self.root/'job';c=h.read(old_job/'control.json')
        h.save(rejected,{'schema_version':'forge-host-decision/1','request_hash':c['request_hash'],
                         'reply_sha256':c['reply_ref']['sha256'],'outcome':'failed','results':None,'reason':'Bad response; reconcile before fresh job.'})
        h.commit(old_job,rejected)
        work=h.read(self.work);work['write_paths']=[str(self.out)];work['reply_path']=str(self.out/'reply.json');h.save(self.work,work)
        h.prepare('package',self.state,self.work,self.job,package_path=package_path)
        issued=h.issue(self.job);self.worker='/root/'+issued['spawn_arguments']['task_name']
        creation=self.root/'valid-creation.json';h.save(creation,{'task_name':self.worker});h.accepted(self.job,creation)
        path=self.reply();reply=h.read(path)
        reply['result']={'invocation_id':h.read(self.job/'request.json')['request']['invocation_id'],
                         'outcome':'ok','artifacts':{'actions':[]},'evidence':[str(self.out/'result.json')]}
        h.save(path,reply);h.receive(self.job,path,self.snapshot({'completed':'Fixture completed'}))
        decision=self.decision();d=h.read(decision);d['results']=reply['result'];h.save(decision,d)
        before=h.sha(self.state);original=h.recover
        def stop(job):
            if (job/'pending.json').exists():raise OSError('Fixture stop before journal apply')
            original(job)
        with mock.patch.object(h,'recover',side_effect=stop):
            with self.assertRaises(OSError):h.commit(self.job,decision)
        if legacy:
            tx=h.read(self.job/'pending.json')
            tx['guards']=[ref for ref in tx['guards'] if ref['path']!=str(package_path)]
            h.save(self.job/'pending.json',tx)
        original_bytes=package_path.read_bytes()
        package_path.write_bytes(original_bytes+b'\n')
        with self.assertRaises(h.runledger.LedgerError):h.reconcile(self.job)
        self.assertEqual(h.sha(self.state),before)
        self.assertTrue((self.job/'pending.json').exists())
        package_path.write_bytes(original_bytes)
        self.assertEqual(h.reconcile(self.job)['phase'],'committed')
        self.assertEqual(h.read(self.state)['flow_state']['steps'],1)
        self.assertTrue(h.commit(self.job,decision)['duplicate'])

    def test_pending_package_commit_rechecks_package_before_any_checkpoint_write(self):
        self._assert_pending_package_commit_guard()

    def test_legacy_pending_package_journal_still_checks_immutable_package_binding(self):
        self._assert_pending_package_commit_guard(legacy=True)

    def test_cli_errors_are_machine_readable_with_next_action(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/hostbridge.py'),'reconcile','--job',str(self.root/'absent')],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        parsed=json.loads(result.stdout)
        self.assertEqual(parsed['status'],'reconcile_required')
        self.assertFalse(parsed['automatic_host_call'])

    def test_two_prepare_processes_cannot_reserve_same_checkpoint(self):
        processes=[]
        for name in ['one','two']:
            args=[sys.executable,str(ROOT/'scripts/hostbridge.py'),'prepare','--kind','project',
                  '--state',str(self.state),'--task','task','--work',str(self.work),'--job',str(self.root/name)]
            processes.append(subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True))
        codes=[]
        for process in processes:
            process.communicate(timeout=10);codes.append(process.returncode)
        self.assertEqual(sorted(codes),[0,2])
        self.assertEqual(len(projectctl.load_state(self.state)['tasks']['task']['attempts']),1)

    def test_declared_input_file_drift_and_newly_appeared_absent_input_are_not_reused(self):
        path=self.root/'input.json';h.save(path,{'value':7})
        work=h.read(self.work);work['input_files']=[h.reference(path)];h.save(self.work,work)
        self.prepare();h.save(path,{'value':8})
        with self.assertRaises(h.runledger.LedgerError):h.reconcile(self.job)
        h.save(path,{'value':7})
        self.assertEqual(h.reconcile(self.job)['phase'],'prepared')
        missing=self.root/'missing.json';work['input_files']=[{'path':str(missing),'sha256':None}];h.save(self.work,work)
        # A different input binding cannot overwrite the existing request.
        with self.assertRaisesRegex(h.BridgeError,'inputs changed'):self.prepare()

    def test_raw_worker_reply_is_preserved_in_private_receipt_copy(self):
        self.activate();reply=self.receive();stored=h.read(self.job/'control.json')['reply_ref']
        self.assertNotEqual(Path(stored['path']),reply)
        self.assertEqual(Path(stored['path']).read_bytes(),reply.read_bytes())

    def test_retry_cannot_overwrite_old_output_evidence(self):
        self.activate();self.receive('failed');h.commit(self.job,self.decision('failed'))
        with self.assertRaisesRegex(h.BridgeError,'overwrite retained'):
            self.prepare(self.root/'unsafe-retry')


if __name__=='__main__':
    unittest.main()
