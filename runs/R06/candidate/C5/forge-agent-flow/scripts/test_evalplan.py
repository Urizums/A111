"""Portable unit tests for evalplan's schema, lock, and strict JSON behavior."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import evalplan
import flowctl


def complete_plan():
    return {
        "schema": "forge-eval/1",
        "id": "meeting_eval",
        "criteria": [
            {
                "id": "quotes",
                "kind": "machine",
                "required": True,
                "assertion": "Each quote is copied exactly.",
            },
            {
                "id": "commitments",
                "kind": "human",
                "required": True,
                "assertion": "Only explicit actions are included.",
            },
            {
                "id": "formatting",
                "kind": "machine",
                "required": False,
                "assertion": "The actions use the declared fields.",
            },
        ],
        "cases": [
            {
                "id": "explicit_actions",
                "inputs": {"notes": "Ari will send it. Please review the draft."},
                "expected": {
                    "artifacts": {
                        "actions": [
                            {
                                "task": "send it",
                                "owner": "Ari",
                                "due": None,
                                "source_quote": "Ari will send it.",
                            },
                            {
                                "task": "review the draft",
                                "owner": None,
                                "due": None,
                                "source_quote": "Please review the draft.",
                            },
                        ]
                    },
                    "evidence": {"domain": "meeting_action_extraction"},
                },
                "expected_status": "completed",
                "criteria": ["quotes", "commitments", "formatting"],
                "required": True,
            },
            {
                "id": "no_actions",
                "inputs": {"notes": "They discussed possible venues."},
                "expected": {"artifacts": {"actions": []}},
                "expected_status": "completed",
                "criteria": ["quotes", "commitments"],
                "required": False,
            },
        ],
        "baseline": "One-agent meeting action extraction with the minimal flow contract.",
        "limitations": ["Expected values are descriptive fixtures, not execution instructions."],
    }


class EvalPlanTests(unittest.TestCase):
    def test_complete_plan_lock_round_trip_and_copy_isolation(self):
        plan = complete_plan()
        self.assertEqual(evalplan.validate(plan), {"valid": True, "errors": []})

        lock = evalplan.make_lock(plan)
        self.assertEqual(set(lock), {"plan", "plan_hash"})
        self.assertEqual(lock["plan_hash"], flowctl.digest(lock["plan"]))
        self.assertEqual(lock["plan"], plan)

        plan["cases"][0]["inputs"]["notes"] = "changed after lock"
        self.assertEqual(lock["plan"]["cases"][0]["inputs"]["notes"], "Ari will send it. Please review the draft.")

        loaded = evalplan.read_lock(lock)
        lock["plan"]["cases"][0]["expected"]["artifacts"]["actions"].clear()
        self.assertEqual(len(loaded["cases"][0]["expected"]["artifacts"]["actions"]), 2)

    def test_example_plan_is_complete_and_matches_package_criteria(self):
        plan = evalplan.load(ROOT / "assets" / "example-plan.json")
        with (ROOT / "assets" / "example-package.json").open(encoding="utf-8") as stream:
            package = json.load(stream)
        self.assertEqual(plan["criteria"], package["acceptance"]["criteria"])
        self.assertEqual(plan["cases"][0]["expected_status"], "completed")
        action = plan["cases"][0]["expected"]["artifacts"]["actions"][1]
        self.assertIsNone(action["owner"])
        self.assertIsNone(action["due"])
        self.assertIn("source_quote", action)
        self.assertEqual(plan["cases"][1]["expected"]["artifacts"]["actions"], [])

    def test_summary_case_missing_inputs_and_expected_is_rejected(self):
        plan = complete_plan()
        del plan["cases"][0]["inputs"]
        del plan["cases"][0]["expected"]
        result = evalplan.validate(plan)
        self.assertFalse(result["valid"])
        self.assertTrue(any("plan.cases[0]: missing required key(s): expected, inputs" in e for e in result["errors"]))
        with self.assertRaises(flowctl.FlowError):
            evalplan.require_valid(plan)

    def test_references_duplicates_and_required_coverage_are_checked(self):
        duplicate = complete_plan()
        duplicate["criteria"][1]["id"] = "quotes"
        duplicate["cases"].append(copy.deepcopy(duplicate["cases"][0]))
        duplicate["cases"][1]["criteria"] = ["quotes", "quotes", "unknown"]
        result = evalplan.validate(duplicate)
        message = "\n".join(result["errors"])
        self.assertIn("duplicate criterion ID", message)
        self.assertIn("duplicate case ID", message)
        self.assertIn("duplicate criterion reference", message)
        self.assertIn("unknown criterion ID", message)

        uncovered = complete_plan()
        uncovered["cases"][0]["criteria"] = ["formatting"]
        uncovered["cases"][1]["criteria"] = ["quotes", "commitments"]
        result = evalplan.validate(uncovered)
        message = "\n".join(result["errors"])
        self.assertIn("required case must include at least one required criterion", message)
        self.assertIn("required criterion 'quotes' is not covered by a required case", message)
        self.assertIn("required criterion 'commitments' is not covered by a required case", message)

    def test_wrong_field_types_are_reported_without_tracebacks(self):
        plan = complete_plan()
        plan["id"] = ["not", "an", "id"]
        plan["criteria"][0]["required"] = 1
        plan["cases"][0]["inputs"] = []
        plan["cases"][0]["expected"] = None
        plan["cases"][0]["required"] = "yes"
        plan["limitations"] = ["ok", 3]
        result = evalplan.validate(plan)
        self.assertFalse(result["valid"])
        self.assertGreaterEqual(len(result["errors"]), 6)
        self.assertTrue(all(type(error) is str for error in result["errors"]))

    def test_load_rejects_duplicate_keys_and_nonfinite_numbers(self):
        malformed = {
            "duplicate": '{"schema":"forge-eval/1","schema":"forge-eval/1"}',
            "nan": '{"schema":"forge-eval/1","baseline":NaN}',
            "infinity": '{"schema":"forge-eval/1","baseline":Infinity}',
            "negative_infinity": '{"schema":"forge-eval/1","baseline":-Infinity}',
            "overflow_exponent": '{"schema":"forge-eval/1","baseline":1e999}',
        }
        with tempfile.TemporaryDirectory() as directory:
            for name, contents in malformed.items():
                with self.subTest(name=name):
                    path = Path(directory) / f"{name}.json"
                    path.write_text(contents, encoding="utf-8")
                    with self.assertRaises(flowctl.FlowError):
                        evalplan.load(path)

    def test_read_lock_rejects_plan_or_hash_tampering(self):
        lock = evalplan.make_lock(complete_plan())

        changed_plan = copy.deepcopy(lock)
        changed_plan["plan"]["baseline"] = "altered"
        with self.assertRaises(flowctl.FlowError):
            evalplan.read_lock(changed_plan)

        changed_hash = copy.deepcopy(lock)
        changed_hash["plan_hash"] = "0" * 64
        with self.assertRaises(flowctl.FlowError):
            evalplan.read_lock(changed_hash)

        invalid_plan = copy.deepcopy(lock)
        del invalid_plan["plan"]["cases"][0]["inputs"]
        invalid_plan["plan_hash"] = flowctl.digest(invalid_plan["plan"])
        with self.assertRaises(flowctl.FlowError):
            evalplan.read_lock(invalid_plan)

        extra_key = dict(lock, summary="digest-only placeholder")
        with self.assertRaises(flowctl.FlowError):
            evalplan.read_lock(extra_key)


if __name__ == "__main__":
    unittest.main()
