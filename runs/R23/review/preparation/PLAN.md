# R23 independent receiver preparation plan

**State:** preparation complete; formal reception not started. Await the coordinator's frozen design identity, selected consumption slice, and separate authorization to begin reception.

## Purpose and independence

Use the frozen requirements in `runs/R23/acceptance.json` and original request in `runs/R23/brief/TASK.md`. Check the actual workflow and coordinator-selected slice from raw R21 inputs. Do not infer a pass from author self-checks, producer diagnostics, prose completion, or a command exit code. This document defines what to inspect and what evidence would reject a claim; it is not a verdict.

For formal reception, use a fresh receiving context supplied with the frozen design and actual slice, original request/criteria, and allowed original sources. Keep author diagnoses, intended answers, prior results/verdicts, and expected-answer keys out of that packet. If a genuinely fresh context is unavailable, record independence as unverified.

## Frozen source basis and units

The request specifies a decision at 2026-10-31 18:00 Asia/Shanghai for 2026-11-01 through 2026-12-12: 42 daily decisions, 12 stores, 8 items per store. The raw decision source states 1,600 units/day network capacity, 6,000 yuan/day procurement ceiling, no inventory carry, lost unmet demand, and a fictional two-day activity flag. Items define procurement cost, shortage and waste losses, and 55 units/item/day bounds. The two losses are objectives; procurement is a constraint. Calendar, promotion, weather and demand reports include dates or publication/availability timestamps.

Trace every proposed unit back to those sources. Distinguish an item/store/day decision from forecast/evaluation windows and update events. For each forecast or plan, identify origin time, target service dates, label revision and publication/availability cutoff, feature publication cutoff, and consumer. If evaluation uses a shorter horizon or partial activity coverage, state that scope and what remains untested. Do not equate it with end-to-end reliability over all 42 future days.

R21 reference material is a candidate business reference only. Compare its configuration and baseline assumptions against the raw source and fixed task; it cannot define the correct answer or validate itself.

## Executable reception sequence after freeze

1. **Bind the packet.** Record hashes/version identifiers for frozen criteria, task, raw-input lock, design and selected slice. Confirm the consumed files are the actual workflow and runnable slice. Missing/ambiguous items leave the associated claim unverified.
2. **Trace workflow interfaces (j1).** For each material claim and output, follow original source or justified derived need → workflow step/owner → input/output fields and units → receiving assertion → failure path. Check horizon, information-update timing, decision constraints/objectives, and evaluation units. Reject missing mandatory paths, unsupported units, unusable interfaces, or treating R21 reference configuration as accepted authority.
3. **Check evidence scope (j2).** For each evidence claim, record dates, units, conditions observed, what it supports, and what remains uncovered. Check decision-time feature/label availability, including revisions or late arrivals, and whether evaluation covers the stated horizon/activity. Reject leakage, a short/incomplete slice represented as full 42-day reliability, unqualified generalization, or an unacknowledged source-bound gap. A concrete gap with a feasible next check is acceptable; do not require universal experiment counts or a fixed number of windows.
4. **Execute the designated slice as consumer (j3).** Start from locked raw sources and the frozen interface; invoke the actual slice and inspect consumer-facing artifacts. Recompute the selected claim's relevant numerical/domain checks from original inputs. The named condition must occur in the run; inspect a meaningful source-relevant boundary/rejection path where false success could otherwise pass. Forecasting examples include time-available features/labels and an as-of boundary; planning examples include integer/nonnegative/item bounds and daily capacity/budget. Select checks implicated by the frozen slice and task. Preserve first failures and exact command/output. Do not retry an unchanged failure or call preparation execution. Static examples, helper-only commands, file-presence checks, and self-report are not run acceptance.
5. **Retain uncovered outcomes.** State which original requirements the slice did not execute or cannot establish. A successful bounded slice supports only observed conditions; it does not establish complete workflow delivery, future realized forecasting reliability, a full modeling paper, or causal skill improvement.
6. **Return separate j1–j4 verdicts.** For each criterion cite the source clause, actual artifact/observation, check, verdict and limitation, plus a concrete rejection condition. Separate mandatory failures from optional suggestions. Preserve conflicts and unknowns. Model, tokens, time and cost stay null unless authenticated telemetry supplies them.

## Criterion-specific reject conditions

- **j1:** Reject if a material requested outcome/source-defined unit or condition lacks a usable workflow path and receiving interface; if a decision/update/evaluation unit is mislabeled; or if R21 baseline/configuration is assumed valid without source-grounded checks.
- **j2:** Reject if evidence does not cover its stated claim, unpublished information is treated as known, or a shorter horizon/incomplete activity condition is described as full-delivery reliability. A source-bound gap is acceptable when its limit and feasible follow-up are explicit.
- **j3:** Reject as not received if the slice is only designed/described/self-reported, not run from permitted raw inputs, fails to activate its claimed condition, or lacks a receiving check of the produced interface/relevant boundary. If environment/material access blocks the run, mark it unverified.
- **j4:** Reject an independence claim if the receiver receives author diagnoses, intended answers, prior outcomes, or relies on the producer's pass report. Reject a mandatory claim only with source-bound contradictory/missing evidence. Add no model, page, window, retry, quality-award or universal experiment quota.

## Handoff and stop

At formal reception, write only within the assigned R23 reception area. Keep preparation, execution and verdict evidence distinct; preserve first failures and actual correction/retry history. End with criterion-by-criterion verdicts and explicit supported/excluded claims. Stop preparation now; wait until the coordinator freezes the design and names the consumer slice, then separately authorizes reception.