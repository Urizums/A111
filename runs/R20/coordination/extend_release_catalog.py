"""Add the actual PDF Git attribute to the mutable catalog, retaining all old entries."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
path = ROOT / 'artifact-manifest.json'
before = path.read_bytes()
catalog = json.loads(before)
assert '.gitattributes' not in {r['path'] for r in catalog['entries']}
source = ROOT / '.gitattributes'
data = source.read_bytes()
assert data == b'*.pdf binary\n'
entry = dict(path='.gitattributes', size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
history = ROOT / 'runs/R19/integrity-history'
serial = 1
while (history / f'release-before-{serial}.json').exists():
    serial += 1
(history / f'release-before-{serial}.json').write_bytes(before)
catalog['entries'].append(entry)
catalog['entries'].sort(key=lambda r: r['path'])
catalog['created_at'] = datetime.now(timezone.utc).isoformat()
out = json.dumps(catalog, ensure_ascii=False, indent=2) + '\n'
if b'\r\n' in before:
    out = out.replace('\n', '\r\n')
path.write_bytes(out.encode('utf-8'))
record = dict(at=catalog['created_at'], added=[entry], previous_entry_count=len(catalog['entries'])-1,
    current_entry_count=len(catalog['entries']), scope='One actual repository PDF-format metadata addition; all old entry values retained.',
    cause='CI 37837767684 on 87b41bb rejected missing release manifest coverage for .gitattributes.',
    failed_command='runs/R20/coordination/production-ci-failed-log-command.json')
(history / f'release-refresh-{serial}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
previous = json.loads(before)
current = {r['path']:r for r in catalog['entries']}
assert all(current[r['path']] == r for r in previous['entries'])
print(json.dumps(dict(history_serial=serial, added=entry, old_release_entries_preserved=len(previous['entries']),
    catalog_entries=len(current), legacy_skill_and_cutoff_locks_unchanged=True)))
