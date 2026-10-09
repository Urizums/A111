# C13 forward-case acceptor preparation

Status: PREPARATION BLOCKED — specified frozen case packet is absent at the authorized path.

## Scope inspected

- `AGENTS.md`
- `runs/R20/final/candidate/C13-lock.json`
- `runs/R20/final/candidate/C13/forge-agent-flow/SKILL.md`
- `runs/R20/final/candidate/C13/forge-agent-flow/references/evaluation.md`
- `runs/R20/final/candidate/C13/forge-agent-flow/references/source-evaluation.md`
- `scripts/record_command.py`

The C13 lock identifies the source revision and hashes, but covers the forge skill and its references only. The C13 candidate directory contains `forge-agent-flow/`; it has no `forward-case/` directory at inspection time.

## Required packet not found

The following requested inputs were unavailable at the specified location and were not inferred or recreated:

- `runs/R20/final/candidate/C13/forward-case/inputs/`
- `runs/R20/final/candidate/C13/forward-case/input-lock.json`
- `runs/R20/final/candidate/C13/forward-case/evaluation/ACCEPTANCE.md`
- `runs/R20/final/candidate/C13/forward-case/evaluation-lock.json`

Without the raw input and frozen acceptance source, there is no defensible mapping from case requirements to f1–f3 receiving assertions. No producer verdict or expected answer was used.

## Source-derived review contract, pending the packet

Once the frozen inputs and acceptance source are made available, the independent review will:

1. Bind each f1–f3 artifact and reported field to the original source definition before recomputation; preserve source conflicts.
2. Reconstruct original-source time/revision, predictions, vector completeness, and residual semantics from raw inputs and the actual artifacts/code.
3. Check numerical domains and relevant constraints; non-finite values cannot pass physical comparisons by default.
4. Independently rerun the actual delivered implementation and retain full command evidence through `scripts/record_command.py`.
5. Evaluate the consumer under either explicitly allowed visible-latest or fixed-evaluation-mature policy, without imposing an unpublished vector count.
6. Run a lawful consumer control and an invalid consumer control where their exact variants can be derived from the frozen source; record both outcomes.
7. Keep requested Luna/high as configuration only; report provider/model, tokens, and cost as unknown/null unless actual telemetry establishes them.
8. Return separate falsifiable first verdicts for f1, f2, and f3, with observed evidence and limits; do not infer broad paper, competition, or superiority claims.

## Terminal status

Preparation stopped at the missing frozen packet. No production files, other R20 material, prior diagnoses, or maker activity were inspected. No executable check was run. Awaiting the coordinator's terminal freeze and the actual frozen packet before substantive acceptance.
