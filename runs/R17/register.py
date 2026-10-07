"""Register new-policy tasks without changing any pre-change task record."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import continuation as ctl
def read(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))
contract=read("runs/R17/acceptance.json")
definitions=[
    ("R17-01","制作进展政策/搜索规划C10及兼容实现","root",[],
     ["runs/R17/candidate/","scripts/continuation.py","scripts/test_continuation.py"],
     [dict(id="a1",assertion="九份纯文档源锁/链接/frontmatter检查，用户前瞻政策及原历史均保留"),
      dict(id="a2",assertion="研发控制器可选新政策执行有实际回归，旧固定模式保持且不作为技能运行依赖")]),
    ("R17-02","新上下文政策与场景独立核查","/root/r17_policy_review",["R17-01"],
     ["runs/R17/review/"],contract["policy"]+contract["independent_review"]),
    ("R17-03","实际多步检索与上下文整理试运行","/root/r17_research_trial",["R17-01"],
     ["runs/R17/research-trial/"],contract["research_trial"]),
    ("R17-04","历史/独立结果/纯文档包装与接续整合","root",["R17-01","R17-02","R17-03"],
     ["runs/R17/package/","runs/R17/final/"],contract["delivery"])
]
with ctl.locked(ROOT):
    state=ctl.load(ROOT)
    old=read("runs/R17/baseline.json")["historical_task_hashes"]
    for tid,digest in old.items():
        assert ctl.identity(ctl.task_map(state)[tid])==digest,tid
    for i,(tid,title,owner,deps,writes,acceptance) in enumerate(definitions):
        assert tid not in ctl.task_map(state)
        state["tasks"].append(dict(id=tid,title=title,queue="challenges",category="user_progress_and_search_policy",
            priority=50+i,owner=owner,depends_on=deps,write_paths=writes,status="planned",
            acceptance=acceptance,inputs=["runs/R17/scope-decision.json","runs/R17/acceptance.json",
                "runs/R17/input-lock.json","runs/R17/candidate/C10-lock.json"],
            next_action=title,evidence=[],attempts=[],repairs_used=0,repair_limit=None,blocker=None,
            execution_policy=dict(mode="progress_guard",source=ctl.ref(ROOT,"runs/R17/scope-decision.json"),
                progress_state="ready",deadline_utc=None,
                stop_conditions=["verified requested output","actual resource or permission boundary",
                    "unsupported unchanged path; diagnose before further execution"])))
    start=ctl.begin(state,ROOT,"R17-01","runs/R17/prepare-command.json")
    result=dict(task_id="R17-01",attempt_id=start["id"],requirements_hash=start["requirements_hash"],
        criteria=[dict(id="a1",status="pass",evidence=["runs/R17/freeze-candidate-command.json",
            "runs/R17/structure-command.json","runs/R17/baseline.json","runs/R17/author-ledger.json"]),
            dict(id="a2",status="pass",evidence=["runs/R17/controller-regression-command.json"])],
        effect=dict(target="Document policy and opt-in development-queue compatibility",
            hypothesis="Classified evidence-backed continuation avoids arbitrary whole-task two-error stops",
            baseline="Original fixed cap; two local source-read recoveries stopped the full real-paper case",
            conditions="Explicit user change; nine C10 docs and local controller tests",
            observations="Actual structure/link/hash checks and 12 controller tests pass; author errors retained",
            limits="Author/structure/local guards only, independent scenario/research/implementation conclusions separate",
            metrics=dict(document_files=9,controller_tests=12,bundled_scripts=0,tokens=None,cost=None)),
        next_action="Receive independent policy and actual search observations; preserve source lock.")
    ctl.write_json(ROOT/"runs/R17/R17-01-result.json",result)
    ctl.finish(state,ROOT,"R17-01","runs/R17/R17-01-result.json")
    for tid in ["R17-02","R17-03"]:
        ctl.begin(state,ROOT,tid,"runs/R17/freeze-candidate-command.json")
    state["execution"].update(current_coordinator="root-codex-r17-policy",
        current_report="runs/R17/PLAN.md",current_candidate="runs/R17/candidate/C10-lock.json",
        current_user_steering="Authorized implementation of classified progress and planned-search policy.",
        repair_policy_review="runs/R16/rule-audit/REPORT.md",
        R17_policy="runs/R17/scope-decision.json",
        R16_budget_proposal_status="superseded_by_user_policy_change_no_numeric_increase",
        current_native_pending=[
            dict(worker="/root/r17_research_trial",task="R17-03",state="creation_observed",actual_model=None),
            dict(worker="/root/r17_controller_review",task="R17-04_support",state="creation_observed",actual_model=None)],
        completed_native_R17=[dict(worker="/root/r17_policy_review",
            evidence="runs/R17/review/C10-review-evidence.json",state="final_notification_received",actual_model=None)])
    state["events"].append(dict(at=ctl.stamp(),command="register_user_progress_policy",
        result=dict(old_tasks_preserved=46,new_tasks=4,global_two_error_limit=False,
            original_case_regraded=False,actual_child_creations=[
                "/root/r17_policy_review","/root/r17_research_trial","/root/r17_controller_review"])))
    ctl.write_json(ROOT/"state/continuation.json",state)
    rows=[]
    for tid,*_ in definitions:
        t=ctl.task_map(state)[tid]
        rows.append({k:t[k] for k in ["id","title","owner","depends_on","write_paths","status","blocker","next_action"]} |
            dict(acceptance=[a["assertion"] for a in t["acceptance"]],evidence=[e["path"] for e in t["evidence"]]))
    rows.append(dict(id="R17-next",title="启动下一阶段任务",owner="root",
        depends_on=[d[0] for d in definitions],write_paths=["state/","runs/"],
        status="planned",acceptance=["原要求通过并有真实后继首步；否则保留真实阻塞"],
        evidence=[],blocker=None,next_action="Select original-identity prospective continuation only after current policy gates."))
    ctl.write_json(ROOT/"state/phases/R17.json",dict(schema="forge-phase-todo/1",phase_id="R17",
        goal="用户授权的分类恢复、进展管理、搜索规划和上下文筛选",tasks=rows))
    ctl.synchronize(ROOT,state)
    cp=read("state/checkpoint.json")
    cp.update(next_action="Finish C10 independent policy/search/controller checks; then package and record prospective continuation.",
        current_candidate="runs/R17/candidate/C10-lock.json",R17_plan="runs/R17/PLAN.md",
        R16_budget_proposal_status="superseded_by_user_policy_change_no_numeric_increase",
        unpublished_work=True)
    ctl.write_json(ROOT/"state/checkpoint.json",cp)
    project=read("state/project-todo.json")
    project["progress_search_policy_R17"]=dict(plan="runs/R17/PLAN.md",scope="runs/R17/scope-decision.json",
        candidate="runs/R17/candidate/C10-lock.json",status="independent_checks_in_progress",
        old_verdicts_unchanged=True,global_two_error_limit=False)
    ctl.write_json(ROOT/"state/project-todo.json",project)
    assert not ctl.validate(state,ROOT),ctl.validate(state,ROOT)
print(json.dumps(dict(new_tasks=4,total_tasks=len(state["tasks"]),old_46_unchanged=True,
    new_policy="progress_guard",main_phase_unchanged="R08")))
