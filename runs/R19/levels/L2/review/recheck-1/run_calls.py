from pathlib import Path
import sys,json,subprocess,datetime,time,hashlib,zipfile,shutil
B=Path.cwd();O=B/'runs/R19/levels/L2/review/recheck-1';E=B/'runs/R19/levels/L2/execution-v2'
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def run(label,cmd,limit,cwd=B):
 p=O/(label+'.receipt.json')
 if p.exists():raise RuntimeError('Refuse repeat receipt '+label)
 st=time.perf_counter();r={'label':label,'argv':list(map(str,cmd)),'cwd':str(cwd),'utc_start':datetime.datetime.now(datetime.timezone.utc).isoformat(),'limit_seconds':limit,'model':None,'tokens':None,'cost':None}
 dump(O/(label+'.start.json'),r)
 with (O/(label+'.stdout.log')).open('w',encoding='utf-8') as so,(O/(label+'.stderr.log')).open('w',encoding='utf-8') as se:
  child=subprocess.Popen(cmd,cwd=cwd,stdout=so,stderr=se);r['pid']=child.pid;dump(O/(label+'.start.json'),r)
  try:r['exit']=child.wait(timeout=limit);r['timeout']=False
  except subprocess.TimeoutExpired:child.kill();child.wait();r['exit']=child.returncode;r['timeout']=True
 r.update(seconds=time.perf_counter()-st,utc_finish=datetime.datetime.now(datetime.timezone.utc).isoformat());dump(p,r);print(json.dumps(r,ensure_ascii=False),flush=True);return r
if __name__=='__main__':
 Z=O/'zip_staged'
 assert not Z.exists()
 with zipfile.ZipFile(E/'algorithm.zip') as z:
  for n in z.namelist():assert not Path(n).is_absolute() and '..' not in Path(n).parts
  z.extractall(Z)
 hashes=[]
 for p in (Z/'code').glob('*.py'):
  q=E/'code'/p.name;hashes.append({'name':p.name,'zip_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'matches_current_code':q.exists() and p.read_bytes()==q.read_bytes()})
 dump(O/'zip-code-receive.json',hashes)
 assert all(x['matches_current_code'] for x in hashes)
 run('zip_full_raw',[sys.executable,'-X','utf8','-B',str(Z/'code/main.py'),'--raw',str(E/'raw'),'--config',str(Z/'configs/main.json'),'--output',str(Z/'results/full')],300)
