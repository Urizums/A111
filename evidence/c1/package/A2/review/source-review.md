# A2 independent source review

The unchanged `materials/package.json` declares the `forge-package/1` schema and two required v1 acceptance criteria: `quotes` (machine) requires each `source_quote` to be an exact substring of the supplied notes; `commitments` (human) requires only explicit action items and null for unstated owners or due dates. The source package and notes hashes match the frozen values recorded in `package/A2/work.json`.

The three included items are supported by the notes:

| Task | Owner | Due | Exact source quote |
|---|---|---|---|
| 更新部署文档 | 赵宁 | 周五 | `赵宁负责更新部署文档，截止周五。` |
| 补充回归用例 | 许静 | 2026-10-09 | `许静负责补充回归用例，截止2026-10-09。` |
| 补充日志告警 | null | null | `决定补充日志告警。` |

The color change is phrased as a suggestion and the external-notice sentence reports status; neither states an action commitment, so neither is included. The relative due date `周五` remains literal, and the third item has no stated owner or date, so both fields remain null. Every quote is an exact substring. The separate Chinese explanation describes the included actions and the exclusions. The worker reply binds the original invocation and its `actions` result to the two artifact paths and their hashes. A2's business file is a direct JSON array of actions, matching the package's artifact type. The independent checker in `check_package_output.py` confirmed the source hashes, artifact structure, all three rows, exact quotes, and both v1 criteria; its captured output is `source-checker.json`.

`packagectl assess` records both required criteria as passed, with the evidence references in `results.json`. This is a new input. No claim is made that the separate frozen no-action case was run or assessed.

Process and evidence qualifications: the worker reported that some initial inspection and capture-help queries were not recorded; the available evidence does not establish whether it successfully read the installed Forge SKILL, so that is unverified. Two code-mode attempts to encode the reply-authoring source failed before a subprocess was launched; the successful authoring source and its capture are retained. The coordinator's `logs/018-read-worker-final-materials.json` is a captured failed read because it assumed `artifacts/captures/check-reply.json`; the actual final worker check-reply capture is `artifacts/check-reply.capture.json` and reports `payload_valid`. The decision end marker was captured, but its begin marker was missed; its span is unverified and no begin time has been reconstructed. The manual decision passed read-only controller preflight, the original commit completed, reconciliation found valid completed evidence, and `packagectl next` returned completed. These preserved process deviations do not change the source acceptance finding.
