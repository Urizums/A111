"""Validation and lock helpers for complete Forge evaluation plans."""

from __future__ import annotations

import copy
import json
import math

import flowctl


SCHEMA = "forge-eval/1"
PLAN_KEYS = {"schema", "id", "criteria", "cases", "baseline", "limitations"}
CRITERION_KEYS = {"id", "kind", "required", "assertion"}
CASE_KEYS = {"id", "inputs", "expected", "expected_status", "criteria", "required"}
LOCK_KEYS = {"plan", "plan_hash"}


def _path_key(key):
    return f"[{key!r}]"


def _scan_json_value(value, path, errors, active):
    """Check the full plan uses only finite, acyclic JSON values."""
    if value is None or type(value) is bool or type(value) is int:
        return
    if type(value) is float:
        if not math.isfinite(value):
            errors.append(f"{path}: numbers must be finite")
        return
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            errors.append(f"{path}: text must contain valid Unicode scalar values")
        return
    if type(value) is list:
        marker = id(value)
        if marker in active:
            errors.append(f"{path}: cyclic values are not valid JSON")
            return
        active.add(marker)
        try:
            for index, item in enumerate(value):
                _scan_json_value(item, f"{path}[{index}]", errors, active)
        finally:
            active.remove(marker)
        return
    if type(value) is dict:
        marker = id(value)
        if marker in active:
            errors.append(f"{path}: cyclic values are not valid JSON")
            return
        active.add(marker)
        try:
            for key, item in value.items():
                if type(key) is not str:
                    errors.append(f"{path}: object keys must be strings; found {key!r}")
                    child_path = f"{path}[{key!r}]"
                else:
                    try:
                        key.encode("utf-8")
                    except UnicodeEncodeError:
                        errors.append(f"{path}: object keys must contain valid Unicode scalar values")
                    child_path = f"{path}{_path_key(key)}"
                _scan_json_value(item, child_path, errors, active)
        finally:
            active.remove(marker)
        return
    errors.append(f"{path}: {type(value).__name__} is not a JSON value")


def _check_exact_keys(value, expected, path, errors):
    missing = sorted(key for key in expected if key not in value)
    unexpected = [key for key in value if type(key) is not str or key not in expected]
    if missing:
        errors.append(f"{path}: missing required key(s): {', '.join(missing)}")
    if unexpected:
        errors.append(f"{path}: unexpected key(s): {', '.join(repr(key) for key in unexpected)}")


def _valid_id(value):
    return type(value) is str and flowctl.IDENT.fullmatch(value) is not None


def _nonempty_text(value):
    return type(value) is str and bool(value.strip())


