# Browser run 1 failure record

Command: `python /workspace/A111/runs/future/versioned_preset_catalog/independent/worker/browser_validate.py 2>&1 | tee /workspace/A111/runs/future/versioned_preset_catalog/independent/worker/logs/run-1.log`

Original harness: `browser_validate.failed1.py` (SHA captured with final artifacts).
Captured output: `run-1.log`; structured observations: `browser-results.failed1.json`.

Run summary: 60 checks passed, 10 failed, and one journey error. The review journey timed out after keyboard activation of the dialog's confirm button; the reader showed the same behavior (the dialog stayed open and the annotation remained). The stock conflict dialog opened and retained the form draft, but the harness incorrectly expected the phrase “另一份” in its body; the actual body states the compared quantities. The rendered accessible-control scan also returned empty `innerText` for buttons nested under `details`, which needs inspection against the DOM before deciding whether it is a harness or candidate issue. A 404 console error was captured. The stock conflict remained unresolved because the harness attempted Enter after Tab; the post-run stored value was the simulated record. The reader delete remained unconfirmed, preserving the saved annotation.

No repair has been made. First-run evidence is retained unchanged before any subsequent run.
