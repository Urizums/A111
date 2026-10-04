"""Persistent-driver failure fixtures; these are not live host observations."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

import hostbridge as h
import hostdriver as d
import packagectl
import projectctl
import test_hostbridge as fixtures

ROOT = Path(__file__).resolve().parents[1]


class DriverTests(unittest.TestCase):
    setUp = fixtures.BridgeTests.setUp
    snapshot = fixtures.BridgeTests.snapshot
    reply = fixtures.BridgeTests.reply
    decision = fixtures.BridgeTests.decision

    def setup_driver(self, **kwargs):
        self.driver = self.root / 'driver'
        self.works = self.root / 'works.json'
        h.save(self.works, {'task':str(self.work)})
        return d.init(self.driver, 'project', self.state, self.works, '/root', **kwargs)

    def next(self):
        action = d.advance(self.driver)
        if action.get('action'):
            self.job = Path(action['action']['job_dir'])
        return action

    def activate(self):
        self.setup_driver()
        action = self.next()['action']
        self.worker = '/root/' + action['arguments']['task_name']
        d.claim(self.driver, action['action_id'])
        self.creation = self.root/'creation.json'
        h.save(self.creation, {'task_name':self.worker})
        d.ack(self.driver, action['action_id'], self.creation)
        return action

    def received(self, outcome='done'):
        self.activate()
        self.reply(outcome)
        query = self.next()['action']
        d.claim(self.driver, query['action_id'])
        d.ack(self.driver, query['action_id'], self.snapshot({'completed':'Fixture completed'}))
        return self.next()['action']

    def test_ready_project_selection_and_repeated_next_are_same_action(self):
        self.setup_driver(); first=self.next(); second=self.next()
        self.assertEqual(first['action'],second['action'])
        self.assertFalse(first['call_allowed'])
        self.assertEqual(first['action']['tool'],'collaboration.spawn_agent')
        self.assertEqual(h.read(self.job/'request.json')['request']['target_binding']['task_id'],'task')
        self.assertEqual(len(projectctl.load_state(self.state)['tasks']['task']['attempts']),1)

    def test_repeated_claim_never_grants_another_call(self):
        self.setup_driver(); action=self.next()['action']
        self.assertTrue(d.claim(self.driver,action['action_id'])['call_allowed'])
        self.assertFalse(d.claim(self.driver,action['action_id'])['call_allowed'])
        self.assertEqual(d.load(self.driver)['host_call_claims'],1)

    def test_missing_creation_ack_uses_status_origin_and_no_second_spawn(self):
        self.setup_driver(); action=self.next()['action']
        self.worker='/root/'+action['arguments']['task_name'];d.claim(self.driver,action['action_id'])
        query=self.next()['action'];self.assertEqual(query['purpose'],'reconcile_missing_creation_receipt')
        d.claim(self.driver,query['action_id']);d.ack(self.driver,query['action_id'],self.snapshot('running'))
        c=h.control(self.job);self.assertEqual(c['acceptance_origin'],'host_status_reconciliation')
        self.assertIn('agents',h.read(c['acceptance_ref']['path']))
        records=d.load(self.driver)['actions'];self.assertEqual(records[action['action_id']]['status'],'reconciled')
        self.assertEqual(sum(h.read(r['payload_ref']['path'])['kind']=='spawn' for r in records.values()),1)

    def test_unknown_status_is_retained_and_never_causes_retry_or_failure(self):
        self.setup_driver();spawn=self.next()['action'];self.worker='/root/'+spawn['arguments']['task_name']
        d.claim(self.driver,spawn['action_id']);query=self.next()['action'];d.claim(self.driver,query['action_id'])
        for raw in [{'agents':[]},{'agents':[{'agent_name':self.worker,'agent_status':'unknown'}]}]:
            path=self.root/'unknown.json';h.save(path,raw)
            with self.assertRaises(h.BridgeError):d.ack(self.driver,query['action_id'],path)
        self.assertEqual(h.control(self.job)['phase'],'dispatching')
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'running')
        self.assertEqual(len(d.load(self.driver)['rejected_imports']),2)
        self.assertEqual(self.next()['action']['kind'],'query')

    def test_wrong_creation_receipt_rejected_without_acceptance(self):
        self.setup_driver();a=self.next()['action'];d.claim(self.driver,a['action_id'])
        path=self.root/'wrong.json';h.save(path,{'task_name':'/root/other'})
        with self.assertRaises(h.BridgeError):d.ack(self.driver,a['action_id'],path)
        self.assertEqual(h.control(self.job)['phase'],'dispatching')

    def test_old_action_ack_cannot_replace_reconciliation(self):
        self.setup_driver();a=self.next()['action'];d.claim(self.driver,a['action_id']);self.next()
        p=self.root/'late.json';h.save(p,{'task_name':'/root/'+a['arguments']['task_name']})
        with self.assertRaisesRegex(h.BridgeError,'Stale'):d.ack(self.driver,a['action_id'],p)

    def test_unclaimed_and_unknown_actions_rejected(self):
        self.setup_driver();a=self.next()['action'];p=self.root/'raw.json';h.save(p,{})
        with self.assertRaisesRegex(h.BridgeError,'unclaimed'):d.ack(self.driver,a['action_id'],p)
        with self.assertRaisesRegex(h.BridgeError,'Unknown'):d.claim(self.driver,'missing')

    def test_duplicate_ack_same_bytes_does_not_change_checkpoint(self):
        spawn=self.activate();before=h.sha(self.state)
        self.assertTrue(d.ack(self.driver,spawn['action_id'],self.creation)['duplicate'])
        self.assertEqual(h.sha(self.state),before)
        h.save(self.creation,{'task_name':self.worker,'extra':'different'})
        with self.assertRaisesRegex(h.BridgeError,'Different ack'):d.ack(self.driver,spawn['action_id'],self.creation)

    def test_completed_worker_requires_source_review_before_commit(self):
        review=self.received()
        self.assertEqual(review['kind'],'review')
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'running')
        self.assertEqual(h.control(self.job)['phase'],'received')
        d.claim(self.driver,review['action_id']);d.ack(self.driver,review['action_id'],self.decision(),True)
        self.assertEqual(self.next()['phase'],'completed')
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'done')
        before=h.sha(self.state);self.next();self.assertEqual(h.sha(self.state),before)

    def test_failed_task_stops_without_automatic_retry(self):
        review=self.received('failed');d.claim(self.driver,review['action_id'])
        d.ack(self.driver,review['action_id'],self.decision('failed'),True)
        self.assertEqual(self.next()['phase'],'blocked')
        self.assertEqual(len(projectctl.load_state(self.state)['tasks']['task']['attempts']),1)

    def test_actual_host_failure_fixture_closes_and_stops(self):
        self.activate();q=self.next()['action'];d.claim(self.driver,q['action_id'])
        d.ack(self.driver,q['action_id'],self.snapshot('failed'))
        self.assertEqual(self.next()['phase'],'blocked')
        self.assertEqual(h.control(self.job)['phase'],'terminated')

    def test_creation_error_is_failed_attempt_and_stops(self):
        self.setup_driver();a=self.next()['action'];d.claim(self.driver,a['action_id'])
        p=self.root/'error.json';h.save(p,{'error':'Fixture host capacity failure'})
        d.ack(self.driver,a['action_id'],p)
        self.assertEqual(self.next()['phase'],'blocked')
        self.assertEqual(h.control(self.job)['phase'],'rejected')

    def test_issue_output_loss_reconstructs_unclaimed_action_without_new_attempt(self):
        self.setup_driver()
        with mock.patch.object(d,'emit',side_effect=OSError('Fixture crash after issue')):
            with self.assertRaises(OSError):self.next()
        a=self.next()['action'];self.assertEqual(a['kind'],'spawn')
        self.assertEqual(len(projectctl.load_state(self.state)['tasks']['task']['attempts']),1)

    def test_prepare_driver_update_gap_resumes_same_job(self):
        self.setup_driver();original=h.prepare
        def crash(*args,**kwargs):
            original(*args,**kwargs);raise OSError('Fixture crash after bridge prepare')
        with mock.patch.object(h,'prepare',side_effect=crash):
            with self.assertRaises(OSError):self.next()
        self.assertEqual(self.next()['action']['kind'],'spawn')
        self.assertEqual(len(projectctl.load_state(self.state)['tasks']['task']['attempts']),1)

    def crash_ack_update(self, action, path, decision=False):
        original=d.write
        def crash(root,state):
            if state['actions'][action['action_id']]['status']=='acked':
                raise OSError('Fixture crash after bridge mutation')
            original(root,state)
        with mock.patch.object(d,'write',side_effect=crash):
            with self.assertRaises(OSError):d.ack(self.driver,action['action_id'],path,decision)
        self.assertEqual(d.load(self.driver)['actions'][action['action_id']]['status'],'ack_pending')

    def test_acceptance_bridge_driver_gap_replays_private_receipt(self):
        self.setup_driver();a=self.next()['action'];d.claim(self.driver,a['action_id'])
        self.worker='/root/'+a['arguments']['task_name'];p=self.root/'create.json';h.save(p,{'task_name':self.worker})
        self.crash_ack_update(a,p)
        self.assertEqual(self.next()['action']['kind'],'query')
        self.assertEqual(h.control(self.job)['acceptance_origin'],'creation_tool_return')

    def test_receive_bridge_driver_gap_replays_without_double_completion(self):
        self.activate();self.reply();q=self.next()['action'];d.claim(self.driver,q['action_id'])
        self.crash_ack_update(q,self.snapshot({'completed':'Fixture complete'}))
        self.assertEqual(self.next()['action']['kind'],'review')
        ledger=h.read(self.job/'ledger.json')['jobs']
        self.assertEqual(len(ledger),1)

    def test_commit_bridge_driver_gap_does_not_finish_twice(self):
        a=self.received();d.claim(self.driver,a['action_id']);self.crash_ack_update(a,self.decision(),True)
        before=h.sha(self.state);self.assertEqual(self.next()['phase'],'completed')
        self.assertEqual(h.sha(self.state),before)
        self.assertEqual(len(projectctl.load_state(self.state)['tasks']['task']['attempts']),1)

    def test_wrong_decision_and_wrong_argument_type_rejected(self):
        a=self.received();d.claim(self.driver,a['action_id']);p=self.decision();value=h.read(p);value['reply_sha256']='0'*64;h.save(p,value)
        with self.assertRaisesRegex(h.BridgeError,'Decision/reply'):d.ack(self.driver,a['action_id'],p,True)
        with self.assertRaisesRegex(h.BridgeError,'matching'):d.ack(self.driver,a['action_id'],p,False)

    def test_action_and_receipt_drift_fail_closed(self):
        a=self.activate();state=d.load(self.driver);ref=state['actions'][a['action_id']]['ack_ref']
        Path(ref['path']).write_text('{}')
        with self.assertRaises(h.runledger.LedgerError):self.next()

    def test_action_payload_drift_fail_closed(self):
        self.setup_driver();a=self.next();Path(a['action_path']).write_text('{}')
        with self.assertRaises(h.runledger.LedgerError):d.claim(self.driver,a['action']['action_id'])

    def test_checkpoint_drift_does_not_authorize_pending_tool(self):
        self.setup_driver();a=self.next()['action'];state=h.read(self.state);state['revision']+=1;h.save(self.state,state)
        with self.assertRaisesRegex(h.BridgeError,'Checkpoint'):d.claim(self.driver,a['action_id'])

    def test_work_template_and_configuration_cannot_change_in_place(self):
        self.setup_driver();h.save(self.work,{'different':'template'})
        with self.assertRaises(h.runledger.LedgerError):self.next()

    def test_configuration_budget_drift_cannot_authorize_a_call(self):
        self.setup_driver();a=self.next()['action'];before=h.sha(self.state)
        state=h.read(self.driver/'driver.json');state['config']['max_actions']=1000;h.save(self.driver/'driver.json',state)
        with self.assertRaisesRegex(h.BridgeError,'configuration drifted'):d.claim(self.driver,a['action_id'])
        self.assertEqual(h.sha(self.state),before)
        self.assertEqual(h.read(self.driver/'driver.json')['claims'],0)

    def test_dispatch_bound_input_drift_cannot_authorize_a_call(self):
        source=self.root/'source.json';h.save(source,{'value':7});work=h.read(self.work)
        work['input_files']=[{'path':str(source),'sha256':'at_dispatch'}];h.save(self.work,work)
        self.setup_driver();a=self.next()['action'];before=h.sha(self.state)
        h.save(source,{'value':8})
        with self.assertRaises(h.runledger.LedgerError):d.claim(self.driver,a['action_id'])
        self.assertEqual(h.sha(self.state),before)
        self.assertEqual(d.load(self.driver)['claims'],0)

    def test_action_budget_blocks_new_calls(self):
        self.setup_driver(max_actions=1);a=self.next()['action'];self.worker='/root/'+a['arguments']['task_name'];d.claim(self.driver,a['action_id'])
        p=self.root/'create.json';h.save(p,{'task_name':self.worker});d.ack(self.driver,a['action_id'],p)
        result=self.next();self.assertEqual(result['phase'],'blocked');self.assertIn('budget',result['reason'])
        self.assertEqual(result['host_call_claims'],1)

    def test_poll_budget_never_infers_timeout_or_respawns(self):
        self.setup_driver(max_polls=1);a=self.next()['action'];self.worker='/root/'+a['arguments']['task_name'];d.claim(self.driver,a['action_id'])
        q=self.next()['action'];d.claim(self.driver,q['action_id']);d.ack(self.driver,q['action_id'],self.snapshot('running'))
        result=self.next();self.assertEqual(result['phase'],'blocked');self.assertIn('poll budget',result['reason'])
        self.assertEqual(h.control(self.job)['phase'],'running')

    def test_sequential_dependency_binds_generated_input_at_dispatch_once(self):
        plan=deepcopy(self.plan);plan['tasks'].append({'id':'second','title':'Use first output','depends_on':['task'],'owner':None,'write_paths':['second/'],'acceptance_ids':['checked']})
        self.state.unlink();projectctl.init(plan,self.state);second=self.root/'second';second.mkdir();w=self.root/'second-work.json'
        h.save(w,{'prompt':'Use first output','inputs':{},'input_files':[{'path':str(self.out/'result.json'),'sha256':'at_dispatch'}],
                  'write_paths':[str(second)],'reply_path':str(second/'reply.json')})
        self.setup_driver();mapping=h.read(self.works);mapping['second']=str(w);h.save(self.works,mapping)
        # Reinitialize a not-yet-used fixture, rather than changing an active configuration.
        (self.driver/'driver.json').unlink();d.init(self.driver,'project',self.state,self.works,'/root')
        a=self.next()['action'];self.worker='/root/'+a['arguments']['task_name'];d.claim(self.driver,a['action_id'])
        p=self.root/'create.json';h.save(p,{'task_name':self.worker});d.ack(self.driver,a['action_id'],p);self.reply()
        q=self.next()['action'];d.claim(self.driver,q['action_id']);d.ack(self.driver,q['action_id'],self.snapshot({'completed':'Fixture complete'}))
        r=self.next()['action'];d.claim(self.driver,r['action_id']);d.ack(self.driver,r['action_id'],self.decision(),True)
        a=self.next()['action'];request=h.read(Path(a['job_dir'])/'request.json')['request']
        self.assertEqual(request['target_binding']['task_id'],'second')
        self.assertEqual(request['work']['input_files'][0],h.reference(self.out/'result.json'))
        self.assertEqual(projectctl.load_state(self.state)['tasks']['task']['status'],'done')

    def test_existing_package_uses_current_node_and_original_response(self):
        package=packagectl.load(ROOT/'assets/example-package.json');p=self.root/'package.json';h.save(p,package);before=h.sha(p)
        h.save(self.state,packagectl.start(package,{'notes':'No commitments.'}));node=packagectl.pending(package,h.read(self.state))['node']
        self.driver=self.root/'driver';self.works=self.root/'works.json';h.save(self.works,{node:str(self.work)})
        d.init(self.driver,'package',self.state,self.works,'/root',p)
        a=self.next()['action'];self.worker='/root/'+a['arguments']['task_name'];d.claim(self.driver,a['action_id'])
        c=self.root/'create.json';h.save(c,{'task_name':self.worker});d.ack(self.driver,a['action_id'],c)
        reply=self.reply();value=h.read(reply);value['result']={'invocation_id':h.read(self.job/'request.json')['request']['invocation_id'],
               'outcome':'ok','artifacts':{'actions':[]},'evidence':[str(self.out/'result.json')]};h.save(reply,value)
        q=self.next()['action'];d.claim(self.driver,q['action_id']);d.ack(self.driver,q['action_id'],self.snapshot({'completed':'Fixture done'}))
        r=self.next()['action'];decision=self.decision();value=h.read(decision);value['results']=h.read(reply)['result'];h.save(decision,value)
        d.claim(self.driver,r['action_id']);d.ack(self.driver,r['action_id'],decision,True)
        self.assertEqual(self.next()['phase'],'completed');self.assertEqual(h.read(self.state)['flow_state']['steps'],1)
        self.assertEqual(h.sha(p),before)

    def test_two_cli_next_processes_return_same_action(self):
        self.setup_driver();args=[sys.executable,str(ROOT/'scripts/hostdriver.py'),'next','--driver',str(self.driver)]
        processes=[subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
        results=[]
        for process in processes:
            stdout,stderr=process.communicate(timeout=10);self.assertEqual(process.returncode,0,stderr);results.append(json.loads(stdout))
        self.assertEqual(results[0]['action'],results[1]['action'])
        self.assertEqual(len(projectctl.load_state(self.state)['tasks']['task']['attempts']),1)


if __name__=='__main__':
    unittest.main()
