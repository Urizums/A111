# R24 — 准备独立接收材料（接收包）

本研究步骤解决“原 Flow 已能推进，但下游到底收到什么”这一交接接口问题。它不改变便携 Skill，不增加每个任务必经的文档格式。只有涉及**真实独立接收**或跨执行环境传递结果时，才需要这种受控材料边界。

`receiver_packet.py` 从已有的 `producer/` 公开业务材料和 `submission/` 真正产物复制一个最小接收包。它只包含原业务需求、五份数据/说明，以及 `ledger.csv`、`suppliers.csv`、`workflow.md` 三份交付；再附上接收说明与校验清单。源文件可以与事先冻结的 Flow 输入哈希绑定。不会复制 `private/oracle.json`、作者诊断、旧测试分数或整个工作区。

接收说明保持自然语言：要求下一位执行者先读原任务和消费者接口，再利用流程解释复做业务结果；出现遗漏、解释不清或来源歧义时，应具体指出。验收绝不能从“接收包存在”“哈希一致”或“工作流文件不为空”推导通过。

## 如何运行

在已准备好源数据与真实产物的环境：

```bash
python runs/R24/studies/reconciliation/receiver_packet.py build \
  --public <case>/producer --submission <output> --out <new_receiver_dir> \
  --flow-inputs <compiled_flow>/inputs.json

python runs/R24/studies/reconciliation/receiver_packet.py verify --packet <new_receiver_dir>

python -m unittest discover -s runs/R24/studies/reconciliation -p 'test_*.py' -v
python runs/R24/studies/reconciliation/native_flow_smoke.py --repo .
```

`--flow-inputs` 用来检验源文件是否与先前的 Flow 输入 SHA-256 匹配。若没有先前的冻结身份，可以省略，但那只能证明复制时的材料一致，不能证明它与先前任务完全相同。研究者不应将脚本输出当作平台凭证或权限证明。

## 实际反例与测试

本地运行：接收包 7 项、现有原生控制器 6 项，共 **13/13** 项测试通过。通过的情形包括文件白名单、作者附加诊断不被转发、冻结原件改动拒绝、符号链接拒绝、接收包篡改拒绝、伪造已验收状态和接收指令替换拒绝、禁止覆盖历史接收包。原生 Flow IR 编译和节点推进依然通过；独立接收节点未授权时仍为 blocked。

额外对公开合成种子 323992 执行了：生成原任务、公开数据计算、数值验收、接收包创建与独立 CLI 核对、ZIP 实际解压和 UTF-8 文本读取。接收包包含八份原材料/交付文件，实际包内另有接收说明和清单。研究者验证只证明传递范围和字节一致，不宣称另一名真实 Agent 已使用 `workflow.md` 完成冷启动。

版本来源及结果见 `RECEIVER-PACKET-RESULT.json`。原生控制器 `flowctl.py` 和 `nestedcheck.py` 是上一轮从 GitHub 原始代码按字节重建的最小运行副本，未对完整 checkout 进行发布验收。原始历史与首次失败不受影响。

## 不能误读的边界

文件白名单不是进程/操作系统沙箱，也不能控制模型继承的上下文、工具日志、命令参数、自动摘要或网络可见资源。接收包生成脚本无法审计文本内部是否夹带作者答案。清单哈希没有外部受信签名；恶意者若能同时改文件和清单，可以构造新的自洽副本。要声称真正独立/盲验，仍需要宿主层的信息隔离和可信冻结材料。

**下一实质动作**应是在能运行真实独立执行者的宿主中，向其仅传入本接收包，要求复做结果并产生独立回执。R24 的 C13/C14-lean 前瞻行为对照仍未运行，本研究包不改变该状态。

## 后续接收方数据复核（2026-10-10）

新研究用 [cold_receiver.py](cold_receiver.py) 只读接收包并再次计算原发票与供应商数据，不依赖作者生产函数。25 项分组本地回归通过；即便接收包清单和错误输出哈希同时修改为自洽，仍会因为业务数值不一致而被拒绝。见 [结果回执](COLD-REPLAY-RESULT.json)。这不是对自然语言交接方法的真实独立 Agent 验收。
