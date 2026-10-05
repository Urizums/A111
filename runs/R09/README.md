# 宿主预检

从仓库根目录运行：

```powershell
python scripts/host_preflight.py --root . --lock state/source-lock.json --lock runs/R08/candidate/C7-lock.json
```

输出只读 JSON。退出码 0 表示冻结字节一致且当前运行时具备 continuation、
POSIX 分量打开和 Linux 计时器所需 API，可以继续探测租约；
退出码 2 表示字节漂移或运行条件不足，按 actions 的实际诊断处理。
这不是产品验收，也不会自动修改文件或启动 worker。

本机 Windows 原生 Python 的 fcntl、POSIX 打开 API 与 Linux boot marker
不可用，因此预期返回 2。已经实际探测的 Ubuntu-24.04 WSL 可运行：

```powershell
wsl -d Ubuntu-24.04 --cd /mnt/c/path/to/A111 -- python3 scripts/host_preflight.py --root .
```

使用当前实际 checkout 的 Linux 路径；示例路径须替换，不复用历史宿主路径。
重新核对未决调用和租约后再修改共享状态。若 Git 自动转换换行使锁失败，
先保留失败与本地改动；新 checkout 可使用
`git -c core.autocrlf=false clone --branch main https://github.com/Urizums/A111.git`。
不得更新历史锁来接受漂移。预检不证明 renameat2、崩溃耐久、provider 或 UI 行为。
