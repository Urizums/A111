# 四层论文与独立诊断入口

以下链接指向各层最后实际交付版本。四层均使用冻结C11和同一官方春季修订D题；最后版本包含原作者收到首审反馈后的知情修订，不是各层第一次生成结果。首次失败、资源和预算仍在对应诊断及首审中。

| 层级 | 最后中文论文 | 独立诊断 | 当前判断 |
| --- | --- | --- | --- |
| L1 | [PDF](../levels/L1/execution-v2/paper/paper.pdf) · [可读源文](../levels/L1/execution-v2/paper/paper.md) | [诊断](../levels/L1/diagnostic-result.json) · [知情复审](../levels/L1/review/recheck-1/report.md) | 六门pass、六维在报告限定范围achieved；首审来源类别绕过失败保留 |
| L2 | [PDF](../levels/L2/execution-v2/paper/paper.pdf) · [可读源文](../levels/L2/execution-v2/paper/paper.md) | [诊断](../levels/L2/diagnostic-result.json) · [知情复审](../levels/L2/review/recheck-1/report.md) | 六门pass、六维有限实例/预算范围achieved；首次实证partial、低预算不稳定观察保留 |
| L3 | [PDF](../levels/L3/execution-v2/paper.pdf) · [可读源文](../levels/L3/execution-v2/paper.md) | [诊断](../levels/L3/diagnostic-result.json) · [知情复审](../levels/L3/review/recheck-final-1/report.md) | a1–a5 pass、a6 partial；完整中文与PDF科学语义修复成立，历史原流/PID和并发缺口仍保留 |
| L4 | [PDF](../levels/L4/execution-v2/paper/paper.pdf) · [可读源文](../levels/L4/execution-v2/paper/paper.md) | [诊断](../levels/L4/diagnostic-result.json) · [知情复审](../levels/L4/review/recheck-1/report.md) | 六门pass、六维明示范围achieved；首次NaN误放行和旧缺失物证保留 |

诊断中的achieved针对已检查的原问、数学依据、实验、复现追溯、科学论证和工作流交接，不是官方评分。不同解法口径、搜索努力与知情修订使本单题不能用于层级因果排名。完整论文不等于原几何全局最优、通用高质量或十月大数据表现。

语言检查包含读者能否恢复问题和定义、理解选模理由与实验、追溯结果并读懂适用条件，以及最终PDF是否保留数字、单位、公式和结论强度。它已是本轮实质交付；后续文风润色不能改变科学含义或补造证据。各报告分别明确本轮新求解、旧身份复用与未重演的范围。

四层来源绑定比较见[comparison.json](comparison.json)，源头分析及C12前瞻范围见[SYNTHESIS.md](SYNTHESIS.md)。C12新题[独立首判](forward/review/report.md)已终态，b1–b5在本材料范围内通过；其[8页论文](forward/production/paper.pdf)是新的受影响行为小切片，不能充作四层结果。
