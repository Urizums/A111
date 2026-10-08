"""Preserve author-listed runtime caches separately; never mutate production."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
source = ROOT / 'runs/R19/final/forward/production/manifest.json'
manifest = json.loads(source.read_text(encoding='utf-8'))
directory = ROOT / 'runs/R19/final/forward/production-ephemera'
directory.mkdir(exist_ok=False)
rows = []
for entry in manifest['files']:
    data = (ROOT / entry['path']).read_bytes()
    assert len(data) == entry['size_bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256']
    if '__pycache__' in Path(entry['path']).parts:
        target = directory / (Path(entry['path']).name + '.bin')
        target.write_bytes(data)
        rows.append(dict(original=entry, archived_path=target.relative_to(ROOT).as_posix()))
assert len(rows) == 3
(directory / 'binding.json').write_text(json.dumps(dict(
    author_manifest_files=len(manifest['files']), root_noncache_files_including_manifest=40,
    exclusion='Root revision lock excludes runtime __pycache__; author manifest remains unchanged.',
    archived=rows, claim='Exact original cache byte preservation; not required source/runtime dependency or acceptance.'
), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(author_identity_rows_checked=len(manifest['files']), caches_archived=len(rows),
                      frozen_production_unchanged=True)))
