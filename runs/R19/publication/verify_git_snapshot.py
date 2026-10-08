"""Read committed frozen bytes, independent of untracked checkout files."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--commit', required=True)
parser.add_argument('--lock', action='append', required=True)
args = parser.parse_args()
raw = subprocess.check_output(['git', '-c', 'core.longpaths=true', 'ls-tree', '-rz', args.commit], cwd=ROOT)
objects = {}
for line in raw.split(b'\0'):
    if line:
        header, path = line.split(b'\t', 1)
        mode, kind, oid = header.split()
        assert kind == b'blob'
        objects[path.decode('utf-8')] = oid.decode('ascii')
index = json.loads(subprocess.check_output(['git', 'show', args.commit + ':state/revision-locks.json'], cwd=ROOT))
missing = []
for relative in index['locks']:
    if relative not in objects:
        missing.append(relative)
        continue
    lock = json.loads(subprocess.check_output(['git', 'show', args.commit + ':' + relative], cwd=ROOT))
    missing.extend(row['path'] for row in lock['files'] if row['path'] not in objects)
assert not missing, {'missing_frozen_paths_in_commit': missing}
cache = {}
checked = 0
process = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                           stdin=subprocess.PIPE, stdout=subprocess.PIPE)
try:
    for relative in args.lock:
        lock = json.loads(subprocess.check_output(['git', 'show', args.commit + ':' + relative], cwd=ROOT))
        for row in lock['files']:
            oid = objects[row['path']]
            if oid not in cache:
                process.stdin.write((oid + '\n').encode('ascii'))
                process.stdin.flush()
                header = process.stdout.readline().split()
                assert len(header) == 3 and header[1] == b'blob'
                size = int(header[2])
                remaining = size
                digest = hashlib.sha256()
                while remaining:
                    block = process.stdout.read(min(remaining, 1024 * 1024))
                    assert block, 'Unexpected Git object stream EOF'
                    digest.update(block)
                    remaining -= len(block)
                assert process.stdout.read(1) == b'\n'
                cache[oid] = size, digest.hexdigest()
            assert cache[oid] == (row['size_bytes'], row['sha256']), row['path']
            checked += 1
finally:
    process.stdin.close()
    process.stdout.close()
    assert process.wait(timeout=30) == 0
print(json.dumps({'commit': args.commit, 'registered_locks_present': len(index['locks']),
                  'registered_frozen_paths_present': True, 'selected_frozen_files_checked': checked,
                  'distinct_blobs_checked': len(cache), 'ok': True,
                  'scope': 'Committed Git byte identity/coverage only; not paper or runtime acceptance.'}))
