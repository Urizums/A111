#!/usr/bin/env python3
"""Persistent host-driven project plan controller.

This bundled-module CLI validates task graphs, records attempts and local evidence,
and supports recovery. It never calls models or tools and does not authenticate
semantic claims, authorization, or evidence producers. State files assume one writer.
Declare write_paths relative to one project root: overlap checks are lexical and do
not resolve relative/absolute aliases or symlinks, isolate workers, or enforce access.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import stat
import sys
import tempfile
import uuid

import evalplan

SCHEMA = "forge-project-plan/1"
STATE_SCHEMA = "forge-project-state/1"
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
LEVELS = {"static": 0, "runtime": 1, "review": 2}
TASK_STATUSES = {"todo", "running", "done", "blocked", "failed"}
OUTCOMES = {"running", "done", "blocked", "failed"}


class ProjectError(ValueError):
    """Invalid project plan, state transition, or evidence."""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ProjectError(f"Value is not canonical JSON: {exc}") from exc


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _reject_constant(value):
    raise ProjectError(f"Non-finite JSON number: {value}")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProjectError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path):
    try:
        with open(path, encoding="utf-8") as stream:
            return json.load(stream, parse_constant=_reject_constant,
                             object_pairs_hook=_unique_object)
    except ProjectError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ProjectError(f"Cannot read JSON file {path}: {exc}") from exc


def save(path, value, exclusive=False):
    """Atomic replace for a single writer; hard-link creation for new states."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=".projectctl-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ProjectError(f"{label} must be a nonempty string")
    return value


def _id(value, label):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ProjectError(f"{label} must be 1-128 safe ASCII characters")
    return value


def _string_list(value, label, allow_empty=True):
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ProjectError(f"{label} must be a {'nonempty ' if not allow_empty else ''}string list")
    for index, item in enumerate(value):
        _string(item, f"{label}[{index}]")
    return value


