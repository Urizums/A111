"""Fault/clock/native-return fixtures; not live provider or quota evidence."""
from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys
import unittest
from unittest import mock

import hostbridge as h
import hostcapacity as cap
import hostdriver as d
import projectctl
import test_hostbridge as b
import test_hostdriver as f


class ResourceTests(unittest.TestCase):
    setUp = b.BridgeTests.setUp
    snapshot = b.BridgeTests.snapshot
    reply = b.BridgeTests.reply
    decision = b.BridgeTests.decision
    setup_driver = f.DriverTests.setup_driver
    next = f.DriverTests.next
    crash_ack_update = f.DriverTests.crash_ack_update

    def configure(self, policy="interrupt", seconds=1, capacity=True):
        self.tick = 100_000_000_000
        self.boot = "fixture-boot"
        patch = mock.patch.object(d, "clock", side_effect=lambda: {
            "boot_id": self.boot, "monotonic_ns": self.tick, "observed_at": "fixture-local-observation"})
        patch.start(); self.addCleanup(patch.stop)
        self.registry = self.root / "capacity.json"
        cap.init(self.registry, 1)
        self.setup_driver(registry=self.registry if capacity else None,
                          deadline_seconds=seconds, deadline_policy=policy)
        action = self.next()["action"]
        self.worker = "/root/" + action["arguments"]["task_name"]
        return action

    def activate(self, **kwargs):
        action = self.configure(**kwargs)
        d.claim(self.driver, action["action_id"])
        self.creation = self.root / "creation.json"
        h.save(self.creation, {"task_name": self.worker})
        d.ack(self.driver, action["action_id"], self.creation)
        return action

    def cutoff_query(self, status="running"):
        self.tick += 2_000_000_000
        query = self.next()["action"]
        self.assertEqual(query["kind"], "query")
        d.claim(self.driver, query["action_id"])
        d.ack(self.driver, query["action_id"], self.snapshot(status))
        return query

    def second(self):
        root = self.root / "second"; root.mkdir()
        out = root / "out"; out.mkdir()
        state = root / "state.json"; projectctl.init(deepcopy(self.plan), state)
        work = root / "work.json"
        h.save(work, {"prompt": "Another fixture", "inputs": {}, "write_paths": [str(out)], "reply_path": str(out / "reply.json")})
        works = root / "works.json"; h.save(works, {"task": str(work)})
        driver = root / "driver"
        d.init(driver, "project", state, works, "/root", registry=self.registry)
        action = d.advance(driver)["action"]
        return driver, state, action

    def held(self):
        return cap.summary(cap.read(self.registry))["held"]

    def test_options_off_preserve_configuration(self):
        self.setup_driver()
        config = d.load(self.driver)["config"]
        self.assertNotIn("capacity", config); self.assertNotIn("deadline", config)

    def test_deadline_begins_at_granted_claim_and_restart_preserves_it(self):
        a = self.configure(); self.tick += 10_000_000_000
        self.assertNotIn("deadline", d.load(self.driver)["current"])
        d.claim(self.driver, a["action_id"])
        started = d.load(self.driver)["current"]["deadline"]["started_clock"]
        self.assertEqual(started["monotonic_ns"], self.tick)
        self.next(); self.tick += 2_000_000_000; self.next()
        self.assertEqual(d.load(self.driver)["current"]["deadline"]["started_clock"], started)

    def test_invalid_deadlines_and_unconfigured_interrupt_rejected(self):
        for seconds in [0, -1, float("inf"), float("nan"), True]:
            with self.assertRaises(h.BridgeError): self.setup_driver(deadline_seconds=seconds)
        with self.assertRaises(h.BridgeError): self.setup_driver(deadline_policy="interrupt")

    def test_reboot_or_backward_clock_never_authorizes_more_calls(self):
        self.activate(); before = d.load(self.driver)["claims"]
        self.boot = "different-boot"
        with self.assertRaisesRegex(h.BridgeError, "boot identity"): self.next()
        self.boot = "fixture-boot"; self.tick = 1
        with self.assertRaisesRegex(h.BridgeError, "backwards"): self.next()
        self.assertEqual(d.load(self.driver)["claims"], before); self.assertEqual(self.held(), 1)

    def test_deadline_queries_before_interrupt_and_return_is_not_terminal(self):
        self.activate(); self.cutoff_query()
        a = self.next()["action"]; self.assertEqual(a["kind"], "interrupt")
        self.assertEqual(a["arguments"], {"target": self.worker})
        self.assertTrue(d.claim(self.driver, a["action_id"])["call_allowed"])
        p = self.root / "interrupt.json"; h.save(p, {"target": self.worker, "previous_status": "interrupted"})
        d.ack(self.driver, a["action_id"], p)
        self.assertEqual(h.control(self.job)["phase"], "running"); self.assertEqual(self.held(), 1)
        q = self.next()["action"]; self.assertEqual(q["kind"], "query")
        d.claim(self.driver, q["action_id"]); d.ack(self.driver, q["action_id"], self.snapshot("interrupted"))
        self.assertEqual(self.held(), 0); self.assertEqual(self.next()["phase"], "blocked")

    def test_missing_interrupt_return_never_issues_second_interrupt(self):
        self.activate(); self.cutoff_query(); a = self.next()["action"]; d.claim(self.driver, a["action_id"])
        for _ in range(2):
            q = self.next()["action"]; self.assertEqual(q["kind"], "query")
            d.claim(self.driver, q["action_id"]); d.ack(self.driver, q["action_id"], self.snapshot("running"))
        actions = d.load(self.driver)["actions"]
        self.assertEqual(sum(h.read(r["payload_ref"]["path"])["kind"] == "interrupt" for r in actions.values()), 1)
        self.assertEqual(self.held(), 1)

    def test_pre_cutoff_running_receipt_imported_late_requires_new_query(self):
        self.activate(); q = self.next()["action"]; d.claim(self.driver, q["action_id"])
        old_snapshot = self.snapshot("running")
        self.tick += 2_000_000_000
        d.ack(self.driver, q["action_id"], old_snapshot)
        after = self.next()["action"]; self.assertEqual(after["kind"], "query")
        self.assertIsNone(d.load(self.driver)["current"]["deadline"]["running_after_deadline"])
        d.claim(self.driver, after["action_id"]); d.ack(self.driver, after["action_id"], self.snapshot("running"))
        self.assertEqual(self.next()["action"]["kind"], "interrupt")

    def test_legacy_unclaimed_interrupt_without_query_clock_requeries(self):
        self.activate(); self.cutoff_query(); old = self.next()["action"]
        state = h.read(self.driver / "driver.json")
        del state["current"]["deadline"]["running_after_deadline"]["query_claim_clock"]
        h.save(self.driver / "driver.json", state)
        with self.assertRaisesRegex(h.BridgeError, "post-deadline"): d.claim(self.driver, old["action_id"])
        self.assertEqual(self.next()["action"]["kind"], "query")
        self.assertFalse(d.claim(self.driver, old["action_id"])["call_allowed"])
        self.assertEqual(d.load(self.driver)["actions"][old["action_id"]]["status"], "superseded")

    def test_interrupt_wrong_worker_is_retained_without_terminal_effect(self):
        self.activate(); self.cutoff_query(); a = self.next()["action"]; d.claim(self.driver, a["action_id"])
        p = self.root / "wrong.json"; h.save(p, {"target": "/root/other", "previous_status": "running"})
        with self.assertRaisesRegex(h.BridgeError, "another worker"): d.ack(self.driver, a["action_id"], p)
        self.assertEqual(self.held(), 1); self.assertEqual(len(d.load(self.driver)["rejected_imports"]), 1)

    def test_observe_policy_keeps_late_result_and_original_review(self):
        self.activate(policy="observe"); self.reply(); self.cutoff_query({"completed": "Fixture final"})
        self.assertEqual(self.held(), 0)
        self.assertIsNotNone(d.load(self.driver)["current"]["deadline"]["completion_observed_after_deadline"])
        a = self.next()["action"]; self.assertEqual(a["kind"], "review")
        d.claim(self.driver, a["action_id"]); d.ack(self.driver, a["action_id"], self.decision(), True)
        self.assertEqual(self.next()["phase"], "completed")

    def test_completed_race_after_interrupt_requires_review(self):
        self.activate(); self.cutoff_query(); a = self.next()["action"]; d.claim(self.driver, a["action_id"])
        self.reply(); q = self.next()["action"]; d.claim(self.driver, q["action_id"])
        d.ack(self.driver, q["action_id"], self.snapshot({"completed": "Fixture race"}))
        self.assertEqual(self.next()["action"]["kind"], "review"); self.assertEqual(self.held(), 0)

    def test_capacity_wait_retains_same_unclaimed_action_and_attempt(self):
        self.activate(); other, state, a = self.second()
        before = h.sha(state)
        for _ in range(2):
            result = d.claim(other, a["action_id"])
            self.assertFalse(result["call_allowed"]); self.assertEqual(result["status"], "waiting_capacity")
            self.assertEqual(d.advance(other)["action"]["action_id"], a["action_id"])
        self.assertEqual(h.sha(state), before); self.assertEqual(d.load(other)["claims"], 0)
        self.assertEqual(len(projectctl.load_state(state)["tasks"]["task"]["attempts"]), 1)

    def test_worker_completion_releases_before_source_review_for_second_checkpoint(self):
        self.activate(); other, _, a = self.second(); self.reply()
        q = self.next()["action"]; d.claim(self.driver, q["action_id"])
        d.ack(self.driver, q["action_id"], self.snapshot({"completed": "Fixture final"}))
        self.assertEqual(projectctl.load_state(self.state)["tasks"]["task"]["status"], "running")
        self.assertTrue(d.claim(other, a["action_id"])["call_allowed"]); self.assertEqual(self.held(), 1)

    def test_missing_creation_and_unknown_host_status_keep_slot(self):
        a = self.configure(); d.claim(self.driver, a["action_id"])
        q = self.next()["action"]; d.claim(self.driver, q["action_id"])
        p = self.root / "unknown.json"; h.save(p, {"agents": []})
        with self.assertRaises(h.BridgeError): d.ack(self.driver, q["action_id"], p)
        self.assertEqual(self.held(), 1)
        self.assertEqual(self.next()["action"]["kind"], "query")

    def test_actual_creation_error_releases_slot(self):
        a = self.configure(); d.claim(self.driver, a["action_id"])
        p = self.root / "error.json"; h.save(p, {"error": "Fixture actual creation failure"})
        d.ack(self.driver, a["action_id"], p)
        self.assertEqual(self.held(), 0)
        slot = next(iter(cap.read(self.registry)["allocations"].values()))
        self.assertEqual(slot["proof"]["origin"], "creation_error")

    def test_reserve_driver_write_gap_reuses_slot_without_repeat_permission(self):
        a = self.configure(); original = d.write
        def crash(root, state):
            if state["actions"][a["action_id"]]["status"] == "claimed": raise OSError("Fixture claim save crash")
            original(root, state)
        with mock.patch.object(d, "write", side_effect=crash):
            with self.assertRaises(OSError): d.claim(self.driver, a["action_id"])
        self.assertEqual(self.held(), 1); self.assertEqual(d.load(self.driver)["claims"], 0)
        self.assertTrue(d.claim(self.driver, a["action_id"])["call_allowed"])
        self.assertFalse(d.claim(self.driver, a["action_id"])["call_allowed"])
        self.assertEqual(len(cap.read(self.registry)["allocations"]), 1)

    def test_terminal_bridge_release_gap_replays_private_status(self):
        self.activate(); self.reply(); q = self.next()["action"]; d.claim(self.driver, q["action_id"])
        with mock.patch.object(cap, "release", side_effect=OSError("Fixture registry unavailable")):
            with self.assertRaises(OSError): d.ack(self.driver, q["action_id"], self.snapshot({"completed": "Fixture final"}))
        self.assertEqual(h.control(self.job)["phase"], "received"); self.assertEqual(self.held(), 1)
        self.assertEqual(self.next()["action"]["kind"], "review"); self.assertEqual(self.held(), 0)

    def test_release_driver_write_gap_replays_without_double_release(self):
        self.activate(); self.reply(); q = self.next()["action"]; d.claim(self.driver, q["action_id"])
        self.crash_ack_update(q, self.snapshot({"completed": "Fixture final"}))
        self.assertEqual(self.held(), 0); self.assertEqual(self.next()["action"]["kind"], "review")

    def test_registry_identity_limit_and_allocation_binding_drift_reject(self):
        a = self.configure(); original = h.read(self.registry)
        for field, value in [("registry_id", "other"), ("limit", 2)]:
            altered = deepcopy(original); altered[field] = value; h.save(self.registry, altered)
            with self.assertRaisesRegex(h.BridgeError, "drifted"): d.claim(self.driver, a["action_id"])
        h.save(self.registry, original); d.claim(self.driver, a["action_id"])
        changed = h.read(self.registry); next(iter(changed["allocations"].values()))["binding"]["worker"] = "/root/other"
        h.save(self.registry, changed); self.reply(); q = self.next()["action"]; d.claim(self.driver, q["action_id"])
        with self.assertRaisesRegex(h.BridgeError, "own this allocation"):
            d.ack(self.driver, q["action_id"], self.snapshot({"completed": "Fixture final"}))

    def test_released_proof_drift_is_not_capacity_availability(self):
        self.activate(); self.reply(); self.cutoff_query({"completed": "Fixture final"})
        proof = next(iter(cap.read(self.registry)["allocations"].values()))["proof"]
        Path(proof["receipt"]["path"]).write_text("{}")
        with self.assertRaises(h.runledger.LedgerError): cap.read(self.registry)

    def test_worker_scope_cannot_write_registry_or_lock(self):
        self.registry = self.out / "capacity.json"; cap.init(self.registry, 1)
        with self.assertRaisesRegex(h.BridgeError, "write scope"): self.setup_driver(registry=self.registry)

    def test_two_real_cli_processes_compete_for_one_local_slot(self):
        a = self.configure(seconds=None, policy="observe"); other, _, second = self.second()
        command = [sys.executable, str(Path(d.__file__)), "claim", "--driver"]
        processes = [subprocess.Popen(command + [str(root), "--action", action["action_id"]], stdout=subprocess.PIPE, text=True)
                     for root, action in [(self.driver, a), (other, second)]]
        results = []
        for process in processes:
            output, _ = process.communicate(timeout=15); self.assertEqual(process.returncode, 0); results.append(json.loads(output))
        self.assertEqual(sum(r["call_allowed"] for r in results), 1); self.assertEqual(self.held(), 1)


if __name__ == "__main__":
    unittest.main()
