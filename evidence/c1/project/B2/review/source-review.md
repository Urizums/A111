# B2 独立 source review

审查者从 materials/expenses.csv 原始行独立分组，并用 Decimal × 100 推导整数分；未使用其他样本或协调者预期答案。

原始 CSV SHA-256：f1a6914eae07b97537e809c9e9fa5000acd02b391ca64484927596a19c2b3bfb。独立 checker：review/check_expenses.py（SHA-256 b22915e08e7187c6992c729fa1fccd33f323f563b75252b0e9894d2d17f2f059）；checker 输出：review/source-check-output.json（SHA-256 a5403ef0d70560fbfac89b5e1a65e4da8e60ef10408e8c5f325cbea91b5c2bb1）。业务和回复文件 SHA-256：summary.json 373f70e1ba7cb5cc74bd33a51592ac109050cde29ec9c4c07c870edc540dbca3；summary_zh.md 85ac768fb707096c04a8565d59f76ae5ac48e513a661b42068b29a037514eb77；worker-reply.json 399ccadb968a68b90a122f47eb1f79188454c57cc5bbf98b190501c294c38634。

## 源数据重新计算

| 类别 | 行数 | 合计（分） | 来源 ID |
| --- | ---: | ---: | --- |
| design | 1 | 1600 | C604 |
| dev | 2 | 946 | C602, C605 |
| ops | 3 | 1464 | C601, C603, C606 |

独立检查项：{"all_ids_and_row_counts_match": true, "captured_check_reply_payload_valid": true, "category_keys_sorted": true, "json_exactly_matches_raw_csv": true, "markdown_chinese_explanation_present": true, "markdown_rows_match_raw_csv": true, "reply_artifact_hashes_match": true, "reply_binds_to_actual_request": true, "reply_result_matches_json": true}。九项均通过：JSON 与原始 CSV 精确一致、分类排序、每类数量与全部 ID、中文表格及 Decimal 说明、reply request 绑定、reply 结果和 JSON 一致、回复引用工件 hash，以及 worker 在 reply 阶段结束前的 captured check-reply。

worker 的 artifacts/logs/check-reply.json 返回 exit 0 / payload_valid；其结束 monotonic_ns 为 2687160561119，worker_reply end 为 2692576040048，同 boot，顺序符合要求。

## 协议与记录缺口

B2 worker 在其最终披露中说明：在原始 CSV 读取前，它调用了 list_agents，返回内容显示 sibling completion summaries（包括类别值），因此不满足“不读 prior results”。该 probe 的精确 argv 和原始返回未保存，无法重建；不推断其实际暴露值或具体调用时刻。worker 另披露初始 capture.py help probes 和 /dev/null bootstrap 尝试未被 cli capture 保存。首条通知明确 /dev/null 已存在且 capture.py 拒绝；对应精确命令、输出与副作用未知。工作者随后自行从 immutable request 找到允许目录 project/B2/artifacts，并报告 request/source 读入已捕获、worker_work markers 已记录。未发送 follow-up/interrupt，也未重发/替换 worker。

native status 查询共 5 次：Q1–Q4 的快照为 running，Q5 为 completed；3 次 notification wait（45 秒上限）依次 timeout、completed、timeout。原 bridge receive 使用 Q5 的真实 completed snapshot 成功。只创建一次实际 worker。worker capture 文件为 artifacts/worker_capture_luna_forge_6e153853d17f.jsonl，schema forge-comparison-cli/1，actor luna_forge_6e153853d17f；各 capture 是单 JSON 对象记录。worker markers 保存在 artifacts/observations/，schema forge-comparison-marker/1，actor alias。协调者的原始 native return 及等待返回保存在 native/，其中若干快照/通知由直接文件写工具落盘，详见 block native/write indexes。

业务正确性为 pass；由于 worker 自报 prior-result exposure 且若干初始化/侦查命令无原始捕获，B2 protocol conformance 不成立，C1 efficacy comparison 应判 invalid；样本保留，不替换。