"""Structural checks for workflow intake, evaluation plans, and architecture.

These checks verify required fields and cross-artifact references. They do not
judge design quality, prove a requirement is correctly interpreted, or establish
that an assumption is true.
"""

from __future__ import annotations

import evalplan
import flowctl
from flowctl import FlowError, IDENT


DECISION_DIMENSIONS = (
    "scope",
    "inputs",
    "outputs",
    "quality",
    "tools_and_authority",
    "failures",
    "state_and_handoffs",
    "budget_and_stop",
    "model_and_topology",
)
CONTRACT_ORIGINS = ("explicit", "derived", "default")
DECISION_ORIGINS = ("explicit", "derived", "default", "not_applicable")
DESIGN_DECISION_IDS = tuple(f"D{number:02}" for number in range(1, 15))


def _nonempty_text(value):
    return type(value) is str and bool(value.strip())


def _safe_id(value):
    return type(value) is str and IDENT.fullmatch(value) is not None


def _object(value, path, errors):
    if type(value) is not dict:
        errors.append(f"{path}: must be an object")
        return False
    if any(type(key) is not str for key in value):
        errors.append(f"{path}: object keys must be strings")
    return True


def _exact_keys(value, expected, path, errors):
    missing = [key for key in expected if key not in value]
    unexpected = [key for key in value if type(key) is str and key not in expected]
    if missing:
        errors.append(f"{path}: missing required field(s): {', '.join(missing)}")
    if unexpected:
        errors.append(f"{path}: unexpected field(s): {', '.join(unexpected)}")


def _validate_package_design(architecture, errors):
    """Check the retained package-design portion of lite/full architectures."""
    fields = ("mode", "necessity", "decisions", "lifecycle", "knowledge", "source_refs")
    missing = [field for field in fields if field not in architecture]
    if missing:
        errors.append(f"design: missing required field(s): {', '.join(missing)}")

    mode = architecture.get("mode")
    if type(mode) is not str or mode not in ("lite", "full"):
        errors.append("design.mode: lite or full required")

    necessity = architecture.get("necessity")
    if _object(necessity, "design.necessity", errors):
        _exact_keys(necessity, ("choice", "rationale", "baseline"), "design.necessity", errors)
        choice = necessity.get("choice")
        if type(choice) is not str or choice not in ("single_agent", "multi_agent"):
            errors.append("design.necessity.choice: must be single_agent or multi_agent")
        for key in ("rationale", "baseline"):
            if not _nonempty_text(necessity.get(key)):
                errors.append(f"design.necessity.{key}: must be nonempty text")

    decisions = architecture.get("decisions")
    decision_ids = set()
    if type(decisions) is not list or not decisions:
        errors.append("design.decisions: must be a nonempty array")
    else:
        for index, decision in enumerate(decisions):
            path = f"design.decisions[{index}]"
            if not _object(decision, path, errors):
                continue
            _exact_keys(decision, ("id", "status", "choice", "rationale", "rejected", "rollback"), path, errors)

            decision_id = decision.get("id")
            if type(decision_id) is not str:
                errors.append(f"{path}.id: must be a decision ID string")
            elif decision_id not in DESIGN_DECISION_IDS:
                errors.append(f"{path}.id: unknown decision ID {decision_id!r}")
            elif decision_id in decision_ids:
                errors.append(f"{path}.id: duplicate decision ID {decision_id!r}")
            else:
                decision_ids.add(decision_id)

            status = decision.get("status")
            if type(status) is not str or status not in ("chosen", "not_applicable"):
                errors.append(f"{path}.status: must be chosen or not_applicable")
            for key in ("choice", "rationale", "rollback"):
                if not _nonempty_text(decision.get(key)):
                    errors.append(f"{path}.{key}: must be nonempty text")
            if not flowctl.strings(decision.get("rejected")):
                errors.append(f"{path}.rejected: must be a string array")

    if type(decisions) is list and decisions and "D02" not in decision_ids:
        errors.append("design.decisions: topology decision D02 is required")
    if mode == "full" and decision_ids != set(DESIGN_DECISION_IDS):
        errors.append("design.decisions: full mode requires all decisions D01-D14")

    lifecycle = architecture.get("lifecycle")
    if _object(lifecycle, "design.lifecycle", errors):
        _exact_keys(lifecycle, ("infra", "post", "after"), "design.lifecycle", errors)
        for key in ("infra", "post", "after"):
            if not _nonempty_text(lifecycle.get(key)):
                errors.append(f"design.lifecycle.{key}: must be nonempty text")

    knowledge = architecture.get("knowledge")
    if type(knowledge) is not list:
        errors.append("design.knowledge: must be an array")
    else:
        for index, entry in enumerate(knowledge):
            path = f"design.knowledge[{index}]"
            if not _object(entry, path, errors):
                continue
            _exact_keys(entry, ("kind", "id", "claim", "status", "environment", "date", "scope", "evidence"), path, errors)
            kind = entry.get("kind")
            if type(kind) is not str or kind not in (
                "proven", "archetypes", "antipatterns", "incidents", "substrate-profiles"
            ):
                errors.append(f"{path}.kind: invalid knowledge kind")
            status = entry.get("status")
            if type(status) is not str or status not in (
                "candidate", "fixture_exercised", "live_exercised", "corroborated"
            ):
                errors.append(f"{path}.status: invalid knowledge evidence status")
            for key in ("id", "claim", "environment", "date", "scope"):
                if not _nonempty_text(entry.get(key)):
                    errors.append(f"{path}.{key}: must be nonempty text")
            if not flowctl.strings(entry.get("evidence")) or not entry.get("evidence"):
                errors.append(f"{path}.evidence: must be a nonempty string array")

    if not flowctl.strings(architecture.get("source_refs")):
        errors.append("design.source_refs: must be a string array")


