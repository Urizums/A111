from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
from datetime import datetime,timezone
import csv,json,hashlib,re
from pypdf import PdfReader
root=Path('runs/R22/execution');ex=root/'correction-v3';doc=ex/'report';sc=root/'science-v1/results'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(n):
    with (sc/n).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def display(v,n=2):return '不可估计' if v=='' else format(Decimal(str(v)).quantize(Decimal(1).scaleb(-n),rounding=ROUND_HALF_UP),f'.{n}f')
def route(r):return r['origin'][5:10]+'/'+('R' if r['method_id']=='shared_ridge10' else 'W')
body=(doc/'REPORT.md').read_text('utf-8');lines=body.splitlines();tables=[];current=[]
for line in lines+['']:
    if line.startswith('|'):current.append(line.strip('|').split('|'))
    elif current:tables.append({'header':current[0],'rows':current[2:]});current=[]
assert len(tables)==15
ledger=[]
def equal(table_index,row_index,column,expected,source,key,field):
    actual=tables[table_index]['rows'][row_index][column];assert actual==expected,(table_index,row_index,column,actual,expected)
    ledger.append({'table_index':table_index+1,'row':row_index+1,'column':column+1,'source':source,'key':key,'field':field,'display':actual})
overall=read('group_overall.csv');stage=read('group_stage.csv');activity=read('group_activity.csv');combined=read('combined_first_two.csv')
for i,r in enumerate(overall):
    for j,(field,n,mult) in enumerate([('mae',3,1),('rmse',3,1),('bias',3,1),('coverage',2,100),('width',3,1),('interval_score',3,1)],1):equal(1,i,j,display(Decimal(r[field])*mult,n),'group_overall.csv',route(r),field)
    for j,(field,mult) in enumerate([('below',100),('above',100),('shortage_per_day',1),('waste_per_day',1),('loss_per_day',1),('procurement_per_day',1),('q_per_day',1)],1):equal(2,i,j,display(Decimal(r[field])*mult,2),'group_overall.csv',route(r),field)
for index,rows,sourcename,fields in [(3,stage,'group_stage.csv',[(3,'mae',3,1),(4,'bias',3,1),(5,'coverage',2,100),(6,'loss_per_day',2,1)]),(4,activity,'group_activity.csv',[(3,'mae',3,1),(4,'coverage',2,100),(5,'interval_score',3,1),(6,'loss_per_day',2,1)]),(6,combined,'combined_first_two.csv',[(2,'mae',3,1),(3,'rmse',3,1),(4,'coverage',2,100),(5,'interval_score',3,1),(6,'loss_per_day',2,1)])]:
    for i,r in enumerate(rows):
        for j,field,n,mult in fields:equal(index,i,j,display(Decimal(r[field])*mult,n),sourcename,r.get('origin','84-day')+'|'+r['method_id']+'|'+r.get('stage',r.get('holiday','all')),field)
sol=read('solver_daily.csv');groups={}
for r in sol:groups.setdefault((r['origin'],r['method_id']),[]).append(r)
for i,(key,rs) in enumerate(sorted(groups.items())):
    for column,field,op in [(3,'budget_slack',min),(4,'budget_slack',max)]:equal(7,i,column,display(op(Decimal(r[field]) for r in rs),2),'solver_daily.csv',str(key),field+' '+op.__name__)
for start,name,dim in [(8,'group_store.csv','store_id'),(11,'group_item.csv','item_id')]:
    rows=read(name);origins=sorted(set(r['origin'] for r in rows))
    for oi,o in enumerate(origins):
        for i,d in enumerate(sorted(set(r[dim] for r in rows))):
            pair={r['method_id']:r for r in rows if r['origin']==o and r[dim]==d};a=Decimal(pair['shared_ridge10']['loss_per_day']);b=Decimal(pair['weekly_mean56']['loss_per_day'])
            for col,val,field in [(2,a,'R loss_per_day'),(3,b,'W loss_per_day'),(4,b-a,'W-R loss_per_day')]:equal(start+oi,i,col,display(val,2),name,o+'|'+d,field)
