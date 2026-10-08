# R20 工作流设计交付报告

交付状态：可供新上下文执行的纯文档流程已设计；只做原始材料全行审计及一天的有限接口smoke。尚无完整模型比较、14天正式预测/备货、不确定性校准、完整中文论文、最优性证明或独立验收。未来真实需求未提供。

## 使用与读取范围

应用指定 `runs/R19/final/candidate/C12/forge-agent-flow/SKILL.md`，读取 workflow-design、modeling、evaluation、iteration-and-recovery、continuation、source-evaluation、collaboration；源skill保持不变。原题、请求、所有raw、输入锁、C12锁及仓库AGENTS、record_command已读取。AGENTS全局起步要求被本次明确限定读域覆盖；未读全局入口/state、R20 evaluation/coordination、旧成果/其他诊断，不搜索既有论文；无外网查询、无新agent。C12锁所有列出的文件只做字节hash核对，包括未用frontend引用，未据该文设计。

本目录的 `forge-freshfood-flow/`只有Markdown；研发代码与运行证据均在skill外。所生成的skill可连同四篇references迁出使用，实例原件路径可重新绑定。指定Forge只作方法来源，不提供标准答案。

## 已做的真实检查

`evidence/001-material-read.json`记录原题/请求/decision/evaluation完整读取与CSV头部，`002-audit-raw.json`记录所有CSV行审计与所有原件/C12锁字节核对；均实际begin/end、完整stdout/stderr/base64及returncode。

- demand_reports 17577行、8条完全重复；14688日期店品组合，revision1为14688、revision2为2881。原点可用最新标签14592组合=5/1–9/29共152天×96；9/30的96日报available_at为10/1 09:00，全部排除。当前原点已可知的最高版本与附件后来最高版本没有需求值变化；这不表示历史实验无修订。
- 五个历史示例原点（7/31、8/14、8/28、9/11、9/16 18:00）训练标签之后变化数依次19、12、18、17、14。因此需要历史原点快照与后到评价标签分离。
- weather 960行，forecast501、observed459，rain_mm空17；未来42forecast均9/30 16:00同批，2雨量为空，无未来observed。五个历史窗口均只知道次日forecast，无法用历史逐日新预报冒充14天原点信息。
- promotions 16032行，最终原点未来1344键全部已知；上述历史14日窗口仅960键已公开。未公布促销需unknown策略，不能提前拼表。
- calendar 167天；weekday与日期一致。holiday=1历史只有6/19、9/25两天=192店品键；未来10/1–7连续七天。节日外推有效样本是日期而非店品行数。
- 原件与C12锁中全部bytes/hash一致；没有same-key-revision冲突或负需求。这里的hash/无异常是源身份与口径观察，不是科学效果验收。

有限smoke：`evidence/003-one-day-smoke.json`从raw按最终原点快照，选10/1一天96组合；56天同星期中位数点基线，用正边际损失改善/采购成本贪心逐件分配，生成 `smoke-one-day.csv`。得到1326件、采购4652元、容量slack274、预算slack1348。该基线点值下损失约30.375元，按原式不加采购；这只是拟合点上的计算，不是历史预测成绩或真实未来收益，贪心未证明最优。天气和促销未用，区间/校准未做，不能据此选生产方案。

初始smoke对负q、小数q、NaN和56件上限违例实际拒绝。为了覆盖全局资源接收边界，保持同日期同方案，新增两份非法plan：5280件被容量断言拒绝；仅K03/K07各店55件=1320件、6600元被预算断言拒绝。`004-resource-boundary-smoke.json`保存新增断言后的真实运行。前一次原始输出保留，不追认为曾覆盖预算违例。CSV输出不变。它支持本scope的数据→预测→可行q→收件断言/损失接口可运行，不支持完整生产。

## 恢复、版本与证据限制

003→004是计划扩大边界覆盖，不是把失败改称通过。旧命令输出始终保留。001–004使用现有record_command；初始两次准备性读取及建目录是宿主tool receipt，没有在执行前保留本目录的portable开始/结束记录，不能事后伪造；其中一个合并读取显示截断，evaluation随后在001完整重读。科学检查的完整输出已保留。003对应smoke代码在增加断言前的版本；`research/smoke-invocation-003.py`由准确变更逆向重建作历史源码存档，标明是后来重建，不冒称调用时hash已记录。

归档003源码的第一次shell构造因嵌套引号触发PowerShell ParserError，Python未启动，未写文件；宿主tool返回exit1，完整错误和原命令存 `evidence/archive-construction-failure.json`。该tool未暴露UTC开始/结束，因此这两个字段为null，不伪造时间。恢复改为代码文件 `research/recover_archive.py`，用record_command记录真实恢复起止和输出；恢复后包检查重新执行。此为环境/命令构造恢复，与科学试验失败区分但事件不抹除。005检查只覆盖已有文档链接及CSV，未证明003档案存在；增加该收件assertion后另存新的检查记录，不倒改005。

生产执行者还需校验更严的时间类型/时区、字段finite/主外键、rolling origin与训练/评价隔离。设计audit按原件统一ISO时戳作字符串筛选，不能不验证格式就泛化。全部现有观察是作者自检，未独立接受。没有CPU/包/solver/中文渲染全面探测；原生py -3.12 -X utf8 -B和stdlib实际可运行。外网、求解器、论文导出和新执行者能力未知；model/tokens/cost为null。没有虚构预算/篇幅/模型配额或比赛成果。

## 终态产物与后续

主入口 `HANDOFF.md`；纯文档skill与refs给出时间接口、研究决策、原题接收检查、从实际结果到完整中文论文/最终格式责任。`research/verify_design.py`只作作者包检查及CSV重新读入数值重算，结果由其真实command receipt给出，不能代替新上下文完整验收。`manifest.json`列实际文件大小与SHA256；它不hash自身或其写入期间仍活动的命令record，避免自引用，root最后冻结可覆盖这些封装文件。

下一执行步骤是root冻结本包后串行启动新执行者T01，分配独立执行写域；新执行者从原件重建快照与能力记录、冻结历史实验，并完成T02–T09。最后另派新上下文验收原件、实际程序、全量表和论文，不提供作者期望解法/旧诊断。没有模拟已启动该下一阶段；本设计者交付后停止写入等待root冻结。
