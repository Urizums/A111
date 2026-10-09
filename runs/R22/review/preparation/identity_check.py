"""Read-only identity check for the sources authorized for R22 reception prep.

This does not inspect scientific result files or execute a policy/model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PROTOCOL_LOCK = ROOT / "runs/R22/protocol-lock.json"
INPUT_LOCK = ROOT / "runs/R21/input-lock.json"
EXECUTION_LOCK = ROOT / "runs/R21/execution-lock.json"
PROSPECTIVE = ROOT / "runs/R21/execution/prospective-freeze.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def locked_identity(path: Path, entry: dict) -> dict:
    actual_size = path.stat().st_size
    actual_sha = sha256(path)
    expected = (entry.get("size_bytes"), entry.get("sha256"))
    actual = (actual_size, actual_sha)
    if expected != actual:
        raise SystemExit(f"identity mismatch: {entry['path']}")
    return {"path": entry["path"], "size_bytes": actual_size, "sha256": actual_sha}


def is_authorized_execution_source(path: str) -> bool:
    if path in {
        "runs/R21/execution/source/v1/config.json",
        "runs/R21/execution/source/v1/reference_policy.py",
        "runs/R21/execution/source/v1/run_science.py",
        "runs/R21/execution/prospective-freeze.json",
        "runs/R21/execution/science-v1/uncertainty/residual_coordinates_all.csv",
    }:
        return True
    if path.startswith("runs/R21/execution/science-v1/data/"):
        leaf = path.rsplit("/", 1)[-1]
        return leaf.startswith(("train_", "train_features_", "predict_features_", "promotion_imputation_sources_")) and leaf.endswith(".csv")
    if path.startswith("runs/R21/execution/science-v1/models/"):
        leaf = path.rsplit("/", 1)[-1]
        return leaf.startswith("coefficients_") and leaf.endswith(".json")
    return False


def main() -> None:
    protocol = json_file(PROTOCOL_LOCK)
    inputs = json_file(INPUT_LOCK)
    execution = json_file(EXECUTION_LOCK)

    protocol_files = [locked_identity(ROOT / item["path"], item) for item in protocol["files"]]
    input_files = [locked_identity(ROOT / item["path"], item) for item in inputs["files"]]
    authorized = [item for item in execution["files"] if is_authorized_execution_source(item["path"])]
    if len(authorized) != sum(is_authorized_execution_source(item["path"]) for item in execution["files"]):
        raise SystemExit("unreachable filter inconsistency")
    execution_files = [locked_identity(ROOT / item["path"], item) for item in authorized]

    # The prospective freeze is a separately authorized source. Its own locked
    # identity is checked when present in the execution lock; the content is
    # never used as a scientific answer key.
    prospective_entry = next((item for item in execution["files"] if item["path"] == "runs/R21/execution/prospective-freeze.json"), None)
    if prospective_entry is None:
        raise SystemExit("prospective-freeze.json missing from execution identity lock")
    prospective = locked_identity(PROSPECTIVE, prospective_entry)
    preparation_files = []
    for path in (Path(__file__).resolve(), Path(__file__).with_name("plan.md")):
        preparation_files.append({
            "path": path.relative_to(ROOT).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        })

    print(json.dumps({
        "schema": "r22-preparation-identities/1",
        "protocol_lock": protocol_files,
        "input_lock": input_files,
        "authorized_execution_sources": execution_files,
        "prospective_freeze": prospective,
        "preparation_source_identities": preparation_files,
        "claim": "read-only identity verification only; no scientific production, scoring, or acceptance judgment",
        "model": None,
        "tokens": None,
        "cost": None,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
