"""Read-only final path, interface, and terminal-receipt inventory."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESIGN = ROOT / "runs/R23/design"


def main() -> None:
    paths = sorted(p for p in DESIGN.rglob("*") if p.is_file())
    escaped = [str(p) for p in paths if not p.resolve().is_relative_to(DESIGN.resolve())]
    assert not escaped, f"file outside design domain: {escaped}"
    required = [
        "WORKFLOW.md", "READ-DOMAIN.md", "SELF-CHECK.md", "COMPLETION-STATE.json",
        "probe.py", "versions/probe-v1.py", "selfcheck.py", "finalize.py",
        "selfcheck.json", "receipts/INDEX.json", "probe-output-v2/predictions.csv",
        "probe-output-v2/replenishment.csv", "probe-output-v2/scenarios.csv",
        "probe-output-v2/feature_lineage.csv", "probe-output-v2/summary.json",
    ]
    missing = [p for p in required if not (DESIGN / p).is_file()]
    assert not missing, f"missing deliverable: {missing}"
    for rel in ["probe.py", "versions/probe-v1.py", "selfcheck.py", "finalize.py"]:
        compile((DESIGN / rel).read_text(encoding="utf-8"), rel, "exec")
    state = json.loads((DESIGN / "COMPLETION-STATE.json").read_text(encoding="utf-8"))
    report = json.loads((DESIGN / "selfcheck.json").read_text(encoding="utf-8"))
    receipts = []
    for path in sorted((DESIGN / "receipts").glob("*.json")):
        if path.name == "INDEX.json":
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        assert d.get("schema") == "forge-command-record/1", path.name
        if "end" not in d:
            continue  # This verification command's own receipt is live until exit.
        assert d.get("state") == "finished" and isinstance(d.get("exit_code"), int), path.name
        receipts.append((path.name, d["exit_code"]))
    assert state["independent_acceptance"] == "pending"
    assert state["production_complete"] is False and state["paper_complete"] is False
    assert report["independent_acceptance"] == "pending"
    flow = (DESIGN / "WORKFLOW.md").read_text(encoding="utf-8")
    for phrase in ["2026-11-01", "2026-12-12", "1,600", "6,000", "weekly_median56", "acceptor", "scenarios.csv"]:
        assert phrase in flow, f"workflow missing required detail: {phrase}"
    print(json.dumps({
        "design_file_count_before_this_receipt": len(paths),
        "required_artifacts": len(required),
        "terminal_receipts_before_this_receipt": len(receipts),
        "nonzero_receipt_names_preserved": [name for name, code in receipts if code != 0],
        "source_files_compile": True,
        "write_domain_paths": "all inside runs/R23/design",
        "status": "author package frozen; independent reception pending",
        "known_initial_receipt_added_after_exit": "this verification command will become terminal after this script returns",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
