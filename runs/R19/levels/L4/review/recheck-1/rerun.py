from pathlib import Path
import json,subprocess,time
OUT=Path(__file__).resolve().parent;C=OUT/'consumer'
def main():
    args=['py','-3.12','-X','utf8','-B','code/solve.py','--data','data/raw_rebuilt.json','--config','configs/refined.json','--out','reviewer_new_run','--method','maxrects']
    assert not (C/'reviewer_new_run').exists()
    start=time.perf_counter()
    with (OUT/'clean-rerun-stdout.txt').open('w',encoding='utf-8') as f:p=subprocess.run(args,cwd=C,stdout=f,stderr=subprocess.STDOUT)
    receipt={'command':args,'cwd':str(C),'exit_code':p.returncode,'elapsed_seconds':time.perf_counter()-start,'process_id':None,'status':'finished','new_archive_actual_run':True}
    (OUT/'clean-rerun-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False));raise SystemExit(p.returncode)
if __name__=='__main__':main()
