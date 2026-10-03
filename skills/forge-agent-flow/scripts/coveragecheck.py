"""Validate an independent branch-coverage sidecar for a frozen Forge plan.

This checker verifies declared coverage structure and binding. It does not infer
requirements from prose or decide whether a designer's declared branches are
semantically complete.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys

import evalplan
import flowctl


SCHEMA = "forge-coverage/1"
ROOT_KEYS = {"schema", "plan_hash", "entries"}
ENTRY_KEYS = {"requirement_id", "criterion_id", "scope", "applicability", "obligations"}
APPLICABILITY_KEYS = {
    "negative",
    "recovery",
    "reuse",
    "authorization",
    "ui_feedback",
    "explanation",
}
KINDS = {
    "success",
    "negative",
    "recovery",
    "reuse",
    "authorization_allowed",
    "authorization_denied",
    "ui_feedback",
    "explanation",
}
DISTINCT_BRANCH_PAIRS = {
    frozenset(("success", "negative")),
    frozenset(("success", "recovery")),
    frozenset(("success", "reuse")),
    frozenset(("success", "authorization_denied")),
    frozenset(("negative", "recovery")),
    frozenset(("authorization_allowed", "authorization_denied")),
}
DISTINCT_BRANCH_KINDS = {"success", "negative", "recovery", "reuse", "authorization_allowed", "authorization_denied"}
OBLIGATION_KEYS = {"id", "kind", "case_ids", "input_variant", "expected_fields"}
HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _safe_id(value):
    return type(value) is str and flowctl.IDENT.fullmatch(value) is not None


def _nonempty_text(value):
    return type(value) is str and bool(value.strip())


def _check_exact_keys(value, expected, path, errors):
    missing = sorted(key for key in expected if key not in value)
    unexpected = [key for key in value if type(key) is not str or key not in expected]
    if missing:
        errors.append(f"{path}: missing required key(s): {', '.join(missing)}")
    if unexpected:
        errors.append(f"{path}: unexpected key(s): {', '.join(repr(key) for key in unexpected)}")


def _object(value, path, errors):
    if type(value) is not dict:
        errors.append(f"{path}: must be an object")
        return False
    return True


def _json_pointer(value, pointer):
    """Return (found, value) for a JSON Pointer into an expected object."""
    if type(pointer) is not str or not pointer.startswith("/"):
        return False, None
    current = value
    for raw_token in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw_token):
            return False, None
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if type(current) is dict:
            if token not in current:
                return False, None
            current = current[token]
        elif type(current) is list and token.isdigit():
            index = int(token)
            if index >= len(current):
                return False, None
            current = current[index]
        else:
            return False, None
    return True, current


def _specific_reason(value):
    """An explanation target must contain authored content, not a blank sentinel."""
    if type(value) is str:
        return bool(value.strip())
    if type(value) is list:
        return bool(value) and all(_specific_reason(item) for item in value)
    if type(value) is dict:
        return bool(value) and all(_specific_reason(item) for item in value.values())
    return False


def _requires_distinct_branch_inputs(left_kind, right_kind):
    if left_kind == right_kind and left_kind in DISTINCT_BRANCH_KINDS:
        return True
    return frozenset((left_kind, right_kind)) in DISTINCT_BRANCH_PAIRS


def _json_load_strict(path):
    def reject_constant(token):
        raise ValueError(f"non-finite JSON number {token!r} is not allowed")

    def finite_float(token):
        value = float(token)
        if not math.isfinite(value):
            raise ValueError(f"non-finite JSON number {token!r} is not allowed")
        return value

    def no_duplicate_keys(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError(f"duplicate JSON object key {key!r}")
            obj[key] = value
        return obj

    try:
        with open(path, "r", encoding="utf-8") as stream:
            return json.load(
                stream,
                object_pairs_hook=no_duplicate_keys,
                parse_constant=reject_constant,
                parse_float=finite_float,
            )
    except (OSError, UnicodeError, TypeError, ValueError, RecursionError) as exc:
        raise flowctl.FlowError(f"could not load coverage sidecar from {path!r}: {exc}") from exc


def assess(plan, coverage):
    """Return ``{valid, errors}`` for a sidecar bound to the complete plan.

    ``plan`` is a complete ``forge-eval/1`` object, not a summary or a lock
    envelope. ``coverage.plan_hash`` must equal the canonical digest of it.
    """
    errors = []
    plan_result = evalplan.validate(plan)
    if not plan_result["valid"]:
        errors.extend(f"plan: {error}" for error in plan_result["errors"])
        return {"valid": False, "errors": errors}
    if type(plan) is not dict:
        return {"valid": False, "errors": ["plan: must be a JSON object"]}

    if not _object(coverage, "coverage", errors):
        return {"valid": False, "errors": errors}
    _check_exact_keys(coverage, ROOT_KEYS, "coverage", errors)
    if coverage.get("schema") != SCHEMA:
        errors.append(f"coverage.schema: must equal {SCHEMA!r}")

    try:
        expected_hash = flowctl.digest(plan)
    except (TypeError, ValueError, RecursionError):
        expected_hash = None
    plan_hash = coverage.get("plan_hash")
    if type(plan_hash) is not str or not HASH_RE.fullmatch(plan_hash):
        errors.append("coverage.plan_hash: must be a lowercase SHA256 hex digest")
    elif expected_hash is not None and plan_hash != expected_hash:
        errors.append("coverage.plan_hash: does not match the canonical complete plan digest")

    raw_criteria = plan.get("criteria")
    criteria = {
        criterion["id"]: criterion
        for criterion in raw_criteria if type(criterion) is dict and type(criterion.get("id")) is str
    } if type(raw_criteria) is list else {}
    cases = {
        case["id"]: case
        for case in plan.get("cases", [])
        if type(case) is dict and type(case.get("id")) is str
    } if type(plan.get("cases")) is list else {}

    raw_entries = coverage.get("entries")
    if type(raw_entries) is not list or not raw_entries:
        errors.append("coverage.entries: must be a nonempty array")
        return {"valid": not errors, "errors": errors}

    seen_pairs = set()
    seen_criteria = set()
    seen_obligation_ids = set()
    for index, entry in enumerate(raw_entries):
        path = f"coverage.entries[{index}]"
        if not _object(entry, path, errors):
            continue
        _check_exact_keys(entry, ENTRY_KEYS, path, errors)

        requirement_id = entry.get("requirement_id")
        if not _safe_id(requirement_id):
            errors.append(f"{path}.requirement_id: must be a safe lowercase identifier")

        criterion_id = entry.get("criterion_id")
        criterion = criteria.get(criterion_id) if _safe_id(criterion_id) else None
        if not _safe_id(criterion_id):
            errors.append(f"{path}.criterion_id: must be a safe lowercase identifier")
        elif criterion is None:
            errors.append(f"{path}.criterion_id: unknown criterion ID {criterion_id!r}")
        elif criterion.get("required") is not True:
            errors.append(
                f"{path}.criterion_id: {criterion_id!r} is optional and cannot discharge required branch coverage"
            )
        else:
            seen_criteria.add(criterion_id)

        pair = (requirement_id, criterion_id)
        if _safe_id(requirement_id) and _safe_id(criterion_id):
            if pair in seen_pairs:
                errors.append(f"{path}: duplicate requirement/criterion mapping {requirement_id!r}/{criterion_id!r}")
            seen_pairs.add(pair)

        if not _nonempty_text(entry.get("scope")):
            errors.append(f"{path}.scope: must briefly state the behavior covered by this mapping")

        applicability = entry.get("applicability")
        if _object(applicability, f"{path}.applicability", errors):
            _check_exact_keys(applicability, APPLICABILITY_KEYS, f"{path}.applicability", errors)
            for dimension in sorted(APPLICABILITY_KEYS):
                dimension_path = f"{path}.applicability.{dimension}"
                declaration = applicability.get(dimension)
                if not _object(declaration, dimension_path, errors):
                    continue
                _check_exact_keys(declaration, {"applies", "reason"}, dimension_path, errors)
                if type(declaration.get("applies")) is not bool:
                    errors.append(f"{dimension_path}.applies: must be a boolean")
                if not _nonempty_text(declaration.get("reason")):
                    errors.append(f"{dimension_path}.reason: must briefly state its scope or why it does not apply")

        raw_obligations = entry.get("obligations")
        if type(raw_obligations) is not list or not raw_obligations:
            errors.append(f"{path}.obligations: must be a nonempty array of independent obligations")
            continue

        kinds_present = set()
        obligation_fixtures = []
        for obligation_index, obligation in enumerate(raw_obligations):
            obligation_path = f"{path}.obligations[{obligation_index}]"
            if not _object(obligation, obligation_path, errors):
                continue
            kind = obligation.get("kind")
            extra_keys = set()
            if kind == "explanation":
                extra_keys = {"reason_fields"}
            elif kind == "ui_feedback":
                extra_keys = {"ui_fields"}
            _check_exact_keys(obligation, OBLIGATION_KEYS | extra_keys, obligation_path, errors)

            obligation_id = obligation.get("id")
            if not _safe_id(obligation_id):
                errors.append(f"{obligation_path}.id: must be a safe lowercase identifier")
            elif obligation_id in seen_obligation_ids:
                errors.append(f"{obligation_path}.id: duplicate obligation ID {obligation_id!r}")
            else:
                seen_obligation_ids.add(obligation_id)

            if type(kind) is not str or kind not in KINDS:
                errors.append(f"{obligation_path}.kind: must be one of {', '.join(sorted(KINDS))}")
            else:
                kinds_present.add(kind)

            if not _nonempty_text(obligation.get("input_variant")):
                errors.append(f"{obligation_path}.input_variant: must describe the distinct triggering input")

            case_ids = obligation.get("case_ids")
            valid_case_ids = []
            obligation_input_digests = {}
            if type(case_ids) is not list or not case_ids:
                errors.append(f"{obligation_path}.case_ids: must be a nonempty array of required case IDs")
            else:
                local_case_ids = set()
                for case_index, case_id in enumerate(case_ids):
                    case_path = f"{obligation_path}.case_ids[{case_index}]"
                    if not _safe_id(case_id):
                        errors.append(f"{case_path}: must be a safe lowercase case ID")
                        continue
                    if case_id in local_case_ids:
                        errors.append(f"{case_path}: duplicate case ID {case_id!r}")
                        continue
                    local_case_ids.add(case_id)
                    case = cases.get(case_id)
                    if case is None:
                        errors.append(f"{case_path}: unknown case ID {case_id!r}")
                        continue
                    if case.get("required") is not True:
                        errors.append(f"{case_path}: {case_id!r} is optional; branch obligations require required cases")
                    if type(criterion_id) is str and criterion_id not in case.get("criteria", []):
                        errors.append(
                            f"{case_path}: case {case_id!r} does not reference mapped criterion {criterion_id!r}"
                        )
                    valid_case_ids.append(case_id)

                    inputs = case.get("inputs")
                    expected = case.get("expected")
                    if type(inputs) is dict and type(expected) is dict:
                        if not expected:
                            errors.append(f"{case_path}: expected output must not be empty")
                        elif flowctl.digest(inputs) == flowctl.digest(expected):
                            errors.append(f"{case_path}: expected output is identical to inputs and declares no output variant")
                        input_digest = flowctl.digest(inputs)
                        if input_digest in obligation_input_digests:
                            previous = ", ".join(obligation_input_digests[input_digest])
                            errors.append(
                                f"{case_path}: input fixture duplicates case(s) {previous!r} within this obligation"
                            )
                        else:
                            obligation_input_digests[input_digest] = [case_id]

            if type(kind) is str and kind in KINDS:
                obligation_fixtures.append({
                    "id": obligation.get("id"),
                    "kind": kind,
                    "case_ids": set(valid_case_ids),
                    "input_cases": obligation_input_digests,
                    "path": obligation_path,
                })

            expected_fields = obligation.get("expected_fields")
            valid_expected_fields = []
            if type(expected_fields) is not list or not expected_fields:
                errors.append(f"{obligation_path}.expected_fields: must list explicit JSON Pointer output fields")
            else:
                field_seen = set()
                for field_index, pointer in enumerate(expected_fields):
                    field_path = f"{obligation_path}.expected_fields[{field_index}]"
                    if type(pointer) is not str or not pointer.startswith("/"):
                        errors.append(f"{field_path}: must be a JSON Pointer into each case's expected object")
                        continue
                    if pointer in field_seen:
                        errors.append(f"{field_path}: duplicate expected field {pointer!r}")
                        continue
                    field_seen.add(pointer)
                    valid_expected_fields.append(pointer)
                    for case_id in valid_case_ids:
                        case = cases[case_id]
                        found, value = _json_pointer(case.get("expected"), pointer)
                        if not found:
                            errors.append(
                                f"{field_path}: {pointer!r} is absent from case {case_id!r} expected output"
                            )

            if kind == "explanation":
                reason_fields = obligation.get("reason_fields")
                if type(reason_fields) is not list or not reason_fields:
                    errors.append(f"{obligation_path}.reason_fields: explanation obligations must name concrete reason/basis output fields")
                else:
                    for reason_index, pointer in enumerate(reason_fields):
                        reason_path = f"{obligation_path}.reason_fields[{reason_index}]"
                        if type(pointer) is not str or pointer not in valid_expected_fields:
                            errors.append(f"{reason_path}: must reference a field listed in expected_fields")
                            continue
                        for case_id in valid_case_ids:
                            found, value = _json_pointer(cases[case_id].get("expected"), pointer)
                            if not found or not _specific_reason(value):
                                errors.append(
                                    f"{reason_path}: case {case_id!r} needs a specific nonempty reason/basis expectation"
                                )
            elif "reason_fields" in obligation:
                errors.append(f"{obligation_path}.reason_fields: only explanation obligations may use reason_fields")

            if kind == "ui_feedback":
                ui_fields = obligation.get("ui_fields")
                if type(ui_fields) is not list or not ui_fields:
                    errors.append(f"{obligation_path}.ui_fields: UI obligations must name concrete visible/UI output fields")
                else:
                    for ui_index, pointer in enumerate(ui_fields):
                        ui_path = f"{obligation_path}.ui_fields[{ui_index}]"
                        if type(pointer) is not str or pointer not in valid_expected_fields:
                            errors.append(f"{ui_path}: must reference a field listed in expected_fields")
            elif "ui_fields" in obligation:
                errors.append(f"{obligation_path}.ui_fields: only ui_feedback obligations may use ui_fields")

        for left_index, left in enumerate(obligation_fixtures):
            for right in obligation_fixtures[left_index + 1:]:
                if not _requires_distinct_branch_inputs(left["kind"], right["kind"]):
                    continue
                shared_cases = sorted(left["case_ids"] & right["case_ids"])
                if shared_cases:
                    errors.append(
                        f"{left['path']} and {right['path']}: distinct {left['kind']!r}/{right['kind']!r} branches reuse case(s): {', '.join(shared_cases)}"
                    )
                shared_inputs = set(left["input_cases"]) & set(right["input_cases"])
                for input_hash in sorted(shared_inputs):
                    left_cases = ", ".join(left["input_cases"][input_hash])
                    right_cases = ", ".join(right["input_cases"][input_hash])
                    errors.append(
                        f"{left['path']} and {right['path']}: distinct {left['kind']!r}/{right['kind']!r} branches have identical input fixture(s) ({left_cases}; {right_cases})"
                    )

        if "success" not in kinds_present:
            errors.append(f"{path}.obligations: every required criterion mapping needs a success obligation")

        if type(applicability) is dict:
            applicable = {
                name: declaration.get("applies")
                for name, declaration in applicability.items()
                if type(declaration) is dict
            }
            obligations_by_kind = {}
            for obligation in raw_obligations:
                if type(obligation) is dict and type(obligation.get("kind")) is str:
                    obligations_by_kind.setdefault(obligation["kind"], []).append(obligation)
            required_kind_by_dimension = {
                "negative": {"negative"},
                "recovery": {"recovery"},
                "reuse": {"reuse"},
                "authorization": {"authorization_allowed", "authorization_denied"},
                "ui_feedback": {"ui_feedback"},
                "explanation": {"explanation"},
            }
            for dimension in sorted(APPLICABILITY_KEYS):
                applies = applicable.get(dimension)
                required_kinds = required_kind_by_dimension[dimension]
                declared_kinds = required_kinds & kinds_present
                if applies is True:
                    missing_kinds = sorted(required_kinds - kinds_present)
                    if missing_kinds:
                        errors.append(
                            f"{path}.applicability.{dimension}: applicable dimension is missing obligation kind(s): {', '.join(missing_kinds)}"
                        )
                elif applies is False:
                    unexpected_kinds = sorted(declared_kinds)
                    if unexpected_kinds:
                        errors.append(
                            f"{path}.applicability.{dimension}: marked not applicable but declares kind(s): {', '.join(unexpected_kinds)}"
                        )
            if applicable.get("recovery") is True and applicable.get("negative") is not True:
                errors.append(f"{path}.applicability.recovery: recovery also requires the negative branch to be applicable")
            if applicable.get("authorization") is True:
                if not obligations_by_kind.get("authorization_allowed"):
                    errors.append(f"{path}.applicability.authorization: authorization requires an allowed case")
                if not obligations_by_kind.get("authorization_denied"):
                    errors.append(f"{path}.applicability.authorization: authorization requires a denied case")

    required_criteria = {
        criterion_id
        for criterion_id, criterion in criteria.items()
        if criterion.get("required") is True
    }
    missing_criteria = sorted(required_criteria - seen_criteria)
    if missing_criteria:
        errors.append(f"coverage.entries: missing required criterion mapping(s): {', '.join(missing_criteria)}")

    return {"valid": not errors, "errors": errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description="validate an independent forge-coverage/1 sidecar")
    parser.add_argument("command", choices=("validate",))
    parser.add_argument("plan", help="complete forge-eval/1 plan JSON")
    parser.add_argument("coverage", help="forge-coverage/1 sidecar JSON")
    args = parser.parse_args(argv)
    try:
        plan = evalplan.load(args.plan)
        coverage = _json_load_strict(args.coverage)
        result = assess(plan, coverage)
    except flowctl.FlowError as exc:
        print(f"invalid: {exc}")
        return 1
    if result["valid"]:
        print(f"valid: {SCHEMA} covers required branches for plan {plan['id']!r}")
        return 0
    for error in result["errors"]:
        print(f"error: {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
