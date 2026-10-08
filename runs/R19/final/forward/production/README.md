# 从原始输入重算

要求 Python 3.12（计算部分仅标准库）。在本目录运行：

```powershell
python solve.py --input ../inputs/raw.json --output solution.json
python verify.py --input ../inputs/raw.json --solution solution.json --output checks.json
python tests.py --input ../inputs/raw.json --solution solution.json --output test_results.json
python experiments.py --input ../inputs/raw.json --output experiments.json
```

孤立复制交付包后，改用 `--input raw.json`；此快照与原始 raw 字节一致。原始材料的 request/problem 可见 paper.md 完整叙述，但正式接收仍以原件为准。

paper.md 是可编辑中文论文源文。若要重建 PDF：`python render_paper.py --source paper.md --output paper.pdf`。PDF 生成须已有 reportlab 与交付包 assets 内 Noto Sans SC 常规字重字体（可用 `--font` 指定另一已有中文 TrueType 字体）；计算和 PDF 查看均不依赖安装新软件。PDF 视觉复核的已渲染 PNG 见 pdf_pages/。

workflow.md 给出工作流与下游接收接口；result.json 记录作者状态和未验证范围；manifest.json 的路径相对 A111 工作根。请勿把作者自检或命令 exit 0 当作独立验收。所有统计为实际运行，provider/model/token/cost 未知。


