"""Regression tests for frozen-plan package execution and assessment."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import evalplan
import flowctl as flow
import packagectl as package


class PackageV2Tests(unittest.TestCase):
    def setUp(self):
        self.package = package.load(Path(__file__).resolve().parents[1] / "assets/example-package.json")
        self.plan = {
            "schema": "forge-eval/1",
            "id": "package_v2_contract",
            "criteria": [
                {"id": "output_shape", "kind": "machine", "required": True,
                 "assertion": "The output has the frozen shape."},
                {"id": "semantic_review", "kind": "human", "required": True,
                 "assertion": "Only explicit actions are included."},
                {"id": "optional_style", "kind": "human", "required": False,
                 "assertion": "The optional presentation preference is met."},
            ],
            "cases": [
                {"id": "no_actions", "inputs": {"notes": "No commitments."},
                 "expected": {"actions": []}, "expected_status": "completed",
                 "criteria": ["output_shape", "semantic_review"], "required": True},
                {"id": "explicit_action", "inputs": {"notes": "Kai will send the draft."},
                 "expected": {"actions": [{"task": "send the draft"}]},
                 "expected_status": "completed", "criteria": ["output_shape"], "required": True},
                {"id": "optional_case", "inputs": {"notes": "No action is stated."},
                 "expected": {"actions": []}, "expected_status": "completed",
                 "criteria": ["optional_style"], "required": False},
            ],
            "baseline": "One host agent extracts actions from supplied notes.",
            "limitations": ["Submitted semantic grades still require independent review."],
        }
        self.package["schema"] = "forge-package/2"
        self.package["acceptance"] = evalplan.make_lock(copy.deepcopy(self.plan))

    def check(self, criterion_id, status="pass"):
        criterion = next(c for c in self.plan["criteria"] if c["id"] == criterion_id)
        return {"id": criterion_id, "kind": criterion["kind"], "status": status,
                "evidence": ["fixture-inspection"] if status != "not_run" else []}

    def run_case(self, case_id, outcome="ok"):
        case = next(c for c in self.plan["cases"] if c["id"] == case_id)
        state = package.start(self.package, copy.deepcopy(case["inputs"]))
        dispatch = package.pending(self.package, state)
        self.assertEqual(dispatch["plan_hash"], self.package["acceptance"]["plan_hash"])
        response = {"invocation_id": dispatch["invocation_id"], "outcome": outcome,
                    "artifacts": {"actions": []} if outcome == "ok" else {},
                    "evidence": ["fixture-run"]}
        return package.advance(self.package, state, response)

    def case_result(self, case_id, checks=None, run=None):
        return {"case_id": case_id, "run": run,
                "checks": list(checks or [])}

    def results(self, case_rows):
        return {"package_hash": flow.digest(self.package),
                "plan_hash": self.package["acceptance"]["plan_hash"],
                "cases": case_rows}

    def full_results(self):
        return self.results([
            self.case_result("no_actions", [self.check("output_shape"), self.check("semantic_review")], self.run_case("no_actions")),
            self.case_result("explicit_action", [self.check("output_shape")], self.run_case("explicit_action")),
            self.case_result("optional_case", [self.check("optional_style")], self.run_case("optional_case")),
        ])

    def test_full_plan_validates_compiles_and_stays_bound_through_dispatch_and_checkpoint(self):
        validation = package.validate(self.package)
        self.assertTrue(validation["valid"], validation["errors"])
        self.assertEqual(validation["plan_hash"], self.package["acceptance"]["plan_hash"])
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "compiled"
            compiled = package.compile_package(self.package, out)
            self.assertEqual(compiled["plan_hash"], self.package["acceptance"]["plan_hash"])
            self.assertEqual(package.load(out / "package.json"), self.package)

        state = package.start(self.package, {"notes": "No commitments."})
        self.assertEqual(state["plan_hash"], self.package["acceptance"]["plan_hash"])
        self.assertEqual(state["input_hash"], flow.digest({"notes": "No commitments."}))
        dispatch = package.pending(self.package, state)
        self.assertEqual(dispatch["plan_hash"], state["plan_hash"])
        self.assertEqual(dispatch["input_hash"], state["input_hash"])
        self.assertNotIn("plan", dispatch)
        self.assertNotIn("expected", dispatch)
        response = {"invocation_id": dispatch["invocation_id"], "outcome": "ok",
                    "artifacts": {"actions": []}, "evidence": ["fixture-run"]}
        end = package.advance(self.package, state, response)
        self.assertEqual(end["plan_hash"], state["plan_hash"])
        self.assertEqual(end["input_hash"], state["input_hash"])
        self.assertEqual(package.pending(self.package, end)["plan_hash"], state["plan_hash"])

    def test_changed_or_rehashed_plan_and_checkpoint_binding_are_rejected(self):
        changed = copy.deepcopy(self.package)
        changed["acceptance"]["plan"]["cases"][0]["expected"]["actions"].append({"task": "forged"})
        self.assertFalse(package.validate(changed)["valid"])

        changed_hash = copy.deepcopy(self.package)
        changed_hash["acceptance"]["plan_hash"] = "0" * 64
        self.assertFalse(package.validate(changed_hash)["valid"])

        old = package.load(Path(__file__).resolve().parents[1] / "assets/example-package.json")
        old_state = package.start(old, {"notes": "No commitments."})
        forged_v2_shape = {**old_state,
                           "plan_hash": self.package["acceptance"]["plan_hash"],
                           "input_hash": flow.digest({"notes": "No commitments."})}
        with self.assertRaises(flow.FlowError):
            package.pending(self.package, forged_v2_shape)
        state = package.start(self.package, {"notes": "No commitments."})
        wrong_binding = copy.deepcopy(state)
        wrong_binding["plan_hash"] = "0" * 64
        with self.assertRaisesRegex(flow.FlowError, "Plan changed"):
            package.pending(self.package, wrong_binding)

    def test_v1_package_and_assessment_remain_compatible(self):
        old = package.load(Path(__file__).resolve().parents[1] / "assets/example-package.json")
        state = package.start(old, {"notes": "No commitments."})
        self.assertEqual(set(state), {"package_hash", "flow_state"})
        checks = [{"id": c["id"], "kind": c["kind"], "status": "pass", "evidence": ["fixture"]}
                  for c in old["acceptance"]["criteria"]]
        verdict = package.assess(old, {"package_hash": flow.digest(old), "checks": checks})
        self.assertEqual(verdict["verdict"], "pass")

    def test_missing_required_cases_or_criteria_are_pending(self):
        no_cases = self.results([])
        self.assertEqual(package.assess(self.package, no_cases)["verdict"], "pending")

        row = self.case_result("no_actions", [], self.run_case("no_actions"))
        outcome = package.assess(self.package, self.results([row]))
        self.assertEqual(outcome["verdict"], "pending")
        self.assertEqual(outcome["required_pending_checks"], [
            {"case_id": "no_actions", "criterion_id": "output_shape"},
            {"case_id": "no_actions", "criterion_id": "semantic_review"},
        ])

    def test_required_failure_cannot_be_hidden_by_other_passing_cases(self):
        rows = self.full_results()["cases"]
        rows[0]["checks"][0]["status"] = "fail"
        outcome = package.assess(self.package, self.results(rows))
        self.assertEqual(outcome["verdict"], "fail")
        self.assertEqual(outcome["required_failed_checks"], [
            {"case_id": "no_actions", "criterion_id": "output_shape"},
        ])

    def test_bad_inputs_hash_kind_duplicates_and_pass_without_complete_run_are_rejected(self):
        case_run = self.run_case("no_actions")
        wrong_input = copy.deepcopy(case_run)
        wrong_input["flow_state"]["artifacts"]["notes"] = "Different frozen input."
        with self.assertRaisesRegex(flow.FlowError, "input_hash"):
            package.assess(self.package, self.results([
                self.case_result("no_actions", [self.check("output_shape")], wrong_input)
            ]))

        wrong_hash = self.results([])
        wrong_hash["plan_hash"] = "0" * 64
        with self.assertRaisesRegex(flow.FlowError, "plan_hash"):
            package.assess(self.package, wrong_hash)

        wrong_kind = self.check("output_shape")
        wrong_kind["kind"] = "human"
        with self.assertRaisesRegex(flow.FlowError, "grader kind"):
            package.assess(self.package, self.results([
                self.case_result("no_actions", [wrong_kind], case_run)
            ]))

        duplicate = self.check("output_shape")
        with self.assertRaisesRegex(flow.FlowError, "duplicate criterion"):
            package.assess(self.package, self.results([
                self.case_result("no_actions", [duplicate, copy.deepcopy(duplicate)], case_run)
            ]))

        with self.assertRaisesRegex(flow.FlowError, "without a run"):
            package.assess(self.package, self.results([
                self.case_result("no_actions", [self.check("output_shape")], None)
            ]))

        in_progress = package.start(self.package, {"notes": "No commitments."})
        with self.assertRaisesRegex(flow.FlowError, "incomplete run"):
            package.assess(self.package, self.results([
                self.case_result("no_actions", [self.check("output_shape")], in_progress)
            ]))
        incomplete = package.assess(self.package, self.results([
            self.case_result("no_actions", [], in_progress)
        ]))
        self.assertEqual(incomplete["verdict"], "pending")
        self.assertIn("no_actions", incomplete["required_pending_cases"])

    def test_optional_case_or_criterion_gaps_are_limited(self):
        rows = self.full_results()["cases"]
        rows.pop()
        outcome = package.assess(self.package, self.results(rows))
        self.assertEqual(outcome["verdict"], "limited")
        self.assertTrue(any(gap.get("case_id") == "optional_case" for gap in outcome["optional_gaps"]))

        rows = self.full_results()["cases"]
        rows[-1]["checks"] = []
        self.assertEqual(package.assess(self.package, self.results(rows))["verdict"], "limited")

    def test_required_terminal_status_mismatch_is_failure(self):
        failed = self.run_case("no_actions", outcome="error")
        row = self.case_result("no_actions", [self.check("output_shape", "fail")], failed)
        outcome = package.assess(self.package, self.results([row]))
        self.assertEqual(outcome["verdict"], "fail")
        self.assertEqual(outcome["required_failed_cases"][0]["case_id"], "no_actions")

    def test_complete_standard_case_flow_passes_with_truth_boundary(self):
        outcome = package.assess(self.package, self.full_results())
        self.assertEqual(outcome["verdict"], "pass")
        self.assertIn("real model identity", outcome["boundary"])
        self.assertIn("semantic truth", outcome["boundary"])

    def test_malformed_schema_type_and_deep_json_fail_cleanly(self):
        malformed = copy.deepcopy(self.package)
        malformed["schema"] = []
        self.assertFalse(package.validate(malformed)["valid"])
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "deep.json"
            source.write_text("[" * 1200 + "0" + "]" * 1200, encoding="utf-8")
            result = subprocess.run([sys.executable, package.__file__, "validate", str(source)],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
