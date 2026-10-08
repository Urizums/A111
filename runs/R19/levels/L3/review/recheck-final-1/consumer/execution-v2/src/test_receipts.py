"""Actual prospective behavior checks, not reconstruction of old history."""
import sys,json,copy
from receipts import Registry,Busy,V2,OLD,save,sha
def main():
    registry=Registry();rows=[];checks={}
    assert registry.inspect()['state']=='idle'
    pid=registry.start([sys.executable,'-X','utf8','-B','-c',"import time; print('active-probe',flush=True); time.sleep(.4)"],'active-probe')
    restored=Registry();checks['fresh_monitor_same_process_identity_and_blocks']=restored.inspect()['state']=='live_block'
    try:restored.start([sys.executable,'-c',"print('must-not-launch')"],'forbidden-successor')
    except Busy:checks['successor_blocked_without_new_pid']=True
    else:raise AssertionError('Successor was incorrectly launched')
    rows.append(registry.finish(pid));assert rows[-1]['status']=='complete'
    assert restored.inspect()['state']=='idle'
    for label,code,limit in [('nonzero-probe',"import sys; print('expected exit7',flush=True); sys.exit(7)",120),('timeout-probe',"import time; print('before timeout',flush=True); time.sleep(3)",.15)]:
        pid=registry.start([sys.executable,'-X','utf8','-B','-c',code],label,limit);rows.append(registry.finish(pid))
    checks['nonzero_preserved']=rows[-2]['status']=='failed' and rows[-2]['returncode']==7
    checks['timeout_reaped_and_retained']=rows[-1]['status']=='timed_out' and 'before timeout' in (Path(rows[-1]['stdout_path'])).read_text(encoding='utf-8')
    data=copy.deepcopy(json.loads((OLD/'data/instance.json').read_text(encoding='utf-8')))
    for c in data['cargo']:c['quantity']=4 if c['cargo_type']=='G1' else 0
    data['vehicles'][0].update(l_cm=60,w_cm=40,h_cm=63)
    inp=V2/'qa/receipt_small_instance.json';save(inp,data);coords=[]
    for i in range(2):
        pid=registry.start([sys.executable,'-X','utf8','-B',str(OLD/'src/solver.py'),'--task','Q1-S1','--input',str(inp),'--out','{ATTEMPT}/output'],f'small-solver-{i+1}')
        row=registry.finish(pid);rows.append(row);assert row['status']=='complete';out=Path(row['attempt'])/'output'
        pid=registry.start([sys.executable,'-X','utf8','-B',str(OLD/'src/checker.py'),str(out)],f'small-checker-{i+1}');vr=registry.finish(pid);rows.append(vr);assert vr['status']=='complete'
        m=json.loads((out/'metrics.json').read_text(encoding='utf-8'));assert m['loaded_counts']=={'G1':2}
        coords.append(sha(out/'placements.csv'))
    checks['two_actual_original_CLI_smokes_distinct_outputs_identical_coordinates']=coords[0]==coords[1]
    checks['all_seven_stdout_stderr_unique_retained']=len({r['stdout_path'] for r in rows})==7 and all(Path(r['stdout_path']).exists() and Path(r['stderr_path']).exists() for r in rows)
    checks['registry_terminal_no_unreaped_own_child']=registry.inspect()['state']=='idle' and not registry.children and not registry.guard.exists()
    assert all(checks.values()),checks
    save(V2/'qa/prospective_receipt_checks.json',{'producer_self_check':True,'checks':checks,'actual_child_receipts':rows,'actual_children':7,'new_numerical_solver_calls':2,'main_formal_solves':0,'small_instance_only':True,'old_three_PID_stdout_recovered':False,'historical_parallel_deviations_reclassified':False,'scope_limit':'Restored active monitor was actually tested while original parent still had the child handle. A genuinely crashed monitor with an already exited child has null return code by design; that branch is not experimentally claimed.'})
    print(json.dumps({'passed':all(checks.values()),'actual_children':7,'small_numerical_smokes':2,'main_solves':0,'registry':'idle'}))
if __name__=='__main__':
    from pathlib import Path
    main()
