# Failure-driven harness correction 2 of 2

Prior failure source: v1 run 1's responsive accessible-name scan flagged `review-error` and `stock-incoming` while their state-example `<details>` containers were closed; the scan read `innerText` from those unrendered descendants.

Correction: open each view's state-example details before the control scan, and collect rendered text or text content only from controls with layout boxes and visible computed style. This makes the reachability/name check exercise the controls after their disclosure is expanded and avoids treating the collapsed sample controls as visible but unnamed.

This is the second and final available correction. Exact diff: `correction-2.diff`. The full run will use `browser_validate.after-correction-2.py`; no further harness or evidence-code corrections are available under the original budget.
