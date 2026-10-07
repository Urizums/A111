"""Serial seed-major, complete pipeline budgets; preserves every receipt."""
from pathlib import Path
import sys,json,time,subprocess,datetime,hashlib
ROOT=Path(__file__).resolve().parents[1]
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def child(cfg,out):
 import main,blocks
 items=main.readitems(ROOT/'data/items.csv');vs=json.loads((ROOT/'data/vehicles.json').read_text())
 main.solve(items,vs,cfg,out)
 main.dump(out/'block_certificates.json',blocks.CERTIFICATES)
def run():
 win=json.loads((ROOT/'research/window.json').read_text());rows=[]
 for seed in win['comparison']['seeds']:
  for method in win['comparison']['methods']:
   name=f'{method}_seed{seed}';out=ROOT/'research/comparison'/name;out.mkdir(parents=True,exist_ok=True)
   if (out/'receipt.json').exists():raise RuntimeError('Refuse repeat existing '+name)
   cfg={'seed':seed,'starts':22,'time_limit':45,'pressure':500,'platforms':method!='A','geometry':method}
   dump(out/'config.json',cfg);start=time.perf_counter();receipt={'case':name,'config':cfg,'utc_start':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':[sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),'--child',str(out)],'code_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'code').glob('*.py')},'outer_limit_seconds':300,'model':None,'tokens':None,'cost':None}
   dump(out/'start.json',receipt)
   with (out/'stdout.log').open('w',encoding='utf8') as so,(out/'stderr.log').open('w',encoding='utf8') as se:
    p=subprocess.Popen(receipt['command'],stdout=so,stderr=se)
    receipt['pid']=p.pid;dump(out/'start.json',receipt)
    try:receipt['returncode']=p.wait(timeout=300);receipt['timeout']=False
    except subprocess.TimeoutExpired:p.kill();p.wait();receipt['returncode']=p.returncode;receipt['timeout']=True
   receipt.update({'outer_seconds':time.perf_counter()-start,'utc_finish':datetime.datetime.now(datetime.timezone.utc).isoformat()});dump(out/'receipt.json',receipt)
   row={'case':name,'method':method,'seed':seed,'outer_seconds':receipt['outer_seconds'],'exit':receipt['returncode'],'timeout':receipt['timeout']}
   if (out/'summary.json').exists():
    s=json.loads((out/'summary.json').read_text());row.update({'library_size':s['library_size'],'self_seconds':s['seconds']})
    for r in s['runs']:
     if r['method']=='column_patterns_MILP':row[r['scenario']+'_vehicles']=r['vehicle_count'];row[r['scenario']+'_cost']=r['cost_yuan'];row[r['scenario']+'_gap']=r['solver']['restricted_mip_gap']
   rows.append(row);dump(ROOT/'research/comparison/progress.json',rows);print(json.dumps(row),flush=True)
 dump(ROOT/'research/comparison/summary.json',rows)
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='--child':
  out=Path(sys.argv[2]);child(json.loads((out/'config.json').read_text()),out)
 else:run()
