"""Preserve old entry bytes and expose observed frontier; no skill adoption."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
backup = ROOT / "runs/R16/entry-before"
backup.mkdir(exist_ok=False)
for name in ["CODEX_HANDOFF.md", "START_HERE.md"]:
    (backup / name).write_bytes((ROOT / name).read_bytes())
handoff = """# Codex 当前研发交接

继续 Urizums/A111:main。用户授权持续研发及上传开发成果，不等待ZCode；成品是Forge纯文档meta-workflow。先读AGENTS.md、START_HERE.md、state/continuation.json和state/checkpoint.json。

当前候选C9在runs/R14/candidate/C9/forge-agent-flow/，八份Markdown，无产品脚本、测试或执行器。作者累计2/2，冻结正文不再修改。源锁runs/R14/candidate/C9-lock.json；实际解包字节验证过的包runs/R14/package/Forge-C9-meta-workflow.zip，未安装个人skill。包装通过不证明行为或完整产品通过。C8及原skills保留，前一入口字节在runs/R16/entry-before/。

R14-02八个新上下文完成微型建模试运行和原要求诊断。独立重算/查看图表初审39pass/1fail，第二轮预算与定位核查后38pass/2fail。初审未改写；第二轮有协调者反馈，不冒充盲审。L3原案例累计3/2超限；L7将预测取整后改变目标，原题最优性失败。两案例停止，不换人或换样本。各层预算依次1/0/3/0/1/2/2/0，限额各2，C9作者另为2/2。99份当前工件和原失败保留。见runs/R14/REPORT.md、math-comparison.json、trials/math/independent-review/。

R14-03真实浏览器路径被宿主明确拒绝且禁止绕过，f2–f5没有运行证据；前端案例0/2，R14-04两领域联合验收和R14-next保持blocked，R15未启动。静态数学诊断不替代浏览器验收；不能换协议、浏览器、CDP或间接执行达到被拒绝结果。

用户新增要求由子agent独立写上半年MathorCup真实题，不看既有论文/解法。只取得官方2026修订D题《多场景、多目标货物运输装箱策略优化》，未搜索九月国赛。R16-01取得PDF、DOCX、XLSX和勘误，原输入及p1–p6在求解前冻结，来源预算2/2。R16-02原actor /root/r16_original_solution 读取全部材料；初始SyntaxError后的替代构造和错误路径后的修正重跑累计2/2。solve.py未执行，没有求解结果、完整论文或独立模型审查；误读非授权manifest的披露保留，未使用是actor声明。R16-02/03/04/next保持blocked。见runs/R16/REPORT.md、TODO.md、budget-decision.json、solution/attempt-ledger.md。

已向用户提出仅增加R16-02原案例累计上限至6的明确问题；没有答复不能当授权。保留已用2、原actor、原题及原验收，不重置来源/C9/其他旧预算。若获授权，保存用户原话与预算覆盖记录，再只接续原actor。常规赛实践不证明十月大数据赛表现或奖项。

原38任务哈希保持一致，主阶段R08没有archive为通过。R08复杂样本3/2且无业务产物，R10-02原actor3/2，R11-02依赖阻塞，R13协议实际采用2/2后失败回滚；原失败、完整产品门槛、输入和预算保留。本轮不采用或补修R13，R12设计检查不等于R13采用成功。旧详情见runs/R10/REPORT.md、runs/R13/REPORT.md及保存的旧入口。

本轮actor已终态，历史未决桥接调用单独保留。共享台账Root串行整合；接续先probe实际租约，不信旧PID。研发控制器经Linux/WSL运行，Windows命令显式UTF8，这些工具不进入C9包。未知实际provider/model/token/cost为null。定时器停用，不承诺后台推进。结束保存checkpoint、上传已授权开发成果并释放实际租约；GitHub CI仅证明对应源码检查，不能覆盖行为失败。
"""
start = """# Codex 接续入口

成品方向为Forge meta-workflow，当前候选C9是八份纯文档：
[技能入口](runs/R14/candidate/C9/forge-agent-flow/SKILL.md)、
[可分发包](runs/R14/package/Forge-C9-meta-workflow.zip)、
[八层实际诊断](runs/R14/REPORT.md)、
[真实原题检查点](runs/R16/REPORT.md)。
包内无脚本、测试或执行器，尚未完整行为验收。

先读AGENTS.md、CODEX_HANDOFF.md、state/checkpoint.json和state/continuation.json。
R14独立诊断38项通过、2项失败：L3原案例3/2，L7改变目标；不修复或掩盖。
前端真实浏览器及两领域联合验收仍blocked，R15未启动。

R16取得上半年2026 MathorCup官方修订D题，子agent没有读取既有论文或解法。
求解actor完成材料读取，但两次恢复耗尽原案例2/2；未运行模型，未完成论文。
仅等待用户明确是否提高该原案例累计上限，保留已用2与原失败；不能自动视为授权。
原38任务、R08/R10/R11/R13失败与预算保留，主阶段仍R08，不等待ZCode。

恢复时实际执行scripts/host_preflight.py、scripts/coordinator_lease.py probe、
scripts/verify_handoff.py --json及scripts/continuation.py next。
它们是研发恢复工具，不是C9运行依赖；先核对真实租约和未决调用。
保持core.autocrlf=false，Windows显式UTF8，研发控制器实际经Linux/WSL运行。
旧入口字节在runs/R16/entry-before/；未安装个人skill，未投稿，定时器停用。
"""
(ROOT / "CODEX_HANDOFF.md").write_text(handoff, encoding="utf-8", newline="\n")
(ROOT / "START_HERE.md").write_text(start, encoding="utf-8", newline="\n")
files = []
for p in sorted((ROOT / "runs/R16/solution").rglob("*")):
    if p.is_file() and "__pycache__" not in p.parts:
        raw = p.read_bytes()
        files.append(dict(path=p.relative_to(ROOT).as_posix(), size_bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest()))
lock = dict(schema="forge-stopped-draft-lock/1", files=files,
    scope="Unexecuted original producer draft and source-reading records at case2/2",
    limits="Byte identity only; no model result, verified baseline, complete paper or acceptance.")
(ROOT / "runs/R16/stopped-solution-lock.json").write_text(
    json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
outputs = ROOT.parents[1] / "outputs"
outputs.mkdir(exist_ok=True)
for source, target in [("runs/R14/REPORT.md", "Forge-C9-validation-report.md"),
                       ("runs/R16/REPORT.md", "MathorCup-original-practice-checkpoint.md")]:
    (outputs / target).write_bytes((ROOT / source).read_bytes())
ledger_path = ROOT / "runs/R16/root-integration-ledger.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
ledger.update(used=2, second_failure="JS patch construction SyntaxError from unescaped Markdown backticks; no tool mutation occurred.",
    second_recovery="Construct entry helper without backtick-containing template fragments.",
    final_boundary="No further corrective integration round beyond2/2.")
ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(dict(entries_updated=2, prior_entries_retained=True, stopped_draft_files=len(files),
    complete_paper=False, reports_copied=2, root_integration_used=2)))
