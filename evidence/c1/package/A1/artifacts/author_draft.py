from pathlib import Path
import hashlib
import json

request_path = Path("/workspace/scratch/73714494ad2f/forge-protocol-comparison-20261003/package/A1/job/request.json")
artifact_dir = Path("/workspace/scratch/73714494ad2f/forge-protocol-comparison-20261003/package/A1/artifacts")
envelope = json.loads(request_path.read_text(encoding="utf-8"))
request = envelope["request"]
artifact_refs = []
for name in ("actions.json", "解释.md"):
    path = artifact_dir / name
    artifact_refs.append({
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
    })
draft = {
    "schema_version": "forge-host-reply/1",
    "job_id": request["job_id"],
    "attempt_id": request["attempt_id"],
    "request_hash": envelope["request_hash"],
    "outcome": None,
    "result": {
        "invocation_id": request["invocation_id"],
        "outcome": None,
        "artifacts": {},
        "evidence": []
    },
    "artifacts": artifact_refs,
    "reason": None
}
(artifact_dir / "worker-reply.draft.json").write_text(
    json.dumps(draft, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)
