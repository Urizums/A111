"""Check terminal author inventory, exact source and ended command receipts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
base = ROOT / 'runs/R20/forward-case/production'
manifest = base / 'manifest.json'
assert hashlib.sha256(manifest.read_bytes()).hexdigest() == 'f0a7523ad9081c56f96eb5147e7adaa326fa9eaefef566ccbd2fa713df63b093'
data = json.loads(manifest.read_text(encoding='utf-8'))
for row in data['inventory']:
    f = (base / row['path']).resolve()
    assert f.is_relative_to(base.resolve())
    b = f.read_bytes()
    assert len(b) == row['size_bytes'] and hashlib.sha256(b).hexdigest() == row['sha256'], row['path']
for rel, expected in data['source_lock_sha256'].items():
    assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected, rel
records = []
for f in sorted((base / 'evidence').glob('*.json')):
    row = json.loads(f.read_text(encoding='utf-8'))
    if 'argv' in row:
        assert row['state'] == 'finished' and row['exit_code'] is not None and row['begin']['utc'] and row['end']['utc'], f
        records.append({'path': f.relative_to(ROOT).as_posix(), 'exit_code': row['exit_code']})
assert len(records) == 11, records
print(json.dumps({'inventory_files': len(data['inventory']), 'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
    'records': records, 'scope': 'Exact author inventory and terminal receipts only; independent scientific acceptance pending.'}))
