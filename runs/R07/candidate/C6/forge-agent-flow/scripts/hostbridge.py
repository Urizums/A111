#!/usr/bin/env python3
"""Host-driven worker bridge. It imports actual receipts; it never calls a model.

POSIX, one cooperating coordinator per checkpoint. JSON journal recovery covers
local checkpoint/ledger/control writes, not external tool side effects.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid

import flowctl
import packagectl
import projectctl
import runledger

SCHEMA = "forge-host-bridge/1"
PHASE_LEDGER = {"prepared": {"none"}, "dispatching": {"none"}, "accepted": {"requested"},
                "running": {"running"}, "received": {"completed"}, "committed": {"completed"},
                "terminated": {"failed", "interrupted"}, "rejected": {"failed"}}


class BridgeError(ValueError):
    pass


def body(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def digest(value):
    return projectctl.digest(value)


def sha(path):
    return runledger.file_sha256(path)


def existing_sha(path):
    return sha(path) if Path(path).exists() else None


def read(path):
    return projectctl.load_json(path)


def save(path, value):
    runledger.save(path, value)
    # Flush directory entries as well as the file on supported POSIX systems.
    fd = os.open(str(Path(path).parent), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def need(condition, message):
    if not condition:
        raise BridgeError(message)


def has_io_cause(error):
    """Preserve IO uncertainty through controller/ledger ValueError wrappers."""
    seen = set()
    while error is not None and id(error) not in seen:
        if isinstance(error, OSError):
            return True
        seen.add(id(error))
        error = error.__cause__ or error.__context__
    return False


def reference(path):
    p = Path(path).resolve(strict=True)
    return {"path": str(p), "sha256": sha(p)}


def check_refs(refs):
    for ref in refs:
        if ref["sha256"] is None:
            need(not Path(ref["path"]).exists(), "Declared absent input appeared; use a new input binding")
        else:
            runledger.evidence_ref(ref["path"], ref["sha256"], "bridge evidence")


@contextmanager
def checkpoint_lock(target):
    # Direct projectctl/packagectl writers do not take this lock. They must not
    # race this bridge; current-hash checks detect observed conflicting changes.
    path = Path(str(Path(target).resolve()) + ".hostbridge.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def recover(job):
    pending = job / "pending.json"
    if not pending.exists():
        return
    tx = read(pending)
    need(tx.get("schema_version") == "forge-host-transaction/1", "Invalid transaction schema")
    target = Path(tx["target"]).resolve()
    allowed = {target, Path(str(target) + ".hostbridge-reservation.json")}
    allowed.update(job / name for name in ["control.json", "request.json", "ledger.json"])
    target_images = [item["after_sha256"] for item in tx["changes"] if Path(item["path"]).resolve() == target]
    need(existing_sha(target) in {tx["target_before_sha256"], *target_images},
         "Checkpoint changed outside transaction; reconcile current owner")
    # Older transaction journals did not include package_ref in guards. The
    # existing immutable control binding must still gate every recovery write.
    if (job / "control.json").exists():
        package_ref = read(job / "control.json").get("package_ref")
        if package_ref:
            check_refs([package_ref])
    check_refs(tx["guards"])
    for item in tx["changes"]:
        path = Path(item["path"]).resolve()
        need(path in allowed, "Transaction destination outside bridge metadata/checkpoint")
        need(hashlib.sha256(body(item["value"])).hexdigest() == item["after_sha256"], "Transaction image drifted")
        need(existing_sha(path) in {item["before_sha256"], item["after_sha256"]},
             "Checkpoint/metadata changed outside transaction; reconcile, do not overwrite")
    for item in tx["changes"]:
        if existing_sha(item["path"]) != item["after_sha256"]:
            save(item["path"], item["value"])
    pending.unlink()
    fd = os.open(str(job), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def transaction(job, target, images, guards=(), expected_target_sha=None):
    need(not (job / "pending.json").exists(), "Pending transaction must be reconciled first")
    expected_target_sha = expected_target_sha or read(job / "control.json")["target_sha256"]
    need(sha(target) == expected_target_sha, "Checkpoint compare-and-set failed; do not overwrite")
    guards = list(guards)
    # Package bytes must be checked before journal recovery writes any image.
    # Legacy jobs keep their package reference outside refs, so include it here.
    if (job / "control.json").exists():
        package_ref = read(job / "control.json").get("package_ref")
        if package_ref and package_ref not in guards:
            guards.append(package_ref)
    tx = {"schema_version": "forge-host-transaction/1", "target": str(target),
          "target_before_sha256": expected_target_sha,
          "guards": list(guards), "changes": []}
    for path, value in images:
        tx["changes"].append({"path": str(path), "before_sha256": existing_sha(path),
                              "after_sha256": hashlib.sha256(body(value)).hexdigest(), "value": value})
    save(job / "pending.json", tx)
    recover(job)


def capture(job, source):
    ref = reference(source)
    fd = os.open(source, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(fd, "rb") as stream:
        need(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "Capture source is not a regular file")
        data = stream.read()
    need(hashlib.sha256(data).hexdigest() == ref["sha256"], "Capture source changed while reading")
    # Canonical receipt copies are private to the coordinator's metadata area.
    out = job / "receipts" / (ref["sha256"] + ".json")
    out.parent.mkdir(exist_ok=True)
    if out.exists():
        need(sha(out) == ref["sha256"], "Receipt identity conflict")
    else:
        fd, name = tempfile.mkstemp(prefix="capture-", dir=out.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.replace(name, out)
            fd = os.open(str(out.parent), os.O_RDONLY)
            try: os.fsync(fd)
            finally: os.close(fd)
        finally:
            if os.path.exists(name): os.unlink(name)
    return reference(out)


def control(job):
    recover(job)
    return checked_control(job)


def checked_control(job):
    """Validate settled bridge bytes without replaying or writing a journal."""
    need(not (job / 'pending.json').exists(), 'Pending bridge transaction needs explicit recovery')
    c = read(job / "control.json")
    need(c.get("schema_version") == SCHEMA, "Unsupported bridge control schema")
    envelope = read(job / "request.json")
    need(envelope["request_hash"] == digest(envelope["request"]) == c["request_hash"], "Request binding drifted")
    need(c["request"] == envelope["request"], "Stored request changed")
    check_refs(c["refs"])
    need(sha(c["target"]) == c["target_sha256"], "Checkpoint moved; reconcile current owner before reuse/submit")
    if c["package_ref"]:
        check_refs([c["package_ref"]])
    recorded = runledger.status(job / "ledger.json", job_id=c["request"]["job_id"], input_hash=c["request_hash"])
    need(recorded["evidence_valid"] and recorded["state"] in PHASE_LEDGER[c["phase"]],
         "Ledger evidence or phase contradicts bridge control; reconcile")
    if c["phase"] not in {"prepared", "dispatching"}:
        need(recorded["attempt_id"] == c["request"]["attempt_id"], "Ledger attempt identity changed")
    return c


def context(job):
    job = Path(job).resolve()
    meta = read(job / ("pending.json" if (job / "pending.json").exists() else "control.json"))
    return job, meta["target"]


def view(c):
    phase = c["phase"]
    actions = {"prepared": "issue_once", "dispatching": "reconcile_host_before_any_retry",
               "accepted": "query_own_worker", "running": "query_own_worker",
               "received": "coordinator_verify_then_commit", "committed": "reuse_record",
               "terminated": "reconcile_effects_before_new_project_attempt",
               "rejected": "inspect_creation_error_before_bounded_retry"}
    decision = (c.get("commit") or {}).get("coordinator_outcome")
    if phase == "committed" and (decision in {"failed", "blocked"} or
                                 c["commit"].get("worker_task_outcome") == "failed"):
        actions[phase] = "reconcile_effects_before_new_" + c["request"]["kind"] + "_attempt"
    return {"phase": phase, "job_id": c["request"]["job_id"], "attempt_id": c["request"]["attempt_id"],
            "request_hash": c["request_hash"], "action": actions[phase],
            "worker": c.get("worker"), "commit": c.get("commit"),
            "coordinator_outcome": decision,
            "automatic_host_call": False, "internal_model_identity_verified": False,
            "tokens": None, "cost": None}


def prepare(kind, state_path, work_path, job_path, task=None, package_path=None, parent="/root"):
    state_path = Path(state_path).resolve(strict=True)
    job = Path(job_path).resolve()
    job.mkdir(parents=True, exist_ok=True)
    work = read(work_path)
    required = {"prompt", "inputs", "write_paths", "reply_path"}
    need(isinstance(work, dict) and required <= set(work) <= required | {"input_files"},
         "Work needs prompt, inputs, write_paths, reply_path; optional input_files bind referenced source bytes/absence")
    input_files = work.get("input_files", [])
    need(isinstance(input_files, list), "input_files must be a reference list")
    for ref in input_files:
        need(isinstance(ref, dict) and set(ref) == {"path", "sha256"} and Path(ref["path"]).is_absolute(),
             "Input reference needs absolute path and sha256, or null for declared absence")
    check_refs(input_files)
    need(isinstance(work["prompt"], str) and work["prompt"].strip(), "Work prompt is empty")
    need(isinstance(work["write_paths"], list) and bool(work["write_paths"]), "Write scopes required")
    need(re.fullmatch(r"/[a-z0-9_]+(?:/[a-z0-9_]+)*", parent) is not None, "Invalid host parent task path")
    scopes = [Path(p).resolve() for p in work["write_paths"]]
    package_path = Path(package_path).resolve(strict=True) if package_path else None
    for scope in scopes:
        need(not job.is_relative_to(scope) and not state_path.is_relative_to(scope), "Worker scope includes coordinator metadata/checkpoint")
        need(package_path is None or not package_path.is_relative_to(scope), "Worker scope includes read-only package")
        need(not any(Path(ref["path"]).resolve().is_relative_to(scope) for ref in input_files),
             "Worker write scope includes a read-only input")
    reply_path = Path(work["reply_path"]).resolve()
    need(any(reply_path.is_relative_to(p) for p in scopes), "Reply path outside assigned write scope")
    work = {**work, "input_files": input_files, "write_paths": [str(p) for p in scopes], "reply_path": str(reply_path)}
    signature = digest({"kind": kind, "target": str(state_path), "task": task,
                        "package": reference(package_path) if package_path else None,
                        "work": work, "parent": parent})
    with checkpoint_lock(state_path):
        recover(job)
        if (job / "control.json").exists():
            c = control(job)
            need(c["signature"] == signature, "Job inputs changed; use a new job and a new eligible target attempt")
            return {**view(c), "request_path": str(job / "request.json"), "reused": True}
        reservation = Path(str(state_path) + ".hostbridge-reservation.json")
        repairs = 0
        if reservation.exists():
            prior = Path(read(reservation)["job_dir"])
            need((prior / "control.json").exists() and not (prior / "pending.json").exists(),
                 "Another prepared transaction owns this checkpoint; reconcile it first")
            old = read(prior / "control.json")
            need(old["phase"] in {"committed", "terminated", "rejected"}, "Checkpoint already has an unresolved host job")
            need(not any(Path(ref["path"]).resolve().is_relative_to(scope)
                         for ref in old["refs"] for scope in scopes),
                 "New worker scope could overwrite retained previous evidence; choose fresh output paths")
            prior_commit = old.get("commit") or {}
            if (old["phase"] in {"terminated", "rejected"} or prior_commit.get("worker_task_outcome") == "failed"
                    or prior_commit.get("coordinator_outcome") in {"failed", "blocked"}):
                repairs = old.get("repair_attempts", 0) + 1
                need(repairs <= 2, "Checkpoint host retry budget exhausted; inspect retained attempts")
        state = projectctl.load_state(state_path) if kind == "project" else read(state_path)
        original_sha = sha(state_path)
        if kind == "project":
            need(package_path is None and task is not None, "Project requires --task and no --package")
            projectctl.validate_state(state)
            started = projectctl.begin(state, task)
            invocation = started["attempt_id"]
            binding = {"task_id": task, "plan_hash": state["plan_hash"],
                       "evaluation_plan_hash": started["evaluation_plan_hash"]}
            dispatch = next(t for t in state["plan"]["tasks"] if t["id"] == task)
            declared = [(state_path.parent / p).resolve() for p in dispatch["write_paths"]]
            need(all(any(scope.is_relative_to(p) for p in declared) for scope in scopes),
                 "Work write paths exceed the task's declared project scope")
        else:
            need(package_path is not None and task is None, "Package requires --package and no --task")
            dispatch = packagectl.pending(read(package_path), state)
            need(dispatch["status"] == "ready", "Package node is not ready")
            settings = dispatch["execution_settings"]
            need(settings["model"] in {"host_default", "gpt-6-luna"},
                 "Current Luna adapter cannot honor this package's explicit model binding")
            if settings["write_scope"]:
                need(all(Path(p).is_absolute() for p in settings["write_scope"]),
                     "Relative package write scope needs an explicit host root mapping; not supplied by this adapter")
                declared = [Path(p).resolve() for p in settings["write_scope"]]
                need(all(any(scope.is_relative_to(p) for p in declared) for scope in scopes),
                     "Work write paths exceed package's configured scope")
            invocation = dispatch["invocation_id"]
            binding = {"node": dispatch["node"], "package_hash": state["package_hash"],
                       "plan_hash": state.get("plan_hash"), "input_hash": state.get("input_hash")}
        attempt = uuid.uuid4().hex if kind == "package" else invocation
        name = "luna_forge_" + attempt[:12]
        reply_contract = {"result": "Task-specific output required by work.prompt"} if kind == "project" else {
            "result": {"required_keys": ["invocation_id", "outcome", "artifacts", "evidence"],
                       "invocation_id": invocation, "outcomes": dispatch["outcomes"],
                       "artifacts": "Map emitted artifact names to their business values, using dispatch.artifact_types",
                       "evidence": "Nonempty list of strings identifying actual output files or observed blockers"}}
        request = {"schema_version": "forge-host-request/1", "job_id": "job_" + uuid.uuid4().hex,
                   "attempt_id": attempt, "invocation_id": invocation, "kind": kind,
                   "target_binding": binding, "dispatch": dispatch, "work": work, "reply_contract": reply_contract,
                   "host": {"parent_task": parent, "task_name": name, "model": "gpt-6-luna",
                            "reasoning_effort": "max", "fork_turns": "none"},
                   "resource_limits": {"max_active_workers": 1, "scope": "checkpoint",
                                       "owner": "coordinator", "enforcement": "bridge reservation; all writers cooperate",
                                       "wall_timeout_seconds": None, "tokens": None}}
        envelope = {"request": request, "request_hash": digest(request)}
        c = {"schema_version": SCHEMA, "signature": signature, "request": request,
             "request_hash": envelope["request_hash"], "target": str(state_path),
             "target_sha256": hashlib.sha256(body(state)).hexdigest(), "target_before_sha256": original_sha,
             "package_ref": reference(package_path) if package_path else None,
             "phase": "prepared", "worker": None, "reply_ref": None, "commit": None,
             "repair_attempts": repairs,
             "refs": [{"path": str(job / "request.json"), "sha256": hashlib.sha256(body(envelope)).hexdigest()}] + input_files}
        empty_ledger = {"schema_version": runledger.SCHEMA, "created_at": runledger.now(), "jobs": {}}
        images = [(job / "request.json", envelope), (job / "ledger.json", empty_ledger),
                  (job / "control.json", c), (reservation, {"job_dir": str(job), "request_hash": c["request_hash"]}),
                  (state_path, state)]
        guards = input_files + ([c["package_ref"]] if c["package_ref"] else [])
        transaction(job, state_path, images, guards, original_sha)
        return {**view(c), "request_path": str(job / "request.json"), "reused": False}


def issue(job):
    c = control(job)
    need(c["phase"] == "prepared", "Host call may already have happened; reconcile saved host status, do not issue again")
    c["phase"] = "dispatching"
    transaction(job, c["target"], [(job / "control.json", c)], c["refs"])
    return dispatch_packet(job, c)


def dispatch_packet(job, c):
    """Pure reconstruction of tool arguments; never authorizes another call."""
    r = c["request"]
    message = (r["work"]["prompt"] + "\n\nRead the immutable host request at " + str(job / "request.json") +
               ". Write only inside its work.write_paths. Do not modify the request, checkpoint, package or skill. "
               "Do not delegate, network, or perform external business effects. "
               "Write work.reply_path using forge-host-reply/1: schema_version, job_id, attempt_id, request_hash, "
               "outcome (done or failed), result, artifacts (nonempty path/sha256 list on done), reason (null on done, actual error on failed). "
               "Use the request's identifiers and current output file hashes. "
               "Return the reply path in your final message. Ordinary choices are yours; report actual blockers/errors.")
    message += ("\nOptional identity/hash helper: " + str(Path(__file__).with_name('hostdraft.py')) +
                " reply --request REQUEST --artifact ACTUAL_FILE --out NEW_DRAFT. "
                "It leaves outcome/result ungraded; fill actual work, then check-reply --request REQUEST --reply ASSIGNED_REPLY. "
                "Preflight is not native completion or semantic acceptance; retain the original draft separately.")
    if r["kind"] == "package":
        message += ("\nFor this package node, dispatch.prompt describes the BUSINESS ARTIFACT schema, not the host reply.result envelope. "
                    "reply.result must have exactly invocation_id, outcome, artifacts, evidence. "
                    "Set invocation_id to " + r["invocation_id"] + "; choose one dispatch outcome. "
                    "Put business values under the emitted names in reply.result.artifacts; do not put a bare business object in reply.result. "
                    "reply.result.evidence is a nonempty list of actual output/blocker reference strings. "
                    "The outer reply.artifacts remains a path/sha256 list. Outcome-to-emitted-name contract: " +
                    json.dumps(r["dispatch"]["outcomes"], ensure_ascii=False))
    return {**view(c), "spawn_arguments": {**{k:v for k,v in r["host"].items() if k != "parent_task"}, "message": message},
            "host_status_query": {"path_prefix": r["host"]["parent_task"] + "/" + r["host"]["task_name"]}}


def ledger_image(job, c, status, receipt, response=None, base=None):
    fd, name = tempfile.mkstemp(prefix="ledger-build-", suffix=".json", dir=job)
    os.close(fd)
    path = Path(name)
    try:
        save(path, base if base is not None else read(job / "ledger.json"))
        args = {"job_id": c["request"]["job_id"], "attempt_id": c["request"]["attempt_id"],
                "status": status, "receipt": receipt["path"], "receipt_sha256": receipt["sha256"]}
        if status == "requested":
            args.update(input_hash=c["request_hash"], model=c["request"]["host"]["model"], reasoning="max")
        if response:
            args.update(response=response["path"], response_sha256=response["sha256"])
        runledger.record(path, **args)
        return read(path)
    finally:
        path.unlink(missing_ok=True)


def accepted(job, receipt_path):
    c = control(job)
    need(c["phase"] == "dispatching", "Creation receipt requires a single persisted issue")
    raw = read(receipt_path)
    worker = c["request"]["host"]["parent_task"] + "/" + c["request"]["host"]["task_name"]
    need(raw.get("task_name") == worker, "Creation receipt task_name does not bind to requested worker")
    return record_acceptance(job, c, receipt_path, worker, "creation_tool_return")


def recover_accepted(job, receipt_path):
    """Recover from actual status evidence without fabricating a create return."""
    c = control(job)
    need(c["phase"] == "dispatching", "Status recovery requires an unresolved persisted issue")
    worker = c["request"]["host"]["parent_task"] + "/" + c["request"]["host"]["task_name"]
    observed_status(read(receipt_path), worker)
    return record_acceptance(job, c, receipt_path, worker, "host_status_reconciliation")


def record_acceptance(job, c, receipt_path, worker, origin):
    receipt = capture(job, receipt_path)
    ledger = ledger_image(job, c, "requested", receipt)
    c.update(phase="accepted", worker=worker, acceptance_origin=origin, acceptance_ref=receipt)
    c["refs"].append(receipt)
    transaction(job, c["target"], [(job / "ledger.json", ledger), (job / "control.json", c)], c["refs"])
    return view(c)


def rejected(job, receipt_path, reason):
    c = control(job)
    need(c["phase"] == "dispatching", "Rejection must bind to an issued request")
    raw = read(receipt_path)
    need(not raw.get("task_name") and (raw.get("error") or raw.get("isError") is True),
         "Creation failure needs a saved error receipt, not an accepted worker or silence")
    need(isinstance(reason, str) and reason.strip(), "Rejection needs reason and next action")
    receipt = capture(job, receipt_path)
    requested = ledger_image(job, c, "requested", receipt)
    ledger = ledger_image(job, c, "failed", receipt, base=requested)
    target = read(c["target"])
    if c["request"]["kind"] == "project":
        projectctl.finish(target, c["request"]["target_binding"]["task_id"], c["request"]["invocation_id"], "failed", reason=reason)
    c.update(phase="rejected", target_sha256=hashlib.sha256(body(target)).hexdigest())
    c["refs"].append(receipt)
    transaction(job, c["target"], [(job / "ledger.json", ledger), (Path(c["target"]), target), (job / "control.json", c)], c["refs"])
    return view(c)


def observed_status(raw, worker):
    matches = [x for x in raw.get("agents", []) if x.get("agent_name") == worker]
    need(len(matches) == 1, "Host snapshot lacks exactly one assigned worker; reconcile rather than infer failure")
    status = matches[0].get("agent_status")
    if isinstance(status, dict) and "completed" in status:
        return "completed"
    need(status in {"running", "failed", "interrupted"}, "Host status unsupported/uncertain; reconcile")
    return status


def observe(job, receipt_path):
    c = control(job)
    need(c["phase"] in {"accepted", "running"}, "Only active jobs can observe running status")
    status = observed_status(read(receipt_path), c["worker"])
    need(status == "running", "Use receive for completed or terminate for terminal host failure")
    receipt = capture(job, receipt_path)
    if c["phase"] == "accepted":
        ledger = ledger_image(job, c, "running", receipt)
        c["phase"] = "running"
        c["refs"].append(receipt)
        transaction(job, c["target"], [(job / "ledger.json", ledger), (job / "control.json", c)], c["refs"])
    return view(c)


def check_reply_identity(c, reply_path, reply):
    """Pure outer reply identity checks shared with optional preflight."""
    r = c["request"]
    need(isinstance(reply, dict) and set(reply) == {"schema_version", "job_id", "attempt_id", "request_hash", "outcome", "result", "artifacts", "reason"}, "Malformed host reply")
    need(reply["schema_version"] == "forge-host-reply/1" and reply["job_id"] == r["job_id"]
         and reply["attempt_id"] == r["attempt_id"] and reply["request_hash"] == c["request_hash"], "Stale reply identity")
    need(Path(reply_path).resolve() == Path(r["work"]["reply_path"]), "Reply is not the assigned output path")


def check_reply_content(c, reply):
    """Pure existing outcome/scope/evidence checks; not semantic acceptance."""
    r = c["request"]
    need(reply["outcome"] in {"done", "failed"}, "Unsupported worker task outcome")
    need(isinstance(reply["artifacts"], list), "Reply artifacts must be a list")
    if reply["outcome"] == "done":
        need(reply["reason"] is None and bool(reply["artifacts"]), "Done needs artifact evidence and null reason")
    else:
        need(isinstance(reply["reason"], str) and bool(reply["reason"].strip()), "Failed reply needs actual error and next action")
    scopes = [Path(p) for p in r["work"]["write_paths"]]
    for ref in reply["artifacts"]:
        need(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "Artifact reference needs path/sha256")
        need(any(Path(ref["path"]).resolve().is_relative_to(p) for p in scopes), "Artifact outside assigned worker scope")
    check_refs(reply["artifacts"])


def receive(job, reply_path, receipt_path):
    c = control(job)
    reply = read(reply_path)
    check_reply_identity(c, reply_path, reply)
    if c["phase"] in {"received", "committed"}:
        need(sha(reply_path) == c["reply_ref"]["sha256"], "Duplicate reply content changed")
        return {**view(c), "duplicate": True}
    need(c["phase"] in {"accepted", "running"}, "Job cannot receive a reply in its current phase")
    check_reply_content(c, reply)
    need(observed_status(read(receipt_path), c["worker"]) == "completed", "Actual host completion observation required")
    receipt = capture(job, receipt_path)
    ledger = read(job / "ledger.json")
    if c["phase"] == "accepted":
        # A completed observation logically establishes the context was running;
        # no separate runtime start timestamp is invented.
        ledger = ledger_image(job, c, "running", receipt)
        c["phase"] = "running"
        c["refs"].append(receipt)
        transaction(job, c["target"], [(job / "ledger.json", ledger), (job / "control.json", c)], c["refs"])
    original_reply_ref = reference(reply_path)
    reply_ref = capture(job, reply_path)
    ledger = ledger_image(job, c, "completed", receipt, reply_ref)
    c.update(phase="received", reply_ref=reply_ref)
    c["refs"] += [receipt, reply_ref, original_reply_ref] + reply["artifacts"]
    transaction(job, c["target"], [(job / "ledger.json", ledger), (job / "control.json", c)], c["refs"])
    return view(c)


def commit_plan(job, c, decision_path):
    """Pure local validation/images; no journal, checkpoint or native effects."""
    c = deepcopy(c)
    decision = read(decision_path)
    need(set(decision) == {"schema_version", "request_hash", "reply_sha256", "outcome", "results", "reason"}, "Malformed coordinator decision")
    need(decision["schema_version"] == "forge-host-decision/1" and decision["request_hash"] == c["request_hash"]
         and c["reply_ref"] and decision["reply_sha256"] == c["reply_ref"]["sha256"], "Decision/reply binding mismatch")
    if c["phase"] == "committed":
        need(reference(decision_path) == c["commit"]["decision_ref"], "A different decision cannot overwrite a committed job")
        return {"control": c, "images": [], "refs": c['refs'], "duplicate": True}
    need(c["phase"] == "received", "Completion receipt and valid reply must precede commit")
    reply = read(c["reply_ref"]["path"])
    need(not (reply["outcome"] == "failed" and decision["outcome"] == "done"), "Actual failed task cannot become done")
    target = read(c["target"])
    refs = c["refs"] + [reference(decision_path)]
    write_target = True
    if c["request"]["kind"] == "project":
        report = projectctl.finish(target, c["request"]["target_binding"]["task_id"],
                                   c["request"]["invocation_id"], decision["outcome"],
                                   decision["results"], decision["reason"])
        for result in (decision["results"] or {}).get("acceptance_results", {}).values():
            refs.extend(result["evidence"])
    else:
        if decision["outcome"] == "done":
            need(decision["reason"] is None, "Package acceptance needs null reason")
            need(decision["results"] == reply["result"], "Package decision must submit the actual worker Flow response")
            target = packagectl.advance(read(c["package_ref"]["path"]), target, decision["results"])
        else:
            need(decision["outcome"] in {"failed", "blocked"} and decision["results"] is None
                 and isinstance(decision["reason"], str) and bool(decision["reason"].strip()),
                 "Package rejection needs failed/blocked, null results, and reason with reconciliation next action")
            # Close only this host attempt. The original Flow invocation remains
            # ready; explicit host recovery may retry it, within the bridge bound.
            write_target = False
        report = {"flow_status": target["flow_state"]["status"], "steps": target["flow_state"]["steps"],
                  "checkpoint_advanced": write_target, "coordinator_outcome": decision["outcome"]}
    check_refs(refs)
    c.update(phase="committed", target_sha256=hashlib.sha256(body(target)).hexdigest() if write_target else sha(c["target"]), refs=refs,
             commit={"decision_ref": reference(decision_path), "target_result": report,
                     "worker_task_outcome": reply["outcome"], "coordinator_outcome": decision["outcome"], "recorded_at": runledger.now()})
    images = ([(Path(c["target"]), target)] if write_target else []) + [(job / "control.json", c)]
    return {"control": c, "images": images, "refs": refs, "duplicate": False}


def commit(job, decision_path):
    original = control(job)
    plan = commit_plan(job, original, decision_path)
    if plan['duplicate']:
        return {**view(plan['control']), 'duplicate': True}
    transaction(job, original['target'], plan['images'], plan['refs'], original['target_sha256'])
    return view(plan['control'])


def terminate(job, receipt_path, reason):
    c = control(job)
    need(c["phase"] in {"accepted", "running"}, "Only an active recorded worker can terminate")
    observed = observed_status(read(receipt_path), c["worker"])
    need(observed in {"failed", "interrupted"}, "Unknown/running/completed host is not proof of termination")
    need(isinstance(reason, str) and reason.strip(), "Termination needs reason and reconciliation next action")
    receipt = capture(job, receipt_path)
    ledger = ledger_image(job, c, observed, receipt)
    target = read(c["target"])
    if c["request"]["kind"] == "project":
        projectctl.finish(target, c["request"]["target_binding"]["task_id"], c["request"]["invocation_id"], "failed", reason=reason)
    c.update(phase="terminated", target_sha256=hashlib.sha256(body(target)).hexdigest())
    c["refs"].append(receipt)
    transaction(job, c["target"], [(job / "ledger.json", ledger), (Path(c["target"]), target), (job / "control.json", c)], c["refs"])
    return view(c)


def reconcile(job):
    c = control(job)
    ledger = runledger.status(job / "ledger.json", job_id=c["request"]["job_id"], input_hash=c["request_hash"])
    result = view(c)
    if c["phase"] in {"accepted", "running", "received", "committed", "terminated", "rejected"}:
        need(ledger["evidence_valid"], "Ledger evidence drifted; reconcile before retry")
    need(ledger["state"] in PHASE_LEDGER[c["phase"]], "Ledger phase contradicts bridge control; reconcile")
    result["ledger"] = ledger
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare", help="reserve a task/node and persist its immutable worker request")
    prepare_parser.add_argument("--kind", choices=["project", "package"], required=True)
    prepare_parser.add_argument("--state", required=True)
    prepare_parser.add_argument("--work", required=True)
    prepare_parser.add_argument("--job", required=True)
    prepare_parser.add_argument("--task")
    prepare_parser.add_argument("--package")
    prepare_parser.add_argument("--parent", default="/root")
    for name in ["issue", "accepted", "recover-accepted", "rejected", "observe", "receive", "commit", "terminate", "reconcile"]:
        p = commands.add_parser(name)
        p.add_argument("--job", required=True)
        if name in {"accepted", "recover-accepted", "rejected", "observe", "receive", "terminate"}:
            p.add_argument("--receipt", required=True)
        if name == "receive":
            p.add_argument("--reply", required=True)
        if name == "commit":
            p.add_argument("--decision", required=True)
        if name in {"terminate", "rejected"}:
            p.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.kind, args.state, args.work, args.job, args.task, args.package, args.parent)
        else:
            job, target = context(args.job)
            with checkpoint_lock(target):
                if args.command in {"issue", "reconcile"}:
                    result = globals()[args.command](job)
                elif args.command in {"accepted", "observe"}:
                    result = globals()[args.command](job, args.receipt)
                elif args.command == "recover-accepted":
                    result = recover_accepted(job, args.receipt)
                elif args.command == "receive":
                    result = receive(job, args.reply, args.receipt)
                elif args.command == "commit":
                    result = commit(job, args.decision)
                else:
                    result = globals()[args.command](job, args.receipt, args.reason)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (BridgeError, projectctl.ProjectError, runledger.LedgerError, flowctl.FlowError,
            OSError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({"status": "reconcile_required", "error": str(error),
                          "next_action": "Inspect the bound checkpoint, job journal and actual host before any retry.",
                          "automatic_host_call": False}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
