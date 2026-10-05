"""Create a new export manifest, refusing to hide source or cutoff drift."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from verify_handoff import ROOT, MUTABLE, read, verify_entries

errors = verify_entries(ROOT, read(ROOT/'state/source-lock.json')['entries'])
errors += verify_entries(ROOT, read(ROOT/'evidence/c1/Snapshot_Manifest.json')['entries'], 'evidence/c1/')
if errors:
    raise SystemExit('\n'.join(errors))
entries = []
for p in sorted(ROOT.rglob('*')):
    rel = p.relative_to(ROOT)
    if (not p.is_file() or any(x in MUTABLE for x in rel.parts)
        or p.name == 'artifact-manifest.json' or p.suffix in {'.pyc','.gz','.bundle'}):
        continue
    data = p.read_bytes()
    entries.append({'path':rel.as_posix(),'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
obj={'schema':'forge-release-manifest/1','created_at':datetime.now(timezone.utc).isoformat(),
     'mutable_directories':['state','runs','validation'], 'entries':entries,
     'limits':'Hash checks establish byte identity, not correctness or freshness of historical claims.'}
(ROOT/'artifact-manifest.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'release_files':len(entries)}))
