#!/usr/bin/env python3
"""Regression checks for the host-driven project plan controller."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import evalplan
import projectctl as p

ROOT = Path(__file__).resolve().parents[1]


class ProjectCtlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = p.load_json(ROOT / "assets" / "example-project-plan.json")
        self.state_path = self.root / "state.json"
        p.init(self.plan, self.state_path)
        self.state = p.load_state(self.state_path)

    def evidence(self, label, content=None):
        path = self.root / (label.replace("/", "_") + ".txt")
        path.write_text(content if content is not None else label, encoding="utf-8")
        return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def evaluation_plan(self, criterion_id="a_runtime", expected=1):
        return {
            "schema": "forge-eval/1", "id": "sample_eval",
            "criteria": [{"id": criterion_id, "kind": "machine", "required": True,
                          "assertion": "The runtime output matches the expected value."}],
            "cases": [{"id": "case_main", "inputs": {"value": 1},
                       "expected": {"value": expected}, "expected_status": "completed",
                       "criteria": [criterion_id], "required": True}],
            "baseline": "An isolated controller fixture.",
            "limitations": ["Fixture only; no application or agent runtime is exercised."],
        }

    def results(self, task_id, levels=None, bad_hash=False, include=None, state=None):
        state = state or self.state
        task = next(task for task in state["plan"]["tasks"] if task["id"] == task_id)
        criteria = {item["id"]: item for item in state["plan"]["acceptance"]}
        mapped = task["acceptance_ids"] if include is None else include
        out = {}
        for aid in mapped:
            level = (levels or {}).get(aid, criteria[aid]["level"])
            ref = self.evidence(f"{task_id}-{aid}")
            if bad_hash:
                ref["sha256"] = "0" * 64
            out[aid] = {"status": "pass", "level": level, "evidence": [ref]}
        result = {"acceptance_results": out}
        if state.get("evaluation_plan_lock") is not None:
            result["evaluation_plan_hash"] = state["evaluation_plan_lock"]["plan_hash"]
        return result

    def start(self, task_id, state=None):
        return p.begin(state or self.state, task_id)

    def finish_done(self, task_id, begun=None, results=None, state=None):
        state = state or self.state
        begun = begun or self.start(task_id, state=state)
        return p.finish(state, task_id, begun["attempt_id"], "done",
                        results=results if results is not None else self.results(task_id, state=state))

    def complete_required_graph(self, state=None):
        state = state or self.state
        for task_id in ("inspect", "implement", "review"):
            self.finish_done(task_id, state=state)

    def test_valid_plan_and_dependencies_and_duplicate_responses(self):
        self.assertTrue(p.validate_plan(self.plan)["valid"])
        ready = p.next_tasks(self.state)
        self.assertEqual([item["task_id"] for item in ready["ready"]], ["inspect", "context_notes"])
        with self.assertRaisesRegex(p.ProjectError, "dependencies are not done"):
            p.begin(self.state, "implement")

        begun = self.start("inspect")
        with self.assertRaisesRegex(p.ProjectError, "already running"):
            p.begin(self.state, "inspect")
        self.finish_done("inspect", begun=begun)
        with self.assertRaisesRegex(p.ProjectError, "Stale or duplicate"):
            p.finish(self.state, "inspect", begun["attempt_id"], "done",
                     results=self.results("inspect"))
        self.assertEqual([item["task_id"] for item in p.next_tasks(self.state)["ready"]],
                         ["implement", "context_notes"])

    def test_wrong_evidence_hash_missing_acceptance_and_wrong_level_are_rejected(self):
        begun = self.start("inspect")
        with self.assertRaisesRegex(p.ProjectError, "exactly"):
            p.finish(self.state, "inspect", begun["attempt_id"], "done",
                     results={"acceptance_results": {}})
        with self.assertRaisesRegex(p.ProjectError, "SHA256 does not match"):
            p.finish(self.state, "inspect", begun["attempt_id"], "done",
                     results=self.results("inspect", bad_hash=True))
        self.finish_done("inspect", begun=begun)

        begun = self.start("implement")
        with self.assertRaisesRegex(p.ProjectError, "does not satisfy required runtime"):
            p.finish(self.state, "implement", begun["attempt_id"], "done",
                     results=self.results("implement", levels={"a_runtime": "review"}))

    def test_resume_reconciles_running_attempt_without_redispatch(self):
        begun = self.start("inspect")
        p.save(self.state_path, self.state)
        recovered = p.load_state(self.state_path)
        nxt = p.next_tasks(recovered)
        self.assertEqual(nxt["status"], "ready")
        self.assertEqual(nxt["reconcile"][0]["attempt_id"], begun["attempt_id"])
        self.assertEqual(nxt["ready"][0]["task_id"], "context_notes")
        with self.assertRaisesRegex(p.ProjectError, "already running"):
            p.begin(recovered, "inspect")

    def test_blocked_branch_does_not_hide_independent_ready_work(self):
        begun = self.start("inspect")
        p.finish(self.state, "inspect", begun["attempt_id"], "blocked", reason="Host access unavailable.")
        nxt = p.next_tasks(self.state)
        self.assertEqual(nxt["status"], "ready")
        self.assertEqual([item["task_id"] for item in nxt["ready"]], ["context_notes"])
        self.assertEqual(nxt["blockers"][0]["task_id"], "inspect")
        self.assertEqual(p.status(self.state)["tokens"], None)
        self.assertEqual(p.status(self.state)["cost"], None)

    def test_two_repairs_are_bounded_and_noop_revision_cannot_reset_them(self):
        for attempt_number in range(3):
            begun = self.start("inspect")
            p.finish(self.state, "inspect", begun["attempt_id"], "failed",
                     reason=f"Fixture failure {attempt_number + 1}.")
        current = self.state["tasks"]["inspect"]
        self.assertEqual(current["status"], "blocked")
        self.assertEqual(current["repair_attempts"], 2)
        self.assertNotIn("inspect", [item["task_id"] for item in p.next_tasks(self.state)["ready"]])
        with self.assertRaisesRegex(p.ProjectError, "exhausted"):
            p.begin(self.state, "inspect")
        with self.assertRaisesRegex(p.ProjectError, "no-content revision"):
            p.revise(self.state, deepcopy(self.plan), ["inspect"], "Try again.")

    def test_completed_results_are_preserved_and_revision_cascades_invalidation(self):
        self.complete_required_graph()
        self.finish_done("context_notes")
        self.assertEqual(self.state["status"], "completed")
        before_attempts = len(self.state["tasks"]["implement"]["attempts"])
        changed = deepcopy(self.plan)
        changed["tasks"][1]["title"] = "Implement the scoped change and run runtime checks"
        with self.assertRaisesRegex(p.ProjectError, "explicit --invalidate"):
            p.revise(self.state, changed, [], "Clarify runtime implementation.")
        with self.assertRaisesRegex(p.ProjectError, "review"):
            p.revise(self.state, changed, ["implement"], "Clarify runtime implementation.")

        result = p.revise(self.state, changed, ["implement", "review"],
                          "Clarify runtime implementation.")
        self.assertEqual(result["invalidated_tasks"], ["implement", "review"])
        self.assertEqual(self.state["tasks"]["inspect"]["status"], "done")
        self.assertEqual(self.state["tasks"]["implement"]["status"], "todo")
        self.assertEqual(len(self.state["tasks"]["implement"]["attempts"]), before_attempts)
        self.assertEqual(self.state["revision_history"][0]["previous_plan"], self.plan)
        self.assertEqual(self.state["status"], "active")
        self.assertEqual(p.next_tasks(self.state)["ready"][0]["task_id"], "implement")

    def test_revision_can_add_new_scoped_nodes_without_erasing_history(self):
        self.finish_done("inspect")
        expanded = deepcopy(self.plan)
        expanded["requirements"].append({
            "id": "req_docs", "text": "Record a design note.",
            "origin": "default", "basis": "Illustrative added requirement.",
            "acceptance_ids": ["a_docs"],
        })
        expanded["acceptance"].append({
            "id": "a_docs", "assertion": "A design note is recorded.",
            "required": True, "level": "static",
        })
        expanded["tasks"].append({
            "id": "design_note", "title": "Write a design note",
            "depends_on": ["inspect"], "owner": None,
            "write_paths": ["docs/"], "acceptance_ids": ["a_docs"],
        })
        result = p.revise(self.state, expanded, [], "Add a design note deliverable.")
        self.assertTrue(result["revised"])
        self.assertEqual(self.state["tasks"]["inspect"]["status"], "done")
        self.assertEqual(self.state["tasks"]["design_note"]["status"], "todo")
        self.assertIn("design_note", p.status(self.state)["todo"])

    def test_required_runtime_cannot_be_replaced_by_review(self):
        changed = deepcopy(self.plan)
        changed["acceptance"][1]["level"] = "review"
        with self.assertRaisesRegex(p.ProjectError, "cannot remove the runtime requirement"):
            p.revise(self.state, changed, [], "Attempt to replace runtime with review.")

    def test_evaluation_binding_is_authoritative_and_results_must_match_its_hash(self):
        eval_path = self.root / "acceptance.json"
        evaluation = self.evaluation_plan()
        eval_path.write_text(json.dumps(evaluation), encoding="utf-8")
        bound_path = self.root / "bound-state.json"
        p.init(self.plan, bound_path, evaluation, eval_path)
        state = p.load_state(bound_path)
        locked_hash = state["evaluation_plan_lock"]["plan_hash"]
        self.assertEqual(locked_hash, evalplan.make_lock(evaluation)["plan_hash"])

        begun = p.begin(state, "inspect")
        self.finish_done("inspect", begun=begun, state=state)
        p.save(bound_path, state)

        changed_external = self.evaluation_plan(expected=2)
        eval_path.write_text(json.dumps(changed_external), encoding="utf-8")
        recovered = p.load_state(bound_path)
        binding = p.status(recovered)["evaluation_plan_binding"]
        self.assertEqual(binding["status"], "bound")
        self.assertEqual(binding["authoritative"], "embedded_state_lock")
        self.assertEqual(binding["plan_hash"], locked_hash)
        self.assertEqual(binding["source_status"], "drifted")
        self.assertEqual(p.status(recovered)["product_acceptance_status"], "not_assessed")

        begun = p.begin(recovered, "implement")
        wrong = self.results("implement", state=recovered)
        wrong["evaluation_plan_hash"] = p.digest(changed_external)
        with self.assertRaisesRegex(p.ProjectError, "does not match the authoritative state lock"):
            p.finish(recovered, "implement", begun["attempt_id"], "done", results=wrong)
        correct = self.results("implement", state=recovered)
        p.finish(recovered, "implement", begun["attempt_id"], "done", results=correct)
        p.save(bound_path, recovered)
        self.assertEqual(p.load_state(bound_path)["tasks"]["implement"]["status"], "done")

    def test_bound_revision_invalidates_runtime_tasks_and_descendants_and_keeps_old_lock(self):
        old_eval = self.evaluation_plan()
        old_source = self.root / "old-eval.json"
        old_source.write_text(json.dumps(old_eval), encoding="utf-8")
        bound_path = self.root / "bound-revision.json"
        p.init(self.plan, bound_path, old_eval, old_source)
        state = p.load_state(bound_path)
        self.complete_required_graph(state)
        self.finish_done("context_notes", state=state)
        self.assertEqual(state["status"], "completed")

        new_eval = self.evaluation_plan(expected=2)
        new_source = self.root / "new-eval.json"
        new_source.write_text(json.dumps(new_eval), encoding="utf-8")
        with self.assertRaisesRegex(p.ProjectError, "explicit --invalidate.*implement, review"):
            p.revise(state, self.plan, [], "Change the frozen runtime case.",
                     evaluation_plan=new_eval, evaluation_source=new_source)
        revision = p.revise(state, self.plan, ["implement", "review"],
                            "Change the frozen runtime case.",
                            evaluation_plan=new_eval, evaluation_source=new_source)
        self.assertEqual(revision["invalidated_tasks"], ["implement", "review"])
        self.assertEqual(state["tasks"]["inspect"]["status"], "done")
        self.assertEqual(state["tasks"]["context_notes"]["status"], "done")
        event = state["revision_history"][-1]
        self.assertEqual(event["previous_evaluation_plan_lock"]["plan"], old_eval)
        self.assertEqual(event["new_evaluation_plan_lock"]["plan"], new_eval)
        self.assertEqual(state["tasks"]["implement"]["attempts"][-1]["evaluation_plan_hash"],
                         p.digest(old_eval))
        self.assertEqual(state["evaluation_plan_lock"]["plan_hash"], p.digest(new_eval))
        p.save(bound_path, state)
        self.assertEqual(p.load_state(bound_path)["status"], "active")

    def test_bound_plan_requires_runtime_criteria_but_not_static_or_review_cases(self):
        wrong = self.evaluation_plan(criterion_id="a_plan")
        with self.assertRaisesRegex(p.ProjectError, "required criteria for runtime acceptance IDs: a_runtime"):
            p.init(self.plan, self.root / "bad-binding.json", wrong)

        correctly_mapped = self.evaluation_plan(criterion_id="a_runtime")
        state_path = self.root / "good-binding.json"
        p.init(self.plan, state_path, correctly_mapped)
        result = p.status(p.load_state(state_path))
        self.assertEqual(result["evaluation_plan_binding"]["status"], "bound")
        self.assertEqual(result["evaluation_plan_binding"]["plan_hash"], p.digest(correctly_mapped))

    def test_overlapping_active_write_paths_are_blocked_but_safe_ready_work_remains(self):
        plan = deepcopy(self.plan)
        plan["tasks"][0]["write_paths"] = ["src/"]
        plan["tasks"][3]["write_paths"] = ["src/module.py"]
        plan["tasks"].append({"id": "safe_task", "title": "Write an unrelated log",
                              "depends_on": [], "owner": None,
                              "write_paths": ["logs/run.txt"], "acceptance_ids": []})
        state_path = self.root / "conflict-state.json"
        p.init(plan, state_path)
        state = p.load_state(state_path)
        begun = p.begin(state, "inspect")
        nxt = p.next_tasks(state)
        ready_ids = {item["task_id"] for item in nxt["ready"]}
        self.assertIn("safe_task", ready_ids)
        self.assertNotIn("context_notes", ready_ids)
        conflict = next(item for item in nxt["blockers"] if item["task_id"] == "context_notes")
        self.assertEqual(conflict["status"], "write_conflict")
        self.assertEqual(conflict["conflicts_with"][0]["task_id"], "inspect")
        with self.assertRaisesRegex(p.ProjectError, "active write-path conflicts"):
            p.begin(state, "context_notes")
        p.begin(state, "safe_task")
        self.assertEqual(state["tasks"]["inspect"]["active_attempt_id"], begun["attempt_id"])

        sequential = deepcopy(self.plan)
        sequential["tasks"][0]["write_paths"] = ["shared/"]
        sequential["tasks"][1]["write_paths"] = ["shared/"]
        sequential_path = self.root / "sequential.json"
        p.init(sequential, sequential_path)
        sequential_state = p.load_state(sequential_path)
        first = p.begin(sequential_state, "inspect")
        p.finish(sequential_state, "inspect", first["attempt_id"], "done",
                 results=self.results("inspect", state=sequential_state))
        p.begin(sequential_state, "implement")

    def test_invalidated_historical_evidence_drift_is_reported_but_does_not_block(self):
        begun = self.start("inspect")
        self.finish_done("inspect", begun=begun)
        attempt = self.state["tasks"]["inspect"]["attempts"][-1]
        evidence = attempt["acceptance_results"]["a_plan"]["evidence"][0]
        evidence_path = Path(evidence["path"])
        missing_ref = self.evidence("historical-evidence-to-delete")
        attempt["acceptance_results"]["a_plan"]["evidence"].append(missing_ref)
        p.save(self.state_path, self.state)
        evidence_path.write_text("changed historical bytes", encoding="utf-8")
        with self.assertRaisesRegex(p.ProjectError, "SHA256 does not match"):
            p.load_state(self.state_path)

        changed = deepcopy(self.plan)
        changed["tasks"][0]["title"] = "Inspect the refreshed target"
        p.revise(self.state, changed, ["inspect"], "Refresh the inspection task scope.")
        p.save(self.state_path, self.state)
        Path(missing_ref["path"]).unlink()
        recovered = p.load_state(self.state_path)
        warnings = p.status(recovered)["evidence_warnings"]
        self.assertTrue(any(item["attempt_id"] == attempt["attempt_id"] and
                            item["status"] == "changed" for item in warnings))
        self.assertTrue(any(item["attempt_id"] == attempt["attempt_id"] and
                            item["status"] == "missing" for item in warnings))
        self.assertEqual(p.next_tasks(recovered)["ready"][0]["task_id"], "inspect")

    def test_legacy_state_without_binding_is_not_configured(self):
        legacy = deepcopy(self.state)
        legacy.pop("evaluation_plan_lock")
        legacy_path = self.root / "legacy-state.json"
        p.save(legacy_path, legacy)
        loaded = p.load_state(legacy_path)
        report = p.status(loaded)
        self.assertEqual(report["evaluation_plan_binding"]["status"], "not_configured")
        self.assertEqual(report["product_acceptance_status"], "not_configured")

    def test_cli_binds_full_evaluation_plan_and_requires_hash_in_results(self):
        script = ROOT / "scripts" / "projectctl.py"
        plan_path = ROOT / "assets" / "example-project-plan.json"
        evaluation = self.evaluation_plan()
        evaluation_path = self.root / "evaluation.json"
        evaluation_path.write_text(json.dumps(evaluation), encoding="utf-8")
        state_path = self.root / "bound-cli-state.json"
        created = subprocess.run(
            [sys.executable, "-B", str(script), "init", str(plan_path), "--state", str(state_path),
             "--evaluation-plan", str(evaluation_path)],
            text=True, capture_output=True, check=False)
        self.assertEqual(created.returncode, 0, created.stderr)
        self.assertEqual(json.loads(created.stdout)["evaluation_plan_binding"]["plan_hash"],
                         p.digest(evaluation))

        begun = subprocess.run([sys.executable, "-B", str(script), "begin", "--state", str(state_path),
                                "--task", "inspect"], text=True, capture_output=True, check=False)
        self.assertEqual(begun.returncode, 0, begun.stderr)
        attempt = json.loads(begun.stdout)
        evidence = self.evidence("cli-bound-evidence")
        results_path = self.root / "cli-results.json"
        results_path.write_text(json.dumps({
            "evaluation_plan_hash": attempt["evaluation_plan_hash"],
            "acceptance_results": {"a_plan": {"status": "pass", "level": "static",
                                                  "evidence": [evidence]}},
        }), encoding="utf-8")
        finished = subprocess.run(
            [sys.executable, "-B", str(script), "finish", "--state", str(state_path),
             "--task", "inspect", "--attempt-id", attempt["attempt_id"], "--outcome", "done",
             "--results", str(results_path)], text=True, capture_output=True, check=False)
        self.assertEqual(finished.returncode, 0, finished.stderr)
        self.assertEqual(p.load_state(state_path)["tasks"]["inspect"]["status"], "done")

    def test_cli_validate_init_status_and_next(self):
        script = ROOT / "scripts" / "projectctl.py"
        plan_path = ROOT / "assets" / "example-project-plan.json"
        checked = subprocess.run([sys.executable, "-B", str(script), "validate", str(plan_path)],
                                 text=True, capture_output=True, check=False)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertTrue(json.loads(checked.stdout)["valid"])
        target = self.root / "cli-state.json"
        created = subprocess.run([sys.executable, "-B", str(script), "init", str(plan_path),
                                  "--state", str(target)], text=True, capture_output=True, check=False)
        self.assertEqual(created.returncode, 0, created.stderr)
        status = subprocess.run([sys.executable, "-B", str(script), "status",
                                 "--state", str(target)], text=True, capture_output=True, check=False)
        self.assertEqual(status.returncode, 0, status.stderr)
        payload = json.loads(status.stdout)
        self.assertEqual(payload["total"], 4)
        self.assertIsNone(payload["tokens"])
        nxt = subprocess.run([sys.executable, "-B", str(script), "next",
                              "--state", str(target)], text=True, capture_output=True, check=False)
        self.assertEqual(nxt.returncode, 0, nxt.stderr)
        self.assertEqual(json.loads(nxt.stdout)["status"], "ready")


if __name__ == "__main__":
    unittest.main()
