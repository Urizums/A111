#!/usr/bin/env python3
"""Run Forge's factory with an exact frozen plan and checked evaluation handoffs.

Local single-writer bookkeeping, not an authenticated audit log or model host.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

import evalplan
import designcheck
import flowctl as flow
import packagectl as package

META_PATH = Path(__file__).resolve().parents[1] / "assets" / "meta-flow.json"
SCHEMA = "forge-factory/1"
MATERIAL_OPERATIONS = {"inspect", "design", "modify"}
MATERIAL_CONFIG_KEY = "materials"
MAX_MATERIAL_MANIFEST_BYTES = 2 * 1024 * 1024


def spec():
    return package.load(META_PATH)


def _material_module():
    # Keep legacy factory runs independent from the optional material gate.
    try:
        import materialcheck
    except ImportError as error:
        raise flow.FlowError(f"Materials gate is unavailable: {error}") from error
    return materialcheck


def _material_result_shape(result):
    required = {"valid", "status", "manifest_sha256", "claim_scope", "allowed_operations",
                "blockers", "claim_limit", "material_sha256"}
    if not isinstance(result, dict) or set(result) != required:
        raise flow.FlowError("Materials assessor returned an incomplete assessment")
    if type(result["valid"]) is not bool or result["status"] not in ("pass", "blocked", "invalid"):
        raise flow.FlowError("Materials assessor returned an invalid status")
    if not isinstance(result["allowed_operations"], list) or not all(
            op in MATERIAL_OPERATIONS for op in result["allowed_operations"]):
        raise flow.FlowError("Materials assessor returned invalid allowed_operations")
    if not isinstance(result["blockers"], list) or not all(
            isinstance(item, str) and item.strip() for item in result["blockers"]):
        raise flow.FlowError("Materials assessor returned invalid blockers")
    if (not isinstance(result["claim_scope"], str) or not isinstance(result["claim_limit"], str) or
            not isinstance(result["material_sha256"], dict)):
        raise flow.FlowError("Materials assessor returned invalid claim or evidence hashes")
    flow.canonical(result)
    return result


def _manifest_digest(path):
    digest = hashlib.sha256()
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_MATERIAL_MANIFEST_BYTES:
            raise flow.FlowError("Materials manifest must be a regular file no larger than 2 MiB")
        stream = os.fdopen(fd, "rb")
        fd = -1
    finally:
        if fd >= 0:
            os.close(fd)
    with stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_regular_manifest(path):
    # O_NONBLOCK avoids hanging if a previously valid manifest is replaced by a FIFO.
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_MATERIAL_MANIFEST_BYTES:
            raise flow.FlowError("Materials manifest must be a regular file no larger than 2 MiB")
    finally:
        os.close(fd)


def _freeze_materials(inputs, materials, operation):
    if (materials is None) != (operation is None):
        raise flow.FlowError("--materials and --operation must be supplied together")
    environment = inputs.get("environment") if isinstance(inputs, dict) else None
    if not isinstance(environment, dict):
        raise flow.FlowError("Factory inputs need an object environment before materials can be configured")
    if MATERIAL_CONFIG_KEY in environment and (materials is not None or operation is not None):
        raise flow.FlowError("environment.materials is reserved; configure it with --materials and --operation")
    if materials is None:
        return inputs
    if operation not in MATERIAL_OPERATIONS:
        raise flow.FlowError("--operation must be inspect, design, or modify")
    path = Path(materials).resolve(strict=True)
    _require_regular_manifest(path)
    checker = _material_module()
    try:
        checker.require_valid(path)
        assessment = _material_result_shape(checker.assess(path))
        manifest_sha256 = _manifest_digest(path)
    except (OSError, TypeError, ValueError, KeyError, OverflowError, AttributeError) as error:
        raise flow.FlowError(f"Materials configuration is incomplete or invalid: {error}") from error
    if not assessment["valid"] or assessment["manifest_sha256"] != manifest_sha256:
        raise flow.FlowError("Materials manifest or evidence is invalid; no dispatch configuration was frozen")
    updated = copy.deepcopy(inputs)
    updated["environment"][MATERIAL_CONFIG_KEY] = {
        "path": str(path), "sha256": manifest_sha256, "operation": operation,
        "assessment": copy.deepcopy(assessment),
    }
    return updated


def _material_blocked(reason, current=None, operation=None):
    result = copy.deepcopy(current) if isinstance(current, dict) else {
        "valid": False, "status": "invalid", "manifest_sha256": None,
        "claim_scope": "local_material_integrity_and_declared_binding_only",
        "allowed_operations": [], "blockers": [], "claim_limit": "none",
        "material_sha256": {},
    }
    result.update({"configured": True, "operation": operation, "decision": "blocked",
                   "gate_blockers": [reason]})
    if isinstance(result.get("blockers"), list) and reason not in result["blockers"]:
        result["blockers"] = [*result["blockers"], reason]
    return result


def _materials_assessment(state):
    """Recheck the frozen manifest and all evidence before every host handoff."""
    artifacts = state.get("flow_state", {}).get("artifacts", {})
    environment = artifacts.get("environment") if isinstance(artifacts, dict) else None
    configured = isinstance(environment, dict) and MATERIAL_CONFIG_KEY in environment
    config = environment.get(MATERIAL_CONFIG_KEY) if configured else None
    if not configured:
        return {"configured": False, "operation": None, "decision": "not_configured",
                "valid": False, "status": "not_configured", "manifest_sha256": None,
                "claim_scope": "local_material_integrity_and_declared_binding_only",
                "allowed_operations": [], "blockers": ["Materials manifest not configured"],
                "claim_limit": "not_configured", "material_sha256": {},
                "gate_blockers": ["Materials manifest not configured"]}
    if (not isinstance(config, dict) or set(config) != {"path", "sha256", "operation", "assessment"} or
            not isinstance(config.get("path"), str) or not Path(config["path"]).is_absolute() or
            not isinstance(config.get("sha256"), str) or len(config["sha256"]) != 64 or
            any(c not in "0123456789abcdef" for c in config["sha256"]) or
            config.get("operation") not in MATERIAL_OPERATIONS):
        return _material_blocked("Frozen materials configuration is incomplete", operation=None)
    path, operation = Path(config["path"]), config["operation"]
    try:
        _require_regular_manifest(path)
        checker = _material_module()
        current = _material_result_shape(checker.assess(path))
    except (OSError, TypeError, ValueError, KeyError, OverflowError, AttributeError) as error:
        return _material_blocked(f"Materials assessment failed: {error}", operation=operation)

    reasons = []
    try:
        # require_valid checks manifest structure and every referenced evidence file.
        checker.require_valid(path)
    except (OSError, TypeError, ValueError, KeyError, OverflowError, AttributeError) as error:
        reasons.append(f"Materials manifest or evidence is invalid: {error}")
    try:
        observed_hash = _manifest_digest(path)
    except OSError as error:
        observed_hash = None
        reasons.append(f"Materials manifest is missing or unreadable: {error}")
    if observed_hash != config["sha256"] or current["manifest_sha256"] != config["sha256"]:
        reasons.append("Materials manifest hash drifted after factory start")
    try:
        baseline = _material_result_shape(config["assessment"])
    except (TypeError, ValueError, KeyError, OverflowError, AttributeError) as error:
        baseline = None
        reasons.append(f"Frozen materials assessment is incomplete: {error}")
    if baseline is not None and flow.canonical(current) != flow.canonical(baseline):
        reasons.append("Materials evidence assessment changed after factory start")
    if not current["valid"]:
        reasons.append("Materials assessment is invalid")
    if operation not in current["allowed_operations"]:
        reasons.append(f"Materials assessment does not allow operation: {operation}")
    if reasons:
        # Keep one copy of each reason while preserving order for readable dispatches.
        return _material_blocked("; ".join(dict.fromkeys(reasons)), current, operation)
    result = copy.deepcopy(current)
    result.update({"configured": True, "operation": operation, "decision": "allow",
                   "gate_blockers": []})
    return result


def start(inputs, materials=None, operation=None):
    frozen_inputs = _freeze_materials(inputs, materials, operation)
    return {"schema": SCHEMA, "flow_state": flow.start(spec(), frozen_inputs)}


def _artifact(state, name):
    return state["flow_state"]["artifacts"].get(name)


def check_state(state):
    if not isinstance(state, dict) or set(state) != {"schema", "flow_state"} or state["schema"] != SCHEMA or not isinstance(state["flow_state"], dict):
        raise flow.FlowError("Expected a forge-factory/1 checkpoint with object flow_state")
    fs = state["flow_state"]
    if not isinstance(fs.get("artifacts"), dict) or not isinstance(fs.get("trace"), list):
        raise flow.FlowError("Factory checkpoint needs artifact object and trace list")
    flow.pending(spec(), fs)  # Verify current meta-flow identity, budgets and types.
    contract = fs['artifacts'].get('contract')
    intakes = [t for t in fs['trace'] if t.get('node') == 'intake' and t.get('outcome') == 'ok']
    if contract is not None:
        designcheck.require_contract(contract, fs['artifacts'].get('request'))
        if len(intakes) != 1 or intakes[0].get('output_hash') != flow.digest({'contract': contract}):
            raise flow.FlowError('Contract differs from its intake handoff')
        original_inputs = {key: fs['artifacts'][key] for key in spec()['inputs']}
        if intakes[0].get('input_hash') != flow.digest(original_inputs):
            raise flow.FlowError('Original request or environment differs from its intake input')
    elif intakes:
        raise flow.FlowError('Intake contract is missing')
    lock = fs["artifacts"].get("test_plan")
    freezes = [t for t in fs["trace"] if t.get("node") == "eval_design" and t.get("outcome") == "ok"]
    if lock is None:
        if freezes:
            raise flow.FlowError("Frozen plan is missing from the checkpoint")
    else:
        evalplan.read_lock(lock)
        designcheck.require_plan(contract, lock['plan'])
        if len(freezes) != 1 or freezes[0].get("output_hash") != flow.digest({"test_plan": lock}):
            raise flow.FlowError("Frozen plan differs from the exact eval_design handoff")
    architecture = fs['artifacts'].get('architecture')
    designs = [t for t in fs['trace'] if t.get('node') in ('architect', 'repair') and t.get('outcome') == 'ok']
    if architecture is not None:
        designcheck.require_architecture(contract, _lock(state)['plan'], architecture)
        if not designs or designs[-1].get('output_hash') != flow.digest({'architecture': architecture}):
            raise flow.FlowError('Architecture differs from its recorded design handoff')
    elif designs:
        raise flow.FlowError('Recorded architecture is missing')
    candidate = fs["artifacts"].get("candidate")
    builds = [t for t in fs["trace"] if t.get("node") == "build" and t.get("outcome") == "ok"]
    if candidate is not None:
        _check_candidate(state, candidate)
        if not builds or builds[-1].get("output_hash") != flow.digest({"candidate": candidate}):
            raise flow.FlowError("Candidate differs from its recorded build handoff")
        if designs and builds[-1]['step'] > designs[-1]['step']:
            designcheck.require_architecture(contract, lock['plan'], architecture, candidate['package']['flow'])
    elif builds:
        raise flow.FlowError("Built candidate is missing from the checkpoint")
    evaluation = fs["artifacts"].get("evaluation")
    reviews = [t for t in fs["trace"] if t.get("node") == "verify" and t.get("outcome") in ("ok", "limited", "fixable")]
    if evaluation is not None:
        if not reviews or reviews[-1].get("output_hash") != flow.digest({"evaluation": evaluation}):
            raise flow.FlowError("Evaluation differs from its recorded verify handoff")
        # A previous evaluation may refer to the previous candidate during repair.
        # Recompute only when it is for the current candidate, otherwise retain it
        # as prior evidence until verify replaces it.
        if candidate and isinstance(evaluation, dict) and isinstance(evaluation.get("results"), dict) and evaluation["results"].get("package_hash") == candidate["package_hash"]:
            computed = package.assess(candidate["package"], evaluation["results"])
            if evaluation.get("assessment") != computed:
                raise flow.FlowError("Stored assessment differs from current deterministic checks")
    elif reviews:
        raise flow.FlowError("Recorded evaluation is missing from the checkpoint")
    return state


def _lock(state):
    lock = _artifact(state, "test_plan")
    if lock is None:
        raise flow.FlowError("Freeze the complete evaluation plan before this operation")
    evalplan.read_lock(lock)
    return lock


def _check_candidate(state, candidate):
    if not isinstance(candidate, dict) or not {"package", "package_hash"} <= set(candidate):
        raise flow.FlowError("Candidate must include full package and package_hash")
    p = candidate["package"]
    if not isinstance(p, dict) or p.get("schema") != "forge-package/2":
        raise flow.FlowError("New factory candidates require forge-package/2")
    package.require_valid(p)
    if p["acceptance"] != _lock(state):
        raise flow.FlowError("Candidate must carry the exact frozen plan, not a summary or revision")
    if candidate["package_hash"] != flow.digest(p):
        raise flow.FlowError("Candidate package_hash does not match its full package")
    return p


def pending(state):
    check_state(state)
    dispatch = flow.pending(spec(), state["flow_state"])
    materials = _materials_assessment(state)
    if materials["decision"] == "blocked":
        return {"status": "blocked", "node": dispatch.get("node"),
                "reason": "; ".join(materials["gate_blockers"]),
                "materials_assessment": materials}
    dispatch["materials_assessment"] = materials
    if _artifact(state, "test_plan") is not None:
        dispatch["plan_hash"] = _lock(state)["plan_hash"]
    return dispatch


def freeze_plan(state, plan, source="supplied complete plan"):
    dispatch = pending(state)
    if dispatch.get("status") != "ready" or dispatch.get("node") != "eval_design":
        raise flow.FlowError("Plan freeze is allowed only at the eval_design stage")
    lock = evalplan.make_lock(plan)
    designcheck.require_plan(_artifact(state, 'contract'), plan)
    response = {"invocation_id": dispatch["invocation_id"], "outcome": "ok",
                "artifacts": {"test_plan": lock},
                "evidence": [f"Complete plan read from {source}; canonical SHA256 {lock['plan_hash']}. The full content is stored in this handoff before build."]}
    new = {"schema": SCHEMA, "flow_state": flow.advance(spec(), state["flow_state"], response)}
    check_state(new)
    return new


def bind_package(state, draft):
    dispatch = pending(state)
    if dispatch.get("status") != "ready" or dispatch.get("node") != "build":
        raise flow.FlowError("Package binding is allowed only at the build stage")
    if not isinstance(draft, dict):
        raise flow.FlowError("Draft package must be an object")
    p = copy.deepcopy(draft)
    p["schema"] = "forge-package/2"
    p["acceptance"] = copy.deepcopy(_lock(state))
    package.require_valid(p)
    designcheck.require_architecture(_artifact(state, 'contract'), _lock(state)['plan'], _artifact(state, 'architecture'), p['flow'])
    return p


def advance(state, response):
    dispatch = pending(state)
    if dispatch.get("status") != "ready":
        raise flow.FlowError(f"Factory cannot advance: {dispatch}")
    if not isinstance(response, dict) or not isinstance(response.get("artifacts"), dict):
        raise flow.FlowError("Expected a dispatcher response with object artifacts")
    response = copy.deepcopy(response)
    node, outcome, artifacts = dispatch["node"], response.get("outcome"), response["artifacts"]
    if node == 'intake' and outcome == 'ok':
        designcheck.require_contract(artifacts.get('contract'), _artifact(state, 'request'))
    if node in ('architect', 'repair') and outcome == 'ok':
        designcheck.require_architecture(_artifact(state, 'contract'), _lock(state)['plan'], artifacts.get('architecture'))
    if node == "eval_design" and outcome == "ok":
        raise flow.FlowError("Use freeze-plan with the complete plan file; summary-only eval_design responses are not accepted")
    if node == "build" and outcome == "ok":
        _check_candidate(state, artifacts.get("candidate"))
        designcheck.require_architecture(_artifact(state, 'contract'), _lock(state)['plan'], _artifact(state, 'architecture'), artifacts['candidate']['package']['flow'])
    if node == "verify" and outcome in ("ok", "limited", "fixable"):
        evaluation = artifacts.get("evaluation")
        if not isinstance(evaluation, dict) or "results" not in evaluation:
            raise flow.FlowError("Verification needs the full case results object")
        candidate = _artifact(state, "candidate")
        _check_candidate(state, candidate)
        computed = package.assess(candidate["package"], evaluation["results"])
        if "assessment" in evaluation and evaluation["assessment"] != computed:
            raise flow.FlowError("A supplied assessment cannot replace the computed assessment")
        if outcome == "ok" and computed["verdict"] != "pass":
            raise flow.FlowError(f"Verification cannot report ok: assessment is {computed['verdict']}")
        evaluation["assessment"] = computed
    if node == "deliver" and outcome == "ok":
        delivery = artifacts.get("delivery")
        evaluation = _artifact(state, "evaluation")
        candidate = _artifact(state, "candidate")
        if not isinstance(delivery, dict) or not isinstance(evaluation, dict):
            raise flow.FlowError("Delivery needs a prior verified evaluation and object delivery")
        _check_candidate(state, candidate)
        computed = package.assess(candidate["package"], evaluation["results"])
        if computed != evaluation.get("assessment"):
            raise flow.FlowError("Delivery assessment no longer matches its candidate")
        bindings = {"assessment": computed, "plan_hash": _lock(state)["plan_hash"], "package_hash": candidate["package_hash"]}
        for key, value in bindings.items():
            if key in delivery and delivery[key] != value:
                raise flow.FlowError(f"Delivery {key} cannot override the recorded binding")
            delivery[key] = copy.deepcopy(value)
    new = {"schema": SCHEMA, "flow_state": flow.advance(spec(), state["flow_state"], response)}
    check_state(new)
    return new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "next", "freeze-plan", "bind-package", "export-plan", "advance", "check"):
        item = commands.add_parser(name)
        item.add_argument("--state", required=True)
        if name == "start":
            item.add_argument("--inputs", required=True)
            item.add_argument("--materials")
            item.add_argument("--operation", choices=sorted(MATERIAL_OPERATIONS))
        if name == "freeze-plan":
            item.add_argument("plan")
        if name == "bind-package":
            item.add_argument("draft")
        if name in ("bind-package", "export-plan"):
            item.add_argument("--out", required=True)
        if name == "advance":
            item.add_argument("--response", required=True)
    args = parser.parse_args()
    try:
        if args.command == "start":
            state = start(package.load(args.inputs), args.materials, args.operation)
            flow.save(args.state, state, exclusive=True)
            result = pending(state)
        else:
            state = package.load(args.state)
            check_state(state)
            if args.command == "next":
                result = pending(state)
            elif args.command == "freeze-plan":
                state = freeze_plan(state, evalplan.load(args.plan), str(Path(args.plan).resolve()))
                flow.save(args.state, state)
                result = pending(state)
            elif args.command == "bind-package":
                p = bind_package(state, package.load(args.draft))
                flow.save(args.out, p, exclusive=True)
                result = {"status": "bound", "package_hash": flow.digest(p), "plan_hash": p["acceptance"]["plan_hash"], "path": str(Path(args.out).resolve())}
            elif args.command == "export-plan":
                lock = _lock(state)
                flow.save(args.out, lock["plan"], exclusive=True)
                result = {"status": "exported", "plan_hash": lock["plan_hash"], "path": str(Path(args.out).resolve())}
            elif args.command == "check":
                lock, candidate = _artifact(state, "test_plan"), _artifact(state, "candidate")
                result = {"status": state["flow_state"]["status"], "steps": state["flow_state"]["steps"],
                          "plan_hash": lock["plan_hash"] if lock else None,
                          "package_hash": candidate["package_hash"] if candidate else None}
            else:
                state = advance(state, package.load(args.response))
                flow.save(args.state, state)
                result = pending(state)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 2 if result.get("status") in ("failed", "blocked") else 0
    except (ValueError, TypeError, KeyError, OSError, OverflowError, AttributeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
