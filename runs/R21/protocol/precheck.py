"""Prospective first step: inspect specification before generating any future truth."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'runs/R21'
assert not (BASE/'inputs/raw').exists() and not (BASE/'evaluation').exists()
files=[]
for f in sorted((BASE/'protocol').glob('*')):
    if f.is_file():
        b=f.read_bytes(); files.append(dict(path=f.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b)))
assert len(json.loads((BASE/'protocol/acceptance.json').read_text(encoding='utf-8'))['criteria'])==5
assert b'2026100902' in (BASE/'protocol/make_case.py').read_bytes()
print(json.dumps(dict(actual_first_step='Prospective new case protocol inspected before generation',future_truth_exists=False,
    future_dates=42,seed_committed=2026100902,zero_improvement_acceptable=True,files=files),ensure_ascii=False))
