from pathlib import Path
import json,hashlib,copy,subprocess,time
from coordinate_review import check,BASE
OUT=Path(__file__).resolve().parent;ROOT=Path(__file__).resolve().parents[6];E=ROOT/'runs/R19/levels/L4/execution';C=OUT/'consumer'
def main():
    out={'fresh_main':[],'changed_input':[],'reproduced_parameters':[],
         'receipt_recovery':{'original_secondary_wrapper_exit_code':1,'actual_error':'TypeError: Object of type int64 is not JSON serializable at final receipt save',
          'effect':'numerical files already saved; in-memory subprocess stdout/exit codes/timing were not serialized and cannot be retroactively recovered',
          'original_secondary_cli_exact_exit_codes':None,'original_secondary_cli_exact_elapsed_seconds':None,
          'recovery':'read and independently verify existing saved artifacts; no rerun to fake original receipt; corrected serializer applies prospectively'}}
    for p in sorted((C/'reviewer_new_run').glob('Q*_*/summary.json')):
        single='single' in p.parent.name;r=check(p.parent,single=single);out['fresh_main'].append(r)
        if not single:
            old=E/'results/classic_refined'/p.parent.name/'placements.csv';new=p.parent/'placements.csv'
            r['original_csv_hash']=hashlib.sha256(old.read_bytes()).hexdigest();r['rerun_csv_hash']=hashlib.sha256(new.read_bytes()).hexdigest()
            r['byte_equal']=r['original_csv_hash']==r['rerun_csv_hash']
    variant=json.loads((C/'data/reviewer_variant750.json').read_text(encoding='utf-8'))
    for p in sorted((C/'reviewer_variant750').glob('Q*_*/summary.json')):
        r=check(p.parent,variant,single='single' in p.parent.name);out['changed_input'].append(r)
    for p in sorted((OUT/'reproduced_parameters').glob('*/summary.json')):
        r=check(p.parent);out['reproduced_parameters'].append(r)
    # A new impossible single-type case is a distinct failure test, not recreation of lost receipt.
    impossible=copy.deepcopy(BASE);impossible['cargo']=[impossible['cargo'][0]]
    impossible['cargo'][0]['dims']=[1001,1001,1001];impossible['cargo'][0]['quantity']=1
    target=C/'data/reviewer_impossible_single.json';target.write_text(json.dumps(impossible,ensure_ascii=False,indent=2),encoding='utf-8')
    args=['py','-3.12','-X','utf8','-B','code/solve.py','--data',str(target),'--config','configs/experiments.json','--out','reviewer_impossible_single','--method','maxrects']
    start=time.perf_counter();p=subprocess.run(args,cwd=C,capture_output=True,text=True,encoding='utf-8')
    out['new_failure_control']={'command':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'elapsed_seconds':time.perf_counter()-start,
       'no_success_summary':not (C/'reviewer_impossible_single'/'run_summary.json').exists(),
       'interpretation':'actual nonzero ValueError rejection; failure is explicit but CLI is traceback rather than structured explanation'}
    allchecks=out['fresh_main']+out['changed_input']+out['reproduced_parameters']
    out['all_saved_numerical_outputs_independently_valid']=all(r['valid'] and r['all_summary_metrics_match'] for r in allchecks)
    (OUT/'rerun-independent-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'main_scenarios':len(out['fresh_main']),'changed_scenarios':len(out['changed_input']),
                     'parameters':[(r['path'],r['metrics']) for r in out['reproduced_parameters']],
                     'all_valid':out['all_saved_numerical_outputs_independently_valid'],'failure_control':out['new_failure_control']},ensure_ascii=False))
if __name__=='__main__':main()
