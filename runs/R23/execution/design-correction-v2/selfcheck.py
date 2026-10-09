"""Check only the j1 source-bound workflow/interface correction."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = ROOT / "runs/R23/execution/design-correction-v2"


def main() -> None:
    task_line = (ROOT / "runs/R23/brief/TASK.md").read_text(encoding="utf-8").splitlines()[8]
    assert "每个方法" in task_line and "method_id" in task_line
    workflow = (HERE / "WORKFLOW.md").read_text(encoding="utf-8")
    interface = (HERE / "METHOD-OUTPUT-INTERFACE.md").read_text(encoding="utf-8")
    status = json.loads((HERE / "CORRECTION-STATUS.json").read_text(encoding="utf-8"))
    expected = 42 * 12 * 8
    assert expected == 4032
    assert "j1" not in workflow and "j1" not in interface
    assert "prior Stage 7" not in workflow and "selected-method-only" not in interface
    assert "every `method_id` in the frozen `requested_methods` registry" in workflow
    assert "recommendation sets a" not in workflow  # Ensure no selected-only instruction survived.
    assert "only to the selected" not in workflow
    for token in ["requested_methods", "recommended_method_id", "future_predictions.csv", "future_replenishment.csv", "4,032", "failed", "unverified", "incomplete"]:
        assert token in workflow or token in interface, token
    for col in ["demand_point_units", "lower90_units", "upper90_units", "interval_level", "q_units", "method_id"]:
        assert col in interface
    assert status["revision_kind"] == "informed correction; not a new blind design"
    assert status["basis"]["source"] == "runs/R23/brief/TASK.md:9"
    assert "selected method" in status["basis"]["finding"]
    assert status["independent_reception"] == "pending"
    assert status["not_changed"][1].startswith("The original one-day consumer slice")
    print(json.dumps({
        "source_line9_has_each_method_and_method_id": True,
        "j1_finding_as_recorded_by_author": "fail; selected-method-only future output contract",
        "expected_rows_per_method_per_table": expected,
        "selected_method_only_contract_removed": True,
        "all_method_output_and_failure_contract_present": True,
        "correction_kind": status["revision_kind"],
        "author_self_check_only": True,
        "independent_reception": "pending",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
