"""Freeze finalizer after the audit and PDF visual review are complete."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "runs/R22/review/recheck-v3"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    prior_path = OUT / "source-freeze-v2.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    paths = [OUT / "source/finalize_recheck.py", OUT / "source/freeze_recheck_source_v3.py"]
    prior["schema"] = "r22-v3-informed-h6-recheck-source-freeze/3"
    prior["prior_source_freeze_sha256"] = sha(prior_path)
    prior["v3_reviewer_source_identities"] = [{"path": p.relative_to(ROOT).as_posix(), "size_bytes": p.stat().st_size, "sha256": sha(p)} for p in paths]
    prior["revision_note"] = "v3 adds a finalizer for h1-h5 identity carry, h6 result, read-domain and per-page visual evidence; previous source and ledgers remain preserved"
    out = OUT / "source-freeze-v3.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(prior, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"frozen": str(out), "new_sources": len(paths)}))


if __name__ == "__main__":
    main()
