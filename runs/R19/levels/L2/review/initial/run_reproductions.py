from pathlib import Path
import subprocess,json,datetime,time,sys
base=Path.cwd();out=base/'runs/R19/levels/L2/review/initial'
def run(label,argv,cwd,limit):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter();record={'label':label,'argv':argv,'cwd':str(cwd),'utc_start':start,'individual_limit_seconds':limit,'purpose':'independent fresh reproduction; no whole-task deadline'}
 with (out/(label+'.stdout.txt')).open('w',encoding='utf-8') as f:
  try:
   p=subprocess.run(argv,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=limit);record.update(exit_code=p.returncode,timeout=False)
  except subprocess.TimeoutExpired:record.update(exit_code=None,timeout=True)
 record.update(seconds=time.perf_counter()-t,utc_finish=datetime.datetime.now(datetime.timezone.utc).isoformat(),terminal=True)
 (out/(label+'.receipt.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(record,ensure_ascii=False),flush=True)
 return record
if __name__=='__main__':
 raw=str(base/'runs/R19/inputs/raw');stage=out/'staged'
 run('full_raw_reproduction',['py','-3.12','-X','utf8','-B',str(stage/'code/main.py'),'--raw',raw,'--output',str(stage/'results/final')],base,180)
 z=out/'zip_staged'
 run('zip_smoke_reproduction',['py','-3.12','-X','utf8','-B','code/main.py','--raw','raw','--items','data/smoke_items.csv','--vehicles','data/vehicles.json','--config','smoke_config.json','--scenario','q2_cost','--output','reviewer_smoke'],z,60)
