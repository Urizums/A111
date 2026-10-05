"""Real child-process regression of the recorded over-budget failure sequence."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
CLI=ROOT/'runs/R06/candidate/C5/forge-agent-flow/scripts/bounded_run.py'

class GuardTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.state=self.base/'journal';self.code=self.base/'candidate.py';self.input=self.base/'input.json';self.input.write_text('{"count":3}');self.code.write_text('print("ready")\n')
 def call(self,*args,expected=0):
  r=subprocess.run([sys.executable,str(CLI),*map(str,args)],capture_output=True,text=True)
  self.assertEqual(r.returncode,expected,r.stdout+r.stderr);return json.loads(r.stdout or r.stderr)
 def init(self):return self.call('init','--state',self.state,'--actor','root-test','--candidate',self.code,'--input',self.input)
 def run_candidate(self,expected=0,timeout=5):return self.call('run','--state',self.state,'--timeout',timeout,'--',sys.executable,self.code,self.input,expected=expected)
 def repair(self,reason='Actual failure-driven correction'):return self.call('repair','--state',self.state,'--reason',reason)
 def test_original_three_failure_classes_stop_at_bound(self):
  variants=['broken = {"a":}\n','def submit(): pass\nsubmit(expectation=True)\n','import json\njson.dumps({"predicate":lambda x:x})\n']
  self.code.write_text(variants[0]);self.init();self.run_candidate(expected=1)
  for v in variants[1:]:self.code.write_text(v);self.repair();self.run_candidate(expected=1)
  self.code.write_text('print("would be a forbidden fourth corrected run")\n')
  self.call('repair','--state',self.state,'--reason','third correction',expected=2);self.run_candidate(expected=2)
  j=json.loads((self.state/'ledger.json').read_text());self.assertEqual(j['phase'],'exhausted');self.assertEqual(len(j['repairs']),2);self.assertEqual(len(j['attempts']),3)
  self.assertEqual([json.loads((self.state/f'attempt-{n}.json').read_text())['exit_code'] for n in (1,2,3)],[1,1,1]);self.assertEqual(len(j['snapshots']),3)
 def test_new_case_actual_recovery_retains_failure_and_bytes(self):
  self.code.write_text('import json,sys\nx=json.load(open(sys.argv[1])); print(x["missing"])\n');original=self.code.read_bytes();self.init();self.run_candidate(expected=1)
  self.code.write_text('import json,sys\nx=json.load(open(sys.argv[1])); print(x["count"]*2)\n');self.repair();r=self.run_candidate();self.assertEqual(r['phase'],'passed')
  record=json.loads((self.state/'attempt-2.json').read_text());self.assertEqual(record['stdout'],'6\n');self.assertTrue(any(p.read_bytes()==original for p in (self.state/'snapshot-0/objects').iterdir()))
 def test_changed_source_without_repair_is_rejected(self):
  self.init();self.code.write_text('print("changed")');self.run_candidate(expected=2);self.assertFalse((self.state/'attempt-1.json').exists())
 def test_original_input_drift_and_duplicate_init_rejected(self):
  self.init();self.call('init','--state',self.state,'--actor','replace','--candidate',self.code,'--input',self.input,expected=2)
  self.input.write_text('{}');self.run_candidate(expected=2)
 def test_failed_run_requires_recorded_changed_candidate(self):
  self.code.write_text('raise ValueError("failure")');self.init();self.run_candidate(expected=1);self.run_candidate(expected=2)
  self.call('repair','--state',self.state,'--reason','no source change',expected=2)
 def test_timeout_and_unknown_state_cannot_retry(self):
  self.code.write_text('import time\ntime.sleep(2)');self.init();r=self.run_candidate(expected=124,timeout=.05);self.assertEqual(r['phase'],'unknown');self.run_candidate(expected=2)
  self.call('repair','--state',self.state,'--reason','not terminal proof',expected=2)
 def test_evidence_drift_is_rejected(self):
  self.init();self.run_candidate();(self.state/'attempt-1.json').write_text('{}');self.call('status','--state',self.state,expected=2)
 def test_input_mutation_by_successful_child_cannot_pass(self):
  self.code.write_text('import sys\nopen(sys.argv[1],"w").write("{}")');self.init();r=self.run_candidate(expected=2);self.assertEqual(r['exit_code'],0);self.assertEqual(r['phase'],'blocked_drift')

if __name__=='__main__':unittest.main()
