"""Portable negative controls for the independent branch coverage checker."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import coveragecheck
import evalplan
import flowctl


def complete_plan():
    cases = [
        ("ordinary_success", {"mode": "create", "text": "draft"}, "created", "Created a draft from the supplied text."),
        ("negative_input", {"mode": "reject", "text": ""}, "rejected", "The required text was empty."),
        ("recovery_path", {"mode": "retry", "text": "draft"}, "recovered", "The retry succeeded after a transient error."),
        ("reuse_path", {"mode": "reuse", "text": "draft"}, "reused", "The existing matching draft was reused."),
        ("authorization_allowed", {"mode": "send", "authorized": True}, "sent", "The user granted permission to send."),
        ("authorization_denied", {"mode": "send", "authorized": False}, "blocked", "The user did not grant permission to send."),
    ]
    return {
        "schema": "forge-eval/1",
        "id": "coverage_fixture",
        "criteria": [
            {"id": "behavior", "kind": "machine", "required": True, "assertion": "The declared operation result matches its input branch."},
            {"id": "rationale", "kind": "human", "required": True, "assertion": "The output gives the concrete reason or basis for its result."},
            {"id": "optional_format", "kind": "machine", "required": False, "assertion": "Optional formatting follows the declared shape."},
        ],
        "cases": [
            {
                "id": case_id,
                "inputs": inputs,
                "expected": {"result": {"state": state}, "evidence": {"reason": reason}},
                "expected_status": "completed" if state not in ("blocked",) else "blocked",
                "criteria": ["behavior", "rationale", "optional_format"],
                "required": True,
            }
            for case_id, inputs, state, reason in cases
        ],
        "baseline": "One bounded host-driven flow with explicit input and result evidence.",
        "limitations": ["Fixtures document expected values; they do not establish execution or semantic correctness."],
    }


def declaration(applies, reason):
    return {"applies": applies, "reason": reason}


def entry(requirement_id, criterion_id, applicability, obligations, scope):
    return {
        "requirement_id": requirement_id,
        "criterion_id": criterion_id,
        "scope": scope,
        "applicability": applicability,
        "obligations": obligations,
    }


def obligation(obligation_id, kind, case_ids, field="/result/state", **extra):
    return {
        "id": obligation_id,
        "kind": kind,
        "case_ids": case_ids,
        "input_variant": f"{kind} trigger with an independently specified input",
        "expected_fields": [field],
        **extra,
    }


def complete_coverage(plan=None):
    plan = plan or complete_plan()
    not_applicable = "This flow has no declared branch for this dimension."
    behavior_applicability = {
        "negative": declaration(True, "Empty input takes the explicit rejection branch."),
        "recovery": declaration(True, "A transient failure can take a retry path."),
        "reuse": declaration(True, "A matching existing result can be reused."),
        "authorization": declaration(True, "Sending requires a user authorization decision."),
        "ui_feedback": declaration(False, not_applicable),
        "explanation": declaration(False, not_applicable),
    }
    behavior_obligations = [
        obligation("success_create", "success", ["ordinary_success"]),
        obligation("reject_empty", "negative", ["negative_input"]),
        obligation("recover_retry", "recovery", ["recovery_path"]),
        obligation("reuse_existing", "reuse", ["reuse_path"]),
        obligation("send_allowed", "authorization_allowed", ["authorization_allowed"]),
        obligation("send_denied", "authorization_denied", ["authorization_denied"]),
    ]
    rationale_applicability = {
        "negative": declaration(False, not_applicable),
        "recovery": declaration(False, not_applicable),
        "reuse": declaration(False, not_applicable),
        "authorization": declaration(False, not_applicable),
        "ui_feedback": declaration(False, not_applicable),
        "explanation": declaration(True, "Outputs disclose the specific reason or basis for a decision."),
    }
    rationale_obligations = [
        obligation("rationale_success", "success", ["ordinary_success"]),
        obligation(
            "rationale_negative",
            "explanation",
            ["negative_input"],
            field="/evidence/reason",
            reason_fields=["/evidence/reason"],
        ),
    ]
    return {
        "schema": "forge-coverage/1",
        "plan_hash": flowctl.digest(plan),
        "entries": [
            entry("operation_result", "behavior", behavior_applicability, behavior_obligations, "Input-to-result branches for the bounded operation."),
            entry("decision_rationale", "rationale", rationale_applicability, rationale_obligations, "Evidence output states why a decision was made."),
        ],
    }


class CoverageCheckTests(unittest.TestCase):
    def test_complete_six_case_matrix_passes(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        self.assertEqual(evalplan.validate(plan), {"valid": True, "errors": []})
        self.assertEqual(coveragecheck.assess(plan, coverage), {"valid": True, "errors": []})

    def test_example_sidecar_is_bound_to_the_example_plan(self):
        plan = evalplan.load(ROOT / "assets" / "example-plan.json")
        coverage = coveragecheck._json_load_strict(ROOT / "assets" / "example-coverage.json")
        self.assertEqual(coverage["plan_hash"], flowctl.digest(plan))
        self.assertEqual(coveragecheck.assess(plan, coverage), {"valid": True, "errors": []})

    def test_missing_applicable_negative_branch_is_rejected(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        coverage["entries"][0]["obligations"] = [
            item for item in coverage["entries"][0]["obligations"] if item["kind"] != "negative"
        ]
        result = coveragecheck.assess(plan, coverage)
        self.assertFalse(result["valid"])
        self.assertIn("applicable dimension is missing obligation kind(s): negative", "\n".join(result["errors"]))

    def test_authorization_requires_both_allowed_and_denied(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        coverage["entries"][0]["obligations"] = [
            item for item in coverage["entries"][0]["obligations"] if item["kind"] != "authorization_denied"
        ]
        message = "\n".join(coveragecheck.assess(plan, coverage)["errors"])
        self.assertIn("applicable dimension is missing obligation kind(s): authorization_denied", message)

    def test_unknown_case_and_criterion_are_rejected(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        coverage["entries"][0]["criterion_id"] = "not_in_plan"
        coverage["entries"][0]["obligations"][0]["case_ids"] = ["not_in_plan"]
        message = "\n".join(coveragecheck.assess(plan, coverage)["errors"])
        self.assertIn("unknown criterion ID", message)
        self.assertIn("unknown case ID", message)

    def test_optional_only_case_cannot_discharge_an_obligation(self):
        plan = complete_plan()
        plan["cases"][1]["required"] = False
        coverage = complete_coverage(plan)
        message = "\n".join(coveragecheck.assess(plan, coverage)["errors"])
        self.assertIn("is optional; branch obligations require required cases", message)

    def test_optional_criterion_cannot_discharge_required_branch_coverage(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        coverage["entries"][0]["criterion_id"] = "optional_format"
        result = coveragecheck.assess(plan, coverage)
        message = "\n".join(result["errors"])
        self.assertIn("is optional and cannot discharge required branch coverage", message)
        self.assertIn("missing required criterion mapping", message)

    def test_same_case_or_same_input_fixture_cannot_stand_for_two_branches(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        negative = next(item for item in coverage["entries"][0]["obligations"] if item["kind"] == "negative")
        negative["case_ids"] = ["ordinary_success"]
        message = "\n".join(coveragecheck.assess(plan, coverage)["errors"])
        self.assertIn("distinct 'success'/'negative' branches reuse case(s)", message)

        plan = complete_plan()
        plan["cases"][1]["inputs"] = copy.deepcopy(plan["cases"][0]["inputs"])
        coverage = complete_coverage(plan)
        message = "\n".join(coveragecheck.assess(plan, coverage)["errors"])
        self.assertIn("distinct 'success'/'negative' branches have identical input fixture", message)

    def test_empty_expected_object_and_expected_equal_to_inputs_are_rejected(self):
        plan = complete_plan()
        plan["cases"][0]["expected"] = {}
        message = "\n".join(coveragecheck.assess(plan, complete_coverage(plan))["errors"])
        self.assertIn("expected output must not be empty", message)

        plan = complete_plan()
        plan["cases"][0]["expected"] = copy.deepcopy(plan["cases"][0]["inputs"])
        coverage = complete_coverage(plan)
        coverage["entries"][0]["obligations"][0]["expected_fields"] = ["/mode"]
        message = "\n".join(coveragecheck.assess(plan, coverage)["errors"])
        self.assertIn("expected output is identical to inputs", message)

    def test_plan_hash_must_bind_the_complete_plan(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        coverage["plan_hash"] = "0" * 64
        message = "\n".join(coveragecheck.assess(plan, coverage)["errors"])
        self.assertIn("does not match the canonical complete plan digest", message)

    def test_explanation_requires_specific_reason_or_basis_fields(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        reason_case = next(case for case in plan["cases"] if case["id"] == "negative_input")
        reason_case["expected"]["evidence"]["reason"] = "   "
        coverage["plan_hash"] = flowctl.digest(plan)
        message = "\n".join(coveragecheck.assess(plan, coverage)["errors"])
        self.assertIn("needs a specific nonempty reason/basis expectation", message)

    def test_cross_cutting_success_obligations_can_share_one_real_journey(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        # UI and explanation are output dimensions of this authorized success journey.
        journey = next(case for case in plan["cases"] if case["id"] == "ordinary_success")
        journey["inputs"] = {"mode": "send", "authorized": True, "text": "draft"}
        journey["expected"]["result"]["state"] = "sent"
        journey["expected"]["evidence"]["reason"] = "The user approved sending this exact draft."
        journey["expected"]["ui"] = {"confirmation": "Message sent."}
        coverage = complete_coverage(plan)
        behavior = coverage["entries"][0]
        behavior["applicability"]["ui_feedback"] = declaration(
            True, "A visible confirmation is returned after an authorized send."
        )
        allowed = next(item for item in behavior["obligations"] if item["kind"] == "authorization_allowed")
        allowed["case_ids"] = ["ordinary_success"]
        behavior["obligations"].append(
            obligation(
                "visible_confirmation",
                "ui_feedback",
                ["ordinary_success"],
                field="/ui/confirmation",
                ui_fields=["/ui/confirmation"],
            )
        )
        rationale = coverage["entries"][1]
        explanation = next(item for item in rationale["obligations"] if item["kind"] == "explanation")
        explanation["case_ids"] = ["ordinary_success"]
        self.assertTrue(coveragecheck.assess(plan, coverage)["valid"])

    def test_backend_matrix_does_not_need_ui_fields_but_declared_ui_does(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        self.assertTrue(coveragecheck.assess(plan, coverage)["valid"])
        coverage["entries"][0]["applicability"]["ui_feedback"] = declaration(
            True, "A visible confirmation is returned after an authorized send."
        )
        message = "\n".join(coveragecheck.assess(plan, coverage)["errors"])
        self.assertIn("applicable dimension is missing obligation kind(s): ui_feedback", message)

    def test_authorization_allow_and_deny_cannot_share_the_same_input(self):
        plan = complete_plan()
        plan["cases"][5]["inputs"] = copy.deepcopy(plan["cases"][4]["inputs"])
        coverage = complete_coverage(plan)
        message = "\n".join(coveragecheck.assess(plan, coverage)["errors"])
        self.assertIn("distinct 'authorization_allowed'/'authorization_denied' branches have identical input fixture", message)

    def test_strict_loader_rejects_duplicate_keys_and_nonfinite_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.json"
            for raw in (
                '{"schema":"forge-coverage/1","schema":"forge-coverage/1"}',
                '{"plan_hash":NaN}',
                '{"plan_hash":1e999}',
            ):
                path.write_text(raw, encoding="utf-8")
                with self.subTest(raw=raw), self.assertRaises(flowctl.FlowError):
                    coveragecheck._json_load_strict(path)

    def test_cli_prints_validity_and_machine_readable_errors_to_stdout(self):
        plan = complete_plan()
        coverage = complete_coverage(plan)
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.json"
            coverage_path = Path(directory) / "coverage.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            coverage_path.write_text(json.dumps(coverage), encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts" / "coveragecheck.py"), "validate", str(plan_path), str(coverage_path)]
            passed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            self.assertIn("valid: forge-coverage/1", passed.stdout)

            coverage["plan_hash"] = "0" * 64
            coverage_path.write_text(json.dumps(coverage), encoding="utf-8")
            rejected = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("error: coverage.plan_hash", rejected.stdout)


if __name__ == "__main__":
    unittest.main()
