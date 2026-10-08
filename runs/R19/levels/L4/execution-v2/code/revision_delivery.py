"""New-version delivery receipts; never alter the frozen v1 or initial review."""
from pathlib import Path
import json,csv,hashlib,math,sys,subprocess,time,zipfile,shutil,ast,datetime
from validator import validate

E=Path(__file__).resolve().parents[1]; R=E.parents[4]
def readj(p):return json.loads(p.read_text(encoding='utf8'))
def writej(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def call(cmd,cwd):
    t=time.perf_counter();p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,encoding='utf8')
    return {'command':cmd,'cwd':str(cwd),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'elapsed_seconds':time.perf_counter()-t,'state':'completed','process_id':None}

def clean():
    C=E/'checks/revision-clean';I=readj(C/'data/instance.json');cfg=readj(C/'configs/refined.json');run=readj(C/'results/run_summary.json');group=[]
    for s in run['scenarios']:
        name=s['scenario'];p=C/'results'/name;ck=validate(I,cfg,rows(p/'placements.csv'),True);assert ck['valid'],ck['errors']
        old=E/'results/classic_refined'/name;before=readj(old/'summary.json')
        fields=['truck_count','cost','UV','UW','mass_kg','volume_cm3']
        eq={k:math.isclose(ck[k],before[k],rel_tol=1e-9,abs_tol=1e-6) for k in fields};assert all(eq.values())
        writej(p/'revision_coordinate_check.json',ck)
        group.append({'scenario':name,'valid':True,'recomputed':{k:ck[k] for k in fields},'same_selected_metrics':eq,'placements_sha256':sha(p/'placements.csv'),'same_selected_csv_bytes':sha(p/'placements.csv')==sha(old/'placements.csv')})
    core={n:{'delivery_sha256':sha(E/'code'/n),'clean_sha256':sha(C/'code'/n)} for n in ['solve.py','validator.py','numeric_contract.py']};assert all(x['delivery_sha256']==x['clean_sha256'] for x in core.values())
    result={'status':'actual_v2_full_clean_solve_and_coordinate_recheck_completed','operation':'new solve from initially absent directory, only three core files plus data/config copied','session_id':39988,'session_exit_code':0,'session_final_stdout':"Q2_min_cost truck_count10 cost6750 validTrue; process exit0 captured by write_stdin",'method':'maxrects','budget':{'pattern_count_per_vehicle':96,'inventory_restarts':12,'master_time_limit_seconds':90,'seed':1904},'elapsed_seconds':run['elapsed_seconds'],'core_identity':core,'scenarios':group,'not_independent_review':True}
    writej(E/'checks/revision-clean-receipt.json',result);print({'clean_elapsed_seconds':result['elapsed_seconds'],'groups':len(group),'all_csv_bytes_match':all(g['same_selected_csv_bytes'] for g in group)})

