# Evaluate the factory and the generated flow separately

For the factory, ask whether a new unseen task produces a coherent, executable
flow and correct capability requirements. For the generated flow, ask whether
executing it actually solves its target task. Static JSON checks answer neither
question fully. Keep both evaluations in the delivery record.

For new factory runs, use the complete-plan protocol in evaluation-plan.md.
Freeze through factoryctl before build, carry the exact full plan and hash,
and use version 2 case-by-case assessment. A prose summary is not a substitute
for the frozen plan. The old v1 assessment remains supported for old packages.

## Before construction

Translate each must-have into an observable assertion. Define input, expected
behavior, forbidden behavior, grader and evidence artifact. Include representative
success and at least one relevant edge/failure case. Avoid broad tests that add
cost without addressing risk. Freeze the case IDs and assertions before repair.
If a test is wrong, record an explicit contract correction and rerun impacted
comparisons; never quietly revise the score denominator.

Use deterministic graders for exact extraction, math, schema, source-span checks,
permissions, budgets and code behavior. Use rubric-based model judging for
subjective quality and disclose dependence. Use human judgment where the user's
preference defines success. Inspect resulting artifacts, not merely the agent's
claim that it succeeded.

Keep actual grader code/command/results for machine checks. A kind label or
submitted pass statement does not establish an executed or independent grader.
For source review, inspect each finding's requirement, origin, basis and current
counterevidence; retain optional design advice without turning it into a frozen
required failure. Before final delivery, reconcile summaries with current raw
receipts and preserve corrections beside superseded evidence.

## Evidence labels

| Label | Required evidence |
| --- | --- |
| designed | A concrete flow and declared acceptance criteria exist. |
| structurally_validated | Checker output for the exact flow hash exists. |
| fixture_exercised | Prewritten responses traversed actual routing/contract logic. |
| live_exercised | A real model/host executed the task; preserve input, outputs and trace. |

These labels describe a dimension of evidence, not a universal readiness ladder.
Record case count, repetition count, model/runtime if known, measured usage and
unknown metrics. One successful run does not estimate a reliable pass rate.
Fixture outputs must be identified as fixtures. Hashes prove identity only when
paired with trustworthy source artifacts; they do not prove factual correctness.

## Comparing versions

Use `assets/benchmark-cases.json` for a shared test menu. Give both factories the
same raw task, source data, capability inventory, budget and grading rules. Use
blind labels for subjective judging. Run the generated flows as well as inspect
their designs. Recommend three repetitions per live case when cost permits;
report raw pass counts and cost/latency distributions instead of completion
percentages. Keep untouched holdouts to check generalization.

Hard gates: critical requirements, evidence honesty, authorized actions and
bounded termination. Among candidates that pass, compare task success first,
then actual tool/coordination errors, recovery, latency, cost and complexity.
Do not let polish or weighted scores hide a critical failure. Do not assume that
a more elaborate topology wins, or that one model's own scores are independent.

## Bounded repair

Record failed assertion, evidence, defect class, minimal change and regression
cases. Repair at most twice by default. Recheck related previously passing
cases. If budget or access prevents more work, return the artifact and unresolved
assertions explicitly. Do not disguise a partial result as a passing one.

Research reference: [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
describes code, model and human graders, artifact-focused evaluation and the
distinction between capability and regression tests. Consulted 2026-09-23.
