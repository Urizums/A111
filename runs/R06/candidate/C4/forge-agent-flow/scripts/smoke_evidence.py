#!/usr/bin/env python3
"""Inspect explicitly bound smoke evidence files using small declarative checks.

This module does not execute commands, fetch URLs, authenticate evidence sources,
or decide whether a product experience is good. It checks local file identity,
format, run binding, and author-declared literal assertions.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
from typing import Any

import flowctl

MANIFEST_SCHEMA = "smoke-evidence-manifest/1"
CLAIM_SCOPE = "structure_binding_plus_declared_content_checks_no_execution_authentication"
CLAIM_LIMIT = (
    "Combines smokecheck structure and candidate binding with local file hashes, "
    "format checks, exact run bindings, and declared literal assertions. It does "
    "not authenticate evidence producers, prove that software actually ran, "
    "establish truthful observations, or judge UX quality."
)
MAX_EVIDENCE_BYTES = 4 * 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_MEDIA_TYPES = {"text/plain", "application/json"}
_MANIFEST_KEYS = {"schema", "plan_hash", "candidate_id", "baseline_id", "entries"}
_ENTRY_BASE_KEYS = {"ref", "purpose", "path", "sha256", "media_type", "candidate_id", "checks"}


class _EvidenceError(flowctl.FlowError):
    pass


def _pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _EvidenceError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_constant(value):
    raise _EvidenceError(f"non-finite JSON number {value}")


def _parse_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise _EvidenceError(f"non-finite JSON number {value}")
    return number


def _parse_json(data: bytes, label: str):
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except (UnicodeError, ValueError, OverflowError, RecursionError) as exc:
        raise _EvidenceError(f"{label}: invalid JSON: {exc}") from exc


def _load_manifest(manifest, root):
    if isinstance(manifest, (str, os.PathLike)):
        path = Path(manifest)
        try:
            controlled_root = path.parent.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise _EvidenceError(f"cannot read evidence manifest {path}: {exc}") from exc
        try:
            raw = _read_regular_file(controlled_root, path.name)
        except (OSError, _EvidenceError) as exc:
            raise _EvidenceError(f"cannot safely read evidence manifest {path}: {exc}") from exc
        return _parse_json(raw, f"evidence manifest {path}"), controlled_root, hashlib.sha256(raw).hexdigest()
    if type(manifest) is dict:
        controlled_root = Path(root if root is not None else Path.cwd())
        try:
            controlled_root = controlled_root.resolve(strict=True)
            canonical = json.dumps(
                manifest, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            ).encode("utf-8")
        except (OSError, RuntimeError, TypeError, ValueError, UnicodeError) as exc:
            raise _EvidenceError(f"cannot canonicalize in-memory evidence manifest: {exc}") from exc
        return manifest, controlled_root, hashlib.sha256(canonical).hexdigest()
    raise _EvidenceError("evidence manifest must be a file path or object")


def _is_nonempty_text(value):
    return type(value) is str and bool(value.strip())


def _exact_keys(value, keys, label, errors):
    missing = sorted(keys - value.keys())
    extra = sorted((repr(k) for k in value if type(k) is not str or k not in keys))
    if missing:
        errors.append(f"{label}: missing key(s): {', '.join(missing)}")
    if extra:
        errors.append(f"{label}: unexpected key(s): {', '.join(extra)}")


def _json_scalar(value):
    if value is None or type(value) in (str, bool, int):
        return True
    return type(value) is float and math.isfinite(value)


def _field_parts(field):
    if type(field) is not str or not field or any(not part for part in field.split(".")):
        return None
    return field.split(".")


def _validate_manifest_shape(manifest):
    errors = []
    if type(manifest) is not dict:
        raise _EvidenceError("evidence manifest must be an object")
    _exact_keys(manifest, _MANIFEST_KEYS, "manifest", errors)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append(f"manifest.schema: must equal {MANIFEST_SCHEMA!r}")
    if not _is_nonempty_text(manifest.get("plan_hash")) or _SHA256.fullmatch(manifest.get("plan_hash", "")) is None:
        errors.append("manifest.plan_hash: must be a lowercase SHA-256 digest")
    for key in ("candidate_id", "baseline_id"):
        if not _is_nonempty_text(manifest.get(key)):
            errors.append(f"manifest.{key}: must be nonempty text")

    entries = manifest.get("entries")
    if type(entries) is not list or not entries:
        errors.append("manifest.entries: must be a nonempty array")
        entries = []
    seen_refs = set()
    seen_paths = set()
    seen_hashes = set()
    for index, entry in enumerate(entries):
        label = f"manifest.entries[{index}]"
        if type(entry) is not dict:
            errors.append(f"{label}: must be an object")
            continue
        purpose = entry.get("purpose")
        binding_key = "journey_id" if purpose == "run" else "behavior_id" if purpose == "regression" else None
        if binding_key == "journey_id":
            keys = _ENTRY_BASE_KEYS | {"journey_id", "round"}
        elif binding_key == "behavior_id":
            keys = _ENTRY_BASE_KEYS | {"behavior_id"}
        else:
            keys = _ENTRY_BASE_KEYS | {"journey_id", "round"}
            errors.append(f"{label}.purpose: must be 'run' or 'regression'")
        _exact_keys(entry, keys, label, errors)
        ref = entry.get("ref")
        if not _is_nonempty_text(ref) or len(ref) > 2048:
            errors.append(f"{label}.ref: must be nonempty text of at most 2048 characters")
        elif ref in seen_refs:
            errors.append(f"{label}.ref: duplicate evidence reference")
        else:
            seen_refs.add(ref)
        if not _is_nonempty_text(entry.get("path")):
            errors.append(f"{label}.path: must be nonempty relative path text")
        elif entry["path"].startswith("/") or "\\" in entry["path"] or "\x00" in entry["path"]:
            errors.append(f"{label}.path: must be a safe POSIX relative path")
        elif any(part in ("", ".", "..") for part in entry["path"].split("/")):
            errors.append(f"{label}.path: empty, '.' and '..' path components are forbidden")
        elif entry["path"] in seen_paths:
            errors.append(f"{label}.path: evidence files cannot be reused across references")
        else:
            seen_paths.add(entry["path"])
        digest = entry.get("sha256")
        if type(digest) is not str or _SHA256.fullmatch(digest) is None:
            errors.append(f"{label}.sha256: must be a lowercase SHA-256 digest")
        elif digest in seen_hashes:
            errors.append(f"{label}.sha256: identical evidence content cannot be reused across references")
        else:
            seen_hashes.add(digest)
        if type(entry.get("media_type")) is not str or entry.get("media_type") not in _MEDIA_TYPES:
            errors.append(f"{label}.media_type: supported values are {sorted(_MEDIA_TYPES)}")
        if not _is_nonempty_text(entry.get("candidate_id")):
            errors.append(f"{label}.candidate_id: must be nonempty text")
        if binding_key == "journey_id":
            if type(entry.get("journey_id")) is not str or _SAFE_ID.fullmatch(entry["journey_id"]) is None:
                errors.append(f"{label}.journey_id: must be a lowercase identifier")
            if type(entry.get("round")) is not int or entry["round"] < 1:
                errors.append(f"{label}.round: must be a positive integer")
        elif binding_key == "behavior_id":
            if type(entry.get("behavior_id")) is not str or _SAFE_ID.fullmatch(entry["behavior_id"]) is None:
                errors.append(f"{label}.behavior_id: must be a lowercase identifier")

        checks = entry.get("checks")
        if type(checks) is not list or not checks:
            errors.append(f"{label}.checks: must be a nonempty array")
            continue
        if entry.get("media_type") == "text/plain":
            binding_checks = 0
            content_checks = 0
            for check_index, check in enumerate(checks):
                check_label = f"{label}.checks[{check_index}]"
                if type(check) is not dict:
                    errors.append(f"{check_label}: must be an object")
                elif check.get("kind") == "contains_binding":
                    _exact_keys(check, {"kind"}, check_label, errors)
                    binding_checks += 1
                elif check.get("kind") == "contains":
                    _exact_keys(check, {"kind", "value"}, check_label, errors)
                    if not _is_nonempty_text(check.get("value")):
                        errors.append(f"{check_label}.value: must be nonempty text")
                    content_checks += 1
                else:
                    errors.append(f"{check_label}.kind: text checks are 'contains_binding' or 'contains'")
            if binding_checks != 1:
                errors.append(f"{label}.checks: require exactly one contains_binding check")
            if not content_checks:
                errors.append(f"{label}.checks: require at least one literal contains assertion")
        elif entry.get("media_type") == "application/json":
            if any(type(check) is not dict or check.get("kind") != "json_equals" for check in checks):
                errors.append(f"{label}.checks: JSON checks must use json_equals")
            for check_index, check in enumerate(checks):
                if type(check) is not dict:
                    continue
                check_label = f"{label}.checks[{check_index}]"
                _exact_keys(check, {"kind", "field", "value"}, check_label, errors)
                if _field_parts(check.get("field")) is None:
                    errors.append(f"{check_label}.field: must be a dotted object-field path")
                if not _json_scalar(check.get("value")):
                    errors.append(f"{check_label}.value: must be a JSON scalar")
    if errors:
        raise _EvidenceError("Invalid smoke evidence manifest: " + "; ".join(errors))
    return entries


def _result_bindings(runs, regressions):
    bindings = []
    refs = []
    for run_index, run in enumerate(runs):
        for ref in run["evidence"]:
            refs.append(ref)
            bindings.append({
                "ref": ref,
                "purpose": "run",
                "candidate_id": run["candidate_id"],
                "journey_id": run["journey_id"],
                "round": run["round"],
                "record": f"runs[{run_index}]",
            })
    for regression_index, regression in enumerate(regressions):
        for ref in regression["evidence"]:
            refs.append(ref)
            bindings.append({
                "ref": ref,
                "purpose": "regression",
                "candidate_id": regression["candidate_id"],
                "behavior_id": regression["behavior_id"],
                "record": f"regressions[{regression_index}]",
            })
    return refs, bindings


def _read_regular_file(root: Path, relative_path: str) -> bytes:
    """Open a relative regular file without following symlinks in any component."""
    if (
        type(relative_path) is not str
        or not relative_path
        or relative_path.startswith("/")
        or "\\" in relative_path
        or "\x00" in relative_path
        or any(part in ("", ".", "..") for part in relative_path.split("/"))
    ):
        raise _EvidenceError("path must be a safe POSIX relative path")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None or not hasattr(os, "open"):
        raise _EvidenceError("this platform lacks safe no-follow file opening")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    root_fd = os.open(root, flags | directory | nofollow)
    current_fd = root_fd
    try:
        parts = relative_path.split("/")
        for part in parts[:-1]:
            next_fd = os.open(part, flags | directory | nofollow, dir_fd=current_fd)
            if current_fd != root_fd:
                os.close(current_fd)
            current_fd = next_fd
        file_fd = os.open(
            parts[-1],
            flags | nofollow | getattr(os, "O_NONBLOCK", 0),
            dir_fd=current_fd,
        )
        try:
            metadata = os.fstat(file_fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise _EvidenceError("evidence path is not a regular file")
            if metadata.st_size <= 0:
                raise _EvidenceError("evidence file is empty")
            if metadata.st_size > MAX_EVIDENCE_BYTES:
                raise _EvidenceError(f"evidence file exceeds {MAX_EVIDENCE_BYTES} bytes")
            chunks = bytearray()
            while len(chunks) <= MAX_EVIDENCE_BYTES:
                chunk = os.read(file_fd, min(65536, MAX_EVIDENCE_BYTES + 1 - len(chunks)))
                if not chunk:
                    break
                chunks.extend(chunk)
            if len(chunks) > MAX_EVIDENCE_BYTES:
                raise _EvidenceError(f"evidence file exceeds {MAX_EVIDENCE_BYTES} bytes")
            if not chunks:
                raise _EvidenceError("evidence file is empty")
            return bytes(chunks)
        finally:
            os.close(file_fd)
    finally:
        if current_fd != root_fd:
            os.close(current_fd)
        os.close(root_fd)


def _binding_marker(entry):
    if entry["purpose"] == "run":
        return f"smoke-run:{entry['candidate_id']}:{entry['journey_id']}:round-{entry['round']}"
    return f"smoke-regression:{entry['candidate_id']}:{entry['behavior_id']}"


def _field_value(value, field):
    current = value
    for part in _field_parts(field) or ():
        if type(current) is not dict or part not in current:
            return False, None
        current = current[part]
    return True, current


def _same_json_value(actual, expected):
    return type(actual) is type(expected) and actual == expected


def _inspect_entry(entry, root):
    """Return entry result and whether all content assertions were evaluated."""
    result = {"ref": entry["ref"], "purpose": entry["purpose"], "path": entry["path"], "status": "invalid", "checks": []}
    try:
        content = _read_regular_file(root, entry["path"])
    except (OSError, _EvidenceError) as exc:
        result["reasons"] = [f"cannot safely read evidence file: {exc}"]
        return result, False, "invalid"
    actual_hash = hashlib.sha256(content).hexdigest()
    result["sha256"] = actual_hash
    if actual_hash != entry["sha256"]:
        result["reasons"] = ["evidence SHA-256 does not match manifest"]
        return result, False, "invalid"

    assertion_errors = []
    if entry["media_type"] == "text/plain":
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            result["reasons"] = [f"text/plain evidence is not valid UTF-8: {exc}"]
            return result, False, "invalid"
        if not text.strip():
            result["reasons"] = ["text/plain evidence is empty"]
            return result, False, "invalid"
        binding_marker = _binding_marker(entry)
        for index, check in enumerate(entry["checks"]):
            if check["kind"] == "contains_binding":
                passed = binding_marker in text.splitlines()
                label = "contains current run binding" if entry["purpose"] == "run" else "contains current regression binding"
            else:
                passed = check["value"] in text
                label = f"contains {check['value']!r}"
            result["checks"].append({"index": index, "assertion": label, "status": "pass" if passed else "fail"})
            if not passed:
                assertion_errors.append(f"text check {index} did not match")
    else:
        try:
            document = _parse_json(content, f"evidence {entry['path']}")
        except _EvidenceError as exc:
            result["reasons"] = [str(exc)]
            return result, False, "invalid"
        if type(document) is not dict or not document:
            result["reasons"] = ["application/json evidence must be a nonempty object"]
            return result, False, "invalid"
        binding_fields = {"candidate_id": entry["candidate_id"]}
        if entry["purpose"] == "run":
            binding_fields.update({"journey_id": entry["journey_id"], "round": entry["round"]})
        else:
            binding_fields["behavior_id"] = entry["behavior_id"]
        for field, expected in binding_fields.items():
            actual = document.get(field, object())
            passed = _same_json_value(actual, expected)
            result["checks"].append({
                "assertion": f"binding field {field} equals {expected!r}",
                "status": "pass" if passed else "fail",
            })
            if not passed:
                assertion_errors.append(f"JSON binding field {field} does not match")
        for index, check in enumerate(entry["checks"]):
            present, actual = _field_value(document, check["field"])
            passed = present and _same_json_value(actual, check["value"])
            result["checks"].append({
                "index": index,
                "assertion": f"JSON field {check['field']} equals {check['value']!r}",
                "status": "pass" if passed else "fail",
            })
            if not passed:
                assertion_errors.append(f"JSON check {index} did not match")
    if assertion_errors:
        result["status"] = "fail"
        result["reasons"] = assertion_errors
        return result, True, "fail"
    result["status"] = "pass"
    result["reasons"] = []
    return result, True, "pass"


def _report(status, base, manifest_hash, content_checked, content_status, entries, reasons):
    combined_status = status
    base_status = base["status"]
    if content_status == "invalid" or base_status == "invalid":
        combined_status = "invalid"
    elif content_status == "fail" or base_status == "fail":
        combined_status = "fail"
    elif base_status == "unverified":
        combined_status = "unverified"
    else:
        combined_status = "pass"
    return {
        "status": combined_status,
        "claim_scope": CLAIM_SCOPE,
        "claim_limit": CLAIM_LIMIT,
        "plan_hash": base.get("plan_hash"),
        "candidate_id": base.get("candidate_id"),
        "structure_assessment": base,
        "content_checked": content_checked,
        "content_status": content_status,
        "evidence_manifest_sha256": manifest_hash,
        "evidence_entries": entries,
        "reasons": reasons,
    }


def assess(plan, results, manifest, root=None):
    """Combine the v1 structure gate with complete local content inspection.

    ``manifest`` may be a manifest path. Its parent directory is then the
    controlled evidence root. For an in-memory manifest, ``root`` selects the
    controlled root and otherwise defaults to the current directory.
    """
    import smokecheck

    base = smokecheck.assess(plan, results)
    try:
        manifest_data, evidence_root, manifest_hash = _load_manifest(manifest, root)
        entries = _validate_manifest_shape(manifest_data)
    except _EvidenceError as exc:
        return _report(
            "invalid", base, None, False, "invalid", [], [str(exc)],
        )

    expected_plan_hash = flowctl.digest(plan)
    header_errors = []
    expected_header = {
        "plan_hash": expected_plan_hash,
        "candidate_id": plan["candidate_id"],
        "baseline_id": plan["baseline"]["id"],
    }
    for field, expected in expected_header.items():
        if manifest_data[field] != expected:
            header_errors.append(f"manifest.{field} does not match the supplied plan")
    if manifest_data["candidate_id"] != results["candidate_id"]:
        header_errors.append("manifest.candidate_id does not match results.candidate_id")
    if manifest_data["baseline_id"] != results["baseline_id"]:
        header_errors.append("manifest.baseline_id does not match results.baseline_id")

    runs, regressions = smokecheck._validate_results(plan, results)
    result_refs, bindings = _result_bindings(runs, regressions)
    manifest_refs = [entry["ref"] for entry in entries]
    result_counts = Counter(result_refs)
    manifest_counts = Counter(manifest_refs)
    reused = sorted(ref for ref, count in result_counts.items() if count != 1)
    if reused:
        header_errors.append("results evidence refs must appear exactly once; reused refs: " + ", ".join(repr(ref) for ref in reused))
    missing = sorted((result_counts - manifest_counts).elements())
    extra = sorted((manifest_counts - result_counts).elements())
    if missing:
        header_errors.append("manifest does not cover results evidence ref(s): " + ", ".join(repr(ref) for ref in missing))
    if extra:
        header_errors.append("manifest has unused evidence ref(s): " + ", ".join(repr(ref) for ref in extra))

    by_ref = {entry["ref"]: entry for entry in entries}
    for binding in bindings:
        entry = by_ref.get(binding["ref"])
        if entry is None:
            continue
        for key in ("purpose", "candidate_id", "journey_id", "round", "behavior_id"):
            if key in binding and entry.get(key) != binding[key]:
                header_errors.append(
                    f"manifest entry for ref {binding['ref']!r} has mismatched {key} binding"
                )
    if header_errors:
        return _report("invalid", base, manifest_hash, False, "invalid", [], header_errors)

    reports = []
    content_states = []
    all_checked = True
    for entry in entries:
        entry_report, checked, state = _inspect_entry(entry, evidence_root)
        reports.append(entry_report)
        content_states.append(state)
        all_checked = all_checked and checked
    content_status = "invalid" if "invalid" in content_states else "fail" if "fail" in content_states else "pass"
    reasons = [
        f"{entry['ref']!r}: {reason}"
        for entry in reports
        for reason in entry.get("reasons", [])
    ]
    return _report(
        "pass", base, manifest_hash, all_checked, content_status, reports, reasons,
    )


__all__ = ["MANIFEST_SCHEMA", "CLAIM_SCOPE", "CLAIM_LIMIT", "MAX_EVIDENCE_BYTES", "assess"]
