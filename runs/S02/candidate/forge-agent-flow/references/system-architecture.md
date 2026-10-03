# System architecture and frontend engineering

Contents: Scope · Quality scenarios · Layer contracts · Decisions and traceability · Review.

Use this method to make a system coherent across runtime boundaries,
application behavior, frontend implementation, and user experience. These layers
have distinct responsibilities, but a decision in one can change another's
quality. Read [experience-handoff.md](experience-handoff.md) for detailed
interaction and visual design; this file defines the contracts and cross-layer
checks that keep those decisions implementable.

Use these labels as review perspectives. Teams may name or combine them
differently; responsibilities and cross-layer contracts matter more than a
universal taxonomy.

## Set the depth from the requested scope

For a complete `software_system` or `agent_infrastructure`, sketch the smallest
architecture that supports the requested end-to-end behavior and quality needs.
For a `scoped_change`, inspect the affected component, state owner, and
interfaces; review only decisions the change can disturb. Do not make a small
repair carry a new system diagram, stack selection, or broad redesign. Follow
existing project conventions unless evidence justifies a change.

Start from the brief and actual host. Identify actors and journeys, system
boundaries, external services, important data and its lifetime, expected usage,
deployment environment, constraints, and protected behavior. Keep explicit
requirements, derived needs, reversible defaults, and unknowns distinct. Never
invent an SLA, permission, or external capability. If no real service target
exists, mark any local prototype target provisional and state what evidence
could replace it.

## Define measurable quality scenarios

For each relevant quality need, state a condition or stimulus, expected system
response, measurement method, and threshold with its source. Choose only
attributes that matter: response time and time-to-usable-view, throughput or
resource use, availability, recovery time and data loss, security boundaries,
accessibility, or maintainability. Ground thresholds in a user requirement,
existing service objective, measured baseline, or an explicitly provisional
prototype target. Do not present an estimate or local default as a production
SLA.

State load assumptions before making capacity claims: traffic shape, concurrent
work, payload size, retention, and dependency limits as relevant. Treat
capacity estimates as hypotheses until representative load or runtime checks
support them. For failure scenarios, specify the observable failure signal,
state that must survive, recovery or reconciliation behavior, and verification
method. “Resilient,” “fast,” and “scalable” alone are not acceptance criteria.

## Assign responsibilities and contracts

**System architecture** owns runtime boundaries: processes or services,
deployment topology, external dependencies, trust boundaries, resource and
capacity assumptions, operational ownership, metrics/logs/traces, actionable
alerts, and recovery. Choose
queues, replicas, or separate services only when a requirement or measured
constraint supports the added complexity. Define timeouts, bounded retries,
health signals, and backup or reconciliation evidence where failure could
affect the outcome. A deployment sketch alone is not operational readiness.

**Application architecture** owns domain behavior and data meaning. Assign one
authoritative owner to each mutable fact; define component responsibilities,
interfaces, validation, and error/result semantics. Specify a state machine and
invariants when work spans steps, persists across navigation, or can be
interrupted. Add authorization only from explicit policy, otherwise keep it
safely configurable and unresolved. Add idempotency when retries or duplicate
requests would matter. Include schema evolution and compatibility when data is
persisted or exchanged. For replayable work, bind the stable operation identity
to its payload and configuration/schema versions; define conflicts for identity
reuse with changed content, and preserve the version needed for recovery. Cover
each consequential submission, including acknowledgement loss, rather than
assuming one deduplicated inner step protects the entire workflow.

**Frontend engineering** turns those contracts into components, routes, and
request lifecycles. Separate transient view state from server-owned state, and
define where drafts live. Specify cancellation or stale-response handling when
users can navigate, change input, or repeat work before a response returns.
Derive cache freshness and invalidation from data ownership. Use optimistic
updates only when rejection or conflict can be reconciled without losing work.
Make loading, empty, error, offline, and recovery states match actual request
and persistence semantics. Select rendering, lazy loading, prefetching, or
caching based on a measured bottleneck or explicit prototype hypothesis. Keep
semantic structure, keyboard and focus behavior, labels, and accessible status
feedback in the implementation contract.

**Interaction and visual design** determine how users understand navigation,
information groups, task sequence, feedback, hierarchy, and emphasis. Resolve
those details with [experience-handoff.md](experience-handoff.md). Feed its
content structure, state coverage, and visual intent into frontend components
and system constraints; design is not a skin applied after behavior is fixed.

## Record decisions and trace delivery

For each consequential choice, record a decision ID and linked requirement,
selected option, considered alternatives and reasons, constraints and evidence,
affected components or interfaces, risks, and a concrete reconsideration
trigger. Label measured effects separately from design assumptions. Carry
reversible defaults and unknowns into the brief or task plan.

Connect each material requirement through a reviewable chain:
`requirement → decision → component/interface → task → acceptance evidence`.
Name the implementation boundary, assign its work, then state an observable
acceptance result and evidence level. A diagram or completed template does not
prove behavior. Keep task and acceptance detail in the project plan rather than
creating a second checklist that can disagree with it.

Check cross-layer consequences before accepting a change. Prefetching may reduce
wait while increasing network/server load or exposing data earlier. Optimistic
updates can feel immediate while complicating conflict recovery. Animation may
clarify a transition while delaying access or harming reduced-motion users.
Denser layouts and stronger color contrast can redirect visual emphasis while
weakening readability, touch targets, or hierarchy. For each relevant tradeoff,
name affected layers, expected benefit, possible regression, and the measurement
or scenario that can distinguish them. Preserve current behavior as a
comparison when feasible; call unmeasured benefits hypotheses.

## Review with counterexamples

Try to break the design with relevant adverse cases: a dependency slows or
fails, a request is duplicated, a user leaves during save, stale data returns
after newer input, permission is absent, or a task is repeated after recovery.
Check that state ownership and error semantics still yield a safe,
understandable result. For consequential architecture, use an authorized fresh
context with the raw brief and candidate when available; otherwise make a
separate self-critique and label it. Resolve omissions or record the blocker
and next evidence needed. This is an internal design check, not a user approval
step or a claim of production readiness.

For example, an offline work-order editor can keep a draft locally, show a
queued state, and submit with an idempotency key after reconnecting. Trace the
requirement through application state, API contract, frontend feedback, and a
recovery task. Acceptance can disconnect during editing, reload, reconnect,
and retry; inspect that the draft survives and one work order is created. This
controlled test proves that scenario only, not live network reliability or a
production availability target.
