#!/usr/bin/env python3
"""Finalize a source-grounded offline C1 audit from this worker's raw extraction."""
import json
import hashlib
import re
import statistics
from pathlib import Path

ROOT = Path('/workspace/A111')
WORK = ROOT / 'runs/S01/cloud-audit/worker'
ANALYSIS = WORK / 'analysis'
EXTRACTED = json.loads((ANALYSIS / 'extracted_sources.json').read_text(encoding='utf-8'))
MARKERS = json.loads((ANALYSIS / 'marker_summary.json').read_text(encoding='utf-8'))['samples']
EXPECTED_PACKAGE = json.loads((ANALYSIS / 'expected_package_actions.json').read_text(encoding='utf-8'))
EXPECTED_PROJECT = json.loads((ANALYSIS / 'expected_project_summary.json').read_text(encoding='utf-8'))

SAMPLES = EXTRACTED['samples']
EXPECTED_ACTIONS = EXPECTED_PACKAGE['actions']
EXPECTED_CATEGORIES = {
    x['category']: {
        'row_count': x['count'],
        'total_fen': x['total_fen'],
        'source_ids': x['ids'],
    }
    for x in EXPECTED_PROJECT['categories']
}

def path_entry(sample, suffix):
    matches = [e for e in SAMPLES[sample] if e['path'].endswith(suffix)]
    if len(matches) != 1:
        return None
    return matches[0]

def exact_entry(sample, path):
    return next((e for e in SAMPLES[sample] if e['path'] == path), None)

def cite(e):
    return None if e is None else {'path': e['path'], 'sha256': e['sha256'], 'size_bytes': e['size_bytes']}

def cli_json(e):
    if e is None:
        return None
    d = e.get('data')
    if not isinstance(d, dict):
        return None
    try:
        return json.loads(d.get('stdout', ''))
    except (TypeError, json.JSONDecodeError):
        return None

def cli_record(e):
    if e is None:
        return None
    d = e.get('data')
    if not isinstance(d, dict):
        return None
    return {k: d.get(k) for k in ['argv', 'begin', 'end', 'exit_code', 'stdout', 'stderr'] if k in d}

