"""Focused fixtures for Flow IR 1.1's intentionally restricted schema subset."""
import unittest

import nestedcheck as n


class NestedCheckTests(unittest.TestCase):
    def test_nullable_types_and_strict_integer_matching(self):
        schema = {'type': ['string', 'null']}
        self.assertEqual(n.schema_errors(schema, None, 'field.schema'), [])
        self.assertEqual(n.value_errors(None, schema, 'field'), [])
        self.assertEqual(n.value_errors('name', schema, 'field'), [])
        self.assertTrue(n.value_errors(4, schema, 'field'))
        self.assertTrue(n.value_errors(True, {'type': 'integer'}, 'field'))
        self.assertTrue(n.value_errors(True, {'type': 'number'}, 'field'))
        self.assertEqual(n.value_errors(4, {'type': 'integer'}, 'field'), [])

    def test_object_required_properties_and_additional_properties_paths(self):
        schema = {
            'type': 'object', 'required': ['quote'],
            'properties': {'quote': {'type': 'string'}, 'owner': {'type': ['string', 'null']}},
            'additionalProperties': False,
        }
        self.assertEqual(n.value_errors({'quote': 'source', 'owner': None}, schema, 'actions[0]'), [])
        self.assertIn('actions[0].quote', n.value_errors({'owner': None}, schema, 'actions[0]')[0])
        self.assertIn('actions[0].extra', n.value_errors(
            {'quote': 'source', 'extra': 1}, schema, 'actions[0]')[0])
        self.assertIn('actions[0].owner', n.value_errors(
            {'quote': 'source', 'owner': {}}, schema, 'actions[0]')[0])

    def test_array_empty_list_and_minimum(self):
        self.assertEqual(n.value_errors([], {'type': 'array', 'items': {'type': 'string'}}, 'rows'), [])
        self.assertTrue(n.value_errors([], {'type': 'array', 'minItems': 1}, 'rows'))
        self.assertTrue(n.schema_errors({'type': 'array', 'minItems': True}, None, 'rows.schema'))

    def test_unknown_and_incompatible_schema_keywords_fail_closed(self):
        for schema in (
            {'type': 'object', '$ref': '#/x'},
            {'type': 'object', 'items': {'type': 'string'}},
            {'type': 'array', 'required': ['x']},
            {'type': 'string', 'additionalProperties': False},
            {'type': ['object', 'array']},
            {'type': ['string', 'null', 'boolean']},
        ):
            with self.subTest(schema=schema):
                self.assertTrue(n.schema_errors(schema, None, 'value.schema'))

    def test_descriptor_root_type_must_match_and_schema_depth_is_bounded(self):
        self.assertTrue(n.schema_errors({'type': 'object'}, 'array', 'value.schema'))
        deep = {'type': 'string'}
        for _ in range(n.MAX_SCHEMA_DEPTH):
            deep = {'type': 'object', 'properties': {'child': deep}}
        errors = n.schema_errors(deep, 'object', 'value.schema')
        self.assertTrue(any('maximum depth' in error for error in errors), errors)

    def test_enum_compares_nested_boolean_and_integer_values_exactly(self):
        schema = {'type': 'object', 'enum': [{'x': 1}]}
        self.assertEqual(n.value_errors({'x': 1}, schema, 'field'), [])
        self.assertTrue(n.value_errors({'x': True}, schema, 'field'))
        self.assertEqual(n.schema_errors({'type': 'array', 'enum': [[1], [True]]}, None, 'arr'), [])

    def test_required_with_closed_object_without_properties_is_impossible(self):
        errors = n.schema_errors({'type': 'object', 'required': ['x'],
                                  'additionalProperties': False}, None, 'obj.schema')
        self.assertTrue(any('impossible' in error for error in errors), errors)

    def test_enum_must_be_nonempty_unique_and_type_compatible(self):
        for schema in (
            {'type': 'string', 'enum': []},
            {'type': 'integer', 'enum': [True]},
            {'type': 'integer', 'enum': [1, 1]},
        ):
            with self.subTest(schema=schema):
                self.assertTrue(n.schema_errors(schema, None, 'value.schema'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
