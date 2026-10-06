"""Record completed source CI; does not change original behavioral verdicts."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import continuation as ctl
def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))
receipt = read("runs/R16/publication/source-ci-completion-command.json")
assert receipt["state"] == "finished" and receipt["exit_code"] == 0
raw = json.loads(receipt["stdout"])
source = read("runs/R16/publication/source-receipt.json")["source_commit"]
assert raw["headSha"] == source and raw["status"] == "completed" and raw["conclusion"] == "success"
ci = {k: raw[k] for k in ["headSha", "status", "conclusion", "url"]}
ci["jobs"] = [{k: j[k] for k in ["name", "status", "conclusion"]} for j in raw["jobs"]]
assert len(ci["jobs"]) == 3 and all(j["conclusion"] == "success" for j in ci["jobs"])
ci["evidence"] = "runs/R16/publication/source-ci-completion-command.json"
ctl.write_json(ROOT / "runs/R16/publication/source-ci-summary.json", ci)
with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    baseline = read("runs/R14/baseline.json")["historical_task_hashes"]
    for tid, digest in baseline.items():
        assert ctl.identity(ctl.task_map(state)[tid]) == digest, tid
    state["execution"].update(source_ci=ci, R14_R16_source_ci=ci)
    state["events"].append(dict(at=ctl.stamp(), command="record_completed_source_ci",
        result=dict(source_commit=source, conclusion="success", full_acceptance_passed=False)))
    ctl.write_json(ROOT / "state/continuation.json", state)
    ctl.synchronize(ROOT, state)
    checkpoint = read("state/checkpoint.json")
    checkpoint.update(current_ci_R14_R16=ci, unpublished_work=False,
        publication_note="Identified development source push and its three CI jobs succeeded; later receipt commit does not alter frozen candidate/trial inputs or pass failed behavioral gates.")
    ctl.write_json(ROOT / "state/checkpoint.json", checkpoint)
print(json.dumps(dict(source_commit=source, ci_conclusion="success", jobs=ci["jobs"],
    old_tasks_preserved=len(baseline), R16_full_paper=False, full_acceptance=False)))
