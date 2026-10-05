import json,subprocess,sys,tempfile,unittest
from pathlib import Path
CLI=Path(__file__).with_name('coordinator_lease.py')
class LeaseTests(unittest.TestCase):
 def test_actual_second_process_is_refused_then_can_claim_after_release(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);first=subprocess.Popen([sys.executable,str(CLI),'hold','--root',str(root),'--owner','first'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   try:
    self.assertTrue(json.loads(first.stdout.readline())['acquired']);second=subprocess.run([sys.executable,str(CLI),'hold','--root',str(root),'--owner','duplicate'],capture_output=True,text=True);self.assertEqual(second.returncode,3);self.assertEqual(json.loads(second.stdout)['holder']['owner'],'first')
    probe=subprocess.run([sys.executable,str(CLI),'probe','--root',str(root)],capture_output=True,text=True);self.assertTrue(json.loads(probe.stdout)['busy'])
    first.communicate('release\n',timeout=5);self.assertEqual(first.returncode,0)
    third=subprocess.run([sys.executable,str(CLI),'hold','--root',str(root),'--owner','successor'],input='release\n',capture_output=True,text=True);self.assertEqual(third.returncode,0);self.assertTrue(json.loads(third.stdout.splitlines()[0])['acquired'])
   finally:
    if first.poll() is None:first.kill();first.communicate()

if __name__=='__main__':unittest.main()
