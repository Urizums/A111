"""Serialize completed observations and bounded stops; development helper only."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import continuation as ctl

def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def budget():
    return {f"L{i}": dict(used=n, limit=2) for i, n in enumerate([1, 0, 3, 0, 1, 2, 2, 0], 1)}

REPORT = """# R14 研发与独立诊断报告

C9 已形成八份纯 Markdown 的 Forge meta-workflow：通用搭建、验收、协作、接续、数学建模、前端和来源筛选。源锁、结构检查及全新解包字节比较通过；包内没有脚本、测试或执行器，没有安装个人 skill。C9 作者累计2/2（源码修复0，编排纠正2），冻结正文不再修改。用户包在工作区 outputs/Forge-C9-meta-workflow.zip。

八个新上下文分别使用同一固定微型题、同一 C9 与最低验收约束，已实际交付工作流、代码、数字结果、图、短论文和原材料/执行检查。99份当前工件冻结在 math-output-lock.json，原失败产物另存且保留。独立核查者重新计算、枚举24,076个可行整数方案，实际查看八张图并读取真实命令记录；自己的首次 IndexError 和两轮累计纠正也保留。

初始盲审为39 pass/1 fail；在同一审查者的第二轮原要求与定位核查后，为38 pass/2 fail。第二轮收到协调者关于预算口径与文件定位的反馈，不能冒充完全盲审；初始文件未改写。逐项依据在 trials/math/independent-review/review.json、addendum.json；后者纠正 L1/L2 源码路径为 solver.py，并保留初始错误定位。

| 层级 | m1 工作流 | m2 预测验证 | m3 原目标优化 | m4 图表论文 | m5 检查及预算 | 原案例修正 |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | pass | pass | pass | pass | pass | 1/2 |
| L2 | pass | pass | pass | pass | pass | 0/2 |
| L3 | pass | pass | pass | pass | fail | 3/2，停止 |
| L4 | pass | pass | pass | pass | pass | 0/2 |
| L5 | pass | pass | pass | pass | pass | 1/2 |
| L6 | pass | pass | pass | pass | pass | 2/2，停止继续修改 |
| L7 | pass | pass | fail | pass | pass | 2/2，停止 |
| L8 | pass | pass | pass | pass | pass | 0/2 |

L1 同一原 actor 修复了把第9周预测用于历史回测的问题，原7份产物保留在 attempt-0；当前回测按真实目标周计算。L3 生产者自报2/2漏计路径失败后的实际恢复，协调者及第二轮审查累计为3/2；缺少原始失败路径命令回执的事实保留，不能把转录当原始命令记录。L6 文档有不存在的 final 回执定位，审查的 addendum 给出实际 smoke-valid-command.json 和 smoke-malformed-command.json，原生产者文件不在边界后补改。L8 后续真实复现记录明确为后续调用，不冒充最初运行回执。

L7 把预测向上取整后优化了不同目标。按原始未取整预测，最优配置为 A/B/C=28/2/30，目标264.9285714286元；L7方案28/1/31按原目标为266.1428571429元，所报270元属于取整后的目标。论文如实描述取整仍不能替代原问题最优性。这一实质失败说明验收者必须从原题重算目标，不能只检查脚本退出0、方案可行或作者声称最优。

八层提示是用户累计层级的操作化摘要，并非逐字受控实验；所有层级同时收到详细最低交付要求。不能据此说“一句 Level1 提示足以做真实竞赛”，也不能按不同验证折的 MAE 排名、声称 Level 越高越好，或推断奖项、性能泛化及层级因果。R14-02完成的是八案例试运行与原要求诊断；两个单案例失败仍保留，并非全层行为通过。

前端原 actor 保留 HTML/workflow 和部分交接，但没有浏览器、键盘、视口或截图运行证据。父线程 file 页面请求被宿主明确拒绝并禁止绕过；没有换协议、浏览器、CDP或间接执行达到被拒绝结果。静态算术检查不满足 f2–f5。R14-03 blocked、原案例0/2；R14-04两领域联合验收和R14-next同样blocked；R15未启动，数学诊断不能替代前端依赖。

2026 MathorCup 大数据赛事的官方时间补充在 research_root/verified-update.md。这一微型题仍是八周三站点自建离线题，不是官方赛题；AI细则未在取得的官方附件中明确。用户新授权的上半年真实原题独立试解见 runs/R16/PLAN.md 与 REPORT.md，它保留而不替换本阶段失败。

