"""Failure/retry and no-overwrite acceptance for the fixed C6 candidate."""
import errno
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'runs/R07/candidate/C6/forge-agent-flow/scripts/snapshot.py'
spec=importlib.util.spec_from_file_location('snapshot_c6',SOURCE)
snapshot=importlib.util.module_from_spec(spec);spec.loader.exec_module(snapshot)

class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source';self.source.mkdir()
        (self.source/'a').write_bytes(b'\x00A\xff');(self.source/'b').write_bytes(b'B\r\n')
        self.bundle=self.root/'bundle';self.out=self.root/'restored'
        snapshot.capture(self.source,self.bundle,['a','b'])
        self.manifest=(self.bundle/'manifest.json').read_bytes()

    def check_clean(self):
        self.assertFalse(self.out.exists())
        self.assertEqual(list(self.root.glob('.restored.restore-*')),[])
        self.assertEqual((self.bundle/'manifest.json').read_bytes(),self.manifest)
        self.assertEqual(len(snapshot.verify(self.bundle)),2)

    def test_second_write_failure_leaves_no_target_and_retry_works(self):
        real_open=Path.open
        def fail_second(path,*args,**kw):
            if path.name=='b' and args and args[0]=='xb':
                raise OSError(errno.ENOSPC,'Injected second-file failure')
            return real_open(path,*args,**kw)
        with patch.object(Path,'open',fail_second):
            with self.assertRaises(OSError):snapshot.restore(self.bundle,self.out)
        self.check_clean();snapshot.restore(self.bundle,self.out)
        self.assertEqual((self.out/'a').read_bytes(),b'\x00A\xff')
        self.assertEqual((self.out/'b').read_bytes(),b'B\r\n')

    def test_publish_failure_leaves_no_target_and_retry_works(self):
        with patch.object(snapshot,'publish_directory',side_effect=OSError(errno.EACCES,'Injected publish failure')):
            with self.assertRaises(OSError):snapshot.restore(self.bundle,self.out)
        self.check_clean();self.assertEqual(snapshot.restore(self.bundle,self.out)['restored'],2)

    def test_existing_empty_directory_is_not_replaced(self):
        self.out.mkdir();before=self.out.stat().st_ino
        with self.assertRaises(FileExistsError):snapshot.restore(self.bundle,self.out)
        self.assertEqual(self.out.stat().st_ino,before)
        self.assertEqual(list(self.out.iterdir()),[])

    def test_existing_file_or_dangling_symlink_is_preserved(self):
        self.out.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):snapshot.restore(self.bundle,self.out)
        self.assertEqual(self.out.read_bytes(),b'existing');self.out.unlink()
        self.out.symlink_to(self.root/'absent')
        with self.assertRaises(FileExistsError):snapshot.restore(self.bundle,self.out)
        self.assertTrue(self.out.is_symlink())

    def test_target_created_during_publish_is_not_overwritten(self):
        real_publish=snapshot.publish_directory
        def competitor(staging,destination):
            destination.mkdir()
            return real_publish(staging,destination)
        with patch.object(snapshot,'publish_directory',competitor):
            with self.assertRaises(FileExistsError):snapshot.restore(self.bundle,self.out)
        self.assertEqual(list(self.out.iterdir()),[])
        self.assertEqual(list(self.root.glob('.restored.restore-*')),[])

    def test_destination_is_absent_until_complete_publication(self):
        real_publish=snapshot.publish_directory
        def inspect(staging,destination):
            self.assertFalse(destination.exists())
            self.assertEqual((staging/'a').read_bytes(),b'\x00A\xff')
            self.assertEqual((staging/'b').read_bytes(),b'B\r\n')
            return real_publish(staging,destination)
        with patch.object(snapshot,'publish_directory',inspect):snapshot.restore(self.bundle,self.out)

    def test_tamper_rejected_before_output_creation(self):
        obj=next((self.bundle/'objects').iterdir());obj.write_bytes(b'tampered')
        with self.assertRaises(ValueError):snapshot.restore(self.bundle,self.out)
        self.assertFalse(self.out.exists())

    def test_unsupported_backend_has_no_partial_result(self):
        with patch.object(snapshot.sys,'platform','unsupported-host'):
            with self.assertRaises(OSError):snapshot.restore(self.bundle,self.out)
        self.check_clean()

if __name__=='__main__':unittest.main()
