#!/usr/bin/env python3
"""Closed, deliberately small schema subset for Flow IR 1.1 artifacts.

This is not a JSON Schema implementation. It accepts only type, required,
properties, items, enum, minItems, and additionalProperties, with a bounded
schema depth and nullable unions of one non-null type plus null.
"""
from __future__ import annotations

import math

SCHEMA_TYPES = {"string", "object", "array", "integer", "number", "boolean", "null"}
NON_NULL_TYPES = SCHEMA_TYPES - {"null"}
SCHEMA_KEYS = {"type", "required", "properties", "items", "enum", "minItems",
               "additionalProperties"}
MAX_SCHEMA_DEPTH = 16


def _path_child(path, key):
    if isinstance(key, str) and key.isidentifier():
        return f"{path}.{key}"
    # JSON quoting keeps odd property names unambiguous in errors.
    import json
    return f"{path}[{json.dumps(key, ensure_ascii=False)}]"


def _array_path(path, index):
    return f"{path}[{index}]"


def _type_set(value):
    """Return an accepted type set, or None for an invalid type declaration."""
    if isinstance(value, str):
        return {value} if value in SCHEMA_TYPES else None
    if not isinstance(value, list) or len(value) != 2:
        return None
    if any(not isinstance(item, str) or item not in SCHEMA_TYPES for item in value):
        return None
    if len(set(value)) != len(value) or "null" not in value:
        return None
    if sum(item != "null" for item in value) != 1:
        return None
    return set(value)


def _matches_one(value, typename):
    if typename == "null":
        return value is None
    if typename == "boolean":
        return type(value) is bool
    if typename == "integer":
        return type(value) is int
    if typename == "number":
        return type(value) is int or (type(value) is float and math.isfinite(value))
    if typename == "string":
        return isinstance(value, str)
    if typename == "object":
        return isinstance(value, dict)
    if typename == "array":
        return isinstance(value, list)
    return False


def _validate_schema(schema, expected_type, path, depth):
    errors = []
    if depth >= MAX_SCHEMA_DEPTH:
        return [f"{path}: schema exceeds maximum depth of {MAX_SCHEMA_DEPTH}"]
    if not isinstance(schema, dict):
        return [f"{path}: schema must be an object"]

    unknown = set(schema) - SCHEMA_KEYS
    if unknown:
        errors.append(f"{path}: unsupported schema keyword(s): {sorted(map(str, unknown))}")
    type_set = _type_set(schema.get("type"))
    if type_set is None:
        errors.append(f"{path}.type: must be a supported type or a nullable [type, 'null'] pair")
        # Continue checking independent shape/keyword errors, but do not infer
        # a base type from a malformed declaration.
        base_type = None
    else:
        base_type = next((item for item in type_set if item != "null"), "null")
        if expected_type is not None and type_set != {expected_type}:
            errors.append(f"{path}.type: must match descriptor type {expected_type!r}")

    if "required" in schema:
        required = schema["required"]
        if base_type != "object":
            errors.append(f"{path}.required: allowed only for object schemas")
        if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
            errors.append(f"{path}.required: must be a string list")
        elif len(required) != len(set(required)):
            errors.append(f"{path}.required: duplicate property names")

    if "properties" in schema:
        properties = schema["properties"]
        if base_type != "object":
            errors.append(f"{path}.properties: allowed only for object schemas")
        if not isinstance(properties, dict) or any(not isinstance(key, str) for key in properties):
            errors.append(f"{path}.properties: must be an object keyed by property names")
        else:
            for key, child in properties.items():
                errors.extend(_validate_schema(child, None, _path_child(f"{path}.properties", key), depth + 1))

    if "items" in schema:
        if base_type != "array":
            errors.append(f"{path}.items: allowed only for array schemas")
        errors.extend(_validate_schema(schema["items"], None, f"{path}.items", depth + 1))

    if "minItems" in schema:
        minimum = schema["minItems"]
        if base_type != "array":
            errors.append(f"{path}.minItems: allowed only for array schemas")
        if type(minimum) is not int or minimum < 0:
            errors.append(f"{path}.minItems: must be a non-negative integer")

    if "additionalProperties" in schema:
        if base_type != "object":
            errors.append(f"{path}.additionalProperties: allowed only for object schemas")
        if type(schema["additionalProperties"]) is not bool:
            errors.append(f"{path}.additionalProperties: must be boolean")

    if "required" in schema and isinstance(schema.get("required"), list) and all(
            isinstance(item, str) for item in schema["required"]):
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        if additional is False and isinstance(properties, dict):
            missing = set(schema["required"]) - set(properties)
            if missing:
                errors.append(f"{path}.required: impossible with additionalProperties false; "
                              f"undeclared {sorted(missing)}")

    if "enum" in schema:
        enum = schema["enum"]
        if not isinstance(enum, list) or not enum:
            errors.append(f"{path}.enum: must be a non-empty list")
        else:
            # The JSON encoding makes bool and number values distinct, unlike
            # Python's `True == 1`; it also rejects non-finite enum numbers.
            import json
            try:
                encoded = [json.dumps(value, sort_keys=True, separators=(",", ":"),
                                      ensure_ascii=False, allow_nan=False) for value in enum]
            except (TypeError, ValueError, OverflowError):
                encoded = []
                errors.append(f"{path}.enum: values must be finite JSON values")
            if encoded and len(encoded) != len(set(encoded)):
                errors.append(f"{path}.enum: duplicate values")
            if type_set is not None:
                for index, value in enumerate(enum):
                    if not any(_matches_one(value, item) for item in type_set):
                        errors.append(f"{_array_path(path + '.enum', index)}: value does not match declared type")

    return errors


