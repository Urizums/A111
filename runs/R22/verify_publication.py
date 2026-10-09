"""Verify new frozen scopes directly from the actual committed Git blobs."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--commit',required=True);a=p.parse_args()
def git_json(name):
    return json.loads(subprocess.check_output(['git','show',name],cwd=ROOT))
current=git_json(a.commit+':state/revision-locks.json')['locks']
previous=git_json(a.commit+'^:state/revision-locks.json')['locks']
assert set(previous)<=set(current)
selected=[lock for lock in current if lock not in previous]
selected+=['runs/R20/final/candidate/C13-lock.json','runs/R21/first-diagnostic-lock.json']
command=[sys.executable,str(ROOT/'runs/R19/publication/verify_git_snapshot.py'),'--commit',a.commit]
for lock in selected:command+=['--lock',lock]
subprocess.run(command,cwd=ROOT,check=True)
print(json.dumps(dict(new_locks=len(set(current)-set(previous)),selected_locks=len(selected),
    scope='Actual committed blobs and frozen path coverage; no untracked checkout substitute or CI quality inference.')))
