# R24 交付检查器开发回执

本节记录实际**本地**开发和测试，不表示已完成 C13/C14 真实 Agent 对照，也不表示 GitHub CI 已验证此单独脚本。

在 2026-10-10 本地 Python 环境执行 `python casebench.py selftest`，八个断言全部通过：简单提取合法；附加文档为警告；错误提取被拒；双方法交付合法；只交选中方法被拒；错误数量被拒；错误推荐被拒；冻结案例不得覆盖。 `python -m py_compile casebench.py` 完成且未报告错误。该检查器没有外部依赖。

未做的事情：没有用两个真实独立的 Agent 上下文分别使用 C13/C14-lean 执行这些案例；没有对成本/效率或长期领域泛化作出观察；没有验证实际宿主级 oracle 隔离。测试文件放在 runs/R24/evaluation/，不会成为 portable Skill 运行依赖。
另执行 `python skillcheck.py --selftest` 与 `python -m py_compile skillcheck.py`，5 项全部通过：最小合法入口、断链、缺失元信息、非法 UTF-8、引用越界。GitHub 回读的 `skillcheck.py` blob SHA 与本地测试文件一致：`71b111758a03338ca1c523aaafe550fc653c7ecf`。这不构成作者以外的独立验收，也未在仓库现有 GitHub CI 工作流中新增对此脚本的自动运行步骤。

## 第二轮评测器真实执行（本地）

修订 `casebench.py` 后使用本地 Python 执行 `python -m py_compile`、`selftest`、全新 `two_methods` 用例生成与两个模拟提交验收。13/13 自测通过，完整提交的 `passed=true` 且 `source_identity_checked=true`；只含 alpha 行的提交为 `passed=false`，缺少四条 beta 方法行。题目 seed=987230。脚本的 `git hash-object` 与 GitHub blob 一致，为 `f8bd05ca83e25f69b42100bdac08939768d052d8`。

新增负例覆盖：生成后原始输入字节被改、任务说明字节被改、JSON 重复键、CSV 多出的无名列；原样恢复后正确答案可以通过。旧八项及新五项均通过。**这只是本地 grader 验证，未调用真实 Agent/独立验收者；没有声称候选 Skill 优于 C13。**
