from pathlib import Path
import hashlib,json
root=Path.cwd()
request=json.loads((root/"package/A1/job/request.json").read_text(encoding="utf-8"))
reply_path=root/"package/A1/artifacts/worker-reply.json"
reply=json.loads(reply_path.read_text(encoding="utf-8"))
assessment=json.loads(json.loads((root/"package/A1/review/package-assess.json").read_text(encoding="utf-8"))["stdout"])
assert assessment["verdict"]=="pass"
decision={
"schema_version":"forge-host-decision/1",
"request_hash":request["request_hash"],
"reply_sha256":hashlib.sha256(reply_path.read_bytes()).hexdigest(),
"outcome":"done",
"results":reply["result"],
"reason":None
}
(root/"package/A1/review/coordinator-decision.json").write_text(json.dumps(decision,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")