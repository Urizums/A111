# 可交接校准产出

本目录是 Forge C13 的一次有界前向构建与执行。采用“每个新原点最新已到达标签”政策，原预测保持其固定截止的信息集。正式产物位于 `results/`：每个新原点的完整日向量、全部坐标残差、版本及到达来源、完整性状态与短中文科学说明。`clean-rerun/` 是独立目录复跑，`fixtures/` 是保留的拒绝样本，后两者都不是正式结果。

从 [中文结果与科学说明](results/说明.md) 开始阅读；[机器来源及结果](results/results.json) 保存源文件、行号（表头为第1行）、SHA-256 和所有版本信息。[可复用工作流](calibration-flow/SKILL.md) 可在其他仓库使用，只含 Markdown；代码、测试、收据均放在其外部。

## 本次结果

| 决策原点（Asia/Shanghai） | 完整日数 | 日期：向量（A,B；件） |
| --- | --- | --- |
| 2026-05-03 18:00 | 1 | 05-01：(1,2) |
| 2026-05-06 18:00 | 3 | 05-01：(3,4)，05-02：(1,-1)，05-03：(2,1) |

05-04 在第二原点也不完整，B 标签尚未到达。预测 v2 迟于原预测截止，两个新原点都不能用它修改原预测。完全重传不增加样本；两原点同日期的修订向量不是独立新增日期。这里只交付校准输入池，没有训练新预测模型、拟合校准器或声称区间/性能/获奖效果。

## 从零复跑

Python 3.12.8 是本次实测运行时，仅用标准库；PowerShell 可使用系统现有 Python。输入目录必须包含 `raw/{series.csv,forecasts.csv,labels.csv,decisions.json}`。输出目录必须此前不存在。可从任意工作目录用绝对路径调用：

```powershell
python -X utf8 -B '完整路径/production/code/calibrate.py' --inputs '完整路径/inputs' --out '新的空缺路径/run/results'
python -X utf8 -B '完整路径/production/code/author_check.py' --inputs '完整路径/inputs' --outputs '新的空缺路径/run/results' --report '新的空缺路径/run/author-check.json'
```

或在本 `production/` 目录执行完整重跑、接收检查和字节比较：

```powershell
& ./code/reproduce.ps1 -Inputs ../inputs -OutputRoot ./my-new-reproduction
```

本次原运行、不同工作目录从零复跑、数值接收检查、真实拒绝都有 `scripts/record_command.py` 的实际收据。已保存输出而非仅给出伪代码。每次复跑新建输出域，不覆盖已有证据。若希望保留逐命令收据，按 `evidence/` 中 argv 形式调用已有记录器并指定唯一 `--out`；它是仓库证据工具，计算程序自身不依赖它。

## 检查与交接边界

[作者接收检查](checks/author-receiving-check.json) 从原表另路重算16个坐标、8个日状态、版本排除和26行中文表格；检查来源、十进制算术、固定预测截止、标签版本/到达、完整日、重复和跨文件一致性。[clean 复跑比较](checks/clean-reproduction.json) 验证6个正式产物字节一致。真实冲突版本与未来标签消费分别被生产端和接收端拒绝，原始坏样本和非零退出收据保留。

这些是**作者检查**。独立上下文接收判断尚由 coordinator 承担，作者完成不能替代该判断。详见 [交接](handoff.md)、[冻结要求与门](brief-and-gates.md)、[过程历史](process-history.json)、[终态](checkpoint.json) 和 `manifest.json`。遥测 model/tokens/cost 为 null；没有创建仍在运行的子进程、后台任务、发布或根目录元数据写入。
