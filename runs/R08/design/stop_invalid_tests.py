"""Terminate only the verified current mutable-source test tree, retaining its record."""
import os
from pathlib import Path
import signal

pid=1031
cmd=(Path('/proc')/str(pid)/'cmdline').read_bytes()
if b'unittest' not in cmd or b'test_*.py' not in cmd:
    raise SystemExit('Current PID is not the captured test; no termination performed')
children={}
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        text=(p/'stat').read_text()
        parent=int(text[text.rfind(')')+2:].split()[1])
        children.setdefault(parent,[]).append(int(p.name))
    except (OSError,ValueError):pass
targets=[]
def visit(pid):
    for child in children.get(pid,[]):visit(child)
    targets.append(pid)
visit(pid)
print({'terminated_invalid_test_tree':targets})
for p in targets:
    try:os.kill(p,signal.SIGTERM)
    except ProcessLookupError:pass
