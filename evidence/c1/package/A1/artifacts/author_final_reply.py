from pathlib import Path
import hashlib
import json

artifact_dir = Path("/workspace/scratch/73714494ad2f/forge-protocol-comparison-20261003/package/A1/artifacts")
envelope = json.loads(Path("/workspace/scratch/73714494ad2f/forge-protocol-comparison-20261003/package/A1/job/request.json").read_text(encoding="utf-8"))
request = envelope["request"]
business = json.loads((artifact_dir / "actions.json").read_text(encoding="utf-8"))
refs = []
for name in ("actions.json", "解释.md"):
    path = artifact_dir / name
    refs.append({
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
    })
reply = {
    "schema_version": "forge-host-reply/1",
    "job_id": request["job_id"],
    "attempt_id": request["attempt_id"],
    "request_hash": envelope["request_hash"],
    "outcome": "done",
    "result": {
        "invocation_id": request["invocation_id"],
        "outcome": business["outcome"],
        "artifacts": {
            "actions": business["artifacts"]["actions"]
        },
        "evidence": [
            str(artifact_dir / "actions.json"),
            str(artifact_dir / "解释.md")
        ]
    },
    "artifacts": refs,
    "reason": None
}
Path(request["work"]["reply_path"]).write_text(
    json.dumps(reply, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)
