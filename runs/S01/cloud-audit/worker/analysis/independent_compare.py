#!/usr/bin/env python3
"""Independent content and artifact-reference checks using frozen source-derived expectations."""
import json,hashlib
from pathlib import Path
ROOT=Path('/workspace/A111')
source=json.loads((ROOT/'runs/S01/cloud-audit/worker/analysis/extracted_sources.json').read_text(encoding='utf-8'))
pkg=json.loads((ROOT/'runs/S01/cloud-audit/worker/analysis/expected_package_actions.json').read_text(encoding='utf-8'))
proj=json.loads((ROOT/'runs/S01/cloud-audit/worker/analysis/expected_project_summary.json').read_text(encoding='utf-8'))
out={'schema':'independent-content-audit/1','package':{},'project':{}}
def entries(group,sid):return source['samples'][f'{group}/{sid}']
def readrec(group,sid,suffix):
    return next((e for e in entries(group,sid) if e['path'].endswith(suffix)),None)
def file_exists_and_hash(e):
    if not e:return None
    p=ROOT/e['path']
    return {'exists':p.is_file(),'actual_sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None,'recorded_sha256':e['sha256']}
for sid in ['B1','A1','A2','B2']:
    es=entries('package',sid)
    action=readrec('package',sid,'/artifacts/actions.json')
    explanation=next((e for e in es if e['path'].endswith(('/artifacts/解释.md','/artifacts/explanation.md','/artifacts/explanation.zh.md'))),None)
    reply=readrec('package',sid,'/artifacts/worker-reply.json')
    actual=action.get('data') if action else None
    direct=actual if isinstance(actual,list) else None
    nested=actual.get('artifacts',{}).get('actions') if isinstance(actual,dict) else None
    content=direct if direct is not None else nested
    reply_content=(reply.get('data') or {}).get('result',{}).get('artifacts',{}).get('actions') if reply else None
    expected=pkg['actions']
    missing=[]
    refs=(reply.get('data') or {}).get('artifacts',[]) if reply else []
    for ref in refs:
        # Map historical absolute path to the retained evidence snapshot by package-relative suffix.
        p=str(ref.get('path',''))
        key='package/'+sid+'/'
        rel=p[p.find(key):] if key in p else ''
        exists=bool(rel and (ROOT/'evidence/c1'/rel).is_file())
        actual_hash=hashlib.sha256((ROOT/'evidence/c1'/rel).read_bytes()).hexdigest() if exists else None
        missing.append({'historical_path':p,'snapshot_path':('evidence/c1/'+rel) if rel else None,'exists':exists,'expected_sha256':ref.get('sha256'),'actual_sha256':actual_hash,'hash_matches':bool(exists and actual_hash==ref.get('sha256'))})
    out['package'][sid]={
      'actions_file':file_exists_and_hash(action),
      'actions_file_path':action['path'] if action else None,
      'actions_file_shape':'array' if isinstance(actual,list) else 'flow_envelope' if isinstance(actual,dict) and nested is not None else type(actual).__name__ if actual is not None else None,
      'actions_file_content_matches_expected':content==expected,
      'worker_reply_present':reply is not None,
      'worker_reply_hash':reply['sha256'] if reply else None,
      'worker_reply_content_matches_expected':reply_content==expected,
      'worker_reply_outer_outcome':(reply.get('data') or {}).get('outcome') if reply else None,
      'worker_reply_inner_outcome':((reply.get('data') or {}).get('result') or {}).get('outcome') if reply else None,
      'worker_reply_referenced_files':missing,
      'explanation_path':explanation['path'] if explanation else None,
      'explanation_sha256':explanation['sha256'] if explanation else None,
      'explanation_text':explanation.get('text') if explanation else None,
      'v1_result':(readrec('package',sid,'/review/results.json') or {}).get('data'),
      'decision':(readrec('package',sid,'/review/decision.json') or readrec('package',sid,'/review/coordinator-decision.json') or {}).get('data'),
      'decision_preflight_record':(readrec('package',sid,'/review/decision-preflight.json') or readrec('package',sid,'/review/check-decision.json') or {}).get('data'),
    }
for sid in ['A1','B1','B2','A2']:
    summary=readrec('project',sid,'/artifacts/summary.json')
    zh=readrec('project',sid,'/artifacts/summary_zh.md')
    reply=readrec('project',sid,'/artifacts/worker-reply.json')
    data=summary.get('data') if summary else None
    cats=(data or {}).get('categories', data) if isinstance(data,dict) else None
    normalized=[]
    if isinstance(cats,dict):
      for name in sorted(cats):
        row=cats[name]
        total=row.get('total_fen',row.get('total_amount_fen'))
        normalized.append({'category':name,'count':row.get('row_count',row.get('count')),'total_fen':total,'ids':row.get('source_ids',row.get('ids'))})
    summary_reply=(reply.get('data') or {}).get('result',{}) if reply else None
    if isinstance(summary_reply,dict) and isinstance(summary_reply.get('categories'),dict):
      summary_reply=summary_reply['categories']
    reply_norm=[]
    if isinstance(summary_reply,dict):
      for name in sorted(summary_reply):
        row=summary_reply[name]
        reply_norm.append({'category':name,'count':row.get('row_count',row.get('count')),'total_fen':row.get('total_fen',row.get('total_amount_fen')),'ids':row.get('source_ids',row.get('ids'))})
    out['project'][sid]={
      'summary_path':summary['path'] if summary else None,'summary_sha256':summary['sha256'] if summary else None,
      'normalized_categories':normalized,'summary_matches_expected':normalized==proj['categories'],
      'summary_zh_path':zh['path'] if zh else None,'summary_zh_sha256':zh['sha256'] if zh else None,'summary_zh_text':zh.get('text') if zh else None,
      'worker_reply_path':reply['path'] if reply else None,'worker_reply_sha256':reply['sha256'] if reply else None,
      'worker_reply_present':reply is not None,'worker_reply_matches_expected':reply_norm==proj['categories'] if reply else None,
      'worker_reply_result_categories':reply_norm if reply else None,
      'source_checks':[{'path':e['path'],'sha256':e['sha256'],'pass':(e.get('data') or {}).get('pass'),'checks':(e.get('data') or {}).get('checks')} for e in entries('project',sid) if '/review/' in e['path'] and Path(e['path']).name.startswith('source-check-output')],
    }
( ROOT/'runs/S01/cloud-audit/worker/analysis/independent_content_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':'runs/S01/cloud-audit/worker/analysis/independent_content_audit.json','package':{k:{'actions_shape':v['actions_file_shape'],'actions_match':v['actions_file_content_matches_expected'],'reply_match':v['worker_reply_content_matches_expected'],'missing_refs':[x for x in v['worker_reply_referenced_files'] if not x['exists']]} for k,v in out['package'].items()},'project':{k:{'summary_match':v['summary_matches_expected'],'reply_present':v['worker_reply_present'],'reply_match':v['worker_reply_matches_expected']} for k,v in out['project'].items()}},ensure_ascii=False))
