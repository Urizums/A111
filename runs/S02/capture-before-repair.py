#!/usr/bin/env python3
"""Observer only: exclusive captures and same-boot monotonic stage markers."""
import argparse
import base64
from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

def stamp():
    return {'utc':datetime.now(timezone.utc).isoformat(), 'monotonic_ns':time.monotonic_ns(), 'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}

def exclusive(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('cli');c.add_argument('--record',required=True);c.add_argument('--actor',required=True);c.add_argument('argv',nargs=argparse.REMAINDER)
    m=sub.add_parser('mark');m.add_argument('--events',required=True);m.add_argument('--actor',required=True);m.add_argument('--stage',required=True);m.add_argument('--event',choices=['begin','end'],required=True)
    n=sub.add_parser('native');n.add_argument('--record',required=True);n.add_argument('--actor',required=True);n.add_argument('--tool',required=True);n.add_argument('--event',choices=['intent','return'],required=True);n.add_argument('--payload',required=True)
    a=p.parse_args()
    if a.command=='mark':
        s=stamp();value={'schema':'forge-comparison-marker/1','actor':a.actor,'stage':a.stage,'event':a.event,**s}
        target=Path(a.events)/(str(s['monotonic_ns'])+'_'+uuid.uuid4().hex+'.json')
        exclusive(target,value);print(json.dumps({'marker':str(target),**value}));return 0
    if a.command=='native':
        raw=Path(a.payload).read_bytes()
        value={'schema':'forge-comparison-native-observer/1','actor':a.actor,'tool':a.tool,'event':a.event,**stamp(),'payload_path':str(Path(a.payload).resolve()),'payload_sha256':hashlib.sha256(raw).hexdigest(),'payload':json.loads(raw),'raw_base64':base64.b64encode(raw).decode(),'scope':'Local before-call intent or after-import observation, not provider timing or authenticated tool evidence'}
        exclusive(a.record,value);print(json.dumps({'record':str(Path(a.record).resolve()),'tool':a.tool,'event':a.event}));return 0
    argv=a.argv[1:] if a.argv and a.argv[0]=='--' else a.argv
    if not argv:p.error('actual argv required after --')
    target=Path(a.record)
    if target.exists():p.error('capture destination exists; preserve it and use a new path')
    begin=stamp()
    result=subprocess.run(argv,capture_output=True)
    end=stamp()
    value={'schema':'forge-comparison-cli/1','actor':a.actor,'cwd':str(Path.cwd()),'argv':argv,'begin':begin,'end':end,'exit_code':result.returncode,'elapsed_seconds':(end['monotonic_ns']-begin['monotonic_ns'])/1e9,'stdout':result.stdout.decode('utf-8',errors='replace'),'stderr':result.stderr.decode('utf-8',errors='replace'),'stdout_base64':base64.b64encode(result.stdout).decode(),'stderr_base64':base64.b64encode(result.stderr).decode()}
    exclusive(target,value)
    sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr)
    return result.returncode

if __name__=='__main__':raise SystemExit(main())
