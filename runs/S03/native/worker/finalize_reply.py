import hashlib
import json
from pathlib import Path


ROOT = Path("/workspace/A111/runs/S03/native/worker")
REQUEST_PATH = Path("/workspace/A111/runs/S03/native/job/request.json")
envelope = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
request = envelope["request"]
totals_path = ROOT / "totals.json"
totals = json.loads(totals_path.read_text(encoding="utf-8"))

artifact_paths = [totals_path, ROOT / "totals.md", ROOT / "operations.json"]
artifacts = [
    {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    for path in artifact_paths
]
reply = {
    "schema_version": "forge-host-reply/1",
    "job_id": request["job_id"],
    "attempt_id": request["attempt_id"],
    "request_hash": envelope["request_hash"],
    "outcome": "done",
    "result": {
        "row_count": totals["row_count"],
        "total_fen": totals["total_fen"],
        "categories": totals["categories"],
        "totals_md": str((ROOT / "totals.md").resolve()),
        "operations": str((ROOT / "operations.json").resolve()),
    },
    "artifacts": artifacts,
    "reason": None,
}
with (ROOT / "reply.json").open("x", encoding="utf-8", newline="\n") as output:
    json.dump(reply, output, ensure_ascii=False, indent=2, allow_nan=False)
    output.write("\n")
