# Local recording qualification Q1

Separate from frozen C1. No business worker, no actual native call, no canonical source change. Uses existing frozen capture.py. Root authors this plan before invoking target commands.

Q01: outer CLI record retains exact target argv, base64/decoded stdout/stderr, exit and same-boot monotonic start/end for successful and failed marker targets.
Q02: successful target marker creates one original event file inside assigned local directory; failure creates no false marker.
Q03: native observer target captures an explicitly synthetic local intent payload; no real creation/status/completion or authority is inferred. Outer CLI and original event payload/hash must agree.
Q04: unsuccessful ordinary target preserves nonzero exit and exact stdout/stderr bytes.
Q05: outer capture wrapper is explicitly the instrumentation boundary; only invoked targets are in this denominator. No recursive capture and no assertion that all host/tool activity is captured.

Independent audit may review these files after C1 stabilizes. Passing this local exercise does not establish future ordinary worker compliance or a performance improvement.
