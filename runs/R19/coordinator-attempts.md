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

状态登记补充：executor-progress-checkpoint-command.json重复观察同一已创建actor，用了created状态标签；没有第二次spawn或新执行者。该helper当时覆盖了未冻结的首次created观察JSON，因此不可把其后来的observed_at当初次创建时间；首次实际命令回执executor-created-command.json保留。后续helper改为唯一观察文件名并使用running_observed，保留再次观察，不从状态标签推算创建次数或provider运行时间。
