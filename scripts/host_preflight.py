#!/usr/bin/env python3
"""Read-only checkout/host diagnostics; never repair evidence or invoke workers."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
import platform
import sys


def inspect_lock(root, lock_name):
    """Check frozen bytes without changing files; no concurrent-read guarantee."""
    def relative(name):
        if (not isinstance(name, str) or not name or '\\' in name
                or PureWindowsPath(name).drive or name.startswith('/')
                or any(p in {'', '.', '..'} for p in name.split('/'))):
            raise ValueError('noncanonical relative path: ' + repr(name))
        path = root / name
        for part in [path, *path.parents]:
            if part == root:
                break
            if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
                raise ValueError('linked component: ' + name)
        if not path.resolve().is_relative_to(root):
            raise ValueError('path escapes checkout: ' + name)
        return path

    errors, checked = [], 0
    try:
        lock = json.loads(relative(lock_name).read_text(encoding='utf-8'))
        rows = lock.get('entries', lock.get('files'))
        if not isinstance(rows, list) or not rows:
            raise ValueError('lock must contain nonempty entries or files')
        seen = set()
        for row in rows:
            name = None
            try:
                if not isinstance(row, dict):
                    raise ValueError('lock row must be an object')
                name = row.get('path')
                if not isinstance(name, str):
                    raise ValueError('lock path must be a string')
                if name in seen:
                    raise ValueError('duplicate lock path: ' + str(name))
                seen.add(name)
                path = relative(name)
                if not path.is_file():
                    raise ValueError('not a regular file: ' + name)
                raw = path.read_bytes()
                checked += 1
                if len(raw) != row['size_bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                    errors.append(dict(path=name, reason='byte_mismatch', crlf_count=raw.count(b'\r\n')))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append(dict(path=name, reason=str(exc)))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(dict(path=lock_name, reason=str(exc)))
    return dict(lock=lock_name, files_checked=checked, ok=not errors, errors=errors)


def probe(root, locks):
    capabilities = dict(fcntl=importlib.util.find_spec('fcntl') is not None,
                        posix_component_open=all(hasattr(os, name) for name in ['O_DIRECTORY', 'O_NOFOLLOW', 'O_NONBLOCK']) and os.open in os.supports_dir_fd,
                        linux_boot_marker=Path('/proc/sys/kernel/random/boot_id').is_file())
    checks = [inspect_lock(root, name) for name in locks]
    compatible = all(capabilities.values())
    byte_identity = all(c['ok'] for c in checks)
    actions = []
    if not byte_identity:
        actions.append('Preserve this failure. Use a fresh git -c core.autocrlf=false clone or restore exact source blobs only after checking local edits; never regenerate historical locks to accept drift.')
    if not compatible:
        actions.append('Use an actually available Linux/WSL runtime and probe again. Native Windows continuation/secure POSIX opener/recording are unsupported; do not silently weaken file or lease safety.')
    if compatible and byte_identity:
        actions.append('Probe the actual coordinator lease, reconcile pending native calls, then hold the lease before shared-state mutation.')
    return dict(schema='forge-host-preflight/1', root=str(root), python=sys.version.split()[0],
                platform=platform.system(), capabilities=capabilities, locks=checks,
                byte_identity=byte_identity, continuation_runtime_compatible=compatible,
                eligible_for_lease_probe=compatible and byte_identity, actions=actions,
                limits=['Read-only byte identity and API availability; no concurrent filesystem safety proof',
                        'Does not acquire a lease, reconcile workers, replay effects or invoke providers',
                        'Snapshot renameat2/filesystem support and installed-product behavior require actual separate checks'],
                tokens=None, cost=None)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--lock', action='append', help='canonical repository-relative lock; repeatable')
    a = p.parse_args()
    root = a.root.absolute()
    if root.is_symlink() or (hasattr(root, 'is_junction') and root.is_junction()) or not root.is_dir():
        p.error('--root must be an existing unlinked checkout directory')
    result = probe(root.resolve(), a.lock or ['state/source-lock.json', 'runs/R07/candidate/C6-lock.json'])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['eligible_for_lease_probe'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
