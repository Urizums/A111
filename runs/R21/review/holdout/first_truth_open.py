"""The first recorded access to holdout truth after all three freeze bindings."""
from __future__ import annotations
import hashlib, io, json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

R = Path("runs/R21")
OUT = R / "review/holdout"

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return hashlib.sha256(p.read_bytes()).hexdigest()

initial_path = R / "review/initial-lock.json"
execution_path = R / "execution-lock.json"
evaluation_path = R / "evaluation-lock.json"
initial_lock = json.loads(initial_path.read_text(encoding="utf-8"))
execution_lock = json.loads(execution_path.read_text(encoding="utf-8"))
evaluation_lock = json.loads(evaluation_path.read_text(encoding="utf-8"))
bindings = json.loads((OUT / "freeze-bindings.json").read_text(encoding="utf-8"))
assert bindings["binding_valid"] is True
assert sha_file(initial_path) == bindings["initial_lock"]["sha256"]
assert sha_file(execution_path) == bindings["execution_lock"]["sha256"]
assert sha_file(evaluation_path) == bindings["evaluation_lock"]["sha256"]

truth_path = R / "evaluation/holdout_truth.csv"
expected = next(x for x in evaluation_lock["files"] if x["path"].replace("\\", "/") == "runs/R21/evaluation/holdout_truth.csv")
read_started = datetime.now(timezone.utc).isoformat()
# This one open is the first read of the holdout truth in this receiving stage.
truth_bytes = truth_path.read_bytes()
read_completed = datetime.now(timezone.utc).isoformat()
actual_sha = sha_bytes(truth_bytes)
frame = pd.read_csv(io.BytesIO(truth_bytes))
keys = [x for x in ("service_date", "store_id", "item_id") if x in frame.columns]
dup_count = int(frame.duplicated(keys).sum()) if len(keys) == 3 else None
report = {
    "schema": "r21-first-holdout-open/1",
    "first_open_utc": read_started,
    "read_complete_utc": read_completed,
    "sequence": {
        "initial_lock_frozen_at": initial_lock["frozen_at"],
        "execution_lock_frozen_at": execution_lock["frozen_at"],
        "evaluation_lock_frozen_at": evaluation_lock["frozen_at"],
        "initial_lock_sha256": sha_file(initial_path),
        "execution_lock_sha256": sha_file(execution_path),
        "evaluation_lock_sha256": sha_file(evaluation_path),
        "initial_lock_precedes_open": datetime.fromisoformat(initial_lock["frozen_at"]) < datetime.fromisoformat(read_started),
        "execution_lock_precedes_open": datetime.fromisoformat(execution_lock["frozen_at"]) < datetime.fromisoformat(read_started),
        "evaluation_lock_precedes_open": datetime.fromisoformat(evaluation_lock["frozen_at"]) < datetime.fromisoformat(read_started),
    },
    "truth_identity": {"path": str(truth_path).replace("\\", "/"), "expected_bytes": expected["size_bytes"],
        "actual_bytes": len(truth_bytes), "expected_sha256": expected["sha256"], "actual_sha256": actual_sha,
        "lock_identity_matches": len(truth_bytes) == expected["size_bytes"] and actual_sha == expected["sha256"]},
    "first_read_shape": {"row_count": len(frame), "columns": list(frame.columns), "key_columns": keys,
        "duplicate_key_count": dup_count, "truth_row_values_emitted_to_stdout": False},
}
report["all_bindings_precede_truth_open"] = all(report["sequence"][k] for k in (
    "initial_lock_precedes_open", "execution_lock_precedes_open", "evaluation_lock_precedes_open"))
assert report["truth_identity"]["lock_identity_matches"] and report["all_bindings_precede_truth_open"]
(OUT / "first-truth-open.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"schema": report["schema"], "first_open_utc": report["first_open_utc"],
                  "initial_lock_precedes_open": report["sequence"]["initial_lock_precedes_open"],
                  "execution_lock_precedes_open": report["sequence"]["execution_lock_precedes_open"],
                  "evaluation_lock_precedes_open": report["sequence"]["evaluation_lock_precedes_open"],
                  "truth_identity_matches": report["truth_identity"]["lock_identity_matches"],
                  "rows": len(frame), "duplicate_keys": dup_count}, ensure_ascii=False, indent=2))
