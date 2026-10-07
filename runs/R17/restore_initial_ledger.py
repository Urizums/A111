"""Restore sealed author ledger; keep subsequent events in separate followup."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
original='''{
  "schema": "forge-classified-author-events/1",
  "candidate": "C10",
  "policy": "Current user progress-based policy; no fixed global correction count",
  "events": [
    {"id":1,"type":"construction_defect","observation":"Initial acceptance JSON contained duplicate policy keys, which would erase its policy assertions when parsed.","change":"Rename the explanatory string key to recovery_policy; preserve initial bytes in acceptance-before-correction-1.json.","status":"corrected_before_candidate_freeze"},
    {"id":2,"type":"patch_construction_failure","observation":"Multi-file patch failed expected-line verification in the C10 working-copy router; the tool made no mutations.","change":"Inspect exact original line, reconstruct patch with actual surrounding text and apply successfully.","status":"corrected"}
  ],
  "candidate_source_corrections_observed": 2,
  "C9_author_unchanged": {"used":2,"limit":2},
  "telemetry": {"model":null,"tokens":null,"cost":null},
  "limits": "Parent tool observations transcribed; not fabricated subprocess receipts. These new author events do not erase or consume another historical case's count."
}
'''
state=json.loads((ROOT/"state/continuation.json").read_text(encoding="utf-8"))
task=next(t for t in state["tasks"] if t["id"]=="R17-01")
digest=next(e["sha256"] for e in task["evidence"] if e["path"]=="runs/R17/author-ledger.json")
variants=[original.encode(),original.replace("\n","\r\n").encode(),
          original.rstrip("\n").encode(),original.replace("\n","\r\n").rstrip("\r\n").encode()]
raw=next((x for x in variants if hashlib.sha256(x).hexdigest()==digest),None)
assert raw is not None,"Refuse reconstruction without exact sealed hash"
(ROOT/"runs/R17/author-ledger.json").write_bytes(raw)
follow=ROOT/"runs/R17/author-ledger-followup.json"
d=json.loads(follow.read_text(encoding="utf-8"))
d["events"].append(dict(id=7,type="evidence_mutation",
    observation="Appended followup events to author ledger already hashed by R17-01, actual handoff validation failed",
    change="Preserve appended version separately; restore only byte-exact sealed original hash; future events separate",
    evidence="runs/R17/handoff-check-wsl-command.json",status="restored_exact_original_hash"))
follow.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(original_hash_restored=digest,followup_retained=True)))
