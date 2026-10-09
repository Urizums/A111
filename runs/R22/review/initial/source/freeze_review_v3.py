"""Freeze only the independent reviewer source and permitted source identities."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
INITIAL = ROOT / "runs/R22/review/initial"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def identify_locked(path: Path, item: dict) -> dict:
    size, digest = path.stat().st_size, sha(path)
    if size != item.get("size_bytes") or digest != item.get("sha256"):
        raise SystemExit(f"locked source identity mismatch: {item['path']}")
    return {"path": item["path"], "size_bytes": size, "sha256": digest}


def allowed_r22(path: str) -> bool:
    return (
        path.startswith("runs/R22/execution/source/v1/")
        or path == "runs/R22/execution/source-delivery-lock.json"
        or path == "runs/R22/execution/WORKFLOW.md"
        or path.startswith("runs/R22/execution/science-v1/")
        or path in {"runs/R22/execution/report-v1/REPORT.md", "runs/R22/execution/report-v1/REPORT.pdf"}
        or path.startswith("runs/R22/execution/figures/")
        or path == "runs/R22/execution/source/build_report_v1.py"
    )


def allowed_r21(path: str) -> bool:
    if path in {
        "runs/R21/execution/prospective-freeze.json",
        "runs/R21/execution/source/v1/config.json",
        "runs/R21/execution/source/v1/reference_policy.py",
        "runs/R21/execution/source/v1/run_science.py",
        "runs/R21/execution/science-v1/uncertainty/residual_coordinates_all.csv",
    }:
        return True
    if path.startswith("runs/R21/execution/science-v1/data/"):
        leaf = path.rsplit("/", 1)[-1]
        return leaf.endswith(".csv") and leaf.startswith(("train_", "train_features_", "predict_features_", "promotion_imputation_sources_"))
    if path.startswith("runs/R21/execution/science-v1/models/"):
        leaf = path.rsplit("/", 1)[-1]
        return leaf.endswith(".json") and leaf.startswith("coefficients_")
    return False


def main():
    protocol_lock = ROOT / "runs/R22/protocol-lock.json"
    prep_lock = ROOT / "runs/R22/receiver-preparation-lock.json"
    input_lock = ROOT / "runs/R21/input-lock.json"
    r21_lock_path = ROOT / "runs/R21/execution-lock.json"
    r22_lock_path = ROOT / "runs/R22/execution-lock.json"
    r22_files = load(r22_lock_path)["files"]
    r21_files = load(r21_lock_path)["files"]

    protocol_files = [identify_locked(ROOT / entry["path"], entry) for entry in load(protocol_lock)["files"]]
    raw_files = [identify_locked(ROOT / entry["path"], entry) for entry in load(input_lock)["files"]]
    r21_sources = [identify_locked(ROOT / entry["path"], entry) for entry in r21_files if allowed_r21(entry["path"])]
    r22_sources = [identify_locked(ROOT / entry["path"], entry) for entry in r22_files if allowed_r22(entry["path"])]
    if not any(item["path"] == "runs/R22/execution/source-delivery-lock.json" for item in r22_sources):
        raise SystemExit("source-delivery-lock identity is missing")
    if not any(item["path"] == "runs/R22/execution/report-v1/REPORT.pdf" for item in r22_sources):
        raise SystemExit("final PDF identity is missing")

    # Hash exact prepared source files. Do not traverse receipts or output folders.
    review_source_paths = [
        INITIAL / "REVIEW_PLAN.md", INITIAL / "source/freeze_review.py", INITIAL / "source/independent_rebuild.py",
        INITIAL / "source/freeze_review_v2.py", INITIAL / "source/independent_rebuild_v2.py",
        INITIAL / "source/freeze_review_v3.py", INITIAL / "source/independent_rebuild_v3.py",
    ]
    review_source = [{"path": path.relative_to(ROOT).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha(path)} for path in review_source_paths]
    result = {
        "schema": "r22-independent-review-source-freeze/3",
        "created_at": None,
        "protocol_lock_sha256": sha(protocol_lock),
        "receiver_preparation_lock_sha256": sha(prep_lock),
        "r21_input_lock_sha256": sha(input_lock),
        "r21_execution_lock_sha256": sha(r21_lock_path),
        "r22_execution_lock_sha256": sha(r22_lock_path),
        "authorized_protocol_files": protocol_files,
        "authorized_raw_input_files": raw_files,
        "authorized_r21_source_identities": r21_sources,
        "authorized_r22_source_and_delivery_identities": r22_sources,
        "independent_review_source": review_source,
        "previous_source_freeze_sha256": sha(INITIAL / "source-freeze-v2.json"),
        "revision_note": "version 3 sums expected scenario loss across coordinates to match the whole-day MILP objective after version 2 stopped at a metric-scope assertion; no scientific finding was made",
        "scope_note": "identity metadata checked for permitted bytes only; prohibited files were not opened; no scientific calculations performed",
        "model": None,
        "tokens": None,
        "cost": None,
    }
    out = INITIAL / "source-freeze-v3.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"frozen": str(out), "source_count": len(review_source), "r22_allowed_source_count": len(r22_sources), "r21_allowed_source_count": len(r21_sources)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
