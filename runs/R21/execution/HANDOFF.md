# R21 首次科学交付交接

完成时间：2026-10-09T03:55:46.704045+00:00。状态是作者范围内首次交付完成，独立验收待不同接收者执行。未来真值未读取。

最终论文：`paper-final-v4/paper.md` 与 `paper-final-v4/paper.pdf`，13页、5图、14表，最新版全部页面实际显示检查。精确身份见 `result.json`。

主路线 shared_ridge10 由42个选择日的实际缺货+报废日均损失选择，选择后参数不回调。备用 weekly_mean56 为首次拟合前固定56日同店品同星期均值；两路线均保留4032行未来预测/区间和4032行整数备货。名义90%不是覆盖保证；未来情景损失不是实測表现。

|方法|选择损失 元/日|验证损失 元/日|验证覆盖 %|未来备货合计 件|
|---|---:|---:|---:|---:|
|shared_ridge10|665.01|631.81|88.99|64537|
|weekly_mean56|724.01|698.06|88.89|64590|

科学结果根目录 `science-v1/`：逐键 `future/<method_id>/predictions.csv`、`replenishment.csv`；历史逐键结果 `results/historical_predictions_plans.csv`；固定成熟历史标签 `data/evaluation_labels_fixed.csv`；各原点训练快照/特征/促销填补源在 `data/`；完整96维残差坐标和各原点接受/排除见 `uncertainty/residual_coordinates_all.csv`、`pool_membership_all_origins.csv`。最终每路线112个残差日，原预测训练信息不回写。

输入/设计/澄清身份从允许原件核对；未打开设计报告、其他R19/R20产物、接收标准、生成器、独立接收材料或未来真值。只用当前输入reference代码原字节副本的政策函数，未执行其旧main。当前 alpha10、169列、促销填补、0.3活动项、情景公式/等权/两项目标均保持固定。完整迁移差异见 source/v1/config.json。

## 实际命令与复现

从仓库根运行，所有输出使用新目录；命令记录目录唯一，已有输出拒绝。完整真实argv/cwd/UTC/monotonic/exit和原始stdout/stderr字节base64见 command-index.json 与 commands/*.json。

```powershell
py -3.12 -X utf8 -B scripts/record_command.py --out runs/R21/execution/commands/REPRO-UNIQUE.json -- py -3.12 -X utf8 -B runs/R21/execution/source/v1/run_science.py --raw runs/R21/inputs/raw --config runs/R21/execution/source/v1/config.json --newout runs/R21/execution/REPRO-NEW-DIR
```

重现纸稿以科学结果、inspection-v1、self-check-v1和prospective-freeze为输入：

```powershell
py -3.12 -X utf8 -B scripts/record_command.py --out runs/R21/execution/commands/PAPER-UNIQUE.json -- py -3.12 -X utf8 -B runs/R21/execution/source/build_paper_v4.py --science runs/R21/execution/science-v1 --inspection runs/R21/execution/inspection-v1 --selfcheck runs/R21/execution/self-check-v1/self-check.json --freeze runs/R21/execution/prospective-freeze.json --newout runs/R21/execution/PAPER-NEW-DIR
```

自检脚本 source/self_check_v1.py（显式raw/science/config/newout），文档检查 source/check_final_document_v1.py（execution/paper/newout），渲染 source/render_paper_v2.py（paper/newout）；对应真实调用均在记录中。复现需要原环境numpy/pandas/scipy/sklearn/matplotlib/reportlab/pypdf、Windows中文字体和Poppler；版本见science-v1/environment.json。

## 保留的失败、修复与限制

第一次误读锁的嵌套路径是工具恢复，未开算。科学首跑exit0，没有改配置或结果。论文首轮mathsf转置图式解析失败exit1，源码和部分输出原样在paper-v1；随后保存paper-v2，再修复附录目录保存paper-final，最后修复Markdown表格空行为连续GFM块保存paper-final-v4。所有旧版本与收据保留。010是预定已有输出拒绝负控制，exit1发生在fit与写入前。

作者科学33项重算检查通过，包括各原点选版、固定成熟标签、完整96残差、逐日版本可用性、原预测重算、基准精确重拟合、4032网格、分位公式、q可行性、两项损失及有限情景最优性。14个GFM表逐行与内容树一致，全部表格单元在PDF抽取中找到。PDF13页真实图像逐页查看，不以抽取替代视觉检查。作者自检不冒充独立验收。

- Future42-day truth unavailable and never read; no future measured coverage/loss/improvement claim.
- 90% empirical marginal level has no guaranteed future or joint coverage.
- Historical validation horizon1-14 only; horizon15-42 not directly validated.
- Activity and forecast-step effects confounded; five validation activity days, denser future weekly activity regime.
- Weather and settlement excluded; no weather causal estimate.
- IID day bootstrap descriptive only due temporal dependence.
- Optimization numerical optimality for fixed finite empirical scenarios, not unknown true distribution.
- Author self-check not independent acceptance; root will freeze terminal bytes then use different receiver.
- Local write scope is collaboration contract, not OS isolation; actual host model/tokens/cost unknown null.

下一动作：root冻结此次首次交付全部终端字节，再交给不同接收上下文验收。执行者到此停止；不查看未来真值、不按之后分数追调。
