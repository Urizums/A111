#!/usr/bin/env python3
"""List all nonzero captured subprocesses in the original B2 sample."""
import json
from pathlib import Path
src=Path('/workspace/A111/runs/S01/cloud-audit/worker/analysis/extracted_sources.json')
data=json.loads(src.read_text(encoding='utf-8'))
for sample in ['package/B2','project/B2']:
    print('\n## '+sample)
    for e in data['samples'][sample]:
        r=e.get('data')
        if isinstance(r,dict) and r.get('schema')=='forge-comparison-cli/1' and r.get('exit_code') not in (0,None):
            print(json.dumps({'path':e['path'],'exit_code':r['exit_code'],'argv':r.get('argv'),'stdout':r.get('stdout'),'stderr':r.get('stderr'),'sha256':e['sha256']},ensure_ascii=False))
