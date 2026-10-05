"""Run the unchanged final suites against one frozen, staged source selection."""
import argparse,json,os,subprocess,sys
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--python',required=True);p.add_argument('--prefix',type=Path,required=True);a=p.parse_args()
root=a.root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
def run(label,argv):
    result=subprocess.run([sys.executable,str(root/'scripts/record_command.py'),'--out',str(out/(label+'.json')),'--',*map(str,argv)],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print(json.dumps({'step':label,'exit_code':result.returncode}),flush=True)
    if result.returncode:
        sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr);raise SystemExit(result.returncode)
run('integrity',[a.python,'-B','scripts/verify_handoff.py','--json'])
run('auxiliary',[a.python,'-B','-m','unittest','discover','-s','scripts','-p','test_*.py'])
run('install',[a.python,'-B','scripts/deploy_cloud.py','--prefix',a.prefix])
run('installed-smoke',[a.python,'-B','scripts/smoke_cloud.py','--prefix',a.prefix,'--out',out/'smoke'])
installed=a.prefix/'current'
for label,relative in [('snapshot','runs/R06/snapshot'),('budget','runs/R06/budget')]:
    run('installed-c5-'+label,[str(a.prefix/'venv/bin/python'),'-B','-m','unittest','discover','-s',str(installed/relative),'-p','test_*.py'])
run('installed-identity',[a.python,'-B','-c','import sys,json;from pathlib import Path;sys.path.insert(0,"scripts");from delivery import source_files,verify_release;verify_release(Path(sys.argv[1]).resolve(),source_files(Path.cwd()));print(json.dumps({"exact_tree":True}))',installed])
(out/'summary.json').write_text(json.dumps({'status':'pass','python':a.python,'prefix':str(a.prefix),'checks':7,'source':'frozen tracked selection; exact installed tree checked again after execution'},indent=2)+'\n')
