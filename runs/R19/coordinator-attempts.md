# 协调者恢复记录

下列是父会话工具返回的当时转录，不是完整provider日志；它们属于R19协调/开发工具域，不改动任何旧试验纠正计数，也不冒充新求解者的错误。

- 首次在workspace外层运行git，发现该目录不是仓库；已使用work/A111真实checkout。
- 读取R16/source/manifest.json失败，实际文件是source-manifest.json；原件仍在，后续只以官方raw文件进入测试。
- PowerShell中rg文件通配参数未展开，已按明确文件路径读取。
- host_preflight首次路径及随后缺--root调用失败；加真实checkout与--root后实际完成，只验证Windows字节锁，控制器使用WSL。
- register-command.json因缺effect.target等控制器结果字段失败；此前未写共享continuation，初始preparation-result.json与失败命令保留。preparation-result-v2.json补齐真实的“准备阶段”效应/限制并成功注册，不增加科学效果主张。
- freeze-check-command.json首次核对使用了错误的JSON规范化方式，产生“历史任务改变”的假警报；改用与continuation.identity完全相同的格式后，freeze-check-v2-command.json实际确认原50份任务内容哈希一致。失败回执保留，不将其解释为历史真的发生变化。

后续恢复以新文件/新回执追加；分类为工具/环境恢复、实质修复或正常研究迭代。两个局部错误不会停止整个业务目标，但不重复无新信息的相同路径。

接续追加：resume-handoff-command.json记录协调者误用Windows原生Python运行依赖fcntl的完整交接检查，实际报ModuleNotFoundError。未修改控制器兼容边界，改用既定WSL运行，另存resume-handoff-wsl-command.json；失败回执保留，属于环境调用恢复，不是求解者缺陷或旧预算重置。三个R19 actor曾报真实额度边界；随后实际账号查询ordinaryUsageAllowed=true，父节点接续同一actor并观察三者running，见resource-interruption-and-resume.json。状态转录没有完整provider耗用数据，model/token/cost保持null。

发布前完整交接检查曾发现活动入口已更新而可变release catalog尚未刷新，真实失败见resume-handoff-wsl-command.json；旧catalog字节另存integrity-history，新目录只更新两入口条目并加入新增冻结版本，所有原版本锁不变。l1-delivery-handoff-command.json随后实际通过1043份revision工件核查。Git默认whitespace检查将CRLF及PDF语法空格当作问题；失败回执保留，按原文本换行和文本文件范围的检查实际通过，不修改冻结PDF/原件。发布观察首次从WSL查gh因该环境没有gh失败，读取实际Windows安装路径后显式调用已有gh.exe成功，未安装或改变认证。状态helper在首次发布后改为保留已观察的R19源提交/CI，同时把后续未发布修改另记；不再在每次actor观察时清空真实发布记录。

完整初审1449项revision哈希检查实际通过，随后Windows Git首次索引审查者复现副本因嵌套路径超过默认长度而失败。该次后续commit没有成果，push只报Everything up-to-date，不算新发布；父工具输出已直接观察，记录于此。下一动作使用Git原生core.longpaths=true的单次命令，不搬动/缩短或修改被冻结的审查路径，也不改变原判定。后续依赖命令逐项执行，避免前步失败被最后成功退出码遮蔽。

状态登记补充：executor-progress-checkpoint-command.json重复观察同一已创建actor，用了created状态标签；没有第二次spawn或新执行者。该helper当时覆盖了未冻结的首次created观察JSON，因此不可把其后来的observed_at当初次创建时间；首次实际命令回执executor-created-command.json保留。后续helper改为唯一观察文件名并使用running_observed，保留再次观察，不从状态标签推算创建次数或provider运行时间。

- L1复审终态入口更新首轮段落索引误选第二段，读回发现后从Git当前版本保留原第二段并正确更新第一段；尚未发布错误版本，历史锁未改。来源/协调文本编辑恢复单独记录，不计入L1作者修正或旧预算。

- 新接续发现publication.observe中synchronize重写checkpoint.next_action；现保存观察前next_action并恢复，保持实际L2前沿。记录L2资源恢复首轮错用native Python，import fcntl失败且未写状态；改为明确WSL命令成功，不属于论文作者修复或旧预算。

- L2方法冻结后发布的文本检查发现两个已冻结Python文件末尾额外空行（check_method_controls.py:52、independent_checker.py:87）；保留文件字节，不改历史锁。仅将EOF空行列为可选样式说明；继续检查行尾空格/缩进，独立算法与数学验收标准不变。

- L2质量接续提示只写QUALITY_FOLLOWUP.md文件名而未给全路径，原作者错查runs/R19/后报告不存在；root明确levels/L2/绝对路径，保留原失败，物流澄清不新增解法/评分。

