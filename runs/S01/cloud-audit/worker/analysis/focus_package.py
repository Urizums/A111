#!/usr/bin/env python3
"""Focus package outputs, job receipts, reviews and B2 correction history."""
import json
from pathlib import Path
ROOT=Path('/workspace/A111')
SRC=ROOT/'runs/S01/cloud-audit/worker/analysis/extracted_sources.json'
OUT=ROOT/'runs/S01/cloud-audit/worker/analysis/focused_package.txt'
src=json.loads(SRC.read_text(encoding='utf-8'))
lines=[]
def add(x=''): lines.append(str(x))
def j(x): return json.dumps(x,ensure_ascii=False,indent=2)
for sid in ['B1','A1','A2','B2']:
    sample='package/'+sid; entries=src['samples'][sample]; add('\n## '+sample)
    for e in entries:
        p=e['path']; d=e.get('data'); n=Path(p).name
        if p.endswith(('/job/control.json','/job/request.json','/job/ledger.json')) or '/job/receipts/' in p:
            add('\nPATH '+p+' SHA256 '+e['sha256']); add(j(d))
        if any(p.endswith('/'+x) for x in ['actions.json','actions.rejected.json','worker-reply.json','worker-reply.draft.json','worker-reply.preflight-rejected.json','results.json','source-checker.json','source-check-output.json','package-assess.json','package-assess-corrected.json','decision.json','coordinator-decision.json','decision-preflight.json','check-decision.json','source-review.md','解释.md','explanation.zh.md','worker-final-message.txt']):
            add('\nPATH '+p+' SHA256 '+e['sha256']); add(j(d) if 'data' in e else e.get('text',''))
    add('\nB2/CURRENT SAMPLE LOGS')
    for e in entries:
        p=e['path']; d=e.get('data')
        if isinstance(d,dict) and d.get('schema')=='forge-comparison-cli/1' and '/logs/' in p:
            name=Path(p).name
            argv=d.get('argv') or []
            relevant=('index' in name or 'correct' in name or 'assess' in name or 'result' in name or 'decision' in name or 'commit' in name or 'reconcile' in name or 'receive' in name or 'issue' in name or 'accepted' in name or 'package-next' in name)
            if sid=='B2' or relevant:
                add(j({'path':p,'exit_code':d.get('exit_code'),'argv':argv if relevant else argv[:4], 'stdout':d.get('stdout'),'stderr':d.get('stderr'),'begin':d.get('begin'),'end':d.get('end')}))
    if sid=='B2':
        add('\nB2 WORKER ARTIFACT CAPTURES')
        for e in entries:
            p=e['path']; d=e.get('data')
            if isinstance(d,dict) and d.get('schema')=='forge-comparison-cli/1' and '/artifacts/logs/' in p:
                add(j({'path':p,'argv':d.get('argv'),'exit_code':d.get('exit_code'),'stdout':d.get('stdout'),'stderr':d.get('stderr'),'begin':d.get('begin'),'end':d.get('end')}))
            if 'lines' in e and p.endswith('process-captures.jsonl'):
                add('PATH '+p+' SHA256 '+e['sha256']); add(j(e['lines']))
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'output':str(OUT),'bytes':OUT.stat().st_size,'lines':len(lines)},ensure_ascii=False))
