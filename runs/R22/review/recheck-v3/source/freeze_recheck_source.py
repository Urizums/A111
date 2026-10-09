"""Freeze allowed correction-v3 bytes and independent audit source by identity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "runs/R22/review/recheck-v3"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"path": path.relative_to(ROOT).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha(path)}


def main() -> None:
    doc_lock_path = ROOT / "runs/R22/document-correction-v3-lock.json"
    doc_lock = json.loads(doc_lock_path.read_text(encoding="utf-8"))
    doc_lock_checks = []
    for entry in doc_lock["files"]:
        path = ROOT / entry["path"]
        doc_lock_checks.append({"path": entry["path"], "size_matches": path.stat().st_size == entry["size_bytes"], "sha256_matches": sha(path) == entry["sha256"]})
    if not all(x["size_matches"] and x["sha256_matches"] for x in doc_lock_checks):
        raise SystemExit("correction-v3 lock byte identity mismatch")

    execution_path = ROOT / "runs/R22/execution-lock.json"
    execution_lock = json.loads(execution_path.read_text(encoding="utf-8"))
    science_entries = [x for x in execution_lock["files"] if x["path"].startswith("runs/R22/execution/science-v1/")]
    science_checks = [{"path": x["path"], "matches": (ROOT / x["path"]).stat().st_size == x["size_bytes"] and sha(ROOT / x["path"]) == x["sha256"]} for x in science_entries]
    if not all(x["matches"] for x in science_checks):
        raise SystemExit("initial science-v1 identity mismatch")

    initial_result = ROOT / "runs/R22/review/initial/result.json"
    initial_freeze = ROOT / "runs/R22/review/initial/source-freeze-v11.json"
    initial_result_obj = json.loads(initial_result.read_text(encoding="utf-8"))
    if initial_result_obj["criterion_statuses"] != {"h1": "pass", "h2": "pass", "h3": "pass", "h4": "pass", "h5": "pass", "h6": "fail"}:
        raise SystemExit("initial first-judgment status unexpectedly changed")
    old_freeze = json.loads(initial_freeze.read_text(encoding="utf-8"))
    if old_freeze["r22_execution_lock_sha256"] != sha(execution_path):
        raise SystemExit("initial h1-h5 carry identity does not bind current R22 execution lock")

    sources = [
        OUT / "PLAN.md",
        OUT / "source/audit_report_v3.py",
        OUT / "source/freeze_recheck_source.py",
        ROOT / "runs/R22/execution/correction-v3/source/build_report_v3.py",
        ROOT / "runs/R22/execution/correction-v3/report/REPORT.md",
        ROOT / "runs/R22/execution/correction-v3/report/REPORT.pdf",
        ROOT / "runs/R22/execution/correction-v3/report/document-data-bindings.json",
        ROOT / "runs/R21/inputs/raw/items.csv",
        ROOT / "runs/R21/input-lock.json",
        ROOT / "runs/R22/protocol/PROTOCOL.md",
        ROOT / "runs/R22/protocol/acceptance.json",
        ROOT / "runs/R22/protocol-lock.json",
        ROOT / "runs/R22/review/initial/result.json",
        ROOT / "runs/R22/review/initial/source-freeze-v11.json",
        ROOT / "runs/R22/review/initial/rebuild-v5/results/keys.csv",
        ROOT / "runs/R22/review/initial/rebuild-v5/results/origins.csv",
    ]
    sources.extend(sorted((ROOT / "runs/R22/execution/correction-v3/report/figures").glob("*.png")))
    sources.extend(sorted((ROOT / "runs/R22/execution/science-v1/results").glob("*.csv")))
    sources.extend(sorted((ROOT / "runs/R22/review/initial/rebuild-v5/results").glob("*.csv")))
    source_identities = [identity(path) for path in sources]
    result = {
        "schema": "r22-v3-informed-h6-recheck-source-freeze/1",
        "document_correction_lock": {"path": "runs/R22/document-correction-v3-lock.json", "sha256": sha(doc_lock_path), "file_count": len(doc_lock_checks), "all_45_byte_identities_match": True},
        "document_correction_lock_byte_checks": doc_lock_checks,
        "initial_science_delivery": {"execution_lock_sha256": sha(execution_path), "execution_lock_file_count": len(execution_lock["files"]), "science_v1_file_count": len(science_checks), "all_science_v1_byte_identities_match": True},
        "initial_judgment_carry": {"initial_result_sha256": sha(initial_result), "initial_result_size_bytes": initial_result.stat().st_size, "initial_source_freeze_sha256": sha(initial_freeze), "statuses": initial_result_obj["criterion_statuses"], "h1_h5_carried_only_after_lock_identity_confirmation": True},
        "authorized_review_input_identities": source_identities,
        "restricted_file_handling": "The correction-v3 manifest was checked by byte identity only. No ATTEMPT_STATUS, CHANGE, author selfcheck, QA, receipts, checker, or diagnostic content was opened.",
        "first_judgment_was_informed": True,
        "actual_model": None,
        "tokens": None,
        "cost": None,
    }
    out = OUT / "source-freeze.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"frozen": str(out), "source_identity_count": len(source_identities), "document_lock_files": len(doc_lock_checks), "science_v1_files": len(science_checks), "initial_statuses": initial_result_obj["criterion_statuses"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
