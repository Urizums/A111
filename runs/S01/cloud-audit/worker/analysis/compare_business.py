#!/usr/bin/env python3
"""Compare frozen business outputs to independent source-derived expectations."""
import hashlib,json
from pathlib import Path
ROOT=Path('/workspace/A111')
SRC=ROOT/'runs/S01/cloud-audit/worker/analysis/extracted_sources.json'
PKG=ROOT/'runs/S01/cloud-audit/worker/analysis/expected_package_actions.json'
PROJ=ROOT/'runs/S01/cloud-audit/worker/analysis/expected_project_summary.json'
OUT=ROOT/'runs/S01/cloud-audit/worker/analysis/business_comparison.json'
src=json.loads(SRC.read_text(encoding='utf-8'))
pkg=json.loads(PKG.read_text(encoding='utf-8'))
proj=json.loads(PROJ.read_text(encoding='utf-8'))
report={'schema':'independent-business-comparison/1','package':{},'project':{}}
for sid in ['B1','A1','A2','B2']:
    entries=src['samples']['package/'+sid]
    actions=[e for e in entries if e['path'].endswith('/artifacts/actions.json')]
    explain=[e for e in entries if e['path'].endswith(('/artifacts/解释.md','/artifacts/explanation.zh.md','/artifacts/explanation.md'))]
    reply=[e for e in entries if e['path'].endswith('/artifacts/worker-reply.json')]
    report['package'][sid]={
        'actions_path':actions[0]['path'] if actions else None,
        'actions_sha256':actions[0]['sha256'] if actions else None,
        'actual_actions':actions[0].get('data') if actions else None,
        'matches_expected':bool(actions and actions[0].get('data')==pkg['actions']),
        'explanation_paths':[{'path':e['path'],'sha256':e['sha256'],'text':e.get('text')} for e in explain],
        'reply_path':reply[0]['path'] if reply else None,
        'reply_sha256':reply[0]['sha256'] if reply else None,
        'reply_data':reply[0].get('data') if reply else None,
    }
for sid in ['A1','B1','B2','A2']:
    entries=src['samples']['project/'+sid]
    summaries=[e for e in entries if e['path'].endswith('/artifacts/summary.json')]
    zh=[e for e in entries if e['path'].endswith('/artifacts/summary_zh.md')]
    checks=[e for e in entries if '/review/' in e['path'] and Path(e['path']).name.startswith('source-check-output')]
    report['project'][sid]={
        'summary_path':summaries[0]['path'] if summaries else None,
        'summary_sha256':summaries[0]['sha256'] if summaries else None,
        'summary_data':summaries[0].get('data') if summaries else None,
        'summary_zh':[{'path':e['path'],'sha256':e['sha256'],'text':e.get('text')} for e in zh],
        'source_checker_outputs':[{'path':e['path'],'sha256':e['sha256'],'data':e.get('data')} for e in checks],
        'worker_reply':[{'path':e['path'],'sha256':e['sha256'],'data':e.get('data')} for e in entries if e['path'].endswith('/artifacts/worker-reply.json')],
    }
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(OUT),'package':{k:{'matches_expected':v['matches_expected'],'actions_sha256':v['actions_sha256'],'action_shape':type(v['actual_actions']).__name__ if v['actual_actions'] is not None else None} for k,v in report['package'].items()},'project':{k:{'summary_present':bool(v['summary_data']),'summary_sha256':v['summary_sha256'],'summary_type':type(v['summary_data']).__name__ if v['summary_data'] is not None else None,'checks':len(v['source_checker_outputs'])} for k,v in report['project'].items()}},ensure_ascii=False))
