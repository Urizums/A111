"""Freeze C10 documents and raw review inputs after actual structure validation."""
import hashlib
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
candidate = HERE / "candidate/C10/forge-agent-flow"
record = json.loads((HERE / "structure-command.json").read_text(encoding="utf-8"))
assert record["state"] == "finished" and record["exit_code"] == 0
docs = sorted(candidate.rglob("*.md"))
assert len(docs) == 9 and all(p.suffix == ".md" for p in candidate.rglob("*") if p.is_file())
for p in docs:
    for match in re.finditer(r"\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
        link = match.group(1).split("#")[0]
        if link and not re.match(r"^[a-z]+://", link):
            assert (p.parent / link).resolve().is_file(), (p, link)
def row(p):
    raw=p.read_bytes()
    return dict(path=p.relative_to(ROOT).as_posix(), size_bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest())
lock=dict(schema="forge-revision-lock/1",revision="C10",parent="C9",
    scope_decision="runs/R17/scope-decision.json",files=[row(p) for p in docs],
    recovery_policy="Classified events and evidence-backed progress; fixed old experimental conditions preserved.",
    limits="Source identity/links only; not behavioral acceptance.")
target=HERE / "candidate/C10-lock.json"
assert not target.exists()
target.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
inputs=[HERE/"acceptance.json",HERE/"scope-decision.json",HERE/"cases/scenarios.json",
        HERE/"cases/research-request.json",target]
input_lock=dict(schema="forge-revision-lock/1",revision="R17-original-inputs",files=[row(p) for p in inputs])
(HERE/"input-lock.json").write_text(json.dumps(input_lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(C10_frozen=True,document_files=len(docs),input_files=len(inputs),
    bundled_scripts=0,links_verified=True,behavior_not_yet_judged=True)))
