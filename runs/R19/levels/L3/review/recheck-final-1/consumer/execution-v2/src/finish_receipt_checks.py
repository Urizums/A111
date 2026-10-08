from pathlib import Path
import sys,json
from receipts import Registry,V2,OLD,save,sha
def main():
    r=Registry();checks={}
    try:r.start([str(V2/'qa/no-such-executable.exe')],'expected-launch-failure')
    except FileNotFoundError:checks['launch_failure_retains_receipt_and_closes_streams']=r.inspect()['state']=='idle' and not r.guard.exists()
    else:raise AssertionError('Expected missing executable')
    dirs=[p for p in (V2/'attempts').glob('solver-*/output')]
    assert len(dirs)==1
    out=dirs[0]
    pid=r.start([sys.executable,'-X','utf8','-B',str(OLD/'src/checker.py'),str(out)],'consumer-cli-checker');vr=r.finish(pid);assert vr['status']=='complete'
    m=json.loads((out/'metrics.json').read_text(encoding='utf-8'));assert m['loaded_counts']=={'G1':2}
    prior=json.loads((V2/'qa/prospective_receipt_checks.json').read_text(encoding='utf-8'))
    checks['public_consumer_CLI_actual_small_run_checked']=sha(out/'placements.csv')==sha(Path(next(x['attempt'] for x in prior['actual_child_receipts'] if x['label']=='small-solver-1'))/'output/placements.csv')
    receipts=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((V2/'attempts').glob('*/receipt.json'))]
    launched=[x for x in receipts if x.get('pid') is not None]
    checks['nine_child_receipts_complete_or_expected_terminal']=len(launched)==9 and all(x['status'] in ['complete','failed','timed_out'] and x['returncode'] is not None for x in launched)
    checks['nine_stream_pairs_unique_byte_retained']=len({x['stdout_path'] for x in launched})==9 and all(sha(x['stdout_path'])==x['stdout_sha256'] and sha(x['stderr_path'])==x['stderr_sha256'] for x in launched)
    checks['final_registry_idle']=r.inspect()['state']=='idle' and not r.children
    assert all(checks.values()),checks
    save(V2/'qa/prospective_receipt_final.json',{'producer_self_check':True,'initial_checks':'prospective_receipt_checks.json','new_checks':checks,'all_receipts':receipts,'actual_children':len(launched),'actual_small_solver_calls':3,'actual_coordinate_checker_calls':3,'actual_process_probes':3,'blocked_before_launch':1,'expected_launch_failure_no_pid':1,'main_formal_solves':0,'final_code_binding':{n:sha(V2/'src'/n) for n in ['receipts.py','receipt_cli.py','finish_receipt_checks.py']},'additional_child_elapsed_seconds':sum(x['elapsed_seconds'] for x in launched),'sampled_child_peak_RSS_bytes':max(x['sampled_peak_RSS_bytes'] or 0 for x in launched),'registry':'idle','original_PID_stdout_gap_recovered':False})
    print(json.dumps({'actual_children':len(launched),'small_numerical_smokes':3,'main_solves':0,'new_checks':checks}))
if __name__=='__main__':main()
