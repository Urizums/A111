#!/usr/bin/env python3
"""Run the new read-only audit finalizer and retain its actual command result."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path('/workspace/A111')
HERE=ROOT/'runs/S01/cloud-audit/worker/analysis'
SCRIPT=HERE/'finalize_audit.py'
OUT=HERE/'finalize_audit.command.json'
argv=[sys.executable,str(SCRIPT)]
run=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
record={'schema':'offline-audit-command/1','argv':argv,'cwd':str(ROOT),'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'record':str(OUT),'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},ensure_ascii=False))
raise SystemExit(run.returncode)
