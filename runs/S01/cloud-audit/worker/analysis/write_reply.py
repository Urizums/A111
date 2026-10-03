#!/usr/bin/env python3
"""Fill the assigned Forge reply with the completed offline audit artifacts."""
import hashlib
import json
from pathlib import Path

ROOT=Path('/workspace/A111')
WORK=ROOT/'runs/S01/cloud-audit/worker'
REQUEST=json.loads((ROOT/'runs/S01/cloud-audit/job/request.json').read_text(encoding='utf-8'))['request']
AUDIT=json.loads((WORK/'audit.json').read_text(encoding='utf-8'))
ARTIFACT_PATHS=[
    'audit.json','report.md',
    'analysis/finalize_audit.py','analysis/finalize_audit.command.json',
    'analysis/capture_finalizer.py','analysis/capture_hostdraft.py','analysis/hostdraft_reply.command.json',
    'analysis/derive_expected.py','analysis/derive_expected.command.json','analysis/expected_package_actions.json',
    'analysis/derive_expected_project.py','analysis/expected_project_summary.json',
    'analysis/extract_sources.py','analysis/extracted_sources.json',
    'analysis/summarize_markers.py','analysis/marker_summary.json','analysis/marker_ledger.txt',
    'analysis/inspect_b2_corrections.py','analysis/b2_corrections.json',
    'analysis/independent_compare.py','analysis/independent_content_audit.json',
]
artifacts=[]
for rel in ARTIFACT_PATHS:
    p=WORK/rel
    if not p.is_file():
        raise FileNotFoundError(p)
    raw=p.read_bytes()
    artifacts.append({'path':str(p),'sha256':hashlib.sha256(raw).hexdigest()})

result={
    'status':'audit_complete',
    'report_path':str(WORK/'report.md'),
    'audit_json_path':str(WORK/'audit.json'),
    'artifact_hashes':artifacts,
    'manifest_matches':AUDIT['snapshot_manifest_check']['matches'],
    'manifest_checked':AUDIT['snapshot_manifest_check']['checked'],
    'package_business_outputs_matching_independent_expected':sum(1 for x in AUDIT['A02_package_outputs'].values() if x['matches_independent_expected']),
    'package_receive_review_preflight_commit_chains_complete':sum(1 for x in AUDIT['A01_package_chains'].values() if x['complete_original_chain_pass']),
    'project_summaries_matching_independent_recompute':sum(1 for x in AUDIT['project_business_recompute'].values() if x['matches_independent_expected']),
    'b2_coordinator_analysis_correction_cycles':AUDIT['A03_B2_corrections']['coordinator_analysis_cycle_count'],
    'b2_coordinator_correction_limit':AUDIT['A03_B2_corrections']['frozen_limit'],
    'frozen_C_grades':{x['id']:x['grade'] for x in AUDIT['A05_frozen_C01_C10']},
    'limitations':['Project/A2 remains running/unknown at the frozen cutoff.','Some marker spans and native wait parameters/returns are unavailable.','C10 historical TODO/browser/SDK/network scope remains unknown.'],
}
reply={
    'schema_version':'forge-host-reply/1',
    'job_id':REQUEST['job_id'],
    'attempt_id':REQUEST['attempt_id'],
    'request_hash':json.loads((ROOT/'runs/S01/cloud-audit/job/request.json').read_text(encoding='utf-8'))['request_hash'],
    'outcome':'done',
    'result':result,
    'artifacts':artifacts,
    'reason':None,
}
out=WORK/'reply.json'
out.write_text(json.dumps(reply,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'reply_path':str(out),'outcome':reply['outcome'],'artifact_count':len(artifacts),'report_sha256':next(x['sha256'] for x in artifacts if x['path'].endswith('/report.md')),'audit_sha256':next(x['sha256'] for x in artifacts if x['path'].endswith('/audit.json'))},ensure_ascii=False))
