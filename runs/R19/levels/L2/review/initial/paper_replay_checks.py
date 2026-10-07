from pathlib import Path
import sys,json,datetime,shutil,fitz
B=Path.cwd();O=B/'runs/R19/levels/L2/review/initial';E=B/'runs/R19/levels/L2/execution';sys.path.insert(0,str(O));from audit_frozen import readcsv,expected,audit
# Independent semantic audit of all successful critical replays; genuine fail remains fail.
cases={r['case']:r for r in readcsv(E/'experiments/experiments.csv')};records=[]
for receipt in sorted(O.glob('parameter_*_integer_schema.receipt.json')):
 r=json.loads(receipt.read_text(encoding='utf-8'));name=r['label'][len('parameter_'):-len('_integer_schema')];case=cases[name];items,vs,cfg=expected(case)
 z={'case':name,'receipt':receipt.name,'exit_code':r['exit_code'],'reported_status':case['status'],'seconds':r['seconds']}
 if r['exit_code']==0:
  result=audit(O/'parameter_replays_integer'/name,items,vs,cfg,True,name);z['independent_audit']=result;z['original_metrics_equal']={k:abs(float(case[k])-result['metrics'][mk])<1e-7 for k,mk in [('vehicles','vehicle_count'),('cost_yuan','cost_yuan'),('volume_utilization','volume_utilization'),('weight_utilization','weight_utilization')]}
 else:z['stderr']=(O/('parameter_'+name+'_integer_schema.stdout.txt')).read_text(encoding='utf-8');z['expected_source_height_failure']=name=='27_vehicle_height' and 'heuristic_no_fit_not_mathematical_infeasibility' in z['stderr']
 records.append(z)
(O/'parameter-replay-audit.json').write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':records,'first_float_schema_attempts_preserved':10,'corrected_to_documented_integer_schema':True,'scope':'9 fresh successful critical cases plus one raw-bound impossible-height fail, all other35 successful saved case layouts independently checked'},ensure_ascii=False,indent=2),encoding='utf-8')
# Source PDF rendering and complete text/box audit. Never read author QA as oracle.
pages=[]
for label,p in [('paper',E/'paper/paper.pdf'),('report',E/'report.pdf')]:
 folder=O/'pdf_render'/label;folder.mkdir(parents=True,exist_ok=True);texts=[]
 with fitz.open(p) as d:
  for ix,page in enumerate(d):
   png=folder/f'page_{ix+1:02d}.png';page.get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(png);txt=page.get_text();texts.append(txt)
   bad=[list(block[:4]) for block in page.get_text('blocks') if block[0]<0 or block[1]<0 or block[2]>page.rect.width+0.1 or block[3]>page.rect.height+0.1]
   pages.append({'document':label,'page':ix+1,'chars':len(txt),'out_of_bounds_blocks':bad,'png':png.relative_to(O).as_posix()})
 (O/(label+'-pdf-text.txt')).write_text('\n\n'.join(texts),encoding='utf-8')
(O/'pdf-render-audit.json').write_text(json.dumps({'source':'directly rendered frozen PDF, no author QA copied','pages':pages,'visual_inspection':'pending individual images'},ensure_ascii=False,indent=2),encoding='utf-8')
for folder in ['figures','paper','checks','experiments']:(O/'staged'/folder).mkdir(exist_ok=True)
shutil.copy2(E/'experiments/experiments.csv',O/'staged/experiments/experiments.csv')
print(json.dumps({'replay_records':len(records),'successes':sum(x['exit_code']==0 for x in records),'all_success_layouts_valid':all(x.get('independent_audit',{'valid':True})['valid'] for x in records),'metric_mismatches':[x['case'] for x in records if not all(x.get('original_metrics_equal',{'expected_fail':True}).values())],'pdf_pages':len(pages),'page_boxes_bad':sum(bool(p['out_of_bounds_blocks']) for p in pages)},ensure_ascii=False),flush=True)
