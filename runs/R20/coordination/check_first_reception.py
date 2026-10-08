"""Bind actual first-reception records and retained failures to immutable bytes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
scope = ROOT / 'runs/R20/review/initial'
def read(p):
    return json.loads(p.read_text(encoding='utf-8'))
manifest_path = scope / 'manifest.json'
assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == 'c40891a3b49080822d0b4be75850bb6256192f05d38b28b2f9eaec4ce76d6448'
manifest = read(manifest_path)
listed = set()
for row in manifest['files']:
    p = (scope / row['path']).resolve()
    assert p.is_relative_to(scope.resolve())
    b = p.read_bytes()
    assert (len(b), hashlib.sha256(b).hexdigest()) == (row['bytes'], row['sha256']), row['path']
    assert row['path'] not in listed
    listed.add(row['path'])
actual = {p.relative_to(scope).as_posix() for p in scope.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
assert actual - listed == {'manifest.json', 'checkpoint.json'} and not listed - actual
cp = read(scope / 'checkpoint.json')
for name, field in [('first-report.md', 'first_report_sha256'), ('first-result.json', 'first_result_sha256')]:
    assert hashlib.sha256((scope / name).read_bytes()).hexdigest() == cp[field]
commands = []
for p in sorted(scope.glob('command-*.json')):
    r = read(p)
    assert r['state'] == 'finished' and r['end'] and r['exit_code'] is not None, p.name
    commands.append(dict(path=p.name, exit_code=r['exit_code']))
before = read(scope / 'command-freeze-before-holdout.json')
holdout = read(scope / 'command-holdout-evaluation.json')
assert before['exit_code'] == holdout['exit_code'] == 0
assert before['end']['utc'] < holdout['begin']['utc']
pre = read(scope / 'pre_holdout_freeze.json')
for row in pre['pre_holdout_result_records']:
    b = (scope / row['path']).read_bytes()
    assert (len(b), hashlib.sha256(b).hexdigest()) == (row['bytes'], row['sha256'])
assert len(list((scope / 'delivery-pages').glob('page-*.png'))) == 11
result = read(scope / 'first-result.json')
assert set(result['domains']) == {'d1', 'd2', 'd3', 'd4', 'd5'}
assert all(v['verdict'] == 'PASS' for v in result['domains'].values())
declared = result['execution_freeze_command']['path']
print(json.dumps(dict(payload_files=len(listed), terminal_files=len(actual), commands=commands,
    declared_first_verdict='PASS d1-d5', first_holdout_after_actual_freeze=True,
    declared_execution_freeze_path=declared, declared_freeze_path_exists=(ROOT / declared).exists(),
    actual_root_freeze_receipt='runs/R20/coordination/production-freeze-command.json',
    scope='Identity/terminal chronology only; source-binding discrepancy and calibration provenance receive a separate informed check.'), ensure_ascii=False))
