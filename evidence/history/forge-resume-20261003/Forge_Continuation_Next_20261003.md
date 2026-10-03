# 下一层研发计划

本轮先完成资源核对、可观察执行和有界续跑。Root 负责需求、接口、泛化、核心实现和修补；Luna 做材料整理、普通任务实测和独立验证。当前两轮功能修补额度已经使用，后续功能单独立项和冻结验收，不混入本轮候选。

下一项优先减少手工编写 host reply/decision 的工作。真实任务暴露了两种成本：证据 SHA 填写错误使验收提交受阻；worker 回复混入外层协议不支持的字段，需要明确记录的规范化协助。这些是实际观察，不据此宣称通用失败率或速度提升。

现有 `forge_template.py response` 生成内层 Flow response，`results` 生成 package-v2 待运行评估框架；host request 已由 bridge prepare 生成并冻结。Root 不再增加第二套 request serializer。Luna 的只读材料在 protocol-materials/protocol-draft-capability.md，供设计决策核对，未作为最终技能实现。

| 工作 | Root 设计与实现 | Luna 验证 | 完成标准 |
| --- | --- | --- | --- |
| Host reply 草稿 | 从原 request 复制 wrapper ID/哈希，区分 package 内层与 host 外层；只能为已经存在且在范围内的实际 artifact 计算 SHA | 新线程使用原始本地任务，保留草稿、实际工作与最后回复 | 未填写业务结果的草稿不能被当作成功提交；原始 request/输入不变 |
| Host decision 草稿 | 从当前已收到的 reply 和原 checkpoint 生成 acceptance ID/plan hash，实际 evidence 路径计算哈希；outcome/验收结论保持未定 | 独立核验正确、错误、缺失、漂移和旧 invocation | 草稿不自动设置通过，不产生 worker lifecycle 回执，不覆盖旧决定 |
| 协议预检查 | 复用 bridge/controller 的原始 validator；清楚区分字段错误、语义验收失败、证据不可读与提交不确定性 | Fresh ordinary executor 与独立负例 CLI 探针 | 错误能定位到原条款；不得重算旧锁以掩盖漂移或降低验收 |
| 开销评估 | 先冻结相同任务和材料的对照计划，分别记录准备/worker/验收/恢复阶段、CLI 与实际 native 调用 | Luna 执行可比任务，Root 复算原始记录 | 同材料、相同边界和可说明条件；无 token/成本数据保持 null；一次更少调用不等于已证明性能提升 |

简单一次性任务继续直接完成和相关检查，通常一个上下文足够。只有当前任务本身要求可复用 flow、原始 checkpoint、委派或独立证据，才引入对应协议；不得为了评估框架把普通任务扩成完整工厂。

并行但不阻塞上述开发的轨道：保留原先的设计 preset catalog 任务，先整理可版本化参考/组件元数据；图形交互、加载与动效验收依旧需要能触达目标应用的实际浏览器。原有浏览器 blocker 不因 CLI 成功而关闭。Provider-wide 限额、使用量和外部业务效果幂等性作为各自 adapter 的独立范围，不从本地 registry 或 native interrupt 推导。

连续性优先保留真实回执与检查点的阶段性证据。存档说明原路径与原哈希、真实 worker 身份和未知效果，不能把归档副本改路径重新哈希后当成原始运行。环境缺失时先核对可观察的宿主状态和原证据，只有明确可恢复的本地状态才续跑；失去证据不能自动触发真实业务重试。
