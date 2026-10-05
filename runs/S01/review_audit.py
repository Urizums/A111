"""Root source checks for the new offline audit; never runs historical controllers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


audit_path = 'runs/S01/cloud-audit/worker/audit.json'
audit = read(audit_path)
checks = []
citations = []


def walk(value):
    if isinstance(value, dict):
        if (isinstance(value.get('path'), str) and value['path'].startswith(
                ('evidence/c1/', 'runs/S01/', 'docs/')) and 'sha256' in value):
            citations.append((value['path'], value['sha256']))
        for item in value.values():
            walk(item)
    elif isinstance(value, list):
        for item in value:
            walk(item)


walk(audit)
unique = sorted(set(citations))
assert unique and all(sha(path) == expected for path, expected in unique)
checks.append(dict(id='source_citations', status='pass', checked=len(unique)))
assert {row['id'] for row in audit['A05_frozen_C01_C10']} == {'C%02d' % n for n in range(1, 11)}
checks.append(dict(id='frozen_requirement_coverage', status='pass', count=10))
assert len(audit['A04_eight_sample_protocol_audit']) == 8
checks.append(dict(id='all_eight_samples_retained', status='pass'))

notes = (ROOT/'evidence/c1/materials/notes.txt').read_text()
expected = [
    dict(task='更新部署文档', owner='赵宁', due='周五', source_quote='赵宁负责更新部署文档，截止周五。'),
    dict(task='补充回归用例', owner='许静', due='2026-10-09', source_quote='许静负责补充回归用例，截止2026-10-09。'),
    dict(task='补充日志告警', owner=None, due=None, source_quote='决定补充日志告警。'),
]
assert all(row['source_quote'] in notes for row in expected)
for sample in ['B1', 'A1', 'A2', 'B2']:
    base = 'evidence/c1/package/' + sample + '/'
    actual = read(base + 'artifacts/actions.json')
    if isinstance(actual, dict):
        actual = actual['artifacts']['actions']
    assert actual == expected
    control = read(base + 'job/control.json')
    assert control['phase'] == 'committed'
    for ref in control['refs']:
        historical = ref['path'].split('forge-protocol-comparison-20261003/', 1)[1]
        assert sha('evidence/c1/' + historical) == ref['sha256']
    chain = audit['A01_package_chains']['package/' + sample]
    assert chain['complete_original_chain_pass']
    checks.append(dict(id='package_' + sample, status='pass', actions=3,
                       original_refs_verified=len(control['refs'])))

corrections = audit['A03_B2_corrections']
assert corrections['coordinator_analysis_cycle_count'] == 3
for row in corrections['coordinator_analysis_cycles']:
    raw = read(row['evidence']['path'])
    assert raw['exit_code'] == row['exit_code']
assert read('evidence/c1/package/B2/logs/018-worker-capture-index-draft.json')['exit_code'] == 1
assert read('evidence/c1/package/B2/logs/034-audit-final-index.json')['exit_code'] == 1
checks.append(dict(id='B2_budget_violation_retained', status='pass', analysis_cycles=3, limit=2,
                   rejected_bridge_operations=2))
historical = read('state/history/project-todo-before-cloud.json')
partial_ids = ['real_agent_executor_integration', 'real_worker_failure_recovery_trials',
               'bridge_budget_timeout_validation']
historical_statuses = {row['id']: row['status'] for row in historical['todo']}
assert all(historical_statuses[id] == 'partial' for id in partial_ids)
assert historical_statuses['preset_browser_acceptance'] == 'blocked'
checks.append(dict(id='C10_historical_tracks', status='pass', source='state/history/project-todo-before-cloud.json',
                   partial_ids=partial_ids, browser_status='blocked',
                   scope='Root history review, outside the independent worker input set'))
result = dict(schema='forge-c1-root-final-review/1', status='completed_with_historical_gaps',
              recorded_at=datetime.now(timezone.utc).isoformat(), audit_path=audit_path,
              audit_sha256=sha(audit_path), checks=checks,
              original_csv_recomputation='runs/S01/root-csv-recomputation.json',
              original_C1_verdict='partial/inconclusive',
              package_completed=4, original_total_completed=7, original_selected=8,
              project_A2='running/unknown at original non-atomic cutoff; saved values do not establish completion',
              root_resolution=['C07 passes preservation only; B2 violated the separate frozen two-correction policy.',
                               'C10 is checked by Root against preserved history, not asserted as an independent worker result.',
                               'Old source-review and embedded index prose limit full-blindness; independent source computations remain available.',
                               'An initial auditor reference lookup bug was corrected using historical path mapping; raw C1 was unchanged.'],
              performance_gain=None, tokens=None, cost=None, old_native_calls=0)
(ROOT/'runs/S01/final-review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(status=result['status'], checks=len(checks), citations=len(unique)), ensure_ascii=False))
