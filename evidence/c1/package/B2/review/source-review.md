# B2 independent source review

The unmodified `materials/package.json` declares `forge-package/1` with two required v1 acceptance criteria. `quotes` is machine-graded and requires each `source_quote` to be an exact substring of the supplied notes. `commitments` is human-graded and requires only explicit action items, with unstated owners and due dates left null. The package and notes byte hashes match their frozen values: `5804faa670d9ba7475234170c7226c047c424adce761893b4aa039937b77c6bc` and `2a6802a93f60d87cc1c66f9c0eeed402398dbe0e0ef8df000f4ae76c18bdafdf`.

Reading the raw notes supports these three actions:

| Task | Owner | Due | Exact source quote |
|---|---|---|---|
| 更新部署文档 | 赵宁 | 周五 | `赵宁负责更新部署文档，截止周五。` |
| 补充回归用例 | 许静 | 2026-10-09 | `许静负责补充回归用例，截止2026-10-09。` |
| 补充日志告警 | null | null | `决定补充日志告警。` |

The color change is only a suggestion, while the external-notice sentence is a status statement; neither is an explicit action commitment. `周五` is preserved literally, and the third action has no stated owner or due date. The worker's `actions.json` is a direct array with exactly the three rows above, and each quote is an exact substring. The Chinese explanation agrees with the values, distinguishes the suggestion and status statement, and does not infer a date. The worker reply binds the original invocation, result, evidence paths, and current hashes. Its required `hostdraft.py check-reply` capture is `artifacts/logs/check-reply.json`, actor `worker`, exit 0 with `payload_valid`.

The independent checker in `check_package_output.py` re-reads the raw package and notes, derives the expected action list, verifies exact quotes and reply bindings, and confirms both v1 criteria. Its captured result in `source-checker.json` is `pass`. `packagectl assess` records both required criteria as passed using the canonical package hash in `results.json`. This is a new input; no claim is made that the frozen no-action input was run or assessed.

Process evidence and limits: the worker reported reading the installed Forge SKILL. The retained `artifacts/process-captures.jsonl` is one pretty-printed `forge-comparison-cli/1` record (despite the filename), whose captured read included `Worker_Protocol.md`, the raw package and notes, and three public reference files; it does not show a read of `SKILL.md`, so that read remains reported but unverified. The worker's captured process records show successful writes, a successful B-mode `hostdraft.py reply`, a successful semantic-check subprocess, the final reply write, and a successful `check-reply`; no worker subprocess failure or artifact correction appears in those captures.

Coordinator recording deviations are retained separately: the first `setup` end marker was emitted after prepare but before issue; a second actual end was recorded after issue, so the stage has duplicate ends and no unambiguous single span. The first status snapshot was running. A premature `hostbridge observe` failed before the job was accepted; an `accepted` attempt with the `list_agents` snapshot failed because that was not the creation receipt. Root supplied the receipt distinction; the original spawn return was then passed to `accepted`, and the same first status snapshot was imported by `observe` successfully. The failures remain in the sample log. Later, one coordinator process-capture reader incorrectly parsed the worker's single JSON document as JSONL; that failed capture remains in `logs/018-worker-capture-index-draft.json`, and the corrected whole-document inspection is in `logs/021-summarize-worker-capture.json`.
