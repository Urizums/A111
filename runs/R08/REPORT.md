# R08 Codex desktop 实施与真实执行结果

2026-10-05 从 GitHub main 的 `83f21cadfe895cbfd3d03075ba012359f670bb7a` 接续。
本批是授权开发成果，完整产品门槛仍未通过，活动阶段 R08 未归档。

| 项目 | 实际结果 | 证据 |
| --- | --- | --- |
| R08-02 / C7 | 完成并冻结；入口 17498→7139 字节，C6 全部实现字节保留 | candidate/C7-lock.json、design/change.json |
| C7 继承回归 | 376 项通过，Ubuntu WSL Python 3.12.3 | design/c7-regression.json |
| R08-03 simple | 全新 Luna/max，5 条接受、4 条拒绝，源数据复算通过 | validation/simple/result.json |
| simple 首业务文件 | 首捕获命令起约195.194秒，包含工具与失败；不是性能优劣结论 | validation/simple/first-command.json、reconciliation-write.json |
| R08-03 complex | 无业务源码/独立reviewer/业务后继首步；三次修正超过两次上限，失败blocked | validation/complex-terminal.json、R08-03-result.json |
| 租约/接续机制 | 1 项实际竞争租约检查及8项 continuation 回归通过 | design/lease-behavior.json、continuation-regression.json |
| R09-01 独立可做支线 | 实作只读预检，正式真实首步后绑定并完成；Windows/WSL 各6项检查通过 | ../R09/R09-01-result.json、preflight/formal-first-step.json |
| 历史保留 | 3811个继承文件字节未变；29个原任务的要求、预算、尝试保留；9个旧blocked含延期ZCode | design/preservation-audit.json |

complex 的实际失败为 WSL 缺 rg、JS 缺 btoa、JS 缺 TextEncoder、Windows
过长命令错误206。reader fallback 和两个 write fallback 共三次修正，发生了上限
违反，原样记录而不截成2。协调者停止该样本，不换worker、不改样本、不清预算。
执行者还读取了分配范围外的两个 C7 示例资产；因此不能声称完全盲测。
simple 的两次命令构造失败同样计为2/2，其业务结果通过不抹去失败。
原生创建及最终返回按实际工具回执转录；没有 provider 认证计时、token 或费用，均 null。
预注册样本/候选/要求与原始文件在 validation/frozen-lock.json 下保留。
首命令记录和原材料字节保留；完整原 host bridge / predispatch snapshot 协议未执行，
不把本轮观察声称为该协议的完整合规或效率试验。

原生 Windows 的 fcntl、POSIX 分量打开、Linux boot marker 不可用；本机可用 WSL。
Git 自动CRLF转换曾使冻结校验失败，原失败保留在 windows-preflight/；
随后从原 Git blob 恢复精确字节，不改历史锁。C7 没有移植 C6 Linux renameat2 恢复后端，
没有个人skill安装提升，也没有 UI、真实 provider、崩溃耐久或泛化通过结论。

R09环境诊断有不同原材料与目标，按支线决定继续，见 ../R09/PLAN_ADDENDUM.md。
R08-next 仍依赖原 R08-03 验收并保持 blocked；没有 continuation advance。
下一可执行队列项是 R09-02：从发布提交的新 checkout 独立核验预检与租约/接续边界。

一轮辅助安装回归与共享状态写入重叠，运行21项后出现3个失败标记，被协调者实际
终止（exit -15）；完整信封在 design/auxiliary-regression.json，不作为验收。
使用固定源码快照进行一次有界纠正，53项辅助回归在20.590秒内通过；结果保留在 design/auxiliary-stable.json。这不是独立验收或性能对比。
协调者原结果读取的GBK错误保留在 validation/root-repair-ledger.json；本次源码快照
纠正另作版本记录，不覆盖已绑定证据。旧各批预算不变。

代码、原始失败、TODO/checkpoint 将同步 main；定时器未启用。
会话结束前核对无未决当前原生worker、保留历史未决调用并释放协调者租约。

固定测试源码树通过一个单独Git提交保留，见 design/stable-source-commit.json；后续提交只整合最终证据与状态。
