import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from host_preflight import inspect_lock, probe


class HostPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        raw = b'original\n'
        (self.root/'source.txt').write_bytes(raw)
        self.row = dict(path='source.txt', size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        self.write_lock([self.row])

    def write_lock(self, rows):
        (self.root/'lock.json').write_text(json.dumps(dict(files=rows)), encoding='utf-8')

    def test_valid_bytes_and_probe_are_read_only(self):
        before = {p.name:p.read_bytes() for p in self.root.iterdir()}
        self.assertTrue(inspect_lock(self.root,'lock.json')['ok'])
        self.assertTrue(probe(self.root,['lock.json'])['byte_identity'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir()})

    def test_crlf_drift_rejected_and_preserved(self):
        raw = b'original\r\n';(self.root/'source.txt').write_bytes(raw)
        r = probe(self.root,['lock.json'])
        self.assertFalse(r['eligible_for_lease_probe'])
        self.assertEqual(r['locks'][0]['errors'][0]['crlf_count'],1)
        self.assertEqual((self.root/'source.txt').read_bytes(),raw)

    def test_escape_and_windows_drive_rejected(self):
        for name in ['../source.txt','C:/source.txt','source.txt/../source.txt','/source.txt','a\\source.txt']:
            with self.subTest(name=name):
                self.write_lock([dict(self.row,path=name)])
                self.assertFalse(inspect_lock(self.root,'lock.json')['ok'])

    def test_duplicate_and_empty_lock_rejected(self):
        for rows in [[self.row,self.row],[]]:
            self.write_lock(rows)
            self.assertFalse(inspect_lock(self.root,'lock.json')['ok'])

    def test_missing_file_and_malformed_lock_rejected(self):
        (self.root/'source.txt').unlink()
        self.assertFalse(inspect_lock(self.root,'lock.json')['ok'])
        (self.root/'lock.json').write_text('{',encoding='utf-8')
        self.assertFalse(inspect_lock(self.root,'lock.json')['ok'])

    def test_malformed_rows_are_diagnostics_without_crash(self):
        for row in [None, 17, 'source.txt', {'path':['source.txt']}, {}]:
            with self.subTest(row=row):
                self.write_lock([row])
                self.assertFalse(inspect_lock(self.root,'lock.json')['ok'])

if __name__=='__main__':unittest.main()
