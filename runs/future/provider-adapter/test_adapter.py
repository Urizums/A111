import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).parent


class AdapterAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'ledger.sqlite3'
        self.n = 0
        self.request = dict(request_id='r1', idempotency_key='source:1', model='local-contract',
                            input='Summarize only supplied material.',
                            limits=dict(timeout_ms=1000, max_output_tokens=100))

    def call(self, command, value, expected=0, raw=False):
        self.n += 1
        if command in {'submit', 'observe'}:
            file = self.root / ('input-' + str(self.n) + '.json')
            file.write_text(value if raw else json.dumps(value))
            value = str(file)
        result = subprocess.run([sys.executable, str(HERE/'adapter.py'), '--database', str(self.db),
                                 command, value], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout if expected == 0 else result.stderr)

    def event(self, status='running', event_id='e1', **changes):
        value = dict(request_id='r1', provider_run_id='provider:1', event_id=event_id,
                     status=status, output=None, error=None, usage=None)
        if status == 'succeeded': value['output'] = 'Observed result'
        if status in {'unknown', 'failed'}: value['error'] = 'Observed transport ambiguity'
        value.update(changes)
        return value

    def test_cli_idempotency_survives_reopen(self):
        self.assertTrue(self.call('submit', self.request)['should_dispatch'])
        self.assertEqual(self.call('get', 'r1')['request'], self.request)
        self.assertFalse(self.call('submit', self.request)['should_dispatch'])

    def test_identity_or_content_conflicts_preserve_record(self):
        self.call('submit', self.request)
        before = self.call('get', 'r1')
        for field, value in [('input', 'Changed body'), ('request_id', 'r2'), ('idempotency_key', 'other:1')]:
            changed = copy.deepcopy(self.request); changed[field] = value
            self.call('submit', changed, 2)
            self.assertEqual(self.call('get', 'r1'), before)

    def test_unknown_dispatch_is_not_permission_to_repeat(self):
        self.call('submit', self.request)
        self.call('observe', self.event('unknown', provider_run_id=None))
        retry = self.call('submit', self.request)
        self.assertEqual(retry['status'], 'unknown'); self.assertFalse(retry['should_dispatch'])
        self.call('observe', self.event('succeeded', 'e2'))
        row = self.call('get', 'r1')
        self.assertEqual(row['status'], 'succeeded'); self.assertEqual(len(row['events']), 2)
        self.assertIsNone(row['events'][1]['usage'])

    def test_cancel_intent_can_race_with_success(self):
        self.call('submit', self.request); self.call('observe', self.event())
        result = self.call('cancel', 'r1')
        self.assertEqual(result['status'], 'running'); self.assertFalse(result['terminal_proven'])
        self.call('observe', self.event('succeeded', 'e2'))
        row = self.call('get', 'r1')
        self.assertTrue(row['cancel_requested']); self.assertEqual(row['status'], 'succeeded')

    def test_explicit_cancellation_acknowledgement(self):
        self.call('submit', self.request); self.call('cancel', 'r1')
        self.call('observe', self.event('cancelled'))
        self.assertTrue(self.call('cancel', 'r1')['terminal_proven'])
        self.assertEqual(self.call('get', 'r1')['status'], 'cancelled')

    def test_duplicate_and_contradictory_terminal_events(self):
        self.call('submit', self.request)
        event = self.event('succeeded'); self.call('observe', event)
        before = self.call('get', 'r1')
        self.assertTrue(self.call('observe', event)['reused'])
        changed = dict(event, output='Conflict'); self.call('observe', changed, 2)
        self.call('observe', self.event('failed', 'e2'), 2)
        self.assertEqual(self.call('get', 'r1'), before)

    def test_wrong_request_run_usage_and_extra_fields_rejected(self):
        self.call('submit', self.request); self.call('observe', self.event())
        before = self.call('get', 'r1')
        cases = [self.event('succeeded', 'e2', request_id='other'),
                 self.event('succeeded', 'e2', provider_run_id='another'),
                 self.event('succeeded', 'e2', usage=dict(input_tokens=True, output_tokens=0)),
                 dict(self.event('succeeded', 'e2'), fabricated_cost=0)]
        for event in cases:
            self.call('observe', event, 2)
            self.assertEqual(self.call('get', 'r1'), before)

    def test_strict_json_and_request_limits(self):
        self.call('submit', '{"request_id":"r1","request_id":"r2"}', 2, raw=True)
        self.call('submit', '{"x":NaN}', 2, raw=True)
        for value in [True, 0, -1, 0.5]:
            request = copy.deepcopy(self.request); request['limits']['max_output_tokens'] = value
            self.call('submit', request, 2)
        self.assertFalse(self.db.exists())


if __name__ == '__main__':
    unittest.main()