def _raise_errors(label, errors):
    if errors:
        raise FlowError(f"invalid {label}:\n" + "\n".join(f"- {error}" for error in errors))


def require_contract(contract, request=None):
    """Validate a successful-intake contract without changing it."""
    errors = []
    if not _object(contract, "contract", errors):
        _raise_errors("workflow contract", errors)
    if request is not None and type(request) is not str:
        errors.append("request: must be the original request text when provided")

    if not _nonempty_text(contract.get("goal")):
        errors.append("goal: must be nonempty text")

    raw_requirements = contract.get("requirements")
    requirement_ids = set()
    if type(raw_requirements) is not list or not raw_requirements:
        errors.append("requirements: must be a nonempty array")
    else:
        for index, requirement in enumerate(raw_requirements):
            path = f"requirements[{index}]"
            if not _object(requirement, path, errors):
                continue
            missing = [key for key in ("id", "text", "origin", "basis", "criteria") if key not in requirement]
            if missing:
                errors.append(f"{path}: missing required field(s): {', '.join(missing)}")

            requirement_id = requirement.get("id")
            if not _safe_id(requirement_id):
                errors.append(f"{path}.id: must be a safe lowercase identifier")
            elif requirement_id in requirement_ids:
                errors.append(f"{path}.id: duplicate requirement ID {requirement_id!r}")
            else:
                requirement_ids.add(requirement_id)

            if not _nonempty_text(requirement.get("text")):
                errors.append(f"{path}.text: must be nonempty text")
            if not _nonempty_text(requirement.get("basis")):
                errors.append(f"{path}.basis: must be nonempty text")

            origin = requirement.get("origin")
            if type(origin) is not str or origin not in CONTRACT_ORIGINS:
                errors.append(f"{path}.origin: must be one of explicit, derived, or default")
            elif origin == "explicit" and request is not None and type(request) is str:
                basis = requirement.get("basis")
                if _nonempty_text(basis) and basis not in request:
                    errors.append(f"{path}.basis: explicit evidence must be an exact substring of request")

            criteria = requirement.get("criteria")
            if type(criteria) is not list or not criteria:
                errors.append(f"{path}.criteria: must be a nonempty array of safe criterion IDs")
            else:
                seen_criteria = set()
                for criterion_index, criterion_id in enumerate(criteria):
                    criterion_path = f"{path}.criteria[{criterion_index}]"
                    if not _safe_id(criterion_id):
                        errors.append(f"{criterion_path}: must be a safe lowercase identifier")
                    elif criterion_id in seen_criteria:
                        errors.append(f"{criterion_path}: duplicate criterion ID {criterion_id!r}")
                    else:
                        seen_criteria.add(criterion_id)

    decisions = contract.get("decisions")
    if _object(decisions, "decisions", errors):
        keys = [key for key in decisions if type(key) is str]
        missing_dimensions = [dimension for dimension in DECISION_DIMENSIONS if dimension not in keys]
        unexpected_dimensions = [key for key in keys if key not in DECISION_DIMENSIONS]
        if missing_dimensions:
            errors.append(f"decisions: missing required dimension(s): {', '.join(missing_dimensions)}")
        if unexpected_dimensions:
            errors.append(f"decisions: unexpected dimension(s): {', '.join(unexpected_dimensions)}")
        for dimension in DECISION_DIMENSIONS:
            if dimension not in decisions:
                continue
            path = f"decisions.{dimension}"
            decision = decisions[dimension]
            if not _object(decision, path, errors):
                continue
            missing = [key for key in ("choice", "reason", "origin") if key not in decision]
            if missing:
                errors.append(f"{path}: missing required field(s): {', '.join(missing)}")
            if not _nonempty_text(decision.get("choice")):
                errors.append(f"{path}.choice: must be nonempty text")
            if not _nonempty_text(decision.get("reason")):
                errors.append(f"{path}.reason: must be nonempty text")
            origin = decision.get("origin")
            if type(origin) is not str or origin not in DECISION_ORIGINS:
                errors.append(
                    f"{path}.origin: must be one of explicit, derived, default, or not_applicable"
                )
            elif origin == "explicit":
                basis = decision.get("basis")
                if not _nonempty_text(basis):
                    errors.append(f"{path}.basis: explicit decisions require nonempty evidence")
                elif type(request) is str and basis not in request:
                    errors.append(f"{path}.basis: explicit evidence must be an exact substring of request")

    blocking_questions = contract.get("blocking_questions")
    if type(blocking_questions) is not list:
        errors.append("blocking_questions: must be an array")
    elif blocking_questions:
        errors.append(
            "blocking_questions: must be empty for successful intake; unresolved blockers belong on the factory blocked branch"
        )

    _raise_errors("workflow contract", errors)
    return contract


