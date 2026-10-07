"""Current source staged with fresh data generated from original bytes, no incumbent answers."""
from pathlib import Path
import subprocess,sys,time,json,datetime,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 tag=sys.argv[1] if len(sys.argv)>1 else 'clean_replay_package'
 stage=ROOT/'research'/tag
 if stage.exists():raise RuntimeError('refuse overwrite existing replay')
 (stage/'code').mkdir(parents=True)
 for p in (ROOT/'code').glob('*.py'):shutil.copy2(p,stage/'code'/p.name)
 (stage/'configs').mkdir();shutil.copy2(ROOT/'configs/main.json',stage/'configs/main.json')
 cmd=[sys.executable,'-X','utf8','-B',str(stage/'code/main.py'),'--raw',str(ROOT/'raw'),'--config',str(stage/'configs/main.json'),'--output',str(stage/'results')]
 d=ROOT/'logs'/tag;d.mkdir(parents=True);s=time.perf_counter();receipt={'command':cmd,'utc_start':datetime.datetime.now(datetime.timezone.utc).isoformat(),'outer_limit_seconds':300,'main_sha256':hashlib.sha256((stage/'code/main.py').read_bytes()).hexdigest(),'no_preloaded_layouts':True,'model':None,'tokens':None,'cost':None}
 (d/'start.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
 with (d/'stdout.log').open('w',encoding='utf8') as so,(d/'stderr.log').open('w',encoding='utf8') as se:
  p=subprocess.Popen(cmd,stdout=so,stderr=se);receipt['pid']=p.pid
  (d/'start.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
  try:receipt['exit']=p.wait(timeout=300);receipt['timeout']=False
  except subprocess.TimeoutExpired:p.kill();p.wait();receipt['exit']=p.returncode;receipt['timeout']=True
 receipt.update({'outer_seconds':time.perf_counter()-s,'utc_finish':datetime.datetime.now(datetime.timezone.utc).isoformat()});(d/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
 if receipt['exit']!=0:raise RuntimeError('raw full replay failure preserved')
 shutil.copytree(stage/'results',ROOT/'results/final')
 s=json.loads((ROOT/'results/final/summary.json').read_text());print(json.dumps({'outer_seconds':receipt['outer_seconds'],'runs':[(r['scenario'],r['vehicle_count'],r['cost_yuan']) for r in s['runs'] if r['method']=='column_patterns_MILP']}))
