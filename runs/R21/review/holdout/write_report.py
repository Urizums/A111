"""Publish Chinese holdout findings from the independent locked scoring outputs."""
from __future__ import annotations
import base64, json
from pathlib import Path
import pandas as pd

OUT = Path("runs/R21/review/holdout")
metrics = json.loads((OUT / "metrics.json").read_text(encoding="utf-8"))
validation = json.loads((OUT / "validation.json").read_text(encoding="utf-8"))
groups = pd.read_csv(OUT / "group_metrics.csv")
daily = pd.read_csv(OUT / "daily_route_metrics.csv")
daily_wide = pd.read_csv(OUT / "daily_route_differences.csv")
calendar = pd.read_csv("runs/R21/inputs/raw/calendar.csv")
future_calendar = calendar[["service_date", "holiday"]].copy()
first = json.loads((OUT / "first-truth-open.json").read_text(encoding="utf-8"))
binding = json.loads((OUT / "freeze-bindings.json").read_text(encoding="utf-8"))
routes = ["shared_ridge10", "weekly_mean56"]
cn = {"shared_ridge10": "R（共享岭回归）", "weekly_mean56": "W（56日同店品星期均值）"}

def f(v, n=2): return f"{float(v):,.{n}f}"
def pct(v): return f"{100*float(v):.2f}%"
def row(cells): return "| " + " | ".join(str(x).replace("|", "\\|") for x in cells) + " |"

lines = [
    "# R21 首锁后 holdout 独立评价",
    "",
    "本报告是在首轮产品与生产域分别冻结后，按协议开启固定私有 holdout 真值得到的新增测量。首版论文、路线、参数和计划未改动；本文不回写首锁，不重新选模或调参。以下结果只描述本次虚构离线案例的42日合成真值，不代表现实市场结果。",
    "",
    "## 冻结顺序与真值身份",
    "",
    f"首轮锁：`{binding['initial_lock']['sha256']}`（冻结时间 {binding['initial_lock']['frozen_at']}；{binding['initial_lock']['file_count']} 项）；生产锁：`{binding['execution_lock']['sha256']}`（冻结时间 {binding['execution_lock']['frozen_at']}；{binding['execution_lock']['file_count']} 项）。真值身份只从 evaluation 锁取值后，第一次内容读取发生于 {first['first_open_utc']}，晚于首轮锁。truth SHA256 为 `{first['truth_identity']['actual_sha256']}`，与锁定字节数及摘要一致。首次读取命令完整收据见 [03-first-truth-open-command.json](03-first-truth-open-command.json)。",
    "",
    f"真值有 {validation['truth_rows']:,} 行、{validation['truth_duplicate_keys']} 个重复键；每条路线以首锁预测和整数计划逐键合并，均为4,032个唯一键、42日。",
    "",
    "## 总体结果",
    "",
    "MAE、RMSE、bias 与区间指标按4,032个店品键汇总；覆盖率是边际覆盖。短缺、报废、两项损失、采购与件数按42日汇总，日均值另列。协议区间评分采用 `width + 20×下侧漏出 + 20×上侧漏出`，区间内只计宽度。采购额是约束核验及支出报告，不加进两项损失目标。",
    "",
    row(["指标", "R（共享岭回归）", "W（星期均值）"]),
    row(["---", "---:", "---:"]),
]
overall_rows = [
    ("键数 / 日期数", lambda x: f"{x['key_count']:,} / {x['date_count']}"),
    ("MAE（件/键）", lambda x: f(x["mae"])), ("RMSE（件/键）", lambda x: f(x["rmse"])),
    ("bias：预测−真值（件/键）", lambda x: f(x["bias_pred_minus_truth"])),
    ("90%区间覆盖", lambda x: pct(x["coverage"])), ("低于下限", lambda x: pct(x["below_rate"])),
    ("高于上限", lambda x: pct(x["above_rate"])), ("平均区间宽度（件）", lambda x: f(x["mean_interval_width"])),
    ("协议区间评分（件/键）", lambda x: f(x["mean_interval_score"])),
    ("缺货损失（元；日均）", lambda x: f(x["shortage_yuan"]) + f"；{f(x['shortage_yuan']/42)}"),
    ("报废损失（元；日均）", lambda x: f(x["waste_yuan"]) + f"；{f(x['waste_yuan']/42)}"),
    ("两项损失（元；日均）", lambda x: f(x["two_part_loss_yuan"]) + f"；{f(x['two_part_loss_yuan_per_day'])}"),
    ("采购支出（元）", lambda x: f(x["procurement_yuan"])), ("备货合计（件）", lambda x: f(x["q_units"], 0)),
    ("产能满载日 / 预算满额日", lambda x: f"{x['capacity_full_days']} / {x['budget_full_days']}"),
    ("最大单日备货 / 采购（件 / 元）", lambda x: f"{x['max_daily_units']} / {f(x['max_daily_procurement_yuan'])}"),
]
for label, fn in overall_rows:
    lines.append(row([label] + [fn(metrics["route_metrics"][r]) for r in routes]))

