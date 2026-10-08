from pathlib import Path
import subprocess,sys,time,json,datetime,hashlib
ROOT=Path(__file__).resolve().parents[1]
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':
 total=time.perf_counter()
 for n in ['check_cases','check_patterns','audit_v2']:
  d=ROOT/'logs/checks'/n;d.mkdir(parents=True,exist_ok=True);cmd=[sys.executable,'-X','utf8','-B',str(ROOT/'code'/f'{n}.py')];start=time.perf_counter();limit=max(1,180-(start-total));receipt={'command':cmd,'utc_start':datetime.datetime.now(datetime.timezone.utc).isoformat(),'remaining_suite_window_seconds':limit,'script_sha256':hashlib.sha256((ROOT/'code'/f'{n}.py').read_bytes()).hexdigest()}
  dump(d/'start.json',receipt)
  with (d/'stdout.log').open('w',encoding='utf8') as so,(d/'stderr.log').open('w',encoding='utf8') as se:
   p=subprocess.Popen(cmd,stdout=so,stderr=se);receipt['pid']=p.pid
   try:receipt['exit']=p.wait(timeout=limit);receipt['timeout']=False
   except subprocess.TimeoutExpired:p.kill();p.wait();receipt['exit']=p.returncode;receipt['timeout']=True
  receipt.update({'outer_seconds':time.perf_counter()-start,'utc_finish':datetime.datetime.now(datetime.timezone.utc).isoformat()});dump(d/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
  if receipt['exit']!=0:raise RuntimeError('check failure, receipt/stderr preserved: '+n)
 # CLI failure using real current C smoke.
 import csv
 with (ROOT/'checks/smoke_C/placements.csv').open(encoding='utf-8-sig') as f:rr=list(csv.DictReader(f))
 rr[0]['z_mm']='10000'
 from main import csvwrite
 csvwrite(ROOT/'checks/rejected_C_placements.csv',rr)
 cmd=[sys.executable,'-X','utf8','-B',str(ROOT/'code/validate.py'),'--placements',str(ROOT/'checks/rejected_C_placements.csv'),'--items',str(ROOT/'data/items.csv'),'--vehicles',str(ROOT/'data/vehicles.json'),'--partial','--output',str(ROOT/'checks/cli_rejection.json')];a=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=10);dump(ROOT/'logs/checks/cli_receipt.json',{'command':cmd,'exit':a.returncode,'stdout':a.stdout,'stderr':a.stderr});assert a.returncode==2
 print('actual CLI rejection exit2; suite terminal',flush=True)
