#!/usr/bin/env python3
"""Check delivery evidence structure and candidate/plan binding.

This is a metadata gate only. Evidence references are not opened or authenticated;
"pass" does not certify that a run occurred or that behavior is correct.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import flowctl

PLAN_SCHEMA = "smokecheck-plan/1"
RESULTS_SCHEMA = "smokecheck-results/1"
CLAIM_SCOPE = "structure_binding_only_no_execution_authentication"
CLAIM_LIMIT = (
    "Checks structure, declared status, and plan/candidate binding only. Evidence "
    "references are not opened or authenticated; this does not certify real execution "
    "or behavior."
)
PLAN_KEYS = {"schema", "project_kind", "baseline", "candidate_id", "journeys"}
BASELINE_KEYS = {"id", "protected_behaviors"}
JOURNEY_KEYS = {
    "id", "goal", "initial_state", "steps", "expected", "kind", "required",
    "min_level", "min_backend",
}
RESULT_KEYS = {
    "schema", "plan_hash", "candidate_id", "baseline_id", "claim_scope", "runs", "regressions"
}
RUN_KEYS = {
    "journey_id", "round", "candidate_id", "level", "backend", "status",
    "observations", "evidence",
}
REGRESSION_KEYS = {"behavior_id", "candidate_id", "status", "evidence"}
KINDS = {"main", "recovery", "repeat"}
LEVELS = {"static", "simulated", "runtime"}
BACKENDS = {"none", "mocked", "live"}
STATUSES = {"pass", "fail", "blocked"}
_LEVEL_RANK = {"static": 0, "simulated": 1, "runtime": 2}
_BACKEND_RANK = {"none": 0, "mocked": 1, "live": 2}
_SAFE_ID = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class _RejectConstant(ValueError):
    pass


def _scan_json(value, path, errors, active):
    """Reject non-JSON Python values before canonical hashing or traversal."""
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
                _scan_json(item, f"{path}[{index}]", errors, active)
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
                    errors.append(f"{path}: object keys must be strings")
                    continue
                try:
                    key.encode("utf-8")
                except UnicodeEncodeError:
                    errors.append(f"{path}: object keys must contain valid Unicode scalar values")
                _scan_json(item, f"{path}[{key!r}]", errors, active)
        finally:
            active.remove(marker)
        return
    errors.append(f"{path}: {type(value).__name__} is not a JSON value")


def _exact_keys(value, expected, path, errors):
    missing = sorted(key for key in expected if key not in value)
    unexpected = [key for key in value if type(key) is not str or key not in expected]
    if missing:
        errors.append(f"{path}: missing key(s): {', '.join(missing)}")
    if unexpected:
        errors.append(f"{path}: unexpected key(s): {', '.join(repr(k) for k in unexpected)}")


def _text(value, path, errors):
    if type(value) is not str or not value.strip():
        errors.append(f"{path}: must be nonempty text")
        return False
    return True


def _identifier(value, path, errors):
    if type(value) is not str or _SAFE_ID.fullmatch(value) is None:
        errors.append(f"{path}: must be a lowercase identifier (a-z, 0-9, underscore)")
        return False
    return True


def _text_list(value, path, errors, *, nonempty=True):
    if type(value) is not list:
        errors.append(f"{path}: must be an array of nonempty strings")
        return False
    if nonempty and not value:
        errors.append(f"{path}: must not be empty")
    valid = True
    for index, item in enumerate(value):
        if type(item) is not str or not item.strip():
            errors.append(f"{path}[{index}]: must be nonempty text")
            valid = False
    return valid and (not nonempty or bool(value))


def _unique(values, path, errors):
    if len(values) != len(set(values)):
        errors.append(f"{path}: values must be unique")


def _raise_errors(errors):
    if errors:
        raise flowctl.FlowError("Invalid smokecheck data: " + "; ".join(errors))


def require_plan(plan):
    """Validate a plan or raise flowctl.FlowError; return the original plan."""
    errors = []
    if type(plan) is not dict:
        raise flowctl.FlowError("Invalid smokecheck plan: plan must be an object")
    try:
        _scan_json(plan, "plan", errors, set())
    except RecursionError:
        errors.append("plan: nesting is too deep to validate")
    _exact_keys(plan, PLAN_KEYS, "plan", errors)
    if plan.get("schema") != PLAN_SCHEMA:
        errors.append(f"plan.schema: must equal {PLAN_SCHEMA!r}")
    if plan.get("project_kind") not in ("new", "change"):
        errors.append("plan.project_kind: must be 'new' or 'change'")
    _text(plan.get("candidate_id"), "plan.candidate_id", errors)

    baseline = plan.get("baseline")
    if type(baseline) is not dict:
        errors.append("plan.baseline: must be an object")
    else:
        _exact_keys(baseline, BASELINE_KEYS, "plan.baseline", errors)
        _text(baseline.get("id"), "plan.baseline.id", errors)
        protected = baseline.get("protected_behaviors")
        if type(protected) is not list:
            errors.append("plan.baseline.protected_behaviors: must be an array of {id, description} objects")
        else:
            behavior_ids = []
            for index, behavior in enumerate(protected):
                path = f"plan.baseline.protected_behaviors[{index}]"
                if type(behavior) is not dict:
                    errors.append(f"{path}: must be an object")
                    continue
                _exact_keys(behavior, {"id", "description"}, path, errors)
                if _identifier(behavior.get("id"), f"{path}.id", errors):
                    behavior_ids.append(behavior["id"])
                _text(behavior.get("description"), f"{path}.description", errors)
            _unique(behavior_ids, "plan.baseline.protected_behaviors ids", errors)
            if plan.get("project_kind") == "change" and not protected:
                errors.append("plan.baseline.protected_behaviors: change projects need at least one behavior")

    journeys = plan.get("journeys")
    if type(journeys) is not list or not journeys:
        errors.append("plan.journeys: must be a nonempty array")
        journeys = []
    journey_ids = []
    found_kinds = set()
    found_required_kinds = set()
    for index, journey in enumerate(journeys):
        path = f"plan.journeys[{index}]"
        if type(journey) is not dict:
            errors.append(f"{path}: must be an object")
            continue
        _exact_keys(journey, JOURNEY_KEYS, path, errors)
        if _identifier(journey.get("id"), f"{path}.id", errors):
            journey_ids.append(journey["id"])
        for key in ("goal", "initial_state"):
            _text(journey.get(key), f"{path}.{key}", errors)
        _text_list(journey.get("steps"), f"{path}.steps", errors)
        _text_list(journey.get("expected"), f"{path}.expected", errors)
        kind = journey.get("kind")
        if type(kind) is not str or kind not in KINDS:
            errors.append(f"{path}.kind: must be one of {sorted(KINDS)}")
        else:
            found_kinds.add(kind)
        required = journey.get("required")
        if type(required) is not bool:
            errors.append(f"{path}.required: must be boolean")
        elif required and type(kind) is str and kind in KINDS:
            found_required_kinds.add(kind)
        if journey.get("min_level") not in ("runtime", "static"):
            errors.append(f"{path}.min_level: must be 'runtime' or 'static'")
        elif kind in ("main", "repeat") and journey["min_level"] != "runtime":
            errors.append(f"{path}.min_level: main and repeat journeys require runtime")
        min_backend = journey.get("min_backend")
        if type(min_backend) is not str or min_backend not in BACKENDS:
            errors.append(f"{path}.min_backend: must be one of {sorted(BACKENDS)}")
    _unique(journey_ids, "plan.journeys ids", errors)
    for kind in sorted(KINDS - found_kinds):
        errors.append(f"plan.journeys: at least one {kind!r} journey is required")
    for kind in sorted(KINDS - found_required_kinds):
        errors.append(f"plan.journeys: at least one required {kind!r} journey is required")

    _raise_errors(errors)
    return plan


def _validate_results(plan, results):
    errors = []
    if type(results) is not dict:
        raise flowctl.FlowError("Invalid smokecheck results: results must be an object")
    try:
        _scan_json(results, "results", errors, set())
    except RecursionError:
        errors.append("results: nesting is too deep to validate")
    _exact_keys(results, RESULT_KEYS, "results", errors)
    if results.get("schema") != RESULTS_SCHEMA:
        errors.append(f"results.schema: must equal {RESULTS_SCHEMA!r}")
    _text(results.get("plan_hash"), "results.plan_hash", errors)
    _text(results.get("candidate_id"), "results.candidate_id", errors)
    _text(results.get("baseline_id"), "results.baseline_id", errors)
    if results.get("claim_scope") != CLAIM_SCOPE:
        errors.append(f"results.claim_scope: must equal {CLAIM_SCOPE!r}")

    runs = results.get("runs")
    if type(runs) is not list:
        errors.append("results.runs: must be an array (use [] when no runs are available)")
        runs = []
    journey_by_id = {journey["id"]: journey for journey in plan["journeys"]}
    seen_run_keys = set()
    for index, run in enumerate(runs):
        path = f"results.runs[{index}]"
        if type(run) is not dict:
            errors.append(f"{path}: must be an object")
            continue
        _exact_keys(run, RUN_KEYS, path, errors)
        journey_id = run.get("journey_id")
        _identifier(journey_id, f"{path}.journey_id", errors)
        if type(journey_id) is str and journey_id not in journey_by_id:
            errors.append(f"{path}.journey_id: not declared by the plan")
        round_number = run.get("round")
        if type(round_number) is not int or round_number < 1:
            errors.append(f"{path}.round: must be a positive integer")
        elif type(journey_id) is str:
            key = (round_number, journey_id)
            if key in seen_run_keys:
                errors.append(f"{path}: duplicate journey in round {round_number}")
            seen_run_keys.add(key)
        _text(run.get("candidate_id"), f"{path}.candidate_id", errors)
        level = run.get("level")
        if type(level) is not str or level not in LEVELS:
            errors.append(f"{path}.level: must be one of {sorted(LEVELS)}")
        backend = run.get("backend")
        if type(backend) is not str or backend not in BACKENDS:
            errors.append(f"{path}.backend: must be one of {sorted(BACKENDS)}")
        status = run.get("status")
        if type(status) is not str or status not in STATUSES:
            errors.append(f"{path}.status: must be one of {sorted(STATUSES)}")
        _text_list(run.get("observations"), f"{path}.observations", errors)
        _text_list(run.get("evidence"), f"{path}.evidence", errors)

    regressions = results.get("regressions")
    if type(regressions) is not list:
        errors.append("results.regressions: must be an array")
        regressions = []
    behavior_ids = []
    protected = {behavior["id"] for behavior in plan["baseline"]["protected_behaviors"]}
    for index, regression in enumerate(regressions):
        path = f"results.regressions[{index}]"
        if type(regression) is not dict:
            errors.append(f"{path}: must be an object")
            continue
        _exact_keys(regression, REGRESSION_KEYS, path, errors)
        behavior_id = regression.get("behavior_id")
        if _identifier(behavior_id, f"{path}.behavior_id", errors):
            behavior_ids.append(behavior_id)
            if behavior_id not in protected:
                errors.append(f"{path}.behavior_id: not declared as protected by the plan")
        _text(regression.get("candidate_id"), f"{path}.candidate_id", errors)
        status = regression.get("status")
        if type(status) is not str or status not in STATUSES:
            errors.append(f"{path}.status: must be one of {sorted(STATUSES)}")
        _text_list(regression.get("evidence"), f"{path}.evidence", errors)
    _unique(behavior_ids, "results.regressions behavior_id", errors)
    _raise_errors(errors)
    return runs, regressions


def _meets_minimum(run, journey):
    return (
        _LEVEL_RANK[run["level"]] >= _LEVEL_RANK[journey["min_level"]]
        and _BACKEND_RANK[run["backend"]] >= _BACKEND_RANK[journey["min_backend"]]
    )


def _report(status, plan_hash, candidate_id, final_round, runtime_rounds, reasons,
            *, uncovered=None, regression_missing=None, regression_failed=None):
    return {
        "status": status,
        "claim_scope": CLAIM_SCOPE,
        "claim_limit": CLAIM_LIMIT,
        "plan_hash": plan_hash,
        "candidate_id": candidate_id,
        "final_round": final_round,
        "runtime_rounds": sorted(runtime_rounds),
        "uncovered_required_journeys": uncovered or [],
        "unverified_protected_behaviors": regression_missing or [],
        "failed_protected_behaviors": regression_failed or [],
        "reasons": reasons,
    }


def assess(plan, results):
    """Return pass/fail/unverified/invalid after validating schema and bindings."""
    require_plan(plan)
    expected_hash = flowctl.digest(plan)
    runs, regressions = _validate_results(plan, results)

    identity_errors = []
    if results["plan_hash"] != expected_hash:
        identity_errors.append("results.plan_hash does not match the supplied plan")
    if results["candidate_id"] != plan["candidate_id"]:
        identity_errors.append("results.candidate_id does not match the plan candidate")
    if results["baseline_id"] != plan["baseline"]["id"]:
        identity_errors.append("results.baseline_id does not match the plan baseline")
    for index, run in enumerate(runs):
        if type(run) is dict and run.get("candidate_id") != plan["candidate_id"]:
            identity_errors.append(f"results.runs[{index}].candidate_id is not the plan candidate")
    for index, regression in enumerate(regressions):
        if type(regression) is dict and regression.get("candidate_id") != plan["candidate_id"]:
            identity_errors.append(f"results.regressions[{index}].candidate_id is not the plan candidate")
    if identity_errors:
        return _report("invalid", expected_hash, plan["candidate_id"], None, set(), identity_errors)

    journey_by_id = {journey["id"]: journey for journey in plan["journeys"]}
    runs_by_round = {}
    runtime_rounds = set()
    for run in runs:
        runs_by_round.setdefault(run["round"], {})[run["journey_id"]] = run
        journey = journey_by_id[run["journey_id"]]
        if run["level"] == "runtime" and _meets_minimum(run, journey):
            runtime_rounds.add(run["round"])

    reasons = []
    failures = []
    uncovered = []
    regression_missing = []
    regression_failed = []
    if not runs:
        reasons.append("No run records were supplied")
    final_round = max(runs_by_round) if runs_by_round else None
    if len(runtime_rounds) < 2:
        reasons.append("At least two distinct rounds with qualifying runtime evidence are required")
    if final_round is not None and final_round not in runtime_rounds:
        reasons.append("The final round has no qualifying runtime evidence")

    final_runs = runs_by_round.get(final_round, {}) if final_round is not None else {}
    if final_round is not None:
        for journey_id, run in final_runs.items():
            if run["status"] != "pass":
                failures.append(f"Final round {final_round} has {run['status']} for journey {journey_id}")

    for journey in plan["journeys"]:
        if not journey["required"]:
            continue
        run = final_runs.get(journey["id"])
        if run is None:
            uncovered.append(journey["id"])
            reasons.append(f"Final round {final_round!r} does not cover required journey {journey['id']}")
        elif run["status"] == "pass" and not _meets_minimum(run, journey):
            uncovered.append(journey["id"])
            reasons.append(
                f"Final round evidence for {journey['id']} is below its minimum level/backend"
            )

    regression_by_id = {regression["behavior_id"]: regression for regression in regressions}
    if plan["project_kind"] == "change":
        for behavior in plan["baseline"]["protected_behaviors"]:
            behavior_id = behavior["id"]
            regression = regression_by_id.get(behavior_id)
            if regression is None:
                regression_missing.append(behavior_id)
                reasons.append(f"No regression result for protected behavior {behavior_id}")
            elif regression["status"] != "pass":
                regression_failed.append(behavior_id)
                failures.append(
                    f"Protected behavior {behavior_id} has regression status {regression['status']}"
                )

    status = "fail" if failures else ("unverified" if reasons else "pass")
    return _report(
        status, expected_hash, plan["candidate_id"], final_round, runtime_rounds,
        failures + reasons, uncovered=uncovered, regression_missing=regression_missing,
        regression_failed=regression_failed,
    )


def _reject_constant(value):
    raise _RejectConstant(f"non-finite JSON number {value}")


def _load_json(path):
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return json.load(stream, parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, _RejectConstant) as exc:
        raise flowctl.FlowError(f"Cannot read JSON from {path}: {exc}") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description="Assess smokecheck delivery evidence structure and binding")
    subparsers = parser.add_subparsers(dest="command", required=True)
    assess_parser = subparsers.add_parser("assess", help="assess one plan/results pair")
    assess_parser.add_argument("plan")
    assess_parser.add_argument("results")
    assess_parser.add_argument(
        "--evidence-manifest",
        help="also inspect every referenced evidence file using a bound manifest",
    )
    args = parser.parse_args(argv)

    try:
        plan = _load_json(args.plan)
        results = _load_json(args.results)
        if args.evidence_manifest:
            import smoke_evidence
            report = smoke_evidence.assess(plan, results, args.evidence_manifest)
        else:
            report = assess(plan, results)
            report["content_inspection"] = {
                "status": "not_checked",
                "reason": "No --evidence-manifest was supplied.",
            }
    except flowctl.FlowError as exc:
        if args.evidence_manifest:
            import smoke_evidence
            report = {
                "status": "invalid",
                "claim_scope": smoke_evidence.CLAIM_SCOPE,
                "claim_limit": smoke_evidence.CLAIM_LIMIT,
                "content_checked": False,
                "content_status": "invalid",
                "reasons": [str(exc)],
            }
        else:
            report = {
                "status": "invalid",
                "claim_scope": CLAIM_SCOPE,
                "claim_limit": CLAIM_LIMIT,
                "content_inspection": {
                    "status": "not_checked",
                    "reason": "No --evidence-manifest was supplied.",
                },
                "reasons": [str(exc)],
            }
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    if report["status"] == "pass":
        return 0
    if report["status"] == "invalid":
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
