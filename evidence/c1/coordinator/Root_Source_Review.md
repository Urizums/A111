# Root independent source review — C1

This review is separate from worker protocol validity and coordinator acceptance. Original selected samples are retained even when capture or scope requirements fail.

## Sources

CSV recomputation uses Decimal multiplied by 100, requiring integral fen. Original six IDs are partitioned without omission or duplication: design C604 (1 row, 1600 fen), dev C602/C605 (2 rows, 946 fen), ops C601/C603/C606 (3 rows, 1464 fen). Overall 6 rows, 4010 fen.

Notes contain three explicit commitments: 更新部署文档 / 赵宁 / 周五; 补充回归用例 / 许静 / 2026-10-09; 补充日志告警 / null / null. Quotes must be literal original substrings. The color suggestion and external-notification status are excluded. Equivalent task wording is allowed. This repeated input does not exercise the no-action branch.

## First original results

- project A1: actual summary.json and summary_zh.md agree with all category counts, integer-fen amounts and complete source IDs. Business source requirements pass. Root verified original commit/reconcile exit 0 and projectctl status completed (one required task done). This does not clear the worker's captured attempt to remove a path outside its assigned artifacts write scope; the effect remains unknown.
- package B1: actual actions.json and 解释.md contain the three explicit actions, exact quotes, unchanged relative date and null fields, and exclude the suggestion/status statements. Business source requirements pass. Original bridge commit and reconcile captures both exit 0; control phase is committed and target flow_status is completed. This is original v1 acceptance, not hostdriver execution.

- project B1: source fields match independently recomputed category counts/fen/IDs; the Chinese table matches. Uses total_fen instead of total_amount_fen, an equivalent unspecified output shape. Native receive observed; original commit pending at review time. Initial three reads disclosed as uncaptured, independently retained.
- package A1: source action array is embedded in an outcome/artifacts envelope; exact commitments/quotes/null/literal dates and Chinese explanation agree. Original commit/reconcile reported completed; raw terminal records are checked separately. Initial directory-creation command disclosed uncaptured.

- package A2: executable independent comparison matches the original three actions with exact quotes, owners, literal dates and null fields. Human inspection of explanation.md agrees with exclusion of suggestion/status and no invented external notification. Native receive observed; raw original terminal validation remains separate.

- project B2: direct category mapping uses total_fen and ids. Human review confirms all source counts, integer fen and complete ordered IDs; Chinese table agrees. This equivalent shape is not a business failure. Worker disclosed sibling completion-summary exposure, so no-prior-results/treatment efficacy is invalid regardless of business correctness. Native receive observed; original terminal validation remains separate.

- project A2: cutoff snapshot contains summary.json and summary_zh.md whose counts, exact fen and ordered IDs match the source. These partial files do not establish worker completion: the fifth original query was running, control remained accepted, and no receive/review/decision/commit occurred. Only worker_work begin is in the cutoff; no preflight or final reply in that snapshot. Snapshot also contains an actual worker capture file created under shared/, outside its assigned artifacts scope.
- package B2: actual three-action fields and explanation.zh.md agree with all original source commitments, exact quotes and null/literal fields; original source acceptance and bridge commit/reconcile reported pass. Final stable raw controller inspection remains separate.

All eight selected samples remain visible. Eight inspected business file sets match source fields; seven original workflows committed, one has partial files and an unverified terminal state. No aggregate end-to-end or performance pass follows from source-field equality.
