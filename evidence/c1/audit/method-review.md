# C1 静态方法核对

核对对象是 `Study_Plan.md`、`coordinator/Study_Freeze.json`、两份 shared protocol、`shared/capture.py`，以及安装版 Forge 的 `host-bridge.md`、`host-drafts.md`、`task-entry.md`。未读取实际业务输出、运行记录、旧试验或 Root 的预期业务答案；这不是八个样本的终态审计。

## 冻结与方法读法

冻结清单的 83 个文件与当前安装版 Forge skill 根目录逐项 SHA-256 相符（83/83；无缺失或差异）。三份公开协议文件也与冻结清单中的哈希相符：`references/host-bridge.md` `f73242b7…fc78a8a`、`references/host-drafts.md` `1a64e569…7fcb09`、`references/task-entry.md` `eb63c548…cb41a8e`。这证明本次静态核对读到的是冻结文本；它不证明各运行样本实际调用或保存了这些材料。

C1 比较的是 A 手工编写 worker reply / coordinator decision scaffold 与 B 使用原始 `hostdraft` scaffold 的成套 authoring 辅助。原 bridge 生命周期、业务输入和验收保持相同；`hostdraft` 的 reply / decision 预检分别只证明外层 payload validity / controller compatibility，不证明 native worker 完成、package 内层响应推进或业务语义正确（`host-bridge.md:53–63, 93–104`; `host-drafts.md:77–86`）。实际完成与业务正确性仍需 coordinator 的原始状态观察、receive 和独立源审查。

这是有限、描述性的重复输入比较：project 与 package 各有两对 A/B，顺序 counterbalanced 而非随机；同一 operator 在四个样本间复用上下文，且两 block 可以并行。计划明确承认学习、缓存、负载和 block 干扰，禁止据此作稳定的全局速度或因果泛化结论（`Study_Plan.md:5, 26`）。阶段跨度含 actor、工具及等待间隙，按协议只能解释为端到端观察跨度，不是模型 active duration；tokens、cost 与 provider 内部身份未知（`Study_Plan.md:17, 22, 24`）。

public task-entry 条款支持把同一 package 用于新输入，同时将新输入核验与原冻结案例覆盖分开，并要求不把新输入成功冒充原 case 覆盖（`task-entry.md:65–70`）。它也要求给 fresh executor 原始材料、准确 package/skill 位置和资源范围，不给先前答案或诊断（`task-entry.md:102–114`）。这与 C1 的重复输入、禁止 worker 获得先前结果相符。

## 方法缺陷

### M1 — C06 的“每个 subprocess 完整留证”与 observer 例外不一致

- **冻结要求：** `Study_Plan.md:14` 的 C06 要求“every invoked subprocess”都保留 argv、raw bytes、exit 和 timestamps。
- **执行说明：** `Operator_Protocol.md:5` 指定 marker/native observer commands “create their own records”。`Worker_Protocol.md:13` 明确说 marker commands 不需要额外 `cli` wrapper。
- **实现：** `capture.py:31–38` 的 `mark` 只写 stage/event、UTC、单个 monotonic 值和 boot ID；`native` 写本地 intent/return payload 及 payload bytes/hash 和单个时间点。两者都不记录 observer subprocess 自身的 argv、stdout/stderr 原始 bytes、exit code 或开始/结束时间。只有 `capture.py:43–48` 的 `cli` 路径保存这些字段，但它保存的是被调用目标命令的数据。
- **实际矛盾：** 如果按 C06 字面把 marker/native observer 本身也算作“every invoked subprocess”，当前明确免包一层的流程无法提供该条要求的完整记录。若作者本意是仅指被 `cli` 包装的目标命令，则冻结文本没有定义这个排除范围。现有方法因此不能无歧义地证明 C06 的全称要求。
- **审计影响：** 后续应按已保存的原始字段如实标明 observer invocation 的证据范围；不得把 marker/native event record 描述成完整的 subprocess capture，也不得补造缺少的 argv/bytes/exit。该方法级缺口本身不判任何尚在写入的样本为失败；样本影响须在数据稳定后按冻结条款和实际文件单独判断。

## 分开的建议与歧义

- **未来方法说明建议，不改本次冻结：** 明确“captured subprocess”只指由 `capture.py cli` 启动的目标命令，并显式列出 observer harness 的排除项；或在未来版本用外层 observer 记录其调用信息。不得把这项建议追溯成新的 pass 标准或改变当前 C1 的冻结条款。
- **C04 actor 用语有歧义：** `Study_Plan.md:12` 把 worker reply preflight 与 “final completion observation” 写在同一句；但 `Worker_Protocol.md:20–22` 规定 worker 完成 preflight、结束 `worker_reply` 后返回，实际 host 状态查询位于 `Operator_Protocol.md:18–19` 的 coordinator 流程；公开 bridge 也把 accepted 与 completed snapshot 分开（`host-bridge.md:53–58`）。因此 final completion observation 应按实际 coordinator 状态查询记录，不应凭这句话推定 worker 能观察自己的 native completion。这个澄清不要求补造 worker 侧状态或改动冻结验收。

## 运行审计边界

Root 已通知：当前 boot ID 与冻结时不同，且原运行分支曾短暂丢失；这条通知不是我对 raw run records 的独立验证。最终核对只在相同 boot ID 的 monotonic markers 间计算跨度；跨 boot、缺失或乱序 marker 对应区间标为 unverified，不拼接、不补造。写入中目录和缺少 receipt 仅表示现有证据尚未稳定，不能仅凭 absence 推断 native 调用没有发生或已经终态失败。待 Root 通知两 block 稳定后再按选样顺序、source hashes、真实 receipts、原件、markers 和 capture indexes 完成审计。
