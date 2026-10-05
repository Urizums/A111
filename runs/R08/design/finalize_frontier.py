"""Update live entry points and linked ledgers without overwriting historical evidence."""
from pathlib import Path
import sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
from coordinate import read,write

def main():
    for name in ['CODEX_HANDOFF.md','START_HERE.md']:
        copy=ROOT/'runs/R08/design/entry-before'/name
        copy.parent.mkdir(parents=True,exist_ok=True)
        if not copy.exists():copy.write_bytes((ROOT/name).read_bytes())
    s=read('state/continuation.json');by_id={t['id']:t for t in s['tasks']}
    phase=read('state/phases/R09.json')
    for row in phase['tasks']:
        if row['id'] in by_id:
            t=by_id[row['id']]
            row.update(status=t['status'],evidence=[e['path'] for e in t['evidence']],blocker=t['blocker'],next_action=t['next_action'])
            if t['attempts']:row['evidence'].append(t['attempts'][-1]['start_evidence']['path'])
    write('state/phases/R09.json',phase)
    project=read('state/project-todo.json')
    project['updated_at']=datetime.now(timezone.utc).isoformat()
    project['codex_continuation_R08']=dict(report='runs/R08/REPORT.md',ledger='state/continuation.json',candidate='runs/R08/candidate/C7-lock.json',R08_02='done',R08_03='blocked_failed_complex_budget_overrun',R08_next='blocked_not_archived',R09_01='done_distinct_branch_with_actual_first_step',next_queue_task_id='R09-02',next_plan='runs/R09/PLAN.md',old_blockers_and_budgets='preserved',tokens=None,cost=None)
    write('state/project-todo.json',project)
    cp=read('state/checkpoint.json')
    cp['execution']=s['execution'];cp['execution'].update(session_state='checkpoint_after_scoped_r08_r09_work',checkpoint_reason='R08-03 is blocked after budget overrun. Distinct R09-01 completed with actual runtime evidence; R09-02 fresh checkout validation is next. No background execution claimed.',current_report='runs/R08/REPORT.md',next_plan='runs/R09/PLAN.md',coordinator_heartbeat=datetime.now(timezone.utc).isoformat(),current_native_pending=[],native_pending=[])
    cp.update(R08_budget_and_failures='runs/R08/validation/root-repair-ledger.json',R09_actual_first_step='runs/R09/preflight/formal-first-step.json',current_native_pending=[],next_queue_task_id='R09-02',next_action='Continue R09-02 fresh-checkout verification on the published commit; do not replay exhausted R08 complex case or archive R08 as passed.')
    s['execution']=cp['execution'];write('state/continuation.json',s);write('state/checkpoint.json',cp)
    (ROOT/'START_HERE.md').write_text('''# Codex 接续入口

继续 GitHub `Urizums/A111:main`，先读 CODEX_HANDOFF.md、AGENTS.md 和当前台账。
状态以 state/continuation.json 为准；state/checkpoint.json 是恢复点。

R08-02 已完成 C7 短入口，376 条继承回归通过。
R08-03 的简单新上下文样本通过；complex 样本因三次修正超过两次上限且无业务产物，
保留失败 blocked。R08-next 仍 blocked，R08 未归档为通过。
独立可做的 R09-01 宿主预检已实际运行并完成；下一可执行项 **R09-02**。
见 [本轮报告](runs/R08/REPORT.md)、[R09计划](runs/R09/PLAN.md) 与
[支线决定](runs/R09/PLAN_ADDENDUM.md)。不能换 worker 重跑耗尽的 complex 样本。

```sh
python3 scripts/host_preflight.py --root . --lock state/source-lock.json --lock runs/R08/candidate/C7-lock.json
python3 scripts/coordinator_lease.py probe --root .
python3 scripts/verify_handoff.py --json
python3 scripts/continuation.py --root . next
```

Windows 原生 continuation/安全 POSIX 文件打开/计时 API 未支持；本次实际用 Ubuntu WSL。
按当前 checkout 的路径运行，先核对未决调用、再持有真实租约。Git 新 clone 使用
`git -c core.autocrlf=false clone`，避免自动转换破坏冻结字节；不要更改历史锁接受漂移。
原始入口字节保存于 runs/R08/design/entry-before/。
定时器保持停用，旧八项阻塞、ZCode 延期、原失败和已耗预算均保留；
没有完整产品发布或性能/泛化通过结论。C7 仍是仓库候选，未安装到个人 skill。
''',encoding='utf-8',newline='\n')
    (ROOT/'CODEX_HANDOFF.md').write_text('''# Codex 当前研发交接

从 `Urizums/A111:main` 接续。用户授权持续研发、上传开发成果，不等待 ZCode。
先读 AGENTS.md、START_HERE.md、state/continuation.json、state/checkpoint.json。

2026-10-05 本次 desktop 工作保存 C7 短入口并冻结锁：
`runs/R08/candidate/C7-lock.json`。C6 保持原字节；入口 17498→7139 字节，
376 条继承回归通过。字节缩减不证明速度、性能或泛化改善。

R08-03 已从两个新 Luna/max 上下文实际执行冻结要求。
simple 对账内容和源数据检查通过；首业务文件约 195.194 秒（含工具往返与失败）。
complex 只有读取和 CLI 帮助记录，未写业务源码、未创建 reviewer、无业务后继首步。
其读域偏差及三次修正超过两次上限均保留：
`runs/R08/validation/complex-terminal.json`、`root-repair-ledger.json`。
这项保持 blocked，禁止转给新 worker、换样本或清零预算刷通过。
R08-next 保持 blocked；没有通过 continuation advance 归档 R08。

不同来源的 R09 环境诊断支线已实际启动并完成 R09-01，
不是重开 complex 样本。正式首步：`runs/R09/preflight/formal-first-step.json`。
只读 host_preflight.py 在 Windows 和 Ubuntu WSL 各通过 6 项相关检查，
原生 Windows 明确报告不兼容，WSL 核对冻结字节后可执行原控制器。
本次没有移植 Windows 控制器或证明恢复发布、provider、UI 或崩溃耐久。
支线依据见 runs/R09/PLAN_ADDENDUM.md；下一实际可执行项 **R09-02**，
从已发布提交的新 checkout 做独立验证，保留原验收与每 actor 两次预算。

原全部旧锁、历史失败和预算未改变；本轮原始 Git 基线为
`83f21cadfe895cbfd3d03075ba012359f670bb7a`，不是早期 PR#2 的旧基线。
审计核对 3811 个继承文件及29个原任务；9个原 blocked 包含旧八项与延期 ZCode。
PR#1 已关闭、原源提交保留；PR#2 已合并。完整产品门槛仍未通过。

当前无未决原生 worker，定时器未开启。原历史未决调用单独保留，不能复用旧 PID。
先运行 host_preflight、verify_handoff 和 continuation next，核对当前租约再持有；
当前 CLI 使用 Python3/Linux，Windows 本机用实际可用 WSL 并替换为当前 checkout 路径。
不存在 provider token/cost 数据时写 null。共享源码、TODO/checkpoint 由协调者串行整合。
报告与恢复动作见 runs/R08/REPORT.md；原交接字节在 runs/R08/design/entry-before/。
结束前提交原始证据、TODO/checkpoint，上传授权开发成果并释放租约。
''',encoding='utf-8',newline='\n')

if __name__=='__main__':main()
