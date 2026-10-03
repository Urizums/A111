# Independent offline C1 audit

Audit scope: A01–A05 and frozen C01–C10, using only the preserved C1 sources and this worker directory. This report records evidence and gaps; a complete audit does not mean the historical requirements all passed.

## Findings

| Check | Grade | Finding |
|---|---|---|
| C01 | partial | Original package/notes and common expense source/plan hashes are bound across the samples; all eight spawn prompts contain task rules but no completed business values. The source lock points to c238b00 with source_modified_by_export=false. The permitted cutoff does not provide a per-run comparison of canonical T1 file hashes against that commit, so the complete frozen requirement is not proven. |
| C02 | pass | 8 distinct raw spawn-return files pair with eight spawn-argument records; all recorded arguments use gpt-6-luna, max reasoning, fork_turns none. No sample has a second creation return. |
| C03 | partial | Treatment A/manual and B/hostdraft are recorded for all eight samples and seven retain a draft plus final reply. Project/A2 was stopped at cutoff while still running; it has business artifacts but no worker reply/final scaffold, receive, review, decision, or commit. |
| C04 | partial | Seven completed samples have captured payload_valid check-reply before the same-boot worker_reply end and a final completion observation. Project/A2 has only five running status returns at cutoff; no worker_reply end, receive, review, decision, commit, or final completion was observed. Four package paths preserve receive/review/preflight/commit as separate records. |
| C05 | pass | All four independently parsed project summaries equal the six-row Decimal/fen recomputation and preserve all IDs. All four package action lists equal the independently frozen three-action result; exact note quotes, literal 周五, 2026-10-09, null owner/date, advice exclusion and status exclusion match. Original package v1 quotes/commitments rows are pass. The no-action branch was not run and is explicitly outside this repeated input. |
| C06 | partial | All eight samples were checked; valid and invalid spans are listed without imputing missing durations. Several setup/decision/receive/worker stages are cross-boot, duplicated, or missing, and the source records disclose uncaptured setup/read commands. Captured CLI records retain argv, exit, stdout/stderr and timestamps, but a complete actual-command denominator is unavailable. |
| C07 | pass | Rejected first versions and failed review/analysis records remain in the frozen snapshot; the incomplete Project/A2 sample remains included. B2 worker had zero local business/reply correction attempts. Three separate coordinator analysis/correction cycles are evidenced; two rejected bridge operations are also retained and reported separately. No replacement spawn or experiment rerun was made. |
| C08 | partial | This audit independently froze package expectations before viewing outputs, checked the manifest, source clauses, all eight marker/receipt sets and actual package chains, and recomputed all business values. Prior per-sample review prose and old index conclusions embedded in raw coordinator CLI stdout were encountered later; aggregate old summaries were not opened. Index-generated artifacts were not independently opened under the audit scope, so index artifact completeness and full blindness are not asserted. |
| C09 | partial | Descriptive A/B median/range/n counts are computed from valid same-boot stage spans for project and package pairs. Several stage counts are below two because of missing/cross-boot/duplicate markers; all spans include measured wall elapsed between observer markers, not model-active time. No stable speed or causal generalization is supported by these four pairs. |
| C10 | unknown | The C1 plan says no target UI or provider SDK was exercised, which is consistent with the allowed offline scope. TODO identity/history, browser blockers, and prior SDK/global/network/external-effect status are outside the permitted source set and remain unknown. |

The snapshot manifest check found **375/375** files matching recorded SHA-256 and byte sizes, with 0 missing and 0 mismatched. The manifest itself describes a non-atomic snapshot and does not certify that the workers had stopped.

## A01 — Package receive, review, preflight and commit chains

Each chain below links the original native receive receipt, frozen v1 review, separate controller decision preflight, final decision, commit and reconcile. `controller_compatible` is protocol preflight only; semantic acceptance is shown separately from `review/results.json` and the package assessment.

| Sample | Receive | Source review / assessment | Decision preflight | Commit and reconcile |
|---|---|---|---|---|
| package/B1 | received via `evidence/c1/package/B1/native/status-call-04-return.json` | ['pass', 'pass'] / pass | controller_compatible (semantic grading not evaluated here) | committed / committed |
| package/A1 | received via `evidence/c1/package/A1/native/status-call-03-return.json` | ['pass', 'pass'] / pass | controller_compatible (semantic grading not evaluated here) | committed / committed |
| package/A2 | received via `evidence/c1/package/A2/native/status-call-04-return.json` | ['pass', 'pass'] / pass | controller_compatible (semantic grading not evaluated here) | committed / committed |
| package/B2 | received via `evidence/c1/package/B2/native/status-query-04-return.json` | ['pass', 'pass'] / pass | controller_compatible (semantic grading not evaluated here) | committed / committed |

