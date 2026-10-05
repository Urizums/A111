"""Build a versioned short entry, retaining all C6 implementation bytes."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / 'runs/R07/candidate/C6/forge-agent-flow'
TARGET = ROOT / 'runs/R08/candidate/C7/forge-agent-flow'

ENTRY = '''---
name: forge-agent-flow
description: Build and verify software systems, agent infrastructure and explicitly requested reusable agent flows. Also handle focused repository changes and one-time tasks directly, scaling planning and checks to the requested outcome.
---

# Agent Flow Forge — C7 short entry

## Start with the requested outcome

Choose the route from the deliverable, not isolated keywords. Read the raw
request and applicable repository rules, identify material constraints, then
perform the smallest useful authorized action. For an ordinary one-time task,
this can be reading the supplied data and producing its first checked output;
do not require a long plan, factory, snapshot or project controller first.
State relevant assumptions briefly. Ask only when a consequential choice has
no safe reversible default; continue independent work while awaiting an answer.

| Outcome | Route and minimum references |
| --- | --- |
| One-time result from supplied material | Direct scoped task. No extra reference required unless a condition below applies. |
| Focused repository change | Repository workflow; affected code, relevant checks and a short impact note. |
| Usable application, service or worker runtime | Program mode: [software-delivery](references/software-delivery.md), [project-execution](references/project-execution.md), and program sections of [evaluation-plan](references/evaluation-plan.md). |
| Explicitly create a reusable agent flow | Factory/package mode: [task-entry](references/task-entry.md), [flow-contract](references/flow-contract.md), [package-contract](references/package-contract.md), and flow sections of [evaluation-plan](references/evaluation-plan.md). |
| Execute a supplied package | Preserve it; read [task-entry](references/task-entry.md) and the matching package schema/host protocol, then execute its actual inputs. |
| Design explicitly requested, or execution actually blocked | Useful design with the exact blocker; do not select this route to avoid runnable work. |

For program work, record relevant requirements, state owners, interfaces and
quality scenarios before the first vertical slice. Use a durable TODO when
coordination or continuity requires it. A startup probe or copied template is
setup evidence; it is not the first business artifact or proof of completion.

## Load only what the current action needs

- New system/architecture: [system-architecture](references/system-architecture.md)
  and [design-from-brief](references/design-from-brief.md). Existing changes use
  their affected layers. Keep requirements, defaults and blockers distinct.
- Graphical product: [experience-handoff](references/experience-handoff.md),
  the independent design-product-experience skill, then actual target interaction.
  CLI work needs command/error/recovery journeys, not graphical palettes.
- Executable product acceptance: [executable-acceptance](references/executable-acceptance.md).
  Runtime, visual, usability and performance evidence establish different claims.
- Review/regrade: the requirements-based verdict section of
  [task-entry](references/task-entry.md). Recompute from original clauses and raw
  evidence; optional advice cannot downgrade satisfied required behavior.
- Stopped project/new host: [portable-continuation](references/portable-continuation.md).
  Probe real tools; preserve original input bytes, failed attempts and budgets.
- Continuous project: [continuous-research](references/continuous-research.md).
  A delivery does not close the goal. Start a valuable successor through actual
  work before phase transition; a next-stage plan alone is insufficient.
- Actual native worker: [host-execution](references/host-execution.md) and
  [host-bridge](references/host-bridge.md). Measured runs additionally require
  [recording-protocol](references/recording-protocol.md) BEFORE dispatch.
- Claimed/unknown native call: [host-driver](references/host-driver.md),
  [host-observability](references/host-observability.md) and resource boundaries
  as applicable. Reconcile the existing call before any retry.
- Frozen bounded development/validation: initialize `scripts/bounded_run.py`
  once with original source and inputs; retain every failure and record each
  failure-driven source change before rerunning. At most two repairs; another
  worker, renamed sample or successful bypass cannot reset the limit.
- Exact-byte handoff: capture and verify `scripts/snapshot.py` bundles before
  issuing a bound native case. Restoring is inspection, not replay of effects.
  C6 restore uses Linux renameat2 and explicitly fails on unsupported hosts;
  C7 does not add cross-platform or crash-durability guarantees.

The detailed inherited architecture, flow/factory and host methods remain in
[extended-contract](references/extended-contract.md). Read its applicable
sections when the selected path requires them, not as a universal startup gate.
Resolve scripts from the directory containing this SKILL.md; PATH aliases and
historical host absolute paths are not required or reusable.

## Decide when independence is necessary

Use one context with a relevant check for ordinary scoped tasks. Use a fresh
independent context when the request/acceptance explicitly requires it, when
grading an authored reusable candidate, or when evidence/tool separation is a
material requirement. Routine output checks alone do not require another agent.
Keep core architecture, skill instructions, fixes and final integration with
the coordinator. Delegate separable research and independent verification to
available Luna/max; otherwise use a real available fresh context and record its
actual model and limits. Give it frozen requirements and artifacts, never
expected answers, prior diagnoses or another worker's conclusions.

Persist intent before one native creation; retain actual return, task identity,
status and terminal artifacts. Instruction-level read/write assignments are
not security isolation. Unknown creation/termination remains unknown, not
permission to duplicate a call. Author self-check is not independent acceptance.
Unavailable independent execution leaves that criterion unverified while local
implementation and regressions continue. Use the host's actual limits; tokens,
cost, provider identity and timing that are unavailable are null.

## Complete and continue with evidence

Check actual output against relevant original requirements. Exercise rejection,
missing input, conflict, failure/recovery and state reuse when material to the
behavior. Freeze candidate acceptance before verification; preserve original
cases and exhausted budgets. A local stub, package, schema, compile or planned
UI is not proof of real provider execution or product completion.

Report artifact, how to run it, observed evidence and remaining blockers.
For ongoing goals update the same ledger/checkpoint, keep blockers local to the
affected branch and perform a meaningful successor's real first step before
closing the phase. No instruction or local controller promises an automatic
background scheduler, production readiness or unobserved performance gains.
'''

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def main():
    lock = json.loads((ROOT/'runs/R07/candidate/C6-lock.json').read_text(encoding='utf-8'))
    for row in lock['files']:
        raw = (ROOT/row['path']).read_bytes()
        assert len(raw) == row['size_bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], row['path']
    shutil.copytree(PARENT, TARGET, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    inherited = (TARGET/'SKILL.md').read_text(encoding='utf-8')
    # Relative references now start in references/, scripts remain in the skill root.
    inherited = inherited.replace('(references/', '(').replace('`scripts/', '`../scripts/')
    (TARGET/'references/extended-contract.md').write_text(inherited, encoding='utf-8', newline='\n')
    (TARGET/'SKILL.md').write_text(ENTRY, encoding='utf-8', newline='\n')
    rows = []
    for path in sorted(TARGET.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            rows.append(dict(path=path.relative_to(ROOT).as_posix(), size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    dump(ROOT/'runs/R08/candidate/C7-lock.json', dict(schema='forge-revision-lock/1', revision='C7', parent='C6', files=rows))
    dump(ROOT/'runs/R08/design/change.json', dict(parent_lock='runs/R07/candidate/C6-lock.json', candidate_lock='runs/R08/candidate/C7-lock.json', entry_bytes_before=len((PARENT/'SKILL.md').read_bytes()), entry_bytes_after=len(ENTRY.encode()), implementation_unchanged=True, claim='Reduced mandatory entry bytes; no performance improvement established', repairs_used=0, repair_limit=2))
    print(json.dumps({'candidate':str(TARGET), 'files':len(rows), 'entry_bytes':len(ENTRY.encode())}))

if __name__ == '__main__':
    main()
