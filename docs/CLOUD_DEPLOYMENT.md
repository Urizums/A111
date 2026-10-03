# 云端部署与交付

本仓库提供 Python CLI 控制器、技能源码与研发证据，没有 Web 服务。
本次部署到用户连接的云环境 `/workspace/agent-forge-cloud`，要求 Python 3.10+，
运行时仅使用标准库。无需模型密钥即可使用本地控制器；真实 worker 由当前宿主的
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
`current`。已有相同发布被修改时拒绝复用；重装不修改先前发布。`venv/` 不安装
第三方包。CLI 命令有 verify、project、package、bridge、driver、draft、capture。
新业务 state 和输出应放到独立工作目录。仓库中的旧 state、绝对路径和 worker ID
是证据，不是可在新宿主上直接恢复的活任务。停止 CLI 即结束该进程，无常驻服务。

本次 C2 技能候选保存在 `runs/S02/candidate/forge-agent-flow/`，它保留完整技能结构，
加入采集协议及失败命令记录修复。原 `skills/` 和 `evidence/` 字节保持不变。
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

人工复核入口：`runs/cloud/VERIFICATION_REPORT.md`、`runs/cloud/issues.json`、
`runs/S01/final-review.md` 和 `runs/S03/validation.json`。这些入口区分真实原生调用、
本地 fixtures 和尚未验证的性能、SDK、全局资源、网络故障、UI 及外部业务效果。
