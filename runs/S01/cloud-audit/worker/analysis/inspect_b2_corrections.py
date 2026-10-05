#!/usr/bin/env python3
"""Summarize original B2 worker and coordinator correction-related raw captures."""
import json
from pathlib import Path
ROOT=Path('/workspace/A111')
SRC=ROOT/'runs/S01/cloud-audit/worker/analysis/extracted_sources.json'
OUT=ROOT/'runs/S01/cloud-audit/worker/analysis/b2_corrections.json'
entries=json.loads(SRC.read_text(encoding='utf-8'))['samples']['package/B2']
by={e['path']:e for e in entries}
result={'schema':'c1-b2-corrections-review/1','worker':{},'coordinator_index_analysis':[],'correction_capture_jsonl':None}
for e in entries:
    p=e['path']; n=Path(p).name
    if p.endswith('/artifacts/actions.json') or p.endswith('/artifacts/worker-reply.json') or p.endswith('/artifacts/worker-reply.draft.json') or p.endswith('/artifacts/explanation.zh.md') or '/artifacts/logs/' in p:
        result['worker'][p]={'sha256':e['sha256'],'data':e.get('data'),'text':e.get('text')}
    if '/logs/' in p and n[:3].isdigit() and 27 <= int(n[:3]) <= 36:
        d=e.get('data',{})
        result['coordinator_index_analysis'].append({'path':p,'sha256':e['sha256'],'argv':d.get('argv'),'exit_code':d.get('exit_code'),'stdout':d.get('stdout'),'stderr':d.get('stderr'),'begin':d.get('begin'),'end':d.get('end')})
    if p.endswith('/artifacts/process-captures.jsonl'):
        result['correction_capture_jsonl']={'path':p,'sha256':e['sha256'],'lines':e.get('lines')}
for name in ['evidence/c1/package/B2/index.json','evidence/c1/package/B2/review/results.json','evidence/c1/package/B2/review/package-assess.json','evidence/c1/package/B2/review/decision.draft.json','evidence/c1/package/B2/review/decision-preflight.json','evidence/c1/package/B2/review/decision.json','evidence/c1/package/B2/job/ledger.json']:
    if name in by: result[name]=by[name].get('data')
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Human stdout deliberately limits artifacts to exact command/correction records.
print(json.dumps({'output':str(OUT),'worker_records':len(result['worker']),'coordinator_index_analysis_records':len(result['coordinator_index_analysis']),'process_capture_lines':len((result['correction_capture_jsonl'] or {}).get('lines',[]))},ensure_ascii=False))