def recursive_action_list(value):
    if isinstance(value, list) and all(isinstance(x, dict) and {'task','owner','due','source_quote'} <= set(x) for x in value):
        return value
    if isinstance(value, dict):
        for child in value.values():
            found = recursive_action_list(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = recursive_action_list(child)
            if found is not None:
                return found
    return None

def normalize_project(value):
    if not isinstance(value, dict):
        return None
    groups = value.get('categories', value)
    if not isinstance(groups, dict):
        return None
    result = {}
    for category, item in groups.items():
        if not isinstance(item, dict):
            return None
        count = item.get('row_count', item.get('count'))
        total = item.get('total_amount_fen', item.get('total_fen'))
        ids = item.get('source_ids', item.get('ids'))
        result[category] = {'row_count': count, 'total_fen': total, 'source_ids': ids}
    return result

def receipt_key(sample):
    entry = path_entry(sample, '/job/control.json')
    if not entry:
        return None
    d = entry.get('data', {})
    return d.get('request', {}).get('job_id')

def wait_file(e):
    p = e['path'].lower()
    n = Path(p).name
    return '/native/' in p and ('notification-wait' in n or n.startswith('wait-') or n.startswith('wait_'))

def status_return_file(e):
    p = e['path'].lower()
    n = Path(p).name
    return '/native/' in p and 'return' in n and 'observer' not in n and ('status' in n or 'query' in n)

def status_sequence_key(record):
    name=Path(record['path']).name.lower()
    if name in {'status-return.json','query-return.json'}:
        return (-1, name)
    match=re.search(r'(?:status|query)[-_](\d+)',name)
    return (int(match.group(1)) if match else 999, name)

def marker_stage_summary(sample):
    rec = MARKERS[sample]
    stage_spans = rec['spans']
    marker_refs = []
    by_boot = {}
    for m in rec['markers']:
        source = exact_entry(sample, m['path'])
        row = {k: m.get(k) for k in ['actor','stage','event','utc','monotonic_ns','boot_id']}
        row.update({'path': m['path'], 'sha256': source['sha256'] if source else None})
        by_boot.setdefault(m['boot_id'], []).append(row)
        marker_refs.append(row)
    for rows in by_boot.values():
        rows.sort(key=lambda x: (x['monotonic_ns'] if x['monotonic_ns'] is not None else -1, x['utc'] or ''))

    waits = [e for e in SAMPLES[sample] if wait_file(e)]
    wait_records = []
    for e in waits:
        d = e.get('data') if isinstance(e.get('data'), dict) else {}
        wait_records.append({
            **cite(e),
            'raw_return': 'return' in Path(e['path']).name,
            'requested_timeout_ms': d.get('requested_timeout_ms'),
            'arguments': d.get('arguments') or d.get('kwargs') or d.get('params'),
            'raw_fields': sorted(d.keys()),
        })
    status_records = []
    for e in SAMPLES[sample]:
        if not status_return_file(e):
            continue
        d = e.get('data') if isinstance(e.get('data'), dict) else {}
        agents = d.get('agents')
        normalized = []
        if isinstance(agents, list):
            for agent in agents:
                status = agent.get('agent_status') if isinstance(agent, dict) else None
                if isinstance(status, dict):
                    status = 'completed' if 'completed' in status else sorted(status.keys())
                normalized.append(status)
        status_records.append({**cite(e), 'agent_statuses': normalized, 'agent_count': len(agents) if isinstance(agents, list) else None})
    status_records.sort(key=status_sequence_key)

    main_stages = ['setup','receive','review','decision','commit','worker_work','worker_reply']
    selected_spans = [
        {k: x.get(k) for k in ['actor','stage','begin_count','end_count','valid','elapsed_seconds','begin_path','end_path','begin_boot_id','end_boot_id']}
        for x in stage_spans if x['stage'] in main_stages
    ]
    invalid = [
        {'actor': x['actor'], 'stage': x['stage'], 'status': x.get('status', 'invalid' if not x.get('valid') else 'valid'),
         'begin_count': x.get('begin_count'), 'end_count': x.get('end_count'),
         'begin_path': x.get('begin_path'), 'end_path': x.get('end_path'),
         'begin_boot_id': x.get('begin_boot_id'), 'end_boot_id': x.get('end_boot_id')}
        for x in stage_spans if x['stage'] in main_stages and not x.get('valid')
    ]
    wait_spans = [x for x in stage_spans if x['stage'].startswith('notification_wait')]
    return {
        'marker_count': rec['marker_count'],
        'boot_count': len(by_boot),
        'boot_ids': list(by_boot),
        'markers_by_boot_in_monotonic_order': by_boot,
        'markers': marker_refs,
        'main_stage_spans': selected_spans,
        'invalid_main_spans': invalid,
        'notification_wait_marker_pairs': [
            {'stage': x['stage'], 'valid': x.get('valid'), 'elapsed_seconds': x.get('elapsed_seconds'),
             'begin_path': x.get('begin_path'), 'end_path': x.get('end_path'),
             'begin_boot_id': x.get('begin_boot_id'), 'end_boot_id': x.get('end_boot_id')}
            for x in wait_spans
        ],
        'wait_records': wait_records,
        'status_return_records': status_records,
        'status_return_count': len(status_records),
        'status_query_limit_5_met': len(status_records) <= 5,
        'cli_capture_count': rec.get('cli_capture_count'),
        'receipt_count': rec.get('receipt_count'),
    }

def action_output(sample):
    file_e = path_entry(sample, '/artifacts/actions.json')
    reply_e = path_entry(sample, '/artifacts/worker-reply.json')
    raw = file_e.get('data') if file_e else None
    actual = recursive_action_list(raw)
    reply = reply_e.get('data') if reply_e else None
    reply_actions = recursive_action_list(reply)
    return {
        'actions_file': cite(file_e),
        'actions_file_shape': 'flow_envelope_nested_artifacts' if isinstance(raw, dict) and actual is not None else ('direct_array' if isinstance(raw, list) else 'unknown'),
        'actual_actions': actual,
        'matches_independent_expected': actual == EXPECTED_ACTIONS,
        'worker_reply': cite(reply_e),
        'reply_outcome': reply.get('outcome') if isinstance(reply, dict) else None,
        'reply_result_outcome': reply.get('result', {}).get('outcome') if isinstance(reply, dict) and isinstance(reply.get('result'), dict) else None,
        'reply_actions_match_independent_expected': reply_actions == EXPECTED_ACTIONS,
        'reply_artifact_refs': reply.get('artifacts') if isinstance(reply, dict) else None,
    }

PACKAGE_SPECS = {
    'package/B1': {
        'receive':'logs/017-bridge-receive.json','results':'review/results.json','checker':'review/source-checker.json',
        'assessment':'review/package-assess-corrected.json','preflight':'review/check-decision.json',
        'decision':'review/coordinator-decision.json','commit':'logs/035-bridge-commit.json','reconcile':'logs/036-bridge-reconcile.json',
        'note':'The first package assessment/source-review reference failed and was preserved; corrected reference assessment is the final review record.'
    },
    'package/A1': {
        'receive':'logs/014-bridge-receive.json','results':'review/results.json','checker':'review/source-checker.json',
        'assessment':'review/package-assess.json','preflight':'review/check-decision.json',
        'decision':'review/coordinator-decision.json','commit':'logs/024-bridge-commit.json','reconcile':'logs/025-bridge-reconcile.json',
        'note':'A1 actions.json stores the expected list inside the Flow response envelope.'
    },
    'package/A2': {
        'receive':'logs/016-bridge-receive.json','results':'review/results.json','checker':'review/source-checker.json',
        'assessment':'review/package-assess.json','preflight':'review/decision-preflight.json',
        'decision':'review/decision.json','commit':'logs/043-bridge-commit.json','reconcile':'logs/045-bridge-reconcile.json',
        'note':'Decision-preflight record is present; no begin marker accompanies the decision-stage end marker.'
    },
    'package/B2': {
        'receive':'logs/013-bridge-receive.json','results':'review/results.json','checker':'review/source-checker.json',
        'assessment':'review/package-assess.json','preflight':'review/decision-preflight.json',
        'decision':'review/decision.json','commit':'logs/024-bridge-commit.json','reconcile':'logs/025-bridge-reconcile.json',
        'note':'B2 bridge control repair_attempts is zero; separate local analysis/bridge failures are counted under A03.'
    },
}

def package_chain(sample, spec):
    get = lambda suffix: path_entry(sample, suffix)
    control_e = get('/job/control.json')
    ledger_e = get('/job/ledger.json')
    control = control_e.get('data', {}) if control_e else {}
    ledger = ledger_e.get('data', {}) if ledger_e else {}
    job_id = receipt_key(sample)
    job = ledger.get('jobs', {}).get(job_id, {}) if job_id else {}
    attempts = job.get('attempts', [])
    events = attempts[0].get('events', []) if attempts else []
    receipt_entries = [cite(e) for e in SAMPLES[sample] if '/job/receipts/' in e['path']]

    receive_e = get('/' + spec['receive'])
    results_e = get('/' + spec['results'])
    checker_e = get('/' + spec['checker'])
    assessment_e = get('/' + spec['assessment'])
    preflight_e = get('/' + spec['preflight'])
    decision_e = get('/' + spec['decision'])
    commit_e = get('/' + spec['commit'])
    reconcile_e = get('/' + spec['reconcile'])

    receive_out = cli_json(receive_e)
    checker_out = cli_json(checker_e)
    assessment_out = cli_json(assessment_e)
    preflight_out = cli_json(preflight_e)
    commit_out = cli_json(commit_e)
    reconcile_out = cli_json(reconcile_e)
    results = results_e.get('data', {}) if results_e else {}
    statuses = [x.get('status') for x in results.get('checks', [])]
    decision = decision_e.get('data', {}) if decision_e else {}
    reply_e = get('/artifacts/worker-reply.json')
    reply_sha = reply_e.get('sha256') if reply_e else None
    receive_argv = receive_e.get('data', {}).get('argv', []) if receive_e else []
    receipt_local = None
    if '--receipt' in receive_argv:
        historical = receive_argv[receive_argv.index('--receipt') + 1]
        basename = Path(historical).name
        receipt_local = next((e for e in SAMPLES[sample] if e['path'].endswith('/native/' + basename)), None)

    control_ref_hashes_match = []
    for ref in control.get('refs', []):
        historical=ref.get('path','')
        ref_base = Path(historical).name
        local = next((e for e in SAMPLES[sample] if Path(e['path']).name == ref_base and e.get('sha256') == ref.get('sha256')), None)
        mapped=None
        for old_suffix,current in [
            ('/materials/package.json','evidence/c1/materials/package.json'),
            ('/materials/notes.txt','evidence/c1/materials/notes.txt'),
            ('/shared/capture.py','evidence/c1/shared/capture.py'),
            ('/shared/Worker_Protocol.md','evidence/c1/shared/Worker_Protocol.md'),
        ]:
            if historical.endswith(old_suffix):
                target=ROOT/current
                actual_hash=hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
                mapped={'path':current,'actual_sha256':actual_hash,'hash_matches':actual_hash==ref.get('sha256')}
                break
        ok=local is not None or bool(mapped and mapped['hash_matches'])
        control_ref_hashes_match.append({'ref': ref, 'local_snapshot_match': local is not None,
                                         'mapped_source_check':mapped,'hash_matches':ok})

    stages = {
        'receive': {'evidence':cite(receive_e),'exit_code':receive_e.get('data',{}).get('exit_code') if receive_e else None,'phase':receive_out.get('phase') if isinstance(receive_out,dict) else None,'native_receipt':cite(receipt_local)},
        'independent_review': {
            'results':cite(results_e),'check_statuses':statuses,
            'source_checker':cite(checker_e),'source_checker_result':checker_out,
            'package_assessment':cite(assessment_e),'package_assessment_result':assessment_out,
        },
        'decision_preflight': {'evidence':cite(preflight_e),'exit_code':preflight_e.get('data',{}).get('exit_code') if preflight_e else None,'result':preflight_out},
        'decision': {'evidence':cite(decision_e),'outcome':decision.get('outcome'),'request_hash_matches':decision.get('request_hash') == control.get('request_hash'),'reply_sha256_matches':decision.get('reply_sha256') == reply_sha},
        'commit': {'evidence':cite(commit_e),'exit_code':commit_e.get('data',{}).get('exit_code') if commit_e else None,'result':commit_out,
                   'reconcile_evidence':cite(reconcile_e),'reconcile_exit_code':reconcile_e.get('data',{}).get('exit_code') if reconcile_e else None,'reconcile_result':reconcile_out},
    }
    pass_chain = (
        stages['receive']['exit_code'] == 0 and stages['receive']['phase'] == 'received'
        and sorted(statuses) == ['pass','pass']
        and isinstance(checker_out,dict) and checker_out.get('review') == 'pass'
        and isinstance(assessment_out,dict) and assessment_out.get('verdict') == 'pass'
        and stages['decision_preflight']['exit_code'] == 0
        and isinstance(preflight_out,dict) and preflight_out.get('status') == 'controller_compatible'
        and decision.get('outcome') == 'done'
        and stages['commit']['exit_code'] == 0 and isinstance(commit_out,dict) and commit_out.get('phase') == 'committed'
        and stages['commit']['reconcile_exit_code'] == 0 and isinstance(reconcile_out,dict) and reconcile_out.get('phase') == 'committed'
        and control.get('phase') == 'committed'
    )
    return {
        'sample':sample,
        'note':spec['note'],
        'control': {**cite(control_e),'phase':control.get('phase'),'request_hash':control.get('request_hash'),
                    'acceptance_origin':control.get('acceptance_origin'),'repair_attempts':control.get('repair_attempts'),
                    'refs':control.get('refs'),'commit':control.get('commit')},
        'ledger': {**cite(ledger_e),'job_id':job_id,'event_statuses':[x.get('status') for x in events],
                   'attempt_count':len(attempts),'receipts':[x for x in receipt_entries]},
        'control_reference_hash_checks':control_ref_hashes_match,
        'stages':stages,
        'complete_original_chain_pass':bool(pass_chain),
    }

def all_cli_check_reply(sample):
    matches=[]
    for e in SAMPLES[sample]:
        candidates=[]
        d=e.get('data')
        if isinstance(d,dict) and 'exit_code' in d:
            candidates.append((None,d))
        if e.get('lines'):
            try:
                raw_doc=json.loads((ROOT/e['path']).read_text(encoding='utf-8'))
                if isinstance(raw_doc,dict):
                    candidates.append((None,raw_doc))
                elif isinstance(raw_doc,list):
                    candidates.extend((None,x) for x in raw_doc if isinstance(x,dict))
            except (OSError,json.JSONDecodeError):
                for line in e.get('lines',[]):
                    if isinstance(line.get('data'),dict):
                        candidates.append((line.get('line'),line['data']))
        for line_no,record in candidates:
            argv=record.get('argv',[])
            if 'check-reply' not in argv or record.get('actor') not in {'worker'} and not str(record.get('actor','')).startswith('luna_'):
                continue
            try:
                out=json.loads(record.get('stdout',''))
            except (TypeError,json.JSONDecodeError):
                out=None
            matches.append({'evidence':cite(e),'line':line_no,'exit_code':record.get('exit_code'),
                            'status':out.get('status') if isinstance(out,dict) else None,
                            'begin':record.get('begin'),'end':record.get('end')})
    return matches

def completion_status(sample, marker_summary):
    records=marker_summary['status_return_records']
    if not records:
        return None
    last=records[-1]
    observed_completed=any('completed' in x['agent_statuses'] for x in records)
    return {'path':last['path'],'agent_statuses':last['agent_statuses'],'completed_observed_any_query':observed_completed}

def paired_statistics():
    pairsets={'project':{'A':['project/A1','project/A2'],'B':['project/B1','project/B2']},
              'package':{'A':['package/A1','package/A2'],'B':['package/B1','package/B2']}}
    stages=['setup','receive','review','decision','commit','worker_work','worker_reply']
    result={}
    for block, arms in pairsets.items():
        result[block]={}
        for stage in stages:
            result[block][stage]={}
            for arm, samples in arms.items():
                values=[]
                for sample in samples:
                    for span in MARKERS[sample]['spans']:
                        if span['stage']==stage and span.get('valid') and span.get('elapsed_seconds') is not None:
                            values.append(float(span['elapsed_seconds']))
                result[block][stage][arm]={
                    'n':len(values),
                    'median_seconds':statistics.median(values) if values else None,
                    'range_seconds':[min(values),max(values)] if values else None,
                }
    return result

sample_markers={sample:marker_stage_summary(sample) for sample in SAMPLES}
package_results={sample:action_output(sample) for sample in ['package/B1','package/A1','package/A2','package/B2']}
project_results={}
for sample in ['project/A1','project/B1','project/B2','project/A2']:
    summary_e=path_entry(sample,'/artifacts/summary.json')
    raw=summary_e.get('data') if summary_e else None
    normalized=normalize_project(raw)
    reply_e=path_entry(sample,'/artifacts/worker-reply.json')
    reply_data=reply_e.get('data') if reply_e else None
    reply_summary=normalize_project(reply_data.get('result')) if isinstance(reply_data,dict) else None
    project_results[sample]={
        'summary':cite(summary_e),
        'actual_normalized':normalized,
        'matches_independent_expected':normalized==EXPECTED_CATEGORIES,
        'summary_markdown':cite(path_entry(sample,'/artifacts/summary_zh.md')) or cite(path_entry(sample,'/artifacts/summary.md')),
        'worker_reply':cite(reply_e),
        'reply_outcome':reply_data.get('outcome') if isinstance(reply_data,dict) else None,
        'reply_normalized':reply_summary,
        'reply_matches_independent_expected':reply_summary==EXPECTED_CATEGORIES if reply_summary is not None else None,
    }

package_chains={sample:package_chain(sample,spec) for sample,spec in PACKAGE_SPECS.items()}

sample_protocol={}
for sample in SAMPLES:
    args_e=path_entry(sample,'/native/spawn-arguments.json')
    if args_e is None:
        args_e=path_entry(sample,'/native/dispatch-packet.json')
    args_data=args_e.get('data',{}) if args_e else {}
    args=args_data.get('spawn_arguments',args_data)
    spawn_returns=[cite(e) for e in SAMPLES[sample] if '/native/' in e['path'] and 'spawn-return' in Path(e['path']).name and 'observer' not in Path(e['path']).name]
    message=args.get('message','') if isinstance(args,dict) else ''
    treatment='A/manual' if 'Treatment A/manual' in message else ('B/hostdraft' if 'Treatment B' in message and 'hostdraft.py' in message else 'unknown')
    drafts=[cite(e) for e in SAMPLES[sample] if 'draft' in Path(e['path']).name.lower() and ('worker-reply' in Path(e['path']).name.lower())]
    reply_e=path_entry(sample,'/artifacts/worker-reply.json')
    check_reply=all_cli_check_reply(sample)
    ms=sample_markers[sample]
    reply_end=next((x for x in ms['markers'] if x['stage']=='worker_reply' and x['event']=='end'),None)
    ordered_checks=[]
    for check in check_reply:
        end=check.get('end') or {}
        same_boot=bool(reply_end and end.get('boot_id')==reply_end.get('boot_id'))
        before=bool(same_boot and end.get('monotonic_ns') is not None and reply_end.get('monotonic_ns') is not None and end['monotonic_ns'] <= reply_end['monotonic_ns'])
        ordered_checks.append({'check':check,'same_boot_as_worker_reply_end':same_boot,'check_end_before_worker_reply_end':before})
    completion=completion_status(sample,ms)
    sample_protocol[sample]={
        'spawn_arguments':cite(args_e),
        'spawn_task_name':args.get('task_name') if isinstance(args,dict) else None,
        'model':args.get('model') if isinstance(args,dict) else None,
        'reasoning_effort':args.get('reasoning_effort',args.get('reasoning')) if isinstance(args,dict) else None,
        'fork_turns':args.get('fork_turns') if isinstance(args,dict) else None,
        'actual_spawn_return_files':spawn_returns,
        'actual_spawn_return_count':len(spawn_returns),
        'treatment':treatment,
        'preserved_worker_reply_drafts':drafts,
        'final_worker_reply':cite(reply_e),
        'check_reply_records':ordered_checks,
        'final_status_observation':completion,
        'marker_audit':ms,
    }

coordinator_failures=[]
b2='package/B2'
for p,reason in [
    ('logs/018-worker-capture-index-draft.json','First capture-index parser failed on pretty-printed JSONL content; parsing logic was corrected.'),
    ('logs/029-index-audit.json','Initial index audit produced empty worker-check and assessment extractions for all package samples because the argv matching failed.'),
    ('logs/034-audit-final-index.json','Initial final index audit assertion failed on B1 assessment ordering; assertion was corrected to accept any passing v1 assessment.'),
]:
    e=path_entry(b2,'/'+p)
    coordinator_failures.append({'cycle':len(coordinator_failures)+1,'classification':'local analysis/correction cycle','interpretation':reason,'evidence':cite(e),'exit_code':e.get('data',{}).get('exit_code') if e else None,'stdout_excerpt':e.get('data',{}).get('stdout','')[:1200] if e else None,'stderr_excerpt':e.get('data',{}).get('stderr','')[:500] if e else None})
bridge_errors=[]
for p,reason in [
    ('logs/007-bridge-observe-01.json','Rejected observe call: only active jobs can observe running status.'),
    ('logs/008-bridge-accepted-01.json','Rejected accepted call because the creation receipt task_name did not bind to the requested worker; the following record uses the raw spawn return.'),
]:
    e=path_entry(b2,'/'+p)
    bridge_errors.append({'classification':'rejected bridge operation (separately reported; denominator interpretation may include it)','interpretation':reason,'evidence':cite(e),'exit_code':e.get('data',{}).get('exit_code') if e else None,'stdout_excerpt':e.get('data',{}).get('stdout','')[:800] if e else None})
worker_record_keys=[
    'evidence/c1/package/B2/artifacts/actions.json',
    'evidence/c1/package/B2/artifacts/logs/write-business.json',
    'evidence/c1/package/B2/artifacts/logs/semantic-check.json',
    'evidence/c1/package/B2/artifacts/worker-reply.draft.json',
    'evidence/c1/package/B2/artifacts/worker-reply.json',
    'evidence/c1/package/B2/artifacts/logs/check-reply.json',
]
b2_worker=[cite(exact_entry(b2,p)) for p in worker_record_keys if exact_entry(b2,p)]

paired_stats=paired_statistics()

manifest_check=EXTRACTED.get('snapshot_manifest_check')
def root_cite(rel):
    p=ROOT/rel
    if not p.is_file():
        return {'path':rel,'sha256':None,'size_bytes':None}
    raw=p.read_bytes()
    return {'path':rel,'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw)}

citations={
    'audit_plan':root_cite('runs/S01/audit-plan.json'),
    'study_plan':root_cite('evidence/c1/Study_Plan.md'),
    'evidence_map':root_cite('docs/EVIDENCE_MAP.md'),
    'snapshot_manifest':root_cite('evidence/c1/Snapshot_Manifest.json'),
    'package_rules':root_cite('evidence/c1/materials/package.json'),
    'notes':root_cite('evidence/c1/materials/notes.txt'),
    'expense_source':root_cite('evidence/c1/materials/expenses.csv'),
    'operator_protocol':root_cite('evidence/c1/shared/Operator_Protocol.md'),
    'worker_protocol':root_cite('evidence/c1/shared/Worker_Protocol.md'),
    'project_plan':root_cite('evidence/c1/shared/project-plan.json'),
    'observer_source':root_cite('evidence/c1/shared/capture.py'),
    'source_lock':root_cite('state/source-lock.json'),
}

def ev_path(sample, suffix):
    return cite(path_entry(sample,suffix))

frozen_checks=[
    {'id':'C01','grade':'partial','requirement':'Canonical T1 hashes unchanged; equal original inputs/plan/package across each block; no hidden expected business values in worker prompts.','evidence':[citations['study_plan'],citations['snapshot_manifest'],citations['source_lock'],ev_path('package/B1','/job/control.json'),ev_path('package/A1','/job/control.json'),ev_path('project/A1','/job/request.json'),ev_path('project/B1','/job/request.json')],'finding':'Original package/notes and common expense source/plan hashes are bound across the samples; all eight spawn prompts contain task rules but no completed business values. The source lock points to c238b00 with source_modified_by_export=false. The permitted cutoff does not provide a per-run comparison of canonical T1 file hashes against that commit, so the complete frozen requirement is not proven.','unknown_or_missing':['Per-run baseline code hashes at T1 cannot be compared from this C1 snapshot alone.'],'advice':None},
    {'id':'C02','grade':'pass','requirement':'Exactly eight actual worker creation calls, at most one per sample; Luna/max/fresh arguments and raw native returns; no fabricated SDK or synthetic workers.','evidence':[sample_protocol[s]['spawn_arguments'] for s in sample_protocol],'finding':f"{sum(x['actual_spawn_return_count'] for x in sample_protocol.values())} distinct raw spawn-return files pair with eight spawn-argument records; all recorded arguments use gpt-6-luna, max reasoning, fork_turns none. No sample has a second creation return.",'unknown_or_missing':['Provider-internal identity is unavailable and is not inferred from native task names.'],'advice':None},
    {'id':'C03','grade':'partial','requirement':'Same original bridge path and acceptance both treatments; A manually authors reply/decision scaffolds, B uses original hostdraft; preserve initial incomplete draft and actual final files.','evidence':[sample_protocol[s]['spawn_arguments'] for s in sample_protocol]+[ev_path('project/A2','/artifacts/summary.json')],'finding':'Treatment A/manual and B/hostdraft are recorded for all eight samples and seven retain a draft plus final reply. Project/A2 was stopped at cutoff while still running; it has business artifacts but no worker reply/final scaffold, receive, review, decision, or commit.','unknown_or_missing':['The full paired acceptance path is absent for project/A2 at cutoff.'],'advice':None},
    {'id':'C04','grade':'partial','requirement':'Worker check-reply is captured before worker_reply end and final completion observation; receive, independent source review, decision preflight, and commit remain separate.','evidence':[sample_protocol[s]['final_worker_reply'] for s in sample_protocol]+[sample_protocol[s]['marker_audit']['main_stage_spans'] for s in sample_protocol],'finding':'Seven completed samples have captured payload_valid check-reply before the same-boot worker_reply end and a final completion observation. Project/A2 has only five running status returns at cutoff; no worker_reply end, receive, review, decision, commit, or final completion was observed. Four package paths preserve receive/review/preflight/commit as separate records.','unknown_or_missing':['Project/A2 remains running/unknown, with no sixth status query or terminal record in the frozen snapshot.'],'advice':None},
    {'id':'C05','grade':'pass','requirement':'Recompute project CSV using Decimal/integer fen and all IDs; package source semantics, exact quotes, null/literal fields and original v1 acceptance retained; no-action branch out of scope.','evidence':[cite(path_entry('project/A1','/artifacts/summary.json')),cite(path_entry('project/B1','/artifacts/summary.json')),cite(path_entry('project/B2','/artifacts/summary.json')),cite(path_entry('project/A2','/artifacts/summary.json'))]+[package_results[s]['actions_file'] for s in package_results]+[cite(path_entry('package/B1','/review/results.json')),cite(path_entry('package/A1','/review/results.json')),cite(path_entry('package/A2','/review/results.json')),cite(path_entry('package/B2','/review/results.json'))],'finding':'All four independently parsed project summaries equal the six-row Decimal/fen recomputation and preserve all IDs. All four package action lists equal the independently frozen three-action result; exact note quotes, literal 周五, 2026-10-09, null owner/date, advice exclusion and status exclusion match. Original package v1 quotes/commitments rows are pass. The no-action branch was not run and is explicitly outside this repeated input.','unknown_or_missing':['Project/A2 protocol completion is separate from its matching saved business outputs.'],'advice':None},
    {'id':'C06','grade':'partial','requirement':'Same-boot monotonic coordinator and worker stage markers; every subprocess retained with argv/raw bytes/exit/timestamps; missing stages are not zero.','evidence':[sample_protocol[s]['marker_audit'] for s in sample_protocol],'finding':'All eight samples were checked; valid and invalid spans are listed without imputing missing durations. Several setup/decision/receive/worker stages are cross-boot, duplicated, or missing, and the source records disclose uncaptured setup/read commands. Captured CLI records retain argv, exit, stdout/stderr and timestamps, but a complete actual-command denominator is unavailable.','unknown_or_missing':['Exact subprocess capture completeness cannot be established for commands disclosed as uncaptured.','Cross-boot elapsed values are null.'],'advice':None},
    {'id':'C07','grade':'pass','requirement':'Preserve failures, first versions, corrections and assistance; retain all eight samples, including failures; do not replace or respawn to improve success/speed.','evidence':[ev_path('project/A1','/artifacts/summary.rejected-v1.json'),ev_path('project/B1','/review/source-check-output.v1.json'),ev_path('package/B1','/artifacts/worker-reply.preflight-rejected.json'),ev_path('package/B1','/review/results.rejected.json')]+b2_worker+[x['evidence'] for x in coordinator_failures],'finding':'Rejected first versions and failed review/analysis records remain in the frozen snapshot; the incomplete Project/A2 sample remains included. B2 worker had zero local business/reply correction attempts. Three separate coordinator analysis/correction cycles are evidenced; two rejected bridge operations are also retained and reported separately. No replacement spawn or experiment rerun was made.','unknown_or_missing':['Some uncaptured command attempts are known only from retained source-review/progress records.'],'advice':None},
    {'id':'C08','grade':'partial','requirement':'Independent audit sample/index/timing/treatment/evidence integrity and source clauses; distinguish required gaps, untested scope and advice; root resolves proposals against originals.','evidence':[citations['snapshot_manifest'],citations['notes'],citations['package_rules'],citations['expense_source']]+[package_results[s]['actions_file'] for s in package_results]+[x['evidence'] for x in coordinator_failures],'finding':'This audit independently froze package expectations before viewing outputs, checked the manifest, source clauses, all eight marker/receipt sets and actual package chains, and recomputed all business values. Prior per-sample review prose and old index conclusions embedded in raw coordinator CLI stdout were encountered later; aggregate old summaries were not opened. Index-generated artifacts were not independently opened under the audit scope, so index artifact completeness and full blindness are not asserted.','unknown_or_missing':['Independent byte-for-byte verification of the historical generated index/aggregate files is not made.'],'advice':'Keep factual findings separate from any proposal about future implementation.'},
    {'id':'C09','grade':'partial','requirement':'Paired A/B records; descriptive medians/ranges/counts; stage spans include actor/tool/wait gaps and are not model-active duration; tokens/cost/provider internal identity unknown; no stable general/global speed claim.','evidence':[sample_protocol[s]['marker_audit'] for s in sample_protocol],'finding':'Descriptive A/B median/range/n counts are computed from valid same-boot stage spans for project and package pairs. Several stage counts are below two because of missing/cross-boot/duplicate markers; all spans include measured wall elapsed between observer markers, not model-active time. No stable speed or causal generalization is supported by these four pairs.','unknown_or_missing':['Token counts, cost, provider-internal identity and actual model-active time are null.'],'advice':None},
    {'id':'C10','grade':'unknown','requirement':'Same TODO identity/history, browser blockers and partial SDK/global/network/external-effect work preserved; concrete next decision from observed bottlenecks.','evidence':[citations['study_plan'],citations['evidence_map']],'finding':'The C1 plan says no target UI or provider SDK was exercised, which is consistent with the allowed offline scope. TODO identity/history, browser blockers, and prior SDK/global/network/external-effect status are outside the permitted source set and remain unknown.','unknown_or_missing':['TODO/history identity and prior blocker records were not read.','No browser, SDK, network, or external-effect evaluation was performed.'],'advice':'Do not infer a runtime or speed improvement from C1. If a driver-initialization change is still desired, freeze it as a separate implementation and evaluate it with a new, independently specified study.'},
]

audit={
    'schema':'forge-c1-independent-audit/1',
    'scope':{'source_root':'evidence/c1','requested_audits':['A01','A02','A03','A04','A05'],'frozen_requirements':'C01-C10','offline':True,'historical_scripts_executed':False,'historical_workers_queried':False,'external_services_contacted':False},
    'source_citations':citations,
    'snapshot_manifest_check':manifest_check,
    'expected_data':{'package':EXPECTED_PACKAGE,'project':EXPECTED_PROJECT},
    'A01_package_chains':package_chains,
    'A02_package_outputs':package_results,
    'project_business_recompute':project_results,
    'A03_B2_corrections':{
        'worker':{'local_correction_attempts':0,'frozen_limit':2,'evidence':b2_worker,'result':'within limit'},
        'coordinator_analysis_cycles':coordinator_failures,
        'coordinator_analysis_cycle_count':len(coordinator_failures),
        'frozen_limit':2,
        'result':'exceeds frozen limit by one analysis/correction cycle',
        'rejected_bridge_operations_separately_reported':bridge_errors,
        'broad_count_if_bridge_failures_are_in_denominator':len(coordinator_failures)+len(bridge_errors),
        'control_repair_attempts_field':package_chains['package/B2']['control'].get('repair_attempts'),
        'denominator_note':'The control repair_attempts counter does not include local index/analysis work. Three distinct local coordinator analysis/correction cycles already exceed the frozen two-correction denominator; if the two rejected bridge operations are included, the count is at least five.'
    },
    'A04_eight_sample_protocol_audit':sample_protocol,
    'C09_descriptive_stage_statistics':paired_stats,
    'A05_frozen_C01_C10':frozen_checks,
    'advice_separate_from_grades':[x['advice'] for x in frozen_checks if x.get('advice')],
    'independence_disclosures':[
        'The three-action package expected result and excluded advice/status clauses were derived and saved before any package output was examined.',
        'After freezing the expected result, original per-sample source-review/decision records were inspected as evidence in the review chain. They contain historical judgments and were not used as the independent expected-value source.',
        'Raw coordinator CLI captures for B2 include stdout derived from the historical block index/summary, notably 029-index-audit.json and 034-audit-final-index.json; 030-inspect-index-script.json contains prior script analysis. These conclusions were encountered as original raw records and are disclosed, not treated as independent authority.',
        'The old aggregate package index/summary files themselves were not opened; no historical controller or analysis script was executed.',
        'Snapshot manifest is explicitly non-atomic and worker_stopped=false; this audit validates the preserved file versions, not that Project/A2 completed.'
    ],
    'overall_audit_completeness':'complete for the requested A01-A05 scope; historical frozen requirement grades include partial, fail and unknown as recorded; this is not a claim that C1 passed.',
}

AUDIT_PATH=WORK/'audit.json'
AUDIT_PATH.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def evs(e):
    if not e: return '—'
    if isinstance(e,list): return '; '.join(f"`{x['path']}` ({x['sha256']})" for x in e if x)
    if isinstance(e,dict) and 'path' in e: return f"`{e['path']}` ({e['sha256']})"
    return str(e)

report=[]
report += ['# Independent offline C1 audit', '', 'Audit scope: A01–A05 and frozen C01–C10, using only the preserved C1 sources and this worker directory. This report records evidence and gaps; a complete audit does not mean the historical requirements all passed.', '']
report += ['## Findings', '', '| Check | Grade | Finding |', '|---|---|---|']
for row in frozen_checks:
    report.append(f"| {row['id']} | {row['grade']} | {row['finding']} |")
report += ['', 'The snapshot manifest check found **{matches}/{checked}** files matching recorded SHA-256 and byte sizes, with {missing} missing and {mismatches} mismatched. The manifest itself describes a non-atomic snapshot and does not certify that the workers had stopped.'.format(**manifest_check), '']

report += ['## A01 — Package receive, review, preflight and commit chains', '', 'Each chain below links the original native receive receipt, frozen v1 review, separate controller decision preflight, final decision, commit and reconcile. `controller_compatible` is protocol preflight only; semantic acceptance is shown separately from `review/results.json` and the package assessment.', '', '| Sample | Receive | Source review / assessment | Decision preflight | Commit and reconcile |', '|---|---|---|---|---|']
for sample,chain in package_chains.items():
    stages=chain['stages']
    recv=stages['receive']; review=stages['independent_review']; pre=stages['decision_preflight']; com=stages['commit']
    assess=review['package_assessment_result'] or {}
    pref=pre['result'] or {}
    commit=(com['result'] or {}).get('phase') if isinstance(com['result'],dict) else None
    recon=(com['reconcile_result'] or {}).get('phase') if isinstance(com['reconcile_result'],dict) else None
    report.append(f"| {sample} | {recv['phase']} via `{recv['native_receipt']['path'] if recv['native_receipt'] else 'missing'}` | {review['check_statuses']} / {assess.get('verdict')} | {pref.get('status')} (semantic grading not evaluated here) | {commit} / {recon} |")
report += ['', 'Source citations and SHA-256 values are in `audit.json` under `A01_package_chains`. Every package control record ends in `committed`; the chain checks also confirm the decision request/reply hashes bind to the same control and final worker reply. Package/B1 preserves its first failed assessment and corrected final assessment.', '']

report += ['## A02 — Independent package output recomputation', '', 'Before opening any package output, I derived the expected list from `materials/notes.txt` and `materials/package.json` and saved it in `analysis/expected_package_actions.json`. The expected actions are:', '', '```json', json.dumps(EXPECTED_ACTIONS,ensure_ascii=False,indent=2), '```', '', 'The exact quotes are required substrings of the source notes. The relative deadline `周五` remains literal; the unstated owner and date for the explicit log-alert decision are null. “建议以后考虑更换配色。” is advice, and “本周没有新增外部通知。” is a status statement, so neither is an action.', '', '| Sample | Business file shape | Independent list match | Reply match |', '|---|---|---|---|']
for sample,result in package_results.items():
    report.append(f"| {sample} | {result['actions_file_shape']} | {result['matches_independent_expected']} | {result['reply_actions_match_independent_expected']} |")
report += ['', 'A1 stores the same action array under a Flow response envelope; unwrapping that envelope yields an exact match. All four worker replies and artifact references are present. Hashes and paths appear in `audit.json` under `A02_package_outputs`.', '']

report += ['## A03 — Package/B2 corrections against the frozen two-correction limit', '', 'The B2 worker has **0/2** local business/reply correction attempts in the retained worker records: its single action output passed a source semantic check, its incomplete draft and final reply are both preserved, and `check-reply` returned `payload_valid`.', '', f"The coordinator made **{len(coordinator_failures)}/2** distinct index/analysis correction cycles, exceeding the limit by one:", '']
for cycle in coordinator_failures:
    report.append(f"{cycle['cycle']}. {cycle['interpretation']} Evidence: `{cycle['evidence']['path'] if cycle['evidence'] else 'missing'}` (exit {cycle['exit_code']}).")
report += ['', f"Two additional rejected B2 bridge operations are recorded separately: `logs/007-bridge-observe-01.json` and `logs/008-bridge-accepted-01.json`; a corrected acceptance uses the raw spawn return in `logs/009-bridge-accepted-spawn-return.json`. If the denominator counts these operational failures too, B2 has at least **{len(coordinator_failures)+len(bridge_errors)}/2** coordinator correction/error attempts. The job control field `repair_attempts: 0` does not count these local index/analysis repairs.", '', 'Each raw path, hash and captured output excerpt is in `audit.json` under `A03_B2_corrections`. The first failures remain preserved; I did not rerun or repair the original experiment.', '']

report += ['## A04 — Eight-sample marker, boot, wait and raw-return audit', '', '| Sample | Markers / boots | Invalid main stage spans | Status returns | Wait marker pairs / raw wait returns | Cutoff observation |', '|---|---:|---|---:|---:|---|']
for sample,protocol in sample_protocol.items():
    m=protocol['marker_audit']
    invalid=', '.join(f"{x['stage']}:{x['status']}" for x in m['invalid_main_spans']) or 'none'
    pairs=len(m['notification_wait_marker_pairs'])
    returns=sum(1 for x in m['wait_records'] if x['raw_return'])
    all_status=m['status_return_records']
    last_status=all_status[-1]['agent_statuses'] if all_status else None
    cutoff='running/unknown' if sample=='project/A2' else ('completed observed' if protocol['final_status_observation'] and protocol['final_status_observation']['completed_observed_any_query'] else 'see final saved record')
    report.append(f"| {sample} | {m['marker_count']} / {m['boot_count']} | {invalid} | {m['status_return_count']} | {pairs} / {returns} | {cutoff} |")
report += ['', 'Marker events are listed in `audit.json` by boot and monotonic order, with each original marker path and hash. Monotonic timestamps are compared only within one boot. Project/A1 and package/B1 setup spans cross boots; package/A2 lacks a decision begin; package/B2 has duplicate setup ends; Project/A2 has an unclosed receive and worker-work span and no reply/review/decision/commit markers. Its fifth status return is still running; the non-atomic manifest provides no sixth query or terminal observation.', '', 'Most wait records do not preserve exact requested timeout arguments. Only package/A1 wait 3 and package/A2 wait 4 expose `requested_timeout_ms: 45000` in observation records, not raw wait-return objects. Project/A1 and Project/B1 have wait marker pairs but no direct wait-return files; package/A1 wait 3 and package/A2 wait 4 likewise have observations instead of exact return records. Elapsed wait-marker spans include orchestration overhead; they do not establish native timeout arguments. Unknown values remain null.', '', 'Raw status-return counts are Project A1=4, B1=4, B2=5, A2=5; Package B1=5, A1=3, A2=4, B2=4. All are at or below the frozen five-query limit. Per-file return hashes, arguments exposed by the snapshot, and final observed statuses are in `audit.json` under `A04_eight_sample_protocol_audit`.', '']

report += ['## A05 — Frozen C01–C10 grades', '', '| ID | Grade | Evidence and gap summary |', '|---|---|---|']
for row in frozen_checks:
    gap='; '.join(row['unknown_or_missing']) if row['unknown_or_missing'] else 'none recorded'
    report.append(f"| {row['id']} | {row['grade']} | {row['finding']} Gap/unknown: {gap} |")
report += ['', 'The machine-readable table preserves the exact requirement text, finding, source paths, and missing/unknown fields in `audit.json` under `A05_frozen_C01_C10`. No additional requirement is graded.', '']

report += ['## C09 descriptive stage spans', '', 'Values are same-boot observer wall spans in seconds. They include tool work, waits and gaps between observer markers, and are not model-active duration. `n` is the number of valid sample spans used; missing values are omitted, never zero-filled.', '', '| Block / stage | A: n / median / range | B: n / median / range |', '|---|---:|---:|']
for block, stages in paired_stats.items():
    for stage, arms in stages.items():
        def fmt(x):
            r=x['range_seconds']
            return f"{x['n']} / {x['median_seconds']:.3f} / {r[0]:.3f}–{r[1]:.3f}" if x['n'] and r else f"{x['n']} / null / null"
        report.append(f"| {block} / {stage} | {fmt(arms['A'])} | {fmt(arms['B'])} |")
report += ['', 'The effective sample size is at most two per arm and smaller for incomplete/cross-boot spans. Tokens, cost, provider-internal identity and active model duration are unknown. These records do not support a stable general speed claim.', '']

report += ['## Independence, limitations and advice', '', 'The package expected actions were frozen before any package output was examined. The source comparisons use the original notes and rules; the project expectation comes from a separate Decimal/integer-fen recomputation. After those expectations were saved, original per-sample source-review and decision records were inspected to trace the review chain. Those documents contain historical judgments and were treated as evidence, not as the independent answer key.', '', 'Some raw B2 coordinator CLI stdout contains earlier block-index/summary-derived conclusions (`029-index-audit.json`, `034-audit-final-index.json`) and earlier script inspection (`030-inspect-index-script.json`). I did not open the old aggregate index/summary files and did not execute their historical builder or controller. These exposures limit claims of blindness and are listed in `audit.json`.', '', 'The snapshot manifest matches all 375 listed file hashes and sizes but is explicitly non-atomic, with `worker_stopped=false`. Therefore Project/A2 remains running/unknown; its saved summary values match the independent calculation but no protocol completion is inferred.', '', 'Advice, separate from grades: do not infer a runtime or speed improvement from C1. If driver-initialization work is still desired, freeze it as a separate implementation and evaluate it in a new, independently specified study. C10 history/TODO and browser or SDK/network/external-effect status remain unknown because they are outside the permitted C1 audit inputs.', '', '## Audit artifacts', '', '- `audit.json`: complete machine-readable A01–A05 evidence, citations, hashes, marker ledger, correction counts, C01–C10 grades and descriptive statistics.', '- `analysis/`: independent derivation scripts and saved expected package/project data, source extraction, comparisons, and actual command/output records.', '- This report is `report.md` in the assigned worker output directory.', '']

REPORT_PATH=WORK/'report.md'
REPORT_PATH.write_text('\n'.join(report)+'\n',encoding='utf-8')
print(json.dumps({'audit_path':str(AUDIT_PATH),'report_path':str(REPORT_PATH),'sample_count':len(SAMPLES),'package_chain_pass_count':sum(x['complete_original_chain_pass'] for x in package_chains.values()),'package_business_match_count':sum(x['matches_independent_expected'] and x['reply_actions_match_independent_expected'] for x in package_results.values()),'project_business_match_count':sum(x['matches_independent_expected'] for x in project_results.values()),'snapshot_manifest_check':{k:v for k,v in manifest_check.items() if k!='details'},'coordinator_b2_analysis_cycles':len(coordinator_failures),'b2_rejected_bridge_operations':len(bridge_errors),'frozen_C_grades':{x['id']:x['grade'] for x in frozen_checks}},ensure_ascii=False))
