#!/usr/bin/env python3
"""Capture actual results from the permitted current hostdraft reply/check commands."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path('/workspace/A111')
WORK=ROOT/'runs/S01/cloud-audit/worker'
ANALYSIS=WORK/'analysis'
REQUEST=ROOT/'runs/S01/cloud-audit/job/request.json'
HOSTDRAFT=ROOT/'skills/forge-agent-flow/scripts/hostdraft.py'

if len(sys.argv)!=2 or sys.argv[1] not in {'reply','check'}:
    raise SystemExit('usage: capture_hostdraft.py reply|check')
mode=sys.argv[1]
if mode=='reply':
    DRAFT=WORK/'hostdraft_reply_draft.json'
    argv=[sys.executable,str(HOSTDRAFT),'reply','--request',str(REQUEST),
          '--artifact',str(WORK/'audit.json'),'--artifact',str(WORK/'report.md'),
          '--out',str(DRAFT)]
    OUT=ANALYSIS/'hostdraft_reply.command.json'
else:
    REPLY=WORK/'reply.json'
    argv=[sys.executable,str(HOSTDRAFT),'check-reply','--request',str(REQUEST),'--reply',str(REPLY)]
    OUT=ANALYSIS/'hostdraft_check_reply.command.json'

run=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
record={'schema':'offline-hostdraft-command/1','mode':mode,'argv':argv,'cwd':str(ROOT),
        'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'record':str(OUT),'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},ensure_ascii=False))
raise SystemExit(run.returncode)
