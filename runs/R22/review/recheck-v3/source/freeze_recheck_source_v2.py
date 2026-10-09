"""Freeze the tolerance-aware narrative audit as an append-only revision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "runs/R22/review/recheck-v3"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    prior = OUT / "source-freeze.json"
    result = json.loads(prior.read_text(encoding="utf-8"))
    paths = [OUT / "source/audit_report_v3_v2.py", OUT / "source/freeze_recheck_source_v2.py"]
    result["schema"] = "r22-v3-informed-h6-recheck-source-freeze/2"
    result["prior_source_freeze_sha256"] = sha(prior)
    result["v2_reviewer_source_identities"] = [{"path": p.relative_to(ROOT).as_posix(), "size_bytes": p.stat().st_size, "sha256": sha(p)} for p in paths]
    result["revision_note"] = "v2 adds explicit tolerance for binary-float representation in source amount rows and checks repeated narrative claims; prior reviewer source and ledger retained"
    out = OUT / "source-freeze-v2.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"frozen": str(out), "new_sources": len(paths)}))


if __name__ == "__main__":
    main()
