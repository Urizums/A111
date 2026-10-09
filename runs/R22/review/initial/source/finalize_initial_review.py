"""Write the frozen-scope first judgment from independently rebuilt evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
INITIAL = ROOT / "runs/R22/review/initial"
RECEIPTS = INITIAL / "receipts"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    reconstruction = json.loads((INITIAL / "rebuild-v5/results/reconstruction.json").read_text(encoding="utf-8"))
    comparison = json.loads((INITIAL / "comparison-v2.json").read_text(encoding="utf-8"))
    clean = json.loads((INITIAL / "clean-rerun-equivalence.json").read_text(encoding="utf-8"))
    crosscheck_receipt = json.loads((RECEIPTS / "68-report-crosscheck.json").read_text(encoding="utf-8"))
    crosscheck = json.loads(crosscheck_receipt["stdout"])
    author_lock = json.loads((ROOT / "runs/R22/execution-lock.json").read_text(encoding="utf-8"))
    author_entries = {item["path"]: item for item in author_lock["files"]}
    author_receipts = []
    for number in range(1, 19):
        name = f"{number:04d}-" + {
            1: "read-authorized-sources", 2: "read-implementation", 3: "read-science-source",
            4: "read-lineage", 5: "read-contract-and-references", 6: "freeze-science",
            7: "first-science-v1", 8: "pdf-runtime-locations", 9: "clean-replay",
            10: "read-produced-results", 11: "existing-output-refused", 12: "author-check",
            13: "pdf-artifact-marker", 14: "build-report", 15: "render-pdf",
            16: "read-final-body", 17: "finalize-delivery", 18: "final-readonly-verification",
        }[number] + ".json"
        relative = f"runs/R22/execution/receipts/{name}"
        path = ROOT / relative
        raw = path.read_bytes()
        record = json.loads(raw)
        locked = author_entries[relative]
        identity_ok = len(raw) == locked["size_bytes"] and hashlib.sha256(raw).hexdigest() == locked["sha256"]
        author_receipts.append({
            "path": relative,
            "identity_matches_execution_lock": identity_ok,
            "argv": record.get("argv"),
            "state": record.get("state"),
            "begin": record.get("begin"),
            "end": record.get("end"),
            "exit_code": record.get("exit_code"),
            "stdout_bytes": len(record.get("stdout_base64", "")) * 3 // 4,
            "stderr_bytes": len(record.get("stderr_base64", "")) * 3 // 4,
        })
    local_receipts = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RECEIPTS.glob("*.json"))]
    local_nonzero = [r for r in local_receipts if r.get("exit_code") not in (0, None)]
    statuses = {
        "h1": "pass",
        "h2": "pass",
        "h3": "pass",
        "h4": "pass",
        "h5": "pass",
        "h6": "fail",
    }
    findings = [
        {"id": "h1", "status": statuses["h1"], "evidence": ["rebuild-v5/results/reconstruction.json", "rebuild-v5/source_rebuild/summary.json", "comparison-v2.json"], "finding": "Raw revisions, duplicate collapse, weather/demand checks, as-of training and feature provenance were reconstructed from locked inputs. Scoring labels were kept out of as-of training."},
        {"id": "h2", "status": statuses["h2"], "evidence": ["rebuild-v5/source_rebuild/residual_coordinates_rebuilt.csv", "rebuild-v5/source_rebuild/source_forecasts_rebuilt.csv", "rebuild-v5/uncertainty/pool_membership.csv", "comparison-v2.json"], "finding": "Both routes and all six source-origin/method forecasts were independently reconstructed. Errors use mature raw labels minus the published 10-decimal point. Exact 96-coordinate/day readiness uses the mature-version arrival time; a qualifying day remains eligible when another same-window day is incomplete. No current-window residual was used."},
        {"id": "h3", "status": statuses["h3"], "evidence": ["rebuild-v5/results/keys.csv", "rebuild-v5/results/group_*.csv", "rebuild-v5/results/daily.csv", "rebuild-v5/results/paired_daily.csv", "comparison-v2.json"], "finding": "Each route has 4,032 keys at each of three origins. All preset horizon, early/late, activity, activity-by-band, activity-by-stage, store, item, date and paired-day tables were compared. The first two windows have 84 unique dates; the third overlaps the prior window by 25 dates and remains separately described. Empty activity cells are explicitly retained with zero sample and not-estimable status."},
        {"id": "h4", "status": statuses["h4"], "evidence": ["rebuild-v5/validation/boundaries.json", "rebuild-v5/results/daily_solver.csv", "rebuild-v5/results/daily.csv", "rebuild-v5/uncertainty/scenarios_*.npz"], "finding": "Real-valued scenarios and intervals are accepted, including valid intervals that do not contain the point forecast. Actions are integer and feasible. A 3-coordinate exhaustive oracle matches the solver minimum; 95/96, late-by-one-second, equal-origin, unfinished-day, invalid domains, invalid scenarios and capacity/budget boundaries were exercised. All 252 solver rows have status 0 and gap 0; maximum recomputed objective/bound difference is about 1.01e-10."},
        {"id": "h5", "status": statuses["h5"], "evidence": ["source-freeze-v10.json", "receipts/33-independent-reconstruction-v5.json", "receipts/46-clean-explicit-output-rerun.json", "clean-rerun-equivalence.json", "receipts/*.json"], "finding": "The independent source was frozen before reconstruction. The clean explicit-output replay finished with exit 0 and matches independent rebuilt tables and scenario tensors. Source replay and raw reconstruction are separate evidence. Initial reviewer implementation errors and repairs remain in versioned sources and receipts."},
        {"id": "h6", "status": statuses["h6"], "evidence": ["runs/R22/execution/report-v1/REPORT.md", "runs/R22/execution/report-v1/REPORT.pdf", "receipts/71-pdfinfo.json", "receipts/72-render-final-pdf.json", "final-pdf-page-01.png..final-pdf-page-13.png", "receipts/69-compact-crosscheck-findings.json"], "finding": "The complete Chinese body and all 13 rendered PDF pages were visually inspected. The report is readable and its caveats, units, scope, charts, grouping tables, and solver limitations are generally consistent with the rebuilt results. One internal numeric inconsistency remains: the 09-19/W table prints waste 340.07 yuan/day while nearby prose prints 340.08; independent value is exactly 340.075 yuan/day, so the two displayed values disagree at the stated precision. First judgment: fail."},
    ]
    result = {
        "schema": "r22-independent-first-review/1",
        "review_domain": "runs/R22/review/initial/",
        "criterion_statuses": statuses,
        "criteria": findings,
        "production_artifact_counts": {"origins": 3, "routes": 2, "keys_per_route_origin": 4032, "total_route_origin_rows": reconstruction["rows"], "source_trace_coordinates": reconstruction["source_rebuild"]["source_rows"], "solver_days": 252, "pdf_pages_visualized": 13},
        "window_facts": {"first_two_unique_days": reconstruction["unique_days_first_two_windows"], "third_window_overlap_dates_with_second": reconstruction["third_window_overlap_dates_with_second"]},
        "clean_rerun": clean,
        "author_receipt_metadata_only": author_receipts,
        "author_task_receipt_count": len(author_receipts),
        "author_task_finished_count": sum(r["state"] == "finished" for r in author_receipts),
        "author_task_nonzero_count": sum(r["exit_code"] not in (0, None) for r in author_receipts),
        "reviewer_command_receipts_present_before_finalizer": len(local_receipts),
        "reviewer_nonzero_command_receipts_present_before_finalizer": len(local_nonzero),
        "reviewer_nonzero_receipt_names": [p.name for p in sorted(RECEIPTS.glob("*.json")) if json.loads(p.read_text(encoding="utf-8")).get("exit_code") not in (0, None)],
        "reviewer_failures_are_not_production_repairs": True,
        "actual_model": None,
        "tokens": None,
        "cost": None,
        "limitations": ["Historical labels were already used in R21; this is a fixed, informed historical replay rather than a new blind test.", "Window overlap makes the third origin a separate endpoint replay, not an independent sample.", "Only 4 activity days occur per window; activity-by-stage empty cells are not estimable.", "No external future truth, procurement deployment, causal effect, or competition claim is established.", "The workspace path is not an operating-system isolation boundary."],
    }
    out_json = INITIAL / "result.json"
    with out_json.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    md = """# R22 独立接收首判\n\n## 首判\n\n按冻结的 h1–h6 逐项首判：h1–h5 通过，h6 失败。失败只涉及报告内部一个两位小数数值不一致；没有修改生产源或报告，也没有把接收实现修复当作作者修复。完整机器记录见同目录 `result.json`。\n\n## 数据与复算\n\n独立实现从锁定原始需求和天气输入重建修订折叠、as-of 训练表、169 列特征、两条固定预测路线、每个原点的 42 日预测和情景、整数计划、逐日损失及全部预定分组。产物为三原点×两路线×4,032 键，共 24,192 行。原误差列没有用作真值；残差按成熟版本原始标签减去来源已发布的 10 位小数点预测重算。成熟修订到达时间用于完整 96 坐标日的可用性判断。某个源窗口的另一日期未齐，不会移除其中已合格的日。\n\nR21 来源轨迹重建覆盖六个来源原点×两方法；预测点与来源发布值、训练快照、特征表、促销填补来源和系数均与锁定字节和重建值对照。情景张量、预测区间、整数计划、求解器记录、每日与汇总损失以及所有分组表同生产冻结结果逐项核对，机器比较记录 66 项表格比较和全部情景比较通过。clean replay 在新的显式输出目录完成，退出码为 0；它与独立原始重建的表和情景分别比对通过。clean replay 仅说明可复现，不代替原始重建。\n\n## 边界与分组\n\n96/96 坐标日通过，95/96 拒绝；晚一秒、同源点、未结束日拒绝；已合格日不会被另一个不完整源日连带删除。3 坐标穷举 oracle 枚举 23 个可行行动并匹配求解器最小目标。合法实数情景通过，整数行动和非负/容量/预算边界按协议验证；点预测不必落在中心偏差区间内。所有 252 个逐日求解状态为 0、gap 为 0，重算目标与界最大绝对差约 1.01×10⁻¹⁰。\n\n各预定分组包括早/晚、六个 7 日步长、活动/普通、活动×步长、活动×早晚、12 店、8 品、逐日、配对日和前两窗 84 日描述合并均已复核。前两窗有 84 个唯一日期；第三窗与第二窗重叠 25 日，作为独立端点压力回放报告，没有伪称为新增独立样本。活动空格按 0 日/0 键保留并标为不可估计。\n\n## h1–h6 首判\n\n- **h1 通过。** 锁定原料、重复行折叠、修订单调性、训练可见时间和原点前特征均从原件独立重建；成熟评分标签未回流到原点训练。证据：`rebuild-v5/results/reconstruction.json`、`rebuild-v5/data/`、`comparison-v2.json`。\n- **h2 通过。** 两条路线和六个来源原点×方法的来源预测独立重建；按成熟标签−已发布 point 10 位值重算误差；成熟修订到达、严格更早来源日与完整 96 坐标要求都得到核验。证据：`rebuild-v5/source_rebuild/`、`rebuild-v5/uncertainty/pool_membership.csv`、`comparison-v2.json`。\n- **h3 通过。** 每原点、每路线 4,032 键；所有预定分组、空活动格、逐日与两窗配对差都已比较。窗口重叠及历史标签非盲测限制如实呈现。证据：`rebuild-v5/results/group_*.csv`、`daily.csv`、`paired_daily.csv`。\n- **h4 通过。** 真实 oracle 与晚一秒、95/96、部分有效日、数值域、非法情景、资源上限等边界已运行；实数情景有效，行动 q 为整数；未加点预测必须落在区间内的门槛。证据：`rebuild-v5/validation/boundaries.json`、`daily_solver.csv`。\n- **h5 通过。** 独立源码冻结后才计算；作者命令收据按锁定身份只核对命令、终态、时点和流长度。显式新目录 clean replay 和独立原始重建分开比较且一致。接收侧失败源码版本和非零收据均保留；这些接收工具/命令错误没有更改生产产物。\n- **h6 失败。** 中文正文完整通读，最终 PDF 共 13 页；已逐页渲染并实际查看第 1–13 页，图表和附录可读，没有发现遮挡、截断或空白页。独立重建的 09-19/W 报废为 340.075 元/日；表3显示 340.07，随后正文显示 340.08。正文与表格在同一指标上给出不同的两位小数值，故按报告与数据一致性首判失败。\n\n## 接收工具记录与限制\n\n首轮独立重建的 v1 因 CSV 换行哈希比较方式失败，v2 因目标函数逐键/总和聚合不一致失败，v3 因输出路径参数不符失败；保留原文件并由后续版本修正接收代码后重跑。一次初版比较器字段映射也失败后由 v2 比较器修正。其余非零本地收据是只读/呈现脚本的命令构造错误；均未产生科学结论、未触碰生产文件。所有这些非零收据保持原样。\n\n本目录命令记录均经 `scripts/record_command.py` 保存；实际执行、结束时间、退出码和完整 stdout/stderr 仍以每个 receipt 原件为准。author receipts 只读取命令、起止、状态、退出码及流长度，不读取其中作者结果或自检语义。R22 execution-lock、source-delivery-lock 与 review source freeze 记录锁定身份；真实模型、token 和成本不可得，记为 null。\n"""
    out_md = INITIAL / "REVIEW.md"
    with out_md.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(md)
    print(json.dumps({"created": [str(out_json), str(out_md)], "criterion_statuses": statuses, "author_receipts": len(author_receipts), "author_nonzero": result["author_task_nonzero_count"], "local_receipts_before_finalizer": len(local_receipts), "local_nonzero_before_finalizer": len(local_nonzero)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
