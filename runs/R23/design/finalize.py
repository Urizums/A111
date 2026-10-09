"""Finalize design-domain status and inventory already-terminal command receipts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESIGN = ROOT / "runs/R23/design"
RECEIPTS = DESIGN / "receipts"


def main() -> None:
    required = [
        "WORKFLOW.md", "probe.py", "versions/probe-v1.py", "READ-DOMAIN.md",
        "SELF-CHECK.md", "selfcheck.py", "selfcheck.json", "COMPLETION-STATE.json",
        "probe-output-v2/predictions.csv", "probe-output-v2/replenishment.csv",
        "probe-output-v2/scenarios.csv", "probe-output-v2/feature_lineage.csv",
        "probe-output-v2/summary.json", "probe-output/predictions.csv",
        "probe-output/replenishment.csv", "probe-output/summary.json",
    ]
    missing = [p for p in required if not (DESIGN / p).is_file()]
    if missing:
        raise FileNotFoundError(f"required design artifact missing: {missing}")
    receipt_rows = []
    for path in sorted(RECEIPTS.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        # record_command.py creates the caller's receipt before this child exits.
        # Exclude only this live finalize invocation; a later inventory can see it terminal.
        if "end" not in record:
            continue
        if record.get("schema") != "forge-command-record/1":
            raise ValueError(f"not a command receipt: {path.name}")
        if record.get("state") != "finished" or "end" not in record or not isinstance(record.get("exit_code"), int):
            raise ValueError(f"nonterminal receipt: {path.name}")
        receipt_rows.append({
            "path": path.relative_to(ROOT).as_posix(),
            "state": record["state"],
            "exit_code": record["exit_code"],
            "begin_utc": record["begin"].get("utc"),
            "end_utc": record["end"].get("utc"),
        })
    all_files = sorted(p.relative_to(ROOT).as_posix() for p in DESIGN.rglob("*") if p.is_file())
    if any(not p.startswith("runs/R23/design/") for p in all_files):
        raise AssertionError("write-boundary inventory escaped design domain")
    index = {
        "schema": "r23-design-command-receipt-index/1",
        "terminal_receipt_count_at_finalize": len(receipt_rows),
        "receipts": receipt_rows,
        "author_failures_retained": [x["path"] for x in receipt_rows if x["exit_code"] != 0],
        "design_files_at_finalize": all_files,
        "write_domain_contract_only": True,
    }
    (DESIGN / "receipts/INDEX.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state_path = DESIGN / "COMPLETION-STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["receipt_index"] = "runs/R23/design/receipts/INDEX.json"
    state["terminal_receipts_at_finalize"] = len(receipt_rows)
    state["designer_state"] = "frozen_pending_independent_reception"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"required_artifacts": len(required), "terminal_receipts": len(receipt_rows), "nonzero_receipts_retained": len(index["author_failures_retained"]), "design_files": len(all_files), "state": state["designer_state"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
