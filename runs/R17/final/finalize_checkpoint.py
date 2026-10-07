"""Save completed checks and the honest unfinished original-case frontier."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"scripts"))
import continuation as ctl
def read(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
receipt=read("runs/R17/final/linux-full-regression-command.json")
assert receipt["state"]=="finished" and receipt["exit_code"]==0
assert "Ran 62 tests" in receipt["stderr"] and "OK" in receipt["stderr"]
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    task=ctl.task_map(state)["R16-02"]
    assert task["status"]=="in_progress" and task["repairs_used"]==3
    assert task["prospective_continuation"]["legacy_repairs_used"]==2
    state["execution"].update(current_report="runs/R17/REPORT.md",current_candidate="runs/R17/candidate/C10-lock.json",
        current_native_pending=[],native_pending_current=[],
        completed_native_R17=[
            dict(worker="/root/r17_policy_review",state="final_notification_received",
                 evidence="runs/R17/review/C10-review-evidence.json",actual_model=None),
            dict(worker="/root/r17_research_trial",state="final_notification_received",
                 evidence="runs/R17/research-trial/result.json",actual_model=None),
            dict(worker="/root/r17_controller_review",state="final_notification_received",
                 evidence="runs/R17/controller-review/addendum2.json",actual_model=None)],
        current_task_process_state="R16-02 unfinished at checkpoint; producer first slice terminal; no background worker.",
        current_full_regression="runs/R17/final/linux-full-regression-command.json",
        current_regression_scope="4742 byte-verified staged development files in local Linux export; 62 scripts tests; not general product acceptance",
        R17_status="delivered_policy_with_actual_R18_first_step")
    state["events"].append(dict(at=ctl.stamp(),command="final_C10_and_original_case_checkpoint",
        result=dict(document_files=9,bundled_scripts=0,script_tests=62,
            original_case_complete=False,original_case_actor_terminal=True,old_failures_retained=True)))
    ctl.write_json(ROOT/"state/continuation.json",state)
    ctl.synchronize(ROOT,state)
    cp=read("state/checkpoint.json")
    cp.update(current_candidate="runs/R17/candidate/C10-lock.json",
        current_report="runs/R17/REPORT.md",current_native_pending=[],R17_status="done_with_real_successor",
        R18_status="actual_first_slice_only",next_action="Continue original R16-02 from frozen first slice: next version stacking/constraint baseline and original Q1/Q2; full paper and independent review pending.",
        final_checks="runs/R17/final/linux-full-regression-command.json",unpublished_work=True)
    ctl.write_json(ROOT/"state/checkpoint.json",cp)
    assert not ctl.validate(state,ROOT),ctl.validate(state,ROOT)
print(json.dumps(dict(tests=62,C10_documents=9,original_case="checkpointed_incomplete",
    live_native_workers=0,main_R08_unpassed=True)))
