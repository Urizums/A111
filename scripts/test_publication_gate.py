import hashlib,json,tempfile,unittest
from pathlib import Path
from check_publication_gate import check,REQUIRED_TASKS,REQUIRED_CHECKS

class PublicationGateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'state').mkdir();(self.root/'candidate.py').write_text('original');(self.root/'result.json').write_text('{"observed":true}')
  def ref(name):return {'path':name,'sha256':hashlib.sha256((self.root/name).read_bytes()).hexdigest()}
  self.evidence=ref('result.json');files=[ref('candidate.py')];self.digest=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  self.gate={'schema':'forge-publication-gate/1','destination':'waw1w1/A111:dev','required_open_tasks':sorted(REQUIRED_TASKS),'candidate':{'files':files,'sha256':self.digest},'checks':{n:{'status':'pass','candidate_sha256':self.digest,'evidence':[self.evidence]} for n in REQUIRED_CHECKS},'findings':[],'unreconciled_native':[]}
  self.state={'tasks':[{'id':n,'status':'done','evidence':[self.evidence],'repairs_used':0,'repair_limit':2,'blocker':None} for n in REQUIRED_TASKS]}
 def result(self):
  (self.root/'state/publication-gate.json').write_text(json.dumps(self.gate));(self.root/'state/continuation.json').write_text(json.dumps(self.state));return check(self.root)
 def test_complete_bound_evidence_can_pass(self):self.assertTrue(self.result()['publishing_allowed'])
 def test_any_required_blocked_failed_not_run_or_missing_denies(self):
  for status in ['blocked','failed','planned','in_progress',None]:
   self.state['tasks'][0]['status']=status;self.gate['publishing_allowed']=True;self.assertFalse(self.result()['publishing_allowed'])
 def test_missing_or_stale_smoke_denies(self):
  self.gate['checks']['installed_smoke']['status']='not_run';self.assertFalse(self.result()['publishing_allowed']);self.gate['checks']['installed_smoke']['status']='pass';self.gate['checks']['installed_smoke']['candidate_sha256']='old';self.assertFalse(self.result()['publishing_allowed'])
 def test_changed_code_or_evidence_denies(self):
  (self.root/'candidate.py').write_text('changed');self.assertFalse(self.result()['publishing_allowed']);(self.root/'candidate.py').write_text('original');(self.root/'result.json').write_text('{}');self.assertFalse(self.result()['publishing_allowed'])
 def test_removed_required_scope_denies(self):self.gate['required_open_tasks'].pop();self.assertFalse(self.result()['publishing_allowed'])
 def test_open_findings_native_or_excess_budget_denies(self):
  self.gate['findings']=[{'id':'new','status':'open'}];self.assertFalse(self.result()['publishing_allowed']);self.gate['findings']=[];self.gate['unreconciled_native']=['unknown'];self.assertFalse(self.result()['publishing_allowed']);self.gate['unreconciled_native']=[];self.state['tasks'][0]['repairs_used']=3;self.assertFalse(self.result()['publishing_allowed'])
 def test_symlink_evidence_and_other_destination_denied(self):
  p=self.root/'result.json';p.unlink();p.symlink_to(self.root/'candidate.py');self.assertFalse(self.result()['publishing_allowed']);self.assertFalse(check(self.root,'Urizums/A111:main')['publishing_allowed'])

if __name__=='__main__':unittest.main()
