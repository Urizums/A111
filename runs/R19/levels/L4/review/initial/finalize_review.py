from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
OUT=Path(__file__).resolve().parent;ROOT=Path(__file__).resolve().parents[6]
def ident(p):return {'path':p.relative_to(ROOT).as_posix(),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    integrity=[]
    for loc in ['runs/R19/levels/L4/execution-lock.json','runs/R19/levels/L4/review/preparation-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/evaluation-lock.json','runs/R19/levels/L4/design-lock.json']:
        lock=json.loads((ROOT/loc).read_text(encoding='utf-8-sig'))
        match=all(all(ident(ROOT/f['path'])[k]==v for k,v in f.items()) for f in lock['files'])
        assert match,loc
        integrity.append({'lock':loc,'files':len(lock['files']),'all_match':match})
    coords=json.loads((OUT/'coordinate-review.json').read_text(encoding='utf-8'));trace=json.loads((OUT/'numerical-trace.json').read_text(encoding='utf-8'))
    rerun=json.loads((OUT/'rerun-independent-review.json').read_text(encoding='utf-8'));receipt=json.loads((OUT/'clean-rerun-receipt.json').read_text(encoding='utf-8'))
    assert coords['all_valid'] and coords['all_summary_metrics_match'] and trace['all_geometry_match'] and trace['all_paper_numeric_rows_match'] and rerun['all_saved_numerical_outputs_independently_valid']
    assert receipt['exit_code']==0
    evidence=lambda *names:['runs/R19/levels/L4/review/initial/'+n for n in names]
    a=[
      {'id':'a1','status':'pass','evidence':evidence('source-contract.json','coordinate-review.json','numerical-trace.json','report.md'),
       'reason':'Every original question, item-coordinate delivery, enterprise report/program, bounded Attachment2 treatment actually covered; independent original goals recomputed.',
       'limitations':['feasible upper bounds under declared single-full-support/one-two segment assumptions; global optimum and complete true frontier unknown']},
      {'id':'a2','status':'pass','evidence':evidence('source-audit.json','source-contract.json','coordinate-review.json','numerical-trace.json','report.md'),
       'reason':'Original fields/units, shared feasibility, cumulative/contact load, density upper bound and valid relaxations independently checked; formal and parameter comparison budgets separate and mechanism explained.',
       'limitations':['uniform static center, conservative support/fragile rotation/pressure-area interpretations disclosed','not a physical transport certification']},
      {'id':'a3','status':'pass','evidence':evidence('receiving-summary.json','clean-rerun-receipt.json','rerun-independent-review.json','rerun-semantic-coordinates.json','numerical-trace.json'),
       'reason':'Extracted program actually reran on direct-original reconstructed input; final goals and normalized complete coordinates reproduced and independently checked; paper/result trace verified.',
       'limitations':['numeric-equivalent float source reconstruction changes CSV bytes; normalized row semantics equal','historical wall time not a reproducible constant; lost supplemental subprocess telemetry remains unknown']},
      {'id':'a4','status':'fail','evidence':evidence('defect-controls.json','NaN_coordinate.csv','NaN_coordinate-author-check.json','coordinate-review.json','rerun-independent-review.json'),
       'reason':'Author receiver actually emits exit0/VALID for NaN x coordinate from otherwise legal single-item source-bound row; independent frozen checker rejects invalid_numeric. Non-real coordinate cannot satisfy original concrete placement/geometry, so the numerical failure receiving guarantee is false despite other substantive experiments.',
       'limitations':['all finite original/fresh final coordinates independently feasible; this is validator failure coverage, not proven invalidity of current final numerical solutions'],
       'next_action':'Reject nonfinite/range-invalid numeric fields before all geometry and summary; retain original verdict/counterexample and independently rerun valid paired control, NaN/Inf and key complete cases on new frozen version.'},
      {'id':'a5','status':'pass','evidence':evidence('reading-extract.json','numerical-trace.json','report.md'),
       'reason':'Actually read both Chinese manuscripts in full and all12+3 PDF pages; scientific problem-model-method-result-validation-interpretation argument complete, numerical main tables and figure sources consistent and conclusions bounded.',
       'limitations':['minor orphan subsection title/linear equation formatting optional; finite candidate limits explicitly stated']},
      {'id':'a6','status':'partial','evidence':evidence('receiving-identities.json','receiving-summary.json','clean-rerun-receipt.json','rerun-independent-review.json','defect-controls.json','report.md')+['runs/R19/levels/L4/execution/logs/events.jsonl','runs/R19/levels/L4/resource-resume-observation.json'],
       'reason':'A new consumer independently used design/program with no designer intervention, full versus smoke duties separate and actor/failures/resume preserved; the receiver still wrongly releases nonfinite coordinates as VALID.',
       'limitations':['actual decimal failing coordinates were not originally saved but exact old error/input/correction disclosed','impossible new input rejects via raw traceback rather than clear infeasibility receipt'],
       'next_action':'Repair finite numeric receiving branch and provide meaningful infeasibility message without weakening original constraints; informed re-review after new production freeze.'}
    ]
    dims=[
      ('problem fidelity','achieved','All original goals, coordinates, report/program and Attachment2 missing fields addressed and source-bound.',None,'Confirm actual fragile rotatability before field use; use appropriate declared branch.'),
      ('mathematical justification','achieved','Shared equations, cumulative/contact load, objective tradeoff, valid bounds and mechanism-based method choice independently substantiated.',None,'Any future multiple support or field mechanics needs a new explicit geometric/force model and evidence.'),
      ('empirical sufficiency and fair alternatives','partial','Same96/12/90 three-route evidence,17 parameter cases,3 seeds, legal bounds and real rejection controls; independent37 checks and focused parameter reruns.',
       'Actual NaN false acceptance shows numerical failure coverage incomplete; other successful controls cannot average it away.','Repair finite numeric checking and actually rerun paired valid/nonfinite controls and critical full cases.'),
      ('reproduction and result-to-paper traceability','achieved','Official raw reconstruction, actual clean runtime, independent all final feasibility/objectives,39 main table rows,64 Attachment2 geometry values and figure provenance consistent.',None,'Preserve raw/config/code identities and limits; do not interpret historical runtime as universal performance.'),
      ('clarity and completeness of scientific argument','achieved','Full Chinese paper/report text and15 rendered pages actually read; defined assumptions, symbols, mechanisms, real answers, validation, explanations and bounded recommendation.',None,'Optional linear-formula/pagination polish; keep substantive limitations and counterexamples clear.'),
      ('workflow transferability and autonomous gap resolution','partial','Real new-consumer execution and author flaw-driven improvements/log preservation; smoke not confused with full and quota resume actor retained.',
       'Receiving numerical finite-value branch releases invalid coordinate; old failed decimal geometry was not preserved although error/input and repair retained.','Add finite-value reception and clear unavailable-fit branch; preserve this first review before informed repair review.')
    ]
    quality=[{'dimension':d,'status':s,'evidence':evidence('report.md','coordinate-review.json','numerical-trace.json','rerun-independent-review.json','defect-controls.json'),
              'reason':reason,'material_gap':gap,'next_action':next_} for d,s,reason,gap,next_ in dims]
    result={
      'task_id':'R19-C11-L4-independent-initial-review','actor':'/root/r19_l4_reviewer',
      'review_type':'first_independent_production_review','informed_by_prior_verdict':False,
      'status':'initial_review_not_fully_accepted','mandatory_all_pass':False,
      'summary':'Finite final solutions, actual reproduction and complete Chinese paper supported; nonfinite-coordinate false acceptance remains a material receiving defect.',
      'a1_a6':a,'quality_diagnosis':quality,
      'source_binding':{'direct_original_reread':True,'pdf_pages':3,'docx_paragraphs':22,'docx_tables':1,'xlsx_all_sheets':3,
        'source_fields_match_program':True,'end_integrity':integrity},
      'performed_checks':{'independent_coordinate_groups':37,'independent_final_fleet_cases':4,'independent_selected_single_cases':4,
        'independent_formal_comparison_fleet_cases':12,'independent_parameter_cases':17,
        'group_count_includes_repeated_selected_classic_fleet':True,'frozen_static_LP_representative_trucks':4,
        'main_clean_exit_code':0,'main_clean_elapsed_seconds':receipt['elapsed_seconds'],
        'main_clean_four_goals_equal':True,'normalized_full_coordinate_rows_equal':True,'raw_csv_byte_equal':False,
        'changed750_cli_outputs_actually_generated_and_independently_valid':True,
        'parameter_base_and_fragile_original_height_actually_rerun':[7000,9800],
        'attachment2_geometry_pairs_recomputed':64,'paper_numeric_main_rows_recomputed':39,
        'paper_full_text_actual_read':True,'enterprise_report_full_text_actual_read':True,
        'paper_pdf_all_pages_rendered_and_visually_read':12,'enterprise_pdf_all_pages_rendered_and_visually_read':3,
        'author_validator_nan_false_acceptance':True,'independent_validator_nan_rejected':True},
      'confirmed_final_values':[r['metrics']|{'scenario':r['scenario']} for r in coords['results'] if 'scenario' in r],
      'defects':[{'id':'D1','severity':'material_receiving_correctness','source_requirement':'PDFp2 concrete each-item placement; DOCX P16-19 geometry/boundary and frozen a4/a6 receiving duties',
         'location':'runs/R19/levels/L4/execution/code/validator.py:33','observation':'NaN x causes CLI exit0 VALID errors=[] while independent invalid_numeric',
         'impact':'invalid numeric output can be consumed as checked; current finite final results separately proved feasible','counterexample':'runs/R19/levels/L4/review/initial/NaN_coordinate.csv'}],
      'failures_and_recovery':[
        {'class':'reviewer_receipt_metadata_error','operation':'main rerun receipt pid field','observed':'subprocess.args command array stored under pid instead of actual ID',
         'retained':'clean-rerun-receipt-original.json','correction':'process_id=null, preserve exact command and completed exit0 receipt; script patched prospectively'},
        {'class':'reviewer_serialization_error','session_id':94967,'actual_exit_code':1,
         'observed':'TypeError Object of type int64 is not JSON serializable at secondary wrapper final save',
         'completed_outputs_retained':True,'recovery':'read already completed artifacts and independently verify; patched numpy scalar JSON conversion prospectively',
         'original_subprocess_exit_codes':None,'original_subprocess_stdout':None,'original_subprocess_elapsed_seconds':None,
         'replacement_call_is_not_original':True,'evidence':'rerun-independent-review.json'},
        {'class':'expected_invalid_output_controls','source':'defect-controls.json','comment':'true observed valid/NaN/overlap/gap CLI calls; failed malformed tests intentionally retained'},
        {'class':'expected_impossible_new_input','source':'rerun-independent-review.json','actual_exit_code':1,'comment':'new1001cm one-item case explicitly nonzero with traceback and no success result'}],
      'resources':{'provider':None,'model':None,'tokens':None,'cost':None,'total_elapsed_seconds':None,
        'environment':json.loads((OUT/'source-audit.json').read_text(encoding='utf-8'))['environment'],
        'known_measured_main_rerun_seconds':receipt['elapsed_seconds'],'network_searches':0,'installs':0,'subagents_spawned':0,
        'no_generic_two_error_stop':True,'whole_review_short_deadline':None},
      'boundaries':{'write_domain':'runs/R19/levels/L4/review/initial/','producer_or_preparation_files_modified':False,
        'other_levels_or_shared_report_read':False,'old_solutions_or_other_verdicts_read':False,'author_pass_as_truth':False},
      'termination':{'all_known_sessions':[{'id':39929,'state':'finished','exit_code':0},{'id':75880,'state':'finished','exit_code':0},{'id':94967,'state':'finished','exit_code':1}],
        'pending_session_ids':[],'background_processes_started':0,'subagent_calls':0,
        'all_synchronous_subprocess_calls_returned':True,'finalizer_exit0_receipt_required':True,'stop_writing_after_manifest':True},
      'limitations':['finite feasible heuristic results not global optima or complete real Pareto frontier','original Attachment2 fields insufficient for full transport cost/load validation',
        'static uniform center/full single-support assumptions do not certify actual vibration/axis load/handling',
        'historical producer timing provenance checked but elapsed constant not independently recoverable',
        'supplemental original in-memory command telemetry lost before JSON save remains unknown'],
      'next_action':'Root receives this frozen initial verdict; any producer repair uses new freeze and explicitly informed review, retaining D1 and initial review.'
    }
    now=datetime.now(timezone.utc).isoformat();result['frozen_at']=now
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    files=[ident(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p!=OUT/'manifest.json']
    manifest={'schema':'independent-initial-review-manifest/1','task_id':result['task_id'],'status':'frozen','frozen_at':now,'files':files,'self_excluded':True,'claim':'actual frozen first review bytes; not an all-pass assertion'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(ident(ROOT/f['path'])==f for f in files)
    print(json.dumps({'status':result['status'],'a1_a6':[(x['id'],x['status']) for x in a],
       'quality':[(x['dimension'],x['status']) for x in quality],'manifest_files':len(files),'manifest':ident(OUT/'manifest.json'),'pending_sessions':[]},ensure_ascii=False))
if __name__=='__main__':main()
