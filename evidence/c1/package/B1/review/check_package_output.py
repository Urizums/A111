from pathlib import Path
import hashlib, json

root = Path.cwd()
pkg_path = root / "materials/package.json"
notes_path = root / "materials/notes.txt"
freeze_path = root / "coordinator/Study_Freeze.json"
actions_path = root / "package/B1/artifacts/actions.json"
explanation_path = root / "package/B1/artifacts/解释.md"
reply_path = root / "package/B1/artifacts/worker-reply.json"
package = json.loads(pkg_path.read_text(encoding="utf-8"))
notes = notes_path.read_text(encoding="utf-8")
actions = json.loads(actions_path.read_text(encoding="utf-8"))
explanation = explanation_path.read_text(encoding="utf-8")
reply = json.loads(reply_path.read_text(encoding="utf-8"))
freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
frozen = {row["path"]: row["sha256"] for row in freeze["study_files"]}
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert digest(pkg_path) == frozen["materials/package.json"]
assert digest(notes_path) == frozen["materials/notes.txt"]
assert package["schema"] == "forge-package/1"
criteria = {row["id"]: row for row in package["acceptance"]["criteria"]}
assert set(criteria) == {"quotes", "commitments"}
assert all(row["required"] is True for row in criteria.values())
assert criteria["quotes"]["assertion"] == "Every source_quote is an exact substring of the supplied notes."
assert criteria["commitments"]["assertion"] == "Only explicit action items are included; unstated owners and due dates remain null."
expected = [
    {"task": "更新部署文档", "owner": "赵宁", "due": "周五", "source_quote": "赵宁负责更新部署文档，截止周五。"},
    {"task": "补充回归用例", "owner": "许静", "due": "2026-10-09", "source_quote": "许静负责补充回归用例，截止2026-10-09。"},
    {"task": "补充日志告警", "owner": None, "due": None, "source_quote": "决定补充日志告警。"},
]
assert actions == expected
assert all(item["source_quote"] in notes for item in actions)
assert len({item["source_quote"] for item in actions}) == len(actions)
assert "建议以后考虑更换配色。" not in [item["source_quote"] for item in actions]
assert "本周没有新增外部通知。" not in [item["source_quote"] for item in actions]
for phrase in ["3 项明确的行动", "周五", "null", "建议以后考虑更换配色。", "本周没有新增外部通知。"]:
    assert phrase in explanation, phrase
assert reply["result"]["invocation_id"] == "effdf28894dd763006de01d952807d97"
assert reply["result"]["outcome"] == "ok"
assert reply["result"]["artifacts"] == {"actions": actions}
assert reply["reason"] is None
assert {entry["path"]: entry["sha256"] for entry in reply["artifacts"]} == {
    str(actions_path.resolve()): digest(actions_path),
    str(explanation_path.resolve()): digest(explanation_path),
}
result = {
    "review": "pass",
    "v1_acceptance": {
        "quotes": "pass: all three source_quote values are exact note substrings",
        "commitments": "pass: the two assigned actions and explicit decision are included; the suggestion and status statement are excluded; unstated owner/due are null",
    },
    "explicit_actions": len(actions),
    "original_package_sha256": digest(pkg_path),
    "notes_sha256": digest(notes_path),
    "actions_sha256": digest(actions_path),
    "explanation_sha256": digest(explanation_path),
    "reply_sha256": digest(reply_path),
    "frozen_case_coverage": "not assessed; this was a new input, and the no-action input was not run",
}
print(json.dumps(result, ensure_ascii=False, indent=2))
