# R22 知情 h6 复审计划

本次是首判 h6 fail 后的知情修正接收，不是新盲审，也不重做科学首交。唯一写域为 `runs/R22/review/recheck-v3/**`。

先读取 R22 v3 文档修正锁、原协议与 acceptance、初判 result 及其锁定重建证据，验证原科学首交身份未变。检查 v3 锁内的字节身份；受限文件只参与哈希校验，绝不读取语义。随后只读取允许的 `correction-v3/source/build_report_v3.py`、新正文、最终 PDF、图形及必要的 document-data-bindings 原件。

冻结本域的独立核验源码后，再依据 `rebuild-v5` 和原始成熟标签/已发布点值，从十进制 CSV 文本独立验证全部正文表格、摘要/图形派生金额、文中重复数字、单位与分组范围。将表格及派生值与全文正文逐处对照，不以初判已知差异作为唯一检查目标。

对新 PDF 用 Poppler 渲染实际页图，核对真实页数并逐页 `view_image`。文本抽取仅辅助检索，不能替代视觉检查。完成后输出独立 `result.json`、中文 `REVIEW.md`、数字核验 ledger 和逐页视觉证据记录；h1–h5 仅在首交身份核验通过后按原 result byte identity 带入，h6 给出本次实际 pass/fail。所有命令均通过 `py -3.12 -X utf8 -B scripts/record_command.py` 保存真实命令收据，非零命令保留并分类；不填补未知的模型/token/cost。
