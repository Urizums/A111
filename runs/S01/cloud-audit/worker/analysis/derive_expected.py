#!/usr/bin/env python3
"""Derive expected package actions only from frozen notes and package rules."""
import json
from pathlib import Path

notes_path = Path('/workspace/A111/evidence/c1/materials/notes.txt')
notes = notes_path.read_text(encoding='utf-8')
# Derived before opening any package result, review, or worker artifact.
# Include only explicit commitments; retain literal relative date text.
expected = {
    'schema': 'independent-package-expected/1',
    'basis': {
        'source_notes': 'evidence/c1/materials/notes.txt',
        'rules': 'evidence/c1/materials/package.json',
        'rules_summary': 'Explicit action items only; exact source quote; unstated owner/date null; relative dates literal; suggestions excluded; no action -> [].',
        'notes_sha256': None,
    },
    'actions': [
        {'task': '更新部署文档', 'owner': '赵宁', 'due': '周五', 'source_quote': '赵宁负责更新部署文档，截止周五。'},
        {'task': '补充回归用例', 'owner': '许静', 'due': '2026-10-09', 'source_quote': '许静负责补充回归用例，截止2026-10-09。'},
        {'task': '补充日志告警', 'owner': None, 'due': None, 'source_quote': '决定补充日志告警。'},
    ],
    'excluded': [
        {'source_quote': '建议以后考虑更换配色。', 'reason': 'advice rather than commitment'},
        {'source_quote': '本周没有新增外部通知。', 'reason': 'status statement, not an action item'},
    ],
}
# Confirm each supporting quote is present in the sole permitted business input.
for action in expected['actions']:
    if action['source_quote'] not in notes:
        raise SystemExit('derived quote absent from supplied notes')
for item in expected['excluded']:
    if item['source_quote'] not in notes:
        raise SystemExit('excluded quote absent from supplied notes')
import hashlib
expected['basis']['notes_sha256'] = hashlib.sha256(notes_path.read_bytes()).hexdigest()
expected['package_samples'] = ['B1', 'A1', 'A2', 'B2']
expected['same_expected_actions_for_each_sample'] = True
out = Path('/workspace/A111/runs/S01/cloud-audit/worker/analysis/expected_package_actions.json')
out.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'output': str(out), 'action_count': len(expected['actions']), 'excluded_count': len(expected['excluded']), 'notes_sha256': expected['basis']['notes_sha256']}, ensure_ascii=False))
