# Reusable workflow: offline modeling workbench frontend

## Brief and contract
Input: versioned numeric source, units, constraints, objective, audience and runtime boundary. Output: editable scenario, computed results, truthful run state, chart/table and evidence handoff. Preserve raw values and state assumptions; fixture-backed demos must disclose their provenance and mock boundary.

| Step / trigger | Inputs and operation | Owner | Output / receiving check | Failure / stop |
|---|---|---|---|---|
| 1. Scope | Original request, raw data, platform; map mandatory journeys, constraints and unknowns | Coordinator | Frozen requirement-to-evidence checklist; verify units, source and write boundary | Ask only for consequential ambiguity; stop unsupported claims |
| 2. Design | User journey, states, layout and accessibility; define component/state interfaces | Designer (may be same person) | Input/result/status contract; implementer checks every required state has an owner | Resolve conflicts before implementation |
| 3. Implement | Accepted contract and fixture; build one vertical slice from input through result | Implementer | Runnable app; receiver checks computation uses displayed inputs and source constraints | Fix within original repair budget; preserve failures |
| 4. Runtime | Actual browser and served app; exercise valid action, invalid input, correction and keyboard path | Runtime checker | Values, statuses and recovery compared with independently computed oracle | Browser unavailable means runtime gate unverified; no DOM-only substitute |
| 5. Visual reception | Runtime screenshots at requested desktop/mobile sizes; inspect hierarchy, legibility, reachable controls and clipping | Visual receiver | Separate visual observations from functional assertions; map screenshot paths to requirements | Correct material defects within budget; stop at limit |
| 6. Deliver | App, workflow, runner, receipts, screenshots, result record | Coordinator | Reproduction command and requirement-to-evidence handoff; state mock and unknowns | Mark remaining gates unverified; never imply production or independent acceptance |

## Iteration and stop policy
Freeze expected assertions before implementation. After each check, retain command/output and distinguish observation from cause hypothesis. Correct only a demonstrated defect; count failed source, runner/orchestration and fallback attempts cumulatively. Default maximum is two correction rounds unless the case gives another limit. After limit exhaustion, stop edits and report actual failures. A single context can perform all roles but cannot claim independent acceptance.

## Runtime receiving checks
1. Load the app in a real target browser; record viewport and browser.
2. Change a primary input, activate by keyboard, compare displayed prediction/table/chart/status to a separately calculated oracle and recompute objective/constraints.
3. Enter negative and nonnumeric values separately; require visible rejection and no fresh success result. Correct the value and verify recovery.
4. Inspect desktop and 320–390 px renders; confirm controls remain reachable and no unintended horizontal clipping.
5. Keep functional, visual and accessibility observations distinct. A deterministic local fixture establishes behavior under that fixture only, never a live backend, complete accessibility audit, production acceptance or performance claim.
