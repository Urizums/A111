"""Reviewer exercises current consumer CLI/registry on an authorized byte copy."""
from pathlib import Path
import sys,subprocess,time,json,hashlib,copy,shutil
H=Path(__file__).resolve().parent
V=H/'consumer/execution-v2';O=H/'consumer/execution'
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
calls=[]
def cli(label,args,expected):
    out=H/'runtime'/label
    if out.exists():
        previous=json.loads((out/'receipt.json').read_text(encoding='utf-8'))
        assert previous['terminal'] and previous['exit_code']==expected
        assert sha(out/'stdout.log')==previous['stdout_sha256'] and sha(out/'stderr.log')==previous['stderr_sha256']
        calls.append({**previous,'resume_from_known_terminal_receipt':True})
        return json.loads((out/'stdout.log').read_text(encoding='utf-8').strip().splitlines()[-1])
    out.mkdir(parents=True)
    cmd=[sys.executable,'-X','utf8','-B',str(V/'src/receipt_cli.py'),*args]
    start=time.perf_counter()
    with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
        p=subprocess.Popen(cmd,cwd=V,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        pid=p.pid
        try:rc=p.wait(timeout=135)
        except subprocess.TimeoutExpired:p.kill();rc=p.wait();raise
    row={'label':label,'argv':cmd,'pid':pid,'exit_code':rc,'elapsed_seconds':time.perf_counter()-start,'stdout_sha256':sha(out/'stdout.log'),'stderr_sha256':sha(out/'stderr.log'),'terminal':True}
    save(out/'receipt.json',row);calls.append(row)
    assert rc==expected,(label,rc,(out/'stderr.log').read_text(encoding='utf-8'))
    return json.loads((out/'stdout.log').read_text(encoding='utf-8').strip().splitlines()[-1])
start=time.perf_counter()
assert cli('inspect-start',['--mode','inspect'],0)['state']=='idle'
replay=cli('formal-replay',['--mode','replay'],0)
assert replay['status']=='complete'
replay_output=Path(replay['attempt'])/'output'
src=H.parents[1]/'review/initial'
for file in ['independent_checker.py','independent_review.py','independent-source-audit.json']:shutil.copy2(src/file,H/file)
import independent_review as own
numeric=[]
for task in own.tasks:
    result=own.review(replay_output/task,task)
    (H/'numeric').mkdir(exist_ok=True);save(H/'numeric'/f'consumer-{task}.json',result)
    assert result['independent_pass_under_declared_model']
    numeric.append({'task':task,**{k:result[k] for k in ['N','n1','n2','C','Uv','Uw','volume_m3','weight_kg','counts','min_top_gap_cm','pair_count']},'max_pressure_kg_m2':max(x['max_pressure_kg_m2'] for x in result['vehicles'])})
data=json.loads((O/'data/instance.json').read_text(encoding='utf-8'))
small=copy.deepcopy(data)
for c in small['cargo']:c['quantity']=4 if c['cargo_type']=='G1' else 0
small['vehicles'][0].update(l_cm=60,w_cm=40,h_cm=63)
inp=V/'qa/reviewer-small.json';save(inp,small)
small_runs=[]
for i in range(2):
    row=cli(f'small-{i+1}',['--mode','solver','--task','Q1-S1','--input',str(inp)],0)
    output=Path(row['attempt'])/'output';a=own.review(output,'Q1-S1',scenario=True)
    assert a['independent_pass_under_declared_model'] and a['counts']=={'G1':2}
    small_runs.append({'receipt':row,'independent_pass':True,'counts':a['counts'],'placements_sha256':sha(output/'placements.csv')})
assert small_runs[0]['receipt']['attempt']!=small_runs[1]['receipt']['attempt']
assert small_runs[0]['placements_sha256']==small_runs[1]['placements_sha256']
bad=copy.deepcopy(small);bad['cargo'][0]['l_cm']=-1
badfile=V/'qa/reviewer-invalid.json';save(badfile,bad)
negative=cli('invalid-input',['--mode','solver','--task','Q1-S1','--input',str(badfile)],2)
assert negative['status']=='failed' and negative['returncode']==2
sys.path.insert(0,str(V/'src'))
from receipts import Registry,Busy
r=Registry();assert r.inspect()['state']=='idle'
probes=[];checks={}
pid=r.start([sys.executable,'-X','utf8','-B','-c',"import time;print('reviewer live',flush=True);time.sleep(.35)"],'reviewer-active')
other=Registry();checks['same_pid_and_creation_time_live_block']=other.inspect()['state']=='live_block'
try:other.start([sys.executable,'-c',"print('must not start')"],'reviewer-forbidden')
except Busy:checks['live_successor_blocked']=True
else:checks['live_successor_blocked']=False
probes.append(r.finish(pid));assert other.inspect()['state']=='idle'
for label,code,limit,expected in [('reviewer-exit7',"import sys;print('reviewer exit7',flush=True);sys.exit(7)",120,'failed'),('reviewer-timeout',"import time;print('reviewer before timeout',flush=True);time.sleep(3)",.15,'timed_out')]:
    pid=r.start([sys.executable,'-X','utf8','-B','-c',code],label,limit)
    row=r.finish(pid);probes.append(row);assert row['status']==expected
checks['exit7_and_timeout_retained']=probes[-2]['returncode']==7 and 'reviewer before timeout' in Path(probes[-1]['stdout_path']).read_text(encoding='utf-8')
try:r.start([str(V/'qa/reviewer-nonexistent-executable.exe')],'reviewer-missing-program')
except FileNotFoundError:checks['launch_failure_recorded']=True
else:checks['launch_failure_recorded']=False
checks['final_idle_and_guard_released']=r.inspect()['state']=='idle' and not r.children and not r.guard.exists()
checks['all_streams_exist_and_distinct']=len({x['stdout_path'] for x in probes})==len(probes) and all(Path(x['stdout_path']).is_file() and Path(x['stderr_path']).is_file() for x in probes)
assert all(checks.values()),checks
assert cli('inspect-end',['--mode','inspect'],0)['state']=='idle'
save(H/'consumer-run.json',{'calls':calls,'formal_replay':replay,'formal_independent_numeric':numeric,'small_runs':small_runs,'negative':negative,'registry_probes':probes,'checks':checks,'elapsed_seconds':time.perf_counter()-start,'own_checker_source_sha256':sha(H/'independent_checker.py'),'historical_lost_evidence_recovered':False,'genuine_monitor_crash_terminal_reconciliation_tested':False,'pending_calls':[],'active_self_started_processes':[]})
print(json.dumps({'formal_tasks':len(numeric),'formal_pairs':sum(x['pair_count'] for x in numeric),'small_runs':len(small_runs),'checks':checks,'elapsed_seconds':time.perf_counter()-start}))
