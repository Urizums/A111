#!/usr/bin/env python3
"""Local evidence ledger for host calls; it never invokes a host or provider."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

SCHEMA = "run-ledger/1"
STATUSES = {"requested", "running", "completed", "failed", "interrupted"}
TERMINAL = {"completed", "failed", "interrupted"}
TRANSITIONS = {
    "requested": {"running", "failed", "interrupted"},
    "running": {"completed", "failed", "interrupted"},
}
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class LedgerError(ValueError):
    """Invalid ledger operation or evidence."""


def now():
    # This is when the local ledger records the event, never a claimed host time.
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def check_id(value, label):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise LedgerError(f"{label} must be 1-128 safe ASCII characters")
    return value


def check_sha(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise LedgerError(f"{label} must be a 64-character SHA256 hex digest")
    return value.lower()


def file_sha256(path):
    digest = hashlib.sha256()
    # O_NONBLOCK makes a path replaced by a FIFO fail closed instead of hanging
    # status/recovery forever. Regular-file reads are unaffected by this flag.
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise LedgerError(f"Evidence path is not a regular file: {path}")
        with os.fdopen(fd, "rb") as stream:
            fd = -1
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    finally:
        if fd >= 0:
            os.close(fd)
    return digest.hexdigest()


def evidence_ref(path, expected_sha, label):
    if not path or not expected_sha:
        raise LedgerError(f"{label} path and SHA256 are required")
    expected = check_sha(expected_sha, f"{label} SHA256")
    try:
        resolved = Path(path).expanduser().resolve(strict=True)
        if not stat.S_ISREG(resolved.stat().st_mode):
            raise LedgerError(f"{label} must be a regular local file: {path}")
        actual = file_sha256(resolved)
    except OSError as exc:
        raise LedgerError(f"Cannot read {label} file {path}: {exc}") from exc
    if actual != expected:
        raise LedgerError(f"{label} SHA256 does not match file: {resolved}")
    return {"path": str(resolved), "sha256": expected}


def save(path, value, exclusive=False):
    """Write atomically for the documented single-writer use case."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=".runledger-", dir=path.parent)
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


def _reject_constant(value):
    raise LedgerError(f"Non-finite JSON number: {value}")


