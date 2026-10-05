# 项目状态与保留的历史

当前长期目标 active，D00/R00 只表示历史交付里程碑。实时状态以 `state/continuation.json` 和 checkpoint 为准。R05/R06 当前代码、原始失败、效果与发布阻塞见 `runs/R06/VERIFICATION_REPORT.md`、`runs/R06/issues.json`。当前 C5 新增字节快照与有界修正记录器，原版本逐字节保留。完整验收之前本轮改动不提交或推送 dev。

原预设窄屏焦点和目录确认交互均保留了实际失败及修复版本；独立验收、作者复测、超额修正及旧 R03 工单 UI 失败分别记录，不相互代替。每小时调度已发生一次活动 Root 内的真实触发；独立冷启动交接和 provider 全局遥测仍未验证。下面的 C1/S/D00 描述保留原验收范围。

项目目标不是单个工单页面，而是一套能把目标转成可执行任务、交付软件或可复用 agent flow、验证并继续迭代的方法与本地控制器。工单审批、导入系统和资料抽取是验证材料。前端体验与运维稳定性是交叉的设计约束，不归并成一个“架构完成”标签。

| 层 | 已有内容 | 验证边界与未完成项 |
| --- | --- | --- |
| 任务入口 | 简单任务、软件系统、agent infra、flow、既有 package 的分流 | 小任务不强制 factory；方法完整性不能替代产品运行 |
| 应用/系统架构 | 领域、数据、权限、部署、故障恢复、性能与可观测性设计方法 | 具体系统必须落实案例；完整 production infra 未宣称完成 |
| 前端架构与体验 | 独立 product-experience skill；布局、密度、色彩、组件状态、动效与交互路线 | 历史两个 UI 阻塞保留为历史；当前浏览器已可用，工单和原预设目标分开验收 |
| 本地执行 | project/package 状态、材料绑定、case grading、审阅、host bridge/driver | 不包含独立 provider SDK；本地限制不等于 provider 全局保证 |
| 恢复 | 保留原 ID、receipt、失败及有界 resume/review；本地容量/截止案例 | 自然网络延迟、外部业务效果对账仍需专门验证 |
| 最近基线 T1 | reply/decision 未完成草稿、原验收 preflight；历史 368 回归、两个真实 worker | 辅助情况与 worker pre-completion 采集缺口保留；未证明提速 |
| 最近实验 C1 | 八个真实 Luna；七个原审批闭环；一个 running 截止 | 采集合同、观察顺序、写域、先前结果暴露、修正额度等问题使效能对比无效 |
| 历史局部采集 Q1 | 四个本地目标，五项独立案例通过 | synthetic native observer 不是实际 native 调用，保持其原证据范围 |
| 新候选 C2 / S03 | 完整版本化技能候选、失败命令记录修复、一个新原生烟测及一次有界复测 | 首轮业务正确但协调端采集失败；复测观察范围内通过；不是全工具轨迹或安全隔离证明 |
| 云端交付 D00 | 标准库 CLI 安装、迁移打包、Python 3.10/3.12 回归与 17 项冒烟 | 托管环境内的 CLI，无公网 Web 服务、永久后台调度或生产 SLA |

C1 样本不是八类未知业务，而是重复费用 CSV / 同一会议记录。Root 已核对八组来源字段，其中 A2 只有截止产出，不能视为完成工作。模型活跃时间、token、成本、内部 provider 身份均未知；阶段跨度包括工具与等待。

## 中断及状态合并

原持久 TODO v9 的最近已完成工作为 T1；本地 C1 draft 已推进到 partial，但最后一次沙盒断连发生在最终审计、归档和 TODO 保存之前。本仓库保存 v9 原件并合入 C1 观察，明确不把 planned 历史状态当最新事实，也不把本地 draft 当独立最终审计。

原 C1 报告最后提到的 audit/final-review.md、Root_Verification.json 尚未生成。它们不是有效现存证据。本仓库保留原报告文字，以这里及 state/checkpoint.json 说明其缺口。

S01 的 A01–A05 离线审计已完成，报告位于 `runs/S01/cloud-audit/worker/`，Root 整合位于 `runs/S01/final-review.md`。四份 package 原链闭合，四份 action 与四份 CSV 输出符合源数据；Project/A2 仍只有 cutoff 产物，不是完成的工作。B2 协调端三次分析修正已超过两次预算，桥接拒绝另行保留。八个样本的 marker/boot/wait 缺失逐项记录；旧性能比较继续为 inconclusive。

独立审计从原材料冻结预期后才查看产物，但随后检查的原 source-review 和部分 CLI stdout 含旧判断，因此不声称全盲。C10 的历史台账超出其只读输入范围，由 Root 对照原台账保留。没有重跑旧业务 worker，也没有给旧样本补造完成记录。

## 不应误判的完成项

既有 v9 的 39 done 保留为历史范围结果；两个 planned、三个 partial、一个 blocked 的原未完成项不被导出动作关闭。C1 comparison 保持 partial/inconclusive。新增采集/范围合同仅在 C2 本地资格检查及实际 S03 观察范围内完成，宿主强制工具/文件隔离仍未验证。原 R2 原始资源目录曾丢失，仅有历史摘要，不能在新宿主上声称重获原件。

原控制器在 Python 3.10/3.12 各通过 368 项回归，辅助检查各 16 项；候选另通过 368 项，安装/异地解压后 CLI 冒烟各 17 项通过。首次失败、修复预算与复测日志见 `runs/cloud/VERIFICATION_REPORT.md` 和 `runs/cloud/issues.json`。S01 审计与部署/S02/S03 的准备有时间重叠，归档计划明确保留实际时间，没有回填阶段开始时间。

历史 UI 阻塞与 provider / resources / network / effects partial 工作保留历史状态，当前可用性由 R04 重新探测；不得用历史阻塞代替现场检查。catalog 可先做来源、schema、token 和状态规范；真实渲染验收保留单独任务。
