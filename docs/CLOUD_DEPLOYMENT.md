# 云端部署与交付

本仓库核心提供 Python CLI 控制器、技能源码与研发证据；本轮新增的工单挑战另有实际 HTTP/SQLite 应用。
本次部署到用户连接的云环境 `/workspace/agent-forge-cloud`，要求 Python 3.10+，
CLI 和工单服务运行时仅使用标准库；浏览器验收额外使用 Playwright / Chromium。无需模型密钥即可使用本地控制器；真实 worker 由当前宿主的
原生协作工具执行。安装目录和证据随托管环境的生命周期保留，不宣称永久托管。

## 安装、运行、验证

从 Git checkout（包含已暂存的新文件）或已解压的交付包执行：

```bash
python3 scripts/deploy_cloud.py --prefix /workspace/agent-forge-cloud
/workspace/agent-forge-cloud/bin/agent-forge --help
/workspace/agent-forge-cloud/bin/agent-forge verify --json
/workspace/agent-forge-cloud/bin/agent-forge project --help
python3 scripts/smoke_cloud.py --prefix /workspace/agent-forge-cloud --out /tmp/forge-smoke-new
```

安装器复制到按全部交付文件内容寻址的 `releases/<sha256>`，验证后原子切换
`current`。已有发布须匹配完整文件/目录集合及每个文件的长度和 SHA-256；额外文件、空目录、缺失、改写和符号链接均拒绝复用，拒绝前不切换现有安装。Git 和 manifest 来源均拒绝不规范路径及父目录链接，读取时逐层 O_NOFOLLOW。POSIX `venv/` 用解释器链接兼容独立 Python 发行版，不安装
第三方包。CLI 命令有 verify、continue、project、package、bridge、driver、draft、capture。
`agent-forge continue --root /workspace/A111 next` 读取当前就绪任务；始终把可写的 checkout 传给 continue，勿将安装发布目录用作运行状态目录。CLI 使用 `-B` 防止生成 pycache 污染发布。
新业务 state 和输出应放到独立工作目录。仓库中的旧 state、绝对路径和 worker ID
是证据，不是可在新宿主上直接恢复的活任务。停止 CLI 即结束该进程，无常驻服务。

当前 C3 候选保存在 `runs/R01/candidate/forge-agent-flow/`，加入持续研发与效果验证规范及接续控制器；历史 C2 保留在 `runs/S02/candidate/forge-agent-flow/`。原 `skills/` 和 `evidence/` 字节保持不变。
宿主应阅读候选 SKILL.md 才能应用新协议；CLI 不会自动注册个人技能或调度模型。

## 打包与搬迁

```bash
python3 scripts/package_delivery.py --out /tmp/agent-forge-delivery.tar.gz
(cd /tmp && sha256sum -c agent-forge-delivery.tar.gz.sha256)
mkdir /tmp/agent-forge-extracted
tar -xzf /tmp/agent-forge-delivery.tar.gz -C /tmp/agent-forge-extracted
python3 /tmp/agent-forge-extracted/agent-forge/scripts/deploy_cloud.py --prefix /tmp/forge-installed
```

打包器只收录 Git 跟踪的源文件和报告，或已解压包 manifest 指定且哈希一致的文件；
排除未跟踪凭据、缓存及 Git 对象。包内有完整 `delivery-manifest.json`。
创建归档拒绝覆盖同名旧文件。CI 在 Python 3.10/3.12 上验证，并上传源码及报告归档。

工单示例可用 `python3 challenges/ticket-desk/app.py --database /tmp/support-desk.sqlite3 --port 8765` 启动，再访问 `http://127.0.0.1:8765`。默认绑定 loopback，数据库放在发布目录之外；没有生产认证或公网 SLA。

本轮复核入口：`runs/R00/VERIFICATION_REPORT.md`、`runs/R00/issues.json`、`state/continuation.json`。

历史复核入口：`runs/cloud/VERIFICATION_REPORT.md`、`runs/cloud/issues.json`、
`runs/S01/final-review.md` 和 `runs/S03/validation.json`。这些入口区分真实原生调用、
本地 fixtures 和尚未验证的性能、SDK、全局资源、网络故障、UI 及外部业务效果。
