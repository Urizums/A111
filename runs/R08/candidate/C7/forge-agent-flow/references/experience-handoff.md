# Experience design handoff

Use this bridge for a deliverable with a user interface. Keep runtime boundaries,
domain rules, frontend state ownership, and the shared project TODO in Forge.
Use the independent [Product Experience Design](https://chatgpt.com/skills?skill_id=6abf2e4f5eac81918006e6d1a19615d3)
(`design-product-experience`) skill for task journeys, visual
hierarchy, semantic palettes, density, component states, reference sampling,
motion specifications, and scoped frontend visual implementation. It also works
on design-only requests without Forge; neither skill requires an invocation
cycle. Do not invoke a UI skill for a service with no interface.

Before the handoff, share the brief, audience, platform, main journeys, actual
stack and components, data and permission contracts, protected behavior,
reversible defaults, unknowns, and available verification tools. Retain one
project plan rather than creating competing status or acceptance records.

Return each important requirement with its design decision, affected region or
component, semantic state, implementation task, and acceptance case. Include:

- Layout, non-color hierarchy, density and palette choices tied to the audience
  and primary action; representative content, long labels and narrow layouts.
- Navigation, Close/Back/Exit, draft persistence, loading, empty, error, offline,
  cancellation, retry, stale response and conflict behavior as relevant.
- Motion purpose, trigger, before/after state, direction, duration/curve source,
  interruption/reversal, focus/input, reduced-motion alternative and checks.
- Observed references separately from inferred benefits; exact revision and
  reuse conditions for adopted material; tunable defaults separately from
  measured outcomes or platform rules.
- Evidence and unresolved checks, separating design, source inspection,
  fixtures, real browser/device behavior, rendered appearance and user outcomes.

Review impacts together: prefetch changes load and data access; optimistic
feedback changes reconciliation; motion changes focus and interruption;
density changes reading and touch behavior. Keep business state independent
from decorative animation completion. Integrate the decision and any contract
change into the same project tasks, then perform relevant acceptance in the
target app. A preset is a candidate, not a product-quality certificate.

If the independent skill is unavailable, apply these minimum contracts directly
in the existing stack and name the missing detailed design review. Continue
unblocked development; do not invent references, current platform rules or
browser results to fill the gap.