rows=[r for r in read('group_activity_stage.csv') if r['holiday']=='1']
for i,r in enumerate(rows):
    for col,field,n,mult in [(3,'mae',3,1),(4,'coverage',2,100),(5,'loss_per_day',2,1)]:equal(14,i,col,'不可估计' if r[field]=='' else display(Decimal(r[field])*mult,n),'group_activity_stage.csv',route(r)+'|'+r['stage'],field)
# Verify repeated monetary narrative against source-decimal values, not renderer fmt.
narrative=[]
def contains(expected,context,source):
    assert expected in context,(expected,context);narrative.append({'display':expected,'context':context,'source':source})
paragraphs=[l for l in lines if l and not l.startswith(('#','|','!'))]
for r in overall:contains(display(r['loss_per_day']),next(l for l in paragraphs if l.startswith('三窗R的MAE')),route(r)+' overall loss')
paragraph=next(l for l in paragraphs if l.startswith('全部三窗R每日损失'))
for method,field in [('shared_ridge10','shortage_per_day'),('weekly_mean56','shortage_per_day'),('shared_ridge10','waste_per_day'),('weekly_mean56','waste_per_day')]:
    r=next(r for r in overall if r['origin'].startswith('2026-09-19') and r['method_id']==method);contains(display(r[field]),paragraph,'09-19 '+method+' '+field)
for o in sorted(set(r['origin'] for r in overall)):
    rs={r['method_id']:r for r in overall if r['origin']==o};contains(display(Decimal(rs['weekly_mean56']['loss_per_day'])-Decimal(rs['shared_ridge10']['loss_per_day'])),paragraph,o+' overall W-R')
paragraph=next(l for l in paragraphs if l.startswith('活动不必同程度'))
for o,h in [('2026-09-02',1),('2026-09-02',0),('2026-07-22',1),('2026-09-19',1),('2026-07-22',0),('2026-09-19',0)]:
    r=next(r for r in activity if r['origin'].startswith(o) and r['holiday']==str(h) and r['method_id']=='shared_ridge10');contains(display(r['loss_per_day']),paragraph,o+' R activity='+str(h))
paragraph=next(l for l in paragraphs if l.startswith('前两窗目标分别'))
for r in combined:contains(display(r['loss_per_day']),paragraph,r['method_id']+' 84-day loss')
c={r['method_id']:r for r in combined};contains(display(Decimal(c['weekly_mean56']['loss_per_day'])-Decimal(c['shared_ridge10']['loss_per_day'])),paragraph,'84-day W-R')
paired=read('paired_daily.csv')
for o in sorted(set(r['origin'] for r in paired)):
    rows=[r for r in paired if r['origin']==o];values=[Decimal(r['loss_W_minus_R']) for r in rows];context=next(l for l in paragraphs if l.startswith(o[:10]+'窗同日期'))
    for value,name in [(sum(values)/len(values),'mean'),(min(values),'min'),(max(values),'max')]:contains(display(value),context,o+' paired '+name)
paragraph=next(l for l in paragraphs if l.startswith('第一窗R从早期'))
for m in ['shared_ridge10','weekly_mean56']:
    r=next(r for r in stage if r['origin'].startswith('2026-07-22') and r['stage']=='15-42' and r['method_id']==m);contains(display(r['loss_per_day']),paragraph,'07-22 late '+m)
# Preserve original lock bytes and all 268 original delivery files.
freeze=json.loads((ex/'source-freeze.json').read_text('utf-8'))
for f in freeze['identities']:assert sha(Path(f['path']))==f['sha256']
lock=json.loads(Path('runs/R22/execution-lock.json').read_text('utf-8'))
for f in lock['files']:assert sha(Path(f['path']))==f['sha256'] and Path(f['path']).stat().st_size==f['size_bytes']
assert len(lock['files'])==268
v2lock=json.loads(Path('runs/R22/document-correction-v2-lock.json').read_text('utf-8'))
assert len(v2lock['files'])==38
for f in v2lock['files']:assert sha(Path(f['path']))==f['sha256'] and Path(f['path']).stat().st_size==f['size_bytes']
assert '不宣称全程未见其他摘要' in body
assert 'CSV文本' in body