Source citations and SHA-256 values are in `audit.json` under `A01_package_chains`. Every package control record ends in `committed`; the chain checks also confirm the decision request/reply hashes bind to the same control and final worker reply. Package/B1 preserves its first failed assessment and corrected final assessment.

## A02 — Independent package output recomputation

Before opening any package output, I derived the expected list from `materials/notes.txt` and `materials/package.json` and saved it in `analysis/expected_package_actions.json`. The expected actions are:

```json
[
  {
    "task": "更新部署文档",
    "owner": "赵宁",
    "due": "周五",
    "source_quote": "赵宁负责更新部署文档，截止周五。"
  },
  {
    "task": "补充回归用例",
    "owner": "许静",
    "due": "2026-10-09",
    "source_quote": "许静负责补充回归用例，截止2026-10-09。"
  },
  {
    "task": "补充日志告警",
    "owner": null,
    "due": null,
    "source_quote": "决定补充日志告警。"
  }
]
```

The exact quotes are required substrings of the source notes. The relative deadline `周五` remains literal; the unstated owner and date for the explicit log-alert decision are null. “建议以后考虑更换配色。” is advice, and “本周没有新增外部通知。” is a status statement, so neither is an action.

| Sample | Business file shape | Independent list match | Reply match |
|---|---|---|---|
| package/B1 | direct_array | True | True |
| package/A1 | flow_envelope_nested_artifacts | True | True |
| package/A2 | direct_array | True | True |
| package/B2 | direct_array | True | True |

A1 stores the same action array under a Flow response envelope; unwrapping that envelope yields an exact match. All four worker replies and artifact references are present. Hashes and paths appear in `audit.json` under `A02_package_outputs`.

## A03 — Package/B2 corrections against the frozen two-correction limit

The B2 worker has **0/2** local business/reply correction attempts in the retained worker records: its single action output passed a source semantic check, its incomplete draft and final reply are both preserved, and `check-reply` returned `payload_valid`.

The coordinator made **3/2** distinct index/analysis correction cycles, exceeding the limit by one:

1. First capture-index parser failed on pretty-printed JSONL content; parsing logic was corrected. Evidence: `evidence/c1/package/B2/logs/018-worker-capture-index-draft.json` (exit 1).
2. Initial index audit produced empty worker-check and assessment extractions for all package samples because the argv matching failed. Evidence: `evidence/c1/package/B2/logs/029-index-audit.json` (exit 0).
3. Initial final index audit assertion failed on B1 assessment ordering; assertion was corrected to accept any passing v1 assessment. Evidence: `evidence/c1/package/B2/logs/034-audit-final-index.json` (exit 1).

Two additional rejected B2 bridge operations are recorded separately: `logs/007-bridge-observe-01.json` and `logs/008-bridge-accepted-01.json`; a corrected acceptance uses the raw spawn return in `logs/009-bridge-accepted-spawn-return.json`. If the denominator counts these operational failures too, B2 has at least **5/2** coordinator correction/error attempts. The job control field `repair_attempts: 0` does not count these local index/analysis repairs.

Each raw path, hash and captured output excerpt is in `audit.json` under `A03_B2_corrections`. The first failures remain preserved; I did not rerun or repair the original experiment.

## A04 — Eight-sample marker, boot, wait and raw-return audit

| Sample | Markers / boots | Invalid main stage spans | Status returns | Wait marker pairs / raw wait returns | Cutoff observation |
|---|---:|---|---:|---:|---|
| project/A1 | 20 / 2 | setup:invalid | 4 | 3 / 0 | completed observed |
| project/B1 | 18 / 1 | none | 4 | 2 / 0 | completed observed |
| project/B2 | 20 / 1 | none | 5 | 3 / 3 | completed observed |
| project/A2 | 12 / 1 | receive:invalid, worker_work:invalid | 5 | 4 / 4 | running/unknown |
| package/B1 | 21 / 2 | setup:invalid | 5 | 4 / 4 | completed observed |
| package/A1 | 20 / 1 | none | 3 | 3 / 2 | completed observed |
| package/A2 | 21 / 1 | decision:invalid | 4 | 4 / 3 | completed observed |
| package/B2 | 21 / 1 | setup:invalid | 4 | 3 / 3 | completed observed |

