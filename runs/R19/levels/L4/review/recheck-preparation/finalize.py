from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
OUT=Path(__file__).resolve().parent;ROOT=Path(__file__).resolve().parents[6]
def identity(p):return {'path':p.relative_to(ROOT).as_posix(),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    lockpath=ROOT/'runs/R19/levels/L4/review/initial-lock.json';lock=json.loads(lockpath.read_text(encoding='utf-8-sig'))
    matches=[all(identity(ROOT/f['path'])[k]==v for k,v in f.items()) for f in lock['files']];assert all(matches)
    old=json.loads((ROOT/'runs/R19/levels/L4/review/initial/result.json').read_text(encoding='utf-8'))
    now=datetime.now(timezone.utc).isoformat()
    result={'task_id':'R19-C11-L4-informed-recheck-preparation','actor':'/root/r19_l4_reviewer','status':'recheck_preparation_complete_frozen',
      'frozen_at':now,'review_type':'informed_recheck_preparation','new_production_read':False,'new_production_received':False,
      'new_version_judgment':None,'new_version_a1_a6':None,'new_version_quality_diagnosis':None,
      'prior_first_review':{'lock':identity(lockpath),'file_count':len(matches),'all_bytes_match':True,'status':old['status'],
         'a1_a6':[{ 'id':a['id'],'status':a['status'] } for a in old['a1_a6']], 'unchanged':True},
      'method':'runs/R19/levels/L4/review/recheck-preparation/method.md',
      'affected_scope':['finite-value rejection','physical/declared value-range rejection','paired valid controls','meaningful cannot-fit rejection',
         'new runnable program archive reception','new critical full scenarios independent recomputation','result-to-scientific-paper consistency'],
      'reuse_policy':'specific old evidence only with actual unchanged identity and dependency scope; old pass never auto-passes new output; no mandatory replay of unchanged historical research',
      'known_counterexample':'runs/R19/levels/L4/review/initial/NaN_coordinate.csv',
      'controls_run_on_new_version':0,'production_checks_performed':False,
      'boundaries':{'write':'runs/R19/levels/L4/review/recheck-preparation/','active_execution_v2_read':False,
         'initial_or_preparation_modified':False,'other_levels_or_root_synthesis_read':False},
      'resources':{'provider':None,'model':None,'tokens':None,'cost':None,'overall_elapsed_seconds':None,
         'network_searches':0,'installs':0,'subagents':0,'generic_two_error_stop':False,'whole_task_short_deadline':None},
      'actual_events':[{'event':'initial-lock source recheck','files':164,'all_match':True,'tool_command_exit_code':0}],
      'termination':{'background_processes_started':0,'pending_tool_sessions':[],'all_prior_commands_returned':True,'finalizer_exit0_receipt_required':True,'stop_writing_after_manifest':True},
      'next_action':'Wait for root new production-lock authorization; formal informed review writes only review/recheck-1/.'}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    files=[identity(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p!=OUT/'manifest.json']
    m={'schema':'informed-recheck-preparation-manifest/1','task_id':result['task_id'],'status':'frozen','frozen_at':now,'files':files,'self_excluded':True,
       'claim':'preparation byte identity; no new production judgment'}
    (OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(identity(ROOT/f['path'])==f for f in files)
    print(json.dumps({'status':result['status'],'manifest_files':len(files),'manifest':identity(OUT/'manifest.json'),'new_version_judgment':None,'pending_tool_sessions':[]},ensure_ascii=False))
if __name__=='__main__':main()
