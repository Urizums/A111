#!/usr/bin/env python3
"""Local active-worker admission for cooperating POSIX host drivers.

No native calls, provider quota, lease expiry or missing-worker inference.
"""
from pathlib import Path
import argparse
import json
import uuid

import hostbridge as h

SCHEMA = "forge-host-capacity/1"


def read(path):
    value = h.read(path)
    h.need(value.get("schema_version") == SCHEMA, "Unsupported capacity registry")
    h.need(type(value.get("limit")) is int and value["limit"] > 0, "Invalid capacity limit")
    h.need(isinstance(value.get("registry_id"), str) and bool(value["registry_id"]), "Missing registry identity")
    for slot in value["allocations"].values():
        h.need(slot["status"] in {"held", "released"}, "Unknown capacity allocation state")
        if slot["status"] == "released":
            h.check_refs([slot["proof"]["receipt"]])
    h.need(sum(s["status"] == "held" for s in value["allocations"].values()) <= value["limit"],
           "Registry holds exceed its limit; reconcile")
    return value


def init(path, limit):
    path = Path(path).resolve()
    h.need(type(limit) is int and limit > 0, "Capacity limit must be a positive integer")
    with h.checkpoint_lock(path):
        if path.exists():
            value = read(path)
            h.need(value["limit"] == limit, "Existing registry cannot change capacity")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            value = {"schema_version": SCHEMA, "registry_id": "capacity_" + uuid.uuid4().hex,
                     "limit": limit, "allocations": {}}
            h.save(path, value)
        return summary(value)


def bind(path):
    path = Path(path).resolve(strict=True)
    with h.checkpoint_lock(path):
        value = read(path)
        return {"path": str(path), "registry_id": value["registry_id"], "limit": value["limit"]}


def checked(config):
    value = read(config["path"])
    h.need(value["registry_id"] == config["registry_id"] and value["limit"] == config["limit"],
           "Capacity registry identity or limit drifted")
    return value


def summary(value):
    held = sum(s["status"] == "held" for s in value["allocations"].values())
    return {"registry_id": value["registry_id"], "limit": value["limit"], "held": held,
            "available": value["limit"] - held, "scope": "cooperating_local_drivers", "automatic_host_call": False}


def reserve(config, binding):
    with h.checkpoint_lock(config["path"]):
        value = checked(config)
        key = binding["job_id"]
        old = value["allocations"].get(key)
        if old:
            h.need(old["binding"] == binding, "Capacity allocation binding mismatch")
            h.need(old["status"] == "held", "Released job cannot reserve another spawn")
            return {**summary(value), "admitted": True, "reused": True}
        if summary(value)["available"] == 0:
            return {**summary(value), "admitted": False}
        value["allocations"][key] = {"binding": binding, "status": "held", "proof": None}
        h.save(config["path"], value)
        return {**summary(value), "admitted": True, "reused": False}


def terminal_proof(job, c):
    """Use only the current attempt's terminal ledger event, never arbitrary refs."""
    phase = c["phase"]
    if phase not in {"received", "committed", "terminated", "rejected"}:
        return None
    request = c["request"]
    attempts = h.read(Path(job) / "ledger.json")["jobs"][request["job_id"]]["attempts"]
    matches = [a for a in attempts if a["attempt_id"] == request["attempt_id"]]
    h.need(len(matches) == 1 and matches[0]["input_sha256"] == c["request_hash"], "Capacity terminal attempt mismatch")
    event = matches[0]["events"][-1]
    h.check_refs([event["receipt"]])
    raw = h.read(event["receipt"]["path"])
    worker = request["host"]["parent_task"] + "/" + request["host"]["task_name"]
    if phase == "rejected":
        h.need(event["status"] == "failed" and not raw.get("task_name") and (raw.get("error") or raw.get("isError") is True),
               "Capacity release needs actual creation rejection")
        origin = "creation_error"
    else:
        observed = h.observed_status(raw, worker)
        expected = {"completed"} if phase in {"received", "committed"} else {"failed", "interrupted"}
        h.need(observed in expected and event["status"] == observed, "Capacity release lacks actual worker terminal evidence")
        origin = "host_terminal_observation"
    return {"status": event["status"], "origin": origin, "receipt": event["receipt"],
            "recorded_at": event["recorded_at"]}


def release(config, binding, job, c):
    with h.checkpoint_lock(binding["checkpoint"]):
        actual = h.control(Path(job))
        h.need(c == actual, "Capacity release control differs from guarded bridge")
        proof = terminal_proof(job, actual)
    if proof is None:
        return None
    request = c["request"]
    h.need(binding["job_id"] == request["job_id"] and binding["attempt_id"] == request["attempt_id"]
           and binding["request_hash"] == c["request_hash"]
           and binding["worker"] == request["host"]["parent_task"] + "/" + request["host"]["task_name"]
           and binding["checkpoint"] == c["target"] and binding["job_dir"] == str(Path(job).resolve()),
           "Capacity terminal binding mismatch")
    with h.checkpoint_lock(config["path"]):
        value = checked(config)
        slot = value["allocations"].get(binding["job_id"])
        h.need(slot is not None and slot["binding"] == binding, "Capacity release does not own this allocation")
        if slot["status"] == "released":
            h.need(slot["proof"] == proof, "Capacity release proof changed")
            return {**summary(value), "duplicate": True}
        slot.update(status="released", proof=proof)
        h.save(config["path"], value)
        return {**summary(value), "duplicate": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["init", "status"]:
        p = commands.add_parser(name)
        p.add_argument("--registry", required=True)
        if name == "init":
            p.add_argument("--limit", type=int, required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = init(args.registry, args.limit)
        else:
            with h.checkpoint_lock(args.registry):
                result = summary(read(args.registry))
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "reconcile_required", "error": str(error), "automatic_host_call": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
