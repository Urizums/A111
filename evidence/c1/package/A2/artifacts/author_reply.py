from pathlib import Path
import hashlib
import json

request_file = Path("/workspace/scratch/73714494ad2f/forge-protocol-comparison-20261003/package/A2/job/request.json")
root = json.loads(request_file.read_text(encoding="utf-8"))
request = root["request"]
artifacts_dir = Path(request["work"]["write_paths"][0])
actions_path = artifacts_dir / "actions.json"
explanation_path = artifacts_dir / "explanation.md"
actions = json.loads(actions_path.read_text(encoding="utf-8"))
notes = request["dispatch"]["inputs"]["notes"]
assert all(item["source_quote"] in notes for item in actions)
actual_artifacts = []
for path in (actions_path, explanation_path):
    actual_artifacts.append({
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    })
draft = {
    "schema_version": "forge-host-reply/1",
    "job_id": request["job_id"],
    "attempt_id": request["attempt_id"],
    "request_hash": root["request_hash"],
    "outcome": None,
    "result": {
        "invocation_id": request["dispatch"]["invocation_id"],
        "outcome": None,
        "artifacts": {},
        "evidence": [],
    },
    "artifacts": actual_artifacts,
    "reason": None,
}
final = {
    "schema_version": "forge-host-reply/1",
    "job_id": request["job_id"],
    "attempt_id": request["attempt_id"],
    "request_hash": root["request_hash"],
    "outcome": "done",
    "result": {
        "invocation_id": request["dispatch"]["invocation_id"],
        "outcome": "ok",
        "artifacts": {"actions": actions},
        "evidence": [str(actions_path), str(explanation_path)],
    },
    "artifacts": actual_artifacts,
    "reason": None,
}
(artifacts_dir / "worker-reply.draft.json").write_text(
    json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
Path(request["work"]["reply_path"]).write_text(
    json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
