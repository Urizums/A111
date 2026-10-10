"""R24 native Flow IR integration tests for the real checked-in controller.

These run author code and local CLI; they do NOT invoke another AI or a blind reviewer.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

STUDY = Path(__file__).resolve().parent
REPO = STUDY.parents[3]
RUNTIME = REPO / 'skills/forge-agent-flow/scripts'
sys.path.insert(0, str(RUNTIME))
sys.path.insert(0, str(STUDY))

import flowctl
from flow_builder import make_flow, verify_public_source
from rehearsal import generate, grade
from native_flow_smoke import run as run_native


class NativeFlowIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='r24-native-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.case = self.root / 'case'
        generate(9011, self.case)
        self.public = self.case / 'producer'
        self.spec, self.inputs = make_flow(self.public)

    def command(self, *args):
        process = subprocess.run(
            [sys.executable, str(RUNTIME / 'flowctl.py'), *map(str, args)],
            text=True, capture_output=True, check=False,
        )
        raw = process.stdout if process.stdout.strip() else process.stderr
        try:
            output = json.loads(raw)
        except json.JSONDecodeError:
            self.fail(f'Invalid CLI JSON: {raw[-1000:]}')
        return process.returncode, output

    def test_native_probe_executes_original_controller(self):
        verdict = run_native(REPO)
        self.assertEqual(verdict['status'], 'pass', verdict)
        self.assertEqual(verdict['locally_replayed_nodes'], 2)
        self.assertEqual(verdict['pending_receiver'], 'blocked')
        self.assertFalse(verdict['terminal_business_acceptance'])
        self.assertTrue(verdict['sanitized_receiver_packet_verified'])
        self.assertEqual(verdict['receiver_files'], 8)

    def test_real_cli_validate_and_compile(self):
        source = self.root / 'flow.json'
        source.write_text(json.dumps(self.spec), encoding='utf-8')
        code, validated = self.command('validate', source)
        self.assertEqual(code, 0, validated)
        self.assertTrue(validated['valid'])
        code, compiled = self.command('compile', source, '--out', self.root / 'compiled')
        self.assertEqual(code, 0, compiled)
        self.assertEqual(compiled['nodes'], 3)
        for node in ('produce', 'audit_data', 'receive_handoff'):
            self.assertTrue((self.root / 'compiled/prompts' / (node + '.md')).is_file())
        self.assertIn('no model execution is implied', (self.root / 'compiled/runbook.md').read_text().lower())

    def test_cli_initial_block_and_real_invocation(self):
        source = self.root / 'flow.json'
        inputs_path = self.root / 'inputs.json'
        state = self.root / 'state.json'
        source.write_text(json.dumps(self.spec), encoding='utf-8')
        inputs_path.write_text(json.dumps(self.inputs), encoding='utf-8')
        code, result = self.command('start', source, '--inputs', inputs_path, '--state', state)
        self.assertEqual(code, 2, result)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('workspace', result['reason'])
        self.assertTrue(state.is_file())
        code, result = self.command('next', source, '--state', state)
        self.assertEqual(code, 2, result)
        self.assertEqual(result['status'], 'blocked')
        # Because one checkpoint now exists, a second start must not overwrite it.
        code, result = self.command('start', source, '--inputs', inputs_path, '--state', state)
        self.assertEqual(code, 2, result)
        self.assertIn('exists', result['error'].lower())

    def test_native_error_and_stale_routes(self):
        spec, inputs = make_flow(self.public, workspace_receipt='observed local Python test')
        self.assertTrue(flowctl.validate(spec)['valid'])
        state = flowctl.start(spec, inputs)
        first = flowctl.pending(spec, state)
        self.assertEqual(first['node'], 'produce')
        bad = {'invocation_id': 'tampered', 'outcome': 'error', 'artifacts': {},
               'evidence': ['A test-only failure']}
        with self.assertRaises(flowctl.FlowError):
            flowctl.advance(spec, state, bad)
        bad['invocation_id'] = first['invocation_id']
        failed = flowctl.advance(spec, state, bad)
        self.assertEqual(failed['status'], 'failed')
        with self.assertRaises(flowctl.FlowError):
            flowctl.advance(spec, failed, bad)
        self.assertEqual(flowctl.pending(spec, failed)['status'], 'failed')

    def test_public_source_changes_fail_bound_guard(self):
        self.assertTrue(verify_public_source(self.inputs['source_bundle'])['passed'])
        payment = self.public / 'payments.json'
        pristine = payment.read_bytes()
        payment.write_bytes(pristine + b' ')
        self.assertFalse(verify_public_source(self.inputs['source_bundle'])['passed'])
        payment.write_bytes(pristine)
        self.assertTrue(verify_public_source(self.inputs['source_bundle'])['passed'])

    def test_real_public_producer_then_consumer_data_gate(self):
        output = self.root / 'submission'
        process = subprocess.run([sys.executable, str(STUDY / 'public_producer.py'),
                                  '--producer', str(self.public), '--out', str(output)],
                                 check=False, text=True, capture_output=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(verify_public_source(self.inputs['source_bundle'])['passed'])
        verdict = grade(self.case, output)
        self.assertTrue(verdict['data_artifacts_passed'], verdict)
        self.assertEqual(verdict['workflow_usability'], 'unverified')
        self.assertFalse(verdict['overall_accepted'])
        # A built artifact is not an independent acceptance receipt.
        self.assertEqual(flowctl.pending(self.spec, flowctl.start(self.spec, self.inputs))['status'], 'blocked')


if __name__ == '__main__':
    unittest.main()
