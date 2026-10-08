# R20 知情来源补核（原冻结版本）

本补核针对已冻结版本和先前首判，范围只增加对残差校准来源与接收时点的独立复核。它不是新盲测：此前正式接收已在首判冻结后读取并评价合成 holdout 真值；本补核没有再次打开或使用 holdout。原始首判域保持不变，以下是补充源证据及对首判的知情影响说明，不重写 `initial/first-report.md` 或 `initial/first-result.json`。

## 冻结回执引用纠正

初始结果 JSON 的 `execution_freeze_command.path` 错写为 `runs/R20/execution/evidence/production-freeze-command.json`；该路径不存在。真实冻结回执在 `runs/R20/coordination/production-freeze-command.json`，SHA-256 为 `be920505db17ed9c4882d0864d88207286df71a7a8e77819b8c161711ca097b3`，字节数1705，记录状态 `finished`、退出码0；开始时间2026-10-08T20:01:02.869748Z，结束时间20:01:22.055586Z。其参数冻结 `runs/R20/execution` 到 `runs/R20/execution-lock.json`，回执输出602文件、frontier R20-04、queue_valid true。错处是首判 JSON 的路径字段，不是冻结回执状态或执行冻结事实。该来源更正不改变首判任何实质门或 verdict。

校验命令完整记录在 `command-freeze-reference.json`；旧引用、实际路径、字节/哈希、argv、起止、退出码和输出也可在 `freeze-reference-correction.json` 查阅。初始 first-result SHA-256（按冻结时计算）为 `e6ff4f4baffa6ba431e6aa157826fe18107690477b864510780a31012134f8d8`；文件未修改。

## 原始来源至校准残差的独立重建

我独立从允许读取的冻结 raw 重建截至配置 cutoff（2026-10-04 18:00，北京时间）的标签版本：按完整键过滤 `available_at <= cutoff`，每键取当时最高 revision，共14,688行。再按六个配置原点训练 Ridge10，并重建每个原点后续14日的点预测；训练快照限于该原点已到达版本且 `service_date < origin`。每一来源日必须有96个唯一店品键。残差逐键定义为该 cutoff 最新标签的需求减去当时固定原点点预测；该来源日的 ready 定义为该96行所选标签 `available_at` 的最大值。校准池仅在来源日结束后按 `ready <= origin` 进入。

独立重建的84个来源日期与最终交付可用范围中83个完整96维误差向量来源一致。逐原点对照交付 `calibration_lineage_*_shared_ridge10.csv` 的日期、source_origin、ready，五个可校准原点均完全相同，入池行数依次为11、25、39、53、67，且每个ready不晚于相应origin。对非最早原点，重新拟合点预测与历史预测表对比5×1,344键，最大差不超过5.0e-11。最终交付 `residual_lineage.csv` 的83行逐项与独立重建日期/ready/source_origin完全一致；`residual_vectors.csv` 为83×96，逐值最大绝对差小于5.0e-11（文件按10位小数输出）。

源级完整逐键证据保存在 `source-key-audit.csv`，共84×96=8,064行，每行包括来源日、来源原点、向量ready、门店/商品、选中revision、该版本available_at/实际值、独立预测、逐值残差及是否在最终原点可用。具体复算和机器可读总结见 `recheck_calibration.py`、`source-recheck-result.json` 与相应完整命令记录 `command-calibration-rebuild.json`、`command-calibration-key-audit.json`；所有使用raw源输入的成功命令都退出0。

在最终决策原点2026-09-30 18:00，83个可用来源日从2026-07-09至2026-09-29。六个来源原点贡献14、14、14、14、14、13日。唯一不符合最终ready条件的窗口日为2026-09-30，其96个标签最晚于2026-10-01 09:00到达，因晚于9月30日18:00而没有进入池。这与论文§5对晚到版本整向量排除的定义一致；其余每个选入版本的available_at均不晚于各自ready，且ready不晚于使用它的origin。没有发现用到原点后才可知的标签版本。

## 边界控制与解释限制

`run.py` 的资格过滤是局部列表表达式 `v['ready'] <= ts(origin)`，并没有暴露可独立注入状态的校准接收函数。故未声称直接向生产接收器注入，而是对raw独立重建实际日级入池集合，并逐原点与冻结交付精确比对；另在独立重建路径做真实边界控制：`ready == origin` 会进入；超过最终origin的2026-09-30完整日向量被排除；把一个96键日向量中任一标签改为原点后1秒，其向量ready随之越界并整日排除；95/96键不满足向量完整性断言。生产路径原本在合并时要求每个fold恰有1,344行、无缺失标签，并由96个键的日期最大available_at计算ready。以上边界注入是独立复刻，不冒充生产代码本体的变异测试。

这个核查支持原首判对d1（时点/版本可知性）、d2（历史验证使用的校准池）、d4（最终交付与从raw重建一致）的判断。它补足了首判文字未逐键展示校准 lineage 的证据缺口，但没有找到必要缺陷，也没有理由更改任何d1–d5首判。此结论只针对所冻结合成数据。没有建议新增模型、扩大实验/页数或设定分数门槛。

## 命令与失败

`command-calibration-rebuild.json` 和 `command-calibration-key-audit.json` 保存argv、cwd、起止时间、标准输出/错误、退出码及base64。冻结引用检查完整记录在 `command-freeze-reference.json`。命令过程均结束；首轮重建与添加逐键审计两次均退出0。未修改raw、冻结代码、交付或initial域；未读作者自检、repair、root诊断、作者活动输出，也未读/使用任何生成器或holdout内容。

模型、token与cost遥测仍未知，均为null；gpt-6-luna/high只是请求配置，不是观测到的provider遥测。
