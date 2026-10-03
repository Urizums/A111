#!/usr/bin/env python3
"""Build an independent raw marker/native/receipt matrix for the eight frozen samples."""
import hashlib,json
from pathlib import Path
ROOT=Path('/workspace/A111')
SRC=ROOT/'runs/S01/cloud-audit/worker/analysis/extracted_sources.json'
OUT=ROOT/'runs/S01/cloud-audit/worker/analysis/trace_matrix.json'
src=json.loads(SRC.read_text(encoding='utf-8'))
report={'schema':'c1-independent-trace-matrix/1','samples':{}}
for sample_id, entries in src['samples'].items():
    markers=[]; natives=[]; waits=[]; queries=[]; receipts=[]; chain=[]; stages={}
    for e in entries:
        p=e['path']; d=e.get('data'); name=Path(p).name
        if isinstance(d,dict) and d.get('schema')=='forge-comparison-marker/1':
            m={k:d.get(k) for k in ['actor','stage','event','utc','monotonic_ns','boot_id']};m['path']=p;markers.append(m)
        if '/native/' in p and isinstance(d,dict):
            natives.append({'path':p,'sha256':e['sha256'],'data':d})
            low=name.lower()
            if 'wait' in low or 'notification' in low:
                waits.append({'path':p,'sha256':e['sha256'],'data':d})
            if ('status' in low or 'query' in low) and ('return' in low or 'host-status-query' in low):
                queries.append({'path':p,'sha256':e['sha256'],'data':d})
        if '/job/receipts/' in p:
            receipts.append({'path':p,'file_sha256':e['sha256'],'data':d})
        if '/job/' in p and name in {'control.json','ledger.json','request.json'}:
            chain.append({'path':p,'sha256':e['sha256'],'data':d})
        if isinstance(d,dict) and d.get('schema')=='forge-comparison-cli/1':
            if '/logs/' in p:
                nm=name.lower()
                if any(s in nm for s in ['prepare','issue','accepted','receive','reconcile','commit','decision','check-reply','package-assess','source-check','terminal','checkpoint']):
                    out=None
                    try:out=json.loads(d.get('stdout',''))
                    except Exception:pass
                    chain.append({'path':p,'sha256':e['sha256'],'argv':d.get('argv'),'exit_code':d.get('exit_code'),'stdout':d.get('stdout'),'stderr':d.get('stderr'),'begin':d.get('begin'),'end':d.get('end'),'stdout_json':out})
    # Sort within boot; UTC is retained to show sequence across boots without comparing monotonic clocks.
    by_boot={}
    for m in markers: by_boot.setdefault(m['boot_id'],[]).append(m)
    for bid,rows in by_boot.items(): rows.sort(key=lambda m:(m.get('monotonic_ns') or -1,m['path']))
    spans=[]
    for actor_stage in sorted({(m['actor'],m['stage']) for m in markers}):
        actor,stage=actor_stage;bs=[m for m in markers if m['actor']==actor and m['stage']==stage and m['event']=='begin'];es=[m for m in markers if m['actor']==actor and m['stage']==stage and m['event']=='end']
        status='unverified'; duration=None
        if len(bs)==1 and len(es)==1:
            b,e=bs[0],es[0]
            if b['boot_id']!=e['boot_id']:status='cross_boot_unverified'
            elif b['monotonic_ns'] is None or e['monotonic_ns'] is None:status='missing_clock_unverified'
            elif e['monotonic_ns']<b['monotonic_ns']:status='reversed_unverified'
            else: status='same_boot_pair'; duration=(e['monotonic_ns']-b['monotonic_ns'])/1e9
        elif len(bs)==0 and len(es)==0: status='no_markers'
        elif len(bs)>1 or len(es)>1: status='duplicate_marker_unverified'
        elif bs: status='missing_end_unverified'
        elif es: status='missing_begin_unverified'
        spans.append({'actor':actor,'stage':stage,'status':status,'duration_seconds':duration,'begin_markers':bs,'end_markers':es})
    report['samples'][sample_id]={
      'marker_count':len(markers),'markers_by_boot':by_boot,'spans':spans,
      'native_files':natives,'wait_records':waits,'status_return_records':queries,
      'receipt_count':len(receipts),'receipts':receipts,'chain_records':chain,
      'observed_status_return_count':sum(1 for q in queries if '/return' in q['path'].lower() and not 'observer' in q['path'].lower() and (q['data'].get('agents') is not None or q['data'].get('agent_status') is not None)),
      'missing_any_setup_marker':not any(m['stage']=='setup' for m in markers),
    }
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(OUT),'samples':{k:{'markers':v['marker_count'],'boots':len(v['markers_by_boot']),'spans':{x['actor']+':'+x['stage']:x['status'] for x in v['spans']},'wait_records':len(v['wait_records']),'status_return_files':len(v['status_return_records']),'receipts':v['receipt_count']} for k,v in report['samples'].items()}},ensure_ascii=False))