def require_plan(contract, plan):
    """Validate the frozen evaluation plan and its required coverage of needs."""
    require_contract(contract)
    try:
        evalplan.require_valid(plan)
    except FlowError:
        raise
    except Exception as exc:
        raise FlowError(f"invalid evaluation plan: {type(exc).__name__}: {exc}") from exc

    criterion_by_id = {item["id"]: item for item in plan["criteria"]}
    errors = []
    for index, requirement in enumerate(contract["requirements"]):
        for criterion_id in requirement["criteria"]:
            criterion = criterion_by_id.get(criterion_id)
            if criterion is None:
                errors.append(
                    f"requirements[{index}].criteria: criterion {criterion_id!r} is missing from plan.criteria"
                )
            elif criterion["required"] is not True:
                errors.append(
                    f"requirements[{index}].criteria: plan criterion {criterion_id!r} must have required=true"
                )

    required_case_count = sum(case["required"] is True for case in plan["cases"])
    if required_case_count < 2:
        errors.append(
            f"plan.cases: need at least two required cases for success and exception probes; found {required_case_count}"
        )
    _raise_errors("workflow evaluation plan", errors)
    return plan


def require_architecture(contract, plan, architecture, flow=None):
    """Validate architecture coverage and references to the frozen plan/flow."""
    require_plan(contract, plan)
    errors = []
    if not _object(architecture, "architecture", errors):
        _raise_errors("workflow architecture", errors)
    _validate_package_design(architecture, errors)

    node_ids = None
    if flow is not None:
        try:
            flowctl.require_valid(flow)
        except FlowError:
            raise
        except Exception as exc:
            raise FlowError(f"invalid flow supplied for node-reference checks: {type(exc).__name__}: {exc}") from exc
        node_ids = {node["id"] for node in flow["nodes"]}

    requirements = {item["id"]: set(item["criteria"]) for item in contract["requirements"]}
    coverage = architecture.get("coverage")
    if type(coverage) is not list:
        errors.append("coverage: must be an array with one entry per requirement")
    else:
        seen_requirements = set()
        for index, entry in enumerate(coverage):
            path = f"coverage[{index}]"
            if not _object(entry, path, errors):
                continue
            missing = [key for key in ("requirement_id", "node_ids", "criteria") if key not in entry]
            if missing:
                errors.append(f"{path}: missing required field(s): {', '.join(missing)}")

            requirement_id = entry.get("requirement_id")
            if not _safe_id(requirement_id):
                errors.append(f"{path}.requirement_id: must be a safe lowercase identifier")
            elif requirement_id not in requirements:
                errors.append(f"{path}.requirement_id: unknown requirement ID {requirement_id!r}")
            elif requirement_id in seen_requirements:
                errors.append(f"{path}.requirement_id: duplicate coverage for {requirement_id!r}")
            else:
                seen_requirements.add(requirement_id)

            raw_node_ids = entry.get("node_ids")
            if type(raw_node_ids) is not list or not raw_node_ids:
                errors.append(f"{path}.node_ids: must be a nonempty array of safe node IDs")
            else:
                seen_nodes = set()
                for node_index, node_id in enumerate(raw_node_ids):
                    node_path = f"{path}.node_ids[{node_index}]"
                    if not _safe_id(node_id):
                        errors.append(f"{node_path}: must be a safe lowercase identifier")
                    elif node_id in seen_nodes:
                        errors.append(f"{node_path}: duplicate node ID {node_id!r}")
                    else:
                        seen_nodes.add(node_id)
                    if node_ids is not None and _safe_id(node_id) and node_id not in node_ids:
                        errors.append(f"{node_path}: node ID {node_id!r} does not exist in flow")

            raw_criteria = entry.get("criteria")
            if type(raw_criteria) is not list:
                errors.append(f"{path}.criteria: must be an array matching the requirement's frozen criteria")
            else:
                seen_criteria = set()
                valid_criteria = True
                for criterion_index, criterion_id in enumerate(raw_criteria):
                    criterion_path = f"{path}.criteria[{criterion_index}]"
                    if not _safe_id(criterion_id):
                        valid_criteria = False
                        errors.append(f"{criterion_path}: must be a safe lowercase identifier")
                    elif criterion_id in seen_criteria:
                        valid_criteria = False
                        errors.append(f"{criterion_path}: duplicate criterion ID {criterion_id!r}")
                    else:
                        seen_criteria.add(criterion_id)
                if _safe_id(requirement_id) and requirement_id in requirements and valid_criteria:
                    expected = requirements[requirement_id]
                    if seen_criteria != expected or len(raw_criteria) != len(expected):
                        errors.append(
                            f"{path}.criteria: must match the frozen criteria for requirement {requirement_id!r}"
                        )

        missing_coverage = sorted(set(requirements) - seen_requirements)
        if missing_coverage:
            errors.append(f"coverage: missing requirement(s): {', '.join(missing_coverage)}")

    required_case_ids = {
        case["id"] for case in plan["cases"] if case["required"] is True
    }
    stress_cases = architecture.get("stress_cases")
    if type(stress_cases) is not list or len(stress_cases) < 2:
        errors.append("stress_cases: must contain at least two cases")
    else:
        seen_case_ids = set()
        for index, stress_case in enumerate(stress_cases):
            path = f"stress_cases[{index}]"
            if not _object(stress_case, path, errors):
                continue
            missing = [key for key in ("case_id", "risk", "handling") if key not in stress_case]
            if missing:
                errors.append(f"{path}: missing required field(s): {', '.join(missing)}")
            case_id = stress_case.get("case_id")
            if not _safe_id(case_id):
                errors.append(f"{path}.case_id: must be a safe lowercase identifier")
            elif case_id in seen_case_ids:
                errors.append(f"{path}.case_id: duplicate stress case ID {case_id!r}")
            else:
                seen_case_ids.add(case_id)
            if _safe_id(case_id) and case_id not in required_case_ids:
                errors.append(
                    f"{path}.case_id: {case_id!r} must reference a required case in the frozen plan"
                )
            if not _nonempty_text(stress_case.get("risk")):
                errors.append(f"{path}.risk: must be nonempty text")
            if not _nonempty_text(stress_case.get("handling")):
                errors.append(f"{path}.handling: must be nonempty text")

    review = architecture.get("review")
    if _object(review, "review", errors):
        missing = [key for key in ("mode", "summary", "unresolved") if key not in review]
        if missing:
            errors.append(f"review: missing required field(s): {', '.join(missing)}")
        mode = review.get("mode")
        if type(mode) is not str or mode not in ("self_review", "fresh_context"):
            errors.append("review.mode: must be self_review or fresh_context")
        if not _nonempty_text(review.get("summary")):
            errors.append("review.summary: must be nonempty text")
        unresolved = review.get("unresolved")
        if type(unresolved) is not list:
            errors.append("review.unresolved: must be an array")
        elif unresolved:
            errors.append("review.unresolved: must be empty for a successful design")

    _raise_errors("workflow architecture", errors)
    return architecture
