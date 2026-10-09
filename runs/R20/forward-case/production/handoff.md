# Actual production handoff

Task: `R20-C13-forward-calibration-production`; actor `/root/r20_c13_forward_maker`. Delivery type: build reusable workflow and execute the original synthetic batch-arrival calibration task in `forward-case/inputs/request.md` and `PROBLEM.md`. Read/write scope was the coordinator's narrow packet, not the surrounding R20 project. No outside answers, source generators, C12, old paper/global state, other actors or external evaluation gates were read. C13 and the original input locks passed identity checks.

## Current authority and consumers

- Entry: `README.md`; reusable pure-Markdown workflow: `calibration-flow/SKILL.md` plus its two references.
- Authoritative numerical/provenance payload: `results/results.json`; CSV interfaces: `results/{coordinates,days,vectors,selection-events}.csv`; scientific consumer: `results/说明.md`.
- Actual source: unchanged `../inputs/raw/`; source file hashes are in results and preflight. Selection details bind CSV row numbers including header and all exact retransmission source lines.
- Executable: `code/calibrate.py`, separate recomputation `code/author_check.py`; one-call helper `code/reproduce.ps1` and comparison `code/compare_rerun.py`.
- Evidence: actual `evidence/001` through `evidence/011` command records; checks and failure history below this directory. Exact inventory and hashes in final `manifest.json`.
- `clean-rerun/`, `script-reproduction/`, and `fixtures/` are reproduction/challenge records, not substitutes for authoritative results. Their independent-looking paths do not imply independent authorship.

## Policy and requirements mapping

Label policy is latest source version known at each decision origin, inclusive time boundary; this choice was allowed by PROBLEM and declared before computation. Forecast origin is fixed: a forecast source arriving afterward is never an original prediction, even if later known at the new origin. All selected physical quantities must be finite and units consistent. Same-key revisions substitute coordinates; identical retransmission deduplicates while retaining source references. Full day requires exactly the coordinate set in series.csv. Partial days remain in audit and never enter vectors. Evaluation label cutoff is retained as metadata and explicitly unused for selection.

| Original mandatory requirement | Actual artifact | Performed evidence |
| --- | --- | --- |
| Reusable handoff workflow | calibration-flow SKILL/references, brief/gates | Role/output/consumer/failure blueprint; standalone input/policy/formula/recovery/checks inspection |
| Every new origin complete day vectors | results/results.json, vectors.csv, days.csv | Source recomputation all origins; complete-set and maximum arrival tests |
| Selected forecast/label versions and source arrival | results JSON, coordinates.csv, selection-events.csv | Every selected source exact payload/line/hash; original forecast cutoff and new-origin label cutoff recomputed |
| Per-item residual and completeness/availability | coordinates.csv, days.csv, Chinese tables | Decimal source arithmetic on16 coordinates; 8 day statuses; partial-day exclusion |
| No retransmission/revision pseudo-samples | duplicate_events and origin vector set | Exact raw dedup and source-line checks; one date/coordinate per origin |
| Reproducible code | code + README + clean-rerun + script-reproduction | Different-cwd new-directory execution, 6 byte-identical outputs; shipped helper actual execution |
| Short Chinese scientific explanation | results/说明.md | 26 data rows checked against independent-of-producer source arithmetic, formula/policy/scope inspected |
| Real bounded smoke and relevant rejection | raw-to-results/check; retained two challenges | Exact-origin-time label and incomplete days exercised; parser rejects conflict and receiver rejects future revision |

The same author wrote and checked these outputs. Source recomputation is a stronger author check, not independent acceptance. This handoff supplies no replacement verdict for any old fixed-condition trial, full contest paper, model quality, universal Forge ability or controlled repeated comparison. It establishes only author-checked forward behavior for these unchanged inputs. Coordinator may freeze these bytes and arrange fresh independent review with original requirements and raw inputs; author diagnostics and expected answers should not be passed as an oracle.

## Failures, resources and terminal state

The first source-lock lookup used an incorrectly supplied in-version path; it failed read-only. Coordinator supplied the exact sibling C13-lock path and that same original was verified. The event and correction are retained, not replayed as an original scientific command. Two expected nonzero rejection tests are successful negative tests, not production defects; actual child exit status is retained despite the PowerShell wrapper's different tool exit presentation. There were no substantive correction runs or model iterations. Unknown model/tokens/cost remain null.

All executed processes returned terminally; no host call is pending and no actor/background service was started. The bounded production goal is author-complete. Next action is coordinator freeze/independent reception; producer stops writes after manifest finalization. No further model/page quota or automatic two-error stop was invented, and no meaningless successor stage is started.
