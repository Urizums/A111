"""Record actual same-actor prospective start; never regrade the stopped attempt."""
import copy
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
import continuation as ctl
def read(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
observed=read("runs/R16/prospective-20261007/first-step.json")
receipt=observed["actual_start_receipt"]
command=read(receipt)
assert command["state"]=="finished"
assert observed["task_id"]=="R16-02" and observed["actor"]=="/root/r16_original_solution"
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    tasks=ctl.task_map(state)
    assert all(tasks[f"R17-0{i}"]["status"]=="done" for i in range(1,5))
    task=tasks["R16-02"]
    original=read("runs/R18/original-task.json")
    assert task==original,"Refuse changing an unexpected original case"
    old_attempts=copy.deepcopy(task["attempts"])
    old_used=task["repairs_used"]
    # This is a prospective amendment; old acceptance/attempt hashes remain retained.
    task.update(acceptance=read("runs/R18/prospective-acceptance.json")["execution_gate"],
        repair_limit=None,status="planned",blocker=None,owner="/root/r16_original_solution",
        write_paths=["runs/R16/prospective-20261007/"],
        execution_policy=dict(mode="progress_guard",source=ctl.ref(ROOT,"runs/R18/amendment.json"),
            progress_state="ready",deadline_utc=None,
            stop_conditions=["original mandatory output verified","actual resource/authority boundary","unsupported unchanged path"]),
        prospective_continuation=dict(amendment="runs/R18/amendment.json",
            original_task="runs/R18/original-task.json",legacy_repairs_used=old_used,
            legacy_repair_limit=original["repair_limit"],legacy_verdict=original["status"],
            queue_restart_is_not_source_error=True),
        recovery_note=dict(observation="Original case stopped after two local source recoveries, no model execution.",
            change_or_new_information="Current user authorized classified-progress policy; same actor/input/goal under C10.",
            expected_check="Keep p1-p5; actually compute baseline and check original constraints before paper.",
            evidence=[ctl.ref(ROOT,"runs/R18/amendment.json"),ctl.ref(ROOT,"runs/R16/budget-decision.json")]))
    task["inputs"]=original["inputs"]+["runs/R18/amendment.json","runs/R18/prospective-acceptance.json",
        "runs/R17/candidate/C10-lock.json"]
    ctl.begin(state,ROOT,"R16-02",receipt)
    assert task["attempts"][:-1]==old_attempts
    assert task["repairs_used"]==old_used+1
    task["next_action"]="Continue original full solve from actual baseline/constraint slice; no full-paper acceptance yet."
    task["evidence"]=[ctl.ref(ROOT,"runs/R16/prospective-20261007/first-step.json"),ctl.ref(ROOT,receipt)]
    state["execution"].update(current_report="runs/R17/REPORT.md",current_native_pending=[],
        native_pending_current=[],current_user_steering="C10 progress/search policy implemented; same original R16-02 prospectively continued.",
        completed_native_R18=[dict(worker="/root/r16_original_solution",state="final_notification_received",
            evidence="runs/R16/prospective-20261007/first-step.json",actual_model=None)],
        next_prospective_plan="runs/R18/PLAN.md",R18_status="real_first_step_observed_full_case_incomplete")
    rows=[]
    for tid,deps in [("R16-02",[]),("R16-03",["R16-02"]),("R16-04",["R16-02","R16-03"])]:
        t=tasks[tid]
        rows.append({k:t[k] for k in ["id","title","owner","write_paths","status","blocker","next_action"]}|
            dict(depends_on=deps,acceptance=[a["assertion"] for a in t["acceptance"]],
                 evidence=[e["path"] for e in t["evidence"]]+[a["start_evidence"]["path"] for a in t["attempts"]]))
    rows.append(dict(id="R18-next",title="启动下一阶段任务",owner="root",
        depends_on=["R16-02","R16-03","R16-04"],write_paths=["state/","runs/"],acceptance=["完成原要求后真实启动后继，否则保留阻塞"],
        status="blocked",evidence=[],blocker="Original full solution/paper and independent acceptance incomplete.",
        next_action="Continue the same original-case goal; do not infer a pass from its first slice."))
    ctl.write_json(ROOT/"state/phases/R18.json",dict(schema="forge-phase-todo/1",phase_id="R18",
        goal="Same R16-02 original identity under prospective user policy, with old attempt retained",tasks=rows))
    phase=ctl.phase_view(read("state/phases/R17.json"),state)
    phase["tasks"][-1].update(status="done",blocker=None,evidence=[receipt],
        next_action="Continue actual original R16-02 slice toward full paper.",
        transition=dict(next_phase_id="R18",todo_path="state/phases/R18.json",first_task_id="R16-02",
            start_evidence=[receipt]))
    ctl.write_json(ROOT/"state/phases/R17.json",phase)
    baseline=read("runs/R17/baseline.json")["historical_task_hashes"]
    unchanged=[tid for tid,h in baseline.items() if ctl.identity(tasks[tid])==h]
    assert len(unchanged)==45 and "R16-02" not in unchanged
    for tid,h in read("runs/R14/baseline.json")["historical_task_hashes"].items():
        assert ctl.identity(tasks[tid])==h,tid
    old_p=read("runs/R16/acceptance.json")["execution_gate"][:5]
    assert task["acceptance"][:5]==old_p
    proof=dict(checked_at=ctl.stamp(),original_38_unchanged=True,pre_R17_45_other_tasks_unchanged=True,
        one_authorized_prospective_amendment="R16-02",old_attempt_bytes_equal=True,p1_to_p5_unchanged=True,
        old_source_corrections=2,queue_restart_counter=task["repairs_used"],new_actor_events=observed.get("actual_events"),
        original_verdict="blocked/unpassed under old2/2",full_solution_passed=False,first_step=observed)
    ctl.write_json(ROOT/"runs/R18/first-step-integration.json",proof)
    state["events"].append(dict(at=ctl.stamp(),command="prospective_same_original_case_start",result=proof))
    ctl.write_json(ROOT/"state/continuation.json",state)
    project=read("state/project-todo.json")
    project["prospective_original_case_R18"]=dict(plan="runs/R18/PLAN.md",amendment="runs/R18/amendment.json",
        status="real_first_step_only",original_task="R16-02",old_attempt_unpassed=True,
        full_case_passed=False,evidence="runs/R18/first-step-integration.json")
    ctl.write_json(ROOT/"state/project-todo.json",project)
    ctl.synchronize(ROOT,state)
    cp=read("state/checkpoint.json")
    cp.update(current_candidate="runs/R17/candidate/C10-lock.json",R17_status="done_with_actual_next_step",
        R18_plan="runs/R18/PLAN.md",R18_status="real_first_step_only",
        next_action="Resume original R16-02 full solve from retained first-step artifacts under C10.",
        current_native_pending=[],unpublished_work=True)
    ctl.write_json(ROOT/"state/checkpoint.json",cp)
    assert not ctl.validate(state,ROOT),ctl.validate(state,ROOT)
print(json.dumps(dict(same_case="R16-02",same_actor=True,old_attempt_preserved=True,
    old_38_unchanged=True,other_45_unchanged=True,full_paper_pass=False,R17_next="actual_start_done")))
