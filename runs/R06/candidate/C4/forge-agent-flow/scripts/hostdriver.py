#!/usr/bin/env python3
"""Persistent typed actions for an autonomous host agent, not a provider SDK.

The host agent claims an action, calls the named native tool once, saves its
actual JSON return, then acknowledges it. Review is an independent coordinator
operation. POSIX, sequential workers, cooperating checkpoint writers only.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import json
import math
import re
import time
import uuid

import hostbridge as h
import hostcapacity as capacity
import packagectl
import projectctl

SCHEMA = "forge-host-driver/1"


def write(root, state):
    h.save(root / "driver.json", state)


def load(root):
    state = h.read(root / "driver.json")
    h.need(state.get("schema_version") == SCHEMA, "Unsupported driver schema")
    h.need(h.digest(state["config"]) == state["config_hash"], "Driver configuration drifted")
    h.check_refs(state["config"]["refs"])
    if state["config"].get("capacity"):
        with h.checkpoint_lock(state["config"]["capacity"]["path"]):
            capacity.checked(state["config"]["capacity"])
    for record in state["actions"].values():
        h.check_refs([record["payload_ref"]])
        if record.get("ack_ref"):
            h.check_refs([record["ack_ref"]])
    if state["current"]:
        h.check_refs([state["current"]["work_ref"]])
    else:
        h.need(h.sha(state["config"]["checkpoint"]) == state["checkpoint_sha256"],
               "Checkpoint moved outside the driver; reconcile current owner")
    return state


def init(root, kind, checkpoint, works, parent, package=None, max_actions=50, max_polls=20,
         registry=None, deadline_seconds=None, deadline_policy="observe"):
    h.need(kind in {"project", "package"}, "Unsupported driver kind")
    h.need(re.fullmatch(r"(?:/[a-zA-Z0-9_.-]+)+", parent) is not None, "Invalid canonical parent path")
    h.need(type(max_actions) is int and max_actions > 0 and type(max_polls) is int and max_polls > 0,
           "Action and poll limits must be positive integers")
    h.need((kind == "package") == bool(package), "Only package drivers require --package")
    mapping = h.read(works)
    h.need(isinstance(mapping, dict) and bool(mapping), "Work map must map task/node IDs to template paths")
    normalized = {}
    for key, path in mapping.items():
        h.need(isinstance(key, str) and isinstance(path, str) and Path(path).is_absolute(),
               "Work templates need ID keys and absolute paths")
        normalized[key] = str(Path(path).resolve(strict=True))
    refs = [h.reference(works)] + [h.reference(p) for p in normalized.values()]
    if package:
        refs.append(h.reference(package))
    config = {"kind": kind, "checkpoint": str(Path(checkpoint).resolve(strict=True)),
              "works": normalized, "parent": parent, "package": str(Path(package).resolve()) if package else None,
              "max_actions": max_actions, "max_polls_per_job": max_polls, "refs": refs}
    h.need(deadline_policy in {"observe", "interrupt"}, "Unsupported deadline policy")
    h.need(deadline_seconds is not None or deadline_policy == "observe", "Interrupt policy needs a deadline")
    if deadline_seconds is not None:
        h.need(type(deadline_seconds) in {int, float} and math.isfinite(deadline_seconds) and deadline_seconds > 0,
               "Deadline seconds must be positive and finite")
        config["deadline"] = {"seconds": deadline_seconds, "policy": deadline_policy}
        clock()  # Fail before dispatch if a same-boot monotonic clock is unavailable.
    if registry:
        config["capacity"] = capacity.bind(registry)
        protected = [Path(config["capacity"]["path"]), Path(config["capacity"]["path"] + ".hostbridge.lock")]
        for path in normalized.values():
            for scope in h.read(path)["write_paths"]:
                h.need(not any(p.is_relative_to(Path(scope).resolve()) for p in protected),
                       "Worker write scope includes capacity registry or its lock")
    root.mkdir(parents=True, exist_ok=True)
    if (root / "driver.json").exists():
        state = load(root)
        h.need(state["config"] == config, "Existing driver cannot change its configuration")
        return {**overview(state), "reused": True}
    state = {"schema_version": SCHEMA, "run_id": "driver_" + uuid.uuid4().hex,
             "config": config, "config_hash": h.digest(config), "phase": "active", "reason": None,
             "checkpoint_sha256": h.sha(checkpoint), "current": None, "jobs": [],
             "actions": {}, "pending": None, "claims": 0, "host_call_claims": 0, "rejected_imports": []}
    write(root, state)
    return overview(state)


def overview(state):
    return {"phase": state["phase"], "reason": state["reason"], "run_id": state["run_id"],
            "jobs": len(state["jobs"]), "claims": state["claims"], "host_call_claims": state["host_call_claims"],
            "pending": state["pending"], "automatic_host_call": False,
            "execution_owner": "host_agent", "tokens": None, "cost": None,
            "internal_model_identity_verified": False}


def clock():
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    h.need(bool(boot), "Deadline boot identity unavailable")
    return {"boot_id": boot,
            "monotonic_ns": time.monotonic_ns(), "observed_at": h.runledger.now()}


def refresh_deadline(state):
    current = state.get("current") or {}
    deadline = current.get("deadline")
    if not deadline:
        return None
    now = clock()
    h.need(now["boot_id"] == deadline["started_clock"]["boot_id"],
           "Deadline boot identity changed; reconcile without wall-clock inference")
    h.need(now["monotonic_ns"] >= deadline["started_clock"]["monotonic_ns"], "Monotonic clock moved backwards")
    if now["monotonic_ns"] >= deadline["deadline_monotonic_ns"] and not deadline["expired_observation"]:
        deadline["expired_observation"] = now
    return now


def allocation_binding(root, state, c):
    spawns = [h.read(r["payload_ref"]["path"]) for r in state["actions"].values()
              if h.read(r["payload_ref"]["path"])["kind"] == "spawn"
              and h.read(r["payload_ref"]["path"])["job_id"] == c["request"]["job_id"]]
    h.need(len(spawns) == 1, "Capacity requires exactly one bound spawn intent")
    return {"run_id": state["run_id"], "driver_dir": str(root.resolve()), "checkpoint": c["target"],
            "job_dir": state["current"]["job_dir"], "job_id": c["request"]["job_id"],
            "attempt_id": c["request"]["attempt_id"], "request_hash": c["request_hash"],
            "worker": c["request"]["host"]["parent_task"] + "/" + c["request"]["host"]["task_name"],
            "spawn_action_id": spawns[0]["action_id"]}


def release_capacity(root, state, c):
    if state["config"].get("capacity") and c["phase"] in {"received", "committed", "terminated", "rejected"}:
        return capacity.release(state["config"]["capacity"], allocation_binding(root, state, c),
                                state["current"]["job_dir"], c)


def post_deadline_running(deadline):
    query_clock = ((deadline or {}).get("running_after_deadline") or {}).get("query_claim_clock")
    return bool(deadline and query_clock and query_clock["boot_id"] == deadline["started_clock"]["boot_id"]
                and query_clock["monotonic_ns"] >= deadline["deadline_monotonic_ns"])


def bridge_control(state):
    job = Path(state["current"]["job_dir"])
    with h.checkpoint_lock(state["config"]["checkpoint"]):
        return h.control(job)


def bridge_call(state, function, *args):
    job = Path(state["current"]["job_dir"])
    with h.checkpoint_lock(state["config"]["checkpoint"]):
        return function(job, *args)


def stop(root, state, reason):
    state.update(phase="blocked", reason=reason)
    write(root, state)
    return overview(state)


def select(root, state):
    config = state["config"]
    with h.checkpoint_lock(config["checkpoint"]):
        h.need(h.sha(config["checkpoint"]) == state["checkpoint_sha256"], "Checkpoint changed before scheduling")
        checkpoint = h.read(config["checkpoint"])
        if config["kind"] == "project":
            checkpoint = projectctl.load_state(config["checkpoint"])
            pending = projectctl.next_tasks(checkpoint)
            h.need(not pending["reconcile"], "Original project has an active task; reconcile it before scheduling")
            ready = [r for r in pending["ready"] if checkpoint["tasks"][r["task_id"]]["status"] == "todo"]
            target = ready[0]["task_id"] if ready else None
        else:
            pending = packagectl.pending(h.read(config["package"]), checkpoint)
            target = pending.get("node") if pending["status"] == "ready" else None
    if target is None:
        state["controller_result"] = pending
        state["phase"] = "completed" if pending["status"] == "completed" else "blocked"
        state["reason"] = None if state["phase"] == "completed" else "Original controller needs review, acceptance or explicit failure reconciliation."
        write(root, state)
        return False
    h.need(target in config["works"], "No bound work template for ready target: " + target)
    directory = root / "jobs" / ("job-%04d" % (len(state["jobs"]) + 1))
    directory.mkdir(parents=True, exist_ok=True)
    work = deepcopy(h.read(config["works"][target]))
    # Explicit dependency binding happens once, when the original target is ready.
    # Literal hashes and absent-input declarations retain the bridge's semantics.
    for ref in work.get("input_files", []):
        if ref.get("sha256") == "at_dispatch":
            ref["path"] = str(Path(ref["path"]).resolve())
            ref["sha256"] = h.existing_sha(ref["path"])
    h.save(directory / "work.json", work)
    state["current"] = {"target_id": target, "job_dir": str(directory / "bridge"),
                        "work_ref": h.reference(directory / "work.json"), "polls": 0}
    # This intent survives prepare/issue succeeding before the driver update.
    write(root, state)
    return True


def ensure_prepared(state):
    current, config = state["current"], state["config"]
    job = Path(current["job_dir"])
    if not (job / "control.json").exists() and not (job / "pending.json").exists():
        h.prepare(config["kind"], config["checkpoint"], current["work_ref"]["path"], job,
                  current["target_id"] if config["kind"] == "project" else None, config["package"], config["parent"])
    return bridge_control(state)


def expose(root, state, action_id):
    record = state["actions"][action_id]
    return {**overview(state), "action": h.read(record["payload_ref"]["path"]),
            "action_path": record["payload_ref"]["path"], "action_sha256": record["payload_ref"]["sha256"],
            "call_allowed": False, "next_step": "claim this action before calling; an already claimed action cannot be called again"}


def emit(root, state, c, kind, tool, arguments, extra=None):
    if state["claims"] >= state["config"]["max_actions"]:
        return stop(root, state, "Action claim budget exhausted; reconcile outstanding effects before changing the run.")
    if kind == "query" and state["current"]["polls"] >= state["config"]["max_polls_per_job"]:
        return stop(root, state, "Host status poll budget exhausted; do not infer failure or respawn.")
    action_id = "action_" + uuid.uuid4().hex
    payload = {"schema_version": "forge-host-action/1", "action_id": action_id, "run_id": state["run_id"],
               "job_dir": state["current"]["job_dir"], "job_id": c["request"]["job_id"],
               "attempt_id": c["request"]["attempt_id"], "request_hash": c["request_hash"],
               "kind": kind, "tool": tool, "arguments": arguments, **(extra or {})}
    path = root / "actions" / (action_id + ".json")
    path.parent.mkdir(exist_ok=True)
    h.save(path, payload)
    state["actions"][action_id] = {"payload_ref": h.reference(path), "status": "proposed", "ack_ref": None}
    state["pending"] = action_id
    write(root, state)
    return expose(root, state, action_id)


def close_current(root, state, c):
    current = state["current"]
    outcome = (c.get("commit") or {}).get("coordinator_outcome")
    state["jobs"].append({**current, "job_id": c["request"]["job_id"], "request_hash": c["request_hash"],
                          "phase": c["phase"], "coordinator_outcome": outcome,
                          "acceptance_origin": c.get("acceptance_origin"), "commit": c.get("commit")})
    state["checkpoint_sha256"] = c["target_sha256"]
    state["current"] = None
    state["pending"] = None
    if c["phase"] != "committed" or outcome != "done":
        state.update(phase="blocked", reason="Actual worker/acceptance failure retained; reconcile effects and inputs before an explicit new attempt.")
    write(root, state)


def advance(root):
    state = load(root)
    refresh_deadline(state)
    if (state.get("current") or {}).get("deadline"):
        write(root, state)
    if state["pending"]:
        record = state["actions"][state["pending"]]
        if record["status"] == "ack_pending":
            apply_ack(root, state, state["pending"])
            state = load(root)
        elif record["status"] == "proposed":
            # Validate the original checkpoint/input binding before exposing a call.
            bridge_control(state)
            action = h.read(record["payload_ref"]["path"])
            if action["kind"] == "interrupt" and not post_deadline_running(state["current"].get("deadline")):
                record["status"] = "superseded"
                state["pending"] = None
                write(root, state)
            else:
                return expose(root, state, state["pending"])
        elif record["status"] == "claimed":
            record["status"] = "uncertain"
            state["pending"] = None
            write(root, state)
    if state["phase"] != "active":
        return {**overview(state), "controller_result": state.get("controller_result")}
    if not state["current"] and not select(root, state):
        return {**overview(state), "controller_result": state.get("controller_result")}
    c = ensure_prepared(state)
    release_capacity(root, state, c)
    if c["phase"] in {"committed", "terminated", "rejected"}:
        close_current(root, state, c)
        return advance(root)
    if c["phase"] == "prepared":
        bridge_call(state, h.issue)
        c = bridge_control(state)
    packet = h.dispatch_packet(Path(state["current"]["job_dir"]), c)
    uncertain_spawn = any(r["status"] in {"claimed", "uncertain", "reconciled"}
                          and h.read(r["payload_ref"]["path"])["kind"] == "spawn"
                          and h.read(r["payload_ref"]["path"])["job_id"] == c["request"]["job_id"]
                          for r in state["actions"].values())
    if c["phase"] == "dispatching" and not uncertain_spawn:
        return emit(root, state, c, "spawn", "collaboration.spawn_agent", packet["spawn_arguments"])
    if c["phase"] in {"dispatching", "accepted", "running"}:
        deadline = state["current"].get("deadline")
        if (c["phase"] in {"accepted", "running"} and deadline and deadline["expired_observation"]
                and post_deadline_running(deadline)
                and not deadline.get("interrupt_claimed_action")
                and state["config"]["deadline"]["policy"] == "interrupt"):
            worker = c["request"]["host"]["parent_task"] + "/" + c["request"]["host"]["task_name"]
            return emit(root, state, c, "interrupt", "collaboration.interrupt_agent", {"target": worker},
                        {"purpose": "deadline_after_actual_running", "terminal_evidence": False})
        return emit(root, state, c, "query", "collaboration.list_agents", packet["host_status_query"],
                    {"purpose": "reconcile_missing_creation_receipt" if c["phase"] == "dispatching" else "observe_worker",
                     "wait_guidance": "Wait for a host notification before repeated running polls; never infer timeout from silence."})
    h.need(c["phase"] == "received", "Unsupported bridge phase")
    return emit(root, state, c, "review", "coordinator.source_review", {},
                {"sources": {"request": str(Path(state["current"]["job_dir"]) / "request.json"),
                             "reply": c["reply_ref"], "checkpoint": c["target"]},
                 "decision_contract": "forge-host-decision/1; independently check original requirements and actual output, then submit the original project/Flow protocol"})


def claim(root, action_id):
    state = load(root)
    h.need(action_id in state["actions"], "Unknown action ID")
    record = state["actions"][action_id]
    if record["status"] != "proposed":
        return {**overview(state), "call_allowed": False, "already_claimed": True,
                "next_step": "next reconciles an unacknowledged action; do not repeat its tool call"}
    h.need(state["phase"] == "active" and state["pending"] == action_id, "Stale action cannot be claimed")
    c = bridge_control(state)
    now = refresh_deadline(state)
    h.need(state["claims"] < state["config"]["max_actions"], "Action budget exhausted")
    action = h.read(record["payload_ref"]["path"])
    if action["kind"] == "spawn":
        if state["config"].get("capacity"):
            admission = capacity.reserve(state["config"]["capacity"], allocation_binding(root, state, c))
            if not admission["admitted"]:
                return {**overview(state), "call_allowed": False, "status": "waiting_capacity", "capacity": admission,
                        "next_step": "Wait for an actual terminal observation to release a slot, then claim this same action."}
        if state["config"].get("deadline"):
            now = clock()
            state["current"]["deadline"] = {"started_clock": now,
                "deadline_monotonic_ns": now["monotonic_ns"] + max(1,
                    int(state["config"]["deadline"]["seconds"]) * 1_000_000_000
                    + int((state["config"]["deadline"]["seconds"] % 1) * 1e9)),
                "expired_observation": None, "running_after_deadline": None,
                "interrupt_claimed_action": None, "interrupt_return_ref": None,
                "completion_observed_after_deadline": None}
    if action["kind"] == "interrupt":
        deadline = state["current"]["deadline"]
        h.need(deadline["expired_observation"] and post_deadline_running(deadline)
               and not deadline["interrupt_claimed_action"], "Interrupt requires one bound post-deadline running observation")
        deadline["interrupt_claimed_action"] = action_id
    if action["kind"] == "query":
        h.need(state["current"]["polls"] < state["config"]["max_polls_per_job"], "Poll budget exhausted")
        state["current"]["polls"] += 1
        if now:
            record["claimed_clock"] = now
    record["status"] = "claimed"
    state["claims"] += 1
    state["host_call_claims"] += int(action["kind"] != "review")
    write(root, state)
    return {**overview(state), "action": action, "call_allowed": True,
            "next_step": "perform exactly this action once; save the actual receipt or independent decision and ack"}


def apply_ack(root, state, action_id):
    record = state["actions"][action_id]
    action = h.read(record["payload_ref"]["path"])
    receipt = record["ack_ref"]["path"]
    c = bridge_control(state)
    now = refresh_deadline(state)
    if action["kind"] == "spawn":
        if c["phase"] == "dispatching":
            raw = h.read(receipt)
            if raw.get("task_name"):
                bridge_call(state, h.accepted, receipt)
            else:
                bridge_call(state, h.rejected, receipt, "Actual creation error; inspect host effects before an explicit new attempt.")
        else:
            accepted_sha = c.get("acceptance_ref", {}).get("sha256")
            rejected_sha = c["phase"] == "rejected" and any(r["sha256"] == record["ack_ref"]["sha256"] for r in c["refs"])
            h.need(accepted_sha == record["ack_ref"]["sha256"] or rejected_sha,
                   "Creation replay differs from the accepted evidence")
    elif action["kind"] == "query":
        if c["phase"] == "dispatching":
            bridge_call(state, h.recover_accepted, receipt)
            c = bridge_control(state)
        worker = c["request"]["host"]["parent_task"] + "/" + c["request"]["host"]["task_name"]
        observed = h.observed_status(h.read(receipt), worker)
        deadline = state["current"].get("deadline")
        if deadline and deadline["expired_observation"]:
            claimed_clock = record.get("claimed_clock")
            if (observed == "running" and claimed_clock
                    and claimed_clock["boot_id"] == deadline["started_clock"]["boot_id"]
                    and claimed_clock["monotonic_ns"] >= deadline["deadline_monotonic_ns"]):
                deadline["running_after_deadline"] = {"clock": now, "query_claim_clock": claimed_clock,
                                                       "receipt": record["ack_ref"]}
            elif observed == "completed":
                deadline["completion_observed_after_deadline"] = {"clock": now, "receipt": record["ack_ref"]}
        if c["phase"] in {"accepted", "running"}:
            if observed == "running":
                bridge_call(state, h.observe, receipt)
            elif observed == "completed":
                bridge_call(state, h.receive, c["request"]["work"]["reply_path"], receipt)
            else:
                bridge_call(state, h.terminate, receipt, "Actual host " + observed + "; reconcile effects before an explicit new attempt.")
        else:
            h.need(any(r["sha256"] == record["ack_ref"]["sha256"] for r in c["refs"]), "Status replay differs from recorded evidence")
        if action.get("purpose") == "reconcile_missing_creation_receipt":
            for old in state["actions"].values():
                payload = h.read(old["payload_ref"]["path"])
                if payload["kind"] == "spawn" and payload["job_id"] == action["job_id"] and old["status"] == "uncertain":
                    old.update(status="reconciled", reconciled_by=action_id)
    elif action["kind"] == "interrupt":
        # Control returns describe the command/previous status, never a terminal observation.
        state["current"]["deadline"]["interrupt_return_ref"] = record["ack_ref"]
    else:
        bridge_call(state, h.commit, receipt)
    release_capacity(root, state, bridge_control(state))
    record["status"] = "acked"
    state["pending"] = None
    write(root, state)
    return {**overview(state), "acked": action_id}


def ack(root, action_id, source, decision=False):
    state = load(root)
    h.need(action_id in state["actions"], "Unknown action ID")
    record = state["actions"][action_id]
    action = h.read(record["payload_ref"]["path"])
    h.need((action["kind"] == "review") == decision, "Action requires the matching receipt/decision argument")
    ref = h.capture(root, source)
    if record["status"] in {"acked", "ack_pending"}:
        h.need(ref["sha256"] == record["ack_ref"]["sha256"], "Different ack cannot overwrite an action")
        return {**overview(state), "duplicate": True} if record["status"] == "acked" else apply_ack(root, state, action_id)
    h.need(state["pending"] == action_id and record["status"] == "claimed", "Stale/unclaimed action cannot import evidence")
    c = bridge_control(state)
    try:
        h.need(action["job_id"] == c["request"]["job_id"] and action["request_hash"] == c["request_hash"], "Action request binding mismatch")
        raw = h.read(ref["path"])
        worker = c["request"]["host"]["parent_task"] + "/" + c["request"]["host"]["task_name"]
        if action["kind"] == "spawn":
            h.need(raw.get("task_name") == worker or (not raw.get("task_name") and (raw.get("error") or raw.get("isError") is True)),
                   "Creation receipt does not bind to requested worker or an actual error")
        elif action["kind"] == "query":
            h.observed_status(raw, worker)
        elif action["kind"] == "interrupt":
            h.need(isinstance(raw, dict) and bool(raw), "Interrupt needs the actual nonempty control return")
            for field in ["task_name", "target", "agent_name"]:
                h.need(field not in raw or raw[field] == worker, "Interrupt return binds another worker")
        else:
            h.need(raw.get("request_hash") == c["request_hash"] and raw.get("reply_sha256") == c["reply_ref"]["sha256"],
                   "Decision/reply binding mismatch")
    except (ValueError, KeyError, TypeError) as error:
        state["rejected_imports"].append({"action_id": action_id, "ref": ref, "error": str(error)})
        write(root, state)
        raise
    record.update(status="ack_pending", ack_ref=ref)
    write(root, state)
    return apply_ack(root, state, action_id)


def inspect(root):
    from hostoverview import describe
    return describe(root, load(root), clock)


def resume(root, expected_run):
    h.need(load(root)['run_id'] == expected_run, 'Run ID does not match the saved driver')
    return advance(root)


def retry_review(root, expected_run, action_id, reason):
    """Reject only a provably invalid, uncommitted local review ack; retain it."""
    state = load(root)
    h.need(state['run_id'] == expected_run, 'Run ID does not match the saved driver')
    h.need(isinstance(reason, str) and bool(reason.strip()), 'Review reconciliation needs a reason')
    h.need(state['phase'] == 'active' and state['pending'] == action_id, 'Only the active pending review can reconcile')
    record = state['actions'][action_id]
    action = h.read(record['payload_ref']['path'])
    h.need(action['kind'] == 'review' and record['status'] == 'ack_pending',
           'Only a pending local source-review ack can reconcile; never discard native actions')
    job = Path(state['current']['job_dir'])
    with h.checkpoint_lock(state['config']['checkpoint']):
        h.need(not (job / 'pending.json').exists(), 'Pending bridge transaction must recover, never discard its ack')
        c = h.checked_control(job)
        h.need(c['phase'] == 'received', 'Review reconciliation requires an uncommitted received reply')
        h.need(action['job_id'] == c['request']['job_id'] and action['request_hash'] == c['request_hash'],
               'Review action request binding mismatch')
        try:
            h.commit_plan(job, c, record['ack_ref']['path'])
        except ValueError as error:
            h.need(not h.has_io_cause(error), 'Review evidence is unavailable; restore it before replay, never discard its ack')
            validation_error = str(error)
        else:
            raise h.BridgeError('Saved review ack is valid; resume it rather than discard it')
        rejection = {'action_id': action_id, 'ref': record['ack_ref'], 'error': validation_error,
                     'reason': reason, 'origin': 'explicit_invalid_uncommitted_review_reconciliation',
                     'recorded_at': h.runledger.now()}
        state['rejected_imports'].append(rejection)
        record.update(status='rejected_ack', ack_rejection=rejection)
        state['pending'] = None
        write(root, state)
    return {**overview(state), 'rejected_review_ack': action_id, 'validation_error': validation_error,
            'call_allowed': False, 'next_step': 'Resume the same run to expose a new source review within the original budget.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("init")
    p.add_argument("--driver", required=True)
    p.add_argument("--kind", choices=["project", "package"], required=True)
    p.add_argument("--state", required=True)
    p.add_argument("--works", required=True)
    p.add_argument("--parent", required=True)
    p.add_argument("--package")
    p.add_argument("--max-actions", type=int, default=50)
    p.add_argument("--max-polls", type=int, default=20)
    p.add_argument("--registry")
    p.add_argument("--deadline-seconds", type=float)
    p.add_argument("--deadline-policy", choices=["observe", "interrupt"], default="observe")
    for name in ["next", "status", "claim", "ack", "inspect", "resume", "retry-review"]:
        p = commands.add_parser(name)
        p.add_argument("--driver", required=True)
        if name in {"claim", "ack", "retry-review"}:
            p.add_argument("--action", required=True)
        if name in {'resume', 'retry-review'}:
            p.add_argument('--expect-run', required=True)
        if name == 'retry-review':
            p.add_argument('--reason', required=True)
        if name == "ack":
            source = p.add_mutually_exclusive_group(required=True)
            source.add_argument("--receipt")
            source.add_argument("--decision")
    args = parser.parse_args(argv)
    root = Path(args.driver).resolve()
    try:
        with h.checkpoint_lock(root / "driver.json"):
            if args.command == "init":
                result = init(root, args.kind, args.state, args.works, args.parent, args.package, args.max_actions, args.max_polls,
                              args.registry, args.deadline_seconds, args.deadline_policy)
            elif args.command == "next":
                result = advance(root)
            elif args.command == "claim":
                result = claim(root, args.action)
            elif args.command == "ack":
                result = ack(root, args.action, args.decision or args.receipt, bool(args.decision))
            elif args.command == 'inspect':
                result = inspect(root)
            elif args.command == 'resume':
                result = resume(root, args.expect_run)
            elif args.command == 'retry-review':
                result = retry_review(root, args.expect_run, args.action, args.reason)
            else:
                state = load(root)
                if state["current"]:
                    bridge_control(state)
                result = overview(state)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "reconcile_required", "error": str(error), "automatic_host_call": False,
                          "next_action": "Inspect saved driver intent and bridge evidence; never repeat a claimed spawn."}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
