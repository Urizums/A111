# Choose a deliverable from a short request

Contents: Intake · Delivery choice · Flow contract · Design review · Boundaries.

## Intake and delivery choice

Accept a short goal. Do not ask the user to supply an architecture, flow graph,
agent roles, evaluation design, tool plumbing, or long requirements form. First
read the request and relevant project material, inspect current host capabilities,
then choose the delivery type from the requested outcome and execution boundary.
Use `software_system` for a working application or service, `agent_infrastructure`
for an executable agent runtime, `agent_flow` for a reusable flow package,
`scoped_change` for a focused existing-repository change, `scoped_task` for a
one-time result from supplied material, and `design_only` only
when requested or when a genuine capability, authority, or material blocker
prevents execution. Record the selected type and why. Keep a reasonable default
reversible and revisable; do not shrink an end-to-end system to a design because
some business detail is missing.

An existing flow package is an execution input, not an instruction to build a
new factory. Start from [task-entry.md](task-entry.md) when consuming it; create
or revise a flow only when the requested outcome needs that work. A simple
scoped task needs a relevant result check, not the strict factory's intake.

Continue through useful implementation and verification without stopping for
routine approval between internal checkpoints. Give concise progress and expose
material assumptions. For underspecified reversible business behavior, build a
local prototype with explicit defaults, a configurable policy surface, and all
uncertain consequential decisions routed to human review. Never infer real
authorization, access, business policy, external effects, or factual evidence.
For greenfield work, register the intended output directory and allowed
operations; do not require a source-to-binary relationship for an artifact that
does not yet exist. For an existing target, use the material gate where required.

Separate facts in the brief as:

- **explicit**: supplied by the user; quote the exact request as its basis;
- **derived**: needed to achieve the requested outcome; state the dependency;
- **default**: a reversible choice that keeps work moving; state and expose it.

When reviewing another artifact, bind each finding to a requirement and its
actual basis. Distinguish a demonstrated requirement failure from a derived
requirement or advisory improvement. A derived must-have needs a concrete
dependency on the requested outcome; preferences for stronger wording, visual
style or a new feature are not automatically defects. Cite counterevidence and
keep supported advice without silently adding it to frozen required criteria.
Record advisory findings outside the factory's must-have requirements list;
do not add an unsupported origin value to its strict schema.

Ask only when a missing fact changes a consequential decision with no safe
default, or a requested external action lacks authority. First finish useful
unblocked work. Localize a blocker to dependent tasks, keep independent tasks
moving, and do not ask the user to debug ordinary design or schema errors.

## Design decisions by path

Use only the decisions relevant to the deliverable. A focused repository fix
does not need a full architecture review, every design dimension, or a user
interface. For `software_system` and `agent_infrastructure`, follow the project
TODO and acceptance methods in [project-execution.md](project-execution.md) and
[evaluation-plan.md](evaluation-plan.md). Record relevant scope, inputs, outputs,
quality, tools and authority, failures, state, stop conditions, and model/runtime
topology in the project brief as needed.

For architecture and system scope, use [system-architecture.md](system-architecture.md)
to connect the applicable runtime, domain, and frontend boundaries to quality
scenarios. For UI scope, use [experience-handoff.md](experience-handoff.md) to
resolve journeys and visual hierarchy together. Carry important decisions into
the same task and acceptance plan; do not create a separate untracked design
phase or ask the user to author the architecture.

The nine-field `contract.decisions` structure below belongs to the existing
strict factory's `agent_flow` path. Complete it when that factory schema requires
it; do not apply it as a universal intake template. Do not spawn agents merely
to fill decision fields.

For flow mode, resolve these nine areas. A short concrete decision is enough;
do not add agents merely to fill this list.

| Key | Decide |
| --- | --- |
| scope | Intended user outcome, included work, exclusions and definition of done. |
| inputs | Sources, required fields, missing/invalid input, freshness and trust. |
| outputs | Deliverable fields, usable format, uncertainty and supporting evidence. |
| quality | Domain-specific correctness criteria and how they will be checked. |
| tools_and_authority | Actual tools, permissions, external effects and unavailable capabilities. |
| failures | Empty/contradictory evidence, tool or model failure, fallback and escalation. |
| state_and_handoffs | What each step reads/writes, immutable context, checkpoints and merge ownership. |
| budget_and_stop | Work bound, retries, termination and honest unknown costs. |
| model_and_topology | Smallest justified graph, model needs and the reason for each split. |

