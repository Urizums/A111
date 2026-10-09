"""Freeze the last report-audit source while retaining all earlier versions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
INITIAL = ROOT / "runs/R22/review/initial"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    previous = INITIAL / "source-freeze-v9.json"
    lock = json.loads(previous.read_text(encoding="utf-8"))
    new_sources = [
        INITIAL / "source/report_crosscheck.py",
        INITIAL / "source/freeze_review_v10.py",
    ]
    lock["schema"] = "r22-independent-review-source-freeze/10"
    lock["independent_review_source"].extend({
        "path": p.relative_to(ROOT).as_posix(),
        "size_bytes": p.stat().st_size,
        "sha256": sha(p),
    } for p in new_sources)
    lock["previous_source_freeze_sha256"] = sha(previous)
    lock["revision_note"] = "version 10 adds the report cross-check script; all previous source versions remain preserved"
    lock["scope_note"] = "identity metadata checked for permitted bytes only; prohibited files were not opened; report summaries are derived from the independent raw rebuild"
    out = INITIAL / "source-freeze-v10.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(lock, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"frozen": str(out), "source_count": len(lock["independent_review_source"])}))


if __name__ == "__main__":
    main()
