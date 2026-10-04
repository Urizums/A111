"""Read-only/resume clock and crash fixtures, not live provider observations."""
from pathlib import Path
import json
import subprocess
import sys
import unittest
from unittest import mock

import hostbridge as h
import hostdriver as d
import test_hostbridge as b
import test_hostdriver as f
import test_resource_driver as r


class OverviewTests(unittest.TestCase):
    setUp = b.BridgeTests.setUp
    snapshot = b.BridgeTests.snapshot
    reply = b.BridgeTests.reply
    decision = b.BridgeTests.decision
    setup_driver = f.DriverTests.setup_driver
    next = f.DriverTests.next
    activate = f.DriverTests.activate
    received = f.DriverTests.received
    crash_ack_update = f.DriverTests.crash_ack_update
    configure = r.ResourceTests.configure
    second = r.ResourceTests.second

    def bytes_before(self):
        return {str(p): p.read_bytes() for p in self.root.rglob('*')
                if p.is_file() and not p.name.endswith('.hostbridge.lock')}

    def inspect_unchanged(self):
        before = self.bytes_before()
        result = d.inspect(self.driver)
        self.assertEqual(self.bytes_before(), before)
        self.assertFalse(result['call_allowed'])
        self.assertFalse(result['automatic_host_call'])
        self.assertTrue(result['read_only'])
        return result

    def test_initial_and_proposed_inspection_never_schedules_or_claims(self):
        self.setup_driver()
        for _ in range(2):
            result = self.inspect_unchanged()
            self.assertIsNone(result['current_target'])
            self.assertEqual(result['next_required_step'], 'resume_original_controller')
        action = self.next()['action']
        result = self.inspect_unchanged()
        self.assertEqual(result['pending_action']['action_id'], action['action_id'])
        self.assertEqual(result['pending_action']['status'], 'proposed')
        self.assertEqual(result['budgets']['actions_remaining'], 50)

    def test_claimed_creation_inspection_and_resume_only_query(self):
        self.setup_driver(); action = self.next()['action']
        d.claim(self.driver, action['action_id'])
        result = self.inspect_unchanged()
        self.assertEqual(result['next_required_step'], 'reconcile_claimed_action')
        query = d.resume(self.driver, result['run_id'])
        self.assertEqual(query['action']['kind'], 'query')
        self.assertFalse(query['call_allowed'])
        state = d.load(self.driver)
        self.assertEqual(state['claims'], 1)
        self.assertEqual(sum(h.read(v['payload_ref']['path'])['kind'] == 'spawn' for v in state['actions'].values()), 1)

    def test_wrong_run_id_rejected_before_any_mutation(self):
        self.setup_driver(); self.next()
        before = self.bytes_before()
        with self.assertRaisesRegex(h.BridgeError, 'Run ID'):
            d.resume(self.driver, 'driver_unrelated')
        self.assertEqual(self.bytes_before(), before)

    def test_ack_pending_inspect_keeps_saved_ack_until_resume(self):
        spawn = self.activate()
        query = self.next()['action']; d.claim(self.driver, query['action_id'])
        self.crash_ack_update(query, self.snapshot('running'))
        result = self.inspect_unchanged()
        self.assertEqual(result['pending_action']['status'], 'ack_pending')
        self.assertEqual(result['next_required_step'], 'replay_saved_ack')
        resumed = d.resume(self.driver, result['run_id'])
        self.assertEqual(resumed['action']['kind'], 'query')
        self.assertEqual(d.load(self.driver)['claims'], 2)
        self.assertEqual(d.load(self.driver)['actions'][spawn['action_id']]['status'], 'acked')

    def test_bridge_journal_inspect_never_replays_and_resume_reuses_it(self):
        self.activate(); query = self.next()['action']; d.claim(self.driver, query['action_id'])
        with mock.patch.object(h, 'recover', side_effect=OSError('Fixture journal crash')):
            # Build the exact guarded transaction without running control's recovery.
            c = h.read(self.job / 'control.json')
            changed = dict(c); changed['phase'] = 'running'
            ledger = h.ledger_image(self.job, c, 'running', h.reference(self.snapshot('running')))
            with self.assertRaises(OSError):
                h.transaction(self.job, c['target'], [(self.job / 'control.json', changed), (self.job / 'ledger.json', ledger)], c['refs'])
        result = self.inspect_unchanged()
        self.assertTrue(result['bridge_transaction_pending'])
        self.assertEqual(result['next_required_step'], 'resume_saved_transaction')
        resumed = d.resume(self.driver, result['run_id'])
        self.assertFalse((self.job / 'pending.json').exists())
        self.assertEqual(resumed['action']['kind'], 'query')
        self.assertEqual(d.load(self.driver)['claims'], 2)

    def test_capacity_inspect_never_admits_or_releases(self):
        first = self.configure(seconds=None, policy='observe')
        d.claim(self.driver, first['action_id'])
        other, _, second = self.second()
        d.claim(other, second['action_id'])
        original = h.sha(self.registry)
        held = self.inspect_unchanged()
        self.assertEqual(held['capacity']['own_slot'], 'held')
        self.assertEqual(held['capacity']['available'], 0)
        waiting = d.inspect(other)
        self.assertEqual(waiting['next_required_step'], 'wait_capacity')
        self.assertIsNone(waiting['capacity']['own_slot'])
        self.assertEqual(h.sha(self.registry), original)
        self.assertEqual(d.load(other)['claims'], 0)

    def test_deadline_observation_is_not_a_persisted_expiry(self):
        action = self.configure(); d.claim(self.driver, action['action_id'])
        self.tick += 2_000_000_000
        result = self.inspect_unchanged()
        self.assertTrue(result['deadline']['cutoff_reached'])
        self.assertEqual(result['deadline']['clock_status'], 'same_boot')
        self.assertIsNone(d.load(self.driver)['current']['deadline']['expired_observation'])
        self.assertEqual(result['capacity']['held'], 1)

    def test_clock_change_backwards_or_unavailable_is_visible(self):
        action = self.configure(); d.claim(self.driver, action['action_id'])
        self.boot = 'new-boot'
        result = self.inspect_unchanged()
        self.assertEqual(result['deadline']['clock_status'], 'changed_boot')
        self.assertEqual(result['next_required_step'], 'reconcile_clock')
        self.boot = 'fixture-boot'; self.tick = 1
        self.assertEqual(self.inspect_unchanged()['deadline']['clock_status'], 'backwards')
        with mock.patch.object(d, 'clock', side_effect=OSError('Fixture clock unavailable')):
            self.assertEqual(self.inspect_unchanged()['deadline']['clock_status'], 'unavailable')

    def test_failed_run_remains_blocked_and_does_not_retry(self):
        self.activate(); query = self.next()['action']; d.claim(self.driver, query['action_id'])
        d.ack(self.driver, query['action_id'], self.snapshot('failed'))
        self.next()
        result = self.inspect_unchanged()
        self.assertEqual(result['next_required_step'], 'explicit_reconciliation')
        before = self.bytes_before()
        self.assertEqual(d.resume(self.driver, result['run_id'])['phase'], 'blocked')
        self.assertEqual(self.bytes_before(), before)

    def test_completed_resume_does_not_advance_original_checkpoint(self):
        review = self.received(); d.claim(self.driver, review['action_id'])
        d.ack(self.driver, review['action_id'], self.decision(), True); self.next()
        result = self.inspect_unchanged()
        self.assertEqual(result['next_required_step'], 'completed')
        before = self.bytes_before()
        for _ in range(2): self.assertEqual(d.resume(self.driver, result['run_id'])['phase'], 'completed')
        self.assertEqual(self.bytes_before(), before)

    def test_exhausted_limits_not_refilled_by_resume(self):
        self.setup_driver(max_actions=1, max_polls=1)
        action = self.next()['action']; d.claim(self.driver, action['action_id']); self.next()
        result = self.inspect_unchanged()
        self.assertEqual(result['phase'], 'blocked')
        self.assertEqual(result['budgets']['actions_remaining'], 0)
        before = self.bytes_before()
        self.assertEqual(d.resume(self.driver, result['run_id'])['phase'], 'blocked')
        self.assertEqual(self.bytes_before(), before)

    def test_inspect_rejects_input_evidence_drift_without_mutation(self):
        self.setup_driver(); self.next(); self.work.write_text('{}')
        before = self.bytes_before()
        with self.assertRaises(ValueError): d.inspect(self.driver)
        self.assertEqual(self.bytes_before(), before)

    def test_cli_inspection_and_wrong_run_resume(self):
        self.setup_driver()
        command = [sys.executable, str(Path(d.__file__)), 'inspect', '--driver', str(self.driver)]
        first = subprocess.run(command, capture_output=True, text=True, timeout=15)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(json.loads(first.stdout)['schema_version'], 'forge-host-inspection/1')
        wrong = subprocess.run(command[:2] + ['resume', '--driver', str(self.driver), '--expect-run', 'unrelated'],
                               capture_output=True, text=True, timeout=15)
        self.assertEqual(wrong.returncode, 2)
        self.assertEqual(json.loads(wrong.stdout)['status'], 'reconcile_required')

    def invalid_review(self):
        review = self.received(); d.claim(self.driver, review['action_id'])
        decision = self.decision()
        value = h.read(decision)
        value['results']['acceptance_results']['checked']['evidence'][0]['sha256'] = '0' * 64
        h.save(decision, value)
        with self.assertRaises(ValueError): d.ack(self.driver, review['action_id'], decision, True)
        return review, decision

    def test_invalid_local_review_ack_can_be_explicitly_rejected_with_old_bytes_retained(self):
        review, decision = self.invalid_review()
        state = d.load(self.driver); old = state['actions'][review['action_id']]['ack_ref']
        old_bytes = Path(old['path']).read_bytes(); checkpoint = h.sha(self.state)
        inspected = self.inspect_unchanged()
        self.assertEqual(inspected['next_required_step'], 'reconcile_invalid_review_ack')
        result = d.retry_review(self.driver, state['run_id'], review['action_id'], 'Correct rejected evidence SHA from original files')
        self.assertFalse(result['call_allowed'])
        self.assertEqual(h.sha(self.state), checkpoint)
        self.assertEqual(Path(old['path']).read_bytes(), old_bytes)
        self.assertEqual(d.load(self.driver)['claims'], state['claims'])
        action = d.resume(self.driver, state['run_id'])['action']
        self.assertEqual(action['kind'], 'review'); self.assertNotEqual(action['action_id'], review['action_id'])
        d.claim(self.driver, action['action_id'])
        # A distinct new decision file is independently constructed from actual evidence.
        fixed = self.root / 'fixed-decision.json'; h.save(fixed, h.read(self.decision()))
        d.ack(self.driver, action['action_id'], fixed, True)
        self.assertEqual(d.resume(self.driver, state['run_id'])['phase'], 'completed')
        self.assertEqual(sum(h.read(v['payload_ref']['path'])['kind'] == 'spawn' for v in d.load(self.driver)['actions'].values()), 1)

    def test_valid_pending_review_ack_cannot_be_discarded(self):
        review = self.received(); d.claim(self.driver, review['action_id'])
        with mock.patch.object(h, 'commit', side_effect=OSError('Fixture IO not validation failure')):
            with self.assertRaises(OSError): d.ack(self.driver, review['action_id'], self.decision(), True)
        state = d.load(self.driver); before = self.bytes_before()
        with self.assertRaisesRegex(h.BridgeError, 'valid'):
            d.retry_review(self.driver, state['run_id'], review['action_id'], 'Do not discard valid intent')
        self.assertEqual(self.bytes_before(), before)
        self.assertEqual(d.resume(self.driver, state['run_id'])['phase'], 'completed')

    def test_invalid_ack_rejection_needs_correct_run_action_and_reason(self):
        review, _ = self.invalid_review(); state = d.load(self.driver)
        for run, action, reason in [('wrong', review['action_id'], 'Reason'),
                                    (state['run_id'], 'wrong', 'Reason'),
                                    (state['run_id'], review['action_id'], '')]:
            before = self.bytes_before()
            with self.assertRaises(h.BridgeError): d.retry_review(self.driver, run, action, reason)
            self.assertEqual(self.bytes_before(), before)

    def test_native_ack_and_committed_review_ack_cannot_be_discarded(self):
        self.activate(); state = d.load(self.driver); before = self.bytes_before()
        with self.assertRaises(h.BridgeError): d.retry_review(self.driver, state['run_id'], next(iter(state['actions'])), 'Reason')
        self.assertEqual(self.bytes_before(), before)
        self.reply(); query = self.next()['action']; d.claim(self.driver, query['action_id'])
        d.ack(self.driver, query['action_id'], self.snapshot({'completed': 'Fixture'}))
        review = self.next()['action']; d.claim(self.driver, review['action_id'])
        self.crash_ack_update(review, self.decision(), True)
        before = self.bytes_before()
        with self.assertRaisesRegex(h.BridgeError, 'uncommitted'):
            d.retry_review(self.driver, state['run_id'], review['action_id'], 'Reason')
        self.assertEqual(self.bytes_before(), before)

    def test_review_ack_with_pending_bridge_transaction_cannot_be_discarded(self):
        review, _ = self.invalid_review(); state = d.load(self.driver)
        h.save(self.job / 'pending.json', {'synthetic': 'uncertain journal must not be discarded'})
        before = self.bytes_before()
        with self.assertRaisesRegex(h.BridgeError, 'transaction'):
            d.retry_review(self.driver, state['run_id'], review['action_id'], 'Reason')
        self.assertEqual(self.bytes_before(), before)

    def test_explicit_rejection_does_not_refill_original_budget(self):
        review, _ = self.invalid_review(); state = d.load(self.driver)
        # Fixture changes the configured budget before the rejection to exercise exhaustion;
        # recompute the local config binding, not an execution-time budget update API.
        state['config']['max_actions'] = state['claims']; state['config_hash'] = h.digest(state['config']); d.write(self.driver, state)
        d.retry_review(self.driver, state['run_id'], review['action_id'], 'Correct uncommitted decision')
        self.assertEqual(d.resume(self.driver, state['run_id'])['phase'], 'blocked')
        self.assertEqual(d.load(self.driver)['claims'], state['claims'])

    def test_wrapped_unavailable_review_evidence_is_not_discardable(self):
        review = self.received(); d.claim(self.driver, review['action_id'])
        extra = self.root / 'coordinator-evidence.json'; h.save(extra, {'review': 'fixture'})
        decision = self.decision(); value = h.read(decision)
        value['results']['acceptance_results']['checked']['evidence'].append(h.reference(extra)); h.save(decision, value)
        with mock.patch.object(h, 'commit', side_effect=OSError('Fixture IO during initial commit')):
            with self.assertRaises(OSError): d.ack(self.driver, review['action_id'], decision, True)
        extra.unlink(); state = d.load(self.driver); before = self.bytes_before()
        result = d.inspect(self.driver)
        self.assertEqual(result['review_ack_validation']['status'], 'unavailable')
        self.assertEqual(result['next_required_step'], 'reconcile_review_evidence')
        with self.assertRaisesRegex(h.BridgeError, 'unavailable'):
            d.retry_review(self.driver, state['run_id'], review['action_id'], 'Do not discard unavailable evidence')
        self.assertEqual(self.bytes_before(), before)


if __name__ == '__main__':
    unittest.main()
