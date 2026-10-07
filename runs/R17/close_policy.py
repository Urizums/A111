"""Close policy delivery using actual checks, before any prospective case change."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
import continuation as ctl
def read(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
guard=read("runs/R17/handoff-check-after-fixes-command.json")
assert guard["state"]=="finished" and guard["exit_code"]==0
assert json.loads(guard["stdout"])["ok"]
assert read("runs/R17/controller-review/addendum2.json")["current_recheck"]=="both_prior_findings_repaired_in_exercised_cases"
assert read("runs/R17/controller-regression-second-fix-command.json")["exit_code"]==0
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    baseline=read("runs/R17/baseline.json")["historical_task_hashes"]
    assert all(ctl.identity(ctl.task_map(state)[tid])==h for tid,h in baseline.items())
    frozen=[]
    for name in ["state/source-lock.json","runs/R14/candidate/C9-lock.json",
                 "runs/R16/input-lock.json","runs/R16/stopped-solution-lock.json"]:
        lock=read(name)
        for row in lock.get("files",lock.get("entries",[])):
            raw=(ROOT/row["path"]).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==row["sha256"],row["path"]
        frozen.append(dict(lock=name,files=len(lock.get("files",lock.get("entries",[]))),match=True))
    history=dict(checked_at=ctl.stamp(),old_tasks=46,all_task_hashes_match=True,
        locks=frozen,old_R08_phase_unpassed=True,limits="Identity checks, no retrospective behavior regrade")
    ctl.write_json(ROOT/"runs/R17/history-verification.json",history)
    entry=dict(checked_at=ctl.stamp(),files={p:(ROOT/p).read_text(encoding="utf-8")
        for p in ["AGENTS.md","START_HERE.md","CODEX_HANDOFF.md","docs/ROADMAP.md"]},
        limits="Exact completion-time entry snapshot; later dated checkpoint updates are allowed")
    ctl.write_json(ROOT/"runs/R17/entry-policy-snapshot.json",entry)
    a=ctl.begin(state,ROOT,"R17-04","runs/R17/controller-regression-second-fix-command.json")
    result=dict(task_id="R17-04",attempt_id=a["id"],requirements_hash=a["requirements_hash"],
        criteria=[
            dict(id="d1",status="pass",evidence=["runs/R17/controller-review/review.json",
                "runs/R17/controller-review/addendum.json","runs/R17/controller-review/addendum2.json",
                "runs/R17/controller-regression-second-fix-command.json",
                "runs/R17/handoff-check-after-fixes-command.json","runs/R17/history-verification.json"]),
            dict(id="d2",status="pass",evidence=["runs/R17/package/build-command.json",
                "runs/R17/package/verification.json","runs/R17/entry-policy-snapshot.json",
                "runs/R17/R17-02-result.json","runs/R17/R17-03-result.json"])],
        effect=dict(target="C10 policy and document-only delivery",hypothesis="Remove arbitrary premature stops while retaining checks and history",
            baseline="Universal 2-correction business stop; real R16 stopped before model execution",
            conditions="Current user amendment; controlled policy review; one real web research; independent informed controller rechecks",
            observations="Original failures retained; 17 target tests and local independent probes pass; 46 old tasks and frozen locks unchanged; fresh nine-document package verified",
            limits="Cooperative metadata controls; no general search correctness, real >2 recovery, full MathorCup paper, frontend acceptance or provider quota claim",
            metrics=dict(documents=9,bundled_scripts=0,target_tests=17,tokens=None,cost=None)),
        next_action="Prospectively continue same original R16-02 actor/input/goal; preserve stopped attempt and p1-p5.")
    ctl.write_json(ROOT/"runs/R17/R17-04-result.json",result)
    ctl.finish(state,ROOT,"R17-04","runs/R17/R17-04-result.json")
    state["execution"].update(current_report="runs/R17/REPORT.md",current_native_pending=[],
        R17_status="policy_delivery_passed_scoped_evidence_not_full_product",
        next_prospective_plan="runs/R18/PLAN.md",current_candidate="runs/R17/candidate/C10-lock.json")
    state["execution"]["native_pending_current"]=[]
    state["events"].append(dict(at=ctl.stamp(),command="C10_policy_delivery",
        result=dict(status="done",historical_46_unchanged=True,full_product_pass=False)))
    ctl.write_json(ROOT/"state/continuation.json",state)
    ctl.write_json(ROOT/"state/phases/R17.json",ctl.phase_view(read("state/phases/R17.json"),state))
    project=read("state/project-todo.json")
    project["progress_search_policy_R17"].update(status="delivery_passed",report="runs/R17/REPORT.md",
        history="runs/R17/history-verification.json",next="runs/R18/PLAN.md")
    ctl.write_json(ROOT/"state/project-todo.json",project)
    ctl.synchronize(ROOT,state)
    cp=read("state/checkpoint.json")
    cp.update(current_candidate="runs/R17/candidate/C10-lock.json",
        R17_status="delivery_passed",next_action="Start authorized prospective R16-02 slice on same actor and original inputs.",
        next_prospective_plan="runs/R18/PLAN.md",unpublished_work=True)
    ctl.write_json(ROOT/"state/checkpoint.json",cp)
    assert not ctl.validate(state,ROOT),ctl.validate(state,ROOT)
print(json.dumps(dict(R17_tasks="4_done",historical_46_unchanged=True,full_product_pass=False)))
