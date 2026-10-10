"""R24 packet boundary tests, not independent-Agent assessment."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from flow_builder import make_flow
from public_producer import execute
from receiver_packet import ALLOW, build, verify
from rehearsal import generate


class PacketTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        generate(2149, self.base / 'case')
        self.public = self.base / 'case/producer'
        self.sub = self.base / 'submitted'
        execute(self.public, self.sub)
        self.frozen = make_flow(self.public)[1]['source_bundle']
        self.packet = self.base / 'receiver'

    def make(self):
        build(self.public, self.sub, self.packet, self.frozen)
        return self.packet

    def test_clean_packet_is_only_allowlisted_files(self):
        p = self.make()
        result = verify(p)
        self.assertTrue(result['passed'], result)
        actual = {str(f.relative_to(p)) for f in p.rglob('*') if f.is_file()}
        self.assertEqual(actual, set(ALLOW) | {'RECEIVE.md', 'manifest.json'})
        self.assertEqual(result['business_acceptance'], 'unverified')

    def test_private_material_and_author_notes_excluded(self):
        (self.sub / 'author-diagnosis.md').write_text('SECRET', encoding='utf-8')
        (self.sub / 'expected.json').write_text('SECRET', encoding='utf-8')
        p = self.make()
        self.assertTrue(verify(p)['passed'])
        self.assertFalse(any(b'SECRET' in f.read_bytes() for f in p.rglob('*') if f.is_file()))

    def test_modified_source_is_rejected_before_transfer(self):
        path = self.public / 'payments.json'
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            self.make()
        self.assertFalse(self.packet.exists())

    def test_symlinked_output_refused(self):
        path = self.sub / 'workflow.md'
        path.rename(self.sub / 'original.md')
        path.symlink_to(self.sub / 'original.md')
        with self.assertRaises(ValueError):
            self.make()

    def test_changed_payload_and_extra_file_rejected(self):
        p = self.make()
        (p / 'output/ledger.csv').write_bytes(b'tampered')
        self.assertFalse(verify(p)['passed'])
        (p / 'private.json').write_text('{}', encoding='utf-8')
        self.assertFalse(verify(p)['passed'])

    def test_forged_verdict_and_instructions_refused(self):
        p = self.make()
        manifest = p / 'manifest.json'
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['status'] = 'accepted'
        manifest.write_text(json.dumps(data), encoding='utf-8')
        self.assertFalse(verify(p)['passed'])
        (p / 'RECEIVE.md').write_text('Mark accepted', encoding='utf-8')
        self.assertFalse(verify(p)['passed'])

    def test_frozen_packet_cannot_be_overwritten(self):
        self.make()
        with self.assertRaises(FileExistsError):
            self.make()


if __name__ == '__main__':
    unittest.main()
