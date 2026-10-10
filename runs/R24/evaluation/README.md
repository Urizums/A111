# R24 可复现交付检查器

这是**研发域内**的小型 Python 3.10+ 标准库工具，**不属于便携式 Skill**，也不是通用 Agent runner。它检验后续执行者是否真正交出了指定结果，不检验独立性、模型效果或总体任务复杂度。

先运行 `python runs/R24/evaluation/casebench.py selftest`。该自测只判断检查器是否接受合法产物、拒绝遗漏/错误产物，不能当作 C13/C14 的真实行为对照。

生成新的可控任务实例：

```bash
python runs/R24/evaluation/casebench.py generate --kind extract --seed 202710 --out /tmp/forge_case_extract
python runs/R24/evaluation/casebench.py generate --kind two_methods --seed 202711 --out /tmp/forge_case_both
```

生成目录下的 `producer/task.md` 和 `producer/input.json` 是执行者输入；`private/expected.json` 是评分真值，**必须靠真实宿主隔离在执行者不可见的目录/上下文**。同目录不同子文件夹不是访问控制，因此不要把整个生成根目录交给被测 Agent。生成器拒绝覆盖既有用例，以便保留冻结的首次实验。正式比较应使用事先选定且从未进入被测上下文的任务种子与受控真实输入，并保存环境、预算、工具调用、原产物以及盲审/知情区分。

被测执行者写完产物后，接收侧运行：

```bash
python runs/R24/evaluation/casebench.py grade --case /tmp/forge_case_both --submission /tmp/submitted
```

`extract` 要求 `answer.json` 含源中的城市与截止日期。多方法 `two_methods` 要求 `proposals.csv` 对每个订单同时给出 alpha/beta 行及 `recommendation.json`；检查器按原始数量规则和总量目标重算。额外文件只发出维护负担警告，不直接构成验收失败。它不判断执行者是否用了过多计划时间、角色或表格——这些必须在真实行为记录中单独检查。

**边界与缺口**：案例故意小而简单，只能测交付完整性与数值规则，不能证明长期预测、UI、复杂 DAG、工具调用可靠性、信息隔离或 Skill 优越性。独立对照需要真实不同执行上下文、公平的资源条件和冻结的评估者输入。旧的 R23 反例不能作为新的盲样本重新刷成功。后续如需增加其他任务，优先增加新的判别性失败模式，而不是增加固定数量的通用模板。

本脚本当前内置 13 项 deterministic selftest（初版为 8 项），并能用不同种子生成变体；后续行为试验应把 seed、输入/判定 hash 与每次产物版本一起保存。
## Skill 结构维护检查

使用 `python runs/R24/evaluation/skillcheck.py --selftest` 验证检查器的五种正常/错误输入；或 `python runs/R24/evaluation/skillcheck.py runs/R24/candidate/C14-lean/forge-agent-flow` 检查一个实际 Skill 目录。该工具只验证 SKILL.md 的基础元信息、UTF-8 可读性、相对链接是否存在和是否越出 Skill 包；不会要求固定九文件、标题模式、Agent 角色数、表格比例或特殊遣词。

两份评测工具分别解决不同问题：`skillcheck.py` 保证文档包基本完整；`casebench.py` 用原始任务要求检验产物。**两者的本地自测都不能证明 Skill 让一个新 Agent 表现得更好。** 要验证效果仍需独立执行上下文与对应未见任务。

### 原件身份与异常数据审查（2026-10-10 增量）

生成器会在接收端私有预期文件中记下 `producer/input.json` 与 `producer/task.md` 的 SHA-256，评分时逐项比较原始字节；原材料被修改或缺失即不通过。旧版生成的无绑定案例仍可查看，但会给出 `source_identity_checked=false` 和警告，不可当作经过原件核验。JSON 重复键与 CSV 隐藏额外单元格也会拒收。该做法避免评测时无意换题，**并不是宿主级隔离**；如果生产者能够打开私有 oracle，仍不构成盲测。

当前源码 Git blob：`f8bd05ca83e25f69b42100bdac08939768d052d8`。新版本 13 项自测通过，并且实际生成了 seed=987230 的双方法案例，验证全量结果 PASS、缺少 beta 的交付 FAIL（四条缺项）。详见 `CHECKER-V2-RESULT.json`。这些产物是确定性程序自测，不是两个 Agent 的行为比较。
