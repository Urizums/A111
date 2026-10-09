# Author self-check for informed correction

State: author-side contract check only. The new version requires a new independent reception; this document is not a verdict.

| Requirement affected by j1 | Correction | Check performed |
| --- | --- | --- |
| Every compared method must produce future point/interval and replenishment tables | Stage 7 loops over frozen `requested_methods`; selection is only a recommendation | `WORKFLOW.md` explicitly requires 4,032 rows per method for both tables |
| Method outputs remain identifiable | Both required schemas include `method_id`; registry enumerates method identity, outputs, and status | Interface requires table method IDs to equal the frozen method set |
| Receiver can verify cardinality and key coverage | Defines independent expected set K = 42 dates × 12 stores × 8 source items = 4,032 keys per method | Self-check computes 42×12×8 and verifies the contract text covers both table key sets and their equality |
| Failure is not disguised as delivery | Failed/unverified methods remain registered, with no empty/fabricated rows; overall status remains incomplete | Interface specifies status, counts, evidence, recovery action, and overall incomplete branch |
| Current operational documents are usable without review history | Current workflow and receiving interface contain only current actions, contracts, failure states, and source requirements | Self-check asserts they contain no j1 label or prior-stage diagnosis; change basis remains in `READ-DOMAIN.md` and `CORRECTION-STATUS.json` |
| Original slice and untested scope are preserved | Correction status states the one-day consumer slice is unchanged; no production rerun occurred | No prior scientific artifacts or consumer outputs were opened or used |
| New work is transparent about prior feedback | Status labels this an informed correction to j1, not a new blind design | Correction basis cites the TASK line and allowed verdict finding |

This correction does not establish any model result, nominal coverage, solver performance, 42-day execution, paper quality, or independent acceptance.
