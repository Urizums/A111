#!/usr/bin/env python3
"""Create and inspect an allowlisted R24 handoff packet.

An explicit file transfer boundary, not a security sandbox or independent review.
The receiving host must still control context, history, commands and permissions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

PUBLIC = ("brief.md", "consumer.md", "invoices.json", "amendments.json", "payments.json")
OUTPUTS = ("ledger.csv", "suppliers.csv", "workflow.md")
ALLOW = tuple(f"input/{name}" for name in PUBLIC) + tuple(f"output/{name}" for name in OUTPUTS)
MAX_BYTES = 2 * 1024 * 1024
INSTRUCTION = """# Cold-start receiving task

You are receiving another worker's output. You have not been given their diagnoses,
private scoring data or prior verdicts. Read input/brief.md and input/consumer.md
first, then review the original input JSON files, output CSVs and output/workflow.md.

Attempt to reproduce the business result from the workflow explanation and the
original sources. Report where the method is unclear or incomplete and whether
all original obligations are met. Preserve failed or unexpected findings.

Do not infer success from the existence of this packet or a passing SHA check.
The packet manifest only proves local bytes were copied consistently. A real
independence claim needs host-enforced control of other visible channels.
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_bytes(root: Path, filename: str) -> bytes:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("source directory missing or symbolic link")
    path = root / filename
    if path.is_symlink():
        raise ValueError(f"refuse symbolic link: {filename}")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
        raise ValueError(f"refuse non-regular/oversize source: {filename}")
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise ValueError(f"source grew during read: {filename}")
    if filename.endswith(".md"):
        text = data.decode("utf-8")
        if not text.strip() or "\ufffd" in text:
            raise ValueError(f"empty or invalid prose: {filename}")
    return data


def build(public: Path, outputs: Path, destination: Path, frozen: dict | None = None) -> dict:
    """Copy only original task materials and artifacts. No directory recursion."""
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"receiver packet already exists: {destination}")
    material = {f"input/{n}": safe_bytes(public, n) for n in PUBLIC}
    material.update({f"output/{n}": safe_bytes(outputs, n) for n in OUTPUTS})
    if frozen is not None:
        expected = frozen.get("source_sha256", {})
        if set(expected) != set(PUBLIC):
            raise ValueError("frozen source identity list not equivalent to public source list")
        for n in PUBLIC:
            if sha(material[f"input/{n}"]) != expected[n]:
                raise ValueError(f"public source differs from frozen flow: {n}")
    # No oracle, author diagnostics, previous tests, internal agent logs, or local absolute paths.
    manifest = {
        "schema": "forge-r24-receiver-packet/1",
        "files": {n: {"sha256": sha(v), "bytes": len(v)} for n, v in sorted(material.items())},
        "status": "ready_for_a_separate_receiver_not_yet_accepted",
        "limitations": "Directory allowlist is not process or context isolation; in-band contents are not semantically audited",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".r24-packet-", dir=destination.parent) as temp:
        staging = Path(temp) / "prepared"
        staging.mkdir()
        for name, contents in material.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(contents)
        (staging / "RECEIVE.md").write_text(INSTRUCTION, encoding="utf-8")
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        check = verify(staging)
        if not check["passed"]:
            raise ValueError(f"staging verification failed: {check['errors']}")
        # Refuse overwrites; publish as a new folder only. Races and permissions are host concerns.
        os.rename(staging, destination)
    return {"created": str(destination), "passed": True, "files": len(material), "ready_for_review": True,
            "independence_confirmed": False, "business_accepted": False}


def verify(folder: Path) -> dict:
    errors = []
    if not folder.is_dir() or folder.is_symlink():
        return {"passed": False, "errors": ["missing or symlinked packet directory"]}
    names = {str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file() or p.is_symlink()}
    required = set(ALLOW) | {"RECEIVE.md", "manifest.json"}
    for item in sorted(required - names):
        errors.append(f"missing packet file: {item}")
    for item in sorted(names - required):
        errors.append(f"unexpected file in receiver packet: {item}")
    for path in folder.rglob("*"):
        if path.is_symlink():
            errors.append(f"symlink in packet: {path.relative_to(folder)}")
    try:
        data = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if data.get("schema") != "forge-r24-receiver-packet/1":
            errors.append("unexpected manifest schema")
        if set(data) != {"schema", "files", "status", "limitations"} or data.get("status") != "ready_for_a_separate_receiver_not_yet_accepted":
            errors.append("manifest status or fields modified")
        if set(data.get("files", {})) != set(ALLOW):
            errors.append("manifest coverage differs from allowed materials")
        for name in ALLOW:
            try:
                source = safe_bytes(folder / name.split("/")[0], name.split("/")[1])
                item = data["files"][name]
                if sha(source) != item["sha256"] or len(source) != item["bytes"]:
                    errors.append(f"source mismatch in receiver packet: {name}")
            except (OSError, KeyError, TypeError, ValueError, UnicodeError) as exc:
                errors.append(f"cannot verify {name}: {exc}")
        if (folder / "RECEIVE.md").read_text(encoding="utf-8") != INSTRUCTION:
            errors.append("receiver instructions changed")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"cannot read packet manifest: {exc}")
    return {"passed": not errors, "errors": errors, "files_checked": len(ALLOW),
            "business_acceptance": "unverified", "receiver_independence": "unverified"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("build")
    a.add_argument("--public", type=Path, required=True)
    a.add_argument("--submission", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--flow-inputs", type=Path, help="Optional flow_builder inputs.json with frozen source identities")
    b = sub.add_parser("verify")
    b.add_argument("--packet", type=Path, required=True)
    args = p.parse_args()
    try:
        frozen = json.loads(args.flow_inputs.read_text(encoding="utf-8"))["source_bundle"] if args.command == "build" and args.flow_inputs else None
        result = build(args.public, args.submission, args.out, frozen) if args.command == "build" else verify(args.packet)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        result = {"passed": False, "errors": [f"{type(exc).__name__}: {exc}"]}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
