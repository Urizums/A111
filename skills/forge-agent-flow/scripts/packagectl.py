#!/usr/bin/env python3
"""Validate, compile and dispatch a Forge package; host declarations are not a sandbox."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

import flowctl as flow
import evalplan

SCHEMA_V1 = "forge-package/1"
SCHEMA_V2 = "forge-package/2"
SCHEMAS = {SCHEMA_V1, SCHEMA_V2}
# Backward-compatible schema constant for callers that imported the v1 API.
SCHEMA = SCHEMA_V1
DECISIONS = {f"D{i:02}" for i in range(1, 15)}
KINDS = {"model", "write_scope", "guard", "token_budget", "cost_budget", "time_budget", "approval", "other"}


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise flow.FlowError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def finite(value):
        raise flow.FlowError(f"Non-finite JSON number: {value}")

    value = json.loads(Path(path).read_text(encoding="utf-8"),
                       object_pairs_hook=unique, parse_constant=finite)
    flow.canonical(value)  # Also reject exponent overflow such as 1e999.
    return value


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _is_v2(package):
    return isinstance(package, dict) and package.get("schema") == SCHEMA_V2


def _read_plan(lock):
    """Return the validated frozen plan carried by a v2 acceptance lock."""
    return evalplan.read_lock(lock)


def _checkpoint_inputs(package, flow_state):
    """Return the exact immutable input map stored in a Flow checkpoint."""
    if not isinstance(flow_state, dict) or not isinstance(flow_state.get("artifacts"), dict):
        raise flow.FlowError("Checkpoint needs an artifact object containing the immutable inputs")
    names = set(package["flow"]["inputs"])
    artifacts = flow_state["artifacts"]
    if not names <= set(artifacts):
        raise flow.FlowError("Checkpoint is missing one or more immutable Flow inputs")
    inputs = {name: artifacts[name] for name in package["flow"]["inputs"]}
    flow.values_match(package["flow"], inputs, package["flow"]["inputs"])
    return inputs


def validate(package):
    errors, blockers = [], []

    def check(ok, message):
        if not ok:
            errors.append(message)

    def shape(value, keys, label):
        ok = isinstance(value, dict) and set(value) == set(keys.split())
        check(ok, f"{label}: expected keys {keys}")
        return ok

    if not shape(package, "schema design flow execution acceptance", "package"):
        return {"valid": False, "errors": errors, "blockers": [], "declared_ready": False}
    try:
        flow.canonical(package)
    except (ValueError, TypeError, OverflowError):
        return {"valid": False, "errors": ["Package must be finite JSON data"], "blockers": [], "declared_ready": False}
    check(isinstance(package["schema"], str) and package["schema"] in SCHEMAS, "Unsupported package schema")
    try:
        flow_result = flow.validate(package["flow"])
        errors.extend(f"flow: {e}" for e in flow_result["errors"])
    except (TypeError, ValueError, KeyError):
        errors.append("flow: malformed structure")
        flow_result = {"valid": False, "warnings": []}
    design, execution = package["design"], package["execution"]
    if shape(design, "mode necessity decisions lifecycle knowledge source_refs", "design"):
        check(design["mode"] in ("lite", "full"), "design.mode: lite or full required")
        if shape(design["necessity"], "choice rationale baseline", "necessity"):
            check(design["necessity"]["choice"] in ("single_agent", "multi_agent"), "Invalid necessity choice")
            for key in ("rationale", "baseline"):
                check(nonempty(design["necessity"][key]), f"necessity.{key}: nonempty text required")
        decisions = design["decisions"]
        check(isinstance(decisions, list) and bool(decisions), "decisions must be nonempty")
        ids = set()
        for decision in decisions if isinstance(decisions, list) else []:
            if not shape(decision, "id status choice rationale rejected rollback", "decision"):
                continue
            did = decision["id"]
            if not isinstance(did, str):
                errors.append("decision id must be a string")
                continue
            check(did in DECISIONS and did not in ids, f"Unknown/duplicate decision: {did}")
            ids.add(did)
            check(decision["status"] in ("chosen", "not_applicable"), f"{did}: invalid status")
            for key in ("choice", "rationale", "rollback"):
                check(nonempty(decision[key]), f"{did}.{key}: nonempty text required")
            check(flow.strings(decision["rejected"]), f"{did}.rejected must be a string list")
        check("D02" in ids, "Topology decision D02 is required")
        if design["mode"] == "full":
            check(ids == DECISIONS, "Full design needs D01-D14; mark inapplicable decisions with reasons")
        if shape(design["lifecycle"], "infra post after", "lifecycle"):
            for key, value in design["lifecycle"].items():
                check(nonempty(value), f"lifecycle.{key}: nonempty text required")
        check(flow.strings(design["source_refs"]), "source_refs must be a string list")
        check(isinstance(design["knowledge"], list), "knowledge must be a list")
        for entry in design["knowledge"] if isinstance(design["knowledge"], list) else []:
            if not shape(entry, "kind id claim status environment date scope evidence", "knowledge entry"):
                continue
            check(entry["kind"] in ("proven", "archetypes", "antipatterns", "incidents", "substrate-profiles"), "Invalid knowledge kind")
            check(entry["status"] in ("candidate", "fixture_exercised", "live_exercised", "corroborated"), "Invalid knowledge evidence status")
            for key in ("id", "claim", "environment", "date", "scope"):
                check(nonempty(entry[key]), f"knowledge.{key}: nonempty text required")
            check(flow.strings(entry["evidence"]) and bool(entry["evidence"]), "Knowledge evidence references required")
    if shape(execution, "adapter parallelism node_settings requirements unresolved", "execution"):
        check(nonempty(execution["adapter"]), "adapter must be nonempty")
        check(type(execution["parallelism"]) is int and execution["parallelism"] > 0, "parallelism must be a positive integer")
        if execution["adapter"] != "host_serial":
            blockers.append(f"Unsupported adapter: {execution['adapter']}")
        if execution["parallelism"] != 1:
            blockers.append("Only serial execution is implemented; explicitly redesign before changing parallelism")
        check(flow.strings(execution["unresolved"]), "unresolved must be a string list")
        if flow.strings(execution["unresolved"]):
            blockers.extend(execution["unresolved"])
        settings, requirements = execution["node_settings"], execution["requirements"]
        check(isinstance(settings, dict), "node_settings must be an object")
        check(isinstance(requirements, list), "requirements must be a list")
        rids, valid_requirements = set(), []
        nodes = {n["id"]: n for n in package["flow"]["nodes"]} if flow_result["valid"] else {}
        check("flow" not in nodes, "Node id 'flow' is reserved for package-wide requirement scope")
        for r in requirements if isinstance(requirements, list) else []:
            if not shape(r, "id scope kind value status binding evidence", "requirement"):
                continue
            rid = r["id"]
            if not nonempty(rid):
                errors.append("Requirement needs a nonempty id")
                continue
            check(rid not in rids, f"Duplicate requirement: {rid}")
            rids.add(rid)
            check(isinstance(r["scope"], str) and (r["scope"] == "flow" or r["scope"] in nodes), f"{rid}: invalid scope")
            check(isinstance(r["kind"], str) and r["kind"] in KINDS, f"{rid}: invalid kind")
            check(r["value"] not in (None, "", [], {}), f"{rid}: requested value required")
            check(r["status"] in ("verified", "unverified", "unsupported"), f"{rid}: invalid status")
            check(isinstance(r["binding"], str), f"{rid}: binding must be text")
            check(flow.strings(r["evidence"]), f"{rid}: evidence must be a string list")
            if r["status"] == "verified":
                check(nonempty(r["binding"]) and bool(r["evidence"]), f"{rid}: verified requires binding and evidence")
            else:
                blockers.append(f"Requirement {rid}: {r['status']}")
            valid_requirements.append(r)
        if isinstance(settings, dict) and flow_result["valid"]:
            check(set(settings) == set(nodes), "node_settings must exactly cover flow nodes")
            for r in valid_requirements:
                if r["kind"] in ("model", "write_scope"):
                    setting = settings.get(r["scope"]) if isinstance(r["scope"], str) else None
                    check(isinstance(setting, dict) and r["value"] == setting.get(r["kind"]),
                          f"{r['id']}: {r['kind']} requirement must exactly match its node setting")
            for nid, setting in settings.items():
                if not shape(setting, "model write_scope", f"settings.{nid}"):
                    continue
                check(nonempty(setting["model"]), f"{nid}: model must be host_default or an explicit identifier")
                check(flow.strings(setting["write_scope"]), f"{nid}: write_scope must be a string list")
                for key in ("model", "write_scope"):
                    requested = setting[key]
                    if (key == "model" and requested == "host_default") or (key == "write_scope" and requested == []):
                        continue
                    mapped = [r for r in valid_requirements if r["scope"] == nid and r["kind"] == key and r["value"] == requested]
                    if not mapped:
                        blockers.append(f"{nid}: missing exact {key} requirement mapping")
                node = nodes.get(nid)
                if node and any(package["flow"]["capabilities"][t]["effect"] == "local_write" for t in node["tools"]):
                    check(bool(setting["write_scope"]), f"{nid}: local_write tools require explicit write_scope")
    acceptance = package["acceptance"]
    if package["schema"] == SCHEMA_V1 and shape(acceptance, "criteria", "acceptance"):
        criteria = acceptance["criteria"]
        check(isinstance(criteria, list) and bool(criteria), "Acceptance criteria must be nonempty")
        ids = set()
        for c in criteria if isinstance(criteria, list) else []:
            if not shape(c, "id kind required assertion", "criterion"):
                continue
            if not nonempty(c["id"]):
                errors.append("Criterion needs a nonempty id")
                continue
            check(c["id"] not in ids, f"Duplicate criterion: {c['id']}")
            ids.add(c["id"])
            check(c["kind"] in ("machine", "human"), f"{c['id']}: invalid grader kind")
            check(type(c["required"]) is bool, f"{c['id']}: required must be boolean")
            check(nonempty(c["assertion"]), f"{c['id']}: assertion required")
    elif package["schema"] == SCHEMA_V2:
        if shape(acceptance, "plan plan_hash", "acceptance"):
            try:
                plan = _read_plan(acceptance)
                plan_result = evalplan.validate(plan)
                if not isinstance(plan_result, dict):
                    errors.append("acceptance.plan: validator returned malformed result")
                else:
                    errors.extend(f"acceptance.plan: {message}" for message in plan_result.get("errors", []))
                    check(plan_result.get("valid") is True, "acceptance.plan: invalid frozen evaluation plan")
                try:
                    expected_plan_hash = flow.digest(plan)
                except (TypeError, ValueError, OverflowError):
                    expected_plan_hash = None
                check(isinstance(acceptance["plan_hash"], str) and
                      acceptance["plan_hash"] == expected_plan_hash,
                      "acceptance.plan_hash: must be the canonical SHA-256 of the full plan")
                if flow_result.get("valid") and isinstance(plan, dict) and isinstance(plan.get("cases"), list):
                    for case in plan["cases"]:
                        if not isinstance(case, dict):
                            continue
                        try:
                            flow.values_match(package["flow"], case.get("inputs"), package["flow"]["inputs"])
                        except (flow.FlowError, TypeError, ValueError, KeyError) as error:
                            errors.append(f"case {case.get('id', '<unknown>')}: inputs must exactly match Flow IR inputs: {error}")
            except (flow.FlowError, TypeError, ValueError, KeyError, AttributeError, OverflowError) as error:
                errors.append(f"acceptance: invalid frozen evaluation lock: {error}")
    else:
        check(False, "Unsupported package schema")
    result = {"valid": not errors, "errors": errors, "blockers": blockers,
              "declared_ready": not errors and not blockers,
              "warnings": flow_result.get("warnings", []),
              "boundary": "Host declarations are not permission enforcement or proof of task success."}
    if package["schema"] == SCHEMA_V2 and isinstance(acceptance, dict) and isinstance(acceptance.get("plan_hash"), str):
        result["plan_hash"] = acceptance["plan_hash"]
    return result


def require_valid(package, runnable=False):
    result = validate(package)
    if not result["valid"] or (runnable and result["blockers"]):
        raise flow.FlowError("; ".join(result["errors"] + result["blockers"]))
    return result


def start(package, inputs):
    require_valid(package, runnable=True)
    state = {"package_hash": flow.digest(package), "flow_state": flow.start(package["flow"], inputs)}
    if _is_v2(package):
        state["plan_hash"] = package["acceptance"]["plan_hash"]
        state["input_hash"] = flow.digest(inputs)
    return state


def pending(package, state):
    require_valid(package, runnable=True)
    expected_keys = {"package_hash", "plan_hash", "input_hash", "flow_state"} if _is_v2(package) else {"package_hash", "flow_state"}
    if not isinstance(state, dict) or set(state) != expected_keys or not isinstance(state["flow_state"], dict):
        if _is_v2(package):
            raise flow.FlowError("V2 checkpoint needs package_hash, plan_hash, input_hash and an object flow_state")
        raise flow.FlowError("Checkpoint needs package_hash and an object flow_state")
    if _is_v2(package) and state.get("plan_hash") != package["acceptance"]["plan_hash"]:
        raise flow.FlowError("Plan changed: create a new run or explicitly migrate validated artifacts")
    if state.get("package_hash") != flow.digest(package):
        raise flow.FlowError("Package changed: create a new run or explicitly migrate validated artifacts")
    if _is_v2(package):
        try:
            stored_inputs = _checkpoint_inputs(package, state["flow_state"])
            input_hash = flow.digest(stored_inputs)
        except (flow.FlowError, TypeError, ValueError, KeyError, OverflowError) as error:
            raise flow.FlowError(f"Invalid checkpoint input binding: {error}") from error
        if not isinstance(state["input_hash"], str) or state["input_hash"] != input_hash:
            raise flow.FlowError("Checkpoint input_hash does not match immutable Flow inputs")
    dispatch = flow.pending(package["flow"], state["flow_state"])
    if _is_v2(package):
        dispatch["plan_hash"] = package["acceptance"]["plan_hash"]
        dispatch["input_hash"] = state["input_hash"]
    if dispatch["status"] == "ready":
        dispatch["execution_settings"] = copy.deepcopy(package["execution"]["node_settings"][dispatch["node"]])
        dispatch["host_requirements"] = copy.deepcopy([r for r in package["execution"]["requirements"] if r["scope"] in ("flow", dispatch["node"])])
    return dispatch


def advance(package, state, response):
    pending(package, state)
    result = {"package_hash": state["package_hash"],
              "flow_state": flow.advance(package["flow"], state["flow_state"], response)}
    if _is_v2(package):
        result["plan_hash"] = state["plan_hash"]
        result["input_hash"] = state["input_hash"]
    return result


def compile_package(package, destination):
    validation = require_valid(package)
    result = flow.compile_flow(package["flow"], destination)
    out = Path(destination)
    flow.save(out / "package.json", package, exclusive=True)
    for nid, settings in package["execution"]["node_settings"].items():
        path = out / "prompts" / f"{nid}.md"
        requirements = [r for r in package["execution"]["requirements"] if r["scope"] in ("flow", nid)]
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n## Host execution requirements\n\n```json\n" + json.dumps({"settings": settings, "requirements": requirements}, ensure_ascii=False, indent=2) + "\n```\n")
    with (out / "runbook.md").open("a", encoding="utf-8") as stream:
        stream.write("\n## Unified package\n\nUse packagectl.py start/next/advance with package.json; do not bypass its requirements via flowctl.py.\n\n")
        stream.write("Declared ready: " + str(validation["declared_ready"]).lower() + ". Host verification is still required.\n\n")
        stream.write("```json\n" + json.dumps(validation, ensure_ascii=False, indent=2) + "\n```\n")
    result.update({"status": "compiled", "package_hash": flow.digest(package), "declared_ready": validation["declared_ready"], "blockers": validation["blockers"]})
    if _is_v2(package):
        result["plan_hash"] = package["acceptance"]["plan_hash"]
    return result


def _assess_v2(package, results, validation):
    if not isinstance(results, dict) or set(results) != {"package_hash", "plan_hash", "cases"}:
        raise flow.FlowError("V2 results need exactly package_hash, plan_hash and cases")
    if results["package_hash"] != flow.digest(package):
        raise flow.FlowError("Results package_hash does not match this package")
    expected_plan_hash = package["acceptance"]["plan_hash"]
    if results["plan_hash"] != expected_plan_hash:
        raise flow.FlowError("Results plan_hash does not match the frozen plan")
    if not isinstance(results["cases"], list):
        raise flow.FlowError("cases must be a list")

    plan = _read_plan(package["acceptance"])
    criteria = {c["id"]: c for c in plan["criteria"]}
    cases = {case["id"]: case for case in plan["cases"]}
    submitted = {}
    for result in results["cases"]:
        if not isinstance(result, dict) or set(result) != {"case_id", "run", "checks"}:
            raise flow.FlowError("Each case result needs exactly case_id, run and checks")
        case_id = result["case_id"]
        if not isinstance(case_id, str) or case_id not in cases:
            raise flow.FlowError(f"Unknown case_id: {case_id}")
        if case_id in submitted:
            raise flow.FlowError(f"Duplicate case result: {case_id}")
        case = cases[case_id]
        if not isinstance(result["checks"], list):
            raise flow.FlowError(f"{case_id}: checks must be a list")
        mapped = set(case["criteria"])
        seen_checks = {}
        for check in result["checks"]:
            if not isinstance(check, dict) or set(check) != {"id", "kind", "status", "evidence"}:
                raise flow.FlowError(f"{case_id}: each check needs id, kind, status and evidence")
            cid = check["id"]
            if not isinstance(cid, str) or cid not in mapped:
                raise flow.FlowError(f"{case_id}: criterion is not mapped to this case: {cid}")
            if cid in seen_checks:
                raise flow.FlowError(f"{case_id}: duplicate criterion result: {cid}")
            criterion = criteria[cid]
            if check["kind"] != criterion["kind"]:
                raise flow.FlowError(f"{case_id}: cannot substitute grader kind for {cid}")
            if check["status"] not in ("pass", "fail", "not_run") or not flow.strings(check["evidence"]):
                raise flow.FlowError(f"{case_id}: invalid result for {cid}")
            if check["status"] != "not_run" and not check["evidence"]:
                raise flow.FlowError(f"{case_id}: evidence reference required for {cid}")
            seen_checks[cid] = check["status"]

        run_status = None
        run = result["run"]
        if run is None:
            if any(status == "pass" for status in seen_checks.values()):
                raise flow.FlowError(f"{case_id}: checks cannot pass without a run")
        else:
            # Validate the packagectl envelope and Flow checkpoint before using its status.
            if not isinstance(run, dict) or set(run) != {"package_hash", "plan_hash", "input_hash", "flow_state"}:
                raise flow.FlowError(f"{case_id}: run must be a v2 packagectl checkpoint")
            flow_state = run["flow_state"]
            flow_state_keys = {"state_version", "flow_hash", "run_id", "status", "node",
                               "steps", "visits", "artifacts", "trace"}
            if not isinstance(flow_state, dict) or set(flow_state) != flow_state_keys:
                raise flow.FlowError(f"{case_id}: malformed Flow checkpoint")
            if (flow_state.get("state_version") != "1.0" or
                    not isinstance(flow_state.get("run_id"), str) or not flow_state["run_id"] or
                    flow_state.get("status") not in ("running", "completed", "failed", "blocked") or
                    type(flow_state.get("steps")) is not int or flow_state["steps"] < 0 or
                    not isinstance(flow_state.get("visits"), dict) or
                    not isinstance(flow_state.get("artifacts"), dict) or
                    not isinstance(flow_state.get("trace"), list)):
                raise flow.FlowError(f"{case_id}: malformed Flow checkpoint")
            try:
                flow.canonical(run)
            except (TypeError, ValueError, OverflowError) as error:
                raise flow.FlowError(f"{case_id}: checkpoint must be finite JSON data: {error}") from error
            visits = flow_state["visits"]
            if (any(not isinstance(node_id, str) or type(count) is not int or count < 0
                    for node_id, count in visits.items()) or
                    sum(visits.values()) != flow_state["steps"] or
                    len(flow_state["trace"]) != flow_state["steps"]):
                raise flow.FlowError(f"{case_id}: inconsistent Flow checkpoint counters")
            terminal_nodes = {"completed": "$done", "failed": "$failed", "blocked": "$blocked"}
            if ((flow_state["status"] in terminal_nodes and
                 (flow_state["node"] != terminal_nodes[flow_state["status"]] or flow_state["steps"] == 0)) or
                    (flow_state["status"] == "running" and flow_state["node"] in terminal_nodes.values())):
                raise flow.FlowError(f"{case_id}: checkpoint status and node are inconsistent")
            try:
                dispatch = pending(package, run)
            except (flow.FlowError, TypeError, ValueError, KeyError, AttributeError, IndexError) as error:
                raise flow.FlowError(f"{case_id}: run binding or checkpoint is invalid: {error}") from error
            if run["package_hash"] != flow.digest(package):
                raise flow.FlowError(f"{case_id}: run package_hash does not match this package")
            if run["plan_hash"] != expected_plan_hash:
                raise flow.FlowError(f"{case_id}: run plan_hash does not match the frozen plan")
            if flow_state["flow_hash"] != flow.digest(package["flow"]):
                raise flow.FlowError(f"{case_id}: run Flow hash does not match this package")
            actual_inputs = {name: flow_state["artifacts"].get(name) for name in package["flow"]["inputs"]}
            try:
                flow.values_match(package["flow"], actual_inputs, package["flow"]["inputs"])
                same_inputs = flow.canonical(actual_inputs) == flow.canonical(case["inputs"])
            except (flow.FlowError, TypeError, ValueError, KeyError, OverflowError) as error:
                raise flow.FlowError(f"{case_id}: run inputs are invalid: {error}") from error
            if not same_inputs:
                raise flow.FlowError(f"{case_id}: run immutable inputs do not match the frozen case")
            run_status = dispatch.get("status")
            if any(status == "pass" for status in seen_checks.values()) and run_status not in ("completed", "failed", "blocked"):
                raise flow.FlowError(f"{case_id}: an incomplete run cannot support passing checks")

        submitted[case_id] = {"checks": seen_checks, "run_status": run_status, "run": run}

    required_failed_cases, required_failed_checks = [], []
    required_pending_cases, required_pending_checks = [], []
    optional_gaps = []
    case_statuses = {}
    for case_id, case in cases.items():
        row = submitted.get(case_id)
        if row is None:
            case_statuses[case_id] = "not_run"
            if case["required"]:
                required_pending_cases.append(case_id)
            else:
                optional_gaps.append({"case_id": case_id, "reason": "case result missing"})
            continue

        actual_status = row["run_status"]
        case_statuses[case_id] = actual_status or "not_run"
        if row["run"] is None:
            if case["required"]:
                required_pending_cases.append(case_id)
            else:
                optional_gaps.append({"case_id": case_id, "reason": "run missing"})
        elif actual_status not in ("completed", "failed", "blocked"):
            if case["required"]:
                required_pending_cases.append(case_id)
            else:
                optional_gaps.append({"case_id": case_id, "reason": "run incomplete", "actual": actual_status})
        elif actual_status != case["expected_status"]:
            if case["required"]:
                required_failed_cases.append({"case_id": case_id, "expected": case["expected_status"], "actual": actual_status})
            else:
                optional_gaps.append({"case_id": case_id, "reason": "run status mismatch",
                                      "expected": case["expected_status"], "actual": actual_status})

        for cid in case["criteria"]:
            criterion = criteria[cid]
            status = row["checks"].get(cid, "not_run")
            if case["required"] and criterion["required"]:
                if status == "fail":
                    required_failed_checks.append({"case_id": case_id, "criterion_id": cid})
                elif status != "pass":
                    required_pending_checks.append({"case_id": case_id, "criterion_id": cid})
            elif status != "pass":
                optional_gaps.append({"case_id": case_id, "criterion_id": cid, "status": status})

    required_failures = bool(required_failed_cases or required_failed_checks)
    has_pending = bool(required_pending_cases or required_pending_checks or validation["blockers"])
    verdict = "fail" if required_failures else "pending" if has_pending else "limited" if optional_gaps else "pass"
    return {"verdict": verdict,
            "required_failed_cases": required_failed_cases,
            "required_failed_checks": required_failed_checks,
            "required_pending_cases": required_pending_cases,
            "required_pending_checks": required_pending_checks,
            "optional_gaps": optional_gaps,
            "case_statuses": case_statuses,
            "blockers": validation["blockers"],
            "boundary": "Package and checkpoint bindings, input values, terminal status, and declared coverage are checked here. Submitted evidence, real model identity, and semantic truth are not proven by this code."}


def assess(package, results):
    validation = validate(package)
    if not validation["valid"]:
        return {"verdict": "fail", "structural_errors": validation["errors"]}
    if _is_v2(package):
        return _assess_v2(package, results, validation)
    if not isinstance(results, dict) or set(results) != {"package_hash", "checks"} or results["package_hash"] != flow.digest(package):
        raise flow.FlowError("Results must contain the exact package_hash and checks")
    if not isinstance(results["checks"], list):
        raise flow.FlowError("checks must be a list")
    criteria = {c["id"]: c for c in package["acceptance"]["criteria"]}
    seen = {}
    for check in results["checks"]:
        if not isinstance(check, dict) or set(check) != {"id", "kind", "status", "evidence"}:
            raise flow.FlowError("Each result needs id, kind, status, evidence")
        cid = check["id"]
        if not isinstance(cid, str) or cid not in criteria or cid in seen:
            raise flow.FlowError(f"Unknown or duplicate result: {cid}")
        if check["kind"] != criteria[cid]["kind"]:
            raise flow.FlowError(f"Cannot substitute grader kind for {cid}")
        if check["status"] not in ("pass", "fail", "not_run") or not flow.strings(check["evidence"]):
            raise flow.FlowError(f"Invalid result for {cid}")
        if check["status"] != "not_run" and not check["evidence"]:
            raise flow.FlowError(f"Evidence reference required for {cid}")
        seen[cid] = check["status"]
    failures = [cid for cid, c in criteria.items() if c["required"] and seen.get(cid) == "fail"]
    missing = [cid for cid, c in criteria.items() if c["required"] and seen.get(cid, "not_run") == "not_run"]
    optional_gaps = [cid for cid, c in criteria.items() if not c["required"] and seen.get(cid) != "pass"]
    verdict = "fail" if failures else "pending" if missing or validation["blockers"] else "limited" if optional_gaps else "pass"
    return {"verdict": verdict, "required_failed": failures, "required_pending": missing,
            "optional_gaps": optional_gaps, "blockers": validation["blockers"],
            "boundary": "Structural checks are computed here; evidence references and submitted task grades need independent inspection."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "compile", "start", "next", "advance", "assess"):
        item = commands.add_parser(name)
        item.add_argument("package")
        if name == "compile":
            item.add_argument("--out", required=True)
        if name in ("start", "next", "advance"):
            item.add_argument("--state", required=True)
        if name == "start":
            item.add_argument("--inputs", required=True)
        if name == "advance":
            item.add_argument("--response", required=True)
        if name == "assess":
            item.add_argument("--results", required=True)
    args = parser.parse_args()
    try:
        package = load(args.package)
        if args.command == "validate":
            result = validate(package)
        elif args.command == "compile":
            result = compile_package(package, args.out)
        elif args.command == "assess":
            result = assess(package, load(args.results))
        elif args.command == "start":
            state = start(package, load(args.inputs))
            flow.save(args.state, state, exclusive=True)
            result = pending(package, state)
        elif args.command == "next":
            result = pending(package, load(args.state))
        else:
            state = advance(package, load(args.state), load(args.response))
            flow.save(args.state, state)
            result = pending(package, state)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        if result.get("valid") is False or result.get("declared_ready") is False or result.get("status") in ("failed", "blocked") or result.get("verdict") in ("fail", "pending", "limited"):
            return 2
        return 0
    except (ValueError, TypeError, KeyError, OSError, OverflowError, AttributeError, RecursionError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
