"""Freeze the final first-judgment writer and preserve previous source freeze."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
INITIAL = ROOT / "runs/R22/review/initial"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    previous = INITIAL / "source-freeze-v10.json"
    lock = json.loads(previous.read_text(encoding="utf-8"))
    additions = [INITIAL / "source/finalize_initial_review.py", INITIAL / "source/freeze_review_v11.py"]
    lock["schema"] = "r22-independent-review-source-freeze/11"
    lock["independent_review_source"].extend({"path": p.relative_to(ROOT).as_posix(), "size_bytes": p.stat().st_size, "sha256": sha(p)} for p in additions)
    lock["previous_source_freeze_sha256"] = sha(previous)
    lock["revision_note"] = "version 11 adds the final review/result writer; all previous reviewer versions remain preserved"
    lock["scope_note"] = "the final record uses only permitted locked bytes and independently rebuilt outputs; author receipt semantics remain excluded"
    out = INITIAL / "source-freeze-v11.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(lock, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"frozen": str(out), "source_count": len(lock["independent_review_source"])}))


if __name__ == "__main__":
    main()
