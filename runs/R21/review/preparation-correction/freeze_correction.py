from __future__ import annotations
import hashlib
import json
from pathlib import Path

root = Path("runs/R21/review/preparation-correction")
excluded = {"correction-lock.json", "freeze-command.json"}
files = []
for p in sorted(x for x in root.iterdir() if x.is_file() and x.name not in excluded):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    files.append({"path": p.as_posix(), "size_bytes": p.stat().st_size, "sha256": h})
lock = {"schema": "r21-reception-preparation-correction-lock/1", "files": files, "claim": "identity of correction-preparation artifacts only; no product acceptance"}
(root / "correction-lock.json").write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"lock": str(root / "correction-lock.json"), "files_frozen": len(files)}, ensure_ascii=False))
