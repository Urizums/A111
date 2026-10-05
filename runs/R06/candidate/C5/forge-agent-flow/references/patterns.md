# Topology choices

| Task evidence | Start with | Escalate only when |
| --- | --- | --- |
| One transformation with supplied context | One agent | Measured defects justify a separate checker. |
| Ordered dependencies with stable steps | Chain with artifact contracts | Dynamic subtasks materially change the work. |
| Distinct request categories | Router and specialist paths | Classification errors justify a fallback. |
| Independent evidence or independent parts | Workers and merge | Host has genuine isolation and join semantics. |
| Open-ended decomposition | Manager and bounded workers | One agent cannot handle the context or tool separation. |
| Clear quality criteria and repairable outputs | Draft, check, bounded repair | Revisions have measurable acceptance benefit. |

Do not confuse a role label with an agent process. The same capable host can
perform successive stages. Independent review means separate context; different
role names in one context do not provide independence. Multiple agents can repeat
the same error, so voting does not substitute for source evidence.

For IR v1, express independent workers sequentially and describe potential
parallelization as an adapter requirement. Do not encode multiple successors as
if every branch runs. For future parallel adapters, specify immutable input
snapshot, per-worker output namespace, join policy, error policy and merge owner.

The factory selects a topology for the particular goal. It does not always
generate its own construction-stage graph for the user's task. Default to a
single candidate plus a simple baseline, then justify additional complexity with
test evidence, coordination cost, or a concrete requirement.

## Research basis

Use these as pattern references, not proof that this particular skill works:

- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
  distinguishes predefined workflows from dynamic agents and recommends starting
  with simple composable patterns. Published 2024-12-19; checked 2026-09-23.
- [LangGraph: Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
  illustrates chaining, routing and parallel workflows. Consult current APIs
  before producing an adapter; this skill does not ship a LangGraph adapter.
- [LangGraph: Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
  distinguishes per-run checkpoints from longer-term stores. The local dispatcher
  only provides a small per-run checkpoint mechanism.
