# ZCode 执行接入口：先真实接通，再自动派单

推荐分工：协调者负责目标、架构、skill、派单和整合；ZCode 执行编码、资料预处理和测试；
必要时才使用 Luna 独立核验。运行账号留在用户已有的 ZCode 环境。
任务输入、源码版本和验收经 GitHub 交接；本机执行、原回复和 diff 回传后再由协调者判定。
MCP 是 ZCode 调用其他工具的入口，配置 MCP 本身不表示外部协调者已经能驱动 ZCode。

## 第一条真实任务

`first-job.json` 固定一次只读项目检查，先确认真实执行与账号，再放开代码修改。
无需新建网站、对公网暴露端口或搭建调度平台。

在安装并配置 **ZCode CLI** 的电脑上，切到已同步的 A111 checkout：

```sh
git clone --branch rd/zcode-bridge-r08 https://github.com/Urizums/A111.git A111-zcode
cd A111-zcode
python integrations/zcode/dispatch.py check --repo .
python integrations/zcode/dispatch.py prepare --repo .
python integrations/zcode/dispatch.py run --repo . --out ../zcode-first-receipt
```

若 CLI 没在 PATH，可加 `--executable` 指定实际 CLI 可执行文件。
本轮只核实上游源码的参数接口，没有证明桌面登录能自动复用于独立 CLI；
先确认你 CLI 的账号和额度。不能把普通桌面主程序当成 CLI。
`check` 只探查命令和帮助，`prepare` 只生成 argv；都不会调用模型。
`run` 是一次真实调用，没有轮询或自动重试。使用独立干净 checkout，回执目录放在 checkout 外。
原回复放在 stdout.bin/stderr.bin，结果由协调者核对，CLI 退出码0不等于业务通过。
`plan` 与 prompt 是执行权限和任务要求，不是操作系统隔离；工作区 diff 检查也不能证明宿主外没有副作用。
超时只证明本地进程被截止，不能证明服务端或子进程全部终止。

## 如果只有桌面应用

可直接在 ZCode 打开已同步的 A111，把 `first-job.json` 的 prompt 交给它执行。
这一步是手动交接，不能宣称当前会话已经调用了你的桌面程序。
自动化再选官方 CLI；或在已建立的 Remote Control 会话中操作当前项目。
账号授权和临时远控入口不要放入公开仓库。

## 当前验证边界

本云端沙盒没有 ZCode CLI，也没有用户本机执行通道。
已经实际执行命令探测和派单预处理，真实账号调用仍 blocked，不能用本地模拟替代。
预期下一动作：在用户已有环境完成第一条只读调用，回传原回执，再接编码任务。
不预先声称节省额度的比例；后续比较同类任务的用量、耗时和人工修正次数。

官方来源（2026-10-05 检查）：

- CLI 与配置：https://github.com/zai-org/ZCode/blob/main/apps/zcode-cli/README.md
- 参数实现：https://github.com/zai-org/ZCode/blob/main/apps/zcode-cli/packages/cli/src/run.ts
- 账号和 Coding Plan：https://zcode.z.ai/en/docs/configuration
- Remote Control：https://zcode.z.ai/en/docs/remote-control
