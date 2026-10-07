from pathlib import Path
import json,hashlib,datetime,sys
base=Path.cwd(); out=base/'runs/R19/levels/L2/review/preparation'
lockpaths=['runs/R19/inputs/raw-lock.json','runs/R19/candidate/C11-lock.json','runs/R19/levels/L2/design-lock.json','runs/R19/evaluation-lock.json']
checks=[]
for rel in lockpaths:
 lock=json.loads((base/rel).read_text(encoding='utf-8-sig'))
 for e in lock['files']:
  p=base/e['path']; b=p.read_bytes(); checks.append({'lock':rel,'path':e['path'],'sha256':hashlib.sha256(b).hexdigest(),'size_bytes':len(b),'hash_match':hashlib.sha256(b).hexdigest()==e['sha256'],'size_match':len(b)==e.get('size_bytes',len(b))})
d=json.loads((out/'official-source-extract.json').read_text(encoding='utf-8'))
controls={'status':'preparation_only_no_execution_access','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all_locked_bytes_match':all(c['hash_match'] and c['size_match'] for c in checks),'lock_checks':checks,'independent_source_read':{'pdf_pages':len(d['pdf']),'pdf_all_pages_visually_inspected':True,'docx_main_paragraphs':len(d['docx']['paragraphs']),'docx_tables':len(d['docx']['tables']),'xlsx_sheets':[s['title'] for s in d['xlsx']['sheets']],'xlsx_nonempty_cells':[{'sheet':s['title'],'count':len(s['cells'])} for s in d['xlsx']['sheets']]},'attachment2_qualification':{'products':8,'vehicles_or_containers':16,'missing_required_fields':['item quantities','item weights','cargo constraint categories','vehicle payload'],'product_unit':'mm','vehicle_unit':'m encoded in strings','cost_unit':'yuan/1000km for headed E column; F4:F6 has no explicit heading','blank_sheet':'Sheet3','geometry_notes':['low railing height is not enclosed volume height','stepped floor row19 cannot be a single rectangular bin without a qualified approximation'],'mandatory_duty':'audit and bounded answer; original expansion optional','no_missing_data_imputation':True},'control_domain':str(out),'read_scope':'only L2 request, official raw and raw-lock, C11 package/lock, L2 design/lock, frozen acceptance/quality/evaluation-lock, applicable AGENTS and PDF skill','execution_domain_accessed':False,'producer_contacted':False,'network_used':False,'software_installed':False,'model':None,'tokens':None,'cost':None}
(out/'data-controls.json').write_text(json.dumps(controls,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'all_locked_bytes_match':controls['all_locked_bytes_match'],'lock_entries':len(checks),'read_coverage':controls['independent_source_read']},ensure_ascii=False,indent=2))