def _exact_keys(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ProjectError(f"{label} keys must be exactly {sorted(keys)}")


def _timestamp(value, label):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ProjectError(f"{label} must be a UTC timestamp ending in Z")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProjectError(f"{label} is invalid") from exc


def make_evaluation_lock(plan, source_path=None):
    result = evalplan.validate(plan)
    if not result["valid"]:
        raise ProjectError("Invalid forge-eval/1 plan: " + "; ".join(result["errors"]))
    source = str(Path(source_path).expanduser().resolve()) if source_path else None
    return {"plan": deepcopy(plan), "plan_hash": digest(plan), "source_path": source}


def validate_evaluation_lock(lock):
    if lock is None:
        return
    _exact_keys(lock, {"plan", "plan_hash", "source_path"}, "evaluation_plan_lock")
    result = evalplan.validate(lock["plan"])
    if not result["valid"]:
        raise ProjectError("Invalid locked forge-eval/1 plan: " + "; ".join(result["errors"]))
    if lock["plan_hash"] != digest(lock["plan"]):
        raise ProjectError("evaluation_plan_lock hash does not match its complete plan")
    source = lock["source_path"]
    if source is not None and (not isinstance(source, str) or not source.strip()):
        raise ProjectError("evaluation_plan_lock.source_path must be null or a nonempty path")


def validate_runtime_mapping(plan, evaluation_lock):
    if evaluation_lock is None:
        return
    required_criteria = {item["id"] for item in evaluation_lock["plan"]["criteria"]
                         if item["required"] is True}
    runtime_ids = {item["id"] for item in plan["acceptance"] if item["level"] == "runtime"}
    missing = sorted(runtime_ids - required_criteria)
    if missing:
        raise ProjectError("Bound forge-eval/1 plan must contain required criteria for runtime acceptance IDs: "
                           + ", ".join(missing))


def validate_plan(plan):
    errors = []

    def check(fn):
        try:
            fn()
        except ProjectError as exc:
            errors.append(str(exc))

    if not isinstance(plan, dict):
        return {"valid": False, "errors": ["Plan must be an object"]}
    allowed = {"schema_version", "id", "goal", "deliverable_kind",
               "requirements", "acceptance", "tasks", "defaults", "unknowns"}
    if not {"schema_version", "id", "goal", "deliverable_kind",
            "requirements", "acceptance", "tasks"} <= set(plan):
        errors.append("Plan is missing required root fields")
    if set(plan) - allowed:
        errors.append(f"Unknown plan root fields: {sorted(set(plan) - allowed)}")
    if errors:
        return {"valid": False, "errors": errors}

    check(lambda: _string(plan["schema_version"], "schema_version"))
    if plan["schema_version"] != SCHEMA:
        errors.append(f"Unsupported schema_version; expected {SCHEMA}")
    check(lambda: _id(plan["id"], "plan id"))
    check(lambda: _string(plan["goal"], "goal"))
    check(lambda: _string(plan["deliverable_kind"], "deliverable_kind"))

    requirements = plan["requirements"]
    acceptance = plan["acceptance"]
    tasks = plan["tasks"]
    if not isinstance(requirements, list) or not requirements:
        errors.append("requirements must be a nonempty list")
        requirements = []
    if not isinstance(acceptance, list) or not acceptance:
        errors.append("acceptance must be a nonempty list")
        acceptance = []
    if not isinstance(tasks, list) or not tasks:
        errors.append("tasks must be a nonempty list")
        tasks = []

    ids = {plan.get("id")} if isinstance(plan.get("id"), str) else set()
    req_by_id, acc_by_id, task_by_id = {}, {}, {}

    for index, item in enumerate(requirements):
        label = f"requirements[{index}]"
        try:
            _exact_keys(item, {"id", "text", "origin", "basis", "acceptance_ids"}, label)
            rid = _id(item["id"], f"{label}.id")
            _string(item["text"], f"{label}.text")
            _string(item["origin"], f"{label}.origin")
            if item["origin"] not in {"explicit", "derived", "default"}:
                raise ProjectError(f"{label}.origin must be explicit, derived, or default")
            _string(item["basis"], f"{label}.basis")
            _string_list(item["acceptance_ids"], f"{label}.acceptance_ids", allow_empty=False)
            if len(item["acceptance_ids"]) != len(set(item["acceptance_ids"])):
                raise ProjectError(f"{label}.acceptance_ids contains duplicates")
            req_by_id[rid] = item
            if rid in ids:
                raise ProjectError(f"Duplicate ID: {rid}")
            ids.add(rid)
        except (ProjectError, TypeError) as exc:
            errors.append(str(exc))

    for index, item in enumerate(acceptance):
        label = f"acceptance[{index}]"
        try:
            _exact_keys(item, {"id", "assertion", "required", "level"}, label)
            aid = _id(item["id"], f"{label}.id")
            _string(item["assertion"], f"{label}.assertion")
            if type(item["required"]) is not bool:
                raise ProjectError(f"{label}.required must be boolean")
            if item["level"] not in LEVELS:
                raise ProjectError(f"{label}.level must be one of {sorted(LEVELS)}")
            acc_by_id[aid] = item
            if aid in ids:
                raise ProjectError(f"Duplicate ID: {aid}")
            ids.add(aid)
        except (ProjectError, TypeError) as exc:
            errors.append(str(exc))

    for index, item in enumerate(tasks):
        label = f"tasks[{index}]"
        try:
            _exact_keys(item, {"id", "title", "depends_on", "owner", "write_paths", "acceptance_ids"}, label)
            tid = _id(item["id"], f"{label}.id")
            _string(item["title"], f"{label}.title")
            _string_list(item["depends_on"], f"{label}.depends_on")
            _string_list(item["write_paths"], f"{label}.write_paths")
            _string_list(item["acceptance_ids"], f"{label}.acceptance_ids")
            owner = item["owner"]
            if owner is not None and (not isinstance(owner, str) or not owner.strip()):
                raise ProjectError(f"{label}.owner must be null or a nonempty string")
            for field in ("depends_on", "acceptance_ids"):
                if len(item[field]) != len(set(item[field])):
                    raise ProjectError(f"{label}.{field} contains duplicates")
            task_by_id[tid] = item
            if tid in ids:
                raise ProjectError(f"Duplicate ID: {tid}")
            ids.add(tid)
        except (ProjectError, TypeError) as exc:
            errors.append(str(exc))

    for field in ("defaults", "unknowns"):
        if field in plan:
            try:
                _string_list(plan[field], field)
            except ProjectError as exc:
                errors.append(str(exc))

    for rid, item in req_by_id.items():
        for aid in item["acceptance_ids"]:
            if aid not in acc_by_id:
                errors.append(f"Requirement {rid} references unknown acceptance {aid}")
    referenced_acceptance = {aid for item in req_by_id.values() for aid in item["acceptance_ids"]}
    for aid in acc_by_id:
        if aid not in referenced_acceptance:
            errors.append(f"Acceptance {aid} is not mapped from a requirement")

    has_required = False
    mapped_acceptance = set()
    for tid, item in task_by_id.items():
        for dep in item["depends_on"]:
            if dep not in task_by_id:
                errors.append(f"Task {tid} depends on unknown task {dep}")
            if dep == tid:
                errors.append(f"Task {tid} cannot depend on itself")
        for aid in item["acceptance_ids"]:
            if aid not in acc_by_id:
                errors.append(f"Task {tid} references unknown acceptance {aid}")
            mapped_acceptance.add(aid)
            if aid in acc_by_id and acc_by_id[aid]["required"]:
                has_required = True
    for aid, item in acc_by_id.items():
        if item["required"] and aid not in mapped_acceptance:
            errors.append(f"Required acceptance {aid} is not mapped to a task")
    if acc_by_id and not any(item["required"] for item in acc_by_id.values()):
        errors.append("At least one acceptance must be required")
    if not has_required:
        errors.append("At least one task must map a required acceptance")

    # Three-color DFS reports a concrete cycle while checking the DAG.
    colors, stack = {}, []

    def visit(tid):
        color = colors.get(tid, 0)
        if color == 2:
            return
        if color == 1:
            cycle = stack[stack.index(tid):] + [tid]
            errors.append("Task dependency cycle: " + " -> ".join(cycle))
            return
        colors[tid] = 1
        stack.append(tid)
        for dep in task_by_id.get(tid, {}).get("depends_on", []):
            if dep in task_by_id:
                visit(dep)
        stack.pop()
        colors[tid] = 2

    for tid in task_by_id:
        visit(tid)

    return {"valid": not errors, "errors": errors}


def require_plan(plan):
    result = validate_plan(plan)
    if not result["valid"]:
        raise ProjectError("; ".join(result["errors"]))


def file_sha256(path):
    hasher = hashlib.sha256()
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ProjectError(f"Evidence path is not a regular file: {path}")
        with os.fdopen(fd, "rb") as stream:
            fd = -1
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
    finally:
        if fd >= 0:
            os.close(fd)
    return hasher.hexdigest()


def check_evidence(item, label):
    _exact_keys(item, {"path", "sha256"}, label)
    raw_path = _string(item["path"], f"{label}.path")
    expected = item["sha256"]
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ProjectError(f"{label}.sha256 must be a 64-character SHA256 hex digest")
    try:
        resolved = Path(raw_path).expanduser().resolve(strict=True)
        if not stat.S_ISREG(resolved.stat().st_mode):
            raise ProjectError(f"{label} must name a regular local file: {raw_path}")
        actual = file_sha256(resolved)
    except OSError as exc:
        raise ProjectError(f"Cannot read evidence file {raw_path}: {exc}") from exc
    if actual != expected.lower():
        raise ProjectError(f"{label} SHA256 does not match file: {resolved}")
    return {"path": str(resolved), "sha256": expected.lower()}


def check_acceptance_results(plan, task_id, results):
    task = next(task for task in plan["tasks"] if task["id"] == task_id)
    expected_ids = task["acceptance_ids"]
    if not isinstance(results, dict) or set(results) != set(expected_ids):
        raise ProjectError(f"acceptance_results must contain exactly {sorted(expected_ids)}")
    criteria = {item["id"]: item for item in plan["acceptance"]}
    checked = {}
    for aid in expected_ids:
        result = results[aid]
        _exact_keys(result, {"status", "level", "evidence"}, f"acceptance_results.{aid}")
        if result["status"] != "pass":
            raise ProjectError(f"acceptance_results.{aid}.status must be pass")
        level = result["level"]
        if level not in LEVELS:
            raise ProjectError(f"acceptance_results.{aid}.level must be one of {sorted(LEVELS)}")
        minimum = criteria[aid]["level"]
        allowed_levels = {"static": {"static", "runtime"},
                          "runtime": {"runtime"}, "review": {"review"}}[minimum]
        if level not in allowed_levels:
            raise ProjectError(f"acceptance_results.{aid} level {level} does not satisfy required {minimum}")
        evidence = result["evidence"]
        if not isinstance(evidence, list) or not evidence:
            raise ProjectError(f"acceptance_results.{aid}.evidence must be a nonempty list")
        checked[aid] = {"status": "pass", "level": level,
                        "evidence": [check_evidence(ref, f"acceptance_results.{aid}.evidence[{i}]")
                                     for i, ref in enumerate(evidence)]}
    return checked


def _task_map(plan):
    return {item["id"]: item for item in plan["tasks"]}


def _acceptance_map(plan):
    return {item["id"]: item for item in plan["acceptance"]}


def required_task_ids(plan):
    required_acceptance = {item["id"] for item in plan["acceptance"] if item["required"]}
    return {item["id"] for item in plan["tasks"]
            if set(item["acceptance_ids"]) & required_acceptance}


def _completion_met(state):
    required_tasks = required_task_ids(state["plan"])
    for task_id in required_tasks:
        current = state["tasks"][task_id]
        if current["status"] != "done":
            return False
    required_acceptance = {item["id"] for item in state["plan"]["acceptance"] if item["required"]}
    task_map = _task_map(state["plan"])
    for aid in required_acceptance:
        mapped = [tid for tid, task in task_map.items() if aid in task["acceptance_ids"]]
        if not mapped:
            return False
        if not any(state["tasks"][tid]["status"] == "done" for tid in mapped):
            return False
    return True


def _sync_status(state):
    state["status"] = "completed" if _completion_met(state) else "active"


def init(plan, state_path, evaluation_plan=None, evaluation_source=None):
    require_plan(plan)
    evaluation_lock = (make_evaluation_lock(evaluation_plan, evaluation_source)
                       if evaluation_plan is not None else None)
    validate_runtime_mapping(plan, evaluation_lock)
    at = now()
    state = {
        "schema_version": STATE_SCHEMA,
        "created_at": at,
        "updated_at": at,
        "revision": 0,
        "status": "active",
        "plan": deepcopy(plan),
        "plan_hash": digest(plan),
        "evaluation_plan_lock": evaluation_lock,
        "tasks": {
            task["id"]: {
                "status": "todo", "attempts": [], "repair_attempts": 0,
                "active_attempt_id": None, "reason": None, "invalidations": [],
            } for task in plan["tasks"]
        },
        "revision_history": [],
    }
    validate_state(state)
    save(state_path, state, exclusive=True)
    binding = _evaluation_binding_status(state)
    return {"initialized": True, "state": str(Path(state_path).resolve()),
            "plan_hash": state["plan_hash"], "status": state["status"],
            "evaluation_plan_binding": binding}


def _validate_history_attempt(attempt, task_id, known_plan_hashes, known_eval_hashes, seen_attempt_ids):
    legacy_keys = {"attempt_id", "plan_hash", "acceptance_ids", "started_at",
                   "finished_at", "outcome", "reason", "acceptance_results"}
    current_keys = legacy_keys | {"evaluation_plan_hash"}
    if set(attempt) == legacy_keys:
        attempt["evaluation_plan_hash"] = None
    _exact_keys(attempt, current_keys, f"task {task_id} attempt")
    attempt_id = _id(attempt["attempt_id"], "attempt_id")
    if attempt_id in seen_attempt_ids:
        raise ProjectError(f"Duplicate attempt_id: {attempt_id}")
    seen_attempt_ids.add(attempt_id)
    if attempt["plan_hash"] not in known_plan_hashes:
        raise ProjectError(f"Task {task_id} attempt references unknown plan hash")
    eval_hash = attempt["evaluation_plan_hash"]
    if eval_hash is not None and eval_hash not in known_eval_hashes:
        raise ProjectError(f"Task {task_id} attempt references unknown evaluation plan hash")
    _string_list(attempt["acceptance_ids"], f"task {task_id} attempt acceptance_ids")
    _timestamp(attempt["started_at"], f"task {task_id} attempt started_at")
    outcome = attempt["outcome"]
    if outcome not in OUTCOMES:
        raise ProjectError(f"Task {task_id} attempt has invalid outcome")
    if outcome == "running":
        if attempt["finished_at"] is not None or attempt["reason"] is not None or attempt["acceptance_results"] is not None:
            raise ProjectError(f"Running task {task_id} attempt has terminal fields")
    else:
        _timestamp(attempt["finished_at"], f"task {task_id} attempt finished_at")
        if outcome in {"blocked", "failed"}:
            _string(attempt["reason"], f"task {task_id} attempt reason")
        elif attempt["reason"] is not None:
            raise ProjectError(f"Done task {task_id} attempt cannot have a reason")
        if outcome == "done":
            if not isinstance(attempt["acceptance_results"], dict):
                raise ProjectError(f"Done task {task_id} attempt has no acceptance results")
            if set(attempt["acceptance_results"]) != set(attempt["acceptance_ids"]):
                raise ProjectError(f"Historical task {task_id} acceptance results are incomplete")
            for aid, result in attempt["acceptance_results"].items():
                _exact_keys(result, {"status", "level", "evidence"}, f"historical acceptance {aid}")
                if result["status"] != "pass" or result["level"] not in LEVELS:
                    raise ProjectError(f"Historical acceptance {aid} has invalid result")
                if not isinstance(result["evidence"], list) or not result["evidence"]:
                    raise ProjectError(f"Historical acceptance {aid} has no evidence")
                for index, evidence in enumerate(result["evidence"]):
                    _exact_keys(evidence, {"path", "sha256"}, f"historical acceptance {aid} evidence[{index}]")
                    _string(evidence["path"], "historical evidence path")
                    if not isinstance(evidence["sha256"], str) or not SHA256.fullmatch(evidence["sha256"]):
                        raise ProjectError("Historical evidence sha256 is invalid")
        elif attempt["acceptance_results"] is not None:
            raise ProjectError(f"Non-done task {task_id} attempt cannot have acceptance results")


def validate_state(state):
    keys = {"schema_version", "created_at", "updated_at", "revision", "status",
            "plan", "plan_hash", "evaluation_plan_lock", "tasks", "revision_history"}
    if isinstance(state, dict) and "case_assessments" in state:
        keys.add("case_assessments")
    _exact_keys(state, keys, "state")
    if "case_assessments" in state:
        if not isinstance(state["case_assessments"], list):
            raise ProjectError("case_assessments must be a list")
        for record in state["case_assessments"]:
            _exact_keys(record, {"at", "plan_hash", "evaluation_plan_hash", "task_fingerprint", "report"}, "case assessment")
            _timestamp(record["at"], "case assessment at")
            for field in ("plan_hash", "evaluation_plan_hash", "task_fingerprint"):
                if not isinstance(record[field], str) or not SHA256.fullmatch(record[field]):
                    raise ProjectError(f"Invalid case assessment {field}")
            _exact_keys(record["report"], {"path", "sha256"}, "case assessment report")
            _string(record["report"]["path"], "case assessment report path")
            if not isinstance(record["report"]["sha256"], str) or not SHA256.fullmatch(record["report"]["sha256"]):
                raise ProjectError("Invalid case assessment report hash")
    if state["schema_version"] != STATE_SCHEMA:
        raise ProjectError(f"Unsupported state schema; expected {STATE_SCHEMA}")
    _timestamp(state["created_at"], "created_at")
    _timestamp(state["updated_at"], "updated_at")
    if type(state["revision"]) is not int or state["revision"] < 0:
        raise ProjectError("revision must be a nonnegative integer")
    require_plan(state["plan"])
    current_hash = digest(state["plan"])
    if state["plan_hash"] != current_hash:
        raise ProjectError("State plan_hash does not match embedded plan")
    current_eval_lock = state["evaluation_plan_lock"]
    validate_evaluation_lock(current_eval_lock)
    validate_runtime_mapping(state["plan"], current_eval_lock)
    if not isinstance(state["revision_history"], list):
        raise ProjectError("revision_history must be a list")
    known_hashes = {current_hash}
    known_plans = {current_hash: state["plan"]}
    known_eval_hashes = {None}
    if current_eval_lock is not None:
        known_eval_hashes.add(current_eval_lock["plan_hash"])
    for index, event in enumerate(state["revision_history"]):
        _exact_keys(event, {"at", "reason", "previous_plan", "previous_plan_hash",
                            "new_plan_hash", "explicit_invalidations", "invalidated_tasks",
                            "previous_evaluation_plan_lock", "new_evaluation_plan_lock"},
                    f"revision_history[{index}]")
        _timestamp(event["at"], f"revision_history[{index}].at")
        _string(event["reason"], f"revision_history[{index}].reason")
        require_plan(event["previous_plan"])
        validate_evaluation_lock(event["previous_evaluation_plan_lock"])
        validate_evaluation_lock(event["new_evaluation_plan_lock"])
        if digest(event["previous_plan"]) != event["previous_plan_hash"]:
            raise ProjectError(f"revision_history[{index}] previous plan hash mismatch")
        if not isinstance(event["new_plan_hash"], str) or not SHA256.fullmatch(event["new_plan_hash"]):
            raise ProjectError(f"revision_history[{index}] new plan hash is invalid")
        _string_list(event["explicit_invalidations"], f"revision_history[{index}].explicit_invalidations")
        _string_list(event["invalidated_tasks"], f"revision_history[{index}].invalidated_tasks")
        known_hashes.add(event["previous_plan_hash"])
        known_hashes.add(event["new_plan_hash"])
        known_plans[event["previous_plan_hash"]] = event["previous_plan"]
        for eval_lock in (event["previous_evaluation_plan_lock"],
                          event["new_evaluation_plan_lock"]):
            if eval_lock is not None:
                known_eval_hashes.add(eval_lock["plan_hash"])

    tasks = state["tasks"]
    expected_task_ids = set(_task_map(state["plan"]))
    if not isinstance(tasks, dict) or set(tasks) != expected_task_ids:
        raise ProjectError("State task IDs do not match embedded plan")
    seen_attempt_ids = set()
    for task_id, current in tasks.items():
        _exact_keys(current, {"status", "attempts", "repair_attempts", "active_attempt_id",
                              "reason", "invalidations"}, f"state task {task_id}")
        if current["status"] not in TASK_STATUSES:
            raise ProjectError(f"Task {task_id} has invalid status")
        if type(current["repair_attempts"]) is not int or not 0 <= current["repair_attempts"] <= 2:
            raise ProjectError(f"Task {task_id} repair_attempts must be 0..2")
        if not isinstance(current["attempts"], list):
            raise ProjectError(f"Task {task_id} attempts must be a list")
        if not isinstance(current["invalidations"], list):
            raise ProjectError(f"Task {task_id} invalidations must be a list")
        for event in current["invalidations"]:
            _exact_keys(event, {"at", "reason", "revision", "source_plan_hash"}, f"task {task_id} invalidation")
            _timestamp(event["at"], f"task {task_id} invalidation at")
            _string(event["reason"], f"task {task_id} invalidation reason")
            if type(event["revision"]) is not int or event["revision"] < 1:
                raise ProjectError(f"Task {task_id} invalidation revision is invalid")
            if event["source_plan_hash"] not in known_hashes:
                raise ProjectError(f"Task {task_id} invalidation has unknown source plan hash")
        running_ids = []
        for attempt in current["attempts"]:
            _validate_history_attempt(attempt, task_id, known_hashes, known_eval_hashes,
                                      seen_attempt_ids)
            if attempt["outcome"] == "running":
                running_ids.append(attempt["attempt_id"])
        status = current["status"]
        active = current["active_attempt_id"]
        if status == "running":
            if len(running_ids) != 1 or active != running_ids[0] or not current["attempts"] or current["attempts"][-1]["attempt_id"] != active:
                raise ProjectError(f"Task {task_id} has inconsistent running attempt")
            if current["reason"] is not None:
                raise ProjectError(f"Running task {task_id} cannot have a reason")
        else:
            if running_ids or active is not None:
                raise ProjectError(f"Non-running task {task_id} has an active attempt")
            if status == "done":
                if not current["attempts"] or current["attempts"][-1]["outcome"] != "done":
                    raise ProjectError(f"Done task {task_id} has no current done attempt")
                last = current["attempts"][-1]
                task_spec = _task_map(state["plan"])[task_id]
                prior_plan = known_plans.get(last["plan_hash"])
                current_eval_hash = (current_eval_lock["plan_hash"]
                                     if current_eval_lock is not None else None)
                if (prior_plan is None or
                        last["acceptance_ids"] != task_spec["acceptance_ids"] or
                        _task_scope(prior_plan, task_id, last["evaluation_plan_hash"]) !=
                        _task_scope(state["plan"], task_id, current_eval_hash)):
                    raise ProjectError(f"Done task {task_id} result does not match current plan")
                runtime_ids = {item["id"] for item in state["plan"]["acceptance"]
                               if item["level"] == "runtime" and
                               item["id"] in task_spec["acceptance_ids"]}
                if runtime_ids and last["evaluation_plan_hash"] != current_eval_hash:
                    raise ProjectError(f"Done runtime task {task_id} is not bound to the current evaluation plan")
                if current_eval_lock is None and last["evaluation_plan_hash"] is not None:
                    raise ProjectError(f"Done task {task_id} has an evaluation hash but state is not bound")
                normalized = check_acceptance_results(state["plan"], task_id,
                                                       last["acceptance_results"])
                if normalized != last["acceptance_results"]:
                    raise ProjectError(f"Done task {task_id} evidence is not canonical")
                if current["reason"] is not None:
                    raise ProjectError(f"Done task {task_id} cannot have a reason")
            elif status == "failed":
                if not current["attempts"] or current["attempts"][-1]["outcome"] != "failed" or current["repair_attempts"] >= 2:
                    raise ProjectError(f"Failed task {task_id} is inconsistent with its repair bound")
                if current["reason"] != current["attempts"][-1]["reason"]:
                    raise ProjectError(f"Failed task {task_id} reason does not match its attempt")
            elif status == "blocked":
                if not current["attempts"] or current["attempts"][-1]["outcome"] not in {"blocked", "failed"}:
                    raise ProjectError(f"Blocked task {task_id} has no blocking attempt")
                if current["attempts"][-1]["outcome"] == "failed" and current["repair_attempts"] < 2:
                    raise ProjectError(f"Blocked task {task_id} reached its repair bound too early")
                if current["reason"] != current["attempts"][-1]["reason"]:
                    raise ProjectError(f"Blocked task {task_id} reason does not match its attempt")
            elif current["reason"] is not None:
                raise ProjectError(f"Todo task {task_id} cannot have a reason")

    expected_status = "completed" if _completion_met(state) else "active"
    if state["status"] != expected_status:
        raise ProjectError("State project status is inconsistent with required task results")


def load_state(path):
    state = load_json(path)
    # Existing forge-project-state/1 files remain readable as unbound legacy runs.
    if isinstance(state, dict):
        state.setdefault("evaluation_plan_lock", None)
        for task in state.get("tasks", {}).values() if isinstance(state.get("tasks"), dict) else ():
            for attempt in task.get("attempts", []) if isinstance(task, dict) else ():
                if isinstance(attempt, dict):
                    attempt.setdefault("evaluation_plan_hash", None)
        for event in state.get("revision_history", []) if isinstance(state.get("revision_history"), list) else ():
            if isinstance(event, dict):
                event.setdefault("previous_evaluation_plan_lock", None)
                event.setdefault("new_evaluation_plan_lock", None)
    validate_state(state)
    return state


def _normalize_declared_path(path):
    return posixpath.normpath(path.replace("\\", "/"))


def _path_overlap(left, right):
    left = _normalize_declared_path(left)
    right = _normalize_declared_path(right)
    return (left == right or left == "." or right == "." or
            left.startswith(right.rstrip("/") + "/") or
            right.startswith(left.rstrip("/") + "/"))


def _active_write_conflicts(state, task):
    conflicts = []
    for other in state["plan"]["tasks"]:
        if other["id"] == task["id"] or state["tasks"][other["id"]]["status"] != "running":
            continue
        overlaps = [[left, right] for left in task["write_paths"]
                    for right in other["write_paths"] if _path_overlap(left, right)]
        if overlaps:
            conflicts.append({"task_id": other["id"], "overlaps": overlaps})
    return conflicts


def _ready_tasks(state):
    result = []
    tasks = _task_map(state["plan"])
    for task in state["plan"]["tasks"]:
        current = state["tasks"][task["id"]]
        if current["status"] not in {"todo", "failed"}:
            continue
        if current["status"] == "failed" and current["repair_attempts"] >= 2:
            continue
        if all(state["tasks"][dep]["status"] == "done" for dep in task["depends_on"]):
            if not _active_write_conflicts(state, task):
                result.append(task)
    return result


def _wall_seconds(state):
    then = datetime.fromisoformat(state["created_at"].replace("Z", "+00:00"))
    elapsed = (datetime.now(timezone.utc) - then).total_seconds()
    return round(max(0.0, elapsed), 3)


def _attempt_seconds(attempt):
    start = datetime.fromisoformat(attempt["started_at"].replace("Z", "+00:00"))
    end_text = attempt["finished_at"] or now()
    end = datetime.fromisoformat(end_text.replace("Z", "+00:00"))
    return max(0.0, (end - start).total_seconds())


def _evaluation_binding_status(state):
    lock = state.get("evaluation_plan_lock")
    if lock is None:
        return {"status": "not_configured", "authoritative": "none",
                "plan_id": None, "plan_hash": None, "source_path": None,
                "source_status": "not_configured"}
    source = lock["source_path"]
    source_status = "not_recorded"
    warning = None
    if source:
        try:
            source_plan = load_json(source)
            source_status = "matches" if digest(source_plan) == lock["plan_hash"] else "drifted"
        except (ProjectError, OSError, ValueError):
            source_status = "unavailable"
        if source_status != "matches":
            warning = f"External evaluation-plan source is {source_status}; the embedded state lock is authoritative."
    result = {"status": "bound", "authoritative": "embedded_state_lock",
              "plan_id": lock["plan"]["id"], "plan_hash": lock["plan_hash"],
              "source_path": source, "source_status": source_status}
    if warning:
        result["warning"] = warning
    return result


def _historical_evidence_warnings(state):
    warnings = []
    for task_id, current in state["tasks"].items():
        current_attempt_id = (current["attempts"][-1]["attempt_id"]
                              if current["status"] == "done" and current["attempts"] else None)
        for attempt in current["attempts"]:
            if attempt["outcome"] != "done" or attempt["attempt_id"] == current_attempt_id:
                continue
            for acceptance_id, result in attempt["acceptance_results"].items():
                for evidence in result["evidence"]:
                    try:
                        actual = file_sha256(evidence["path"])
                        problem = None if actual == evidence["sha256"] else "changed"
                    except FileNotFoundError:
                        problem = "missing"
                    except OSError:
                        problem = "unreadable"
                    except ProjectError:
                        problem = "not_regular_file"
                    if problem:
                        warnings.append({"task_id": task_id, "attempt_id": attempt["attempt_id"],
                                         "acceptance_id": acceptance_id, "path": evidence["path"],
                                         "status": problem, "historical": True})
    return warnings


def status(state):
    tasks = state["tasks"]
    ready = {item["id"] for item in _ready_tasks(state)}
    counts = {name: sum(current["status"] == name for current in tasks.values())
              for name in ("todo", "running", "done", "blocked", "failed")}
    blockers = []
    reconcile = []
    for task in state["plan"]["tasks"]:
        current = tasks[task["id"]]
        if current["status"] == "running":
            reconcile.append({"task_id": task["id"],
                              "attempt_id": current["active_attempt_id"],
                              "started_at": current["attempts"][-1]["started_at"]})
        elif current["status"] == "blocked":
            blockers.append({"task_id": task["id"], "status": "blocked",
                             "reason": current["reason"]})
        elif current["status"] == "failed":
            blockers.append({"task_id": task["id"], "status": "failed",
                             "reason": current["reason"],
                             "repair_attempts_used": current["repair_attempts"]})
        elif current["status"] in {"todo", "failed"} and task["id"] not in ready:
            waiting_for = [{"task_id": dep, "status": tasks[dep]["status"]}
                           for dep in task["depends_on"] if tasks[dep]["status"] != "done"]
            if waiting_for:
                blockers.append({"task_id": task["id"], "status": "waiting",
                                 "dependencies": waiting_for})
        if current["status"] in {"todo", "failed"} and task["id"] not in ready:
            conflicts = _active_write_conflicts(state, task)
            if conflicts:
                blockers.append({"task_id": task["id"], "status": "write_conflict",
                                 "conflicts_with": conflicts})
    attempt_seconds = sum(_attempt_seconds(attempt)
                          for current in tasks.values() for attempt in current["attempts"])
    assessment = product_assessment(state)
    return {
        "status": state["status"],
        "plan_id": state["plan"]["id"],
        "plan_hash": state["plan_hash"],
        "revision": state["revision"],
        "completed": counts["done"],
        "total": len(tasks),
        "required_completed": sum(tasks[task_id]["status"] == "done"
                                  for task_id in required_task_ids(state["plan"])),
        "required_total": len(required_task_ids(state["plan"])),
        "tasks": counts,
        "todo": [task["id"] for task in state["plan"]["tasks"]
                 if tasks[task["id"]]["status"] == "todo"],
        "ready": sorted(ready),
        "reconcile": reconcile,
        "blockers": blockers,
        "evaluation_plan_binding": _evaluation_binding_status(state),
        "product_acceptance_status": assessment["status"],
        "product_assessment": assessment,
        "evidence_warnings": _historical_evidence_warnings(state),
        "actual_elapsed_seconds": _wall_seconds(state),
        "recorded_attempt_seconds": round(attempt_seconds, 3),
        "tokens": None,
        "cost": None,
    }


def next_tasks(state):
    ready = _ready_tasks(state)
    reconciling = [{"task_id": task["id"],
                    "attempt_id": state["tasks"][task["id"]]["active_attempt_id"],
                    "started_at": state["tasks"][task["id"]]["attempts"][-1]["started_at"]}
                   for task in state["plan"]["tasks"] if state["tasks"][task["id"]]["status"] == "running"]
    overview = status(state)
    repairs = acceptance_repairs(state, overview["product_assessment"])
    if ready:
        result_status = "ready"
    elif reconciling:
        result_status = "reconcile"
    elif state["status"] == "completed":
        verdict = overview["product_assessment"]["status"]
        result_status = ({"pass": "completed", "not_configured": "completed",
                          "fail": "acceptance_failed", "needs_review": "needs_review"}
                         .get(verdict, "needs_acceptance"))
        if repairs and all(row["repair_budget_exhausted"] for row in repairs):
            result_status = "blocked"
    elif overview["blockers"]:
        result_status = "blocked"
    else:
        result_status = "waiting"
    return {
        "status": result_status,
        "plan_hash": state["plan_hash"],
        "ready": [{
            "task_id": task["id"], "title": task["title"],
            "depends_on": list(task["depends_on"]), "owner": task["owner"],
            "write_paths": list(task["write_paths"]),
            "acceptance_ids": list(task["acceptance_ids"]),
            "repair_attempt": state["tasks"][task["id"]]["repair_attempts"] + 1
                              if state["tasks"][task["id"]]["status"] == "failed" else None,
        } for task in ready],
        "reconcile": reconciling,
        "blockers": overview["blockers"],
        "completed": overview["completed"],
        "total": overview["total"],
        "product_acceptance_status": overview["product_acceptance_status"],
        "acceptance_repairs": repairs,
    }


def task_fingerprint(state):
    return digest({tid: {"status": item["status"],
                         "attempt_ids": [attempt["attempt_id"] for attempt in item["attempts"]],
                         "invalidations": item["invalidations"]}
                   for tid, item in state["tasks"].items()})


def product_assessment(state):
    lock = state.get("evaluation_plan_lock")
    if lock is None:
        return {"status": "not_configured"}
    records = state.get("case_assessments", [])
    if not records:
        return {"status": "not_assessed"}
    record = records[-1]
    if (record["plan_hash"] != state["plan_hash"] or
            record["evaluation_plan_hash"] != lock["plan_hash"] or
            record["task_fingerprint"] != task_fingerprint(state)):
        return {"status": "stale", "reason": "Plan or task attempts changed; rerun acceptance"}
    try:
        import caserunner
        checked = check_evidence(record["report"], "case report")
        result = caserunner.grade(lock["plan"], load_json(checked["path"]))
        if result["status"] == "pass" and not _completion_met(state):
            result = dict(result, status="pending_tasks")
        return result
    except (ProjectError, OSError, ValueError, TypeError, KeyError) as exc:
        return {"status": "unverified", "reason": str(exc)}


def assess_cases(state, report_path):
    import caserunner
    lock = state.get("evaluation_plan_lock")
    if lock is None:
        raise ProjectError("Case assessment requires a bound full evaluation plan")
    reference = {"path": str(Path(report_path).resolve()), "sha256": file_sha256(report_path)}
    caserunner.grade(lock["plan"], load_json(report_path))
    state.setdefault("case_assessments", []).append({
        "at": now(), "plan_hash": state["plan_hash"],
        "evaluation_plan_hash": lock["plan_hash"],
        "task_fingerprint": task_fingerprint(state), "report": reference})
    state["revision"] += 1
    state["updated_at"] = now()
    validate_state(state)
    return product_assessment(state)


def acceptance_repairs(state, assessment):
    failures = [row for row in assessment.get("cases", [])
                if row["required"] and row["status"] == "fail"]
    repairs = []
    for row in failures:
        ids = [task["id"] for task in state["plan"]["tasks"]
               if set(task["acceptance_ids"]) & set(row["criteria"])]
        remaining = {tid: max(0, 2 - state["tasks"][tid]["repair_attempts"]) for tid in ids}
        exhausted = bool(ids) and not any(remaining.values())
        action = ("Repair budget exhausted; preserve unresolved failure and deliver candidate with needed evidence"
                  if exhausted else
                  "Preserve candidate and logs; reopen an affected done task, repair, rerun in a new directory")
        repairs.append({"case_id": row["id"], "reason": row["reason"], "task_ids": ids,
                        "repair_attempts_remaining": remaining,
                        "repair_budget_exhausted": exhausted, "next_action": action})
    return repairs


def reopen(state, task_id, reason):
    """Reopen observed failed acceptance without changing frozen requirements."""
    _string(reason, "reason")
    assessment = product_assessment(state)
    implicated = {tid for row in acceptance_repairs(state, assessment) for tid in row["task_ids"]}
    if task_id not in implicated or state["tasks"][task_id]["status"] != "done":
        raise ProjectError("Reopen requires a done task mapped to current failed required cases")
    current = state["tasks"][task_id]
    if current["repair_attempts"] >= 2:
        raise ProjectError("Task exhausted its two repair attempts; preserve unresolved acceptance failure")
    affected = {task_id}
    while True:
        expanded = affected | {task["id"] for task in state["plan"]["tasks"]
                               if set(task["depends_on"]) & affected}
        if expanded == affected:
            break
        affected = expanded
    if any(state["tasks"][tid]["status"] == "running" for tid in affected):
        raise ProjectError("Reconcile active dependent attempts before reopen")
    at = now()
    revision = state["revision"] + 1
    for tid in affected:
        item = state["tasks"][tid]
        item["invalidations"].append({"at": at, "reason": reason, "revision": revision,
                                      "source_plan_hash": state["plan_hash"]})
        if item["status"] == "done":
            item.update(status="todo", active_attempt_id=None, reason=None)
    current["repair_attempts"] += 1
    state["revision"] = revision
    state["updated_at"] = at
    _sync_status(state)
    validate_state(state)
    return {"status": "ready", "reopened_task": task_id, "invalidated_tasks": sorted(affected),
            "repair_attempts_used": current["repair_attempts"]}


def begin(state, task_id):
    _id(task_id, "task_id")
    tasks = _task_map(state["plan"])
    if task_id not in tasks:
        raise ProjectError(f"Unknown task: {task_id}")
    spec = tasks[task_id]
    current = state["tasks"][task_id]
    if current["status"] == "blocked" and current["repair_attempts"] >= 2:
        raise ProjectError(f"Task {task_id} exhausted its two repair attempts and is blocked")
    if current["status"] not in {"todo", "failed"}:
        if current["status"] == "running":
            raise ProjectError(f"Task {task_id} is already running; reconcile attempt {current['active_attempt_id']}")
        raise ProjectError(f"Task {task_id} cannot begin from status {current['status']}")
    if current["status"] == "failed" and current["repair_attempts"] >= 2:
        raise ProjectError(f"Task {task_id} exhausted its two repair attempts and is blocked")
    unfinished = [dep for dep in spec["depends_on"] if state["tasks"][dep]["status"] != "done"]
    if unfinished:
        raise ProjectError(f"Task {task_id} dependencies are not done: {unfinished}")
    conflicts = _active_write_conflicts(state, spec)
    if conflicts:
        raise ProjectError(f"Task {task_id} has active write-path conflicts: {conflicts}")
    if current["status"] == "failed":
        current["repair_attempts"] += 1
    attempt_id = uuid.uuid4().hex
    started = now()
    attempt = {
        "attempt_id": attempt_id,
        "plan_hash": state["plan_hash"],
        "evaluation_plan_hash": (state["evaluation_plan_lock"]["plan_hash"]
                                  if state.get("evaluation_plan_lock") is not None else None),
        "acceptance_ids": list(spec["acceptance_ids"]),
        "started_at": started,
        "finished_at": None,
        "outcome": "running",
        "reason": None,
        "acceptance_results": None,
    }
    current["attempts"].append(attempt)
    current.update(status="running", active_attempt_id=attempt_id, reason=None)
    state["revision"] += 1
    state["updated_at"] = started
    _sync_status(state)
    validate_state(state)
    return {"task_id": task_id, "attempt_id": attempt_id, "started_at": started,
            "plan_hash": state["plan_hash"],
            "evaluation_plan_hash": attempt["evaluation_plan_hash"],
            "revision": state["revision"]}


def finish(state, task_id, attempt_id, outcome, results=None, reason=None):
    if outcome not in {"done", "blocked", "failed"}:
        raise ProjectError("outcome must be done, blocked, or failed")
    task_id = _id(task_id, "task_id")
    attempt_id = _id(attempt_id, "attempt_id")
    if task_id not in state["tasks"]:
        raise ProjectError(f"Unknown task: {task_id}")
    current = state["tasks"][task_id]
    if current["status"] != "running" or current["active_attempt_id"] != attempt_id:
        raise ProjectError(f"Stale or duplicate response for task {task_id}; active attempt does not match")
    attempt = current["attempts"][-1]
    if outcome == "done":
        if reason is not None:
            raise ProjectError("reason is allowed only for blocked or failed outcomes")
        if results is None:
            raise ProjectError("done requires --results with actual acceptance evidence")
        lock = state.get("evaluation_plan_lock")
        expected_keys = ({"acceptance_results", "evaluation_plan_hash"}
                         if lock is not None else {"acceptance_results"})
        if not isinstance(results, dict) or set(results) != expected_keys:
            raise ProjectError(f"results file must contain exactly {sorted(expected_keys)}")
        if lock is not None and results["evaluation_plan_hash"] != lock["plan_hash"]:
            raise ProjectError("results evaluation_plan_hash does not match the authoritative state lock")
        expected_eval_hash = lock["plan_hash"] if lock is not None else None
        if attempt["evaluation_plan_hash"] != expected_eval_hash:
            raise ProjectError("Active attempt is stale for the current evaluation-plan binding")
        checked = check_acceptance_results(state["plan"], task_id, results["acceptance_results"])
        attempt["acceptance_results"] = checked
        attempt["reason"] = None
    else:
        if results is not None:
            raise ProjectError("blocked/failed outcomes cannot include --results")
        _string(reason, "reason")
        attempt["reason"] = reason
        attempt["acceptance_results"] = None
    ended = now()
    attempt["finished_at"] = ended
    attempt["outcome"] = outcome
    current["active_attempt_id"] = None
    current["reason"] = reason if outcome != "done" else None
    if outcome == "done":
        current["status"] = "done"
    elif outcome == "blocked":
        current["status"] = "blocked"
    elif current["repair_attempts"] >= 2:
        current["status"] = "blocked"
        current["reason"] = reason + " (repair limit reached)"
        attempt["reason"] = current["reason"]
    else:
        current["status"] = "failed"
    state["revision"] += 1
    state["updated_at"] = ended
    _sync_status(state)
    validate_state(state)
    return {"task_id": task_id, "attempt_id": attempt_id, "outcome": outcome,
            "task_status": current["status"], "reason": current["reason"],
            "status": state["status"], "revision": state["revision"],
            "plan_hash": state["plan_hash"],
            "evaluation_plan_hash": (state["evaluation_plan_lock"]["plan_hash"]
                                      if state.get("evaluation_plan_lock") is not None else None)}


def _descendants(plan):
    reverse = {item["id"]: set() for item in plan["tasks"]}
    for task in plan["tasks"]:
        for dep in task["depends_on"]:
            if dep in reverse:
                reverse[dep].add(task["id"])
    return reverse


def _cascade(roots, plans):
    affected = set(roots)
    queue = list(roots)
    maps = [_descendants(plan) for plan in plans]
    while queue:
        node = queue.pop()
        for reverse in maps:
            for child in reverse.get(node, ()):
                if child not in affected:
                    affected.add(child)
                    queue.append(child)
    return affected


def _revision_roots(old, new):
    old_tasks, new_tasks = _task_map(old), _task_map(new)
    roots = {tid for tid in new_tasks if tid not in old_tasks or old_tasks[tid] != new_tasks[tid]}
    old_acc, new_acc = _acceptance_map(old), _acceptance_map(new)
    changed_acc = {aid for aid in new_acc if aid not in old_acc or old_acc[aid] != new_acc[aid]}
    for aid in changed_acc:
        roots.update(tid for tid, task in old_tasks.items() if aid in task["acceptance_ids"])
        roots.update(tid for tid, task in new_tasks.items() if aid in task["acceptance_ids"])
    old_req = {item["id"]: item for item in old["requirements"]}
    new_req = {item["id"]: item for item in new["requirements"]}
    for rid in set(old_req) | set(new_req):
        if rid not in old_req or rid not in new_req or old_req[rid] != new_req[rid]:
            affected_ids = set(old_req.get(rid, {}).get("acceptance_ids", [])) | set(new_req.get(rid, {}).get("acceptance_ids", []))
            roots.update(tid for tid, task in old_tasks.items()
                         if set(task["acceptance_ids"]) & affected_ids)
            roots.update(tid for tid, task in new_tasks.items()
                         if set(task["acceptance_ids"]) & affected_ids)
    global_fields = ("goal", "deliverable_kind", "defaults", "unknowns")
    if any(old.get(key) != new.get(key) for key in global_fields):
        roots.update(old_tasks)
    return roots


def _task_scope(plan, task_id, evaluation_plan_hash=None, memo=None):
    """Fingerprint the task's relevant plan content and all dependency scopes."""
    memo = {} if memo is None else memo
    if task_id in memo:
        return memo[task_id]
    tasks = _task_map(plan)
    task = tasks[task_id]
    acceptance_ids = set(task["acceptance_ids"])
    material = {
        "goal": plan["goal"], "deliverable_kind": plan["deliverable_kind"],
        "defaults": plan.get("defaults"), "unknowns": plan.get("unknowns"),
        "task": task,
        "acceptance": [item for item in plan["acceptance"] if item["id"] in acceptance_ids],
        "requirements": [item for item in plan["requirements"]
                         if set(item["acceptance_ids"]) & acceptance_ids],
        "dependencies": {dep: _task_scope(plan, dep, evaluation_plan_hash, memo)
                          for dep in task["depends_on"]},
    }
    if any(item["id"] in acceptance_ids and item["level"] == "runtime"
           for item in plan["acceptance"]):
        material["evaluation_plan_hash"] = evaluation_plan_hash
    memo[task_id] = digest(material)
    return memo[task_id]


def revise(state, new_plan, invalidate_ids, reason, evaluation_plan=None, evaluation_source=None):
    require_plan(new_plan)
    old_eval_lock = state.get("evaluation_plan_lock")
    if evaluation_plan is None:
        new_eval_lock = old_eval_lock
    else:
        candidate_lock = make_evaluation_lock(evaluation_plan, evaluation_source)
        new_eval_lock = (candidate_lock if old_eval_lock is None or
                         candidate_lock["plan_hash"] != old_eval_lock["plan_hash"]
                         else old_eval_lock)
    validate_runtime_mapping(new_plan, new_eval_lock)
    old_eval_hash = old_eval_lock["plan_hash"] if old_eval_lock is not None else None
    new_eval_hash = new_eval_lock["plan_hash"] if new_eval_lock is not None else None
    evaluation_changed = old_eval_hash != new_eval_hash
    if new_plan["id"] != state["plan"]["id"]:
        raise ProjectError("revise cannot change plan id")
    if any(item["status"] == "running" for item in state["tasks"].values()):
        raise ProjectError("Cannot revise while tasks are running; reconcile every active attempt first")
    old_requirement_ids = {item["id"] for item in state["plan"]["requirements"]}
    new_requirement_ids = {item["id"] for item in new_plan["requirements"]}
    if not old_requirement_ids <= new_requirement_ids:
        raise ProjectError("revise cannot remove requirement IDs")
    old_acceptance_ids = {item["id"] for item in state["plan"]["acceptance"]}
    new_acceptance_ids = {item["id"] for item in new_plan["acceptance"]}
    if not old_acceptance_ids <= new_acceptance_ids:
        raise ProjectError("revise cannot remove acceptance IDs")
    old_task_ids = set(state["tasks"])
    new_task_ids = {item["id"] for item in new_plan["tasks"]}
    if not old_task_ids <= new_task_ids:
        raise ProjectError("revise cannot remove task IDs")
    old = state["plan"]
    old_acc, new_acc = _acceptance_map(old), _acceptance_map(new_plan)
    for aid, prior in old_acc.items():
        updated = new_acc[aid]
        if prior["required"] and not updated["required"]:
            raise ProjectError(f"revise cannot weaken required acceptance {aid}")
        if prior["level"] == "runtime" and updated["level"] != "runtime":
            raise ProjectError(f"revise cannot remove the runtime requirement for {aid}")

    new_hash = digest(new_plan)
    supplied = list(dict.fromkeys(invalidate_ids))
    for task_id in supplied:
        _id(task_id, "invalidate task id")
        if task_id not in old_task_ids:
            raise ProjectError(f"Cannot invalidate unknown task: {task_id}")
    reason = _string(reason, "revision reason")
    if new_hash == state["plan_hash"] and not evaluation_changed and supplied:
        raise ProjectError("Cannot reset attempts through a no-content revision")
    if new_hash == state["plan_hash"] and not evaluation_changed:
        return {"revised": False, "reason": "Plan content is unchanged",
                "plan_hash": state["plan_hash"], "invalidated_tasks": []}

    roots = _revision_roots(old, new_plan) | set(supplied)
    if evaluation_changed:
        runtime_ids = {item["id"] for plan in (old, new_plan) for item in plan["acceptance"]
                       if item["level"] == "runtime"}
        roots.update(task["id"] for plan in (old, new_plan) for task in plan["tasks"]
                     if set(task["acceptance_ids"]) & runtime_ids)
    affected = _cascade(roots, [old, new_plan])
    unchanged_scope_manual = [task_id for task_id in supplied
                              if _task_scope(old, task_id, old_eval_hash) ==
                              _task_scope(new_plan, task_id, new_eval_hash)]
    if unchanged_scope_manual:
        raise ProjectError("Explicit invalidation requires changed task or dependency scope: "
                           + ", ".join(sorted(unchanged_scope_manual)))
    completed_affected = sorted(task_id for task_id in affected
                                if task_id in state["tasks"] and
                                state["tasks"][task_id]["status"] == "done")
    missing_explicit = sorted(set(completed_affected) - set(supplied))
    if missing_explicit:
        raise ProjectError("Completed affected tasks require explicit --invalidate entries: "
                           + ", ".join(missing_explicit))
    revised_at = now()
    next_revision = state["revision"] + 1
    old_scopes = {task_id: _task_scope(old, task_id, old_eval_hash) for task_id in old_task_ids}
    new_scopes = {task_id: _task_scope(new_plan, task_id, new_eval_hash) for task_id in new_task_ids}
    for task_id in sorted(new_task_ids - old_task_ids):
        state["tasks"][task_id] = {
            "status": "todo", "attempts": [], "repair_attempts": 0,
            "active_attempt_id": None, "reason": None, "invalidations": [],
        }
    for task_id in sorted(affected):
        current = state["tasks"][task_id]
        scope_changed = task_id not in old_scopes or old_scopes[task_id] != new_scopes[task_id]
        current["invalidations"].append({
            "at": revised_at, "reason": reason, "revision": next_revision,
            "source_plan_hash": new_hash,
        })
        if scope_changed:
            current.update(status="todo", repair_attempts=0,
                           active_attempt_id=None, reason=None)
        elif current["status"] == "done":
            current.update(status="todo", active_attempt_id=None, reason=None)
        # An unchanged blocked/failed task keeps its prior repair budget and blocker.
    event = {
        "at": revised_at,
        "reason": reason,
        "previous_plan": deepcopy(old),
        "previous_plan_hash": state["plan_hash"],
        "new_plan_hash": new_hash,
        "previous_evaluation_plan_lock": deepcopy(old_eval_lock),
        "new_evaluation_plan_lock": deepcopy(new_eval_lock),
        "explicit_invalidations": supplied,
        "invalidated_tasks": sorted(affected),
    }
    state["revision_history"].append(event)
    state["plan"] = deepcopy(new_plan)
    state["plan_hash"] = new_hash
    state["evaluation_plan_lock"] = deepcopy(new_eval_lock)
    state["revision"] = next_revision
    state["updated_at"] = revised_at
    _sync_status(state)
    validate_state(state)
    return {"revised": True, "plan_hash": new_hash,
            "revision": state["revision"], "status": state["status"],
            "invalidated_tasks": sorted(affected),
            "historical_plan_hash": event["previous_plan_hash"],
            "evaluation_plan_hash": new_eval_hash}


def _print_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="structurally validate a plan")
    validate_parser.add_argument("plan")

    init_parser = sub.add_parser("init", help="create a persistent project state")
    init_parser.add_argument("plan")
    init_parser.add_argument("--state", required=True)
    init_parser.add_argument("--evaluation-plan", help="complete forge-eval/1 plan to bind as authoritative")

    status_parser = sub.add_parser("status", help="report machine-readable progress and blockers")
    status_parser.add_argument("--state", required=True)

    next_parser = sub.add_parser("next", help="list ready tasks and active attempts to reconcile")
    next_parser.add_argument("--state", required=True)

    assess_parser = sub.add_parser("assess", help="regrade and attach a real program-mode case run")
    assess_parser.add_argument("--state", required=True)
    assess_parser.add_argument("--report", required=True)

    reopen_parser = sub.add_parser("reopen", help="reopen a done task after observed required-case failure")
    reopen_parser.add_argument("--state", required=True)
    reopen_parser.add_argument("--task", required=True)
    reopen_parser.add_argument("--reason", required=True)

    begin_parser = sub.add_parser("begin", help="record a real host task attempt")
    begin_parser.add_argument("--state", required=True)
    begin_parser.add_argument("--task", required=True)

    finish_parser = sub.add_parser("finish", help="record a task result from the host")
    finish_parser.add_argument("--state", required=True)
    finish_parser.add_argument("--task", required=True)
    finish_parser.add_argument("--attempt-id", required=True)
    finish_parser.add_argument("--outcome", choices=("done", "blocked", "failed"), required=True)
    finish_parser.add_argument("--results", help="JSON with acceptance_results; when bound, also evaluation_plan_hash")
    finish_parser.add_argument("--reason", help="required for blocked or failed")

    revise_parser = sub.add_parser("revise", help="revise a plan while preserving task history")
    revise_parser.add_argument("plan")
    revise_parser.add_argument("--state", required=True)
    revise_parser.add_argument("--evaluation-plan", help="replace the full forge-eval/1 binding in a revision")
    revise_parser.add_argument("--invalidate", action="append", default=[], metavar="TASK_ID",
                               help="explicitly invalidate a completed affected task; repeat as needed")
    revise_parser.add_argument("--reason", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            result = validate_plan(load_json(args.plan))
        elif args.command == "init":
            evaluation = load_json(args.evaluation_plan) if args.evaluation_plan else None
            source = args.evaluation_plan if args.evaluation_plan else None
            result = init(load_json(args.plan), args.state, evaluation, source)
        elif args.command == "status":
            result = status(load_state(args.state))
        elif args.command == "next":
            result = next_tasks(load_state(args.state))
        elif args.command == "assess":
            state = load_state(args.state)
            result = assess_cases(state, args.report)
            save(args.state, state)
        elif args.command == "reopen":
            state = load_state(args.state)
            result = reopen(state, args.task, args.reason)
            save(args.state, state)
        elif args.command == "begin":
            state = load_state(args.state)
            result = begin(state, args.task)
            save(args.state, state)
        elif args.command == "finish":
            state = load_state(args.state)
            results = load_json(args.results) if args.results else None
            result = finish(state, args.task, args.attempt_id, args.outcome,
                            results=results, reason=args.reason)
            save(args.state, state)
        else:
            state = load_state(args.state)
            evaluation = load_json(args.evaluation_plan) if args.evaluation_plan else None
            source = args.evaluation_plan if args.evaluation_plan else None
            result = revise(state, load_json(args.plan), args.invalidate, args.reason,
                            evaluation_plan=evaluation, evaluation_source=source)
            if result["revised"]:
                save(args.state, state)
        _print_json(result)
        if result.get("valid") is False or result.get("status") in {"blocked", "failed", "fail", "unverified", "needs_review", "acceptance_failed"}:
            return 2
        return 0
    except (ProjectError, FileExistsError, OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