def load(path):
    try:
        with open(path, encoding="utf-8") as stream:
            ledger = json.load(stream, parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise LedgerError(f"Cannot read ledger {path}: {exc}") from exc
    validate_ledger(ledger)
    return ledger


def init_ledger(path):
    target = Path(path)
    ledger = {"schema_version": SCHEMA, "created_at": now(), "jobs": {}}
    save(target, ledger, exclusive=True)
    return {"initialized": True, "ledger": str(target.resolve())}


def _is_timestamp(value):
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value.endswith("Z")
    except ValueError:
        return False


def validate_ledger(ledger):
    if not isinstance(ledger, dict) or set(ledger) != {"schema_version", "created_at", "jobs"}:
        raise LedgerError("Malformed ledger root")
    if ledger["schema_version"] != SCHEMA or not _is_timestamp(ledger["created_at"]):
        raise LedgerError("Unsupported ledger version or invalid creation time")
    jobs = ledger["jobs"]
    if not isinstance(jobs, dict):
        raise LedgerError("Ledger jobs must be an object")
    for job_id, job in jobs.items():
        check_id(job_id, "job_id")
        if not isinstance(job, dict) or set(job) != {"attempts"} or not isinstance(job["attempts"], list):
            raise LedgerError(f"Malformed job {job_id}")
        seen = set()
        previous_id = None
        active = 0
        for attempt in job["attempts"]:
            keys = {"attempt_id", "parent_attempt", "model", "reasoning", "input_sha256", "events"}
            if not isinstance(attempt, dict) or set(attempt) != keys:
                raise LedgerError(f"Malformed attempt in job {job_id}")
            attempt_id = check_id(attempt["attempt_id"], "attempt_id")
            if attempt_id in seen:
                raise LedgerError(f"Duplicate attempt_id {attempt_id} in job {job_id}")
            seen.add(attempt_id)
            parent = attempt["parent_attempt"]
            if previous_id is None:
                if parent is not None:
                    raise LedgerError(f"First attempt in job {job_id} cannot have a parent")
            elif parent != previous_id:
                raise LedgerError(f"Attempt {attempt_id} must name preceding attempt {previous_id} as parent")
            previous_id = attempt_id
            if not isinstance(attempt["model"], str) or not attempt["model"].strip():
                raise LedgerError(f"Attempt {attempt_id} has no model")
            if not isinstance(attempt["reasoning"], str) or not attempt["reasoning"].strip():
                raise LedgerError(f"Attempt {attempt_id} has no reasoning setting")
            check_sha(attempt["input_sha256"], "input_sha256")
            events = attempt["events"]
            if not isinstance(events, list) or not events:
                raise LedgerError(f"Attempt {attempt_id} must begin with requested")
            current = None
            for event in events:
                if not isinstance(event, dict) or set(event) != {"status", "recorded_at", "receipt", "response"}:
                    raise LedgerError(f"Malformed event in attempt {attempt_id}")
                status = event["status"]
                if not isinstance(status, str) or status not in STATUSES or not _is_timestamp(event["recorded_at"]):
                    raise LedgerError(f"Invalid status or record time in attempt {attempt_id}")
                if current is None:
                    if status != "requested":
                        raise LedgerError(f"Attempt {attempt_id} must begin with requested")
                elif status not in TRANSITIONS.get(current, set()):
                    raise LedgerError(f"Illegal transition in attempt {attempt_id}: {current} -> {status}")
                current = status
                _validate_ref_shape(event["receipt"], "receipt")
                if status == "completed":
                    _validate_ref_shape(event["response"], "response")
                elif event["response"] is not None:
                    raise LedgerError(f"Only completed events may contain a response in {attempt_id}")
            if current not in TERMINAL:
                active += 1
        if active > 1:
            raise LedgerError(f"Job {job_id} has multiple unresolved attempts")


def _validate_ref_shape(ref, label):
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
        raise LedgerError(f"Malformed {label} reference")
    if not isinstance(ref["path"], str) or not Path(ref["path"]).is_absolute():
        raise LedgerError(f"{label} path must be absolute")
    check_sha(ref["sha256"], f"{label} SHA256")


def _job(ledger, job_id):
    return ledger["jobs"].setdefault(job_id, {"attempts": []})


def _find_attempt(job, attempt_id):
    for attempt in job["attempts"]:
        if attempt["attempt_id"] == attempt_id:
            return attempt
    return None


def _current_status(attempt):
    return attempt["events"][-1]["status"]


def _verify_ref(ref, label, problems):
    try:
        actual = file_sha256(ref["path"])
    except (OSError, LedgerError) as exc:
        problems.append(f"{label} missing/unreadable: {ref['path']} ({exc})")
        return
    if actual != ref["sha256"]:
        problems.append(f"{label} SHA256 changed: {ref['path']}")


def verify_attempt(attempt):
    problems = []
    for index, event in enumerate(attempt["events"], 1):
        _verify_ref(event["receipt"], f"event {index} receipt", problems)
        if event["response"] is not None:
            _verify_ref(event["response"], f"event {index} response", problems)
    return problems


def record(ledger_path, *, job_id, attempt_id, status, receipt, receipt_sha256,
           input_hash=None, model=None, reasoning=None, parent_attempt=None,
           response=None, response_sha256=None):
    """Append one verified event and atomically replace the local ledger."""
    check_id(job_id, "job_id")
    check_id(attempt_id, "attempt_id")
    if status not in STATUSES:
        raise LedgerError(f"Unknown status: {status}")
    receipt_ref = evidence_ref(receipt, receipt_sha256, "host receipt")
    response_ref = None
    if status == "completed":
        response_ref = evidence_ref(response, response_sha256, "host response")
    elif response is not None or response_sha256 is not None:
        raise LedgerError("Response file/hash are allowed only for completed")
    if (response is None) != (response_sha256 is None):
        raise LedgerError("Host response path and SHA256 must be supplied together")
    checked_input = check_sha(input_hash, "input hash") if input_hash is not None else None

    old = load(ledger_path)
    updated = deepcopy(old)
    job = _job(updated, job_id)
    attempt = _find_attempt(job, attempt_id)
    if status == "requested":
        if attempt is not None:
            raise LedgerError(f"attempt_id already exists: {attempt_id}")
        if checked_input is None or not isinstance(model, str) or not model.strip() or not isinstance(reasoning, str) or not reasoning.strip():
            raise LedgerError("A requested attempt needs --input-hash, --model, and --reasoning")
        for previous in job["attempts"]:
            problems = verify_attempt(previous)
            if problems:
                raise LedgerError("Cannot start a new attempt: invalid evidence in the existing history: " + "; ".join(problems))
        if any(_current_status(item) in {"requested", "running"} for item in job["attempts"]):
            raise LedgerError(f"Job {job_id} already has an unresolved attempt; reconcile it first")
        if any(item["input_sha256"] == checked_input and _current_status(item) == "completed" for item in job["attempts"]):
            raise LedgerError("A completed attempt already has this input hash; reuse it instead of replaying")
        if not job["attempts"]:
            if parent_attempt is not None:
                raise LedgerError("The first attempt cannot have --parent-attempt")
        else:
            expected_parent = job["attempts"][-1]["attempt_id"]
            if parent_attempt != expected_parent:
                raise LedgerError(f"A new attempt must use --parent-attempt {expected_parent}")
        attempt = {"attempt_id": attempt_id, "parent_attempt": parent_attempt,
                   "model": model.strip(), "reasoning": reasoning.strip(),
                   "input_sha256": checked_input, "events": []}
        job["attempts"].append(attempt)
    else:
        if attempt is None:
            raise LedgerError(f"Unknown attempt_id {attempt_id} for job {job_id}; begin with requested")
        current = _current_status(attempt)
        if status not in TRANSITIONS.get(current, set()):
            raise LedgerError(f"Illegal transition: {current} -> {status}")
        if checked_input is not None and checked_input != attempt["input_sha256"]:
            raise LedgerError("Input hash cannot change within an attempt; create a new attempt")
        if model is not None and model != attempt["model"]:
            raise LedgerError("Model cannot change within an attempt")
        if reasoning is not None and reasoning != attempt["reasoning"]:
            raise LedgerError("Reasoning setting cannot change within an attempt")
        if parent_attempt is not None and parent_attempt != attempt["parent_attempt"]:
            raise LedgerError("Parent attempt cannot change")
        problems = verify_attempt(attempt)
        if problems:
            raise LedgerError("Cannot extend attempt with invalid evidence: " + "; ".join(problems))
    event = {"status": status, "recorded_at": now(), "receipt": receipt_ref,
             "response": response_ref}
    attempt["events"].append(event)
    validate_ledger(updated)
    save(ledger_path, updated)
    return {"job_id": job_id, "attempt_id": attempt_id, "status": status,
            "recorded_at": event["recorded_at"], "ledger": str(Path(ledger_path).resolve())}


def status(ledger_path, *, job_id, input_hash):
    check_id(job_id, "job_id")
    wanted = check_sha(input_hash, "input hash")
    ledger = load(ledger_path)
    job = ledger["jobs"].get(job_id)
    base = {"job_id": job_id, "input_sha256": wanted, "automatic_host_call": False}
    if not job or not job["attempts"]:
        return {**base, "state": "none", "action": "start_eligible", "attempt_id": None,
                "evidence_valid": True, "reason": "No attempt is recorded for this job."}

    attempts = job["attempts"]
    # Any invalid evidence makes the job outcome uncertain; a matching completion
    # cannot be called completed/reusable until a human or host reconciles it.
    invalid = [(item, verify_attempt(item)) for item in attempts]
    invalid = [(item, issues) for item, issues in invalid if issues]
    if invalid:
        item, issues = invalid[0]
        return {**base, "state": "evidence_invalid", "recorded_status": _current_status(item),
                "action": "reconcile", "attempt_id": item["attempt_id"],
                "evidence_valid": False, "evidence_issues": issues,
                "reason": "A stored receipt/response is missing or changed; inspect the host before any retry."}

    active = [item for item in attempts if _current_status(item) in {"requested", "running"}]
    if active:
        item = active[0]
        return {**base, "state": _current_status(item), "action": "reconcile",
                "attempt_id": item["attempt_id"], "evidence_valid": True,
                "reason": "Check the host for this attempt; never automatically issue it again."}

    matching = [item for item in attempts if item["input_sha256"] == wanted]
    completed = [item for item in matching if _current_status(item) == "completed"]
    if completed:
        item = completed[-1]
        return {**base, "state": "completed", "action": "reuse", "attempt_id": item["attempt_id"],
                "evidence_valid": True, "reason": "A completed attempt has the same input hash and intact evidence."}
    if matching:
        item = matching[-1]
        if _current_status(item) in {"failed", "interrupted"}:
            return {**base, "state": _current_status(item), "action": "reconcile_before_retry",
                    "attempt_id": item["attempt_id"], "evidence_valid": True,
                    "external_reconciliation_required": True,
                    "reason": "Reconcile possible host-side effects with the host/operator before creating a new attempt_id."}
        return {**base, "state": _current_status(item), "action": "retry_eligible",
                "attempt_id": item["attempt_id"], "evidence_valid": True,
                "reason": "The prior attempt is terminal without a matching completion; retry with a new attempt_id."}
    latest = attempts[-1]
    latest_status = _current_status(latest)
    if latest_status in {"failed", "interrupted"}:
        return {**base, "state": "input_changed", "recorded_status": latest_status,
                "attempt_input_sha256": latest["input_sha256"],
                "action": "reconcile_before_retry", "attempt_id": latest["attempt_id"],
                "evidence_valid": True, "external_reconciliation_required": True,
                "reason": "Reconcile possible host-side effects with the host/operator before creating a new attempt_id."}
    return {**base, "state": "input_changed", "recorded_status": latest_status,
            "attempt_input_sha256": latest["input_sha256"], "action": "retry_eligible",
            "attempt_id": latest["attempt_id"], "evidence_valid": True,
            "reason": "Input hash changed or is new; prior completion cannot be reused. Create a new attempt_id."}


def _print_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init_parser = sub.add_parser("init", help="create a new empty local ledger")
    init_parser.add_argument("--ledger", required=True)

    rec = sub.add_parser("record", help="append a verified host event")
    rec.add_argument("--ledger", required=True)
    rec.add_argument("--job-id", required=True)
    rec.add_argument("--attempt-id", required=True)
    rec.add_argument("--status", required=True, choices=sorted(STATUSES))
    rec.add_argument("--receipt", required=True, help="saved local actual host receipt file")
    rec.add_argument("--receipt-sha256", required=True)
    rec.add_argument("--input-hash")
    rec.add_argument("--model")
    rec.add_argument("--reasoning")
    rec.add_argument("--parent-attempt")
    rec.add_argument("--response", help="saved local host response; required for completed")
    rec.add_argument("--response-sha256")

    stat_parser = sub.add_parser("status", help="derive a recovery action for one input hash")
    stat_parser.add_argument("--ledger", required=True)
    stat_parser.add_argument("--job-id", required=True)
    stat_parser.add_argument("--input-hash", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = init_ledger(args.ledger)
        elif args.command == "record":
            result = record(args.ledger, job_id=args.job_id, attempt_id=args.attempt_id,
                            status=args.status, receipt=args.receipt, receipt_sha256=args.receipt_sha256,
                            input_hash=args.input_hash, model=args.model, reasoning=args.reasoning,
                            parent_attempt=args.parent_attempt, response=args.response,
                            response_sha256=args.response_sha256)
        else:
            result = status(args.ledger, job_id=args.job_id, input_hash=args.input_hash)
    except (LedgerError, FileExistsError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    _print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
