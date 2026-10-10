# 接收包独立程序复算（R24）

这项研究只回答一个有限问题：另一个**不借用作者计算函数**的程序，仅凭接收包公开材料，能否独立重算每张发票和每个供应商的余额，并拒绝看似哈希完整但业务错误的输出？

新脚本 `cold_receiver.py` 只接收接收包路径和一个未创建的回执路径；它不导入 `rehearsal.py`、`public_producer.py` 或评分器，也不读取 `private/oracle.json`。实际代码重新读取业务描述、截止时间、修订与付款，并与收到的两份 CSV 对照。 `test_cold_receiver.py` 为研发者编写的反例测试，允许使用原有生成器造数据，但真正的接收子进程只获得接收包。

```bash
python runs/R24/studies/reconciliation/cold_receiver.py --packet <RECEIVER_PACKET> --receipt <NEW_RECEIPT.json>
python -m unittest discover -s runs/R24/studies/reconciliation -p 'test_cold_receiver.py' -v
python -m unittest discover -s runs/R24/studies/reconciliation -p 'test_native_flow_integration.py' -v
python -m unittest discover -s runs/R24/studies/reconciliation -p 'test_receiver_packet.py' -v
python runs/R24/studies/reconciliation/native_flow_smoke.py --repo .
```

实际本地分别执行了 12 项接收复算、6 项原版 Flow 控制器及 7 项交接边界测试，共 **25 项通过**。新版本原生 Flow 探针会在完成生产、数据核验与接收包制作后，另启 Python 进程验证接收包业务结果，随后因真正独立接收者仍不可用而正确保持 `blocked`。示例接收包由前一轮合成数据构成，不是新的盲测数据。

特别验证：更改 CSV 错误数值后同步重算清单 SHA-256，旧文件完整性检查仍会通过，但新的业务复算会拒绝结果；同样会拒绝遗漏余额为零的供应商、挪动截止时间付款、伪造“已接受”、篡改接收指令或留空必需的工作流文件。

**必要界限：** 这证明了一个单独的程序代码路径可以复核数据，不证明 `workflow.md` 的文字能使新的 AI/人类掌握方法，也不证明模型上下文隔离。清单没有外部可信签名；研究脚本针对这一个合成对账业务，不是通用自然语言推导器或需要被移入 Skill 的新硬性规范。业务/独立接收仍是 `unverified`，C13/C14-lean 行为对照仍是 `not_run`。

首次回归的一项测试因断言错误信息措辞不符而失败，随后修复测试断言并完整复跑 12 项通过；原始失败不追溯改判。首次一次全套串行测试因执行超时中断，改为分组运行并分别保存回执。

复现与版本信息见 [COLD-REPLAY-RESULT.json](COLD-REPLAY-RESULT.json)。未来应改用未见业务材料，在真实新上下文中实际复做并报告交接语义的可用性，而不是继续扩展此案例的静态规则表。