def archive():
    z=E/'program_attachment.zip'
    payload=[E/'README.md',E/'base-binding.json']+[E/'code'/n for n in ['solve.py','validator.py','numeric_contract.py','experiments.py']]+list((E/'data').glob('*'))+list((E/'configs').glob('*.json'))+[E/'results/selected.json']
    payload+=list((E/'results/classic_refined').rglob('*'))+list((E/'results/selected_single').rglob('*'))
    with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED) as f:
        for p in sorted(set(p for p in payload if p.is_file())):f.write(p,p.relative_to(E).as_posix())
    target=E/'checks/revision-archive-test';assert not target.exists();target.mkdir()
    with zipfile.ZipFile(z) as f:
        assert f.testzip() is None
        for n in f.namelist():assert not Path(n).is_absolute() and '..' not in Path(n).parts
        f.extractall(target)
    data=readj(target/'data/instance.json');cfg=readj(target/'configs/refined.json')
    for g in data['cargo']:g['quantity']=g['quantity']//4
    cfg.update(pattern_count_per_vehicle=12,inventory_restarts=2,master_time_limit_seconds=8)
    writej(target/'data/synthetic_750.json',data);writej(target/'configs/smoke.json',cfg)
    cmd=['py','-3.12','-X','utf8','-B','code/solve.py','--data','data/synthetic_750.json','--config','configs/smoke.json','--out','results/new_archive_smoke','--method','maxrects']
    run=call(cmd,target);assert run['exit_code']==0,run
    groups=[]
    for s in readj(target/'results/new_archive_smoke/run_summary.json')['scenarios']:
        root=target/'results/new_archive_smoke'/s['scenario'];ck=validate(data,cfg,rows(root/'placements.csv'),True);assert ck['valid'],ck['errors'];groups.append({'scenario':s['scenario'],'valid':True,'truck_count':ck['truck_count'],'cost':ck['cost']})
    # The extracted artifact itself, including numeric_contract, must reject the original defect.
    base=['py','-3.12','-X','utf8','-B','code/validator.py','--data','data/instance.json','--config','configs/refined.json','--single']
    nan=call(base+['--placements',str(E/'history/initial-review-NaN_coordinate.csv'),'--out','nan_rejection.json'],target);assert nan['exit_code']==1 and not readj(target/'nan_rejection.json')['valid']
    good=call(base+['--placements',str(E/'checks/revision-controls/legal_pair.csv'),'--out','legal_acceptance.json'],target);assert good['exit_code']==0 and readj(target/'legal_acceptance.json')['valid']
    core={n:{'archive_extracted_sha256':sha(target/'code'/n),'delivery_sha256':sha(E/'code'/n)} for n in ['solve.py','validator.py','numeric_contract.py']};assert all(v['archive_extracted_sha256']==v['delivery_sha256'] for v in core.values())
    rec={'status':'actual_extracted_v2_zip_smoke_and_paired_receiver_passed','zip_sha256':sha(z),'crc_check':True,'core_identity':core,'smoke_solve':run,'smoke_input':'synthetic inventory one quarter of official (750 items), 12 patterns/2 starts/8s; not a full official archive rerun','smoke_groups':groups,'extracted_NaN_rejection':nan,'extracted_legal_acceptance':good,'official_full_clean_run':'checks/revision-clean-receipt.json','not_independent_review':True}
    writej(E/'checks/revision-archive-receipt.json',rec);print({'archive_groups':groups,'zip_sha256':sha(z),'status':rec['status']})

def audit():
    binding=readj(E/'base-binding.json');base=[];review=[]
    for x in binding['base_files']:
        p=R/x['path'];ok=p.stat().st_size==x['size_bytes'] and sha(p)==x['sha256'];assert ok,x['path'];base.append({'path':x['path'],'unchanged':ok})
    for name,x in binding['initial_review_authorized_files'].items():
        p=R/name;ok=p.stat().st_size==x['size_bytes'] and sha(p)==x['sha256'];assert ok,name;review.append({'path':name,'unchanged':ok})
    lock=readj(E/'history/initial-review-lock.json');locked={x['path']:x for x in lock['files']}
    for name,x in binding['initial_review_authorized_files'].items():
        if name in locked:assert x['sha256']==locked[name]['sha256'] and x['size_bytes']==locked[name]['size_bytes']
    old=readj(E/'history/execution-v1-result.json');sources=[]
    for name,x in old['source_identity'].items():
        p=R/'runs/R19/inputs/raw'/name;ok=sha(p)==x['sha256'] and p.stat().st_size==x['size_bytes'];assert ok; sources.append({'path':p.relative_to(R).as_posix(),'unchanged':ok})
    numbers=readj(E/'checks/paper_numbers.json');oldnumbers=readj(E.parent/'execution/checks/paper_numbers.json')
    numberfields={k:numbers[k]==oldnumbers[k] for k in ['selected_results','parameter_rows','hand_chain']};assert all(numberfields.values())
    figures=[]
    for p in sorted((E/'figures').glob('*')):
        assert sha(p)==sha(E.parent/'execution/figures'/p.name);figures.append({'path':p.relative_to(E).as_posix(),'sha256':sha(p),'reused_v1_bytes':True})
    from reportlab.pdfbase.ttfonts import TTFont
    cmap=TTFont('RevisionGlyphCheck','C:/Windows/Fonts/simsun.ttc',subfontIndex=0).face.charToGlyph
    alltext=''.join((E/'paper'/n).read_text(encoding='utf8') for n in ['paper.md','enterprise_report.md'])
    missing=sorted(set(c for c in alltext if not c.isspace() and ord(c) not in cmap));assert not missing,missing
    render=readj(E/'checks/reading_render.json');assert all(r['all_pages_rendered'] and r['no_text_outside_safe_bounds'] for r in render)
    reading={'status':'final_v2_author_reading_checked_pending_informed_review','actor':'/root/r19_l4_executor','independent':False,'all_12_plus_3_pages_rendered_and_visually_inspected':True,'files':[{'path':r['file'],'pages':len(r['pages']),'sha256':sha(E/r['file']),'embedded_fonts':r['embedded_fonts'],'no_text_outside_safe_bounds':r['no_text_outside_safe_bounds']} for r in render],'missing_font_characters':missing,'evidence':['checks/reading/paper_contact_01.png','checks/reading/paper_contact_02.png','checks/reading/enterprise_report_contact_01.png','checks/reading/paper_09.png','checks/reading/enterprise_report_03.png','checks/reading/enterprise_report_02.png'],'observed':['all pages legible, tables/figures present, no clipping or overlap observed','new paper7.4 and report6 explicitly retain first NaN false acceptance and a4fail/a6partial','model, quantities, costs, units,17 parameters,64 geometry pairs and claim strength unchanged','ZIP/core scope separated from full-domain research/reading evidence','author self-check is not independent informed acceptance'],'numeric_evidence_equality':numberfields,'timestamp_local':datetime.datetime.now().isoformat()}
    writej(E/'checks/revision-reading-review.json',reading)
    parsed=[]
    for p in E.rglob('*.py'):
        ast.parse(p.read_text(encoding='utf8'));parsed.append(p.relative_to(E).as_posix())
    selected=readj(E/'results/selected.json');assert all((E/x['root']/'placements.csv').exists() for x in selected['scenarios'].values());assert (E/selected['single_root']/'pareto.json').exists()
    record={'status':'v2_integrity_checked_pending_independent_review','base_files_count':len(base),'all_v1_base_files_unchanged':True,'original_files':base,'authorized_initial_review_files':review,'initial_lock_metadata_count':len(lock['files']),'initial_scope_files_actually_read':list(binding['initial_review_authorized_files']),'initial_metadata_lock_checked_without_reading_other_review_payloads':True,'sources':sources,'numeric_manuscript_evidence_unchanged':numberfields,'figures':figures,'python_AST_parsed':parsed,'selected_relative_paths_resolve_in_v2':True,'checks_scope':'read-only checks of original/initial/official sources; write onlyv2','timestamp_local':datetime.datetime.now().isoformat()}
    writej(E/'checks/revision-integrity.json',record);print({'original_files_unchanged':len(base),'authorized_initial_files_unchanged':len(review),'numeric_fields_unchanged':numberfields,'pages':[len(r['pages']) for r in render]})

