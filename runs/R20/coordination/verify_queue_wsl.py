"""Run the original nonportable queue predicate in the real POSIX runtime."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_handoff import validate_continuation
p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--state',required=True);a=p.parse_args()
def read(rel,expected):
    b=(ROOT/rel).read_bytes()
    assert hashlib.sha256(b).hexdigest()==expected,rel
    return json.loads(b)
cp=read('state/checkpoint.json',a.checkpoint)
state=read('state/continuation.json',a.state)
errors=validate_continuation(cp,state,ROOT)
print(json.dumps(dict(errors=errors,checkpoint_sha256=a.checkpoint,state_sha256=a.state,
    actual_posix_runtime=True,original_predicate='verify_handoff.validate_continuation',
    scope='Original real fcntl/POSIX source reads and full queue validation; no runtime stub or monkeypatched lock.'),ensure_ascii=False))
raise SystemExit(1 if errors else 0)
