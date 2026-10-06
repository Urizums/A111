"""R14 development-state integration; not part of the delivered skill."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import continuation as ctl

patch = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
baseline = json.loads((ROOT / "runs/R14/baseline.json").read_text(encoding="utf-8"))
with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    before = {t["id"]: t for t in state["tasks"]}
    for tid, digest in baseline["historical_task_hashes"].items():
        assert hashlib.sha256(json.dumps(before[tid], sort_keys=True, ensure_ascii=False).encode()).hexdigest() == digest, tid
    state["execution"].update(patch.get("execution", {}))
    state["events"].append(dict(at=ctl.stamp(), command="R14_resumption_integrate", result=dict(source=sys.argv[1], old_tasks_preserved=True)))
    ctl.write_json(ROOT / "state/continuation.json", state)
    phase = json.loads((ROOT / "state/phases/R14.json").read_text(encoding="utf-8"))
    phase = ctl.phase_view(phase, state)
    if patch.get("transition"):
        phase["tasks"][-1].update(patch["transition"])
    ctl.write_json(ROOT / "state/phases/R14.json", phase)
    ctl.synchronize(ROOT, state)
    checkpoint = json.loads((ROOT / "state/checkpoint.json").read_text(encoding="utf-8"))
    checkpoint.update(patch.get("checkpoint", {}))
    ctl.write_json(ROOT / "state/checkpoint.json", checkpoint)
    project = json.loads((ROOT / "state/project-todo.json").read_text(encoding="utf-8"))
    project["domain_workflows_R14"].update(patch.get("project", {}))
    ctl.write_json(ROOT / "state/project-todo.json", project)
print(json.dumps(dict(updated=True, old_tasks_preserved=len(baseline["historical_task_hashes"]), source=sys.argv[1])))
