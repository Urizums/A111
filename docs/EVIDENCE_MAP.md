# 证据迁移与不可重放边界

| 原位置 | 当前仓库位置 | 使用方式 |
| --- | --- | --- |
| C1 coordinator/cutoff-snapshot/project | evidence/c1/project | 固定截止副本；不使用原 live project |
| C1 coordinator/cutoff-snapshot/shared | evidence/c1/shared | 与固定副本同批快照 |
| C1 原 package | evidence/c1/package | 原操作员已停的输出/记录；只读审计 |
| C1 materials、audit、coordinator 元数据/Q1 | evidence/c1/ 对应目录 | 保留原要求、分析和局部测试 |
| C1 截止 manifest | evidence/c1/Snapshot_Manifest.json | entries.relative_path 拼到 evidence/c1/ 校验 sha256/size |
| T1 / O3 / design / roles 选定报告 | evidence/history/… | 历史摘要/验证记录；未携带全部旧原始目录 |
| 原 canonical skill | skills/名称/… | state/source-lock.json 映射 tracked path 与 sha256 |
| 原持久 TODO v9 | state/history/project-todo-v9.json | 只读历史原件 |
| 本地 C1 草稿 + 本次交接 | state/project-todo.json | 保留历史，补充最新状态 |

原 JSON 中的绝对路径、哈希、worker ID 和 boot ID 均不替换。它们绑定历史原件；审计器根据映射读取当前文件，不因旧绝对路径在新机器不存在就判历史未发生。反过来，记录提到某路径也不证明其原文件已被携带；history/index.json 列明实际保留范围。

C1 的旧 analysis scripts 含原宿主路径，作为历史源码保留，不能直接假定可运行。新分析工具必须使用当前仓库相对路径并写 runs/，把新结果与旧结果分开。原请求/状态不作为当前执行配置导入。

快照非原子、原 worker 未被证实停止：逐文件稳定性和 cutoff 时间保留。这只定义审计的文件版本，不追认旧 A2 完成。不重跑八个样本、不进行第六次旧查询、不重发未知 spawn。

artifact-manifest.json 固定发布包的源码、文档与证据；state/、runs/、validation/ 是接续时可更新目录。修改不可变内容后需要产生新的发布 manifest，而不是用改哈希掩盖旧证据变化。验证器仍独立检查 source-lock 和 cutoff 原哈希。
