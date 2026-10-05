#!/usr/bin/env python3
"""Summarize raw marker timelines and action artifacts from frozen C1 sources."""
import json
from pathlib import Path
ROOT = Path('/workspace/A111')
SRC = ROOT / 'runs/S01/cloud-audit/worker/analysis/extracted_sources.json'
EXPECTED = ROOT / 'runs/S01/cloud-audit/worker/analysis/expected_package_actions.json'
OUT = ROOT / 'runs/S01/cloud-audit/worker/analysis/marker_summary.json'
src = json.loads(SRC.read_text(encoding='utf-8'))
expected = json.loads(EXPECTED.read_text(encoding='utf-8'))
report = {'schema':'c1-marker-summary/1', 'samples':{}}
for sample_id, entries in src['samples'].items():
    markers=[]
    native=[]
    waits=[]
    captures=[]
    receipts=[]
    found={}
    for entry in entries:
        data=entry.get('data')
        p=entry['path']
        if isinstance(data, dict):
            if data.get('schema') == 'forge-comparison-marker/1' or data.get('schema') == 'forge-comparison-worker-marker/1':
                markers.append({'path':p,'actor':data.get('actor'),'stage':data.get('stage'),'event':data.get('event'),'utc':data.get('utc'),'monotonic_ns':data.get('monotonic_ns'),'boot_id':data.get('boot_id')})
            if '/native/' in p:
                native.append({'path':p,'data':data})
                if 'wait' in p.lower() or 'notification' in p.lower() or 'wait' in json.dumps(data).lower(): waits.append({'path':p,'data':data})
            if '/job/receipts/' in p: receipts.append({'path':p,'data':data})
            if data.get('schema') == 'forge-comparison-cli/1':
                captures.append({'path':p,'argv':data.get('argv'),'exit_code':data.get('exit_code'),'elapsed_seconds':data.get('elapsed_seconds'),'begin':data.get('begin'),'end':data.get('end'),'stdout':data.get('stdout'),'stderr':data.get('stderr')})
            name=Path(p).name
            if name in {'actions.json','actions.rejected.json','worker-reply.json','worker-reply.draft.json','decision.json','coordinator-decision.json','decision-preflight.json','check-decision.json','results.json','source-check-output.json','source-check-output.v2.json'}:
                found[p]=data
        elif 'lines' in entry and ('capture' in entry['path'] or 'process-captures' in entry['path']):
            found[entry['path']]=entry['lines']
    markers.sort(key=lambda x:(x.get('monotonic_ns') is None, x.get('monotonic_ns') or 0, x['path']))
    spans=[]
    by={}
    for m in markers: by.setdefault((m['actor'],m['stage']),{}).setdefault(m['event'],[]).append(m)
    for (actor,stage), events in sorted(by.items()):
        begins=events.get('begin',[]); ends=events.get('end',[])
        span={'actor':actor,'stage':stage,'begin_count':len(begins),'end_count':len(ends),'valid':False}
        if len(begins)==1 and len(ends)==1:
            b,e=begins[0],ends[0]
            span.update({'begin_path':b['path'],'end_path':e['path'],'begin_monotonic_ns':b['monotonic_ns'],'end_monotonic_ns':e['monotonic_ns'],'begin_boot_id':b['boot_id'],'end_boot_id':e['boot_id']})
            span['valid']=bool(b['boot_id']==e['boot_id'] and b['monotonic_ns'] is not None and e['monotonic_ns'] is not None and e['monotonic_ns']>=b['monotonic_ns'])
            if span['valid']: span['elapsed_seconds']=(e['monotonic_ns']-b['monotonic_ns'])/1e9
        spans.append(span)
    sample={'marker_count':len(markers),'markers':markers,'spans':spans,'native_count':len(native),'native_records':native,'wait_records':waits,'receipt_count':len(receipts),'receipts':receipts,'cli_capture_count':len(captures),'cli_captures':captures,'business_and_decision_records':found}
    if sample_id.startswith('package/'):
        action_records=[(p,v) for p,v in found.items() if Path(p).name=='actions.json']
        sample['expected_package_actions']=expected['actions']
        sample['action_comparisons']=[]
        for p, value in action_records:
            actual=value.get('actions') if isinstance(value,dict) else None
            sample['action_comparisons'].append({'path':p,'actual':actual,'matches_expected':actual==expected['actions']})
    report['samples'][sample_id]=sample
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(OUT),'samples':{k:{'markers':v['marker_count'],'valid_spans':sum(bool(s.get('valid')) for s in v['spans']),'invalid_or_incomplete_spans':sum(not s.get('valid') for s in v['spans']),'native':v['native_count'],'waits':len(v['wait_records']),'receipts':v['receipt_count'],'cli_captures':v['cli_capture_count'],'actions':v.get('action_comparisons',[])} for k,v in report['samples'].items()}},ensure_ascii=False))
