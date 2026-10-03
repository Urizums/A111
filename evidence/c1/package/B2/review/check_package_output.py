from pathlib import Path
import hashlib
import json

root = Path.cwd()
package_path = root / "materials/package.json"
notes_path = root / "materials/notes.txt"
freeze_path = root / "coordinator/Study_Freeze.json"
state_path = root / "package/B2/state.json"
request_path = root / "package/B2/job/request.json"
business_path = root / "package/B2/artifacts/actions.json"
explanation_path = root / "package/B2/artifacts/explanation.zh.md"
verification_path = root / "package/B2/artifacts/verification.json"
reply_path = root / "package/B2/artifacts/worker-reply.json"
check_path = root / "package/B2/artifacts/logs/check-reply.json"

package = json.loads(package_path.read_text(encoding="utf-8"))
notes = notes_path.read_text(encoding="utf-8")
actions = json.loads(business_path.read_text(encoding="utf-8"))
explanation = explanation_path.read_text(encoding="utf-8")
reply = json.loads(reply_path.read_text(encoding="utf-8"))
check = json.loads(check_path.read_text(encoding="utf-8"))
state = json.loads(state_path.read_text(encoding="utf-8"))
request_wrapper = json.loads(request_path.read_text(encoding="utf-8"))
request = request_wrapper["request"]
freeze = json.loads(freeze_path.read_text(encoding="utf-8"))

sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
frozen = {row["path"]: row["sha256"] for row in freeze["study_files"]}
assert sha(package_path) == frozen["materials/package.json"]
assert sha(notes_path) == frozen["materials/notes.txt"]
assert package["schema"] == "forge-package/1"
criteria = {row["id"]: row for row in package["acceptance"]["criteria"]}
assert set(criteria) == {"quotes", "commitments"}
assert all(row["required"] for row in criteria.values())
assert criteria["quotes"]["kind"] == "machine"
assert criteria["quotes"]["assertion"] == "Every source_quote is an exact substring of the supplied notes."
assert criteria["commitments"]["kind"] == "human"
assert criteria["commitments"]["assertion"] == "Only explicit action items are included; unstated owners and due dates remain null."

expected = [
    {
        "task": "更新部署文档",
        "owner": "赵宁",
        "due": "周五",
        "source_quote": "赵宁负责更新部署文档，截止周五。",
    },
    {
        "task": "补充回归用例",
        "owner": "许静",
        "due": "2026-10-09",
        "source_quote": "许静负责补充回归用例，截止2026-10-09。",
    },
    {
        "task": "补充日志告警",
        "owner": None,
        "due": None,
        "source_quote": "决定补充日志告警。",
    },
]
assert isinstance(actions, list) and actions == expected
assert all(row["source_quote"] in notes for row in actions)
assert all("建议以后考虑更换配色" not in row["source_quote"] for row in actions)
assert all("本周没有新增外部通知" not in row["source_quote"] for row in actions)
for phrase in ["3 项明确行动", "周五", "2026-10-09", "null", "建议以后考虑更换配色", "本周没有新增外部通知"]:
    assert phrase in explanation, phrase

invocation_id = request["invocation_id"]
assert state["package_hash"] == request["target_binding"]["package_hash"]
start_capture = json.loads(Path("package/B2/logs/002-package-start.json").read_text())
assert json.loads(start_capture["stdout"])["invocation_id"] == invocation_id
assert reply["schema_version"] == "forge-host-reply/1"
assert reply["job_id"] == request["job_id"]
assert reply["attempt_id"] == request["attempt_id"]
assert reply["request_hash"] == request_wrapper["request_hash"]
assert reply["outcome"] == "done" and reply["reason"] is None
assert reply["result"] == {
    "invocation_id": invocation_id,
    "outcome": "ok",
    "artifacts": {"actions": expected},
    "evidence": [
        str(business_path.resolve()),
        str(explanation_path.resolve()),
        str(verification_path.resolve()),
    ],
}
assert {row["path"]: row["sha256"] for row in reply["artifacts"]} == {
    str(business_path.resolve()): sha(business_path),
    str(explanation_path.resolve()): sha(explanation_path),
    str(verification_path.resolve()): sha(verification_path),
}
assert check["schema"] == "forge-comparison-cli/1" and check["actor"] == "worker"
assert check["exit_code"] == 0 and json.loads(check["stdout"])["status"] == "payload_valid"
assert check["argv"][-4:] == ["--request", str(request_path.resolve()), "--reply", str(reply_path.resolve())]

print(json.dumps({
    "review": "pass",
    "business_file_shape": "direct actions array",
    "v1_acceptance": {"quotes": "pass", "commitments": "pass"},
    "explicit_actions": len(actions),
    "package_source_sha256": sha(package_path),
    "notes_sha256": sha(notes_path),
    "business_file_sha256": sha(business_path),
    "explanation_sha256": sha(explanation_path),
    "verification_sha256": sha(verification_path),
    "reply_sha256": sha(reply_path),
    "check_reply_capture": str(check_path.relative_to(root)),
    "frozen_case_coverage": "not assessed; this was a new input, and the no-action input was not run",
}, ensure_ascii=False, indent=2))
