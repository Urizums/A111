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

本脚本内置八项 deterministic selftest，并能用不同种子生成变体；后续行为试验应把 seed、输入/判定 hash 与每次产物版本一起保存。