def validate(plan):
    """Return structural and coverage errors for a complete evaluation plan."""
    errors = []
    if type(plan) is not dict:
        return {"valid": False, "errors": ["plan: must be a JSON object"]}

    try:
        _scan_json_value(plan, "$", errors, set())
    except RecursionError:
        errors.append("$: nesting is too deep to validate as JSON")

    _check_exact_keys(plan, PLAN_KEYS, "plan", errors)
    if plan.get("schema") != SCHEMA:
        errors.append(f"plan.schema: must equal {SCHEMA!r}")
    if not _valid_id(plan.get("id")):
        errors.append("plan.id: must match flowctl.IDENT (lowercase safe identifier)")

    criterion_ids = set()
    criterion_required_ids = set()
    raw_criteria = plan.get("criteria")
    criteria_items = raw_criteria if type(raw_criteria) is list else None
    if criteria_items is None:
        errors.append("plan.criteria: must be a nonempty list")
    elif not criteria_items:
        errors.append("plan.criteria: must be a nonempty list")
    else:
        for index, criterion in enumerate(criteria_items):
            path = f"plan.criteria[{index}]"
            if type(criterion) is not dict:
                errors.append(f"{path}: must be an object")
                continue
            _check_exact_keys(criterion, CRITERION_KEYS, path, errors)

            criterion_id = criterion.get("id")
            if not _valid_id(criterion_id):
                errors.append(f"{path}.id: must be a safe lowercase snake_case identifier")
            if type(criterion_id) is str:
                if criterion_id in criterion_ids:
                    errors.append(f"{path}.id: duplicate criterion ID {criterion_id!r}")
                criterion_ids.add(criterion_id)

            kind = criterion.get("kind")
            if type(kind) is not str or kind not in ("machine", "human"):
                errors.append(f"{path}.kind: must be 'machine' or 'human'")

            required = criterion.get("required")
            if type(required) is not bool:
                errors.append(f"{path}.required: must be a boolean")
            elif required and type(criterion_id) is str:
                criterion_required_ids.add(criterion_id)

            if not _nonempty_text(criterion.get("assertion")):
                errors.append(f"{path}.assertion: must be nonempty text")

    if criteria_items is not None and not criterion_required_ids:
        errors.append("plan.criteria: at least one criterion must be required")

    baseline = plan.get("baseline")
    if not _nonempty_text(baseline):
        errors.append("plan.baseline: must be nonempty text")

    limitations = plan.get("limitations")
    if type(limitations) is not list:
        errors.append("plan.limitations: must be a list of strings")
    else:
        for index, limitation in enumerate(limitations):
            if type(limitation) is not str:
                errors.append(f"plan.limitations[{index}]: must be a string")

    referenced_ids = set()
    required_case_covered_ids = set()
    raw_cases = plan.get("cases")
    case_items = raw_cases if type(raw_cases) is list else None
    if case_items is None:
        errors.append("plan.cases: must be a nonempty list")
    elif not case_items:
        errors.append("plan.cases: must be a nonempty list")
    else:
        seen_case_ids = set()
        for index, case in enumerate(case_items):
            path = f"plan.cases[{index}]"
            if type(case) is not dict:
                errors.append(f"{path}: must be an object")
                continue
            _check_exact_keys(case, CASE_KEYS, path, errors)

            case_id = case.get("id")
            if not _valid_id(case_id):
                errors.append(f"{path}.id: must be a safe lowercase snake_case identifier")
            if type(case_id) is str:
                if case_id in seen_case_ids:
                    errors.append(f"{path}.id: duplicate case ID {case_id!r}")
                seen_case_ids.add(case_id)

            if type(case.get("inputs")) is not dict:
                errors.append(f"{path}.inputs: must be an object")
            if type(case.get("expected")) is not dict:
                errors.append(f"{path}.expected: must be an object")

            expected_status = case.get("expected_status")
            if type(expected_status) is not str or expected_status not in (
                "completed",
                "failed",
                "blocked",
            ):
                errors.append(f"{path}.expected_status: must be completed, failed, or blocked")

            case_required = case.get("required")
            if type(case_required) is not bool:
                errors.append(f"{path}.required: must be a boolean")

            case_criteria = case.get("criteria")
            if type(case_criteria) is not list or not case_criteria:
                errors.append(f"{path}.criteria: must be a nonempty list of criterion IDs")
                continue

            seen_refs = set()
            has_required_criterion = False
            for ref_index, criterion_ref in enumerate(case_criteria):
                ref_path = f"{path}.criteria[{ref_index}]"
                if type(criterion_ref) is not str:
                    errors.append(f"{ref_path}: must be a string criterion ID")
                    continue
                if criterion_ref in seen_refs:
                    errors.append(f"{ref_path}: duplicate criterion reference {criterion_ref!r}")
                seen_refs.add(criterion_ref)
                if criterion_ref not in criterion_ids:
                    errors.append(f"{ref_path}: unknown criterion ID {criterion_ref!r}")
                    continue
                referenced_ids.add(criterion_ref)
                if criterion_ref in criterion_required_ids:
                    has_required_criterion = True
                    if case_required is True:
                        required_case_covered_ids.add(criterion_ref)

            if case_required is True and not has_required_criterion:
                errors.append(f"{path}.criteria: a required case must include at least one required criterion")

    for criterion_id in sorted(criterion_ids):
        if criterion_id not in referenced_ids:
            errors.append(f"plan.criteria: criterion {criterion_id!r} is not referenced by any case")
        if criterion_id in criterion_required_ids and criterion_id not in required_case_covered_ids:
            errors.append(
                f"plan.criteria: required criterion {criterion_id!r} is not covered by a required case"
            )

    return {"valid": not errors, "errors": errors}


def require_valid(plan):
    """Return a valid plan or raise flowctl.FlowError with all validation errors."""
    result = validate(plan)
    if not result["valid"]:
        details = "\n".join(f"- {error}" for error in result["errors"])
        raise flowctl.FlowError(f"invalid evaluation plan:\n{details}")
    return plan


def make_lock(plan):
    """Create a detached full-plan lock using flowctl's canonical digest."""
    require_valid(plan)
    locked_plan = copy.deepcopy(plan)
    return {"plan": locked_plan, "plan_hash": flowctl.digest(locked_plan)}


def read_lock(lock):
    """Validate a two-key plan lock and return a detached complete plan."""
    if type(lock) is not dict:
        raise flowctl.FlowError("evaluation plan lock must be an object")
    if set(lock) != LOCK_KEYS:
        missing = sorted(LOCK_KEYS - set(lock))
        unexpected = [key for key in lock if key not in LOCK_KEYS]
        details = []
        if missing:
            details.append(f"missing key(s): {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected key(s): {', '.join(repr(key) for key in unexpected)}")
        raise flowctl.FlowError("invalid evaluation plan lock: " + "; ".join(details))

    plan = lock["plan"]
    require_valid(plan)
    plan_hash = lock["plan_hash"]
    if type(plan_hash) is not str:
        raise flowctl.FlowError("evaluation plan lock plan_hash must be a string")
    expected_hash = flowctl.digest(plan)
    if plan_hash != expected_hash:
        raise flowctl.FlowError("evaluation plan lock hash does not match the canonical plan digest")
    return copy.deepcopy(plan)


def _reject_constant(token):
    raise ValueError(f"non-finite JSON number {token!r} is not allowed")


def _parse_finite_float(token):
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"non-finite JSON number {token!r} is not allowed")
    return value


def _object_without_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def load(path):
    """Load a complete plan, rejecting duplicate keys and non-finite numbers."""
    try:
        with open(path, "r", encoding="utf-8") as stream:
            plan = json.load(
                stream,
                object_pairs_hook=_object_without_duplicate_keys,
                parse_constant=_reject_constant,
                parse_float=_parse_finite_float,
            )
    except flowctl.FlowError:
        raise
    except (OSError, UnicodeError, TypeError, ValueError, RecursionError) as exc:
        raise flowctl.FlowError(f"could not load evaluation plan from {path!r}: {exc}") from exc
    return require_valid(plan)
