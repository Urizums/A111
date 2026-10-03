#!/usr/bin/env python3
"""Capture actual execution of the new reply-writing script."""
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path('/workspace/A111')
HERE=ROOT/'runs/S01/cloud-audit/worker/analysis'
argv=[sys.executable,str(HERE/'write_reply.py')]
run=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
record={'schema':'offline-audit-command/1','argv':argv,'cwd':str(ROOT),'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
out=HERE/'write_reply.command.json'
out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'record':str(out),'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},ensure_ascii=False))
raise SystemExit(run.returncode)