本轮可交付 C9 文档候选及诊断证据；完整产品门槛仍未通过。C8、旧源码锁、原38任务、R08/R10/R11/R13失败和所有预算保持不变，当前主阶段仍是R08。没有后台任务、竞赛提交或奖项结论。
"""

with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    original = read("runs/R14/baseline.json")["historical_task_hashes"]
    for tid, digest in original.items():
        assert ctl.identity(ctl.task_map(state)[tid]) == digest, tid
    assert not ctl.validate(state, ROOT), ctl.validate(state, ROOT)
    prior = ROOT / "runs/R14/resumption/report-before-final.md"
    assert not prior.exists()
    prior.write_bytes((ROOT / "runs/R14/REPORT.md").read_bytes())
    (ROOT / "runs/R14/REPORT.md").write_text(REPORT, encoding="utf-8", newline="\n")
    review = read("runs/R14/trials/math/independent-review/review.json")
    addendum = read("runs/R14/trials/math/independent-review/addendum.json")
    matrix = {level: {key: item["status"] for key, item in values.items()}
              for level, values in review["levels"].items()}
    matrix["L3"]["m5"] = addendum["verdict_changes"]["L3_m5"]["addendum"]
    assert matrix["L7"]["m3"] == "fail" and matrix["L3"]["m5"] == "fail"
    ctl.write_json(ROOT / "runs/R14/math-comparison.json", dict(
        schema="forge-observed-level-comparison/1", matrix=matrix,
        counts=addendum["revised_counts"]["after_addendum"], case_budgets=budget(),
        evidence=["runs/R14/math-output-lock.json",
                  "runs/R14/trials/math/independent-review/review.json",
                  "runs/R14/trials/math/independent-review/addendum.json",
                  "runs/R14/trials/math/independent-review/independent-calculations.json",
                  "runs/R14/resumption/L3-budget-decision.json"],
        limits="One synthetic case per level, shared detailed acceptance; distinct validation folds; no ranking, prompt causality, award or full contest inference.",
        author_budget=dict(used=2, limit=2), reviewer_budget=dict(used=2, limit=2),
        combined_R14_04_status="blocked", producer_self_check_is_independent=False))
    t = ctl.task_map(state)["R14-02"]
    result = dict(task_id=t["id"], attempt_id=t["attempts"][-1]["id"],
        requirements_hash=t["attempts"][-1]["requirements_hash"],
        criteria=[
            dict(id="a1", status="pass", evidence=["runs/R14/math-output-lock.json", "runs/R14/math-comparison.json"]),
            dict(id="a2", status="pass", evidence=["runs/R14/REPORT.md",
                "runs/R14/trials/math/independent-review/review.json",
                "runs/R14/trials/math/independent-review/addendum.json"])],
        effect=dict(target="Eight frozen level workflow trials and descriptive original-requirement diagnosis",
            hypothesis="Actual independent checks can expose defects that producer smoke alone misses",
            baseline="No independent original-objective/budget diagnosis",
            conditions="One synthetic eight-week fixture, fixed C9 and common detailed acceptance; separate fresh producers",
            observations="All eight trials produced artifacts; 38/40 diagnostic requirements pass, L7 m3 and L3 m5 fail; failures preserved",
            limits="Task completion is production and honest diagnosis, not universal per-case pass or combined frontend/math acceptance",
            metrics=dict(pass_count=38, fail_count=2, unverified_count=0, case_budgets=budget(), tokens=None, cost=None)),
        next_action="Retain failed original cases and blocked frontend/combined gate; no post-boundary repairs.")
    ctl.write_json(ROOT / "runs/R14/R14-02-result.json", result)
    ctl.finish(state, ROOT, "R14-02", "runs/R14/R14-02-result.json")
    t = ctl.task_map(state)["R16-02"]
    t["repairs_used"] = 2
    result = dict(task_id=t["id"], attempt_id=t["attempts"][-1]["id"],
        requirements_hash=t["attempts"][-1]["requirements_hash"],
        criteria=[dict(id=p["id"], status="blocked",
            evidence=["runs/R16/budget-decision.json", "runs/R16/solution/attempt-ledger.md", "runs/R16/REPORT.md"])
            for p in t["acceptance"]],
        effect=dict(target="Original official MathorCup D full solution and paper",
            hypothesis="C9 can organize original full contest work without solution-paper input",
            baseline="Official raw material only",
            conditions="Offline original actor, frozen official data and p1-p6; default cumulative limit2",
            observations="Raw material reading succeeded only after two corrections. Draft solve.py has not run; no model result/full paper.",
            limits="Source acquisition is passed; solution capability, paper consistency and independent acceptance remain unverified",
            metrics=dict(case_used=2, case_limit=2, source_used=2, source_limit=2,
                candidate_author_used=2, candidate_author_limit=2, solver_runs=0, tokens=None, cost=None)),
        next_action="Await explicit original-case limit increase with used2 retained; no replacement actor or sample.")
    ctl.write_json(ROOT / "runs/R16/R16-02-result.json", result)
    ctl.finish(state, ROOT, "R16-02", "runs/R16/R16-02-result.json")
    for tid in ["R16-03", "R16-04"]:
        ctl.task_map(state)[tid].update(status="blocked",
            blocker="R16-02 stopped at original cumulative budget2/2 without model results or a complete paper.",
            evidence=[ctl.ref(ROOT, "runs/R16/R16-02-result.json")],
            next_action="Preserve original dependencies; do not dispatch review or claim full report until original solution gate passes.")
    completed = [dict(worker=f"/root/r14_math_l{i}", state="terminal_observation_received",
        evidence=f"runs/R14/trials/math/L{i}/result.json", case_corrections_used=n,
        case_limit=2, actual_model=None) for i, n in enumerate([1, 0, 3, 0, 1, 2, 2, 0], 1)]
    completed += [
        dict(worker="/root/r14_frontend", state="terminal_runtime_blocked", case_corrections_used=0, case_limit=2,
            evidence="runs/R14/R14-03-result.json", actual_model=None),
        dict(worker="/root/r14_math_independent_final", state="terminal_second_addendum_received", corrections_used=2, limit=2,
            evidence="runs/R14/trials/math/independent-review/addendum.json", actual_model=None),
        dict(worker="/root/r16_official_problem_packet", state="terminal_official_material_delivered", corrections_used=2, limit=2,
            evidence="runs/R16/source/source-manifest.json", actual_model=None),
        dict(worker="/root/r16_original_solution", state="terminal_paused_original_budget_boundary", corrections_used=2, limit=2,
            evidence="runs/R16/budget-decision.json", actual_model=None)]
    state["execution"].update(native_pending=[], current_native_pending=[],
        completed_native_R14_R16_observation=completed, completed_native_R14_observation=completed[:9],
        session_state="R14_diagnostic_complete_R16_original_budget_stop",
        checkpoint_reason="Original failures retained; no full real-paper delivery. Explicit original-case limit change pending.",
        current_report="runs/R16/REPORT.md", R14_report="runs/R14/REPORT.md",
        R16_plan="runs/R16/PLAN.md", next_plan="runs/R16/PLAN.md",
        R16_solution_actor="/root/r16_original_solution", R16_case_budget=dict(used=2, limit=2),
        R14_case_budgets=budget(), monitor_enabled=False,
        coordinator_heartbeat=ctl.stamp(), tokens=None, cost=None)
    state["events"].append(dict(at=ctl.stamp(), command="R14_R16_checkpoint",
        result=dict(old_task_count=len(original), old_tasks_preserved=True, actual_pending_actors=[],
            R14_diagnostic_failures=["L3:m5", "L7:m3"], R16_case_stop="2/2",
            R15_started=False, R16_complete_paper=False, full_acceptance_passed=False)))
    ctl.write_json(ROOT / "state/continuation.json", state)
    for phase_id in ["R14", "R16"]:
        phase = ctl.phase_view(read(f"state/phases/{phase_id}.json"), state)
        phase["tasks"][-1].update(status="blocked", blocker=(
            "R14-03 browser runtime and R14-04 combined acceptance remain blocked; no R15 first step."
            if phase_id == "R14" else "Original R16 solution stopped2/2; no full paper/review; no successor first step."),
            evidence=[f"runs/{phase_id}/REPORT.md"],
            next_action="Resolve original prerequisite within explicit authorization; preserve failed cases and budgets.")
        ctl.write_json(ROOT / f"state/phases/{phase_id}.json", phase)
    ctl.synchronize(ROOT, state)
    checkpoint = read("state/checkpoint.json")
    checkpoint.update(current_validation="C9 structure/package identity passed. R14 math diagnostics38pass/2fail. Frontend/combined gate blocked. R16 source passed, solution stopped2/2 without paper.",
        next_action="Explicit user decision needed only for increasing R16-02 original cumulative limit; preserve used2 and original actor/input/criteria.",
        current_R14_report="runs/R14/REPORT.md", current_R16_report="runs/R16/REPORT.md",
        C9_candidate="runs/R14/candidate/C9-lock.json", C9_package="runs/R14/package/Forge-C9-meta-workflow.zip",
        R16_budget_decision="runs/R16/budget-decision.json", current_native_pending=[],
        termination="Concrete bounded checkpoint; all current actors terminal, historical unresolved call retained; no automatic background work.",
        unpublished_work=True)
    ctl.write_json(ROOT / "state/checkpoint.json", checkpoint)
    project = read("state/project-todo.json")
    project["domain_workflows_R14"].update(status="diagnostics_complete_combined_acceptance_blocked",
        report="runs/R14/REPORT.md", math_result="runs/R14/R14-02-result.json",
        counts=dict(pass_count=38, fail_count=2), case_budgets=budget(), R15_started=False)
    project["real_historical_problem_R16"].update(status="original_solution_budget_blocked",
        report="runs/R16/REPORT.md", budget_decision="runs/R16/budget-decision.json",
        source_status="done", solution_status="blocked", original_case_used=2, original_case_limit=2,
        full_paper_delivered=False, independent_review_started=False)
    ctl.write_json(ROOT / "state/project-todo.json", project)
    assert not ctl.validate(state, ROOT), ctl.validate(state, ROOT)
    for tid, digest in original.items():
        assert ctl.identity(ctl.task_map(state)[tid]) == digest, tid
print(json.dumps(dict(old_tasks_preserved=len(original), tasks=len(state["tasks"]), active_phase="R08",
    R14_math_task="done_observation_only", R14_diagnostic_pass=38, R14_diagnostic_fail=2,
    R16_solution="blocked2/2", full_paper_delivered=False, current_pending_actors=0)))
