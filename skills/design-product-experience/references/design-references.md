# Design references: source and sampling record

Use references to investigate a specific task and platform. The notes below were checked on 2026-10-02 by the coordinator. Product pages and standards can change; revisit the live source before relying on a current rule. These presets reproduce no third-party text, screen, CSS, or asset. Unless a row says otherwise, specific reuse terms were not checked because these sources are observation-only; verify current terms before adapting material.

| Source | Observed and checked | Appropriate use | Permission and limits |
| --- | --- | --- | --- |
| [Refero Styles](https://styles.refero.design/) | The page offers AI-readable DESIGN.md material covering colors, type, spacing, and components. Checked 2026-10-02. | A lead for discovering design-system vocabulary and token categories; reuse material only when its current terms permit it. | Terms and the specific DESIGN.md revision were not checked. Pin the exact revision and retain notices before adapting it. A catalog page does not establish fit for the target product. |
| [Mobbin](https://mobbin.com/) | Official product describes real-product screens, flows, videos, and prototypes. Checked 2026-10-02. | Observe task order, screen-to-screen continuity, and alternate states in a comparable product. | Access or subscription is not a reuse license. Record only what was actually viewed; reuse screens/assets only if current terms grant that right. |
| [Pageflows](https://pageflows.com/) | Official search-result listing describes recordings and step annotations. The homepage could not be opened during this check; search only, checked 2026-10-02. | An unverified lead for finding annotated flows. | Reopen and verify the particular flow before citing observations. Availability and reuse rights were not verified. |
| [CollectUI](https://collectui.com/) | Official page presents daily interface inspiration. Checked 2026-10-02. | Visual inspiration for composition or visual treatment. | Inspiration does not establish interaction behavior or task success. Contributor-specific asset reuse terms were not checked; reuse only if verified terms allow it. |
| [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) | Official HIG entry point. Page body retrieval was insufficient for this check; checked 2026-10-02. | Find applicable Apple platform guidance, then read the specific current section. | No specific Apple rule is claimed as verified here. Do not treat the link alone as compliance evidence. |
| [Android Design](https://developer.android.com/design) | Official Design & Plan guidance checked 2026-10-02. | Platform-specific design research before Android implementation. | Guidance is not runtime evidence; validate in the target app and device. |
| [Android system bars](https://developer.android.com/design/ui/mobile/guides/foundations/system-bars) | Official system-bars guidance checked 2026-10-02. | Account for system bars and insets in mobile layout and navigation review. | Do not transplant a desktop/web arrangement into mobile without device evidence. |
| [WCAG: Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) | W3C Understanding page checked 2026-10-02: color cannot be the sole visual means of conveying information. | Review status, validation, selection, and chart cues for a second signal. | Understanding guidance is explanatory; evaluate the actual rendered interface. |
| [WCAG: Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) | W3C Understanding page checked 2026-10-02: 4.5:1 for normal text and 3:1 for large text as defined by the criterion. | Check text/background pairs in each palette and relevant state. | Check the criterion's definition and exceptions; do not infer passing contrast from a screenshot. |
| [WCAG: Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) | W3C Understanding page checked 2026-10-02; the criterion discussed is Level AAA. | Consider disabling non-essential interaction-triggered motion. | Do not describe this criterion as AA or imply every animation is prohibited. |
| [shadcn/ui theming](https://ui.shadcn.com/docs/theming) and [license file](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md) | Official theming docs describe semantic background/foreground token pairs. License file is available in the repository. Checked 2026-10-02. | A candidate only when the existing stack already uses shadcn/ui; semantic pairing can inform an independent token map. | No source or dependency is copied by these presets. The repository link is mutable: before adapting code, pin the exact revision and inspect its applicable license and notices. |

| [MDN reduced-motion media query](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion) | Official reference checked 2026-10-02: the query reflects the user’s device preference for reducing non-essential motion. | Define a static or simplified transition reaching the same semantic state. | Presence of the rule in CSS is source evidence; check the actual target with the preference enabled before claiming behavior. |

## Sampling steps

1. Pick two or three references that match the audience's task, platform, and content scale. Prefer one reference for interaction flow and another for visual hierarchy; do not infer behavior from a static gallery.
2. Follow the whole relevant path. Record the page or flow URL, access date, starting state, actor/action, visible response, loading/error/empty state, navigation, and how a user returns or exits. Record what you observed before writing your interpretation.
3. Classify each source as an exact target source, compatible component, platform guidance, visual inspiration, or unverified lead. Only call a source “exact” after checking identity and provenance.
4. Note applicable reuse terms separately from design observations. Screenshots, recordings, and search results are not licenses. Before reusing code or media, identify the exact source revision, license, required notices, and asset-specific terms. If any part is unclear, use the observation to make an original design and mark reuse unverified.
5. Translate the observation into a task-specific hypothesis, semantic tokens, page regions/components, and states. Validate visual hierarchy and interactive behavior separately against a shared journey ID; neither a reference screenshot nor a candidate screenshot proves task effectiveness.

## Research packet handoff

Give a research worker a task/audience/platform, questions to investigate,
preferred sources and a separate output path. For a small question, return a
short evidence note; for a cross-source interface study, return:

- **Sources:** URL, access date, page/flow identity, retrieval method, readable
  scope, direct observations, and unavailable sections. Record exact revision,
  license and notices when proposing material reuse; mark unknowns explicitly.
- **Preprocessed candidates:** region/attention map, navigation and close/back
  paths, component states, palette/token pairs and motion transitions supported
  by those observations. Distinguish observed facts from inferred candidates;
  tie each candidate to the target task and its source. Static material cannot
  establish a transition, focus behavior or complete user flow.
- **Fit and questions:** alternatives, platform/task differences, conflicting
  observations, assumptions and what must be checked in the target app.
  Calculations label their selected inputs and limits; access failures remain
  failures rather than successful observations.

The coordinator verifies consequential claims against the source, judges fit,
selects or rejects candidates and authors the reusable skill. Preserve the
research packet separately from the adopted design. A researcher does not
decide skill architecture, author core instructions or certify target behavior.
Use a fresh evaluator after authoring; validation may produce reports or
fixtures, while the coordinator owns skill repairs. Follow the user's actual
role assignment rather than delegating core authorship merely because the
worker can produce a fluent draft.
