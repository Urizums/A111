"""Actual byte preservation and rejection regressions for C4."""
import importlib.util,json,os,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=ROOT/'runs/R06/candidate/C4/forge-agent-flow/scripts/snapshot.py'
spec=importlib.util.spec_from_file_location('snapshot',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class SnapshotTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.src=self.base/'source';self.src.mkdir();self.bundle=self.base/'bundle'
 def test_original_retained_state_survives_later_mutation(self):
  original=(ROOT/'runs/R05/baseline/state/continuation.json').read_bytes();(self.src/'state.json').write_bytes(original)
  mod.capture(self.src,self.bundle,['state.json']);(self.src/'state.json').write_text('{}');out=self.base/'restored';mod.restore(self.bundle,out)
  self.assertEqual((out/'state.json').read_bytes(),original)
 def test_new_binary_unicode_same_hash_dedup(self):
  (self.src/'原始').mkdir();data=b'\x00\xff\r\n';(self.src/'原始/a').write_bytes(data);(self.src/'b').write_bytes(data)
  mod.capture(self.src,self.bundle,['原始/a','b']);self.assertEqual(len(list((self.bundle/'objects').iterdir())),1);self.assertEqual(mod.verify(self.bundle),[('原始/a',data),('b',data)])
 def test_invalid_and_duplicate_paths_leave_no_bundle(self):
  for paths in [['../escape'],['/abs'],['a//b'],['a/./b'],['a','a']]:
   with self.assertRaises((ValueError,OSError)):mod.capture(self.src,self.bundle,paths)
   self.assertFalse(self.bundle.exists())
 def test_parent_and_leaf_symlinks_rejected(self):
  (self.base/'outside').mkdir();(self.base/'outside/file').write_text('private');(self.src/'link').symlink_to(self.base/'outside',target_is_directory=True);(self.src/'leaf').symlink_to(self.base/'outside/file')
  for name in ['link/file','leaf']:
   with self.assertRaises(OSError):mod.capture(self.src,self.bundle,[name])
 def test_existing_snapshot_never_overwritten(self):
  (self.src/'a').write_text('old');mod.capture(self.src,self.bundle,['a']);before=(self.bundle/'manifest.json').read_bytes();(self.src/'a').write_text('new')
  with self.assertRaises(FileExistsError):mod.capture(self.src,self.bundle,['a'])
  self.assertEqual((self.bundle/'manifest.json').read_bytes(),before)
 def test_tamper_and_extra_objects_rejected(self):
  (self.src/'a').write_text('old');mod.capture(self.src,self.bundle,['a']);obj=next((self.bundle/'objects').iterdir());obj.write_text('new')
  with self.assertRaises(ValueError):mod.verify(self.bundle)
  obj.write_text('old');(self.bundle/'objects/extra').write_text('x')
  with self.assertRaises(ValueError):mod.verify(self.bundle)
 def test_restore_refuses_existing_destination_and_unsafe_manifest(self):
  (self.src/'a').write_text('old');mod.capture(self.src,self.bundle,['a'])
  with self.assertRaises(FileExistsError):mod.restore(self.bundle,self.src)
  p=self.bundle/'manifest.json';m=json.loads(p.read_text());m['files'][0]['path']='../escape';p.write_text(json.dumps(m))
  with self.assertRaises(ValueError):mod.restore(self.bundle,self.base/'out')
  self.assertFalse((self.base/'out').exists())

if __name__=='__main__':unittest.main()
