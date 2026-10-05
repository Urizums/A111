# R09：跨环境接续诊断

本阶段来源于 R08 当前 Windows checkout 的两项实际观察：原生 Python
导入 fcntl 失败，以及 Git 自动 CRLF 转换使冻结字节核对失败。
Ubuntu WSL 能执行原控制器；不据此宣称 Windows 原生控制器已移植。

| 任务 | 验收与边界 |
| --- | --- |
| R09-01 宿主与冻结字节预检 | 实作只读 CLI，报告原生执行条件与字节漂移；Windows/WSL 分别实际运行，不自动改文件、租约、预算或 provider。新候选最多两轮修正。 |
| R09-02 独立新 checkout 验证 | 另一个新上下文从实际 Git 提交创建新 checkout，核对预检诊断与相关 continuation/lease 行为；只报告实际宿主，不伪造 Windows 全功能支持。 |
| R09-next 启动下一阶段任务 | 从本阶段实际观察选有价值的新任务，先执行真实首步再归档。 |

R09/preflight/ 下早期命令属于 R08 的环境故障调查与后继准备。
R08 验收通过后另跑新的正式首步并通过 continuation start 绑定；
早期准备命令不单独满足 R08 的阶段转换门槛。
旧样本、失败、锁和已耗预算全部保留。定时器不启用，未知费用写 null。
