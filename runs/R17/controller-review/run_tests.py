import os, subprocess, sys
repo = sys.argv[1]
env = os.environ.copy()
env['PYTHONPATH'] = repo + '/runs/R17/controller-review/shim:' + repo + '/scripts'
raise SystemExit(subprocess.run([sys.executable, '-B', '-m', 'unittest', 'test_continuation'],
                               cwd=repo + '/scripts', env=env).returncode)
