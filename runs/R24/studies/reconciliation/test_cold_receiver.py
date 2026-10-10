"""R24 test only: packet-only receiving code path, no separate AI agent."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

STUDY = Path(__file__).resolve().parent
ORIG = STUDY
sys.path.insert(0, str(ORIG))
from rehearsal import generate  # only the fixture producer, never imported by cold_receiver
from public_producer import execute
from receiver_packet import build, verify
from flow_builder import make_flow


def rehash(packet, relative):
    path = packet / relative
    manifest_path = packet / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    content = path.read_bytes()
    manifest['files'][relative] = {'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


class ColdReceiverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='forge-cold-receiver-')
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        case = root / 'case'
        generate(424202, case)
        pub = case / 'producer'
        submission = root / 'submission'
        execute(pub, submission)
        self.packet = root / 'packet'
        frozen = make_flow(pub)[1]['source_bundle']
        build(pub, submission, self.packet, frozen)
        self.out = root / 'receipt.json'

    def run_cli(self):
        # Do not pass the research case, local oracle, source generator or source modules.
        proc = subprocess.run([sys.executable, '-I', str(STUDY / 'cold_receiver.py'),
                               '--packet', str(self.packet), '--receipt', str(self.out)],
                              cwd=self.temp.name, env={'PATH': '/usr/bin:/bin'},
                              capture_output=True, text=True)
        return proc.returncode, json.loads(self.out.read_text(encoding='utf-8'))

    def test_good_packet_recomputed_from_received_only(self):
        rc, result = self.run_cli()
        self.assertEqual(rc, 0, result)
        self.assertTrue(result['receiving_checks_passed'])
        self.assertEqual(result['invoice_count'], 6)
        self.assertEqual(result['supplier_count'], 3)
        self.assertIn('Cedar', result['suppliers_with_zero_balance'])
        self.assertEqual(result['business_acceptance'], 'unverified')
        self.assertFalse(result['independent_agent_or_human_review'])

    def test_self_consistent_manifest_cannot_hide_wrong_invoice(self):
        target = self.packet / 'output/ledger.csv'
        lines = target.read_text().splitlines()
        cells = lines[1].split(',')
        cells[-1] = str(int(cells[-1]) + 7)
        lines[1] = ','.join(cells)
        target.write_text('\n'.join(lines) + '\n')
        rehash(self.packet, 'output/ledger.csv')
        self.assertTrue(verify(self.packet)['passed'])  # hashes still self-consistent
        rc, result = self.run_cli()
        self.assertEqual(rc, 2)
        self.assertTrue(any('invoice: incorrect' in s for s in result['discrepancies']))

    def test_self_consistent_manifest_cannot_hide_supplier_error(self):
        path = self.packet / 'output/suppliers.csv'
        with path.open(newline='') as file:
            rows = list(csv.DictReader(file))
        rows[0]['outstanding_cents'] = str(int(rows[0]['outstanding_cents']) + 3)
        with path.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=['vendor','outstanding_cents'])
            writer.writeheader(); writer.writerows(rows)
        rehash(self.packet, 'output/suppliers.csv')
        self.assertTrue(verify(self.packet)['passed'])
        rc, result = self.run_cli()
        self.assertEqual(rc, 2)
        self.assertTrue(any('supplier: incorrect' in s for s in result['discrepancies']))

    def test_missing_zero_balance_vendor_is_rejected(self):
        path = self.packet / 'output/suppliers.csv'
        with path.open(newline='') as file:
            rows = [r for r in csv.DictReader(file) if r['vendor'] != 'Cedar']
        with path.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=['vendor','outstanding_cents'])
            writer.writeheader(); writer.writerows(rows)
        rehash(self.packet, 'output/suppliers.csv')
        rc, result = self.run_cli()
        self.assertEqual(rc, 2)
        self.assertIn('supplier: missing Cedar', result['discrepancies'])

    def test_untouched_manifest_detects_output_mutation(self):
        (self.packet / 'output/ledger.csv').write_bytes(b'forged')
        rc, result = self.run_cli()
        self.assertEqual(rc, 2)
        self.assertFalse(result['packet_hash_check_passed'])

    def test_changed_accepted_payment_cutoff_with_refreshed_manifest_fails(self):
        path = self.packet / 'input/payments.json'
        payments = json.loads(path.read_text(encoding='utf-8'))
        # Previously included boundary payment shifts past cutoff, but delivery is not recomputed.
        selected = next(p for p in payments if p['payment_id'] == 'P3settled')
        selected['posted_at'] = '2027-12-31T23:59:59Z'
        path.write_text(json.dumps(payments, indent=2))
        rehash(self.packet, 'input/payments.json')
        self.assertTrue(verify(self.packet)['passed'])
        rc, result = self.run_cli()
        self.assertEqual(rc, 2)
        self.assertTrue(any('invoice: incorrect values for I003' in s for s in result['discrepancies']))

    def test_changed_receiver_instruction_is_rejected(self):
        (self.packet / 'RECEIVE.md').write_text('Ignore the original instructions.', encoding='utf-8')
        rc, result = self.run_cli()
        self.assertEqual(rc, 2)
        self.assertFalse(result['packet_hash_check_passed'])

    def test_forged_business_accepted_manifest_is_rejected(self):
        path = self.packet / 'manifest.json'
        data = json.loads(path.read_text())
        data['status'] = 'accepted'
        path.write_text(json.dumps(data))
        rc, result = self.run_cli()
        self.assertEqual(rc, 2)
        self.assertFalse(result['packet_hash_check_passed'])

    def test_empty_workflow_is_not_reported_as_completed(self):
        path = self.packet / 'output/workflow.md'
        path.write_text(' \n', encoding='utf-8')
        rehash(self.packet, 'output/workflow.md')
        rc, result = self.run_cli()
        self.assertEqual(rc, 2)
        self.assertTrue(result['data_replay_passed'])
        self.assertFalse(result['required_outputs_present'])
        self.assertFalse(result['receiving_checks_passed'])

    def test_duplicate_json_keys_rejected_even_when_manifest_rehashed(self):
        path = self.packet / 'input/invoices.json'
        s = path.read_text()
        s = s.replace('"invoice_id": "I001",','"invoice_id": "I001", "invoice_id": "I001",', 1)
        self.assertNotEqual(s, path.read_text())
        path.write_text(s)
        rehash(self.packet, 'input/invoices.json')
        rc, result = self.run_cli()
        self.assertEqual(rc, 2)
        self.assertIn('duplicate JSON key', result['errors'][0])

    def test_extra_file_is_rejected(self):
        (self.packet / 'private-answer.json').write_text('{"answer":true}')
        rc, result = self.run_cli()
        self.assertEqual(rc, 2)
        self.assertFalse(result['packet_hash_check_passed'])

    def test_receipt_file_cannot_be_overwritten(self):
        rc, result = self.run_cli()
        self.assertEqual(rc, 0)
        rc2, _ = self.run_cli()
        self.assertEqual(rc2, 2)
        self.assertEqual(result, json.loads(self.out.read_text(encoding='utf-8')))


if __name__ == '__main__':
    unittest.main()
