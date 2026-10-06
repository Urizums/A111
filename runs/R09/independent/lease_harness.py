#!/usr/bin/env python3
"""Hold one coordinator lease while an independent process probes it."""
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--competing-record', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    lease_cli = root / 'scripts/coordinator_lease.py'
    recorder = root / 'scripts/record_command.py'
    hold_argv = [sys.executable, str(lease_cli), 'hold', '--root', str(root), '--owner', 'r09-independent-checkout']
    competing_argv = [sys.executable, str(recorder), '--out', str(args.competing_record), '--',
                      sys.executable, str(lease_cli), 'probe', '--root', str(root)]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    record = dict(schema='forge-command-record/1', argv=hold_argv, cwd=str(root),
                  begin=stamp(), state='started')
    with args.out.open('x', encoding='utf-8') as evidence:
        json.dump(record, evidence, ensure_ascii=False, indent=2)
        evidence.flush()
        os.fsync(evidence.fileno())

        process = None
        first_line = b''
        remainder = b''
        stderr = b''
        code = 127
        harness_error = None
        competitor_code = None
        try:
            process = subprocess.Popen(hold_argv, cwd=root, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            first_line = process.stdout.readline()
            competing = subprocess.run(competing_argv, cwd=root, capture_output=True)
            competitor_code = competing.returncode
            process.stdin.write(b'release\n')
            process.stdin.flush()
            process.stdin.close()
            code = process.wait(timeout=10)
            remainder = process.stdout.read()
            stderr = process.stderr.read()
        except BaseException as exc:
            harness_error = repr(exc)
            if process is not None and process.poll() is None:
                try:
                    process.stdin.write(b'release\n')
                    process.stdin.flush()
                    process.stdin.close()
                    code = process.wait(timeout=10)
                    remainder = process.stdout.read()
                    stderr = process.stderr.read()
                except BaseException:
                    process.kill()
                    process.wait()
                    remainder = process.stdout.read()
                    stderr = process.stderr.read()
                    code = process.returncode
            elif process is not None:
                code = process.returncode
                remainder = process.stdout.read()
                stderr = process.stderr.read()
            if harness_error:
                stderr += ('\nHARNESS: ' + harness_error).encode('utf-8')

        stdout = first_line + remainder
        record.update(state='finished', end=stamp(), exit_code=code,
                      stdout=stdout.decode('utf-8', errors='replace'),
                      stderr=stderr.decode('utf-8', errors='replace'),
                      stdout_base64=base64.b64encode(stdout).decode(),
                      stderr_base64=base64.b64encode(stderr).decode())
        evidence.seek(0)
        json.dump(record, evidence, ensure_ascii=False, indent=2)
        evidence.write('\n')
        evidence.truncate()
        evidence.flush()
        os.fsync(evidence.fileno())

    print(json.dumps(dict(hold_exit_code=code, competing_recorder_exit_code=competitor_code,
                          hold_first_line=first_line.decode('utf-8', errors='replace').strip(),
                          release_observed=b'"released": true' in stdout or b'"released":true' in stdout,
                          harness_error=harness_error), ensure_ascii=False))
    return 0 if code == 0 and competitor_code == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