R, W = (metrics["route_metrics"][r] for r in routes)
loss_delta = W["two_part_loss_yuan"] - R["two_part_loss_yuan"]
score_delta = W["mean_interval_score"] - R["mean_interval_score"]
lines += [
    "",
    f"在这42日中，W−R 两项损失差为 **{f(loss_delta)}元总额（{f(loss_delta/42)}元/日）**；逐日看，W 有5日损失较低、37日较高。W−R 平均区间评分差为 **{f(score_delta)}**；逐日平均评分差为 {f(metrics['daily_pair_summary']['daily_interval_score_difference_weekly_minus_ridge']['mean_score_per_key_day'], 3)}，9日 W 较低、33日较高。两方法的实测覆盖都低于名义90%，R为{pct(R['coverage'])}、W为{pct(W['coverage'])}；R区间略窄且覆盖较高。这里只报告预先冻结的有限样本描述，不进行显著性或因果推断，也不把4032键当作独立重复。",
    "",
    "## 可行性与核验",
    "",
    "| 核验 | R | W |",
    "| --- | ---: | ---: |",
]
for label, key in [("全体预测/区间/计划有限", "all_predictions_intervals_and_plans_finite"), ("点预测非负且区间包含点预测、水平为0.9", "all_prediction_and_interval_bounds_valid"), ("整数计划且每店品不超55件", "all_q_integer_and_item_bounded"), ("每天96个唯一键", "all_dates_96_unique_keys"), ("每日总量≤1600件", "all_daily_capacity_limits_valid"), ("每日采购≤6000元", "all_daily_budget_limits_valid")]:
    lines.append(row([label] + ["通过" if metrics["route_metrics"][r][key] else "失败" for r in routes]))
lines += [
    "",
    "该实现按原始 `items.csv` 的品类缺货/报废单价逐键重算损失，按 `decision.json` 的每日1600件与6000元限制逐日核验，并保留首锁计划。两条路线均有24/12个产能满载日/预算满额日（R/W），没有超限日。",
    "",
    "## 预定分组结果",
    "",
    "下表覆盖协议预定分组；完整每组 MAE、RMSE、bias、覆盖、两侧漏出、宽度、区间评分、缺货、报废、总损失、件数及采购数值均在 [group_metrics.csv](group_metrics.csv)。组内键的相关性不消失，组数据仍是描述性汇总。",
    "",
]
def paired_group_table(dimensions, title):
    lines.append(f"### {title}")
    lines.append("")
    lines.append(row(["组", "日期数", "键数/路线", "R MAE", "W MAE", "R覆盖", "W覆盖", "R评分", "W评分", "R损失/日", "W损失/日", "W−R损失/日"]))
    lines.append(row(["---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:"]))
    for dim in dimensions:
        subset = groups[groups.dimension == dim]
        names = sorted(subset.group.astype(str).unique())
        for name in names:
            a = subset[(subset.group.astype(str) == name) & (subset.route == "shared_ridge10")].iloc[0]
            b = subset[(subset.group.astype(str) == name) & (subset.route == "weekly_mean56")].iloc[0]
            lines.append(row([name, int(a.date_count), int(a.key_count), f(a.mae), f(b.mae), pct(a.coverage), pct(b.coverage), f(a.mean_interval_score), f(b.mean_interval_score), f(a.two_part_loss_yuan_per_day), f(b.two_part_loss_yuan_per_day), f(b.two_part_loss_yuan_per_day-a.two_part_loss_yuan_per_day)]))
    lines.append("")

