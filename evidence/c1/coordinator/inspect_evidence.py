#!/usr/bin/env python3
"""Read current C1 originals; missing/incomplete data is never a zero duration."""
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics

BASE=Path(__file__).resolve().parents[1]
SKILL=Path('/root/.codex/skills/remote-skills/skill-6ab323b7c2a081919b95502e8e7297f0')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def frozen_ref(p):
    path=Path(p)
    snapshot=BASE/'coordinator/cutoff-snapshot'
    if snapshot.exists():
        try:rel=path.relative_to(BASE)
        except ValueError:return path
        if rel.parts and rel.parts[0] in {'project','shared'}:return snapshot/rel
    return path

def stage(markers,actor,name):
    begin=[x for x in markers if x.get('actor')==actor and x.get('stage')==name and x.get('event')=='begin']
    end=[x for x in markers if x.get('actor')==actor and x.get('stage')==name and x.get('event')=='end']
    if len(begin)!=1 or len(end)!=1:
        return {'verified':False,'seconds':None,'reason':'missing or multiple markers','begin_count':len(begin),'end_count':len(end)}
    a,b=begin[0],end[0]
    if a['boot_id']!=b['boot_id'] or b['monotonic_ns']<a['monotonic_ns']:
        return {'verified':False,'seconds':None,'reason':'different boot or reversed clock','begin':a,'end':b}
    return {'verified':True,'seconds':(b['monotonic_ns']-a['monotonic_ns'])/1e9,'boot_id':a['boot_id'],'begin_ns':a['monotonic_ns'],'end_ns':b['monotonic_ns']}

freeze=read(BASE/'coordinator/Study_Freeze.json')
samples=[]
for block,order in freeze['orders'].items():
 for name in order:
    run=(BASE/'coordinator/cutoff-snapshot'/block/name) if block=='project' and (BASE/'coordinator/cutoff-snapshot/Snapshot_Manifest.json').exists() else BASE/block/name
    cli=[];markers=[];native=[];pending_json=[]
    control_path=run/'job/control.json'
    control=read(control_path) if control_path.exists() else None
    worker_alias=(control.get('worker') or '').split('/')[-1] if control else ''
    record_paths=set(run.rglob('*.json')) | set(run.rglob('*.jsonl'))
    extra_shared=set()
    if block=='project' and worker_alias:
        snapshot_shared=BASE/'coordinator/cutoff-snapshot/shared'
        for outside in snapshot_shared.rglob('*.jsonl'):
            try:outside_value=read(outside)
            except (ValueError,OSError):continue
            if isinstance(outside_value,dict) and outside_value.get('actor')==worker_alias and outside_value.get('schema')=='forge-comparison-cli/1':extra_shared.add(outside)
        record_paths |= extra_shared
    for path in sorted(record_paths):
        try:value=read(path)
        except (ValueError,OSError):pending_json.append(str(path.relative_to(BASE)));continue
        if not isinstance(value,dict):continue
        schema=value.get('schema')
        if schema=='forge-comparison-cli/1':cli.append({'path':str(path.relative_to(BASE)),**value})
        elif schema=='forge-comparison-marker/1':
            item={'path':str(path.relative_to(BASE)),**value}
            if worker_alias and item.get('actor')==worker_alias:item['raw_actor']=item['actor'];item['actor']='worker'
            markers.append(item)
        elif schema=='forge-comparison-native-observer/1':native.append({'path':str(path.relative_to(BASE)),**value})
    captures=[]
    for entry in cli:
        try:
            stdout=base64.b64decode(entry['stdout_base64'],validate=True)
            stderr=base64.b64decode(entry['stderr_base64'],validate=True)
            raw_ok=stdout.decode('utf-8',errors='replace')==entry['stdout'] and stderr.decode('utf-8',errors='replace')==entry['stderr']
            same_boot=entry['begin']['boot_id']==entry['end']['boot_id']
            seconds=(entry['end']['monotonic_ns']-entry['begin']['monotonic_ns'])/1e9
            duration_ok=same_boot and seconds>=0 and abs(seconds-entry['elapsed_seconds'])<1e-8
        except (ValueError,KeyError,TypeError):raw_ok=False;duration_ok=False
        captures.append({'path':entry['path'],'raw_bytes_valid':raw_ok,'duration_valid':duration_ok})
    native_checks=[]
    for entry in native:
        try:
            raw=base64.b64decode(entry['raw_base64'],validate=True)
            ok=hashlib.sha256(raw).hexdigest()==entry['payload_sha256'] and json.loads(raw)==entry['payload'] and sha(frozen_ref(entry['payload_path']))==entry['payload_sha256']
        except (ValueError,KeyError,TypeError,OSError):ok=False
        native_checks.append({'path':entry['path'],'payload_bytes_valid':ok,'tool':entry.get('tool'),'event':entry.get('event')})
    times={x:stage(markers,'coordinator',x) for x in ['setup','receive','review','decision','commit']}
    times.update({x:stage(markers,'worker',x) for x in ['worker_work','worker_reply']})
    control_path=run/'job/control.json'
    control=read(control_path) if control_path.exists() else None
    refs=[]
    if control:
        for ref in control['refs']:
            try:ok=sha(frozen_ref(ref['path']))==ref['sha256']
            except OSError:ok=False
            refs.append({'path':ref['path'],'hash_valid':ok})
    worker_preflights=[];decision_preflights=[]
    generators=[]
    for entry in cli:
        argv=entry['argv']
        if not any(str(x).endswith('/hostdraft.py') for x in argv):continue
        if 'check-reply' in argv and entry.get('actor') in {'worker',worker_alias}:worker_preflights.append(entry)
        if 'check-decision' in argv:decision_preflights.append(entry)
        if 'reply' in argv or 'decision' in argv:generators.append({'path':entry['path'],'argv':argv,'exit_code':entry['exit_code'],'actor':entry.get('actor')})
    worker_preflight_order=[]
    for entry in worker_preflights:
        t=times['worker_reply'];ok=t['verified'] and entry['end']['boot_id']==t.get('boot_id') and entry['begin']['monotonic_ns']>=t.get('begin_ns',0) and entry['end']['monotonic_ns']<=t.get('end_ns',-1)
        try:payload=json.loads(entry['stdout']);valid=entry['exit_code']==0 and payload['status']=='payload_valid'
        except (ValueError,KeyError):valid=False
        completed=[]
        if control and control.get('worker'):
            for n in native:
                if n.get('event')!='return' or n.get('tool','').split('.')[-1]!='list_agents':continue
                if any(a.get('agent_name')==control['worker'] and isinstance(a.get('agent_status'),dict) and 'completed' in a['agent_status'] for a in n.get('payload',{}).get('agents',[])):
                    completed.append(n)
        before_observed=None if not completed else any(entry['end']['boot_id']==n['boot_id'] and entry['end']['monotonic_ns']<=n['monotonic_ns'] for n in completed)
        worker_preflight_order.append({'path':entry['path'],'payload_valid':valid,'inside_worker_reply_span':ok,'before_actual_completed_snapshot_import':before_observed})
    intents=Counter(x.get('tool','').split('.')[-1] for x in native if x.get('event')=='intent')
    returns=Counter(x.get('tool','').split('.')[-1] for x in native if x.get('event')=='return')
    combined=None
    if times['worker_reply']['verified'] and times['decision']['verified']:
        combined=times['worker_reply']['seconds']+times['decision']['seconds']
    samples.append({'block':block,'sample':name,'evidence_scope':'project cutoff snapshot; worker may still run' if block=='project' else 'original package records','treatment':name[0],'pair':int(name[1]),'phase':control['phase'] if control else 'not_prepared','worker':control.get('worker') if control else None,'attempt_id':control['request']['attempt_id'] if control else None,'timing':times,'worker_reply_plus_decision_seconds':combined,'captured_subprocess_count':len(cli),'outside_shared_worker_capture_paths':[str(p.relative_to(BASE)) for p in sorted(extra_shared)],'capture_integrity':captures,'pending_or_invalid_json':pending_json,'native_intent_counts':dict(intents),'native_return_counts':dict(returns),'native_capture_integrity':native_checks,'bound_reference_integrity':refs,'worker_preflight_order':worker_preflight_order,'decision_preflight_capture_paths':[x['path'] for x in decision_preflights],'scaffold_generator_calls':generators,'nonzero_cli':[{'path':x['path'],'argv':x['argv'],'exit_code':x['exit_code'],'stdout':x['stdout'],'stderr':x['stderr']} for x in cli if x['exit_code']],'captured_subprocess_elapsed_seconds':sum(x['elapsed_seconds'] for x in cli)})

