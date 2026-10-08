# R19 design-contract-audit TODO

唯一owner：/root/r19_design_contract_audit；唯一写域：runs/R19/design-contract-audit/。仅向root交付；禁止接触层执行/审查/diagnostic-result或发送结论给其参与者。

| task_id | 依赖 | 验收 | 状态 | 实际证据 / 下一动作 |
| --- | --- | --- | --- | --- |
| DCA-01 | root授权 | 读协作约束，锁定只读/写域及非运行判定边界 | done | AGENTS协作部分及本report范围；没有读取共享恢复入口 |
| DCA-02 | DCA-01 | 实际核对指定7份锁与原材料关键事实 | done | lock-verification.json：46/46；PDF3页、DOCX全部段表、XLSX3表直接读取 |
| DCA-03 | DCA-02 | 四层源锚定矩阵，区分明示/待运行/真实局部缺口及对立解释 | done | report.md、comparison.json；D1为文本歧义，未推断运行结果 |
| DCA-04 | DCA-03 | 交付读回有效、锚点存在、manifest实际hash及终态诚实 | done | comparison.json有效；101个不同workflow行锚点及其他handoff锚点存在；7锁46/46；payload-manifest.json封存实际文件身份后停止写入 |
| DCA-NEXT 启动下一阶段任务 | DCA-04及root综合调度 | 不提前综合或启动其他层；本独立审查不获后续研发写域 | cancelled_in_this_scope | 后续计划与首项由root在四层完整诊断后决定；actual_start_evidence=null |

保留事件：DCA-ERR01初次C11锁位置不存在，改到真实candidate/C11-lock.json，7锁完整核对。DCA-OBS01四次批量输出截断，按相关范围复读；不把观察容量警告当源结论或求解失败。未进行求解/研究模型迭代，定位更正保留不清零。model/token/cost=null；本agent所有调用已返回、未启动后台进程。终态design_contract_audit_complete，整层/阶段判定保留给root。
