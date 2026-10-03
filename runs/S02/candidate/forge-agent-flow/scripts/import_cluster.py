#!/usr/bin/env python3
"""Safely preserve a cluster-architect design as a Forge translation brief.

This importer deliberately does not translate legacy policy into executable
Flow IR. It is stdlib-only and performs no model, shell, or adapter calls.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


LEGACY_SCHEMA = "cluster-architect/design/1"
BRIEF_SCHEMA = "forge/legacy-brief/1"
SAFE_ROLE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")

UNRESOLVED = [
    "Legacy roles do not declare Forge typed artifacts or per-outcome routes; these must be designed during translation.",
    "Actual host mappings are unverified for every model, tool, guard, write_scope, approval gate, and budget.",
    "Legacy source concurrency cannot be mapped to Forge's serial host-driven engine; no parallel execution is implied.",
    "concurrency.sizing_inputs is preserved verbatim and has not been validated; the source hard_cap is neither recalculated nor endorsed.",
]


class ImportDesignError(ValueError):
    """The legacy input cannot be represented safely as a translation brief."""


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ImportDesignError(f"Design is not canonical finite JSON data: {exc}") from exc


def _check_finite(value: Any, location: str = "design") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ImportDesignError(f"{location} contains a non-finite number")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ImportDesignError(f"{location} contains a non-string object key")
            _check_finite(child, f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _check_finite(child, f"{location}[{index}]")


def _normalized_id(role_id: str) -> str:
    # Restrict IDs to one safe path component before deriving a node name.
    if not SAFE_ROLE_ID.fullmatch(role_id):
        raise ImportDesignError(
            f"Unsafe role ID {role_id!r}: expected 1-64 ASCII letters, digits, '_' or '-', starting with a letter"
        )
    return role_id.lower().replace("-", "_")


def inspect_design(design: dict) -> dict:
    """Return a non-executable, loss-preserving Forge translation brief."""
    if not isinstance(design, dict):
        raise ImportDesignError("Design root must be a JSON object")
    _check_finite(design)
    # Validate JSON representability before deriving the digest or copying it.
    canonical = _canonical(design)

    if design.get("schema") != LEGACY_SCHEMA:
        raise ImportDesignError(f"Missing or unsupported schema; expected {LEGACY_SCHEMA!r}")
    source_roles = design.get("roles")
    if not isinstance(source_roles, list) or not source_roles:
        raise ImportDesignError("Required 'roles' field must be a non-empty array")

    roles = []
    seen_ids: set[str] = set()
    seen_normalized: dict[str, str] = {}
    for index, role in enumerate(source_roles):
        if not isinstance(role, dict):
            raise ImportDesignError(f"roles[{index}] must be an object")
        if "proposed_node_id" in role:
            raise ImportDesignError(
                f"roles[{index}].proposed_node_id is reserved by the importer"
            )
        if "id" not in role or not isinstance(role["id"], str):
            raise ImportDesignError(f"roles[{index}].id must be a string")
        role_id = role["id"]
        proposed = _normalized_id(role_id)
        if role_id in seen_ids:
            raise ImportDesignError(f"Duplicate role ID: {role_id!r}")
        if proposed in seen_normalized:
            raise ImportDesignError(
                f"Role IDs {seen_normalized[proposed]!r} and {role_id!r} collide after normalization to {proposed!r}"
            )
        seen_ids.add(role_id)
        seen_normalized[proposed] = role_id
        preserved_role = copy.deepcopy(role)
        preserved_role["proposed_node_id"] = proposed
        roles.append(preserved_role)

    return {
        "schema": BRIEF_SCHEMA,
        "status": "needs_translation",
        "source_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "source_design": copy.deepcopy(design),
        "roles": roles,
        "unresolved": list(UNRESOLVED),
    }


def _reject_constant(value: str) -> None:
    raise ImportDesignError(f"Non-finite JSON number is not allowed: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ImportDesignError(f"Duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def load_design(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as stream:
            design = json.load(stream, object_pairs_hook=_unique_object,
                               parse_constant=_reject_constant)
    except ImportDesignError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ImportDesignError(f"Cannot read valid JSON design from {path}: {exc}") from exc
    if not isinstance(design, dict):
        raise ImportDesignError("Design root must be a JSON object")
    return design


def write_new(path: Path, value: dict) -> None:
    """Publish complete JSON only if the requested destination is new."""
    body = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=".legacy-brief-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        # Hard-link publication is atomic and fails rather than replacing a file.
        os.link(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", type=Path, help="legacy cluster-architect design JSON")
    parser.add_argument("--out", required=True, type=Path, help="new JSON path; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        result = inspect_design(load_design(args.design))
        write_new(args.out, result)
    except (ImportDesignError, OSError) as exc:
        print(f"import_cluster: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote translation brief: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
