"""Behavioral tests for the local run evidence ledger."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

import runledger


class RunLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = self.root / "runs.json"
        runledger.init_ledger(self.ledger)
        self.receipts = []

    def evidence(self, name, contents):
        path = self.root / name
        path.write_text(contents, encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.receipts.append((path, digest))
        return path, digest

    def record(self, status, *, attempt="a1", job="job1", input_hash=None,
               parent=None, receipt=None, response=None, model=None, reasoning=None):
        receipt = receipt or self.evidence(f"receipt-{len(self.receipts)}.json", '{"ok":true}')
        kwargs = {}
        if status == "requested":
            kwargs.update(input_hash=input_hash or "a" * 64, model=model or "gpt-test",
                          reasoning=reasoning or "medium", parent_attempt=parent)
        if response:
            kwargs.update(response=response[0], response_sha256=response[1])
        return runledger.record(
            self.ledger, job_id=job, attempt_id=attempt, status=status,
            receipt=receipt[0], receipt_sha256=receipt[1], **kwargs)

    def job(self):
        return runledger.load(self.ledger)["jobs"]["job1"]

    def test_init_is_exclusive_and_cli_reports_existing_ledger_as_json(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = runledger.main(["init", "--ledger", str(self.ledger)])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn('"error"', stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_requested_running_completed_chain_reuses_only_intact_matching_input(self):
        input_hash = "b" * 64
        self.record("requested", input_hash=input_hash)
        self.record("running")
        response = self.evidence("response.json", '{"answer":42}')
        self.record("completed", response=response)

        result = runledger.status(self.ledger, job_id="job1", input_hash=input_hash)
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["action"], "reuse")
        self.assertTrue(result["evidence_valid"])
        self.assertEqual([e["status"] for e in self.job()["attempts"][0]["events"]],
                         ["requested", "running", "completed"])

    def test_receipt_and_completed_response_must_match_local_sha256(self):
        receipt = self.root / "bad-receipt.json"
        receipt.write_text("receipt")
        with self.assertRaisesRegex(runledger.LedgerError, "receipt SHA256 does not match"):
            runledger.record(self.ledger, job_id="job1", attempt_id="a1", status="requested",
                             receipt=receipt, receipt_sha256="0" * 64,
                             input_hash="a" * 64, model="m", reasoning="medium")
        self.record("requested")
        self.record("running")
        response = self.evidence("response.txt", "answer")
        with self.assertRaisesRegex(runledger.LedgerError, "response SHA256 does not match"):
            runledger.record(self.ledger, job_id="job1", attempt_id="a1", status="completed",
                             receipt=self.evidence("receipt-complete.json", "{} ")[0],
                             receipt_sha256=self.receipts[-1][1], response=response[0],
                             response_sha256="0" * 64)

    def test_requested_or_running_attempt_status_requires_reconciliation(self):
        input_hash = "a" * 64
        self.record("requested", input_hash=input_hash)
        for status in ("requested",):
            result = runledger.status(self.ledger, job_id="job1", input_hash=input_hash)
            self.assertEqual(result["state"], status)
            self.assertEqual(result["action"], "reconcile")
            self.record("running")
        result = runledger.status(self.ledger, job_id="job1", input_hash=input_hash)
        self.assertEqual(result["state"], "running")
        self.assertEqual(result["action"], "reconcile")
        with self.assertRaisesRegex(runledger.LedgerError, "unresolved attempt"):
            self.record("requested", attempt="a2", parent="a1", input_hash="c" * 64)

    def test_failed_and_interrupted_attempts_are_preserved_and_warn_before_retry(self):
        input_hash = "a" * 64
        self.record("requested", input_hash=input_hash)
        self.record("failed")
        failed_result = runledger.status(self.ledger, job_id="job1", input_hash=input_hash)
        self.assertEqual(failed_result["action"], "reconcile_before_retry")
        self.assertTrue(failed_result["external_reconciliation_required"])
        self.assertIn("side effects", failed_result["reason"].lower())

        self.record("requested", attempt="a2", parent="a1", input_hash="c" * 64)
        self.record("interrupted", attempt="a2")
        changed_input = runledger.status(self.ledger, job_id="job1", input_hash="c" * 64)
        self.assertEqual(changed_input["action"], "reconcile_before_retry")
        self.assertTrue(changed_input["external_reconciliation_required"])
        attempts = self.job()["attempts"]
        self.assertEqual([item["attempt_id"] for item in attempts], ["a1", "a2"])
        self.assertEqual(attempts[1]["parent_attempt"], "a1")
        self.assertEqual([item["events"][-1]["status"] for item in attempts],
                         ["failed", "interrupted"])

    def test_same_completed_input_cannot_be_dispatched_again_and_changed_input_is_not_reused(self):
        input_hash = "a" * 64
        self.record("requested", input_hash=input_hash)
        self.record("running")
        self.record("completed", response=self.evidence("response.json", "done"))
        with self.assertRaisesRegex(runledger.LedgerError, "reuse it"):
            self.record("requested", attempt="a2", parent="a1", input_hash=input_hash)
        changed = runledger.status(self.ledger, job_id="job1", input_hash="b" * 64)
        self.assertEqual(changed["state"], "input_changed")
        self.assertEqual(changed["recorded_status"], "completed")
        self.assertNotEqual(changed["action"], "reuse")
        self.assertEqual(changed["action"], "retry_eligible")

    def test_missing_or_changed_evidence_blocks_completed_and_retry_claims(self):
        input_hash = "a" * 64
        self.record("requested", input_hash=input_hash)
        self.record("running")
        self.record("completed", response=self.evidence("response.json", "done"))
        (self.root / "response.json").write_text("tampered")
        result = runledger.status(self.ledger, job_id="job1", input_hash=input_hash)
        self.assertEqual(result["state"], "evidence_invalid")
        self.assertFalse(result["evidence_valid"])
        self.assertEqual(result["action"], "reconcile")
        with self.assertRaisesRegex(runledger.LedgerError, "invalid evidence"):
            self.record("requested", attempt="a2", parent="a1", input_hash="b" * 64)

    def test_terminal_events_cannot_be_overwritten(self):
        self.record("requested")
        self.record("failed")
        before = self.ledger.read_bytes()
        with self.assertRaisesRegex(runledger.LedgerError, "Illegal transition"):
            self.record("running")
        with self.assertRaisesRegex(runledger.LedgerError, "Illegal transition"):
            self.record("completed", response=self.evidence("response.json", "done"))
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_malformed_json_and_malformed_shapes_fail_without_traceback(self):
        self.ledger.write_text("{", encoding="utf-8")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = runledger.main(["status", "--ledger", str(self.ledger),
                                   "--job-id", "job1", "--input-hash", "a" * 64])
        self.assertEqual(code, 2)
        self.assertIn('"error"', stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

        self.ledger.write_bytes(b"\xff")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = runledger.main(["status", "--ledger", str(self.ledger),
                                   "--job-id", "job1", "--input-hash", "a" * 64])
        self.assertEqual(code, 2)
        self.assertIn('"error"', stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

        malformed = {"schema_version": runledger.SCHEMA,
                     "created_at": "2026-01-01T00:00:00Z",
                     "jobs": {"job1": {"attempts": [{
                         "attempt_id": "a1", "parent_attempt": None, "model": "m",
                         "reasoning": "medium", "input_sha256": "a" * 64,
                         "events": [17]}]}}}
        self.ledger.write_text(json.dumps(malformed), encoding="utf-8")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = runledger.main(["status", "--ledger", str(self.ledger),
                                   "--job-id", "job1", "--input-hash", "a" * 64])
        self.assertEqual(code, 2)
        self.assertIn('"error"', stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_missing_previous_evidence_blocks_starting_any_new_attempt(self):
        self.record("requested")
        self.record("failed")
        receipt = Path(self.job()["attempts"][0]["events"][0]["receipt"]["path"])
        receipt.unlink()
        before = self.ledger.read_bytes()
        with self.assertRaisesRegex(runledger.LedgerError, "invalid evidence"):
            self.record("requested", attempt="a2", parent="a1", input_hash="b" * 64)
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_fifo_replacing_evidence_fails_closed_without_blocking(self):
        self.record("requested")
        self.record("failed")
        receipt = Path(self.job()["attempts"][0]["events"][0]["receipt"]["path"])
        receipt.unlink()
        os.mkfifo(receipt)
        result = runledger.status(self.ledger, job_id="job1", input_hash="a" * 64)
        self.assertEqual(result["state"], "evidence_invalid")
        self.assertFalse(result["evidence_valid"])

    def test_bad_event_status_type_is_reported_as_ledger_error(self):
        malformed = {"schema_version": runledger.SCHEMA,
                     "created_at": "2026-01-01T00:00:00Z",
                     "jobs": {"job1": {"attempts": [{
                         "attempt_id": "a1", "parent_attempt": None, "model": "m",
                         "reasoning": "medium", "input_sha256": "a" * 64,
                         "events": [{"status": [], "recorded_at": "2026-01-01T00:00:00Z",
                                     "receipt": {"path": str(self.root / "r"), "sha256": "0" * 64},
                                     "response": None}]}]}}}
        self.ledger.write_text(json.dumps(malformed), encoding="utf-8")
        with self.assertRaisesRegex(runledger.LedgerError, "Invalid status"):
            runledger.load(self.ledger)


if __name__ == "__main__":
    unittest.main()
