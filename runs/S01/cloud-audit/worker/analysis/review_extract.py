#!/usr/bin/env python3
"""Emit a human-readable independent audit view of extracted original sample records."""
import json
from pathlib import Path
ROOT=Path('/workspace/A111')
SRC=ROOT/'runs/S01/cloud-audit/worker/analysis/extracted_sources.json'
OUT=ROOT/'runs/S01/cloud-audit/worker/analysis/raw_review.txt'
source=json.loads(SRC.read_text(encoding='utf-8'))
lines=[]
def add(v=''): lines.append(str(v))
def compact(v): return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def omit_base64(v):
    if isinstance(v,dict):
        return {k:('<<base64 omitted; retained in source extraction>>' if k=='raw_base64' else omit_base64(x)) for k,x in v.items()}
    if isinstance(v,list): return [omit_base64(x) for x in v]
    return v
for sample_id, entries in source['samples'].items():
    add('\n## '+sample_id)
    markers=[]
    native=[]
    caps=[]
    picked=[]
    for e in entries:
        p=e['path']; d=e.get('data')
        if isinstance(d,dict) and d.get('schema')=='forge-comparison-marker/1': markers.append((d.get('monotonic_ns') or 0,p,d))
        if '/native/' in p and isinstance(d,dict): native.append((p,d))
        if isinstance(d,dict) and d.get('schema')=='forge-comparison-cli/1': caps.append((p,d))
        basename=Path(p).name
        if basename in {'control.json','request.json','ledger.json','actions.json','actions.rejected.json','worker-reply.json','worker-reply.draft.json','worker-reply.preflight-rejected.json','results.json','source-review.md','decision.json','coordinator-decision.json','decision.draft.json','decision-preflight.json','check-decision.json','source-check-output.json','source-check-output.v2.json','summary.json','summary_zh.md','explanation.zh.md','解释.md','package-assess.json','check-package.json','worker-final-message.txt'}:
            picked.append(e)
    add('MARKERS')
    if not markers: add('(none)')
    for _,p,d in sorted(markers): add(compact({'path':p,'actor':d.get('actor'),'stage':d.get('stage'),'event':d.get('event'),'utc':d.get('utc'),'monotonic_ns':d.get('monotonic_ns'),'boot_id':d.get('boot_id')}))
    add('NATIVE CALLS AND WAITS')
    for p,d in sorted(native):
        # Full observer payload carries the raw native record. Keep it minus duplicate base64.
        add(compact({'path':p,'data':omit_base64(d)}))
    add('JOB, OUTPUT, REVIEW, DECISION RECORDS')
    for e in sorted(picked,key=lambda x:x['path']):
        add('PATH '+e['path']+' SHA256 '+e['sha256'])
        if 'data' in e: add(compact(e['data']))
        elif 'text' in e: add(e['text'])
    if sample_id.startswith('package/'):
        add('SELECTED CLI CAPTURES')
        for p,d in sorted(caps):
            n=Path(p).name.lower()
            if any(w in n for w in ['bridge','issue','receive','accepted','observe','status','wait','decision','commit','reconcile','assess','result','review','index','correct','check','draft','reply','preflight','packagectl','validate','actions','artifact','receipt']):
                add(compact({'path':p,'argv':d.get('argv'),'exit_code':d.get('exit_code'),'elapsed_seconds':d.get('elapsed_seconds'),'stdout':d.get('stdout'),'stderr':d.get('stderr'),'begin':d.get('begin'),'end':d.get('end')}))
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'output':str(OUT),'bytes':OUT.stat().st_size,'lines':len(lines)},ensure_ascii=False))