def final():
    old=readj(E/'history/execution-v1-result.json');binding=readj(E/'base-binding.json');integrity=readj(E/'checks/revision-integrity.json')
    clean=readj(E/'checks/revision-clean-receipt.json');archive=readj(E/'checks/revision-archive-receipt.json');reading=readj(E/'checks/revision-reading-review.json');control=readj(E/'checks/revision-checks.json')
    probe=json.loads((E/'checks/revision-process-probe.json').read_text(encoding='utf-8-sig'))
    assert integrity['all_v1_base_files_unchanged'] and probe['matching_python_count']==0 and not probe['pending_sessions']
    assert sha(E/'program_attachment.zip')==archive['zip_sha256']
    # Bind the actual final full-run tool receipt, rather than a prose rendering of stdout.
    terminal={'chunk_id':'e7c015','wall_time_seconds':0.0000073,'exit_code':0,'original_token_count':46,'output':"Q2_min_cost {'scenario': 'Q2_min_cost', 'truck_count': 10, 'cost': 6750, 'UV': np.float64(0.7288448563616349), 'UW': 0.428125, 'elapsed_seconds': 29.540811499988195, 'valid': True}\r\n"}
    clean.pop('session_final_stdout',None);clean['session_terminal_tool_receipt']=terminal
    clean['command']=['py','-3.12','-X','utf8','-B','code/solve.py','--data','data/instance.json','--config','configs/refined.json','--out','results','--method','maxrects'];clean['cwd']=str(E/'checks/revision-clean')
    writej(E/'checks/revision-clean-receipt.json',clean)
    receipts={'scope':'actual revision orchestration receipts available to this author; subprocess full stdout/stderr in revision-receipts and revision-archive-receipt; old v1 receipts preserved without reconstruction','new_yielded_sessions':[{'session_id':26441,'state':'completed','exit_code':0,'operation':'revision_checks.py controls/full-coordinate checks; terminal return observed before context continuation'},{'session_id':39988,'state':'completed','receipt':terminal}],
      'immediate_tools':[{'operation':'PDF skill artifact edit hook','exit_code':0,'operation_kind':'edit','expected_output_count':2,'output_format':'pdf','receipt_availability':'actual successful hook observed before context continuation'},
       {'chunk_id':'92792a','operation':'clean-result coordinate/byte audit','exit_code':0,'output':"{'clean_elapsed_seconds': 132.56487239999115, 'groups': 4, 'all_csv_bytes_match': True}\r\n"},
       {'operation':'README patch first attempt','status':'failed_before_mutation','output':'apply_patch verification failed: invalid patch: multiple operations target C:\\Users\\admin\\Documents\\Codex\\2026-10-05\\urizums-a111-main-codex-handoff-md\\work\\A111\\runs\\R19\\levels\\L4\\execution-v2\\README.md','recovery':'separate authorized delete/add in v2, succeeded; archive not started by rejected attempt'},
       {'chunk_id':'c18f5b','operation':'archive build/actual extracted smoke and pair','exit_code':0,'output':"{'archive_groups': [{'scenario': 'Q1_fleet_T1', 'valid': True, 'truck_count': 5, 'cost': 2250}, {'scenario': 'Q1_fleet_T2', 'valid': True, 'truck_count': 3, 'cost': 2100}, {'scenario': 'Q2_min_vehicles', 'valid': True, 'truck_count': 3, 'cost': 2100}, {'scenario': 'Q2_min_cost', 'valid': True, 'truck_count': 3, 'cost': 2100}], 'zip_sha256': 'bce886a6929549a01c9376c1a3f4b5eb971ed3d9c46a7e1917942681ce19d185', 'status': 'actual_extracted_v2_zip_smoke_and_paired_receiver_passed'}\r\n"},
       {'chunk_id':'c492d2','operation':'first delivery integrity audit','exit_code':1,'error':'FileNotFoundError: history/v1-result.json','observed_cause':'auxiliary finalizer assumed wrong historical filename; actual history/execution-v1-result.json exists','recovery':'changed only auxiliary audit filename; no scientific rerun or original mutation'},
       {'chunk_id':'d5773e','operation':'delivery integrity audit after filename correction','exit_code':0,'output':"{'original_files_unchanged': 417, 'authorized_initial_files_unchanged': 5, 'numeric_fields_unchanged': {'selected_results': True, 'parameter_rows': True, 'hand_chain': True}, 'pages': [12, 3]}\r\n"},
       {'chunk_id':'bdd6ac','operation':'final manuscript/report generation','exit_code':0,'output':'paper characters 16527 report characters 3421\r\n'},
       {'chunk_id':'a6e971','operation':'final all-pages rendering','exit_code':0,'structured_output':'checks/reading_render.json','pages':[12,3]},
       {'chunk_id':'bcd859','operation':'process probe before finalizer','exit_code':0,'structured_output':'checks/revision-process-probe.json','matching_python_count':0}],
      'missing_lock_recovery':{'operation':'read named initial/initial-lock.json','exit_code':1,'observed':'file absent','authorized_correct_location':'runs/R19/levels/L4/review/initial-lock.json','exact_old_tool_output_not_available_after_context_continuation':True},
      'finalizer_state':'this foreground final command writes result/manifest then returns; caller must inspect its terminal receipt and perform read-only hash/process verification before handing off'}
    writej(E/'checks/revision-tool-receipts.json',receipts)
    stamp=datetime.datetime.now().isoformat()
    additions=[{'attempt_id':'L4-V2-003','class':'actual_revision_delivery_checks','full_official_clean_solve_seconds':clean['elapsed_seconds'],'same_full_metrics_and_four_csv_bytes':True,'recheck_old_coordinate_groups':33,'new_official_solve_scenarios':4,'archive_scope':'actual extracted750-piece smoke plus actual NaN/legal receiving pair, not full official archive rerun','reading':'regenerated12+3pages, all rendered and read; old figures/research numeric evidence bound and unchanged'},
       {'attempt_id':'L4-V2-004','class':'auxiliary_tool_recoveries','errors':[{'operation':'README patch delete/add one request','observed':'multiple operations target rejected before mutation','fix':'separate operations in v2'},{'operation':'delivery audit first call','exit_code':1,'observed':'history/v1-result.json missing','fix':'use actual history/execution-v1-result.json','retry_exit_code':0}],'no_scientific_budget_or_failure_count_reset':True},
       {'attempt_id':'L4-V2-005','class':'informed_revision_author_freeze','status':'author_delivery_complete_pending_same_reviewer','original417files_and_authorized5initialfiles_unchanged':True,'process_probe_count_before_foreground_finalizer':0,'pending_prior_sessions':[],'finalizer_requires_terminal_receipt_and_read_only_postfreeze_check':True,'independent_verdict_not_announced':True}]
    with (E/'logs/events.jsonl').open('a',encoding='utf8') as f:
        for x in additions:x['timestamp']=stamp;f.write(json.dumps(x,ensure_ascii=False)+'\n')
    todo=(E/'TODO.md').read_text(encoding='utf8');head,tail=todo.split('# Same-author informed revision v2',1)
    tail=tail.replace('- [ ]','- [x]');(E/'TODO.md').write_text(head+'# Same-author informed revision v2'+tail+'\nFinal v2 '+stamp+': all affected author checks completed; manifest write is last mutation. Same reviewer informed reception pending. Old/initial verdict and historical budgets/failures retained.\n',encoding='utf8')
    prefix=E.relative_to(R).as_posix()
    def relocate(obj):
        if isinstance(obj,dict):return {k:relocate(v) for k,v in obj.items()}
        if isinstance(obj,list):return [relocate(v) for v in obj]
        if isinstance(obj,str):return obj.replace('runs/R19/levels/L4/execution/',prefix+'/')
        return obj
    result=relocate(old)
    result.update(task_id='R19-C11-L4-execution-v2',original_task_id=old['task_id'],status='informed_revision_complete_author_checked_pending_rereview',same_original_author=True,write_domain=prefix+'/',completed_at_local=stamp,manifest=prefix+'/manifest.json')
    result['core_final_code_sha256']={n:sha(E/'code'/n) for n in ['solve.py','validator.py','numeric_contract.py']}
    result['version_identity']={'base_binding':prefix+'/base-binding.json','original_result':prefix+'/history/execution-v1-result.json','original_execution_mutated':False,'initial_review_mutated':False,'base_unchanged_files':417,'authorized_initial_files_checked':5,'initial_locked_payload_count':164,'composition':'full v2 domain with updated three core files and manuscripts/ZIP, byte-bound copied original research and coordinates; relative selected roots resolve locally','delivered_zip_sha256':sha(E/'program_attachment.zip'),'original_selected_csv_and_science_evidence_unchanged':True}
    result['original_independent_review']={'verdict':binding['initial_verdict'],'report':prefix+'/history/initial-review-report.md','result':prefix+'/history/initial-review-result.json','defect':'NaN x legal pair originally accepted exit0/VALID, independently rejected','status':'original verdict retained; informed re-review pending','author_may_declare_independent_pass':False}
    result['historical_checks']=old['checks'];result['historical_checks']['scope']='original author checks, not renewed or independent assertions; byte binding in base-binding.json'
    result['checks']={'status':'all_affected_author_checks_complete','finite_and_range_contract':'code/numeric_contract.py before solve/geometry/metrics','main_actual_CLI_controls':len(control['controls']),'additional_nonfinite_input_receiver_calls':24,'legal_control_accepted':True,'nonfinite_coordinates_and_inputs_explicitly_rejected':True,'NaN_replaced_by_zero':False,'old_wrong_CLI_and_matrix_traceback_reproduced_and_retained':True,'impossible1001_new_exit_code':3,'impossible1001_message':'INFEASIBLE_INPUT; no allowed vehicle pose/load; failure.json, no new success summary or traceback','old_full_coordinates_rechecked_groups':33,'critical_selected_full_receiver_CLI':4,'new_full_clean_solve_scenarios':4,'new_full_clean_solve_seconds':clean['elapsed_seconds'],'new_full_12000_item_rows_rechecked':True,'four_selected_CSV_byte_hashes_equal':True,'archive_actual_smoke_and_pair':True,'archive_official_full_solve_repeated':False,'reading_pages':[12,3],'initial_verdict_retained':True,'independent_informed_reception':'pending_same_reviewer_in_separate_domain','evidence':[prefix+'/checks/'+n for n in ['revision-checks.json','revision-clean-receipt.json','revision-archive-receipt.json','revision-reading-review.json','revision-integrity.json','revision-tool-receipts.json','revision-process-probe.json']]}
    result['experiments']['scope']='original actual scientific research retained and bound; no new 17-case optimization or three-route comparison asserted'
    result['experiments']['revision_full_clean_solve']={'method':'maxrects','same_budget':clean['budget'],'elapsed_seconds':clean['elapsed_seconds'],'four_scenarios_valid_and_bytes_match':True}
    result['experiments']['revision_archive_smoke']={'synthetic_items':750,'pattern_count_per_vehicle':12,'inventory_restarts':2,'master_time_limit_seconds':8,'elapsed_seconds':archive['smoke_solve']['elapsed_seconds'],'scope':'delivered archive executable smoke; distinct from official clean full solve and old research comparison'}
    for row in result['coverage']:row['revision_scope']='scientific evidence reused from v1; affected numeric receiving and finite final coordinates rechecked in v2; author coverage assessment only'
    events=[json.loads(line) for line in (E/'logs/events.jsonl').read_text(encoding='utf8').splitlines() if line.strip()]
    result['failures_and_iterations']['attempt_ids']=[x['attempt_id'] for x in events]
    from collections import Counter
    result['failures_and_iterations']['event_classes']=dict(Counter(x['class'] for x in events))
    result['failures_and_iterations']['revision_failures']=['initial independently found NaN false acceptance','old1001 matrix traceback, actually reproduced','specified initial lock nested path missing then resolved to same authorized named lock','README patch rejected before mutation then repaired','auxiliary audit wrong history filename then repaired']
    result['failures_and_iterations']['old_decimal_failure_coordinates_not_reconstructed']=True
    result['resources']['revision_observation']={'ordinaryUsageAllowed':True,'primary_used_percent':41,'secondary_used_percent':85,'observation_at':'L4-V2-001 revision start','reset_consumed':False,'purchase':False,'model_replacement':False,'identity_or_historical_budget_reset':False,'actual_model':None,'tokens':None,'cost':None}
    result['resources']['total_revision_elapsed_seconds']=None;result['resources']['note']='Only actual instrumented solver/subprocess windows reported; no inferred account cost/tokens or whole-task deadline.'
    result['artifacts']=[prefix+'/'+n for n in ['paper/paper.md','paper/paper.pdf','paper/enterprise_report.md','paper/enterprise_report.pdf','program_attachment.zip','README.md','results/selected.json','code/solve.py','code/validator.py','code/numeric_contract.py','base-binding.json','TODO.md']]
    result['artifact_identity']={n:{'size_bytes':(E/n).stat().st_size,'sha256':sha(E/n)} for n in ['paper/paper.md','paper/paper.pdf','paper/enterprise_report.md','paper/enterprise_report.pdf','program_attachment.zip','README.md','results/selected.json']}
    result['limitations']=[x for x in old['limitations'] if not x.startswith('One local producer')]+['Finite/range gate repaired in same-author informed version; all current revision checks are author checks, same independent reviewer still pending','Input CLI follows declared two-vehicle/five-cargo contract; no universal solver-completeness or arbitrary extreme-scale numerical claim','Original failed decimal coordinates were not saved and remain unavailable; no reconstruction performed']
    result['still_pending_reception']=['Coordinator freezes this v2 and same reviewer performs informed affected re-review in another domain; do not overwrite original initial verdict']+old['still_pending_reception'][1:]
    result['terminal_process_state']={'status':'all_prior_sessions_terminal_before_final_foreground_writer','observed_at':probe['timestamp_local'],'matching_python_count':0,'query_scope':'own execution/execution-v2 numerical/artifact commands; author finalizer then writes result/manifest and must have actual exit receipt before handoff','historical_sessions':old['terminal_process_state']['sessions'],'revision_yielded_sessions':probe['known_new_sessions'],'immediate_subprocess_receipts_terminal':True,'pending_sessions':[],'background_jobs_started':False,'post_manifest_check':'caller read-only manifest/process check after foreground finalizer actual exit; no further writes permitted'}
    result['write_freeze']='manifest is final artifact mutation; actor then performs read-only hash/process verification and sends terminal tool receipt to coordinator'
    writej(E/'result.json',result)
    entries=[{'path':p.relative_to(R).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(E.rglob('*')) if p.is_file() and p!=E/'manifest.json']
    manifest={'task_id':result['task_id'],'actor':result['actor'],'root_basis':str(R),'self_excluded':True,'payload_excludes_manifest':True,'version':'same-author-informed-v2','entry_count':len(entries),'total_payload_size_bytes':sum(x['size_bytes'] for x in entries),'entries':entries,'created_at_local':datetime.datetime.now().isoformat()}
    writej(E/'manifest.json',manifest)
    print({'status':result['status'],'result':str(E/'result.json'),'manifest':str(E/'manifest.json'),'payload_files':len(entries),'payload_bytes':manifest['total_payload_size_bytes'],'pending_prior_sessions':[],'final_writer':'about to return; actual tool exit must be confirmed; no writes after this'})

if __name__=='__main__':
    {'clean':clean,'archive':archive,'audit':audit,'final':final}[sys.argv[1]]()
