# Continuous research and delivery

Keep the long-term project goal, a particular delivery milestone, and host
execution availability as separate state. A successful PR, merge or smoke test
updates its delivery record; unfinished accepted capabilities keep the goal
active. Preserve earlier completed/cancelled phases as history.

Maintain two queues: required capabilities and exploratory challenges. Every
item needs priority, dependencies, owner, write paths, frozen input, acceptance,
evidence, repair budget, blocker/recovery condition and next action. Choose ready
work by priority. A blocked task does not stop independent ready work. Do not
replace unfinished requirements with new task names or reset their failure count.

Use small progressive batches. Cover distinct business domains and delivery
forms: direct one-off task, import/migration, complete application, reusable agent
flow, worker failure/recovery and actual UI interaction. Begin with simple work;
increase a meaningful dimension after observing the previous batch. Keep future
categories explicit in the backlog. Do not repeat renamed samples or manufacture
tasks solely to appear continuously busy.

For each expansion, record the user target, concrete unknown and hypothesis.
Resolve material unknowns with bounded primary-source research: source URL,
version/access time, supporting passage, alternatives, adoption reason and a
small experiment. Stop research once it supports an implementable decision.
Root authors architecture, skill text and core logic. Luna may research, prepare
UI requirements, scaffold bounded work and independently validate original
requirements; do not give validators the expected result or author diagnosis.

Separate feasibility from actual effect. Run on the target runtime, then record
baseline, conditions, raw results, limits and observed usability, correctness,
recovery, interventions, completion, UI or timing measures relevant to that task.
Unavailable metrics are null. Unit tests, command workers, native model workers
and provider-wide behavior support different claims. Never equate a fake worker
or local command crash with full provider recovery. Preserve first failures and
at most two repairs per frozen candidate; do not change inputs or acceptance to
turn a failure into a pass.

For UI work, derive hierarchy, density, spacing, colors, responsive behavior and
loading/error/empty/conflict states from that product. Verify actual interactions
against the real backend in the target browser. Template reuse alone is not UI
acceptance; screenshots alone do not prove interactions.

The last phase item is “启动下一阶段任务”. It is done only when the next phase
plan exists and its first task has actual start evidence. A placeholder state
change is insufficient. A fresh-context handoff should receive the repository,
original goal and material, select the next task through the entry contract,
preserve failed attempts, complete it and start its successor without a user
“continue” message. Bound each worker assignment; Root continues the project.

`scripts/continuation.py --root CHECKOUT next` selects work without mutating it.
`start TASK --evidence COMMAND.json` binds actual command evidence, input hashes
and acceptance. `finish TASK --result RESULT.json` checks criteria/effect records.
`delivery ID --evidence FILE` records a milestone without closing the goal.
`advance --next-phase PLAN.json` requires the actual successor start and archives
the previous phase. `validate` checks retained evidence. The state uses one
cooperating writer and a POSIX lock; `sync` repairs derived checkpoint/phase views
after an interrupted write. It is not a sandbox, multi-file transaction, model
API, or daemon. CLI compatibility and host behavior require their own tests.

Before ending a host session, save the current frontier, pending native calls,
budgets and next action. Probe available continuation/monitor tools. If a real
schedule is configured, keep its returned ID and distinguish scheduled from
executed. If no supported background execution exists, say so explicitly and
leave the checkpoint ready to resume; never claim code keeps running merely
because a prompt or TODO says it should.
