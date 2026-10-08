"""Later reconstruction from the exact 003-to-004 patch; not an invocation-time capture."""
import hashlib
from pathlib import Path

p=Path('runs/R20/design/research/smoke.py')
s=p.read_text(encoding='utf-8')
begin=s.index("    for name in ['capacity','budget']:")
end=s.index("    assert len([r for r in raw",begin)
historic=s[:begin]+s[end:]
target=p.with_name('smoke-invocation-003.py')
assert not target.exists(), 'archive already exists; do not overwrite'
target.write_text(historic,encoding='utf-8')
print('Recovered historical script:',target.as_posix())
print('Actual SHA256:',hashlib.sha256(target.read_bytes()).hexdigest())
print('Reconstruction time only; original invocation source hash was not recorded.')
