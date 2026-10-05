#!/usr/bin/env python3
"""Conservative local material identity and source/binary binding gate.

This checks declared files and hashes; it does not authenticate who created an
artifact or prove that a declared source snapshot is complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path


MANIFEST_SCHEMA = "forge-materials/1"
PROVENANCE_SCHEMA = "forge-provenance/1"
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
ALL_OPERATIONS = ["inspect", "design", "modify"]
DESIGN_OPERATIONS = ["inspect", "design"]
CLAIM_SCOPE = "local_material_integrity_and_declared_binding_only"
CLAIM_LIMIT = (
    "Verifies manifest structure, regular-file SHA-256 values, and declared source/binary "
    "fingerprint binding. It does not authenticate the producer or authority, prove the "
    "declared snapshot is complete, establish runtime readiness, or authorize external writes."
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ARCHIVE_SUFFIXES = (
    ".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst", ".gitbundle", ".zip",
    ".tar", ".tgz", ".tbz2", ".txz", ".tzst", ".7z", ".bundle",
)
_MANIFEST_KEYS = {"schema", "intent", "source", "binary", "references", "provenance"}
_SOURCE_KEYS = {"path", "sha256", "role", "identity", "stack", "platform", "fingerprint_scope"}
_BINARY_KEYS = {"path", "sha256", "role", "identity", "stack", "platform"}
_REFERENCE_KEYS = _BINARY_KEYS
_PROVENANCE_REF_KEYS = {"path", "sha256"}
_PROVENANCE_KEYS = {"schema", "kind", "source_sha256", "binary_sha256", "issuer"}


class MaterialError(ValueError):
    """Raised when a manifest or one of its declared files is structurally invalid."""


class _DuplicateKey(ValueError):
    pass


def _object_without_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"non-JSON numeric constant {value!r}")


def _json_load(data, label):
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, _DuplicateKey, ValueError, RecursionError) as exc:
        raise MaterialError(f"{label}: invalid JSON: {exc}") from exc


def _canonical_bytes(value):
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise MaterialError(f"manifest: cannot canonicalize JSON value: {exc}") from exc


def _text(value, label, errors):
    if type(value) is not str or not value.strip() or len(value) > 512:
        errors.append(f"{label}: must be nonempty text of at most 512 characters")
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        errors.append(f"{label}: must contain valid Unicode text")
        return False
    return True


def _exact_keys(value, expected, label, errors):
    if type(value) is not dict:
        errors.append(f"{label}: must be an object")
        return False
    missing = sorted(expected - set(value))
    extra = sorted((key for key in value if type(key) is str and key not in expected), key=str)
    invalid_keys = [key for key in value if type(key) is not str]
    if missing:
        errors.append(f"{label}: missing field(s): {', '.join(missing)}")
    if extra:
        errors.append(f"{label}: unexpected field(s): {', '.join(extra)}")
    if invalid_keys:
        errors.append(f"{label}: object keys must be strings")
    return not missing and not extra and not invalid_keys


def _safe_relative_path(value, label, base, errors):
    if not _text(value, label, errors):
        return None
    if "\\" in value or "\x00" in value:
        errors.append(f"{label}: use a relative POSIX path")
        return None
    relative = Path(value)
    if relative.is_absolute():
        errors.append(f"{label}: must be relative to the manifest directory")
        return None
    root = base.resolve(strict=True)
    candidate = base / relative
    try:
        # Keep all material beneath the manifest directory and reject a symlink as
        # the final file; parent symlinks are safe only when they resolve inside it.
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        if stat.S_ISLNK(candidate.lstat().st_mode):
            raise OSError("final path is a symbolic link")
    except (OSError, RuntimeError, ValueError) as exc:
        errors.append(f"{label}: cannot resolve safe regular file beneath manifest directory ({exc})")
        return None
    return resolved


def _read_regular(path, label, *, base=None, max_bytes=MAX_FILE_BYTES, collect=False):
    """Hash a bounded regular file without following a final-component symlink."""
    path = Path(path)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        fd = os.open(os.fspath(path), flags)
    except OSError as exc:
        raise MaterialError(f"{label}: cannot open regular file: {exc}") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise MaterialError(f"{label}: must be a regular file")
        if before.st_size > max_bytes:
            raise MaterialError(f"{label}: exceeds the {max_bytes}-byte size limit")
        digest = hashlib.sha256()
        content = bytearray() if collect else None
        total = 0
        while True:
            chunk = os.read(fd, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise MaterialError(f"{label}: exceeds the {max_bytes}-byte size limit")
            digest.update(chunk)
            if content is not None:
                content.extend(chunk)
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        ) or total != after.st_size:
            raise MaterialError(f"{label}: file changed while it was being checked")
        return digest.hexdigest(), bytes(content) if content is not None else None
    finally:
        os.close(fd)


def _load_input(value):
    if isinstance(value, (str, os.PathLike)):
        manifest_path = Path(value)
        if not manifest_path.is_absolute():
            manifest_path = Path.cwd() / manifest_path
        digest, raw = _read_regular(
            manifest_path, "manifest", max_bytes=MAX_MANIFEST_BYTES, collect=True
        )
        manifest = _json_load(raw, "manifest")
        if type(manifest) is not dict:
            raise MaterialError("manifest: root must be an object")
        base = manifest_path.parent.resolve(strict=True)
        return manifest, base, digest
    if type(value) is dict:
        raw = _canonical_bytes(value)
        if len(raw) > MAX_MANIFEST_BYTES:
            raise MaterialError("manifest: exceeds the 2 MiB size limit")
        return value, Path.cwd().resolve(strict=True), hashlib.sha256(raw).hexdigest()
    raise MaterialError("manifest: input must be a filesystem path or object")


def _check_sha(value, label, errors):
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        errors.append(f"{label}: must be a lowercase 64-character SHA-256 hex digest")
        return False
    return True


def _check_artifact(obj, expected_keys, role, label, base, errors, *, source=False):
    if not _exact_keys(obj, expected_keys, label, errors):
        if type(obj) is not dict:
            return None
    if obj.get("role") != role:
        errors.append(f"{label}.role: must equal {role!r}")
    for field in ("identity", "stack", "platform"):
        _text(obj.get(field), f"{label}.{field}", errors)
    expected_hash_ok = _check_sha(obj.get("sha256"), f"{label}.sha256", errors)
    if source:
        if obj.get("fingerprint_scope") != "complete_source_snapshot":
            errors.append(f"{label}.fingerprint_scope: must be 'complete_source_snapshot'")
        source_path = obj.get("path")
        if type(source_path) is str:
            lowered = source_path.lower()
            if not lowered.endswith(_ARCHIVE_SUFFIXES):
                errors.append(
                    f"{label}.path: target source fingerprint must use a fixed archive file "
                    f"({', '.join(_ARCHIVE_SUFFIXES)})"
                )
    resolved_path = _safe_relative_path(obj.get("path"), f"{label}.path", base, errors)
    actual_hash = None
    if resolved_path is not None:
        try:
            actual_hash, _ = _read_regular(resolved_path, f"{label}.path")
            if expected_hash_ok and actual_hash != obj.get("sha256"):
                errors.append(f"{label}.sha256: does not match the actual file")
        except MaterialError as exc:
            errors.append(str(exc))
    return actual_hash


def _validate(manifest, base):
    errors = []
    if not _exact_keys(manifest, _MANIFEST_KEYS, "manifest", errors):
        return errors, {}
    if manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append(f"manifest.schema: must equal {MANIFEST_SCHEMA!r}")
    intent = manifest.get("intent")
    if intent not in ("source_only", "binary_source"):
        errors.append("manifest.intent: must be 'source_only' or 'binary_source'")

    source_hash = _check_artifact(
        manifest.get("source"), _SOURCE_KEYS, "target_source", "manifest.source", base,
        errors, source=True,
    )
    binary_hash = None
    if intent == "source_only":
        if manifest.get("binary") is not None:
            errors.append("manifest.binary: must be null for source_only intent")
        if manifest.get("provenance") is not None:
            errors.append("manifest.provenance: must be null for source_only intent")
    elif intent == "binary_source":
        binary_hash = _check_artifact(
            manifest.get("binary"), _BINARY_KEYS, "target_binary", "manifest.binary", base,
            errors,
        )
    elif manifest.get("binary") is not None or manifest.get("provenance") is not None:
        errors.append("manifest.binary and manifest.provenance must be null for an unknown intent")

    references = manifest.get("references")
    if type(references) is not list:
        errors.append("manifest.references: must be an array")
    else:
        for index, reference in enumerate(references):
            label = f"manifest.references[{index}]"
            role = reference.get("role") if type(reference) is dict else None
            if role not in ("reference_source", "reference_binary", "visual_inspiration"):
                errors.append(f"{label}.role: must be reference_source, reference_binary, or visual_inspiration")
                continue
            _check_artifact(reference, _REFERENCE_KEYS, role, label, base, errors)

    provenance = manifest.get("provenance")
    provenance_hash = None
    provenance_data = None
    if intent == "binary_source" and provenance is not None:
        if _exact_keys(provenance, _PROVENANCE_REF_KEYS, "manifest.provenance", errors):
            hash_ok = _check_sha(provenance.get("sha256"), "manifest.provenance.sha256", errors)
            path = _safe_relative_path(provenance.get("path"), "manifest.provenance.path", base, errors)
            if path is not None:
                try:
                    provenance_hash, provenance_data = _read_regular(
                        path, "manifest.provenance.path", collect=True
                    )
                    if hash_ok and provenance_hash != provenance.get("sha256"):
                        errors.append("manifest.provenance.sha256: does not match the actual file")
                except MaterialError as exc:
                    errors.append(str(exc))

    details = {
        "source": source_hash,
        "binary": binary_hash,
        "provenance": provenance_hash,
        "provenance_data": provenance_data,
    }
    return errors, details


def require_valid(path_or_dict):
    """Validate manifest structure and all declared file hashes.

    Returns the loaded manifest. Raises MaterialError if its schema is malformed,
    a referenced file is unsafe/unavailable, or a declared hash has drifted.
    A structurally valid manifest may still lack source/binary relationship proof;
    use :func:`assess` to decide whether modification is allowed.
    """
    manifest, base, _ = _load_input(path_or_dict)
    errors, _ = _validate(manifest, base)
    if errors:
        raise MaterialError("Invalid material manifest: " + "; ".join(errors))
    return manifest


def _provenance_binds(data, source_hash, binary_hash):
    """Return whether a hashed evidence file structurally binds both artifacts."""
    if data is None:
        return False, "provenance evidence is unavailable"
    try:
        record = _json_load(data, "provenance evidence")
    except MaterialError as exc:
        return False, str(exc)
    if type(record) is not dict or set(record) != _PROVENANCE_KEYS:
        return False, "provenance evidence has an invalid structure"
    if record.get("schema") != PROVENANCE_SCHEMA:
        return False, f"provenance evidence schema must equal {PROVENANCE_SCHEMA!r}"
    if record.get("kind") not in ("build_provenance", "authoritative_record"):
        return False, "provenance evidence kind is unrecognized"
    if not _text(record.get("issuer"), "provenance evidence.issuer", []):
        return False, "provenance evidence issuer is missing"
    if record.get("source_sha256") != source_hash or record.get("binary_sha256") != binary_hash:
        return False, "provenance evidence does not bind the actual source and binary fingerprints"
    return True, None


def _identity_blockers(manifest):
    blockers = []
    source = manifest["source"]
    binary = manifest["binary"]
    for field, label in (("identity", "application identity"), ("stack", "stack"), ("platform", "platform")):
        source_value = source[field].strip()
        binary_value = binary[field].strip()
        if source_value.casefold() == "unknown" or binary_value.casefold() == "unknown":
            blockers.append(f"{label} is unknown for source or binary")
        elif source_value != binary_value:
            blockers.append(f"source and binary {label} conflict")
    return blockers


def _invalid_report(manifest_hash, errors):
    return {
        "valid": False,
        "status": "invalid",
        "manifest_sha256": manifest_hash,
        "claim_scope": CLAIM_SCOPE,
        "allowed_operations": [],
        "blockers": errors,
        "claim_limit": CLAIM_LIMIT,
        "material_sha256": {"source": None, "binary": None, "provenance": None},
    }


def assess(path_or_dict):
    """Return a fail-closed operation assessment for a manifest path or object."""
    try:
        manifest, base, manifest_hash = _load_input(path_or_dict)
    except (MaterialError, OSError, ValueError, RecursionError) as exc:
        return _invalid_report(None, [str(exc)])
    errors, details = _validate(manifest, base)
    material_hashes = {key: details.get(key) for key in ("source", "binary", "provenance")}
    if errors:
        report = _invalid_report(manifest_hash, errors)
        report["material_sha256"] = material_hashes
        return report

    blockers = []
    allowed = list(ALL_OPERATIONS)
    if manifest["intent"] == "binary_source":
        blockers.extend(_identity_blockers(manifest))
        provenance = manifest.get("provenance")
        if provenance is None:
            bound, reason = False, "no build provenance or authoritative record was supplied"
        else:
            bound, reason = _provenance_binds(
                details.get("provenance_data"), details.get("source"), details.get("binary")
            )
        if not bound:
            blockers.append(reason or "source/binary relationship is unresolved")
        if blockers:
            allowed = list(DESIGN_OPERATIONS)

    status = "pass" if "modify" in allowed else "blocked"
    return {
        "valid": True,
        "status": status,
        "manifest_sha256": manifest_hash,
        "claim_scope": CLAIM_SCOPE,
        "allowed_operations": allowed,
        "blockers": blockers,
        "claim_limit": CLAIM_LIMIT,
        "material_sha256": material_hashes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check material identity and source/binary binding")
    parser.add_argument("manifest", help="forge-materials/1 manifest JSON")
    args = parser.parse_args(argv)
    report = assess(args.manifest)
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report["valid"] and "modify" in report["allowed_operations"] else 2


if __name__ == "__main__":
    sys.exit(main())
