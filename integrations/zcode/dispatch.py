#!/usr/bin/env python3
"""Small explicit ZCode CLI dispatch. No server, scheduler, retry, or credential copying."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def stamp():
    return datetime.now(timezone.utc).isoformat()


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['prepare', 'check', 'run'])
    p.add_argument('--repo', type=Path, default=Path.cwd())
    p.add_argument('--job', type=Path, default=Path(__file__).with_name('first-job.json'))
    p.add_argument('--executable', default='zcode')
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    repo = a.repo.resolve()
    raw = a.job.read_bytes()
    job = json.loads(raw)
    if job.get('schema') != 'forge-zcode-job/1' or job.get('mode') != 'plan':
        raise ValueError('This first adapter accepts read-only plan jobs only')
    subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', job['base_commit'], 'HEAD'], check=True)
    timeout = job['timeout_seconds']
    if type(timeout) is not int or not 1 <= timeout <= 300:
        raise ValueError('Timeout must be 1..300 seconds')
    executable = shutil.which(a.executable)
    argv = [executable or a.executable, '--cwd', str(repo), '--mode', 'plan',
            '--output-format', 'json', '--prompt', job['prompt']]
    record = {'job_id': job['id'], 'job_sha256': hashlib.sha256(raw).hexdigest(),
              'argv': argv, 'head': git(repo, 'rev-parse', 'HEAD'),
              'executable_found': executable is not None, 'model_called': False,
              'tokens': None, 'cost': None, 'acceptance': 'not_assessed'}
    if a.action == 'prepare':
        record['state'] = 'prepared_only'
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0
    if executable is None:
        record.update(state='blocked', reason='ZCode CLI is not installed/reachable on this host')
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 2
    help_result = subprocess.run([executable, '--help'], cwd=repo, stdin=subprocess.DEVNULL,
                                 capture_output=True, text=True, timeout=10)
    supported = help_result.returncode == 0 and all(
        flag in help_result.stdout for flag in ['--cwd', '--prompt', '--mode', '--output-format'])
    record.update(help_exit_code=help_result.returncode, supported_flags=supported)
    if not supported or a.action == 'check':
        record['state'] = 'cli_preflight_only' if supported else 'blocked_unsupported_cli'
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0 if supported else 2
    if a.out is None:
        raise ValueError('run requires a fresh --out directory')
    out = a.out.resolve()
    if out == repo or repo in out.parents:
        raise ValueError('Keep the receipt directory outside this checkout')
    before = git(repo, 'status', '--porcelain=v1', '--untracked-files=all')
    if before:
        raise ValueError('Use a clean isolated checkout for this first live read-only job')
    out.mkdir(parents=True, exist_ok=False)
    (out / 'job.json').write_bytes(raw)
    record.update(state='intent_saved', began_at=stamp())
    (out / 'intent.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    try:
        result = subprocess.run(argv, cwd=repo, stdin=subprocess.DEVNULL,
                                capture_output=True, timeout=timeout)
        (out / 'stdout.bin').write_bytes(result.stdout)
        (out / 'stderr.bin').write_bytes(result.stderr)
        record.update(state='executed_unverified', model_called='not_observable_from_exit_code',
                      exit_code=result.returncode, ended_at=stamp(),
                      workspace_unchanged=git(repo, 'status', '--porcelain=v1', '--untracked-files=all') == before)
    except subprocess.TimeoutExpired as error:
        (out / 'stdout.bin').write_bytes(error.stdout or b'')
        (out / 'stderr.bin').write_bytes(error.stderr or b'')
        record.update(state='local_timeout_remote_state_unknown', ended_at=stamp(),
                      model_called='unknown', remote_terminal_verified=False,
                      reason='Local subprocess cutoff is not provider or descendant termination proof; reconcile before retry')
    (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record['state'] == 'executed_unverified' and record['exit_code'] == 0 and record['workspace_unchanged'] else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({'state': 'blocked', 'error': str(error)}, ensure_ascii=False))
        raise SystemExit(2)
