# Q1 本地 recording qualification 独立核验

本核验只涵盖已稳定的 `coordinator/recording-qualification/`，不读取 C1 两个业务 block，也不把 Q1 计入八个 C1 样本。Q1 明确限定为本地 target 命令：0 business workers、0 actual native calls；synthetic `native` target 是本地调用 `capture.py native`，不代表实际 `spawn_agent` 或 status 工具调用。

## 冻结身份与范围

`Plan_Freeze.json` 中的 `plan_sha256` 与 `Qualification_Plan.md` 的 SHA-256 完全匹配：`31b2e2138aa71d0eed5fd670721ecce5e0f2afdd3ec2e978390be6e951c7073f`。冻结列出 Q01–Q05，且把 outer capture wrapper 明确列为 instrumentation boundary：只把它启动的 target 纳入分母，不递归采集 wrapper，也不声称覆盖所有 host/tool activity（`Qualification_Plan.md`, Q05）。因此 C1 observer subprocess 的字面范围问题不会自动变成 Q1 的失败；Q1 仅验证其明文定义的本地 target 范围。

四个 outer records 的 `argv` 均指向实际目标；四份 stdout/stderr 的 base64 解码后都与保存的文本字段一致。每条记录 begin/end 的 boot ID 都相同，monotonic span 非负，且 `elapsed_seconds` 等于 `(end.monotonic_ns - begin.monotonic_ns) / 1e9`。四个目标记录及 SHA-256：

| Target | Exit | Same-boot span | Outer record SHA-256 |
| --- | ---: | ---: | --- |
| marker-success | 0 | 32,805,183 ns | `73d2e28a7b202a3edb44326e726bffda47c7333310051cf4756a2b3f2cc77b51` |
| marker-failure | 2 | 29,753,303 ns | `3bf3de3a69631d1b8605a551600b595b8dd6e6dfc1f3ecf3716d7b4cdb6df2aa` |
| synthetic-native | 0 | 34,404,799 ns | `683adbc1bde16f5b382221c872ca816094e7bf7e52f2c57007f8597dc219e4de` |
| target-failure | 7 | 13,731,138 ns | `263380837aaddcd90aaf7aba5efdcd7383e8d3496cb1dee4d64362163b2e3723` |

## Q01–Q05 核验

- **Q01 — 通过，限本地目标。** 成功与失败 marker target 的 outer record 都包含其确切 `argv`、stdout/stderr 的原始 base64 与 decoded 字段、exit code，以及同 boot 起止 monotonic timestamps。成功目标的 event 时间戳落在 outer span 内；失败目标以 exit 2 结束。
- **Q02 — 通过。** `events/` 中恰有一个事件文件。它与成功 target stdout 中报告的绝对路径相同，事件字段和值完全相符。失败 marker 的 stdout 为空，且没有创建第二个事件或伪造 marker。
- **Q03 — 通过，限 synthetic payload。** `synthetic-native-event.json` 的 `raw_base64` 解码后逐字节等于 `synthetic-intent.json` 原始 bytes；payload SHA-256 `0867e76ee70b9327ce4e82b1d058e5eff0f2b981b0b0ab7425031e394e5eb519` 与记录一致，解析后的 JSON 也一致。Outer target stdout 指向该本地 event 文件。payload 自称仅用于本地 target 测试且“never called”；文件没有 native tool receipt 或 worker 创建证据。
- **Q04 — 通过。** `target-failure.json` 的 argv 明确写出 stdout bytes `41 00 42`、stderr bytes `45 ff 0a` 并退出 7。所存 base64 字符串为 `QQBC` 与 `Rf8K`；解码后分别得到上述 stdout/stderr bytes。文本字段是对应的 UTF-8 replacement 解码，exit code 保留为 7。
- **Q05 — 通过，且仅按其明确边界。** 计划把 outer wrapper 指定为采集边界，并明确不递归采集 wrapper、不声称覆盖所有 host/tool 行为。Q1 记录没有越界声称真实 native 工具或普通 worker 已被测量。

## 结论边界与留存限制

基于保存的 target records，Q01–Q05 的本地 qualification 证据相符。它只验证这些本地目标的 argv、bytes、退出码和 observer event 写入；不证明 C1 的任何 worker/operator 遵守协议，不证明真实 native receipt 捕获，不验证其他 host activity，也不能支撑性能或提速结论。Q1 当前目录没有 C1 run records。

`Plan_Freeze.json` 绑定计划文本的 hash，但未记录 `shared/capture.py` 的执行时代码 hash；target records 保存脚本路径而非脚本 bytes/hash。审计时当前文件 hash 为 `1610164872febd6b589e21d923d28113ab1c507be1e222a0206a6379e75a0558`。因此这些原件可验证捕获行为的保存值，但无法仅凭 Q1 freeze 证明当时运行的脚本字节与当前文件完全相同。Q01–Q05 没有把该代码 hash 列为验收行；这里作为 provenance 限制记录，不扩成新的 Q1 失败标准。

同理，freeze 绑定了 plan 内容，但 Q1 目录没有独立的 plan-freeze 时间标记；原件本身不能证明 hash 写入早于 target 调用。Root 的任务说明称其先冻结五条验收再调用 targets；这与现有记录相容，但该先后顺序未由本目录的独立时间证据证明。保留这项 provenance 限制，不据此补设通过标准。