pairs=[]
for block in freeze['orders']:
 for pair in [1,2]:
    a=next(x for x in samples if x['block']==block and x['sample']=='A'+str(pair))
    b=next(x for x in samples if x['block']==block and x['sample']=='B'+str(pair))
    av,bv=a['worker_reply_plus_decision_seconds'],b['worker_reply_plus_decision_seconds']
    eligible=av is not None and bv is not None and a['phase']=='committed' and b['phase']=='committed' and all(t['verified'] for t in a['timing'].values()) and all(t['verified'] for t in b['timing'].values())
    pairs.append({'block':block,'pair':pair,'A_observed_seconds':av,'B_observed_seconds':bv,'B_minus_A_observed_seconds':bv-av if av is not None and bv is not None else None,'B_over_A_observed_ratio':bv/av if av is not None and bv is not None and av>0 else None,'interval_and_terminal_candidate_valid':eligible,'efficacy_grade':'not decided; source correctness, treatment, assistance and all frozen capture clauses require independent Root review'})

result={'at':datetime.now(timezone.utc).isoformat(),'read_only':True,'selected_samples':8,'source_unchanged':all(sha(SKILL/x['path'])==x['sha256'] for x in freeze['source_manifest']),'study_files_unchanged':all(sha(BASE/x['path'])==x['sha256'] for x in freeze['study_files']),'samples':samples,'pairs':pairs,'stage_scope':'Observed actor/tool/wait spans, not provider or active model duration','capture_scope':'Actual capture.py cli targets only. Marker/native observer invocations lack full subprocess fields: frozen C06 gap retained.','tokens':None,'cost':None,'provider_identity_verified':False,'speed_gain_claimed':False}
(BASE/'coordinator/Observed_Evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source_unchanged':result['source_unchanged'],'study_unchanged':result['study_files_unchanged'],'samples':[{'block':x['block'],'sample':x['sample'],'phase':x['phase'],'captured_cli':x['captured_subprocess_count'],'worker':x['worker']} for x in samples]},ensure_ascii=False,indent=2))
