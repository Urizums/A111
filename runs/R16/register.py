"""Register newly authorized real-question branch; preserves historical tasks."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import continuation as ctl

contract = json.loads((ROOT / "runs/R16/acceptance-draft.json").read_text(encoding="utf-8"))
definitions = [
    ("R16-01", "取得官方真实赛题和中性输入包", "official_source_luna", [], ["runs/R16/source/"], contract["source_gate"]),
    ("R16-02", "不读既有解法的原创完整试解与论文", "fresh_executor_luna", ["R16-01"], ["runs/R16/solution/"], contract["execution_gate"]),
    ("R16-03", "原题原数据与论文代码的独立核验", "fresh_reviewer_luna", ["R16-02"], ["runs/R16/review/"], contract["independent_review_gate"]),
    ("R16-04", "汇总真实证据与大数据赛迁移边界", "root", ["R16-01", "R16-02", "R16-03"], ["runs/R16/report/"],
     [dict(id="a1", assertion="逐问证据与失败真实保留，原题试解/复现/独立核验/竞争力推论分开，不改旧失败预算"),
      dict(id="a2", assertion="明确常规赛与大数据赛迁移的依据和差异，交付论文及工件与可执行下一项而不保证奖项")]),
]
with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    baseline = json.loads((ROOT / "runs/R14/baseline.json").read_text(encoding="utf-8"))
    existing = ctl.task_map(state)
    for tid, digest in baseline["historical_task_hashes"].items():
        assert ctl.identity(existing[tid]) == digest, tid
    for index, (tid, title, owner, deps, writes, criteria) in enumerate(definitions):
        assert tid not in existing
        inputs = ["runs/R16/PLAN.md", "runs/R16/scope-decision.json"]
        if index:
            inputs += ["runs/R16/acceptance.json", "runs/R16/input-lock.json", "runs/R14/candidate/C9-lock.json"]
        state["tasks"].append(dict(id=tid, title=title, queue="challenges", category="new_user_real_historical_problem",
            complexity=3, priority=40 + index, depends_on=deps, owner=owner, write_paths=writes, inputs=inputs,
            acceptance=criteria, status="planned", evidence=[], attempts=[], repairs_used=0, repair_limit=2,
            blocker=None, next_action=title))
    start = ctl.begin(state, ROOT, "R16-01", "runs/R16/source/fetch-receipt.json")
    rows = []
    for tid, *_ in definitions:
        t = ctl.task_map(state)[tid]
        rows.append({k: t[k] for k in ["id", "title", "owner", "depends_on", "write_paths", "status", "blocker", "next_action"]} |
                    dict(acceptance=[a["assertion"] for a in t["acceptance"]], evidence=[]))
    rows[0]["evidence"] = ["runs/R16/source/fetch-receipt.json"]
    rows.append(dict(id="R16-next", title="启动下一阶段任务", owner="root",
        depends_on=[t[0] for t in definitions], write_paths=["state/", "runs/"],
        acceptance=["前驱完成且有下一阶段计划/首项/真实首步，否则保持真实阻塞"],
        status="planned", evidence=[], blocker=None, next_action="Choose a useful executable successor after original real-question gates"))
    ctl.write_json(ROOT / "state/phases/R16.json", dict(schema="forge-phase-todo/1", phase_id="R16",
        goal="子agent不接触既有解法的2026真实MathorCup原创试解", tasks=rows))
    state["events"].append(dict(at=ctl.stamp(), command="register_new_user_historical_problem_scope",
        result=dict(plan="runs/R16/PLAN.md", actual_official_fetch="runs/R16/source/fetch-receipt.json", previous_gate_bypass=False)))
    state["execution"].update(current_report="runs/R14/REPORT.md", R16_plan="runs/R16/PLAN.md",
        R16_source_actor="/root/r16_official_problem_packet", R16_original_solution_search=False)
    ctl.write_json(ROOT / "state/continuation.json", state)
    ctl.synchronize(ROOT, state)
    project = json.loads((ROOT / "state/project-todo.json").read_text(encoding="utf-8"))
    project["real_historical_problem_R16"] = dict(plan="runs/R16/PLAN.md", scope="runs/R16/scope-decision.json",
        status="official_source_fetch_actually_started", new_user_scope=True, old_cases_reset=False)
    ctl.write_json(ROOT / "state/project-todo.json", project)
print(json.dumps(dict(R16_source_started=True, actual_official_fetch=True, active_phase_unchanged="R08", old_tasks_preserved=38)))
