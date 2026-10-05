#!/usr/bin/env python3
"""Retain raw command evidence. Never pass credentials in argv or captured output."""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def stamp():
    boot = Path('/proc/sys/kernel/random/boot_id')
    return dict(utc=datetime.now(timezone.utc).isoformat(), monotonic_ns=time.monotonic_ns(),
                boot_id=boot.read_text().strip() if boot.exists() else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('a command is required')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Reserve before execution: duplicate output must not repeat the target effect.
    with args.out.open('x', encoding='utf-8') as f:
        begin = stamp()
        record = dict(schema='forge-command-record/1', argv=command, cwd=str(Path.cwd()),
                      begin=begin, state='started')
        json.dump(record, f, indent=2); f.flush(); os.fsync(f.fileno())
        try:
            result = subprocess.run(command, capture_output=True)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except OSError as exc:
            code, stdout, stderr = 127, b'', str(exc).encode()
        record.update(state='finished', end=stamp(), exit_code=code,
                      stdout=stdout.decode('utf-8', errors='replace'),
                      stderr=stderr.decode('utf-8', errors='replace'),
                      stdout_base64=base64.b64encode(stdout).decode(),
                      stderr_base64=base64.b64encode(stderr).decode())
        f.seek(0); json.dump(record, f, ensure_ascii=False, indent=2)
        f.write('\n'); f.truncate(); f.flush(); os.fsync(f.fileno())
    sys.stdout.buffer.write(stdout); sys.stderr.buffer.write(stderr)
    return code if code >= 0 else 128 - code


if __name__ == '__main__':
    raise SystemExit(main())
