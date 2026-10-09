from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DOMAIN = ROOT / "runs/R23/review/clean-initial"
RECORD_NAMES = [
    "01-packet-identities.json",
    "02-doc-continuation-and-correct-lock.json",
    "03-workflow-and-terminal-shape.json",
    "04-approved-slice-sources.json",
    "05-process-projection.json",
    "06-identity-audit.json",
    "07-original-criteria-and-brief.json",
    "08-history-receipt-field-audit.json",
    "09-independent-freeze-hashes.json",
    "10-freeze-independent-selection.json",
    "11-independent-source-recomputation.json",
    "12-preserve-first-freeze.json",
    "13-freeze-corrected-selection.json",
    "14-independent-source-recomputation.json",
    "15-explicit-lock-members.json",
    "17-write-source-terminal-fields.json",
    "18-reference-source-notes.json",
]


def main() -> None:
    rows = []
    for name in RECORD_NAMES:
        path = DOMAIN / "records" / name
        raw = path.read_bytes()
        receipt = json.loads(raw)
        rows.append({
            "receipt_path": path.relative_to(ROOT).as_posix(),
            "receipt_size_bytes": len(raw),
            "receipt_sha256": hashlib.sha256(raw).hexdigest(),
            "schema": receipt.get("schema"),
            "state": receipt.get("state"),
            "begin": receipt.get("begin"),
            "end": receipt.get("end"),
            "exit_code": receipt.get("exit_code"),
        })
    out = {
        "schema": "r23-clean-receiver-process-fields/1",
        "records": rows,
        "failed_shell_receipts": [r["receipt_path"] for r in rows if r["exit_code"] != 0],
    }
    dest = DOMAIN / "receiver-process-fields.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": dest.relative_to(ROOT).as_posix(), "records": len(rows),
                      "nonzero_exit_count": len(out["failed_shell_receipts"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
