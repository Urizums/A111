"""Check factory plan continuity and grade gates with explicit synthetic fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import evalplan
import factoryctl as factory
import flowctl as flow
import packagectl as package


class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.draft = package.load(Path(__file__).resolve().parents[1] / "assets/example-package.json")
        design = package.load(Path(__file__).resolve().parents[1] / "assets/example-design.json")
        self.contract = design['contract']
        self.architecture = design['architecture']
        for row, name in zip(self.architecture['stress_cases'], ('empty', 'empty_again')):
            row['case_id'] = name
        self.plan = {"schema": "forge-eval/1", "id": "factory_fixture",
                     "criteria": copy.deepcopy(self.draft["acceptance"]["criteria"]),
                     "cases": [{"id": "empty", "inputs": {"notes": "No actions."},
                                "expected": {"actions": []}, "expected_status": "completed",
                                "criteria": [c["id"] for c in self.draft["acceptance"]["criteria"]], "required": True}],
                     "baseline": "One agent", "limitations": ["Synthetic fixture only"]}
        second = copy.deepcopy(self.plan['cases'][0])
        second['id'] = 'empty_again'
        second['inputs']['notes'] = 'No further actions.'
        self.plan['cases'].append(second)
        self.initial = factory.start({"request": design['request'], "environment": {"fixture": True}})

    def response(self, state, artifacts, outcome="ok"):
        return {"invocation_id": factory.pending(state)["invocation_id"], "outcome": outcome,
                "artifacts": artifacts, "evidence": ["Synthetic factory test fixture"]}

    def at_eval(self):
        return factory.advance(self.initial, self.response(self.initial, {"contract": self.contract}))

    def at_architect(self):
        return factory.freeze_plan(self.at_eval(), self.plan)

    def at_build(self):
        state = self.at_architect()
        return factory.advance(state, self.response(state, {"architecture": self.architecture}))

    def at_verify(self):
        state = self.at_build()
        p = factory.bind_package(state, self.draft)
        candidate = {"package": p, "package_hash": flow.digest(p)}
        return factory.advance(state, self.response(state, {"candidate": candidate})), p

    def results(self, p, failed=False):
        rows = []
        for index, case in enumerate(self.plan['cases']):
            state = package.start(p, case["inputs"])
            d = package.pending(p, state)
            state = package.advance(p, state, {"invocation_id": d["invocation_id"], "outcome": "ok", "artifacts": {"actions": []}, "evidence": ["Synthetic output"]})
            checks = [{"id": c["id"], "kind": c["kind"], "status": "pass", "evidence": ["Synthetic grade"]} for c in self.plan["criteria"]]
            if failed and index == 0:
                checks[0]["status"] = "fail"
            rows.append({'case_id':case['id'], 'run':state, 'checks':checks})
        return {"package_hash": flow.digest(p), "plan_hash": p["acceptance"]["plan_hash"],
                "cases": rows}

    def materials_fixture(self, folder, intent="source_only", unknown_identity=False):
        root = Path(folder)
        source = root / "complete-source.zip"
        source.write_bytes(b"Synthetic complete source snapshot\n")
        identity = "unknown" if unknown_identity else "fixture app"
        manifest = {
            "schema": "forge-materials/1", "intent": intent,
            "source": {"path": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                       "role": "target_source", "identity": identity, "stack": "python",
                       "platform": "test", "fingerprint_scope": "complete_source_snapshot"},
            "binary": None, "references": [], "provenance": None,
        }
        if intent == "binary_source":
            binary = root / "target.bin"
            binary.write_bytes(b"Synthetic target binary\n")
            manifest["binary"] = {"path": binary.name, "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                                  "role": "target_binary", "identity": identity,
                                  "stack": "python", "platform": "test"}
        path = root / "materials.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def start_inputs(self):
        return {"request": "Build a synthetic fixture package.", "environment": {"fixture": True}}

    def test_legacy_dispatch_marks_materials_not_configured(self):
        dispatch = factory.pending(factory.start(self.start_inputs()))
        self.assertEqual(dispatch["status"], "ready")
        self.assertEqual(dispatch["materials_assessment"]["decision"], "not_configured")
        self.assertEqual(dispatch["materials_assessment"]["status"], "not_configured")

    def test_source_only_modify_is_allowed_and_checkpoint_freezes_absolute_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = self.materials_fixture(folder)
            state = factory.start(self.start_inputs(), manifest, "modify")
            frozen = state["flow_state"]["artifacts"]["environment"]["materials"]
            self.assertEqual(frozen["path"], str(manifest.resolve()))
            self.assertEqual(frozen["sha256"], hashlib.sha256(manifest.read_bytes()).hexdigest())
            dispatch = factory.pending(state)
            self.assertEqual(dispatch["status"], "ready")
            self.assertEqual(dispatch["materials_assessment"]["operation"], "modify")
            self.assertEqual(dispatch["materials_assessment"]["decision"], "allow")
            self.assertIn("modify", dispatch["materials_assessment"]["allowed_operations"])

    def test_identity_blockers_allow_design_with_explanation_but_block_modify_and_advance(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = self.materials_fixture(folder, "binary_source", unknown_identity=True)
            design_state = factory.start(self.start_inputs(), manifest, "design")
            design_dispatch = factory.pending(design_state)
            self.assertEqual(design_dispatch["status"], "ready")
            assessment = design_dispatch["materials_assessment"]
            self.assertEqual(assessment["decision"], "allow")
            self.assertTrue(assessment["blockers"])
            self.assertIn("does not authenticate", assessment["claim_limit"])

            modify_state = factory.start(self.start_inputs(), manifest, "modify")
            modify_dispatch = factory.pending(modify_state)
            self.assertEqual(modify_dispatch["status"], "blocked")
            self.assertNotIn("modify", modify_dispatch["materials_assessment"]["allowed_operations"])
            before = copy.deepcopy(modify_state)
            with self.assertRaisesRegex(flow.FlowError, "cannot advance"):
                factory.advance(modify_state, {"invocation_id": "forged", "outcome": "ok",
                                               "artifacts": {}, "evidence": ["Forged response"]})
            self.assertEqual(modify_state, before)

    def test_manifest_drift_blocks_design_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = self.materials_fixture(folder)
            state = factory.start(self.start_inputs(), manifest, "design")
            manifest.write_text(manifest.read_text(encoding="utf-8") + " ", encoding="utf-8")
            dispatch = factory.pending(state)
            self.assertEqual(dispatch["status"], "blocked")
            self.assertIn("hash drifted", dispatch["reason"])

    def test_evidence_change_blocks_pending_and_cannot_be_bypassed_by_advance(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = self.materials_fixture(folder)
            source = Path(folder) / "complete-source.zip"
            state = factory.start(self.start_inputs(), manifest, "inspect")
            source.write_bytes(b"changed after start")
            dispatch = factory.pending(state)
            self.assertEqual(dispatch["status"], "blocked")
            self.assertIn("invalid", dispatch["reason"].lower())
            with self.assertRaises(flow.FlowError):
                factory.advance(state, {"invocation_id": "forged", "outcome": "ok",
                                        "artifacts": {}, "evidence": ["Forged response"]})

    def test_partial_material_configuration_fails_closed_in_api_and_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = self.materials_fixture(folder)
            with self.assertRaisesRegex(flow.FlowError, "supplied together"):
                factory.start(self.start_inputs(), manifest, None)
            with self.assertRaisesRegex(flow.FlowError, "supplied together"):
                factory.start(self.start_inputs(), None, "design")
            malformed = self.start_inputs()
            malformed["environment"]["materials"] = None
            malformed_dispatch = factory.pending(factory.start(malformed))
            self.assertEqual(malformed_dispatch["status"], "blocked")
            inputs_path, state_path = Path(folder) / "inputs.json", Path(folder) / "state.json"
            inputs_path.write_text(json.dumps(self.start_inputs()), encoding="utf-8")
            base = [sys.executable, factory.__file__, "start", "--state", str(state_path),
                    "--inputs", str(inputs_path)]
            for extra in (["--materials", str(manifest)], ["--operation", "design"]):
                result = subprocess.run(base + extra, text=True, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(state_path.exists())
            result = subprocess.run(base + ["--materials", str(manifest), "--operation", "modify"],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["materials_assessment"]["decision"], "allow")
            saved = package.load(state_path)
            self.assertEqual(saved["flow_state"]["artifacts"]["environment"]["materials"]["operation"], "modify")

    def test_fifo_replacement_blocks_without_hanging(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = self.materials_fixture(folder)
            state = factory.start(self.start_inputs(), manifest, "inspect")
            manifest.unlink()
            import os
            os.mkfifo(manifest)
            dispatch = factory.pending(state)
            self.assertEqual(dispatch["status"], "blocked")

    def test_freeze_only_in_eval_design_and_only_once(self):
        with self.assertRaisesRegex(flow.FlowError, "eval_design"):
            factory.freeze_plan(self.initial, self.plan)
        state = self.at_architect()
        with self.assertRaisesRegex(flow.FlowError, "eval_design"):
            factory.freeze_plan(state, self.plan)

    def test_summary_response_is_rejected_without_mutating_state(self):
        state = self.at_eval()
        before = copy.deepcopy(state)
        with self.assertRaisesRegex(flow.FlowError, "freeze-plan"):
            factory.advance(state, self.response(state, {"test_plan": {"summary": "all criteria pass"}}))
        self.assertEqual(state, before)
        with self.assertRaises(flow.FlowError):
            factory.freeze_plan(state, {"summary": "missing full case inputs"})
        self.assertEqual(state, before)

    def test_exact_plan_is_bound_to_handoff_and_later_dispatch(self):
        state = self.at_architect()
        lock = state["flow_state"]["artifacts"]["test_plan"]
        self.assertEqual(lock, evalplan.make_lock(self.plan))
        self.assertEqual(state["flow_state"]["trace"][-1]["output_hash"], flow.digest({"test_plan": lock}))
        self.assertEqual(factory.pending(state)["inputs"]["test_plan"], lock)

    def test_mutation_remains_rejected_even_if_plan_digest_is_recalculated(self):
        state = self.at_architect()
        state["flow_state"]["artifacts"]["test_plan"]["plan"]["baseline"] = "Changed after freeze"
        lock = state["flow_state"]["artifacts"]["test_plan"]
        lock["plan_hash"] = flow.digest(lock["plan"])
        with self.assertRaisesRegex(flow.FlowError, "eval_design handoff"):
            factory.pending(state)

    def test_bind_waits_for_build_and_copies_exact_authoritative_lock(self):
        with self.assertRaisesRegex(flow.FlowError, "build stage"):
            factory.bind_package(self.at_architect(), self.draft)
        state = self.at_build()
        changed = copy.deepcopy(self.draft)
        changed["acceptance"] = {"criteria": []}
        p = factory.bind_package(state, changed)
        self.assertEqual(p["acceptance"], state["flow_state"]["artifacts"]["test_plan"])
        self.assertEqual(p["schema"], "forge-package/2")

    def test_build_rejects_another_valid_plan_or_wrong_package_hash(self):
        state = self.at_build()
        p = factory.bind_package(state, self.draft)
        p["acceptance"]["plan"]["baseline"] = "Different but valid plan"
        p["acceptance"]["plan_hash"] = flow.digest(p["acceptance"]["plan"])
        with self.assertRaisesRegex(flow.FlowError, "exact frozen plan"):
            factory.advance(state, self.response(state, {"candidate": {"package": p, "package_hash": flow.digest(p)}}))
        p = factory.bind_package(state, self.draft)
        with self.assertRaisesRegex(flow.FlowError, "package_hash"):
            factory.advance(state, self.response(state, {"candidate": {"package": p, "package_hash": "wrong"}}))

    def test_verify_requires_full_results_and_cannot_override_failure(self):
        state, p = self.at_verify()
        for evaluation in ({"summary": "pass"}, {"results": self.results(p, failed=True)},
                           {"results": self.results(p, failed=True), "assessment": {"verdict": "pass"}}):
            with self.subTest(evaluation=evaluation), self.assertRaises(flow.FlowError):
                factory.advance(state, self.response(state, {"evaluation": evaluation}))

    def test_missing_cases_cannot_pass_but_can_be_delivered_as_limited(self):
        state, p = self.at_verify()
        results = {"package_hash": flow.digest(p), "plan_hash": p["acceptance"]["plan_hash"], "cases": []}
        with self.assertRaisesRegex(flow.FlowError, "cannot report ok"):
            factory.advance(state, self.response(state, {"evaluation": {"results": results}}))
        state = factory.advance(state, self.response(state, {"evaluation": {"results": results}}, "limited"))
        self.assertEqual(state["flow_state"]["artifacts"]["evaluation"]["assessment"]["verdict"], "pending")
        state = factory.advance(state, self.response(state, {"delivery": {"note": "Limited fixture"}}))
        self.assertEqual(state["flow_state"]["artifacts"]["delivery"]["assessment"]["verdict"], "pending")

    def test_all_six_stages_complete_with_exact_bound_delivery(self):
        state, p = self.at_verify()
        state = factory.advance(state, self.response(state, {"evaluation": {"results": self.results(p)}}))
        state = factory.advance(state, self.response(state, {"delivery": {"note": "Fixture result"}}))
        fs = state["flow_state"]
        self.assertEqual(fs["status"], "completed")
        self.assertEqual(fs["steps"], 6)
        self.assertEqual(fs["artifacts"]["delivery"]["assessment"]["verdict"], "pass")
        self.assertEqual(fs["artifacts"]["delivery"]["plan_hash"], flow.digest(self.plan))
        self.assertEqual(fs["artifacts"]["delivery"]["package_hash"], flow.digest(p))

    def test_delivery_cannot_relabel_a_pending_assessment(self):
        state, p = self.at_verify()
        results = {"package_hash": flow.digest(p), "plan_hash": p["acceptance"]["plan_hash"], "cases": []}
        state = factory.advance(state, self.response(state, {"evaluation": {"results": results}}, "limited"))
        with self.assertRaisesRegex(flow.FlowError, "cannot override"):
            factory.advance(state, self.response(state, {"delivery": {"assessment": {"verdict": "pass"}}}))

    def test_lifecycle_completion_retains_failed_acceptance(self):
        state, p = self.at_verify()
        state = factory.advance(state, self.response(state, {"evaluation": {"results": self.results(p, failed=True)}}, "limited"))
        with self.assertRaisesRegex(flow.FlowError, "cannot override"):
            factory.advance(state, self.response(state, {"delivery": {"assessment": {"verdict": "pass"}}}))
        state = factory.advance(state, self.response(state, {"delivery": {"note": "Unresolved failure disclosed"}}))
        self.assertEqual(state["flow_state"]["status"], "completed")
        self.assertEqual(state["flow_state"]["artifacts"]["delivery"]["assessment"]["verdict"], "fail")

    def test_rebuilt_candidate_rejects_previous_candidate_results(self):
        state, p = self.at_verify()
        old_results = self.results(p, failed=True)
        state = factory.advance(state, self.response(state, {"evaluation": {"results": old_results}}, "fixable"))
        state = factory.advance(state, self.response(state, {"architecture": self.architecture}))
        draft = copy.deepcopy(self.draft)
        draft["flow"]["nodes"][0]["prompt"] += " Preserve exact quotes."
        new = factory.bind_package(state, draft)
        state = factory.advance(state, self.response(state, {"candidate": {"package": new, "package_hash": flow.digest(new)}}))
        with self.assertRaises(flow.FlowError):
            factory.advance(state, self.response(state, {"evaluation": {"results": old_results}}))

    def test_edited_candidate_checkpoint_is_rejected(self):
        state, p = self.at_verify()
        state["flow_state"]["artifacts"]["candidate"]["note"] = "Changed after build"
        with self.assertRaisesRegex(flow.FlowError, "build handoff"):
            factory.pending(state)

    def test_intake_omissions_blockers_and_false_explicit_basis_rejected(self):
        incomplete = copy.deepcopy(self.contract)
        del incomplete['decisions']['failures']
        blocked = copy.deepcopy(self.contract)
        blocked['blocking_questions'] = ['Which account may be changed?']
        invented = copy.deepcopy(self.contract)
        invented['requirements'][0]['basis'] = 'An instruction the user never gave.'
        before = copy.deepcopy(self.initial)
        for contract in ({'goal': 'Thin summary'}, incomplete, blocked, invented):
            with self.subTest(contract=contract), self.assertRaises(flow.FlowError):
                factory.advance(self.initial, self.response(self.initial, {'contract': contract}))
            self.assertEqual(self.initial, before)

    def test_unmapped_required_criteria_cannot_freeze(self):
        plan = copy.deepcopy(self.plan)
        plan['criteria'][0]['id'] = 'other_quotes'
        for case in plan['cases']:
            case['criteria'] = ['other_quotes', 'commitments']
        with self.assertRaises(flow.FlowError):
            factory.freeze_plan(self.at_eval(), plan)

    def test_incomplete_architecture_cannot_advance(self):
        state = self.at_architect()
        bad = copy.deepcopy(self.architecture)
        bad['coverage'].pop()
        unresolved = copy.deepcopy(self.architecture)
        unresolved['review']['unresolved'] = ['No recovery policy decided']
        for architecture in ({'mode':'lite'}, bad, unresolved):
            with self.assertRaises(flow.FlowError):
                factory.advance(state, self.response(state, {'architecture':architecture}))

    def test_unknown_coverage_node_cannot_bind_or_submit_package(self):
        state = self.at_architect()
        bad = copy.deepcopy(self.architecture)
        bad['coverage'][0]['node_ids'] = ['missing_node']
        state = factory.advance(state, self.response(state, {'architecture':bad}))
        with self.assertRaises(flow.FlowError):
            factory.bind_package(state, self.draft)
        valid_package = factory.bind_package(self.at_build(), self.draft)
        candidate = {'package':valid_package, 'package_hash':flow.digest(valid_package)}
        with self.assertRaises(flow.FlowError):
            factory.advance(state, self.response(state, {'candidate':candidate}))

    def test_original_request_contract_and_design_drift_rejected(self):
        state = self.at_build()
        for artifact, field in (('contract','goal'), ('architecture','mode')):
            changed = copy.deepcopy(state)
            changed['flow_state']['artifacts'][artifact][field] = 'Edited after handoff'
            with self.assertRaises(flow.FlowError):
                factory.pending(changed)
        changed = copy.deepcopy(state)
        changed['flow_state']['artifacts']['request'] += ' New unrelated instruction.'
        with self.assertRaisesRegex(flow.FlowError, 'Original request'):
            factory.pending(changed)

    def test_repair_can_change_topology_before_new_candidate_binding(self):
        state, p = self.at_verify()
        state = factory.advance(state, self.response(state, {'evaluation':{'results':self.results(p, failed=True)}}, 'fixable'))
        revised = copy.deepcopy(self.architecture)
        for row in revised['coverage']:
            row['node_ids'] = ['extract_v2']
        state = factory.advance(state, self.response(state, {'architecture':revised}))
        draft = copy.deepcopy(self.draft)
        draft['flow']['entry'] = 'extract_v2'
        draft['flow']['nodes'][0]['id'] = 'extract_v2'
        draft['execution']['node_settings']['extract_v2'] = draft['execution']['node_settings'].pop('extract')
        for requirement in draft['execution']['requirements']:
            if requirement['scope'] == 'extract':
                requirement['scope'] = 'extract_v2'
        new = factory.bind_package(state, draft)
        state = factory.advance(state, self.response(state, {'candidate':{'package':new,'package_hash':flow.digest(new)}}))
        self.assertEqual(factory.pending(state)['node'], 'verify')

    def test_cli_rejection_preserves_checkpoint_bytes_and_export_is_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state_file, response_file = root / "state.json", root / "response.json"
            state = self.at_eval()
            flow.save(state_file, state)
            flow.save(response_file, self.response(state, {"test_plan": {"summary": "fake"}}))
            original = state_file.read_bytes()
            r = subprocess.run([sys.executable, factory.__file__, "advance", "--state", str(state_file), "--response", str(response_file)], text=True, capture_output=True)
            self.assertEqual(r.returncode, 2)
            self.assertEqual(state_file.read_bytes(), original)
            state = factory.freeze_plan(state, self.plan)
            flow.save(state_file, state)
            out = root / "export.json"
            cmd = [sys.executable, factory.__file__, "export-plan", "--state", str(state_file), "--out", str(out)]
            r = subprocess.run(cmd, text=True, capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(evalplan.load(out), self.plan)
            before = out.read_bytes()
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 2)
            self.assertEqual(out.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
