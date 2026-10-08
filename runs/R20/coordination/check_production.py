"""Verify ended production identity; never substitutes for independent science review."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
scope = ROOT / 'runs/R20/execution'
manifest_path = scope / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == '25dfbf98875721fd5dcf3af0adc4ecb7109e965ee6743deef887f5e0ea2dfe06'
listed = set()
for row in manifest['files']:
    path = (scope / row['path']).resolve()
    assert path.is_relative_to(scope.resolve())
    data = path.read_bytes()
    assert len(data) == row['size_bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
    assert row['path'] not in listed
    listed.add(row['path'])
actual = {p.relative_to(scope).as_posix() for p in scope.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
assert actual - listed == set(manifest['excluded']), (actual - listed, manifest['excluded'])
assert not listed - actual
records = []
for p in sorted((scope / 'evidence').glob('0*.json')):
    r = json.loads(p.read_text(encoding='utf-8'))
    assert r['state'] == 'finished' and r['end'] and r['exit_code'] is not None, p.name
    records.append(dict(path=p.relative_to(ROOT).as_posix(), exit_code=r['exit_code']))
assert len(records) == 18
assert [r['path'].rsplit('/', 1)[-1] for r in records if r['exit_code'] != 0] == [
    '010-author-receiving-check.json', '012-author-check-normalized.json']
assert not json.loads((scope / 'checkpoint.json').read_text(encoding='utf-8'))['unknown_call_states']
pdf = scope / 'delivery/paper/paper.pdf'
assert hashlib.sha256(pdf.read_bytes()).hexdigest() == 'fccb98acd2785f6db5fccc45c97e43fc99d2e353e7fb60613bc903a93da2d1cb'
print(json.dumps(dict(payload_files=len(listed), terminal_files=len(actual),
    payload_bytes=sum(r['size_bytes'] for r in manifest['files']), command_records=records,
    largest_file_bytes=max(r['size_bytes'] for r in manifest['files']),
    current_artifact_root='delivery/', formal_reception='unverified',
    claim='Exact final and retained historical bytes with ended processes only.'), ensure_ascii=False))
