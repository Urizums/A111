"""Record observed source publication; receipts commit is a separate observation."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"scripts"))
import continuation as ctl
def read(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
raw=read("runs/R17/publication/source-ci-final-command.json")
assert raw["state"]=="finished" and raw["exit_code"]==0
ci=json.loads(raw["stdout"])
assert ci["headSha"]=="0258f31753a1a96126c66a4681c694696c3d2371"
assert ci["status"]=="completed" and ci["conclusion"]=="success"
assert all(j["conclusion"]=="success" for j in ci["jobs"])
assert read("runs/R17/publication/source-push-command.json")["exit_code"]==0
publication=dict(schema="forge-observed-publication/1",observed_at=ctl.stamp(),
    source_commit=ci["headSha"],repository="https://github.com/Urizums/A111",branch="main",
    source_ci=ci,source_push="runs/R17/publication/source-push-command.json",
    local_regression="runs/R17/final/linux-full-regression-command.json",
    C10_package="runs/R17/package/Forge-C10-meta-workflow.zip",
    product_document_files=9,product_scripts=0,original_case_first_step="runs/R18/first-step-integration.json",
    full_product_acceptance_passed=False,complete_contest_paper_delivered=False,
    limits="Exact source commit and observed CI only; later receipt commit CI is separate. Old experiment failures are not regraded.")
ctl.write_json(ROOT/"runs/R17/publication/publication.json",publication)
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    state["deliveries"]["C10-meta-workflow-and-original-case-first-step"]=dict(status="delivered",
        evidence=ctl.ref(ROOT,"runs/R17/publication/publication.json"),source_commit=ci["headSha"],
        full_acceptance=False,at=ctl.stamp())
    state["execution"].update(current_publication="runs/R17/publication/publication.json",
        current_source_commit=ci["headSha"],current_source_ci=ci["url"],
        current_source_ci_observed="success",receipt_commit_observation="pending")
    state["events"].append(dict(at=ctl.stamp(),command="observed_C10_source_publication",
        result=dict(source_commit=ci["headSha"],source_ci="success",full_product_pass=False)))
    ctl.write_json(ROOT/"state/continuation.json",state)
    ctl.synchronize(ROOT,state)
    cp=read("state/checkpoint.json")
    cp.update(current_candidate="runs/R17/candidate/C10-lock.json",current_report="runs/R17/REPORT.md",
        current_native_pending=[],R17_status="published_with_actual_R18_first_step",
        next_action="Continue same original R16-02 with a new versioned stacking/constraint slice; full paper and independent review pending.",
        publication="runs/R17/publication/publication.json",source_commit=ci["headSha"],
        source_ci_observed="success",unpublished_work=False,
        receipt_commit_pending_at_this_snapshot=True)
    ctl.write_json(ROOT/"state/checkpoint.json",cp)
    assert not ctl.validate(state,ROOT),ctl.validate(state,ROOT)
print(json.dumps(dict(source_commit=ci["headSha"],source_ci="success",full_product_pass=False)))
