"""Retain mistaken-path evidence byte-for-byte outside the skill candidate."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
source = (ROOT / 'runs/R20/final/candidate/C13/forward-case/review/preparation').resolve()
target = (ROOT / 'runs/R20/forward-case/review/preparation-path-error').resolve()
assert source.is_relative_to(ROOT) and target.is_relative_to(ROOT) and not target.exists()
target.mkdir(parents=True)
rows = []
for f in sorted(source.iterdir()):
    assert f.is_file()
    b = f.read_bytes()
    dest = target / f.name
    f.rename(dest)
    assert dest.read_bytes() == b
    rows.append({'original_path': f.relative_to(ROOT).as_posix(), 'archived_path': dest.relative_to(ROOT).as_posix(),
        'size_bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()})
source.rmdir()
source.parent.rmdir()
source.parent.parent.rmdir()
receipt = ROOT / 'runs/R20/coordination/c13-path-recovery.json'
with receipt.open('x', encoding='utf-8') as stream:
    json.dump({'observed_at': datetime.now(timezone.utc).isoformat(), 'files': rows,
        'reason': 'Coordinator packet path correction; same independent actor retained. Original blocked preparation preserved, no science attempted.',
        'maker_correction': 'Source lock clarified to runs/R20/final/candidate/C13-lock.json before production.',
        'acceptor': '/root/r20_c13_forward_acceptor', 'requested_model': 'gpt-6-luna', 'requested_reasoning': 'high',
        'actual_model': None, 'tokens': None, 'cost': None}, stream, ensure_ascii=False, indent=2)
print(json.dumps({'archived_files': len(rows), 'same_actor_recovery': True}))