def schema_errors(schema, expected_type, path):
    """Return schema-definition errors, including the descriptor type binding."""
    return _validate_schema(schema, expected_type, path, 0)


def _validate_value(value, schema, path):
    errors = []
    type_set = _type_set(schema.get("type"))
    # Flow validation has already validated schemas, but keep this function
    # fail-closed when used directly or if a caller bypasses validate().
    if type_set is None:
        return [f"{path}: invalid schema type"]
    if not any(_matches_one(value, item) for item in type_set):
        label = " or ".join(sorted(type_set))
        return [f"{path}: expected {label}"]

    enum = schema.get("enum")
    if enum is not None and not any(_same_json_value(value, choice) for choice in enum):
        return [f"{path}: value is not in enum"]

    base_type = next((item for item in type_set if item != "null"), "null")
    if value is None:
        return errors
    if base_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for name in required:
            if name not in value:
                errors.append(f"{_path_child(path, name)}: required property is missing")
        for name, child_value in value.items():
            child_schema = properties.get(name)
            if child_schema is None:
                if schema.get("additionalProperties", True) is False:
                    errors.append(f"{_path_child(path, name)}: additional property is not allowed")
            else:
                errors.extend(_validate_value(child_value, child_schema, _path_child(path, name)))
    elif base_type == "array":
        minimum = schema.get("minItems", 0)
        if len(value) < minimum:
            errors.append(f"{path}: expected at least {minimum} items")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, child_value in enumerate(value):
                errors.extend(_validate_value(child_value, item_schema, _array_path(path, index)))
    return errors


def _same_json_value(left, right):
    """Compare JSON values without Python's bool/int equality ambiguity."""
    import json
    try:
        left_json = json.dumps(left, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False, allow_nan=False)
        right_json = json.dumps(right, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, OverflowError):
        return False
    return left_json == right_json


def value_errors(value, schema, path):
    """Return instance errors with paths rooted at the artifact/input name."""
    malformed = schema_errors(schema, None, f"{path}.schema")
    if malformed:
        return malformed
    return _validate_value(value, schema, path)
