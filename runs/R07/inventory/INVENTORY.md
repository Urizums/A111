# Agent Forge takeover inventory

This inventory is based on source commit `6f509c8` and the preserved R06 records. The project goal remains active; the R05/R06 handoff was delivered as an unfinished handoff, and strict acceptance did not pass. The reported plan to close upstream PR #1 and continue with its owner is requester context; remote PR state was not checked.

## Reusable capabilities already implemented

- **Continuation and evidence controls:** task/phase ledgers, coordinator lease, frozen-input tracking, handoff integrity and strict publication gate. Start with `START_HERE.md` and `AGENTS.md`; current R05 phase has no ready next task. Evidence: `scripts/continuation.py`, `scripts/verify_handoff.py`, `state/continuation.json`, `state/phase-todo.json`.
- **Snapshot and bounded execution:** C4 snapshots inputs and verifies/restores original bytes; C5 records local command executions and correction counts. These are cooperative local guards, not remote truth or provider-wide quotas. Evidence: `runs/R06/candidate/C5/forge-agent-flow/scripts/{snapshot.py,bounded_run.py}`, `runs/R06/snapshot/`, `runs/R06/budget/`.
- **Local provider-neutral workflows:** request/result, idempotency and cancellation protocol work, plus a real local HTTP/SQLite ticket journey and simultaneous edits (one success, one conflict, history retained). This does not establish live provider SDK behavior. Evidence: `runs/future/provider-adapter/`, `runs/R03/app/`, `runs/future/concurrent-ticket/`, `runs/R06/regression/http-310.json`.
- **Preset UI/catalog fixes:** narrow-screen navigation/focus, scrolling table labels, three catalog presets and stale confirmation callback handling were repaired and Root-retested. Independent acceptance remains blocked as described below. Evidence: `runs/future/preset_browser_acceptance/`, `runs/future/versioned_preset_catalog/`, `runs/R06/FEEDBACK_LOOPS.md`.
- **Local task-flow examples:** simple GeoJSON delivery and a complex approval example exercise idempotency, concurrency, process-crash rollback/recovery and a local post-review. No real approval/notification effect or autonomous native-agent delegation was proved. Evidence: `runs/R06/handoff/simple/`, `runs/R06/handoff/complex/`, `runs/R06/approval/`.
- **Portable CLI/package checks:** Python 3.10/3.12 source and extracted-archive installs, CLI smoke, and candidate regressions have preserved passing records. Reported totals: controller 368 each; C3/C5 376 each; auxiliary 47 each; install smoke 17 each; C5 snapshot 7 and bounded-run 8. Evidence: `runs/R06/final/source-py310/`, `runs/R06/final/source-py312/`, `runs/R06/final/archive-py310/`, `runs/R06/final/archive-py312/`, `runs/R06/final/summary.json`.

## Runnable local commands

These are the repository's documented/check-in commands, not newly executed by this inventory. The historical pass counts apply to R06 evidence; rerun the relevant checks after any source changes.

