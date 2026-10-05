"""File selection and byte checks shared by cloud installation and packaging."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_file(root, name):
    """Accept canonical relative POSIX names with no symlink in any component."""
    if (not isinstance(name, str) or not name or '\x00' in name or '\\' in name
            or PureWindowsPath(name).drive or name.startswith('/')
            or any(part in {'', '.', '..'} for part in name.split('/'))):
        raise ValueError('Noncanonical delivery path: ' + repr(name))
    root = Path(root)
    if root.is_symlink():
        raise ValueError('Delivery root is a symlink')
    root = root.resolve(strict=True)
    path = root
    try:
        for part in name.split('/'):
            path = path / part
            if path.is_symlink():
                raise ValueError('Symlink in delivery path: ' + name)
        if not path.resolve(strict=True).is_relative_to(root):
            raise ValueError('Delivery path escapes root: ' + name)
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError('Delivery path is not a regular file: ' + name)
    except OSError as exc:
        raise ValueError('Unavailable delivery file: ' + name) from exc
    return path


def read_file(root, name):
    """Revalidate at use and open each component without following links (POSIX)."""
    safe_file(root, name)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(Path(root).resolve(strict=True), directory_flags)
    try:
        parts = name.split('/')
        for part in parts[:-1]:
            child = os.open(part, directory_flags, dir_fd=fd)
            os.close(fd)
            fd = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(leaf, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError('Delivery path is not a regular file: ' + name)
            return stream.read()
    except OSError as exc:
        raise ValueError('Delivery path changed or is unsafe: ' + name) from exc
    finally:
        os.close(fd)


def verify_release(root, rows):
    """Check the exact installed tree, including directories, before any reuse."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Release is not a regular directory')
    expected_files = {row['path'] for row in rows}
    expected_dirs = {str(parent) for name in expected_files
                     for parent in PurePosixPath(name).parents if str(parent) != '.'}
    files, directories = set(), set()
    for parent, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            path = Path(parent) / name
            rel = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError('Symlink in release: ' + rel)
            if stat.S_ISDIR(mode):
                directories.add(rel)
            elif stat.S_ISREG(mode):
                files.add(rel)
            else:
                raise ValueError('Non-regular release entry: ' + rel)
    if files != expected_files or directories != expected_dirs:
        raise ValueError('Release file set has drifted: ' + repr(sorted(
            (files ^ expected_files) | (directories ^ expected_dirs))))
    for row in rows:
        raw = read_file(root, row['path'])
        if len(raw) != row['size_bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Release bytes changed: ' + row['path'])


def source_files(root):
    root = Path(root)
    manifest = root / 'delivery-manifest.json'
    if manifest.exists() or manifest.is_symlink():
        rows = json.loads(read_file(root, 'delivery-manifest.json'))['files']
        if not isinstance(rows, list) or not rows:
            raise ValueError('Delivery manifest requires a nonempty file list')
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError('Invalid delivery manifest row')
            name = row.get('path')
            safe_file(root, name)
            if name in seen:
                raise ValueError('Duplicate delivery path: ' + name)
            seen.add(name)
            if (type(row.get('size_bytes')) is not int or row['size_bytes'] < 0
                    or not isinstance(row.get('sha256'), str)
                    or not re.fullmatch('[0-9a-f]{64}', row['sha256'])):
                raise ValueError('Invalid delivery metadata: ' + name)
            raw = read_file(root, name)
            if len(raw) != row['size_bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('Delivery bytes changed: ' + row['path'])
        return rows
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'],
                            capture_output=True, check=True)
    names = sorted(filter(None, result.stdout.decode().split('\0')))
    if not names:
        raise ValueError('No tracked files; stage the delivery before packaging')
    rows = []
    for name in names:
        raw = read_file(root, name)
        rows.append(dict(path=name, sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)))
    return rows


def content_id(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
