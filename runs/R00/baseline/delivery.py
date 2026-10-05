"""File selection and byte checks shared by cloud installation and packaging."""
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(root):
    manifest = root / 'delivery-manifest.json'
    if manifest.exists():
        rows = json.loads(manifest.read_text())['files']
        for row in rows:
            path = root / row['path']
            if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                raise ValueError('Unsafe delivery path: ' + row['path'])
            if not path.is_file() or digest(path) != row['sha256']:
                raise ValueError('Delivery bytes changed: ' + row['path'])
        return rows
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'],
                            capture_output=True, check=True)
    names = sorted(filter(None, result.stdout.decode().split('\0')))
    if not names:
        raise ValueError('No tracked files; stage the delivery before packaging')
    rows = []
    for name in names:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Delivery requires regular tracked files: ' + name)
        rows.append(dict(path=name, sha256=digest(path), size_bytes=path.stat().st_size))
    return rows


def content_id(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