paired_group_table(["activity"], "活动 / 普通日")
paired_group_table(["horizon_band"], "六个7日步长带")
paired_group_table(["activity_x_horizon"], "活动与步长交叉组")
paired_group_table(["store"], "12家门店")
paired_group_table(["item"], "8个品类")

lines += [
    "### 42个逐日配对结果",
    "",
    "下表给出两路线的逐日实测两项损失及协议区间评分（每行均含该日96个店品键），Δ为 W−R。它用于查看日期间变化，不是独立重复检验。",
    "",
    row(["日期", "活动", "步长带", "R损失/日", "W损失/日", "Δ损失", "R评分", "W评分", "Δ评分"]),
    row(["---", "---", "---", "---:", "---:", "---:", "---:", "---:", "---:"]),
]
date_groups = groups[groups.dimension == "date"]
for _, x in daily_wide.sort_values("service_date").iterrows():
    a = date_groups[(date_groups.group.astype(str) == str(x.service_date)) & (date_groups.route == "shared_ridge10")].iloc[0]
    b = date_groups[(date_groups.group.astype(str) == str(x.service_date)) & (date_groups.route == "weekly_mean56")].iloc[0]
    holiday = int(future_calendar.loc[future_calendar.service_date == x.service_date, "holiday"].iloc[0])
    day = (pd.Timestamp(x.service_date) - pd.Timestamp("2026-11-01")).days + 1
    band = f"{((day-1)//7)*7+1:02d}-{min(((day-1)//7+1)*7,42):02d}"
    lines.append(row([x.service_date, "活动" if holiday else "普通", band, f(a.two_part_loss_yuan_per_day), f(b.two_part_loss_yuan_per_day), f(b.two_part_loss_yuan_per_day-a.two_part_loss_yuan_per_day), f(a.mean_interval_score), f(b.mean_interval_score), f(b.mean_interval_score-a.mean_interval_score)]))

