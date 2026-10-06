"""Current publication documents; no change to the exhausted evaluation or skill."""
from pathlib import Path
import hashlib

root=Path(__file__).resolve().parents[3]
for name in ['START_HERE.md','CODEX_HANDOFF.md']:
    assert (root/name).read_bytes()==(root/'runs/R10/resumption/entry-before'/name).read_bytes()

start='''# Codex 接续入口

当前用户定位为 Forge meta-workflow。C8 是纯方法开发候选：
[技能入口](runs/R10/candidate/C8/forge-agent-flow/SKILL.md)、
[五文件独立包](runs/R11/package/Forge-C8-meta-workflow.zip)、
[研发报告](runs/R10/REPORT.md)。包内不含脚本、测试或执行器。

先读 AGENTS.md、CODEX_HANDOFF.md 和 state/checkpoint.json；state/continuation.json 保存完整任务历史。
R10-01 源码/结构通过；R09-02 新checkout独立核验完成；R11-01 实际独立包装与解包完成。
R10-02 同一actor接续后累计3次纠正超过2次预算，三份业务草稿未完成原材料检查，保持blocked。
R10-next、依赖已验收批次的R11-02/R11-next保持blocked，不换样本或worker刷通过。
R08-03/R08-next、旧产品门槛、失败和预算仍保留；R08没有归档为通过。

```sh
python3 scripts/host_preflight.py --root . --lock state/source-lock.json --lock runs/R10/candidate/C8-lock.json
python3 scripts/coordinator_lease.py probe --root .
python3 scripts/verify_handoff.py --json
python3 scripts/continuation.py --root . next
```

以上是研发恢复工具，不是C8运行依赖。原生Windows控制器仍不兼容，实际用Linux/WSL。
新clone保留core.autocrlf=false，避免冻结字节改变；先核对真实租约与未决调用再写共享台账，不复用旧PID。
旧入口字节在 runs/R10/resumption/entry-before/，更早备份也保留。定时器停用，未知token/cost为null。
C8未安装个人skill，没有独立行为或完整产品通过结论。
'''
handoff='''# Codex 当前研发交接

继续 Urizums/A111:main，用户授权持续研发及上传开发成果，不等待ZCode。
用户澄清成品为forge-skill/meta-workflow；原话与边界在 runs/R10/scope-decision.json。
先读 AGENTS.md、START_HERE.md、state/continuation.json、state/checkpoint.json。

C8在 runs/R10/candidate/C8/forge-agent-flow/，锁为 runs/R10/candidate/C8-lock.json。
仅SKILL.md加四份参考，无脚本/测试/运行控制器依赖，不替换旧锁定skills/。
R10-01作者源码/结构完成；R11-01实际独立打包、解包、字节/引用/frontmatter检查通过。
可分发包为 runs/R11/package/Forge-C8-meta-workflow.zip；未安装个人skill。
包装通过不证明独立行为、性能/泛化或完整产品验收。

R09-02已从发布提交11e5ce90864e73a3f600df066cfbb469c6428a18的新clone独立验证。
22条真实完成命令：Windows缺fcntl等API，WSL队列核对与单checkout锁取得/竞争/释放有证据。
见 runs/R09/independent/report.json 与 runs/R09/R09-02-result.json。
创建请求gpt-6-luna/max，报告自称GPT-6；认证准确模型未知，不能将自称视为遥测。
R09支线末项已绑定R11真实首步；没有越过R08主阶段。

R10-02首次因额度中断，2026-10-06权限恢复后followup接续同一actor、同一原材料。
原命令缺state，原件保留，另存SHA绑定终态转录；没有替代worker或新样本。
actor确认3次纠正/尝试超过限额2：脱敏、终态转录、失败的JS纠正命令构造。
三份流程/模板/批次草稿存在，F3有已承认措辞缺陷，没有原材料检查或worker结果。
虽草稿自标finished，协调者按原要求记失败blocked；预算真实数3不截断为2。
验证协调修正2/2，C8源码修正0；证据见 runs/R10/resumption/native-terminal.json 与 R10-02-result.json。
R10-next blocked；R11-02缺少原定已验收的实际批次/checkpoint，零尝试blocked；R11-next blocked。
禁止改验收、转交新worker或改名样本规避此边界。

R08-03原复杂CLI样本继续blocked（3/2且缺业务产物），R08-next仍blocked，未advance归档。
C7及旧源码、案例、失败、预算和延期ZCode都保留；原完整产品门槛不因新范围/上传通过。
本轮保留基线11e5ce9，更早83f21ca、PR#1原源与PR#2合并历史不重写。
本轮报告 runs/R10/REPORT.md；旧交接字节 runs/R10/resumption/entry-before/。

先运行宿主/字节预检、verify_handoff与continuation next，核对真实租约和历史未决调用再持有。
原控制器用Python3/Linux；Windows经实际WSL运行，C8本身不依赖它。不要复用旧PID。
新增两位验证者终态已收；历史未决调用单独保留。共享源码与台账由Root串行整合。
未知provider/token/cost为null，定时器停用；不能凭提示词承诺后台自动执行。
发布仅是可审阅开发候选和证据。结束前保存checkpoint、上传授权开发成果并释放实际租约。
'''
report='''# C8 meta-workflow 研发记录

用户明确forge-skill/meta-workflow定位后授权继续研发。scope-decision.json保存原话和范围。
C7、旧源码、案例、失败与已用预算保留，没有用新候选改判原失败。

## 成品边界与实际结果

C8只有SKILL.md和四份必要参考：流程设计、协作、判定、接续；五份文档合计15887字节。
没有脚本、测试或控制器依赖，没有强制另一skill/模型。字节数不证明效率或泛化。
源码和锁在candidate/C8/与candidate/C8-lock.json；旧平台和研发测试保留在仓库，不随C8分发。
R10-01作者源码/结构检查完成；R09-02独立新clone的22条真实命令完成，确认Windows与WSL的工具边界。
报告自称GPT-6，创建请求gpt-6-luna/max；认证准确模型不可得，保持未知。
R11-01实际创建独立zip并在新目录解包；五文件字节、引用、独立frontmatter检查通过。
包为 ../R11/package/Forge-C8-meta-workflow.zip，SHA256为2a1cee218731fb1919092adf159ee39befbdf78ab567640532cbe56ba77cd492。
R09支线转换绑定R11真实首步；包装和检查不能替代业务行为验收。

## 独立行为样本失败，保留原记录

R10-02使用新冻结反馈分流请求，未重开R08 approval-CLI。
原actor额度中断后恢复同一上下文、原输入与输出域。未换worker、样本或验收，未重置预算。
原首命令缺state字段，原件保留，新增SHA绑定终态转录。
actor确认3次纠正/尝试：记录脱敏、终态转录、失败的JS纠正命令构造，超过2次上限。
没有子进程开始或业务文件改变，不免除失败的编排修正。探索性错路径观察也保留；完整错误未落盘，不伪造。
三份流程/模板/批次草稿存在，F3有已承认措辞错误；无原材料核验、worker验收或result.json。
草稿虽自标State: finished，最终worker承认未完成。协调者按原要求记失败blocked。
见R10-02-result.json、resumption/native-terminal.json与resumption/artifact-review.md。
验证协调预算2/2，actor3/2，C8源码修正0。草稿不随技能分发，也不作为通过样本。
R10-next blocked；依赖已验收批次/checkpoint的R11-02零尝试blocked，R11-next blocked。
R08-03/R08-next和原完整产品门槛不改判；不会转交新worker、改名或修正草稿后重刷原验收。

## 恢复与发布范围

本轮上传纯方法开发候选、原证据、TODO和checkpoint，未安装个人skill。
没有独立行为、性能/泛化或完整产品通过结论；上传和CI通过均不表示这些结论。
费用/token不可得处为null，定时器停用，长期目标active。无可绕过已耗预算继续的原案例。
新会话先核对源码/队列/未决调用和真实租约；不复用旧PID，不制造新案例掩盖失败。
本轮交接发布补丁因多次操作同一路径而拒绝，原文件未变；该传输失败另记publication/transport-failure.json。
其后仅整理发布文档，没有重跑C8样本或修改源码；原验证预算保持不变。
'''
for name,content in [('START_HERE.md',start),('CODEX_HANDOFF.md',handoff)]:
    (root/name).write_text(content,encoding='utf-8',newline='\n')
target=root/'runs/R10/REPORT.md'
with target.open('x',encoding='utf-8',newline='\n') as stream:stream.write(report)
print('Current handoff and report written; original entry bytes and validation budgets retained.')
