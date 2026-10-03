"""Portable tests for explicit smoke evidence content inspection."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import smoke_evidence
import smokecheck
from test_smokecheck import complete_plan, complete_results


def _dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def make_evidence(root, plan=None, results=None):
    plan = plan or complete_plan()
    results = results or complete_results(plan)
    entries = []
    for run in results["runs"]:
        ref = run["evidence"][0]
        if run["round"] == 1:
            media_type = "text/plain"
            relative = f"evidence/runs/{run['journey_id']}-r{run['round']}.txt"
            marker = f"smoke-run:{run['candidate_id']}:{run['journey_id']}:round-{run['round']}"
            content = f"{marker}\nObserved expected outcome.\n".encode("utf-8")
            checks = [
                {"kind": "contains_binding"},
                {"kind": "contains", "value": "Observed expected outcome"},
            ]
        else:
            media_type = "application/json"
            relative = f"evidence/runs/{run['journey_id']}-r{run['round']}.json"
            document = {
                "candidate_id": run["candidate_id"],
                "journey_id": run["journey_id"],
                "round": run["round"],
                "observation": "expected_state_visible",
            }
            content = json.dumps(document, sort_keys=True).encode("utf-8")
            checks = [{"kind": "json_equals", "field": "observation", "value": "expected_state_visible"}]
        file_path = root / relative
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        entries.append({
            "ref": ref,
            "purpose": "run",
            "path": relative,
            "sha256": hashlib.sha256(content).hexdigest(),
            "media_type": media_type,
            "candidate_id": run["candidate_id"],
            "journey_id": run["journey_id"],
            "round": run["round"],
            "checks": checks,
        })
    for regression in results["regressions"]:
        ref = regression["evidence"][0]
        relative = f"evidence/regressions/{regression['behavior_id']}.json"
        document = {
            "candidate_id": regression["candidate_id"],
            "behavior_id": regression["behavior_id"],
            "observation": "protected_behavior_preserved",
        }
        content = json.dumps(document, sort_keys=True).encode("utf-8")
        file_path = root / relative
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        entries.append({
            "ref": ref,
            "purpose": "regression",
            "path": relative,
            "sha256": hashlib.sha256(content).hexdigest(),
            "media_type": "application/json",
            "candidate_id": regression["candidate_id"],
            "behavior_id": regression["behavior_id"],
            "checks": [{
                "kind": "json_equals",
                "field": "observation",
                "value": "protected_behavior_preserved",
            }],
        })
    manifest = {
        "schema": smoke_evidence.MANIFEST_SCHEMA,
        "plan_hash": smokecheck.flowctl.digest(plan),
        "candidate_id": plan["candidate_id"],
        "baseline_id": plan["baseline"]["id"],
        "entries": entries,
    }
    return plan, results, manifest


class SmokeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan, self.results, self.manifest = make_evidence(self.root)
        self.manifest_path = self.root / "manifest.json"
        _dump(self.manifest_path, self.manifest)

    def tearDown(self):
        self.temp.cleanup()

    def assess(self, plan=None, results=None, manifest=None):
        return smoke_evidence.assess(
            plan or self.plan,
            results or self.results,
            manifest or self.manifest_path,
        )

    def entry_for(self, purpose, round_number=None):
        return next(
            entry for entry in self.manifest["entries"]
            if entry["purpose"] == purpose
            and (round_number is None or entry.get("round") == round_number)
        )

    def refresh_hash(self, entry):
        entry["sha256"] = hashlib.sha256((self.root / entry["path"]).read_bytes()).hexdigest()
        _dump(self.manifest_path, self.manifest)

    def test_complete_manifest_binds_and_checks_text_json_runs_and_regressions(self):
        report = self.assess()
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["structure_assessment"]["status"], "pass")
        self.assertEqual(report["content_status"], "pass")
        self.assertTrue(report["content_checked"])
        self.assertEqual(len(report["evidence_entries"]), 8)
        self.assertIn("no_execution_authentication", report["claim_scope"])

    def test_missing_evidence_file_cannot_pass(self):
        entry = self.manifest["entries"][0]
        (self.root / entry["path"]).unlink()
        _dump(self.manifest_path, self.manifest)
        report = self.assess()
        self.assertEqual(report["status"], "invalid")
        self.assertEqual(report["content_status"], "invalid")
        self.assertFalse(report["content_checked"])

    def test_empty_file_cannot_pass_even_with_matching_hash(self):
        entry = self.manifest["entries"][0]
        path = self.root / entry["path"]
        path.write_bytes(b"")
        self.refresh_hash(entry)
        report = self.assess()
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])

    def test_hash_drift_cannot_pass(self):
        entry = self.manifest["entries"][0]
        with (self.root / entry["path"]).open("ab") as stream:
            stream.write(b"changed")
        _dump(self.manifest_path, self.manifest)
        report = self.assess()
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])

    def test_invalid_json_evidence_cannot_pass(self):
        entry = self.entry_for("run", 2)
        path = self.root / entry["path"]
        path.write_text('{"candidate_id":', encoding="utf-8")
        self.refresh_hash(entry)
        report = self.assess()
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])

    def test_nonfinite_json_number_cannot_pass(self):
        entry = self.entry_for("run", 2)
        path = self.root / entry["path"]
        path.write_text(
            json.dumps({
                "candidate_id": entry["candidate_id"],
                "journey_id": entry["journey_id"],
                "round": entry["round"],
                "observation": "expected_state_visible",
                "score": "1e999",
            }).replace('"score": "1e999"', '"score": 1e999'),
            encoding="utf-8",
        )
        self.refresh_hash(entry)
        report = self.assess()
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])

    def test_invalid_json_manifest_cannot_pass(self):
        self.manifest_path.write_text('{"schema":', encoding="utf-8")
        report = self.assess()
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])

    def test_manifest_cross_candidate_binding_is_invalid(self):
        entry = self.manifest["entries"][0]
        entry["candidate_id"] = "older-candidate"
        _dump(self.manifest_path, self.manifest)
        report = self.assess()
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])

    def test_cross_candidate_and_old_round_content_fail(self):
        entry = self.entry_for("run", 2)
        path = self.root / entry["path"]
        document = json.loads(path.read_text(encoding="utf-8"))
        document["candidate_id"] = "older-candidate"
        document["round"] = 1
        path.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
        self.refresh_hash(entry)
        report = self.assess()
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["content_status"], "fail")
        self.assertTrue(report["content_checked"])

    def test_binding_marker_must_be_an_exact_line_not_a_round_prefix(self):
        entry = self.entry_for("run", 1)
        path = self.root / entry["path"]
        path.write_text(
            f"smoke-run:{entry['candidate_id']}:{entry['journey_id']}:round-10\n"
            "Observed expected outcome.\n",
            encoding="utf-8",
        )
        self.refresh_hash(entry)
        report = self.assess()
        self.assertEqual(report["status"], "fail")
        self.assertTrue(report["content_checked"])

    def test_reused_ref_across_rounds_is_rejected(self):
        results = copy.deepcopy(self.results)
        first = next(run for run in results["runs"] if run["journey_id"] == "open_home" and run["round"] == 1)
        second = next(run for run in results["runs"] if run["journey_id"] == "open_home" and run["round"] == 2)
        second["evidence"] = list(first["evidence"])
        report = self.assess(results=results)
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])
        self.assertTrue(any("reused refs" in reason for reason in report["reasons"]))

    def test_missing_ref_and_unused_manifest_entry_are_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["entries"].pop()
        report = self.assess(manifest=manifest)
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])

    def test_empty_entries_and_unsupported_media_type_fail_closed(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["entries"] = []
        self.assertEqual(self.assess(manifest=manifest)["status"], "invalid")
        manifest = copy.deepcopy(self.manifest)
        manifest["entries"][0]["media_type"] = "image/png"
        report = self.assess(manifest=manifest)
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])

        manifest = copy.deepcopy(self.manifest)
        manifest["entries"][0]["media_type"] = ["text/plain"]
        self.assertEqual(self.assess(manifest=manifest)["status"], "invalid")

    def test_file_and_hash_reuse_across_run_refs_are_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        run_entries = [entry for entry in manifest["entries"] if entry["purpose"] == "run"]
        first, second = run_entries[0], run_entries[1]
        second["path"] = first["path"]
        second["sha256"] = first["sha256"]
        report = self.assess(manifest=manifest)
        self.assertEqual(report["status"], "invalid")

        manifest = copy.deepcopy(self.manifest)
        run_entries = [entry for entry in manifest["entries"] if entry["purpose"] == "run"]
        first, second = run_entries[0], run_entries[1]
        copied_path = self.root / "evidence" / "runs" / "copied-evidence.txt"
        copied_path.parent.mkdir(parents=True, exist_ok=True)
        copied_path.write_bytes((self.root / first["path"]).read_bytes())
        second["path"] = "evidence/runs/copied-evidence.txt"
        second["sha256"] = first["sha256"]
        report = self.assess(manifest=manifest)
        self.assertEqual(report["status"], "invalid")

    def test_invalid_traversal_path_and_symlink_fail_closed(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["entries"][0]["path"] = "../outside.txt"
        self.assertEqual(self.assess(manifest=manifest)["status"], "invalid")

        entry = self.manifest["entries"][0]
        link_path = self.root / "evidence" / "runs" / "linked.txt"
        link_path.symlink_to(self.root / entry["path"])
        entry["path"] = "evidence/runs/linked.txt"
        entry["sha256"] = hashlib.sha256((self.root / "evidence/runs/open_home-r1.txt").read_bytes()).hexdigest()
        _dump(self.manifest_path, self.manifest)
        report = self.assess()
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])

    def test_manifest_fifo_is_rejected_without_blocking(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation is unavailable")
        fifo = self.root / "manifest-fifo.json"
        os.mkfifo(fifo)
        report = self.assess(manifest=fifo)
        self.assertEqual(report["status"], "invalid")
        self.assertFalse(report["content_checked"])

    def test_default_cli_marks_content_unchecked_and_new_cli_passes(self):
        plan_path = self.root / "plan.json"
        results_path = self.root / "results.json"
        _dump(plan_path, self.plan)
        _dump(results_path, self.results)
        script = ROOT / "scripts" / "smokecheck.py"
        legacy = subprocess.run(
            [sys.executable, str(script), "assess", str(plan_path), str(results_path)],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(legacy.returncode, 0, legacy.stderr)
        legacy_report = json.loads(legacy.stdout)
        self.assertEqual(legacy_report["claim_scope"], smokecheck.CLAIM_SCOPE)
        self.assertEqual(legacy_report["content_inspection"]["status"], "not_checked")
        self.assertNotIn("content_checked", legacy_report)

        explicit = subprocess.run(
            [sys.executable, str(script), "assess", str(plan_path), str(results_path), "--evidence-manifest", str(self.manifest_path)],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(explicit.returncode, 0, explicit.stderr + explicit.stdout)
        explicit_report = json.loads(explicit.stdout)
        self.assertEqual(explicit_report["status"], "pass")
        self.assertTrue(explicit_report["content_checked"])
        self.assertEqual(explicit_report["content_status"], "pass")

    def test_content_pass_cannot_override_unverified_structure_assessment(self):
        results = copy.deepcopy(self.results)
        results["runs"] = [run for run in results["runs"] if run["round"] == 2]
        evidence_root = self.root / "only-one-round"
        evidence_root.mkdir()
        plan, results, manifest = make_evidence(evidence_root, self.plan, results)
        report = smoke_evidence.assess(plan, results, manifest, root=evidence_root)
        self.assertEqual(report["structure_assessment"]["status"], "unverified")
        self.assertEqual(report["content_status"], "pass")
        self.assertEqual(report["status"], "unverified")

    def test_content_pass_cannot_override_failed_structure_assessment(self):
        results = copy.deepcopy(self.results)
        final_run = next(run for run in results["runs"] if run["journey_id"] == "open_home" and run["round"] == 2)
        final_run["status"] = "fail"
        evidence_root = self.root / "failed-structure"
        evidence_root.mkdir()
        plan, results, manifest = make_evidence(evidence_root, self.plan, results)
        report = smoke_evidence.assess(plan, results, manifest, root=evidence_root)
        self.assertEqual(report["structure_assessment"]["status"], "fail")
        self.assertEqual(report["content_status"], "pass")
        self.assertEqual(report["status"], "fail")


if __name__ == "__main__":
    unittest.main()