- L2初审发布文本检查指出冻结paper-regeneration.diff.txt第1/3行的空文件标签差异头带尾空格（--- / +++）。这是实际差异工具原文，保留字节/锁；样式检查明确仅排除该证据文件，其他正文/源码行尾空白检查继续，科学验收未改变。

- 本轮CI接续首轮误把命令记录器定位于runs/R19/record_command.py，Python在启动前报文件不存在；实际工具位于scripts/record_command.py。未写执行回执、未修改锁或论文，明确正确路径后继续。协调者随后将日志写入的字面换行纠正；只读准备时误查L3/design/README.md，文件不存在，后续以文件清单定位。

- L2 v2冻结后交接核查首轮误给verify_handoff.py追加不支持的--root参数，参数解析即失败，未执行验证；回执l2-v2-handoff-command.json保留。随后在真实checkout使用该脚本支持的--json选项，另存新回执。不属于论文作者缺陷、不改旧预算。

- L2终态/L3方法准备发布时，Git普通路径通配符递归匹配，误将活动L3执行域中的JSON加入暂存；发布前独立清单检查发现。实际只撤回该域暂存，生产文件没有改写、没有提交或上传。随后改为逐个顶层文件路径并明确检查活动域/租约无暂存；错误属于协调者文件选择，不改作者计数或旧预算。

- L3成稿清单显示论文在execution根下，而root诊断关闭工具原先硬编码paper/子目录。前瞻调整收集工具允许显式传实际论文路径，仍必须位于本层冻结执行域且实际列入锁；默认保持L1/L2原路径。不为收集器强迫生产者改目录，不将文件存在视作独立论文验收。实际关闭命令会使用真实交付路径。

- L3发布编排中两次依赖操作过早派发：完整核查在refresh命令返回session而未收回终态时开始，push在commit返回session而未收回终态时开始。随后逐个收回原会话，refresh/完整10438文件检查/commit/push均实际exit0，远端身份另查，不重复副作用。已返回session不等于完成，后续必须先收回上游终态再派发依赖操作；本记录不推断此前具体进程完成先后，也不改任何科研失败/预算。

- L3原审查者以partial记录a6不可还原的历史缺口，root收集器旧枚举只允许pass/fail/blocked/unverified。前瞻增加对原生partial的保存，不强迫审查者改成pass或覆盖初判；partial仍计为非pass，latest_mandatory_pass仍只有全pass才true。关闭完整诊断与科学门通过继续分开。

- L4 reviewer初次物流提示误写runs/R19/raw-lock.json，实际文件为runs/R19/inputs/raw-lock.json。审查者真实报告不存在后root明确授权正确原锁路径，保留错误及恢复，不增加答案/评分或扩大其他层读域。这是协调者路径错误，不归入作者科学缺陷或旧预算。

- L3关闭/L4启动整合时，root先启动catalog刷新但工具返回尚在运行，随后运行publication观察；二者控制器实际各自持锁，后续收取刷新exit0并再次检查共享台账。此调度未遵守依赖前先收终态的协调纪律，保留观察，不用于证明并发安全。另只读CI文件定位误猜cloud-delivery.yml而文件不存在，随后rg文件清单定位实际validate.yml；未影响CI或源文件。

- L3终态暂存选择器首次把自身尚在运行的publication命令回执选入候选；写索引前assert拒绝，实际未暂存任何文件。原失败l3-close-safe-stage-command.json保留。对publication顶层同样先排除started回执，再另存恢复调用，不更改冻结生产/审查文件。

- L4冻结准备的source-readback.txt第77行是原DOCX空段落的实际转录“DOCX P22: ”，Git文本样式检查报尾空格。保留转录/锁原字节，只将此原件读回证据从样式检查排除；其余文档/程序继续检查。这不降低几何、论文或独立验收门槛。

- 源dc621f9的CI 37736189267实际失败：本地完整身份检查读到了未提交的L3/review/recheck-final-1-lock.json，但暂存选择器只遍历L3顶层及final目录，遗漏嵌套review中的锁本身，远端fresh checkout因此缺文件。Windows作业success、Python3.10身份检查fail、3.12矩阵作业cancelled，不能称全CI通过。冻结锁字节未改；补齐该原锁并给选择器增加全部revision索引/文件的Git跟踪覆盖检查，另次提交和CI验证；原失败/日志保留，不重跑论文或改其科学判定。

- 新覆盖检查首轮使用Git普通行式ls-files，中文路径被转义成带引号文本，产生旧R16中文PDF未跟踪的假警报；锁/文件实际未变。失败回执保留，改用Git原生NUL分隔-z读取确切UTF-8文件名，避免按显示文本判身份。
