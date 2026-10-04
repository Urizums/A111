"""Inspect safe runtime capabilities; never read credential values."""
import importlib.util,json,os,shutil,sqlite3,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
out=Path(__file__).parent
commands=[['python3.10','--version'],['chromium','--version'],['gh','api','repos/waw1w1/A111/actions/permissions'],['gh','api','repos/waw1w1/A111/actions/workflows'],['gh','api','repos/waw1w1/A111/actions/runs?per_page=5']]
rows=[]
for argv in commands:
 r=subprocess.run(argv,capture_output=True,text=True,timeout=25);rows.append(dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
probe=dict(at=datetime.now(timezone.utc).isoformat(),python=sys.version,sqlite=sqlite3.sqlite_version,playwright=bool(importlib.util.find_spec('playwright')),commands=rows,
 credential_presence_only={k:bool(os.environ.get(k)) for k in ['OPENAI_API_KEY','ANTHROPIC_API_KEY']},
 boundary='Presence does not prove authorization or provider support; no credential values inspected, no API billing invoked.',
 known_native='Actual collaboration tool creation/running/completion receipts in R01/R02/R03. Not a standalone provider SDK.',
 global_telemetry='No callable provider-global concurrency/token/cost/cancel-ack telemetry supplied by this host.',
 background='Scheduled automation connector is callable; code-executor availability in a future run is not established.')
(out/'probe.json').write_text(json.dumps(probe,indent=2)+'\n');print(json.dumps({k:v for k,v in probe.items() if k!='commands'},indent=2))