```sh
python3 scripts/verify_handoff.py --json
python3 scripts/continuation.py --root . next
python3 scripts/check_publication_gate.py --root .  # expected exit 2 while required gates remain blocked
python3 -m unittest discover -s skills/forge-agent-flow/scripts -p 'test_*.py'
python3 -m unittest discover -s runs/R01/candidate/forge-agent-flow/scripts -p 'test_*.py'
python3 -m unittest discover -s runs/R06/candidate/C5/forge-agent-flow/scripts -p 'test_*.py'
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The workflow in `.github/workflows/validate.yml` additionally records auxiliary, local HTTP journey, install/smoke, and package commands. They are not substitutes for browser/independent-worker or live-provider acceptance.

## Original unresolved IDs and budget state

`state/continuation.json` has **12 done / 8 blocked / 0 failed** task records. Historical failures remain in issue/evidence records and must not be normalized into passes. The eight blocked task IDs are:

| Task ID | Preserved state / blocker | Budget to retain |
|---|---|---|
| `BACKLOG-preset_browser_acceptance` | Root retest passed, but independent final acceptance and native terminal reconciliation are missing. | Coordinator 2/2; no reset or replacement validator. |
| `BACKLOG-versioned_preset_catalog` | Independent v2 reported 74 pass / 2 failed 390px focus samples; Root Tab cycles passed separately. | Continuation counter 1/2; independent harness 2/2 exhausted. Preserve both counters. |
| `CAP-sdk_adapter_contract` | Root's local protocol tests passed; independent validator made a third correction against its limit of two. | Local task counter 0/2; independent acceptance exceeded 2, so later pass cannot release it. |
| `BACKLOG-host_protocol_overhead_comparison` | Only 4/8 frozen samples ran; package setup stayed invalid and P2B marker order was wrong. | Root 2/2 exhausted; do not replace samples or restart. |
| `BACKLOG-real_agent_executor_integration` | No authorized provider endpoint, model, identity/credentials or independent SDK run. | 0/2; resume only after environment changes. |
| `BACKLOG-real_worker_failure_recovery_trials` | Local process crash was tested; provider cancel-terminal, natural network failure and isolated external-effect tests are absent. | 0/2; resume only with real observation contract and permitted sandbox. |
| `BACKLOG-bridge_budget_timeout_validation` | Host exposes no provider-global usage/admission/cancel-ack telemetry. | 0/2; local limits are not global enforcement. |
| `R06-scheduled_handoff` | Trigger/state observation exists; independent cold start and substantive successor step remain unverified; hourly automation was disabled. | 0/2; do not recreate the automation. |

Related blocked issue keys include `R05-adapter-validation-budget`, `R05-preset-independent`, `R05-protocol-study`, `R05-provider-runtime`, `R05-provider-global-and-recovery`, `R06-cold-start`, `R05-catalog-independent-focus`, and `R03-independent-UI-historical`. `R05-UI-focus`, `R05-catalog-confirm`, and the listed R06 snapshot/budget/staging/root-review/result-protocol/state-validator defects are recorded as fixed/retested, but those fixes do not clear separate blocked acceptance branches. R06 handoff/root and release-integration budgets are each 2/2; see `runs/R06/final/repair-budget-audit.json` and `runs/R06/handoff/root-repair-budget.json`.

## Environment gaps versus local validation issues

- **Missing host/provider environment:** no configured independent provider endpoint/model/identity/credential; no provider-global resource/admission/cancel-terminal telemetry; no authorized external-effect recovery sandbox; independent cold-start execution is unverified. These are capability/evidence gaps, not proof of a local implementation defect. Evidence: `runs/R06/environment-final.json`, `runs/R04/capability-probe/probe.json`, `runs/R06/scheduling/`.
- **Local code or validation defects/limits:** the overhead study has invalid package setup, incomplete samples and a marker-order error; independent catalog focus sampling has two failed samples after its correction budget; the adapter independent run exceeded its repair budget; UI independent acceptance/reconciliation is unresolved. Keep the Root retests and independent outcomes distinct. Evidence: `runs/future/host_protocol_overhead_comparison/report.json`, `runs/future/versioned_preset_catalog/independent/retest-v2/browser-results.json`, `runs/future/provider-adapter/independent/budget-clarification.json`, `runs/future/preset_browser_acceptance/root-final-review.json`.

## Evidence entry points and next useful work

Read `runs/R06/upstream-handoff/README.md`, `runs/R06/VERIFICATION_REPORT.md`, `runs/R06/issues.json`, `runs/R06/FEEDBACK_LOOPS.md`, `runs/R06/final/summary.json`, `runs/R06/final/repair-budget-audit.json`, `runs/R06/upstream-handoff/strict-acceptance.json`, `state/continuation.json`, and `state/checkpoint.json`. The strict gate is intentionally still red; handoff delivery is not full acceptance.

The original queue has no ready task and `R05-next` is blocked by its dependencies. First take a read-only local baseline (lease probe, handoff integrity, `continuation.py next`, strict gate), then let Root define and freeze a fresh R07 scope from unmet product needs. Do not spend any blocked task's remaining budget, change its samples/validator, operate historical workers/timers, or treat absent host capabilities as local test failures. Keep new work under its assigned R07 path and leave original records intact.
