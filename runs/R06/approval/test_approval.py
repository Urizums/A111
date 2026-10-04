import concurrent.futures,json,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parent
class ApprovalTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.db=self.root/'state.sqlite';self.policy=json.loads((BASE/'policy.json').read_text());self.counter=0
 def request(self,**changes):
  r=dict(request_id='req-1',idempotency_key='key-1',ticket_id='T1',expected_version=0,category='lighting',amount_cents=8000,risk='low',evidence_complete=True,requester='applicant',reviewer='reviewer');r.update(changes);return r
 def call(self,r,policy=None,extra=(),expected=0):
  self.counter+=1;p=self.root/f'request-{self.counter}.json';p.write_text(json.dumps(r));q=self.root/f'policy-{self.counter}.json';q.write_text(json.dumps(policy or self.policy));args=[sys.executable,str(BASE/'approval.py'),'--database',str(self.db),'decide',str(p),'--policy',str(q),*extra];v=subprocess.run(args,capture_output=True,text=True);self.assertEqual(v.returncode,expected,v.stdout+v.stderr);return json.loads(v.stdout or v.stderr) if v.stdout or v.stderr else None
 def inspect(self,ticket='T1'):
  r=subprocess.run([sys.executable,str(BASE/'approval.py'),'--database',str(self.db),'inspect',ticket],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);return json.loads(r.stdout)
 def test_rule_precedence_and_local_scope(self):
  cases=[({},'approved','sample_rule_match'),({'reviewer':'applicant','risk':'high'},'manual','self_review'),({'amount_cents':None},'manual','amount_unknown'),({'category':'structural'},'manual','category_review'),({'risk':'high'},'manual','risk_review'),({'evidence_complete':False},'manual','evidence_missing'),({'amount_cents':20001},'manual','amount_review')]
  for n,(fields,status,reason) in enumerate(cases):
   r=self.request(request_id=f'r{n}',idempotency_key=f'k{n}',ticket_id=f'T{n}',**fields);v=self.call(r);self.assertEqual((v['decision'],v['reason']),(status,reason));self.assertTrue(v['local_demo_only'])
 def test_disabled_policy_defaults_to_manual(self):
  p=dict(self.policy,enabled=False);self.assertEqual(self.call(self.request(),p)['reason'],'policy_disabled')
 def test_durable_idempotency_and_conflicting_payload(self):
  r=self.request();first=self.call(r);again=self.call(r);self.assertFalse(first['reused']);self.assertTrue(again['reused']);self.assertEqual(len(self.inspect()['audit']),1)
  self.call(dict(r,amount_cents=9000),expected=3);self.assertEqual(self.inspect()['ticket']['version'],1)
 def test_second_version_has_contiguous_audit_and_rejects_stale(self):
  self.call(self.request());r=self.request(request_id='r2',idempotency_key='k2',expected_version=1,risk='high');self.call(r)
  self.call(self.request(request_id='r3',idempotency_key='k3'),expected=3);v=self.inspect();self.assertEqual([x['new_version'] for x in v['audit']],[1,2]);self.assertEqual(v['ticket']['decision'],'manual')
 def test_late_process_crash_rolls_back_and_same_input_retries(self):
  r=self.request();self.call(r,extra=['--simulate-crash-before-commit'],expected=75);self.assertEqual(self.inspect(),{'ticket':None,'audit':[],'local_demo_only':True});self.call(r);self.assertEqual(len(self.inspect()['audit']),1)
 def test_two_processes_share_same_version_without_lost_audit(self):
  self.inspect();q=self.root/'policy.json';q.write_text(json.dumps(self.policy));args=[]
  for n in (1,2):
   p=self.root/f'concurrent-{n}.json';p.write_text(json.dumps(self.request(request_id=f'r{n}',idempotency_key=f'k{n}')));args.append([sys.executable,str(BASE/'approval.py'),'--database',str(self.db),'decide',str(p),'--policy',str(q)])
  with concurrent.futures.ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda a:subprocess.run(a,capture_output=True,text=True),args))
  self.assertEqual(sorted(r.returncode for r in results),[0,3]);self.assertEqual(len(self.inspect()['audit']),1)
 def test_invalid_boolean_amount_has_no_decision(self):
  self.call(self.request(amount_cents=True),expected=2);self.assertFalse(self.db.exists())

if __name__=='__main__':unittest.main()
