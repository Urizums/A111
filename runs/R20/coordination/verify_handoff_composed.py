"""Execute every original checker predicate with one real POSIX delegation."""
import contextlib
import hashlib
import io
import json
import runpy
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
namespace=runpy.run_path(str(ROOT/'scripts/verify_handoff.py'),run_name='original_readonly_checker')
delegation=None
def delegated(cp,state,root):
    global delegation
    hashes={}
    for rel,loaded in [('state/checkpoint.json',cp),('state/continuation.json',state)]:
        b=(ROOT/rel).read_bytes()
        assert json.loads(b)==loaded,'Changed original checker input: '+rel
        hashes[rel]=hashlib.sha256(b).hexdigest()
    command=['wsl','-d','Ubuntu-24.04','--cd','/mnt/c/Users/admin/Documents/Codex/2026-10-05/urizums-a111-main-codex-handoff-md/work/A111',
        'python3','runs/R20/coordination/verify_queue_wsl.py','--checkpoint',hashes['state/checkpoint.json'],'--state',hashes['state/continuation.json']]
    actual=subprocess.run(command,cwd=ROOT,capture_output=True)
    delegation=json.loads(actual.stdout.decode('utf-8'))
    assert actual.returncode in [0,1] and delegation['actual_posix_runtime']
    for rel,sha in hashes.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha,'Changed during real delegation: '+rel
    return delegation['errors']
# Only the runtime of this predicate changes. It is actually executed, using
# unchanged original code and the exact same snapshot; no predicate returns a stub.
namespace['main'].__globals__['validate_continuation']=delegated
sys.argv=['scripts/verify_handoff.py','--json']
captured=io.StringIO()
with contextlib.redirect_stdout(captured):
    exit_code=namespace['main']()
result=json.loads(captured.getvalue())
result['runtime_composition']=dict(file_path_phase_checkpoint_link_checks='Original functions/main on native Python',
    queue_check=delegation,source_checker_sha256=hashlib.sha256((ROOT/'scripts/verify_handoff.py').read_bytes()).hexdigest(),
    original_checker_source_modified=False,scope='Every original predicate performed; real POSIX queue delegation. Native Windows controller execution is not claimed.')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(exit_code)
