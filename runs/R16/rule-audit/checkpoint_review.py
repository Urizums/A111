"""Record current user rule-review steering without changing rules or budgets."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import continuation as ctl

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    baseline = read("runs/R14/baseline.json")["historical_task_hashes"]
    before_tasks = ctl.identity(state["tasks"])
    for tid, digest in baseline.items():
        assert ctl.identity(ctl.task_map(state)[tid]) == digest
    state["execution"].update(current_coordinator="root-codex-r16-rule-audit",
        current_report="runs/R16/rule-audit/REPORT.md",
        current_user_steering="Pause solution and investigate the unreviewed repair rule before policy or budget changes.",
        R16_budget_proposal_status="superseded_by_policy_review_not_authorized",
        repair_policy_review="runs/R16/rule-audit/REPORT.md",
        coordinator_release_evidence="runs/R16/rule-audit/lease-release.json")
    state["events"].append(dict(at=ctl.stamp(), command="record_user_rule_review",
        result=dict(rules_changed=False, budgets_changed=False, solution_resumed=False,
            prior_2_to_6_proposal="deferred_for_rule_review", report="runs/R16/rule-audit/REPORT.md")))
    assert ctl.identity(state["tasks"]) == before_tasks
    ctl.write_json(ROOT / "state/continuation.json", state)
    ctl.synchronize(ROOT, state)
    checkpoint = read("state/checkpoint.json")
    checkpoint.update(next_action="Review repair policy with user before implementing any rule change or continuing R16. Earlier 2-to-6 prompt is deferred, not authorization.",
        repair_policy_review="runs/R16/rule-audit/REPORT.md",
        current_development_report="runs/R16/rule-audit/REPORT.md",
        R16_budget_proposal_status="superseded_by_policy_review_not_authorized",
        unpublished_work=True,
        termination="Rule audit saved; solution remains paused, all original task states/counters unchanged; no background actor.")
    ctl.write_json(ROOT / "state/checkpoint.json", checkpoint)
    project = read("state/project-todo.json")
    project["real_historical_problem_R16"].update(rule_review="runs/R16/rule-audit/REPORT.md",
        current_action="Policy review before deciding continuation; no rule/budget changes.")
    ctl.write_json(ROOT / "state/project-todo.json", project)
    assert not ctl.validate(state, ROOT), ctl.validate(state, ROOT)
outputs = ROOT.parents[1] / "outputs"
(outputs / "Forge-repair-policy-audit.md").write_bytes((ROOT / "runs/R16/rule-audit/REPORT.md").read_bytes())
print(json.dumps(dict(rule_audit_saved=True, all_46_tasks_unchanged=True,
    original_38_hashes_unchanged=True, rules_changed=False, budgets_changed=False, solver_resumed=False)))
