# R24 — 原生 Flow 接收端上下文投影审计与修复

日期：2026-10-11。按“审计真实实现 → 用原控制器重现 → 最小修补 → 回归 → 保留独立接收阻塞”推进。

## 缺陷及危害

仓库修复前的 `flow_builder.py` 在 `receive_handoff` 的 `reads` 中声明 `['request','source_bundle','tables','audit']`。但 `audit` 是研究者的评分结论、可能包含隐私/私有真值的路径；`source_bundle` 与 `tables` 包含作者工作区本地路径。节点 prompt 虽写了“只读公开资料”，原生 `flowctl.pending()` 却按声明的 `reads` 真正把这些值投影到接收端。**这会污染独立冷启动接收验证**，不能只用一段提示词修复。

通过原生控制器真实 `pending()` 构造权限测试夹具，故意在研究者审计数据中置入 `HIDDEN_RESEARCHER_SECRET` 和 `/RESEARCHER_PRIVATE/`。修复前接收派发结构确实包含 `audit`、作者路径和私有文本，虽无法由此证明某个真实独立 Agent 已实际读取；这是**输入投影泄露**的完整复现。

## 修复方案

- 将 `audit_data` 的输出分为**研究者私有** `audit` 与**交接方公开** `handoff` 两份 artifact；
- `receive_handoff` 只声明 `reads=['handoff']`，不接收 `request`、`source_bundle`、`tables` 或 `audit`；
- `handoff` 只含可供真实宿主解析的 `packet_ref='receiver_packet_mount'`、`entry='RECEIVE.md'`、`file_count`、`manifest_sha256`，不包含作者目录、私有审计和 oracle；
- 实际服务端/宿主应将 `packet_ref` 映射为**隔离、只读的接收包挂载**；本研究没有权限实际挂载，也不能凭字符串声称隔离成功；
- 修改本地集成测试，授权接收者仅限于单次 `pending()` 的**传输投影测试**，不伪造真实 Agent 收据、业务验收或完成状态。

## 真实测试

对源码字节精确的原原版 `flow_builder.py`（Git Blob `b94822195df8e946088a10c469258c56c7712259`）和原版 GitHub `flowctl.py` 测试，修复前后的接收投影：
- **之前**：读取键 `request/source_bundle/tables/audit`；输入结构包含研究者私有标记、私有路径、作者源文件路径；
- **之后**：只读 `handoff`；`flowctl.pending()` 已不包含这些标记或作者源文件路径，真实接收节点在没有接收能力时仍保持 `blocked`。
- 本地 `flow_builder.py selftest`：**13/13 通过**；
- 原生 Flow `test_native_flow_integration.py`：**7/7 通过**（含真实 `pending` 接收输入投影回归）；
- `test_receiver_packet.py`：**7/7 通过**；
- `test_cold_receiver.py`：**12/12 通过**；
- 原生 `native_flow_smoke.py --repo .`：**PASS**，运行两个可执行节点，第三个接收节点保持 **blocked**；
- 本轮总计 **39 项确定性检查通过**，但其中没有独立 AI 接收者实测。原始两项风险和修复后的投影样本均保存在机器回执，不追溯更改已有历史。

## 需要谨慎保留的边界

`flowctl.pending()` 只表达控制器的**数据投影**；它不能强制限制具体模型通过共享工作区、挂载权限、已有上下文和旧对话记忆看到其他文件。若未来接入独立接收宿主，必须证明它的进程、工具与文件挂载只能看到对应的安全 packet，也必须由独立接收者真正读取 `workflow.md` 并自行重做。此前的程序冷复算不是该实验证据。

本变更只在 `runs/R24/studies/reconciliation/`，不修改原版 `skills/`、C13、C14-lean、原始 R08 checkpoint。真实 18 文件 V7 Python `prepare` 与独立 Agent 对照仍未运行；其历史阻塞与本修复分别记账。
