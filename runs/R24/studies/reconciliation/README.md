# 一项更接近真实自主设计的工作流实验

这不是一张要求 Agent 照着代码步骤操作的题，而是一份简短的业务需求：运营团队要在某个决策时刻，完成发票和付款的对账，保留每张发票及每个供应商的结果，再把流程交给下一位同事复用。下游导入端有真实需要的 CSV 接口。公开材料包含原始发票、修订和付款事件；方法由执行者选择。

**为什么做它：** 先前 `casebench.py` 的两种任务足以检查显式列出的字段和方法是否完整，却很难检验 Agent 是否能自己发现领域职责，例如截止时点、迟到修订、无效付款、供应商聚合，以及能否让别人不依赖作者的隐含知识复现。此处用新的任务类别探测这些能力。它不能单独证明 Forge 的一般智能或 C14-lean 的优势。

## 在开发环境直接运行

```bash
python runs/R24/studies/reconciliation/rehearsal.py selftest
python runs/R24/studies/reconciliation/rehearsal.py generate --seed 2819 --out /tmp/forge_reconcile_demo
# 只把 /tmp/forge_reconcile_demo/producer 的内容交给被测执行者
python runs/R24/studies/reconciliation/rehearsal.py grade --case /tmp/forge_reconcile_demo --submission /tmp/workflow_output
```

生成器拒绝覆盖既有目录。它会在 `producer/` 产生 `brief.md`、`consumer.md` 和三个 JSON 源数据，在 `private/` 产生带公开材料 SHA-256 的结果预期。不要把 `private/` 给执行者；同机的两个子目录**不是访问控制**，正式研究必须由实际宿主分别管理读权限、工具消息与上下文历史。

使用者需要输出 `ledger.csv`、`suppliers.csv` 与可供同事实际复用的 `workflow.md`。数据检查器会核对所有发票和供应商、整数分、时间截断与只认可用修订/有效付款。**它刻意不通过关键词猜测流程是否好用**：只要出现了工作流文件，`workflow_usability` 仍是 `unverified`，`overall_accepted` 不会自动变成 true。必须由真实下游接收者在不读取作者答案的情况下试着重做一遍，再作实质验收。程序的 0 退出码只支持自动化数据检查范围。

## 如何用于 C13 / C14-lean 的公平对照

选择实际未见过的新输入实例，在执行前确定验收与真正可见的数据。分别给新上下文相同的业务简报、源文件、资源和允许的工具，一组读取 C13，另一组读取 C14-lean；不要把作者的修正记录、旧实验答案和 `private/` 通过 argv、日志、摘要或其他通道发给执行者。

数据评分与流程可用性分开：前者由程序从冻结 oracle 核，后者由真实同事/独立 Agent 根据原件复现、检查解释能否覆盖非法/迟到/重复材料，并观察是否出现多余架构或失去必要检查。缺少独立上下文时可做作者自检，但不能称双盲或版本因果对照。代码不负责召唤/调度模型、持久化密钥或隔离工作区。真实测试开始前还需明确预算/能力/权限与停止条件。

**案例边界：** 对账使用纯合成数据，六张发票、三家供应商，截止日随种子变化。它只测特定交付和信息截断逻辑，不涉及生产级财务系统、税务规则、付款合规或真实个人信息。此生成器及评分器属于研发域，不进入便携式 Skill，也不强制未来 Agent Flow 采用固定 CSV 结构。