Apply relevant domain methods rather than generic role names. For a research
report, define source selection, claim-to-source evidence, conflict handling and
unknowns. For extraction, define eligible facts, missing values, duplicates and
source spans. For a tool action, define authorization, preconditions, result
verification and recovery before enabling effects. These are thinking aids,
not universal task requirements or permissions.

Use patterns.md to choose a graph. A node prompt must state its actual objective,
permitted inputs, working method, output contract, evidence needs and failure
response. "You are an expert, do a good job" is not a working method. Pass only
needed artifacts between steps. Specify concrete reconciliation when merging
outputs; do not assume different agents agree or supply independent evidence.

## Contracts checked by the factory

Use `assets/example-design.json` with `assets/example-plan.json` and
`assets/example-package.json` as one consistent worked example. Replace its
domain content; do not copy its claims into unrelated tasks. This section
documents the strict factory's flow-mode contract; it is not the project TODO
schema for program mode.

Successful intake's `contract` requires these fields (extra context is allowed):

- `goal`: nonempty outcome text.
- `requirements`: nonempty must-have list. Each item has safe unique `id`,
  `text`, `origin` (`explicit`, `derived`, `default`), `basis` and `criteria`.
  `criteria` is a nonempty list of proposed acceptance IDs. For explicit items,
  `basis` is an exact substring of the original request; for others it explains
  why the requirement belongs. Do not mark a composite requirement explicit merely
  because one clause or a broad goal occurs in the request: split added design
  choices into derived/default items. Keep one authoritative requirements list here.
- `decisions`: exactly the nine keys in the table. Each value has nonempty
  `choice`, `reason`, and `origin` (`explicit`, `derived`, `default`, or
  `not_applicable`). Explicit decisions also require `basis`, an exact quote
  from the original request. Explain inapplicability; it is not a blank exemption.
- `blocking_questions`: an empty array for success. A real blocker uses the
  blocked outcome with the blocker in the response `evidence` array and no
  emitted artifacts.
  Save any partial design separately as working material, not as a successful
  contract in the checkpoint; resume with a new run after the blocker is resolved.

At eval_design, every requirement's acceptance IDs must exist in the full plan
and be required criteria. Include at least two required cases: a representative
success and a relevant challenge such as absent data or contradictory evidence.
The code checks counts and references; the designer checks whether these cases
actually test the stated behavior. Freeze the complete plan as usual.

Successful `architecture` retains the existing lite/full decisions and also has:

- `coverage`: exactly one row per requirement, with `requirement_id`, nonempty
  `node_ids`, and `criteria` equal to that requirement's criterion IDs. At build,
  these must name actual nodes in the generated flow.
- `stress_cases`: at least two different required frozen `case_id` values, each
  with concrete `risk` and `handling`. Explain the candidate's behavior on that
  input, not merely "test passes".
- `review`: `mode` is `self_review` or `fresh_context`, `summary` records the
  design critique and resolutions, and `unresolved` is empty for success.

The wrapper checks these at intake, plan freeze, architecture, repair and build.
It also binds the original request, contract and architecture to recorded stage
hashes. Rejection means fix the indicated omission internally; it is not a reason
to ask the user to write the missing field. Do not bypass checks via flowctl.
Existing package/1 and package/2 execution remains unchanged. Old factory
checkpoints use a different meta-flow hash and need a new run for this protocol.

## Design review before build

Actively try to break the design against the raw request: find a missing must-have,
an unsupported assumption, lost context, conflicting output, dead-end branch,
unbounded retry, wrong model/tool binding, or a "success" without usable evidence.
Check requirement coverage and the actual node prompts, not just the table.
Resolve findings before the successful architecture handoff, without changing
the frozen criteria. Record residual uncertainty honestly at delivery.

Where host rules permit and the user authorized delegation, use a fresh reviewer
for consequential or ambiguous architecture. Give that reviewer the raw task and
candidate, not your conclusion that it is good. Keep routine separable execution
with the user's preferred smaller model; give architecture integration to the
most capable available coordinator. Do not hard-code capability claims or invent
a stronger model. If only one context is available, conduct a distinct critique
pass and label it self_review. Never pretend that role switching is independence.

## Boundaries

These checks catch missing fields, inconsistent references and unfinished reviews.
They cannot judge whether a polished but shallow rationale is true, whether a
weak model overlooked a domain requirement, or whether the selected graph is
optimal. Use actual output evaluation and stronger review where available.
Do not promise perfect design, zero questions, or a proven improvement for all
weaker models. Keep the user's first interaction short and the internal work
explicit, reproducible and bounded.
