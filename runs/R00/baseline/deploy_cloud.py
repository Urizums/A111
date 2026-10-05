#!/usr/bin/env python3
"""Install the Python CLI into a versioned directory on the current cloud host."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv

from delivery import content_id, digest, source_files


LAUNCHER = '''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
prefix = Path(__file__).resolve().parents[1]
root = (prefix / 'current').resolve()
commands = {
    'verify': 'scripts/verify_handoff.py',
    'project': 'skills/forge-agent-flow/scripts/projectctl.py',
    'package': 'skills/forge-agent-flow/scripts/packagectl.py',
    'bridge': 'skills/forge-agent-flow/scripts/hostbridge.py',
    'driver': 'skills/forge-agent-flow/scripts/hostdriver.py',
    'draft': 'skills/forge-agent-flow/scripts/hostdraft.py',
    'capture': 'runs/S02/candidate/forge-agent-flow/scripts/capture.py',
}
if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print('agent-forge COMMAND [ARGS]\\nCommands: ' + ', '.join(commands))
    sys.exit(0)
if sys.argv[1] not in commands:
    print('Unknown command: ' + sys.argv[1], file=sys.stderr)
    sys.exit(2)
target = root / commands[sys.argv[1]]
os.execv(str(prefix / 'venv/bin/python'),
         [str(prefix / 'venv/bin/python'), str(target), *sys.argv[2:]])
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', required=True, type=Path)
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error('Python 3.10+ is required')
    root = Path(__file__).resolve().parents[1]
    prefix = args.prefix.resolve()
    if prefix.is_relative_to(root):
        parser.error('Install outside the source directory')
    rows = source_files(root)
    identity = content_id(rows)
    releases = prefix / 'releases'; releases.mkdir(parents=True, exist_ok=True)
    release = releases / identity
    if not release.exists():
        stage = Path(tempfile.mkdtemp(prefix='.install-', dir=releases))
        try:
            for row in rows:
                target = stage / row['path']; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root / row['path'], target)
                if digest(target) != row['sha256']:
                    raise ValueError('Source changed while installing: ' + row['path'])
            # Verify before activation; state remains portable evidence, not a resumable old host.
            subprocess.run([sys.executable, str(stage / 'scripts/verify_handoff.py'), '--json'], check=True)
            stage.rename(release)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    else:
        for row in rows:
            if digest(release / row['path']) != row['sha256']:
                raise ValueError('Existing release has drifted: ' + row['path'])
    if not (prefix / 'venv/bin/python').exists():
        venv.EnvBuilder(with_pip=False).create(prefix / 'venv')
    bin_dir = prefix / 'bin'; bin_dir.mkdir(exist_ok=True)
    launcher = bin_dir / 'agent-forge'
    launcher.write_text(LAUNCHER); launcher.chmod(0o755)
    link = prefix / '.current-next'
    if link.is_symlink():
        link.unlink()
    link.symlink_to(release, target_is_directory=True)
    os.replace(link, prefix / 'current')
    record = dict(schema='forge-cloud-install/1', release=str(release), content_id=identity,
                  files=len(rows), launcher=str(launcher), python=sys.version,
                  boundary='CLI on this host; no HTTP service or native provider daemon')
    (prefix / 'deployment.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
