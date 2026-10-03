# 下一轮：是否减少协议工作量

本轮首先交付可用草稿与预检查，并确认原始协议没有被绕开。Luna 整理的 measurement-materials.md 是来源材料；下面由 Root 定义下一轮对照方法。当前尚未执行对照，不能从不同输入的前后轮耗时推断提升。

使用同一已保存候选、相同业务输入和原验收要求，按 project 与已有 package 分块。每块先安排两对运行，共八个实际 worker；每对随机/交替 A、B 顺序。A 手工构造身份/哈希/验收框架，B 使用 reply/decision 草稿；两边都用同样的只读预检查、相同 native 流程和独立 source review。保持请求的 Luna/max/fresh 设置、工具授权、action/poll 限制及材料相同，每次使用新且互不重叠的输出目录、checkpoint 和 runtime IDs，记录路径与 ID 差异。不得改变成功标准或丢弃失败来形成对比。

| 观测项 | 采集方式 | 解释边界 |
| --- | --- | --- |
| 准备、回复构造、验收构造阶段 | 协调者记录同一 boot 的 monotonic 起止、actor、实际 CLI argv/退出码 | 是本地观察跨度，包含工具与协调等待，不能称模型活跃时长 |
| JSON/哈希错误和修正 | 保留第一份原件、失败输出、修正原件与重试；预先固定错误分类 | 独立分母包括失败；不能隐藏需要 Root 协助的样本 |
| 调用与步骤 | 单独统计实际 spawn/query/interrupt、review claims、draft/preflight CLI、通知等待 | 增加预检查可能减少错误但增加步骤；不能只挑一种计数 |
| worker与终态 | 原 native 返回、claim/导入时刻、实际完成观察、原始回复 | provider start/end 和内部模型身份仍未知，不把 ledger 时间当模型运行时间 |
| 源结果与提交 | Root 复算原始输入，核对 artifact/decision 哈希、原 checkpoint、冻结验收 | 完成与正确性必须相同；更少验证不算改进 |

先报告每对记录和范围，再给中位数、区间、失败/协助数；八个 worker 只构成小型描述性样本，不据此宣称稳定通用加速。Token/成本没有实际 telemetry 时保持 null。显著工具/容量阻塞保留并单独解释，不能随意剔除或补跑到得到喜欢的结果。

若结果显示主要时间消耗仍在手写 work/plan 和串联 CLI，下一项再评估最小 work/driver 启动辅助。继续让 bridge 构造请求和持有状态，不新增第二套 request serializer，不自动选择业务规则或授权。若新增草稿步骤没有实际收益，保留可选路径或简化入口；简单一次性任务继续直接完成。设计 preset 整理与实际图形验收保留原有任务与 browser blocker，不从本轮 CLI 成功关闭它们。
