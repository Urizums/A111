from pathlib import Path
import subprocess,sys,time,json,datetime,hashlib
ROOT=Path(__file__).resolve().parents[1]
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':
 for i in range(36):
  d=ROOT/'logs/parameters'/f'{i:02d}';d.mkdir(parents=True,exist_ok=True)
  if (d/'receipt.json').exists():raise RuntimeError('refuse repeated completed case')
  cmd=[sys.executable,'-X','utf8','-B',str(ROOT/'code/experiments.py'),str(i)];s=time.perf_counter();receipt={'case_index':i,'command':cmd,'utc_start':datetime.datetime.now(datetime.timezone.utc).isoformat(),'outer_limit_seconds':120,'code_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'code/main.py',ROOT/'code/blocks.py',ROOT/'code/experiments.py',ROOT/'code/validate.py']},'model':None,'tokens':None,'cost':None};dump(d/'start.json',receipt)
  with (d/'stdout.log').open('w',encoding='utf8') as so,(d/'stderr.log').open('w',encoding='utf8') as se:
   p=subprocess.Popen(cmd,stdout=so,stderr=se);receipt['pid']=p.pid;dump(d/'start.json',receipt)
   try:receipt['exit']=p.wait(timeout=120);receipt['timeout']=False
   except subprocess.TimeoutExpired:p.kill();p.wait();receipt['exit']=p.returncode;receipt['timeout']=True
  receipt.update({'outer_seconds':time.perf_counter()-s,'utc_finish':datetime.datetime.now(datetime.timezone.utc).isoformat()});dump(d/'receipt.json',receipt);print(json.dumps({'case':i,'exit':receipt['exit'],'timeout':receipt['timeout'],'outer_seconds':receipt['outer_seconds']}),flush=True)
  if receipt['timeout'] or receipt['exit']!=0:
   # Nothing silently resumes or replaces a killed/unknown case.
   raise RuntimeError('case terminal failure requires diagnosis; preserved '+str(i))
