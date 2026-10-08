"""Consumer replay/solve interface. Every new output goes into a fresh v2 attempt."""
import argparse,sys,json
from pathlib import Path
from receipts import Registry,OLD
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['replay','solver','inspect','reconcile'],required=True);ap.add_argument('--input');ap.add_argument('--task',default='Q1-S1');a=ap.parse_args();r=Registry()
    if a.mode=='inspect':print(json.dumps(r.inspect(),ensure_ascii=False));return
    if a.mode=='reconcile':print(json.dumps(r.reconcile_terminal(),ensure_ascii=False));return
    if a.mode=='replay':argv=[sys.executable,'-X','utf8','-B',str(OLD/'src/reproduce.py'),'--out','{ATTEMPT}/output']
    else:
        argv=[sys.executable,'-X','utf8','-B',str(OLD/'src/solver.py'),'--task',a.task,'--out','{ATTEMPT}/output']
        if a.input:argv+=['--input',str(Path(a.input).resolve())]
    pid=r.start(argv,a.mode);receipt=r.finish(pid);print(json.dumps(receipt,ensure_ascii=False));raise SystemExit(0 if receipt['status']=='complete' else 2)
if __name__=='__main__':main()
