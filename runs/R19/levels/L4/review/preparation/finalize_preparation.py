from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[5]
def identity(p):
    return {'path':p.relative_to(ROOT).as_posix(),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    audit=json.loads((OUT/'source-audit.json').read_text(encoding='utf-8'))
    controls=json.loads((OUT/'small-controls-results.json').read_text(encoding='utf-8'))
    assert all(x['all_match'] for x in audit['locks'])
    assert controls['all_controls_pass'] and controls['control_count']==25
    for source in audit['source_identity']:
        assert identity(ROOT/source['path'])==source
    result={
      'task_id':'R19-C11-L4-independent-review-preparation',
      'actor':'/root/r19_l4_reviewer',
      'status':'preparation_complete_frozen',
      'phase':'pre_production_handoff',
      'method_frozen_before_production_access':True,
      'production_received':False,
      'production_read':False,
      'production_acceptance_performed':False,
      'production_verdict':None,
      'mandatory':[{ 'id':f'a{n}','status':'not_evaluated','verdict':None } for n in range(1,7)],
      'quality_diagnosis':[{'dimension':x,'judgment':None,'status':'not_evaluated'} for x in [
        'problem fidelity','mathematical justification','empirical sufficiency and fair alternatives',
        'reproduction and result-to-paper traceability','clarity and completeness of scientific argument',
        'workflow transferability and autonomous gap resolution']],
      'source_identity':audit['source_identity'],
      'source_checks':{'original_pdf_pages_direct_read':3,'original_pdf_pages_rendered_and_visually_read':3,
        'original_docx_paragraphs':len(audit['docx']['paragraphs']),'original_docx_tables':len(audit['docx']['tables']),
        'original_docx_xml_inspected':True,'xlsx_sheets_all_direct_read':list(audit['xlsx']),
        'raw_lock_match':True,'evaluation_lock_match':True,'design_lock_match':True,
        'source_contract':'runs/R19/levels/L4/review/preparation/source-contract.json'},
      'method':{'path':'runs/R19/levels/L4/review/preparation/method.md',
        'plan':'runs/R19/levels/L4/review/preparation/plan.md',
        'checker':'runs/R19/levels/L4/review/preparation/independent_checks.py',
        'independence':'reviewer-owned geometry/support/load/objective logic; author pass not truth',
        'paper_reading':'actual full Chinese language/mathematics/scientific-argument reading at production; no keyword/file-count proxy'},
      'controls':{'scope':'synthetic_preparation_only_not_production_acceptance','count':25,'all_pass':True,
        'actual_latest_elapsed_seconds':controls['elapsed_seconds'],
        'false_acceptance_rate':None,'false_rejection_rate':None,
        'attempts':[{'attempt':1,'control_count':23,'exit_code':0,'all_pass':True,'elapsed_seconds':0.018781299993861467,
                     'evidence':'original tool receipt; original 23 controls retained in later reports'},
                    {'attempt':2,'control_count':25,'exit_code':1,'all_pass':False,'elapsed_seconds':0.01557689999754075,
                     'evidence':'runs/R19/levels/L4/review/preparation/small-controls-attempt-02-failed.json'},
                    {'attempt':3,'control_count':25,'exit_code':0,'all_pass':True,'elapsed_seconds':controls['elapsed_seconds'],
                     'evidence':'runs/R19/levels/L4/review/preparation/small-controls-results.json'}]},
      'failures_and_corrections':[
        {'type':'input_logistics','original_operation':'Get-Content runs/R19/raw-lock.json',
         'actual_error':'Cannot find path .../runs/R19/raw-lock.json because it does not exist.',
         'cause':'coordinator supplied incorrect path','authority':'root message explicitly authorized corrected runs/R19/inputs/raw-lock.json',
         'changed_operation':'read exact corrected path; did not expand search domain','outcome':'corrected raw lock read and all bytes match'},
        {'type':'preparation_control_data_defect','attempt':2,'actual_exit_code':1,
         'actual_error':'directed_lower_upper_center control_pass=False; expected outside point was exactly on allowed closed boundary',
         'old_geometry':'directed lower x in [0,80], upper x30 length100 => center80',
         'changed_geometry':'upper x40 length100 => center90 truly outside',
         'retained_old_output':'small-controls-attempt-02-failed.json','checker_semantics_changed':False,
         'outcome':'attempt3 all25 pass; failure not erased'}],
      'observed_events':[{'type':'tool_output_truncation','effect':'large batch outputs truncated; targeted reads and direct raw extraction used; not evidence of completed authoring'}],
      'environment':audit['environment'],
      'resources':{'provider':None,'model':None,'tokens':None,'cost':None,'total_elapsed_seconds':None,
                   'network_searches':0,'software_installs':0,'subagents_spawned':0,
                   'individual_static_LP_time_limit_seconds':10,'whole_task_short_deadline':None},
      'boundaries':{'write_domain':'runs/R19/levels/L4/review/preparation/',
         'read_domains':['runs/R19/inputs/L4.md','runs/R19/candidate/C11/forge-agent-flow/',
          'runs/R19/levels/L4/design/','runs/R19/inputs/raw/','runs/R19/acceptance.json','runs/R19/quality-diagnosis.md',
          'runs/R19/evaluation-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/levels/L4/design-lock.json',
          'necessary read-only PDF/DOCX/XLSX tool guides'],
         'execution_domains_read':False,'other_levels_read':False,'shared_status_or_report_read':False,
         'old_solutions_or_papers_read':False,'shared_state_modified':False},
      'limitations':['production schema adaptation, full scenario checks, clean rerun and actual final paper reading are pending',
        'full-support and multi-support directed-center strict branches are conservative interpretations, not extra universal official constraints',
        'LP establishes only static reaction feasibility under uniform-centre and declared area assumptions, not local material or transport dynamics safety',
        'Attachment2 cannot supply complete real optimization instance or cost validation without missing measured fields',
        'synthetic known controls do not measure general checker reliability or establish production acceptance'],
      'termination':{'background_processes_started':0,'ongoing_tool_session_ids':[],
                     'all_prior_exec_calls_completed':True,'finalizer_synchronous_exit0_receipt_required':True,
                     'no_post_terminal_write':True},
      'next_action':'wait for explicit official frozen production handoff from root; do not read production domains until authorized'
    }
    now=datetime.now(timezone.utc).isoformat()
    result['frozen_at']=now
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    files=[identity(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json']
    manifest={'schema':'independent-review-preparation-manifest/1','task_id':result['task_id'],'status':'frozen',
              'frozen_at':now,'scope':'runs/R19/levels/L4/review/preparation/',
              'files':files,'self_excluded':True,'claim':'byte identity only; preparation self-controls are not production acceptance'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for f in files:assert identity(ROOT/f['path'])==f
    print(json.dumps({'status':result['status'],'manifest_files':len(files),'all_identities_match':True,
                      'manifest':identity(OUT/'manifest.json'),'controls':25,'production_received':False},ensure_ascii=False))
if __name__=='__main__':main()
