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

## 2026-10-10：源材料守卫与分离的公开输入生产路径

本轮发现并修复了一个真正会影响交付的缝隙：把 SHA-256 写进 `source_bundle`，**不代表** `flowctl` 会自动读取磁盘并核对文件仍然一致。旧版 `flow_builder.py` 冻结了哈希，但旧 `native_flow_smoke.py` 没有在调度前后核对这一事实。

新增 `verify_public_source()`，通过预先冻结的五个文件身份检查实际字节、缺失/异常文件、超大文件与符号链接；研究适配器在创建实例时核验一次，原生集成探针计划在分派前、生产后及评估时分别调用。它只是本地瞬时一致性检查，**不是**宿主权限隔离、持久锁或平台安全承诺。

另增 `public_producer.py`：只用 `producer/` 公开文件独立计算并输出两份 CSV 和方法说明；它不导入 `rehearsal.compute`，也不读取 `private/oracle.json`。这避免了生产与评分共用同一函数导致的虚假可信度，但仍由同一研发者编写，因此不属于独立审查。

本地实际结果：`flow_builder.py selftest` **12/12** 通过；公开源读取的生产程序在种子 100–159 的 **60/60** 个实例中均被研究评分器接受；新增的 E2E 负例显示修改公开付款文件后守卫拒绝、恢复原始字节后通过、真实生产结果被接收、篡改供应商输出后又被拒绝。证据见 `FLOW-GUARD-V2-RESULT.json`。

受测且已回读的 Git Blob：`flow_builder.py` = `b94822195df8e946088a10c469258c56c7712259`；`public_producer.py` = `691cb6d234e099911580edd4d5b94310ea101dfd`；`native_flow_smoke.py` = `312f9270bd581765d19f198ec0b4977680cce7fa`。之前的九项自测与旧代码身份保留在初次记录中，没有追溯修改历史通过结论。

当前本地没有完整 `flowctl.py` 及其依赖，原生探针仍返回 `blocked`，故**原控制器实际编译及节点推进仍未过门**。GitHub 现有 CI 不自动运行此研究脚本；完整 native gate 需在获得真正的 A111 checkout 后执行。随后才值得在新独立 Agent 上比较 C13/C14-lean 与交接可复用性。

## 2026-10-10 后续实测：原生 Flow 控制器已通过

此前因本地缺少控制器文件而记录的 `blocked` 是**当时的真实结果**，保留不覆盖。现在已从 GitHub 连接读取完整的上游 `flowctl.py` 与 `nestedcheck.py`，在本地重建最小 A111 文件环境，并用 Git Blob SHA 确认与主干原始文件字节完全相同（`afd4df10b3406083fd9e337171a6b2b5477508ca` / `c0e221a2b16f2eda18c719cf05959d5dcea1fc16`）。

真实运行 `native_flow_smoke.py --repo .` 返回 `status=pass`，经原控制器完成 Flow IR 1.1 校验、编译和两个节点的状态推进，拒绝伪造与重复调用 ID，并在无独立接收者能力时保持第三节点阻塞。新增 `test_native_flow_integration.py` 覆盖实际 `flowctl` CLI 的 validate、compile、start、next、原状态不可覆盖、失败路径和源文件身份约束，六项均通过。原测试代码 Blob 为 `ad22fe51edb3a9f8fc95d68984ba0c26ecfbb4a4`。同环境复跑研究适配器 12/12 和对账生成器 13/13 自测均通过。

这次**确实执行了原版控制器**，但运行环境是哈希验证过的最小源文件镜像，非完整 GitHub checkout；没有运行仓库所有测试，也没有调用一个真实独立的 Agent。第三节点保持 `blocked` 且 `terminal_business_acceptance=false`，`workflow.md` 的冷启动可用性仍待另一实际接收者检查。C13/C14-lean 的新材料公平行为对照同样尚未进行。

详细实测机器回执见 `NATIVE-FLOW-REAL-RESULT.json`。在完整 A111 checkout 中可复跑：

```bash
python -m unittest discover -s runs/R24/studies/reconciliation -p 'test_native_flow_integration.py' -v
python runs/R24/studies/reconciliation/native_flow_smoke.py --repo .
```

这使 R24 的**本地原生集成门**获得实测通过，但不替代独立接收、运行权限或候选晋级门。避免为了一个通过的切片继续膨胀便携 Skill；优先利用新上下文开展真正的能力研究。

## 接收包集成（2026-10-10）

原生 Flow 的数据核验完成后，现已调用 [受控接收包生成与校验](RECEIVER-PACKET.md)，向接收者只准备八份原始输入与交付文件，并额外携带接收说明和哈希清单。13 项本地测试通过；原控制器仍在缺少独立接收能力时阻塞，而不是自行标记业务成功。接收包只能约束复制了什么文件，不能保证另一个模型的上下文真正独立。详见 `RECEIVER-PACKET-RESULT.json`。

## 仅凭接收包重新计算（2026-10-10）

原生 Flow 的 `audit_data` 现在额外启动了不读取私有真值和生产函数的 [冷启动接收复算](COLD-REPLAY.md)。新复算与真实原控制器推进均已在本地通过，第三个需要独立 Agent 的节点仍正确保持 `blocked`。相应证据在 `COLD-REPLAY-RESULT.json`。此项不提升 `workflow.md` 的自然语言可用性为已验收。
