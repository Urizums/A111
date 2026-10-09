# Adapt Forge to applied mathematical modeling

Read when creating/running a mathematical modeling workflow. Preserve the task's
actual mathematical/empirical goal; competition names are context, not model
selectors or a secret scoring rubric. Real contest edition, track, official rules,
AI boundary, corrections and submission requirements must be checked from current
organizer material. Preparation exercises and actual submissions are different.
Do not infer the big-data track's dates/rules from the ordinary MathorCup contest
or apply last year's CUMCM AI rules without verifying the current version.

## From problem to researchable questions

For each subquestion define outcome, observable input/output, units, variables,
decision variables where relevant, hard/soft constraints, uncertainty, evaluation
criterion and dependencies. Read attachments and official amendments before
choosing methods. Distinguish predictive, descriptive, causal, optimization and
simulation tasks; their evaluation needs differ. Background search supports a
decision, not a list of models to paste into the paper.

Audit data source, types, units, time/spatial alignment, missingness, anomalies,
duplicates, availability at decision time and relevant relations. Preserve raw
data; document justified treatment. Label leakage can come from preprocessing,
feature availability, group/temporal splits or reusing a held-out set for selection.
Do not use information unavailable at the proposed decision time.

When an earlier evaluation result later feeds calibration, tuning or another
decision, treat it as an input at that new decision time. Check the exact
label revision and its arrival time, as well as the source prediction made
under its original information. For a joint residual or grouped statistic,
check when all required coordinates became available and how incomplete
groups are handled. A past target date or an earlier test-window name alone
does not establish availability. Make this rule explicit in the receiving
interface and test a relevant late-arrival or revision boundary.

Start with a feasible interpretable baseline. Consider another established or
improved approach only where the question and resources justify it. The user's
three-route request can warrant three candidates; it is not a universal quota.
Compare on the same admissible data, split, constraints, resources and relevant
criterion. Complex methods need demonstrated benefit or an explicit tradeoff.

| Task kind | Examples of relevant receiving checks |
| --- | --- |
| Forecast/prediction | Decision-time feature availability, chronological/group split where needed, baseline and held-out errors, residuals |
| Optimization | Units, feasibility, constraint slack, objective recomputation, small-instance oracle/bounds where attainable, infeasibility handling |
| Statistical/causal claims | Assumptions, estimand, uncertainty and confounding limits; association is not causal identification |
| Simulation | Mechanism validity, seeds/replications, conservation/boundary behavior, comparison with analytic or observed anchors |

## Useful dependency chain

Problem/attachment audit → justified mathematical abstraction → baseline →
candidate experiment(s) → source/numerical validation → supported interpretation →
figures and paper → cross-artifact receiving review. Research and data audit can
often run in parallel; solver work needs accepted variable/constraint interfaces;
paper writing must distinguish pending experiments from verified results.

Give each solver an input schema and units, assumptions, equations, parameter
provenance, output/result schema, experiment conditions and error checks. Give the
reviewer the original problem/data and real outputs, enough access to recompute
constraints/objectives and check leakage, not a desired ranking. Figures need
legible labels/units and data provenance; do not infer verification from aesthetics.

Use sensitivity, robustness, ablation or simulation when they test a material
assumption or claimed improvement. Do not request every experiment for every
question. Record why the chosen test addresses the uncertainty and what it cannot
establish. Innovation can be a supported abstraction, objective, constraint or
combination; novelty without evidence is not a bonus fact.

Freeze code/config/data/result identities for selected experiments. Produce an
executable reproduction path, not merely pseudocode or a statement that results
are reproducible. Check a clean rerun's numerical/semantic result as appropriate.
Trace equations, parameter values, tables and plot data through results to the
paper. Core conclusions cannot exceed the data, model assumptions or experiment.

## Design the evidence needed by the final paper

A request to complete mathematical modeling includes a usable scientific argument
even when the user does not spell out research, experiments or review. Derive
those duties from the actual problem and intended conclusions, not prompt length.
Build the reusable workflow so another executor can perform them without the
designer's private reasoning. Keep definitions, data availability, constraint
interpretations and unresolved decisions visible at each receiving interface.

Before solving, map each requested answer to a proposed claim, the computation or
experiment that could support it, a counterexample that would refute it, and the
paper section consuming the evidence. This map evolves with results; it is not a
prefabricated answer. Cover all original questions before optional sophistication.
For a multiobjective task state how alternatives are compared and tradeoffs shown;
do not quietly replace the original objectives with a convenient weighted sum.

After the first feasible result identify the material weakness that could change
the answer: an omitted constraint, loose bound, unsupported assumption, poor
baseline, unstable estimate or unexplained discrepancy. Choose a targeted next
experiment and its receiving check. If no improvement is supported, report the
tradeoff or limitation. A smoke pass permits continued work; it does not establish
that a first candidate or its paper is sufficient for final delivery.

Treat paper production as a consumer of checked evidence. A complete paper needs
a stand-alone account of the problem, necessary assumptions with consequences,
defined quantities/equations, reproducible methods, actual results answering every
question, validation, interpretation and limits. Its abstract should report the
supported findings; figures/tables should resolve a question, with units and
sources, rather than decorate a model-name narrative. Do not fabricate novelty,
citations, convergence, optimality or experiments. An unproved optimum remains a
feasible candidate with an appropriate bound or explicitly unknown gap.

Include a substantive receiving review before delivery: can a fresh reader
recover the original question, recompute critical results from raw inputs, find
the evidence for each conclusion and identify conditions where it fails? Separate
mathematical, evidential or meaning defects from optional style. Language that
obscures definitions, reasoning or conclusion scope belongs in substantive
review; do not defer it to later polishing. Repair the affected argument against
checked evidence before strengthening the narrative. The
workflow should support this review without outsourcing its judgment to author
self-checks or promising a competition outcome.

Check the format the reader will receive: critical numbers, units, formulas,
assumptions and claim strength must survive rendering, conversion and rewriting.
Correct source text does not establish a correct exported document. Explain for
the intended reader; keep execution provenance accessible without letting internal
run logs replace the scientific or practical argument.

## Interpret prompt detail honestly

User Levels1–8 add contest context/goals, problem decomposition, candidate comparison,
full execution, research, delegation and iterative criticism. They are input
conditions, not grades of guaranteed ability. A Level1 request still needs proper
problem understanding/checks; Level8 cannot create unavailable task/data or override
contest integrity. More roles/models/words can worsen coordination or leakage.

To compare levels, hold skill, problem/data, tools, resources and evaluation fixed;
use fresh contexts, preserve all outputs/failures and inspect the same externally
defined outcomes. Repeats and broader cases are needed for robust comparison.
Without them report descriptive single-case observations, not a causal level
ranking, award probability or complete competition performance guarantee.

Set a deadline-aware stopping policy: finish mandatory questions, checks and
paper consistency before adding optional sophistication. In real contests retain
human responsibility and the organizer's AI-use disclosures/limits; autonomous
practice does not authorize autonomous submission or replacing required human work.
