# Adapt Forge to substantial frontend work

Read when UI architecture, interaction, visual design and implementation must
work together. Start from users, journeys, data/state and actual platform. Respect
the existing stack and available design tools; no particular framework or other
skill is required merely to name a frontend workflow.

Resolve information architecture, interaction, visual system, component/state
ownership and runtime interfaces together. Identify navigation, input/validation,
loading, empty, error, success and recovery states relevant to the actual task.
Give parallel designers/developers shared tokens/interfaces with one integrator,
not incompatible full apps to splice together.

An appropriate first slice crosses the main journey: raw input → visible state
change → correct user-relevant result → receiving check. Run it in the actual
browser/target runtime. Compilation, static DOM counts or screenshots alone cannot
prove interactive success. A mocked backend proves the declared UI contract under
that mock, not production integration.

Freeze assertions for the main journey, invalid/error recovery, keyboard access,
responsive layout and any required visual reference. Use real interactions and
meaningful screenshots at specified viewports. Check accessible labels, focus,
keyboard completion and clipping/scroll behavior where relevant. A single viewport
cannot establish all-device compatibility; performance claims need measurements
with defined conditions, not subjective fast/slow language.

Distinguish functional behavior, visual inspection, accessibility observations and
usability evidence. When visual acceptance matters, assign who actually inspects
rendered output and what task/reference criterion would reject it. Attractive
styling is neither proof of task correctness nor a universal layout prescription.

Use expected state/output and original constraints as the oracle. For numerical
frontends check chart/table/export values against raw fixtures or a separately
computed result; do not validate only the rendering of whatever the app supplies.
Preserve source status: unchecked demo data should not appear as verified results.

The reusable workflow delivers its method and real scoped evidence; product
HTML/CSS/JS, screenshots and browser tests belong to the generated app/evaluation
workspace. The Forge skill package remains the method. Stop or mark a gate
unverified if browser, reference or required environment is unavailable rather
than quietly converting runtime acceptance into text review.
