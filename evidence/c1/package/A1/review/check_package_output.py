from pathlib import Path
import hashlib, json
root=Path.cwd()
pkg_path=root/"materials/package.json"
notes_path=root/"materials/notes.txt"
freeze_path=root/"coordinator/Study_Freeze.json"
business_path=root/"package/A1/artifacts/actions.json"
explanation_path=root/"package/A1/artifacts/解释.md"
reply_path=root/"package/A1/artifacts/worker-reply.json"
package=json.loads(pkg_path.read_text(encoding="utf-8"))
notes=notes_path.read_text(encoding="utf-8")
stored=json.loads(business_path.read_text(encoding="utf-8"))
explanation=explanation_path.read_text(encoding="utf-8")
reply=json.loads(reply_path.read_text(encoding="utf-8"))
freeze=json.loads(freeze_path.read_text(encoding="utf-8"))
frozen={row["path"]:row["sha256"] for row in freeze["study_files"]}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(pkg_path)==frozen["materials/package.json"]
assert sha(notes_path)==frozen["materials/notes.txt"]
assert package["schema"]=="forge-package/1"
criteria={row["id"]:row for row in package["acceptance"]["criteria"]}
assert set(criteria)=={"quotes","commitments"} and all(row["required"] for row in criteria.values())
assert criteria["quotes"]["assertion"]=="Every source_quote is an exact substring of the supplied notes."
assert criteria["commitments"]["assertion"]=="Only explicit action items are included; unstated owners and due dates remain null."
expected=[
 {"task":"更新部署文档","owner":"赵宁","due":"周五","source_quote":"赵宁负责更新部署文档，截止周五。"},
 {"task":"补充回归用例","owner":"许静","due":"2026-10-09","source_quote":"许静负责补充回归用例，截止2026-10-09。"},
 {"task":"补充日志告警","owner":None,"due":None,"source_quote":"决定补充日志告警。"},
]
if isinstance(stored,list):
 actions=stored
 shape="direct actions array"
else:
 assert isinstance(stored,dict) and stored.get("outcome")=="ok" and set(stored)=={"outcome","artifacts"}
 assert set(stored["artifacts"])=={"actions"}
 actions=stored["artifacts"]["actions"]
 shape="Flow response envelope with actions array nested under artifacts"
assert actions==expected
assert all(x["source_quote"] in notes for x in actions)
assert len({x["source_quote"] for x in actions})==len(actions)
for phrase in ["3 项明确行动","周五","null","建议以后考虑更换配色","本周没有新增外部通知"]:
 assert phrase in explanation,phrase
assert reply["result"]["invocation_id"]=="d136ac6ce1fc81d124075d4d665b52c3"
assert reply["result"]["outcome"]=="ok"
assert reply["result"]["artifacts"]=={"actions":actions}
assert reply["reason"] is None
assert {a["path"]:a["sha256"] for a in reply["artifacts"]}=={
 str(business_path.resolve()):sha(business_path),
 str(explanation_path.resolve()):sha(explanation_path)
}
print(json.dumps({
 "review":"pass",
 "business_file_shape":shape,
 "v1_acceptance":{"quotes":"pass","commitments":"pass"},
 "explicit_actions":len(actions),
 "package_source_sha256":sha(pkg_path),
 "notes_sha256":sha(notes_path),
 "business_file_sha256":sha(business_path),
 "explanation_sha256":sha(explanation_path),
 "reply_sha256":sha(reply_path),
 "frozen_case_coverage":"not assessed; this was a new input, and the no-action input was not run"
},ensure_ascii=False,indent=2))
