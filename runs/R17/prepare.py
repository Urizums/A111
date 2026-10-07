"""Capture pre-policy history and create a document-only C10 working copy."""
import hashlib
import json
import shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
before = HERE / "before"
before.mkdir(exist_ok=False)
for name in ["AGENTS.md", "START_HERE.md", "CODEX_HANDOFF.md", "docs/ROADMAP.md",
             "scripts/continuation.py", "scripts/test_continuation.py",
             "state/continuation.json", "state/checkpoint.json", "state/project-todo.json"]:
    target = before / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT / name).read_bytes())
state = json.loads((ROOT / "state/continuation.json").read_text(encoding="utf-8"))
baseline = dict(source_head="f05c134b1a805b2cd000b14b52fbde7035d4a951",
    historical_task_hashes={t["id"]: hashlib.sha256(json.dumps(t, sort_keys=True,
        ensure_ascii=False).encode()).hexdigest() for t in state["tasks"]},
    candidate_parent="runs/R14/candidate/C9-lock.json",
    old_2_to_6_proposal="superseded_by_user_policy_change; no numeric increase or reset",
    limits="Snapshots preserve old verdicts/counters. A prospective authorized amendment must retain the original snapshot, not silently rewrite history.")
(HERE / "baseline.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
shutil.copytree(ROOT / "runs/R14/candidate/C9/forge-agent-flow",
                HERE / "candidate/C10/forge-agent-flow")
print(json.dumps(dict(historical_tasks_snapshotted=len(state["tasks"]),
    old_rules_retained=True, C10_working_copy_created=True, candidate_not_yet_frozen=True)))
