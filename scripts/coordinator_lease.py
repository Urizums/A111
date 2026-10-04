"""Cooperative single-checkout coordinator lease; no distributed/provider guarantee."""
import argparse,fcntl,json,os,sys
from datetime import datetime,timezone
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['probe','hold']);p.add_argument('--root',type=Path,required=True);p.add_argument('--owner');a=p.parse_args();state=a.root/'state';state.mkdir(exist_ok=True);metadata=state/'coordinator-lease.json'
    with (state/'coordinator.lock').open('a') as lock:
        try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            info=json.loads(metadata.read_text()) if metadata.exists() else None
            print(json.dumps({'acquired':False,'busy':True,'holder':info,'action':'use_existing_coordinator_or_wait'}),flush=True);return 3 if a.action=='hold' else 0
        if a.action=='probe':
            print(json.dumps({'busy':False,'acquired':False,'action':'eligible_to_claim_after_reconciling_native_calls'}));return 0
        if not a.owner:p.error('--owner required for hold')
        info={'owner':a.owner,'pid':os.getpid(),'acquired_at':datetime.now(timezone.utc).isoformat(),'scope':'single checkout advisory file lock, not distributed host isolation'};metadata.write_text(json.dumps(info,indent=2)+'\n');print(json.dumps({'acquired':True,'busy':True,'holder':info}),flush=True)
        for line in sys.stdin:
            if line.strip()=='release':break
        info['released_at']=datetime.now(timezone.utc).isoformat();metadata.write_text(json.dumps(info,indent=2)+'\n');print(json.dumps({'released':True}),flush=True);return 0

if __name__=='__main__':raise SystemExit(main())
