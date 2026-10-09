from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from pypdf import PdfReader
import pandas as pd
ex=Path('runs/R22/execution');doc=ex/'report-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
pages=list(sorted(doc.glob('page-*.png')));reader=PdfReader(doc/'REPORT.pdf');assert len(pages)==len(reader.pages)==13
body=(doc/'REPORT.md').read_text('utf-8');assert len(body)>10000
for phrase in ['知情固定策略历史回放','不可估计','11.9708333333','作者验证','附录A','附录B','附录C','sum(cq)≤6000','IS90=']:assert phrase in body
text='\n'.join(p.extract_text() for p in reader.pages)
for phrase in ['固定42日需求预测','11.9708333333','不可估计','附录A','附录B','附录C','下侧漏出并不等于缺货']:assert phrase in text
assert all(len(p.extract_text())>300 for p in reader.pages)
for i in range(1,7):assert len(list((doc/'figures').glob(f'{i:02d}_*.png')))==1
observations=[
 '标题、摘要和问题边界完整；中文、金额单位、约束符号可读，无裁切。',
 '训练边界表和源残差方法可读；公式与代码式符号换行正常。',
 '评价定义、总体预测和决策表完整，数字列对齐，无重叠。',
 '三窗总体图、论证和早晚表清楚；图例及轴单位可读。',
 '六带曲线图可读，早晚解释接续完整；活动表在页尾开始。',
 '活动表跨页重复表头；覆盖图、漏出论证及活动支持表可读。',
 '活动空格热图明确0日不可估计；日配对曲线和首窗描述完整。',
 '后两窗配对、84日合并、店品热图和资源表开始部分可读。',
 '资源表跨页表头重复；验证方法、错误保留和解释局限完整。',
 '局限接续、复现入口和来源可读；店附录开始，表格未裁切。',
 '全部店分层续表清楚，门店标识与金额差值完整。',
 '商品附录八品三窗清楚，负差符号和金额单位可读。',
 '活动×早晚空格为0/0不可估计，末尾区间与损失单位区别完整。'
]
dump(ex/'visual-qa-final.json',{'schema':'r22-author-visual-qa/1','independent':False,'actual_reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'full_markdown_read_receipt':'receipts/0016-read-final-body.json','pdf_sha256':sha(doc/'REPORT.pdf'),'marker_receipt':'receipts/0013-pdf-artifact-marker.json','export_receipt':'receipts/0014-build-report.json','render_receipt':'receipts/0015-render-pdf.json','actual_observation_tool':'functions.exec tools.view_image; each final page emitted and visually read in this executor context','pages':[{'page':i+1,'path':str(p),'sha256':sha(p),'actually_viewed':True,'observation':observations[i]} for i,p in enumerate(pages)],'figures_actually_seen_in_pages':6,'visual_defects_observed':[],'optional_notes':['图5先于图4呈现；编号可追溯、意义不变，未作为强制缺陷。'],'full_report_read':True})
commands=[]
for p in sorted((ex/'receipts').glob('*.json')):
    obj=json.loads(p.read_text('utf-8'))
    if obj['state']=='finished':commands.append({'receipt':str(p),'argv':obj['argv'],'begin_utc':obj['begin']['utc'],'end_utc':obj['end']['utc'],'exit_code':obj['exit_code']})
dump(ex/'command-manifest-through-review.json',commands)
sourcefiles=[p for p in (ex/'source').rglob('*') if p.is_file()]+[ex/'WORKFLOW.md',ex/'prospective-freeze.json']
dump(ex/'source-delivery-lock.json',{'schema':'r22-source-delivery-identity/1','frozen_at_utc':datetime.now(timezone.utc).isoformat(),'files':[{'path':str(p).replace('\\','/'),'sha256':sha(p),'size_bytes':p.stat().st_size} for p in sorted(sourcefiles)],'claim':'document/export/check source identity; prospective science lock separately proves prior timing'})
dump(ex/'result.json',{'schema':'r22-author-result/1','task':'R22-02','status':'produced_and_author_selfchecked','independent_acceptance':False,'write_domain':'runs/R22/execution/**','os_isolation':False,'actual_model':None,'tokens':None,'cost':None,'main_markdown':'runs/R22/execution/report-v1/REPORT.md','main_pdf':'runs/R22/execution/report-v1/REPORT.pdf','final_pdf_pages':13,'figures':6,'prospective_source_lock':'runs/R22/execution/prospective-freeze.json','delivery_source_lock':'runs/R22/execution/source-delivery-lock.json','science_output':'runs/R22/execution/science-v1','clean_output':'runs/R22/execution/clean-v1','author_selfcheck':'runs/R22/execution/author-selfcheck-v1/selfcheck.json','author_visual_qa':'runs/R22/execution/visual-qa-final.json','command_manifest':'runs/R22/execution/command-manifest-through-review.json','terminal_receipts_in_manifest':len(commands),'last_finalization_receipt':'runs/R22/execution/receipts/0017-finalize-delivery.json','assertions':{'six_route_origin_grids_4032':True,'source_raw_backtrace':True,'published_point10_error_recomputed':True,'pool_days':[11,53,70],'integer_action_resources':True,'solver_days':252,'meaningful_oracle_and_boundaries':True,'all_predefined_groups_and_empty_cells':True,'clean_semantic_numeric_equivalence':True,'whole_chinese_body_actually_read':True,'all_final_pdf_pages_actually_viewed':True,'author_selfcheck_only':True},'failures':[{'receipt':'0002-read-implementation.json','kind':'read_path_recovery','exit_code':1,'description':'R21 prospective-freeze initially addressed at root; actual execution sibling subsequently verified; no fit yet.'},{'receipt':'0011-existing-output-refused.json','kind':'expected_rejection_boundary','exit_code':1,'description':'Existing science-v1 output refused before writing; intended boundary assertion.'}],'scientific_source_repairs':[],'restricted_reads_not_performed':['R21/evaluation/**','protocol/make_case.py','prior reports/results/selfchecks/diagnostics','R22/audit/**','root REPORT/TODO/checkpoint or shared actor artifacts'],'root_next_action':'After terminal finalization and read-only verification, freeze whole first delivery domain; hand fresh acceptor protocol/raw/locked actual source/science/report, excluding result.json/author-selfcheck/visual-qa and author diagnostics as judging inputs.'})
print('Delivery finalized; actual 13 page views recorded. Author self-check only. Await read-only terminal verification, then stop writes for root freeze.')
