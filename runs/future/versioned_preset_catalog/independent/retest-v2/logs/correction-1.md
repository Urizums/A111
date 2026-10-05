# Failure-driven harness correction 1 of 2

Prior failure source: v1 run 1, preserved without edits at `../worker/browser_validate.failed1.py` (SHA-256 `ae7cdde439cd90d885a1825065c8f5786f3ce9bbbb6c8b0aabd57b2a44856188`), `../worker/browser-results.failed1.json` (SHA-256 `9d971e683253f5eac4232169c5630c5eb4a46bbfa6bcf6f3ebd5510eab86b414`), and `../worker/logs/run-1.log`. It timed out waiting for review success after keyboard confirmation, recorded reader confirmation as closed without deletion, and read stock storage before the delayed save completed. The stock assertion also expected a phrase that was absent from the actual dialog copy.

Correction: replace close/button-enabled waits with state-based completion checks; record keyboard confirmation outcome independently; if keyboard confirmation does not apply the change, use a separately recorded pointer path to finish the journey; compare stock conflict text to the observed current/draft quantity copy and wait for exact version 1/version 3 storage plus success status. This keeps the keyboard result visible while allowing the remaining required journey observations.

The original baseline and target-bound harnesses are preserved. This correction is the state/interaction evidence repair, counted as 1 of 2 available corrections. Exact diff: `correction-1.diff`. Corrected harness snapshot: `browser_validate.after-correction-1.py`.
