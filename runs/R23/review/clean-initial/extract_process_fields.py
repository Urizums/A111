from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "runs/R23/receiving-packet/process-terminals.json"
OUT = ROOT / "runs/R23/review/clean-initial/source-process-fields.json"


def main() -> None:
    projection_bytes = SOURCE.read_bytes()
    projection = json.loads(projection_bytes)
    rows = []
    for item in projection["records"]:
        expected = item["source"]
        path = ROOT / expected["path"]
        content = path.read_bytes()
        receipt = json.loads(content)
        source_match = (
            len(content) == expected["size_bytes"]
            and hashlib.sha256(content).hexdigest() == expected["sha256"]
        )
        fields_match = all(
            receipt.get(field) == item[field]
            for field in ["schema", "state", "begin", "end", "exit_code"]
        )
        rows.append({
            "source_path": expected["path"],
            "source_size_bytes": len(content),
            "source_sha256": hashlib.sha256(content).hexdigest(),
            "source_identity_matches_projection": source_match,
            "schema": receipt.get("schema"),
            "state": receipt.get("state"),
            "begin": receipt.get("begin"),
            "end": receipt.get("end"),
            "exit_code": receipt.get("exit_code"),
            "projection_fields_match": fields_match,
        })
    result = {
        "schema": "r23-source-process-fields/1",
        "source_projection": SOURCE.relative_to(ROOT).as_posix(),
        "source_projection_sha256": hashlib.sha256(projection_bytes).hexdigest(),
        "records": rows,
        "all_identity_and_field_matches": all(
            row["source_identity_matches_projection"] and row["projection_fields_match"]
            for row in rows
        ),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": OUT.relative_to(ROOT).as_posix(),
        "records": len(rows),
        "all_matches": result["all_identity_and_field_matches"],
        "nonzero_exit_count": sum(row["exit_code"] != 0 for row in rows),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