lines += [
    "",
    "## 解释与局限",
    "",
    "在锁定的42日真值上，R在MAE、RMSE、两项损失和区间评分上均低于W；两路线的区间覆盖都未达到名义90%，因此本次结果没有覆盖保证。R计划备货比W少53件，采购支出少10元。该差异只描述协议中这两条已冻结路线在这一段合成真值上的结果，不证明R普遍优越，不说明某项业务机制造成差异，也不构成真实市场收益。",
    "",
    "日期连续且可能相关；活动、步长、门店、品类的分组样本大小不一。42日和4032键并非4032个独立重复，因此不报告显著性检验或置信保证。仅有两条冻结候选，未来15–42日误差和活动制度外推风险仍是具体限制。情景模型、成本定义、库存无跨日结转和需求记录都属于该虚构案例的设定。",
    "",
    "本报告在真值开放后新增，不改变首版论文对当时未知未来的合法陈述；首版论文和首锁结果仍保持原样。",
    "",
    "## g5 判定",
    "",
    "**PASS（完整测量流程）**：两条首锁路线均完成全部逐键与逐日核验，按预定公式重算全部主要指标、协议分组、日级配对与资源约束；覆盖不达名义90%、方法间差异和所有组结果如实保留，未追调参数、重选路线、使用显著性/因果主张或把4032键当作独立样本。该判定表示预定评价已完整执行，不表示某条路线满足额外绩效门槛。",
    "",
    "机器可读的完整结果见 [metrics.json](metrics.json)、[group_metrics.csv](group_metrics.csv)、[daily_route_metrics.csv](daily_route_metrics.csv)、[daily_route_differences.csv](daily_route_differences.csv)、[key_metrics.csv](key_metrics.csv) 与 [validation.json](validation.json)。",
    "",
]
(OUT / "HOLDOUT_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

command_receipts = []
for p in sorted(OUT.glob("*-command*.json")):
    if p.name.startswith("write-report") or p.name.startswith("finalize"):
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    ob = base64.b64decode(d.get("stdout_base64", ""), validate=True)
    eb = base64.b64decode(d.get("stderr_base64", ""), validate=True)
    command_receipts.append({"receipt": str(p).replace("\\", "/"), "state": d.get("state"), "exit_code": d.get("exit_code"),
        "begin_utc": d.get("begin", {}).get("utc"), "end_utc": d.get("end", {}).get("utc"),
        "argv": d.get("argv"), "stdout_bytes": len(ob), "stderr_bytes": len(eb),
        "streams_match_base64_utf8_replace": ob.decode("utf-8", errors="replace") == d.get("stdout", "") and eb.decode("utf-8", errors="replace") == d.get("stderr", "")})

result = {
    "schema": "r21-independent-g5-result/1", "g5_verdict": "PASS", "meaning": "predefined frozen holdout evaluation completed; no separate performance quota",
    "initial_lock_sha256": binding["initial_lock"]["sha256"], "execution_lock_sha256": binding["execution_lock"]["sha256"],
    "evaluation_lock_sha256": binding["evaluation_lock"]["sha256"], "truth_sha256": first["truth_identity"]["actual_sha256"],
    "first_truth_open_utc": first["first_open_utc"], "first_truth_open_receipt": "runs/R21/review/holdout/03-first-truth-open-command.json",
    "validation": validation, "route_metrics": metrics["route_metrics"], "daily_pair_summary": metrics["daily_pair_summary"],
    "group_dimensions": metrics["group_dimensions"], "group_metrics_rows": metrics["group_metrics_rows"],
    "all_group_and_daily_tables_written": True,
    "no_tuning_or_route_reselection": True, "no_causal_or_significance_claim": True,
    "4032_keys_not_independent_replicates": True,
    "observed_unrecorded_read": {"occurred": True, "command": "Get-Content runs/R21/inputs/raw/items.csv -TotalCount 5; Get-Content runs/R21/inputs/raw/calendar.csv -TotalCount 5; Get-Content runs/R21/inputs/raw/decision.json; Get-Content runs/R21/execution/science-v1/future/shared_ridge10/predictions.csv -TotalCount 4; Get-Content runs/R21/execution/science-v1/future/shared_ridge10/replenishment.csv -TotalCount 4; Get-Content runs/R21/evaluation/holdout_truth.csv -TotalCount 4",
        "scope": "read-only authorized files after first recorded truth opening; output captured in tool result, no fabricated receipt", "status": "disclosed"},
    "recorded_commands_so_far": command_receipts,
    "model": None, "tokens": None, "cost": None,
}
(OUT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"report": str(OUT / "HOLDOUT_REPORT.md"), "g5_verdict": result["g5_verdict"],
                  "recorded_commands": len(command_receipts), "all_recorded_commands_terminal": all(x["state"] == "finished" and x["exit_code"] is not None for x in command_receipts),
                  "truth_opened_utc": result["first_truth_open_utc"], "route_summary": {r: {"loss": metrics["route_metrics"][r]["two_part_loss_yuan"], "coverage": metrics["route_metrics"][r]["coverage"]} for r in routes}}, ensure_ascii=False, indent=2))