Marker events are listed in `audit.json` by boot and monotonic order, with each original marker path and hash. Monotonic timestamps are compared only within one boot. Project/A1 and package/B1 setup spans cross boots; package/A2 lacks a decision begin; package/B2 has duplicate setup ends; Project/A2 has an unclosed receive and worker-work span and no reply/review/decision/commit markers. Its fifth status return is still running; the non-atomic manifest provides no sixth query or terminal observation.

Most wait records do not preserve exact requested timeout arguments. Only package/A1 wait 3 and package/A2 wait 4 expose `requested_timeout_ms: 45000` in observation records, not raw wait-return objects. Project/A1 and Project/B1 have wait marker pairs but no direct wait-return files; package/A1 wait 3 and package/A2 wait 4 likewise have observations instead of exact return records. Elapsed wait-marker spans include orchestration overhead; they do not establish native timeout arguments. Unknown values remain null.

Raw status-return counts are Project A1=4, B1=4, B2=5, A2=5; Package B1=5, A1=3, A2=4, B2=4. All are at or below the frozen five-query limit. Per-file return hashes, arguments exposed by the snapshot, and final observed statuses are in `audit.json` under `A04_eight_sample_protocol_audit`.

## A05 — Frozen C01–C10 grades

| ID | Grade | Evidence and gap summary |
|---|---|---|
| C01 | partial | Original package/notes and common expense source/plan hashes are bound across the samples; all eight spawn prompts contain task rules but no completed business values. The source lock points to c238b00 with source_modified_by_export=false. The permitted cutoff does not provide a per-run comparison of canonical T1 file hashes against that commit, so the complete frozen requirement is not proven. Gap/unknown: Per-run baseline code hashes at T1 cannot be compared from this C1 snapshot alone. |
| C02 | pass | 8 distinct raw spawn-return files pair with eight spawn-argument records; all recorded arguments use gpt-6-luna, max reasoning, fork_turns none. No sample has a second creation return. Gap/unknown: Provider-internal identity is unavailable and is not inferred from native task names. |
| C03 | partial | Treatment A/manual and B/hostdraft are recorded for all eight samples and seven retain a draft plus final reply. Project/A2 was stopped at cutoff while still running; it has business artifacts but no worker reply/final scaffold, receive, review, decision, or commit. Gap/unknown: The full paired acceptance path is absent for project/A2 at cutoff. |
| C04 | partial | Seven completed samples have captured payload_valid check-reply before the same-boot worker_reply end and a final completion observation. Project/A2 has only five running status returns at cutoff; no worker_reply end, receive, review, decision, commit, or final completion was observed. Four package paths preserve receive/review/preflight/commit as separate records. Gap/unknown: Project/A2 remains running/unknown, with no sixth status query or terminal record in the frozen snapshot. |
| C05 | pass | All four independently parsed project summaries equal the six-row Decimal/fen recomputation and preserve all IDs. All four package action lists equal the independently frozen three-action result; exact note quotes, literal 周五, 2026-10-09, null owner/date, advice exclusion and status exclusion match. Original package v1 quotes/commitments rows are pass. The no-action branch was not run and is explicitly outside this repeated input. Gap/unknown: Project/A2 protocol completion is separate from its matching saved business outputs. |
| C06 | partial | All eight samples were checked; valid and invalid spans are listed without imputing missing durations. Several setup/decision/receive/worker stages are cross-boot, duplicated, or missing, and the source records disclose uncaptured setup/read commands. Captured CLI records retain argv, exit, stdout/stderr and timestamps, but a complete actual-command denominator is unavailable. Gap/unknown: Exact subprocess capture completeness cannot be established for commands disclosed as uncaptured.; Cross-boot elapsed values are null. |
| C07 | pass | Rejected first versions and failed review/analysis records remain in the frozen snapshot; the incomplete Project/A2 sample remains included. B2 worker had zero local business/reply correction attempts. Three separate coordinator analysis/correction cycles are evidenced; two rejected bridge operations are also retained and reported separately. No replacement spawn or experiment rerun was made. Gap/unknown: Some uncaptured command attempts are known only from retained source-review/progress records. |
| C08 | partial | This audit independently froze package expectations before viewing outputs, checked the manifest, source clauses, all eight marker/receipt sets and actual package chains, and recomputed all business values. Prior per-sample review prose and old index conclusions embedded in raw coordinator CLI stdout were encountered later; aggregate old summaries were not opened. Index-generated artifacts were not independently opened under the audit scope, so index artifact completeness and full blindness are not asserted. Gap/unknown: Independent byte-for-byte verification of the historical generated index/aggregate files is not made. |
| C09 | partial | Descriptive A/B median/range/n counts are computed from valid same-boot stage spans for project and package pairs. Several stage counts are below two because of missing/cross-boot/duplicate markers; all spans include measured wall elapsed between observer markers, not model-active time. No stable speed or causal generalization is supported by these four pairs. Gap/unknown: Token counts, cost, provider-internal identity and actual model-active time are null. |
| C10 | unknown | The C1 plan says no target UI or provider SDK was exercised, which is consistent with the allowed offline scope. TODO identity/history, browser blockers, and prior SDK/global/network/external-effect status are outside the permitted source set and remain unknown. Gap/unknown: TODO/history identity and prior blocker records were not read.; No browser, SDK, network, or external-effect evaluation was performed. |

