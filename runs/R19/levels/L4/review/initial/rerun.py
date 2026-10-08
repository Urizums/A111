from pathlib import Path
import subprocess,time,json
OUT=Path(__file__).resolve().parent
def main():
    c=OUT/'consumer';args=['py','-3.12','-X','utf8','-B','code/solve.py','--data','data/raw_rebuilt.json','--config','configs/refined.json','--out','reviewer_new_run','--method','maxrects']
    assert not (c/'reviewer_new_run').exists()
    start=time.perf_counter()
    with (OUT/'clean-rerun-stdout.txt').open('w',encoding='utf-8') as f:
        proc=subprocess.run(args,cwd=c,stdout=f,stderr=subprocess.STDOUT,text=True)
    receipt={'command':args,'cwd':str(c),'input':'direct raw reconstructed fields, matching official original',
             'exit_code':proc.returncode,'elapsed_seconds':time.perf_counter()-start,'process_id':None,
             'status':'finished','ongoing_process':False}
    (OUT/'clean-rerun-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))
    raise SystemExit(proc.returncode)
if __name__=='__main__':main()
