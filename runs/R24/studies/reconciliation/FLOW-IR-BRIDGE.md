# R24：把对账任务接到已有 Flow IR

这次不再额外造一套 Agent 控制器，而是让研究案例复用仓库内的 `skills/forge-agent-flow/scripts/flowctl.py`。该控制器已经具备 Flow IR 1.1 的校验、编译、状态推进和调用身份检查；本目录只补上本案例的输入适配与可复验回执。

`flow_builder.py` 从公开的 `producer/` 材料构造一份三步 Flow：实际产出发票与供应商结果；根据原数据核实结果；由真实下游接收者冷启动复现 `workflow.md`。它不是通用自然语言规划模型，只为这个明确的研究案例建立可运行接口。研究代码和测试器不加入可移植 Skill。

## 运行方式

在真正的 A111 仓库根目录中：

```bash
python runs/R24/studies/reconciliation/rehearsal.py generate --seed <NEW_SEED> --out <NEW_CASE_DIR>
python runs/R24/studies/reconciliation/flow_builder.py build --public <NEW_CASE_DIR>/producer --out <NEW_FLOW_DIR>
python skills/forge-agent-flow/scripts/flowctl.py validate <NEW_FLOW_DIR>/flow.json
python skills/forge-agent-flow/scripts/flowctl.py compile <NEW_FLOW_DIR>/flow.json --out <NEW_COMPILED_DIR>
python runs/R24/studies/reconciliation/native_flow_smoke.py
```

别把 `private/` 交给执行者；同一主机上的子文件夹并不是实际安全隔离。未获得真实执行能力回执时，`flow_builder.py` 默认将本地写入与独立接收者均标为不可用。操作者可用 `--workspace-receipt` 声明其本地写入条件，但一段字符串不构成可信的提供商授权。为了避免伪造独立性，该适配器**没有**通过传入字符串直接启用独立接收者的参数；只有真实宿主核实该能力后，才能在其允许的受控流程中绑定。

`native_flow_smoke.py` 设计为在仓库内调用既有 Flow IR 控制器，先验证和编译，再以研究脚本模拟 producer/audit 的有限计算回执，最后检查独立接收节点是否如实阻塞。这不是独立 Agent 行为测验，不能由本地模拟收据提升 C14-lean。

## 实际执行与局限

2026-10-10 在本地 Python 3.13.5 环境中，`flow_builder.py` 的 9 项自测全部通过，生成了具有 `produce → audit_data → receive_handoff` 节点的 `flow.json` 和 `inputs.json`。公开源文件哈希在生成的输入中冻结；修改原件会改变身份。编译前本地结构检查通过；它只是小范围检查，不是完整的原生 `flowctl.validate`。

同一环境缺少仓库原有的 `flowctl.py`。实际调用 `native_flow_smoke.py` 返回 `status=blocked`、退出码 2，且 `performed_native_check=false`。这正确反映运行条件缺失；**尚不能宣称既有控制器的原生集成测试已通过**。应在真正的 A111 checkout 内执行上述命令，保留原始日志、环境与任何首次失败。

进一步仍需真实新执行者使用 C13 与 C14-lean 完成未见任务，并由确实隔离的另一接收者重做工作。没有这些结果，不能判定哪一版 Skill 更好。

脚本本地受测与 Github Git blob 已按字节身份核对：`flow_builder.py` 为 `ad78e96776c6b3148d5cad9f3c63ee4def6da135`，`native_flow_smoke.py` 为 `29c675768c2894a33496a0c98b82daad5c4039b4`。本次审查详情见 `FLOW-IR-LOCAL-RESULT.json`。