The machine-readable table preserves the exact requirement text, finding, source paths, and missing/unknown fields in `audit.json` under `A05_frozen_C01_C10`. No additional requirement is graded.

## C09 descriptive stage spans

Values are same-boot observer wall spans in seconds. They include tool work, waits and gaps between observer markers, and are not model-active duration. `n` is the number of valid sample spans used; missing values are omitted, never zero-filled.

| Block / stage | A: n / median / range | B: n / median / range |
|---|---:|---:|
| project / setup | 1 / 56.219 / 56.219–56.219 | 2 / 64.737 / 45.999–83.475 |
| project / receive | 1 / 305.197 / 305.197–305.197 | 2 / 284.466 / 189.538–379.395 |
| project / review | 1 / 340.333 / 340.333–340.333 | 2 / 209.157 / 194.646–223.668 |
| project / decision | 1 / 45.748 / 45.748–45.748 | 2 / 87.945 / 33.598–142.292 |
| project / commit | 1 / 28.244 / 28.244–28.244 | 2 / 31.451 / 26.201–36.701 |
| project / worker_work | 1 / 171.123 / 171.123–171.123 | 2 / 108.859 / 90.035–127.684 |
| project / worker_reply | 1 / 52.708 / 52.708–52.708 | 2 / 45.610 / 37.647–53.572 |
| package / setup | 2 / 42.556 / 38.337–46.775 | 0 / null / null |
| package / receive | 2 / 298.243 / 291.246–305.240 | 2 / 363.182 / 349.367–376.997 |
| package / review | 2 / 237.795 / 139.197–336.393 | 2 / 311.545 / 270.591–352.499 |
| package / decision | 1 / 40.576 / 40.576–40.576 | 2 / 38.109 / 33.705–42.514 |
| package / commit | 2 / 15.474 / 2.245–28.703 | 2 / 16.687 / 15.528–17.846 |
| package / worker_work | 2 / 54.502 / 22.164–86.840 | 2 / 87.884 / 57.387–118.380 |
| package / worker_reply | 2 / 97.820 / 55.861–139.780 | 2 / 104.077 / 72.723–135.430 |

The effective sample size is at most two per arm and smaller for incomplete/cross-boot spans. Tokens, cost, provider-internal identity and active model duration are unknown. These records do not support a stable general speed claim.

## Independence, limitations and advice

The package expected actions were frozen before any package output was examined. The source comparisons use the original notes and rules; the project expectation comes from a separate Decimal/integer-fen recomputation. After those expectations were saved, original per-sample source-review and decision records were inspected to trace the review chain. Those documents contain historical judgments and were treated as evidence, not as the independent answer key.

Some raw B2 coordinator CLI stdout contains earlier block-index/summary-derived conclusions (`029-index-audit.json`, `034-audit-final-index.json`) and earlier script inspection (`030-inspect-index-script.json`). I did not open the old aggregate index/summary files and did not execute their historical builder or controller. These exposures limit claims of blindness and are listed in `audit.json`.

The snapshot manifest matches all 375 listed file hashes and sizes but is explicitly non-atomic, with `worker_stopped=false`. Therefore Project/A2 remains running/unknown; its saved summary values match the independent calculation but no protocol completion is inferred.

Advice, separate from grades: do not infer a runtime or speed improvement from C1. If driver-initialization work is still desired, freeze it as a separate implementation and evaluate it in a new, independently specified study. C10 history/TODO and browser or SDK/network/external-effect status remain unknown because they are outside the permitted C1 audit inputs.

## Audit artifacts

- `audit.json`: complete machine-readable A01–A05 evidence, citations, hashes, marker ledger, correction counts, C01–C10 grades and descriptive statistics.
- `analysis/`: independent derivation scripts and saved expected package/project data, source extraction, comparisons, and actual command/output records.
- This report is `report.md` in the assigned worker output directory.

