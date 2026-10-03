#!/usr/bin/env python3
"""Package tracked source and reports, without credentials, caches or git objects."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile

from delivery import content_id, source_files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    rows = source_files(root)
    manifest = dict(schema='forge-delivery/1', content_id=content_id(rows), files=rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation keeps previously published delivery archives intact.
    with args.out.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz') as archive:
        for row in rows:
            archive.add(root / row['path'], arcname='agent-forge/' + row['path'], recursive=False)
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
        entry = tarfile.TarInfo('agent-forge/delivery-manifest.json'); entry.size = len(raw)
        entry.mode = 0o644
        archive.addfile(entry, io.BytesIO(raw))
    sha = hashlib.sha256(args.out.read_bytes()).hexdigest()
    args.out.with_name(args.out.name + '.sha256').write_text(sha + '  ' + args.out.name + '\n')
    print(json.dumps(dict(archive=str(args.out.resolve()), sha256=sha,
                         content_id=manifest['content_id'], files=len(rows))))


if __name__ == '__main__':
    main()
