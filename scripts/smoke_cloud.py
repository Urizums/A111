#!/usr/bin/env python3
"""Exercise an installed CLI with fresh local fixture state, not historical workers."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    executable = str(args.prefix.resolve() / 'bin/agent-forge')
    release = (args.prefix / 'current').resolve()
    package = str(release / 'skills/forge-agent-flow/assets/example-package.json')
    records, checks = [], []

    def call(label, *arguments, code=0):
        argv = [executable, *map(str, arguments)]
        begin = time.monotonic_ns()
        result = subprocess.run(argv, cwd=args.out, capture_output=True)
        row = dict(label=label, argv=argv, exit_code=result.returncode, expected_exit=code,
                   elapsed_ns=time.monotonic_ns()-begin,
                   stdout_base64=base64.b64encode(result.stdout).decode(),
                   stderr_base64=base64.b64encode(result.stderr).decode(),
                   stdout=result.stdout.decode(errors='replace'), stderr=result.stderr.decode(errors='replace'))
        records.append(row)
        checks.append(dict(id=label, pass_=result.returncode == code))
        try:
            return json.loads(result.stdout)
        except ValueError:
            return {}

    def check(name, condition):
        checks.append(dict(id=name, pass_=bool(condition)))

    def save(name, value):
        path = (args.out / name).resolve()
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        return path

    verify = call('installed-integrity', 'verify', '--json')
    check('installed-integrity-verdict', verify.get('ok') is True)
    call('help', '--help')
    call('unknown-command-rejected', 'does-not-exist', code=2)
    call('package-validation', 'package', 'validate', package)
    inputs = save('inputs.json', {'notes': 'No commitments were made. This is a CLI fixture.'})
    state = (args.out / 'fresh-package-state.json').resolve()
    initial = call('package-start', 'package', 'start', package, '--inputs', inputs, '--state', state)
    before = state.read_bytes()
    resumed = call('package-resume', 'package', 'next', package, '--state', state)
    check('next-readonly', state.read_bytes() == before)
    check('same-invocation', initial.get('invocation_id') == resumed.get('invocation_id')
          and bool(resumed.get('invocation_id')))
    stale = save('stale-response.json', dict(invocation_id='stale', outcome='ok',
                                           artifacts={'actions': []}, evidence=['Fixture']))
    call('stale-response-rejected', 'package', 'advance', package, '--state', state, '--response', stale, code=2)
    check('rejection-preserves-state', state.read_bytes() == before)
    response = save('response.json', dict(invocation_id=resumed.get('invocation_id'), outcome='ok',
                                         artifacts={'actions': []}, evidence=['Local no-action fixture; no LLM claim.']))
    final = call('package-complete', 'package', 'advance', package, '--state', state, '--response', response)
    persisted = json.loads(state.read_text())['flow_state']
    check('completed-empty-actions', final.get('status') == 'completed'
          and persisted.get('status') == 'completed' and persisted.get('artifacts', {}).get('actions') == [])
    completed = state.read_bytes()
    call('completed-resume', 'package', 'next', package, '--state', state)
    check('completed-resume-readonly', state.read_bytes() == completed)
    changed = json.loads(Path(package).read_text()); changed['flow']['goal'] += ' changed'
    changed_path = save('changed-package.json', changed)
    call('changed-package-rejected', 'package', 'next', changed_path, '--state', state, code=2)
    check('drift-rejection-preserves-state', state.read_bytes() == completed)
    result = dict(schema='forge-cloud-smoke/1', passed=all(row['pass_'] for row in checks),
                  release=str(release), checks=checks, commands=records,
                  state_sha256=hashlib.sha256(state.read_bytes()).hexdigest(),
                  scope='Installed CLI / local package fixtures; real native evidence is separate under runs/S03.')
    save('report.json', result)
    print(json.dumps({'passed': result['passed'], 'checks': len(checks), 'report': str(args.out / 'report.json')}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