reader=PdfReader(doc/'REPORT.pdf');pdftext='\n'.join(p.extract_text() for p in reader.pages)
for phrase in ['340.08','1117.93','678.03','61.63','5.13','50.28','ROUND_HALF_UP','旧稿首判h6失败','不可估计','附录A','附录B','附录C']:assert phrase in pdftext
figures=[]
for p in sorted((doc/'figures').glob('*.png')):
    assert sha(p)==sha(root/'report-v1/figures'/p.name);figures.append({'path':str(p),'sha256':sha(p),'same_plot_bytes_as_first_delivery':True})
assert len(figures)==6
observations=[
 '完整摘要与边界、中文和约束符号可读，未观察裁切。',
 '训练边界表、R/W定义、残差来源和优化公式可读。',
 '总体两表可读；09-19/W报废实际显示340.08，符合正文。',
 '总体图、早晚表完整；09-19/W远期日损失显示678.03。',
 '六带图轴单位清楚；早晚论证和活动表开端完整。',
 '活动表重复表头；R09-19活动损失1117.93与下方正文一致。',
 '活动空格热图、配对曲线及单位可读，0日不可估计明确。',
 '合并表和店品热图单位清楚；资源表开端正常。',
 '资源表接续和原验证可读；意外代理摘要暴露及知情复审说明完整，局限开端可读。',
 '局限、来源、CSV文本Decimal派生再舍入和旧失败保留说明可读；附录A开端完整。',
 '门店续表无裁切；S05/W61.63、S10/W减R5.13、09-02/S09差额6.83与来源一致。',
 '商品表完整可读；K01/W50.28显示正确，末表跨页正常。',
 '商品续表与附录C完整；R09-19活动远期1117.93，空格不可估计。'
]
pages=sorted(doc.glob('page-*.png'));assert len(pages)==len(reader.pages)==len(observations)
result={'schema':'r22-known-document-correction-v3-author-check/1','verdict':'pass','attempt':3,'repairs_used':2,'repair_limit':None,'repair_number':2,'independent':False,'actual_checked_at_utc':datetime.now(timezone.utc).isoformat(),'rule':'Decimal of published CSV text, ROUND_HALF_UP','complete_body_read_receipt':'receipts/0005-read-full-v3-md.json','display_cell_checks':len(ledger),'cell_ledger':ledger,'repeated_monetary_claims_checked':len(narrative),'narrative_ledger':narrative,'original_delivery_268_files_unchanged':True,'v2_locked_38_files_unchanged':True,'context_exposure_retained':True,'whole_context_blind_claim':False,'science_rerun':False,'renderer_change_frozen_before_pdf':True,'source_sha256':sha(ex/'source/build_report_v3.py'),'pdf_sha256':sha(doc/'REPORT.pdf'),'markdown_sha256':sha(doc/'REPORT.md'),'actual_pdf_pages':len(reader.pages),'all_pages_actually_viewed_using':'functions.exec tools.view_image, each final page separately emitted and read','page_observations':[{'page':i+1,'path':str(p),'sha256':sha(p),'actually_viewed':True,'observation':observations[i]} for i,p in enumerate(pages)],'figures':figures,'visual_defects_observed':[],'first_verdict_retained':'h1-h5 pass; h6 fail (informed root packet); subsequent reception is known repair re-review','failure_categories_kept_separate':['original author read-path recovery','original expected existing-output refusal','independent receiver 12 recorded errors (informed root packet; not read/regraded)','document consistency repair 2, attempt 3; attempt 2 failure retained'],'model':None,'tokens':None,'cost':None}
visual={'schema':'r22-v3-actual-page-review/1','independent':False,'actual_pdf_pages':len(reader.pages),'pdf_sha256':result['pdf_sha256'],'markdown_sha256':result['markdown_sha256'],'complete_markdown_read':True,'page_observations':result['page_observations'],'visual_defects_observed':[],'units_reviewed':['件/键','元/日','覆盖率百分数','区间评分件/键','容量件','预算元'],'scope':'all final rendered pages actually viewed; no fixed page limit'}
with (ex/'visual-qa-final.json').open('x',encoding='utf-8') as f:json.dump(visual,f,ensure_ascii=False,indent=2);f.write('\n')
with (ex/'author-selfcheck-v3.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['repair_number','verdict','attempt','repairs_used','display_cell_checks','repeated_monetary_claims_checked','original_delivery_268_files_unchanged','actual_pdf_pages','visual_defects_observed','source_sha256','pdf_sha256','markdown_sha256']},ensure_ascii=False,indent=2))
