from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DOMAIN = ROOT / "runs/R23/review/clean-initial"
SOURCES = [
    "runs/R23/receiving-packet/manifest.json",
    "runs/R23/receiving-packet-lock.json",
    "runs/R23/receiving-packet/process-terminals.json",
    "runs/R23/brief/TASK.md",
    "runs/R23/brief/INPUTS.json",
    "runs/R23/acceptance.json",
    "runs/R20/final/candidate/C13-lock.json",
    "runs/R20/final/candidate/C13/forge-agent-flow/SKILL.md",
    "runs/R20/final/candidate/C13/forge-agent-flow/references/collaboration.md",
    "runs/R20/final/candidate/C13/forge-agent-flow/references/continuation.md",
    "runs/R20/final/candidate/C13/forge-agent-flow/references/evaluation.md",
    "runs/R20/final/candidate/C13/forge-agent-flow/references/frontend.md",
    "runs/R20/final/candidate/C13/forge-agent-flow/references/iteration-and-recovery.md",
    "runs/R20/final/candidate/C13/forge-agent-flow/references/modeling.md",
    "runs/R20/final/candidate/C13/forge-agent-flow/references/source-evaluation.md",
    "runs/R20/final/candidate/C13/forge-agent-flow/references/workflow-design.md",
    "runs/R21/input-lock.json",
    "runs/R21/inputs/raw/calendar.csv",
    "runs/R21/inputs/raw/decision.json",
    "runs/R21/inputs/raw/demand_reports.csv",
    "runs/R21/inputs/raw/items.csv",
    "runs/R21/inputs/raw/promotions.csv",
    "runs/R21/inputs/raw/stores.csv",
    "runs/R21/inputs/raw/weather.csv",
    "runs/R21/inputs/reference/BASELINE.md",
    "runs/R21/inputs/reference/experiment.json",
    "runs/R21/inputs/reference/run.py",
    "runs/R23/design-correction-v2-lock.json",
    "runs/R23/execution/design-correction-v2/WORKFLOW.md",
    "runs/R23/execution/design-correction-v2/METHOD-OUTPUT-INTERFACE.md",
    "runs/R23/design/probe.py",
    "runs/R23/execution-lock.json",
    "runs/R23/execution/v2/consumer_slice.py",
    "runs/R23/execution/v2/consumer-slice-config.json",
    "runs/R23/execution/v2/consumer-slice-freeze.json",
    "runs/R23/execution/v2/consumer-point-slice.csv",
    "runs/R23/execution/v2/consumer-point-slice-report.json",
    "runs/R23/execution/receipts/r23-consumer-30-compute-v2-final.txt",
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    code = DOMAIN / "verify_slice.py"
    config = DOMAIN / "verifier-config.json"
    freeze = {
        "schema": "r23-clean-initial-independent-freeze/1",
        "frozen_before_recomputation": True,
        "verifier": "runs/R23/review/clean-initial/verify_slice.py",
        "verifier_sha256": sha(code),
        "config": "runs/R23/review/clean-initial/verifier-config.json",
        "config_sha256": sha(config),
        "freezer_sha256": sha(Path(__file__)),
        "source_files": [
            {"path": name, "size_bytes": (ROOT / name).stat().st_size, "sha256": sha(ROOT / name)}
            for name in SOURCES
        ],
        "selection": {
            "actual_slice": "R23-CONSUMER-POINT-IN-TIME-2026-10-14",
            "decision": "Independently recompute only the frozen one-day, two-method point forecasts and source-time boundary; do not add interval or replenishment outcomes that this slice did not produce.",
            "tolerance": 1e-8,
            "methods": ["shared_ridge10_consumer", "weekly_median56_consumer"],
        },
        "telemetry": {"actual_model": None, "tokens": None, "cost": None},
    }
    out = DOMAIN / "freeze.json"
    out.write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"freeze_path": str(out.relative_to(ROOT)).replace("\\", "/"),
                      "verifier_sha256": freeze["verifier_sha256"],
                      "config_sha256": freeze["config_sha256"],
                      "source_count": len(freeze["source_files"]),
                      "frozen_before_recomputation": True}, indent=2))


if __name__ == "__main__":
    main()
