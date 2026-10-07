# L3 TODO / 已确认设计进展

任务：R19 / C11 / L3 独立工作流设计；owner=L3设计构建者；写域=runs/R19/levels/L3/design；输入=L3.md及指定raw原件；不求解原题、不读其他层和历史答案、不改共享state。写域为合作约定，不是安全隔离。

|ID|依赖|任务/接受条件|状态|证据/阻塞/下一动作|
|---|---|---|---|---|
|D1|无|读取本层用户要求和指定skill及相关references，明确交付为设计|done|已读取workflow-design/modeling/evaluation/iteration-and-recovery/continuation；读取AGENTS后以本任务明确的只读/写界优先，不读START_HERE/state。|
|D2|D1|保存确认进展后提取原材料、冻结源定位|done|先创建本TODO，再提取；source_extract.json和source_map.md，三页PDF源图均看过，DOCX全部段落/表及XLSX全部cells/合并/无公式核查。|
|D3|D2|六类任务、题目3及程序必交映射到输入输出/目标/硬约束/检查|done|workflow.md第2-6节，明确附2可选及缺信息分支；没有填任何数值结果。|
|D4|D3|工作流可移交：决策、分支、方法比较、逐件数据接口、数值门、论文/复跑/停止条件|done|workflow.md、handoff.md；所有求解/测试为待执行，不设通用两次恢复停止。|
|D5|D4|自检设计文件与原题/接口一致，生成诚实状态|done|result.json；设计静态检查与源对照完成，未把自检声称独立接受。|
|NEXT|D5|启动下一阶段任务：接收者在独立执行目录核查原始hash并写规范化data与assumptions|not_started|路径=handoff.md“接手后第一项真实动作”；task_id=A-data-audit；此构建授权仅设计，未实际启动求解，设计任务到此完成；执行者接手后真实启动才更改状态。|

当前状态：design_complete / execution_not_started。已保存初始和原题审计后的进展。真实失败1（静态断言：handoff缩写使完整任务ID缺失）；工具恢复0；实质修复1（展开六任务ID，原断言重验通过）；研究/求解迭代0；未决调用0。这里只计本构建者已观察事件，不代表接收者执行不会失败。截止、计算总预算未知；model/tokens/cost=null。无联网、安装、其他层读取或共享state修改。未来执行预算由真实资源约束记录，不虚构。

尚需执行的全量工作：A数据及假设冻结；B/C基准和真正端到端烟测；D/F六任务算法与方案；G数值核验/同条件比较；H参数分析和可选附2适配；I完整论文与技术报告；J干净复跑及逐项交付判定。当前完成的是方法设计，不是这些执行事项。

失败事件：第一次静态设计检查命令exit1/AssertionError；确认缺Q1-S2、Q1-F2、Q2-C的字面ID，源于“Q1-S1/S2”等缩写。已将交接首动作展开六个完整ID，再按同断言重验；不会删除原失败或作为整任务停止理由。

修正后静态检查通过：全部必需文件非空、JSON可读、原始hash一致、六ID跨workflow/handoff可见、约束/接口关键词及源对照、相对raw路径正确、未知遥测null和未执行状态一致。检查器关键词用工作流实际措辞“累计”，该调整未改变原承重要求或数值门槛。此检查只涉及设计，不是求解烟测或接受。
