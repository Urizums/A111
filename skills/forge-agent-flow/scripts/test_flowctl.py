#!/usr/bin/env python3
"""Behavioral regression checks. All model responses here are explicit fixtures."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import flowctl as f

ROOT = Path(__file__).resolve().parents[1]


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.flow = f.load(ROOT / 'assets/minimal-flow.json')

    def response(self, state, outcome='ok', values=None):
        return {'invocation_id': f.pending(self.flow, state)['invocation_id'],
                'outcome': outcome, 'artifacts': {'actions': []} if values is None else values,
                'evidence': ['Fixture response: routing/contract test, not live model execution.']}

    def nested_flow(self):
        spec = copy.deepcopy(self.flow)
        spec['schema_version'] = '1.1'
        spec['artifacts']['actions']['schema'] = {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['task', 'quote'],
                'properties': {
                    'task': {'type': 'string'},
                    'owner': {'type': ['string', 'null']},
                    'quote': {'type': 'string'},
                },
                'additionalProperties': False,
            },
        }
        return spec

    def cycle(self):
        self.flow['budgets']['max_steps'] = 5
        node = self.flow['nodes'][0]
        node['max_visits'] = 2
        node['routes']['retry'] = 'extract'
        node['emits']['retry'] = []

    def test_bundled_flows_valid(self):
        for name in ('minimal-flow.json', 'meta-flow.json', 'triage-flow.json'):
            with self.subTest(name=name):
                result = f.validate(f.load(ROOT / 'assets' / name))
                self.assertTrue(result['valid'], result)

    def test_fixture_success_and_evidence(self):
        state = f.start(self.flow, {'notes': 'No actions.'})
        completed = f.advance(self.flow, state, self.response(state))
        self.assertEqual(completed['status'], 'completed')
        self.assertEqual(completed['artifacts']['actions'], [])
        self.assertEqual(completed['steps'], 1)
        self.assertEqual(state['steps'], 0)
        self.assertIn('output_hash', completed['trace'][0])

    def test_wrong_input_type_rejected(self):
        with self.assertRaises(f.FlowError):
            f.start(self.flow, {'notes': []})

    def test_flow_10_keeps_shallow_descriptor_and_payload_semantics(self):
        state = f.start(self.flow, {'notes': ''})
        result = f.advance(self.flow, state, self.response(
            state, values={'actions': [{'owner': {'unconstrained': True}}]}))
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(f.validate(self.flow)['valid'])

        with_schema = copy.deepcopy(self.flow)
        with_schema['artifacts']['actions']['schema'] = {'type': 'array'}
        self.assertFalse(f.validate(with_schema)['valid'])

    def test_flow_11_nested_schema_accepts_empty_list_nullable_owner_and_locations(self):
        spec = self.nested_flow()
        self.assertTrue(f.validate(spec)['valid'], f.validate(spec)['errors'])

        state = f.start(spec, {'notes': ''})
        result = f.advance(spec, state, {
            'invocation_id': f.pending(spec, state)['invocation_id'],
            'outcome': 'ok',
            'artifacts': {'actions': [{'task': 'send draft', 'owner': None, 'quote': 'Kai will send it.'}]},
            'evidence': ['Fixture output.'],
        })
        self.assertEqual(result['status'], 'completed')

        empty_state = f.start(spec, {'notes': ''})
        empty = f.advance(spec, empty_state, {
            'invocation_id': f.pending(spec, empty_state)['invocation_id'],
            'outcome': 'ok', 'artifacts': {'actions': []}, 'evidence': ['Fixture no-action output.'],
        })
        self.assertEqual(empty['status'], 'completed')

    def test_flow_11_rejects_missing_nested_field_wrong_type_and_extra_field(self):
        spec = self.nested_flow()
        cases = (
            ({'task': 'send draft', 'owner': None}, r'actions\[0\]\.quote'),
            ({'task': 'send draft', 'owner': {}, 'quote': 'quoted'}, r'actions\[0\]\.owner'),
            ({'task': 'send draft', 'owner': None, 'quote': 'quoted', 'typo': 1}, r'actions\[0\]\.typo'),
        )
        for row, expected_path in cases:
            with self.subTest(row=row):
                state = f.start(spec, {'notes': ''})
                before = copy.deepcopy(state)
                with self.assertRaisesRegex(f.FlowError, expected_path):
                    f.advance(spec, state, {
                        'invocation_id': f.pending(spec, state)['invocation_id'], 'outcome': 'ok',
                        'artifacts': {'actions': [row]}, 'evidence': ['Fixture output.'],
                    })
                self.assertEqual(state, before)

    def test_flow_11_schema_definition_fails_closed(self):
        bad_schemas = (
            {'type': 'array', 'items': {'type': 'object', '$ref': '#/definitions/action'}},
            {'type': 'array', 'items': {'type': 'object', 'minItems': 1}},
            {'type': 'array', 'minItems': True},
            {'type': 'object', 'items': {'type': 'string'}},
            {'type': 'array', 'items': {'type': 'object', 'required': ['x'],
                                        'additionalProperties': False}},
            {'type': 'object'},  # Top-level schema does not match descriptor type.
        )
        for schema in bad_schemas:
            with self.subTest(schema=schema):
                spec = self.nested_flow()
                spec['artifacts']['actions']['schema'] = schema
                result = f.validate(spec)
                self.assertFalse(result['valid'], result)

    def test_flow_11_enum_compares_nested_boolean_and_integer_exactly(self):
        spec = self.nested_flow()
        spec['artifacts']['actions']['schema'] = {
            'type': 'array', 'items': {'type': 'object', 'enum': [{'x': 1}]},
        }
        state = f.start(spec, {'notes': ''})
        with self.assertRaisesRegex(f.FlowError, r'actions\[0\].*enum'):
            f.advance(spec, state, {
                'invocation_id': f.pending(spec, state)['invocation_id'], 'outcome': 'ok',
                'artifacts': {'actions': [{'x': True}]}, 'evidence': ['Fixture output.'],
            })

    def test_start_validates_nested_input(self):
        spec = self.nested_flow()
        spec['inputs']['source'] = {
            'type': 'object', 'description': 'Source metadata.',
            'schema': {'type': 'object', 'required': ['name'],
                       'properties': {'name': {'type': 'string'}}, 'additionalProperties': False},
        }
        spec['nodes'][0]['reads'].append('source')
        with self.assertRaisesRegex(f.FlowError, r'source\.name'):
            f.start(spec, {'notes': '', 'source': {}})
        state = f.start(spec, {'notes': '', 'source': {'name': 'minutes.md'}})
        self.assertEqual(f.pending(spec, state)['status'], 'ready')

    def test_pending_revalidates_nested_input_before_downstream_dispatch(self):
        spec = self.nested_flow()
        spec['budgets']['max_steps'] = 2
        producer = spec['nodes'][0]
        producer['routes']['ok'] = 'consume'
        consumer = copy.deepcopy(producer)
        consumer.update(id='consume', reads=['actions'], writes=[], prompt='Consume validated actions.',
                       acceptance=['Actions satisfy their schema.'], max_visits=1,
                       routes={'ok': '$done', 'error': '$failed', 'blocked': '$blocked'},
                       emits={'ok': [], 'error': [], 'blocked': []})
        spec['nodes'].append(consumer)
        self.assertTrue(f.validate(spec)['valid'], f.validate(spec)['errors'])
        state = f.start(spec, {'notes': ''})
        state = f.advance(spec, state, {
            'invocation_id': f.pending(spec, state)['invocation_id'], 'outcome': 'ok',
            'artifacts': {'actions': [{'task': 'send draft', 'owner': None, 'quote': 'quoted'}]},
            'evidence': ['Fixture output.'],
        })
        state['artifacts']['actions'][0].pop('quote')
        with self.assertRaisesRegex(f.FlowError, r'actions\[0\]\.quote'):
            f.pending(spec, state)

    def test_cli_nested_rejection_leaves_checkpoint_bytes_unchanged(self):
        spec = self.nested_flow()
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            flow_path, inputs_path, state_path, response_path = [
                directory / name for name in ('flow.json', 'inputs.json', 'run.json', 'response.json')]
            f.save(flow_path, spec)
            f.save(inputs_path, {'notes': ''})
            command = [sys.executable, str(ROOT / 'scripts/flowctl.py')]
            started = subprocess.run(command + ['start', str(flow_path), '--inputs', str(inputs_path),
                                                '--state', str(state_path)],
                                     capture_output=True, text=True)
            self.assertEqual(started.returncode, 0, started.stderr)
            before = state_path.read_bytes()
            dispatch = json.loads(started.stdout)
            f.save(response_path, {
                'invocation_id': dispatch['invocation_id'], 'outcome': 'ok',
                'artifacts': {'actions': [{'task': 'send draft'}]}, 'evidence': ['Fixture output.'],
            })
            rejected = subprocess.run(command + ['advance', str(flow_path), '--state', str(state_path),
                                                  '--response', str(response_path)],
                                      capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertIn('actions[0].quote', rejected.stderr)
            self.assertEqual(state_path.read_bytes(), before)

    def test_missing_input_rejected(self):
        with self.assertRaises(f.FlowError):
            f.start(self.flow, {})

    def test_output_type_rejected_without_mutation(self):
        state = f.start(self.flow, {'notes': 'No actions.'})
        before = copy.deepcopy(state)
        with self.assertRaises(f.FlowError):
            f.advance(self.flow, state, self.response(state, values={'actions': {}}))
        self.assertEqual(state, before)

    def test_extra_output_rejected(self):
        state = f.start(self.flow, {'notes': ''})
        with self.assertRaises(f.FlowError):
            f.advance(self.flow, state, self.response(state, values={'actions': [], 'notes': 'overwrite'}))

    def test_unknown_outcome_rejected(self):
        state = f.start(self.flow, {'notes': ''})
        with self.assertRaises(f.FlowError):
            f.advance(self.flow, state, self.response(state, outcome='invented'))

    def test_error_branch_requires_no_success_output(self):
        state = f.start(self.flow, {'notes': ''})
        failed = f.advance(self.flow, state, self.response(state, outcome='error', values={}))
        self.assertEqual(failed['status'], 'failed')
        self.assertNotIn('actions', failed['artifacts'])

    def test_node_blocked_branch(self):
        state = f.start(self.flow, {'notes': ''})
        result = f.advance(self.flow, state, self.response(state, outcome='blocked', values={}))
        self.assertEqual(result['status'], 'blocked')

    def test_duplicate_response_rejected(self):
        self.cycle()
        state = f.start(self.flow, {'notes': ''})
        response = self.response(state, outcome='retry', values={})
        advanced = f.advance(self.flow, state, response)
        with self.assertRaisesRegex(f.FlowError, 'Stale or duplicate'):
            f.advance(self.flow, advanced, response)

    def test_changed_flow_rejects_checkpoint(self):
        state = f.start(self.flow, {'notes': ''})
        self.flow['nodes'][0]['prompt'] += ' Altered.'
        with self.assertRaisesRegex(f.FlowError, 'Flow changed'):
            f.pending(self.flow, state)

    def test_node_visit_limit(self):
        self.cycle()
        state = f.start(self.flow, {'notes': ''})
        for _ in range(2):
            state = f.advance(self.flow, state, self.response(state, outcome='retry', values={}))
        self.assertEqual(f.pending(self.flow, state)['reason'], 'max_visits exhausted')
        with self.assertRaises(f.FlowError):
            f.advance(self.flow, state, {})

    def test_global_step_limit(self):
        self.cycle()
        self.flow['budgets']['max_steps'] = 1
        state = f.start(self.flow, {'notes': ''})
        state = f.advance(self.flow, state, self.response(state, outcome='retry', values={}))
        self.assertEqual(f.pending(self.flow, state)['reason'], 'max_steps exhausted')

    def capability(self, available, authorization, effect='read'):
        self.flow['capabilities']['example'] = {'binding': 'actual_host.example',
            'effect': effect, 'available': available, 'authorization': authorization,
            'evidence': 'Test fixture capability declaration.'}
        self.flow['nodes'][0]['tools'] = ['example']

    def test_unavailable_capability_blocks(self):
        self.capability(False, 'not_applicable')
        self.assertTrue(f.validate(self.flow)['warnings'])
        state = f.start(self.flow, {'notes': ''})
        self.assertEqual(f.pending(self.flow, state)['status'], 'blocked')

    def test_missing_write_authorization_blocks(self):
        self.capability(True, 'required', 'external_write')
        state = f.start(self.flow, {'notes': ''})
        self.assertIn('authorization', f.pending(self.flow, state)['reason'])

    def test_external_authorization_not_applicable_rejected(self):
        self.capability(True, 'not_applicable', 'external_write')
        self.assertFalse(f.validate(self.flow)['valid'])

    def test_unknown_capability_rejected(self):
        self.flow['nodes'][0]['tools'] = ['imaginary']
        self.assertFalse(f.validate(self.flow)['valid'])

    def test_unknown_target_rejected(self):
        self.flow['nodes'][0]['routes']['ok'] = 'nowhere'
        self.assertFalse(f.validate(self.flow)['valid'])

    def test_unreachable_node_rejected(self):
        node = copy.deepcopy(self.flow['nodes'][0])
        node['id'] = 'unreachable'
        self.flow['nodes'].append(node)
        self.assertFalse(f.validate(self.flow)['valid'])

    def test_incomplete_final_output_rejected(self):
        self.flow['nodes'][0]['emits']['ok'] = []
        result = f.validate(self.flow)
        self.assertFalse(result['valid'])
        self.assertTrue(any('completion lacks' in e for e in result['errors']))

    def test_read_not_guaranteed_on_branch_rejected(self):
        first = self.flow['nodes'][0]
        second = copy.deepcopy(first)
        second.update(id='review', reads=['actions'], writes=[])
        second['emits']['ok'] = []
        first['routes']['ok'] = 'review'
        first['routes']['empty'] = 'review'
        first['emits']['empty'] = []
        self.flow['nodes'].append(second)
        result = f.validate(self.flow)
        self.assertFalse(result['valid'])
        self.assertTrue(any('not guaranteed' in e for e in result['errors']))

    def test_input_is_immutable(self):
        self.flow['nodes'][0]['writes'].append('notes')
        self.assertFalse(f.validate(self.flow)['valid'])

    def test_dispatch_slices_inputs(self):
        self.flow['inputs']['unrelated'] = {'type': 'string', 'description': 'Not needed by this node.'}
        state = f.start(self.flow, {'notes': '', 'unrelated': 'do not dispatch'})
        self.assertEqual(set(f.pending(self.flow, state)['inputs']), {'notes'})

    def test_empty_evidence_rejected(self):
        state = f.start(self.flow, {'notes': ''})
        response = self.response(state)
        response['evidence'] = []
        with self.assertRaises(f.FlowError):
            f.advance(self.flow, state, response)

    def test_boolean_not_integer_and_nested_nan_rejected(self):
        self.assertFalse(f.matches(True, 'integer'))
        self.assertFalse(f.matches(True, 'number'))
        state = f.start(self.flow, {'notes': ''})
        with self.assertRaises(ValueError):
            f.advance(self.flow, state, self.response(state, values={'actions': [float('nan')]}))

    def test_compiler_outputs_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'package'
            f.compile_flow(self.flow, target)
            self.assertEqual(f.load(target / 'flow.json'), self.flow)
            self.assertTrue((target / 'prompts/extract.md').is_file())
            self.assertIn('flowchart TD', (target / 'flow.mmd').read_text())
            with self.assertRaises(FileExistsError):
                f.compile_flow(self.flow, target)

    def test_checkpoint_roundtrip_and_exclusive_start(self):
        state = f.start(self.flow, {'notes': ''})
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'run.json'
            f.save(path, state, exclusive=True)
            self.assertEqual(f.load(path), state)
            with self.assertRaises(FileExistsError):
                f.save(path, state, exclusive=True)

    def test_cli_roundtrip_and_invalid_response_preserves_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            flow, inputs, state, response = [directory / x for x in ('flow.json','inputs.json','run.json','response.json')]
            f.save(flow, self.flow)
            f.save(inputs, {'notes': 'Nothing assigned.'})
            command = [sys.executable, str(ROOT / 'scripts/flowctl.py')]
            result = subprocess.run(command + ['start', str(flow), '--inputs', str(inputs), '--state', str(state)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            before = state.read_bytes()
            body = {'invocation_id': json.loads(result.stdout)['invocation_id'], 'outcome':'ok', 'artifacts':{'actions':{}}, 'evidence':['Fixture.']}
            f.save(response, body)
            result = subprocess.run(command + ['advance', str(flow), '--state', str(state), '--response', str(response)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(state.read_bytes(), before)
            body['artifacts']['actions'] = []
            f.save(response, body)
            result = subprocess.run(command + ['advance', str(flow), '--state', str(state), '--response', str(response)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'completed')


if __name__ == '__main__':
    unittest.main(verbosity=2)
