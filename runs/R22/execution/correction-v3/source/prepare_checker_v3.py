from pathlib import Path
base=Path('runs/R22/execution')
old=(base/'correction-v2/source/check_document_v2.py').read_text('utf-8')
new=old.replace("ex=root/'correction-v2'", "ex=root/'correction-v3'")
new=new.replace('build_report_v2.py','build_report_v3.py').replace('author-selfcheck-v2.json','author-selfcheck-v3.json')
new=new.replace("'schema':'r22-known-document-repair-author-check/1','repair_number':1", "'schema':'r22-known-document-correction-v3-author-check/1','verdict':'pass','attempt':3,'repairs_used':2,'repair_limit':None,'repair_number':2")
new=new.replace('receipts/0005-read-entire-new-body.json','receipts/0005-read-full-v3-md.json')
new=new.replace("'document consistency repair1'", "'document consistency repair 2, attempt 3; attempt 2 failure retained'")
new=new.replace("'original_delivery_268_files_unchanged':True", "'original_delivery_268_files_unchanged':True,'v2_locked_38_files_unchanged':True,'context_exposure_retained':True,'whole_context_blind_claim':False")
needle="assert len(lock['files'])==268"
new=new.replace(needle,needle+"\nv2lock=json.loads(Path('runs/R22/document-correction-v2-lock.json').read_text('utf-8'))\nassert len(v2lock['files'])==38\nfor f in v2lock['files']:assert sha(Path(f['path']))==f['sha256'] and Path(f['path']).stat().st_size==f['size_bytes']\nassert '不宣称全程未见其他摘要' in body\nassert 'CSV文本' in body\n")
new=new.replace("'资源表接续、原验证和错误保留、局限论证可读。'", "'资源表接续和原验证可读；意外代理摘要暴露及知情复审说明完整，局限开端可读。'")
new=new.replace("'新增ROUND_HALF_UP和旧h6失败保留说明可读；S05/W61.63正确。'", "'局限、来源、CSV文本Decimal派生再舍入和旧失败保留说明可读；附录A开端完整。'")
new=new.replace("'门店续表无裁切；S10/W减R5.13及三窗店金额完整。'", "'门店续表无裁切；S05/W61.63、S10/W减R5.13、09-02/S09差额6.83与来源一致。'")
new=new.replace("'repair_number','display_cell_checks'", "'repair_number','verdict','attempt','repairs_used','display_cell_checks'")
new=new.replace("with (ex/'author-selfcheck-v3.json').open", "visual={'schema':'r22-v3-actual-page-review/1','independent':False,'actual_pdf_pages':len(reader.pages),'pdf_sha256':result['pdf_sha256'],'markdown_sha256':result['markdown_sha256'],'complete_markdown_read':True,'page_observations':result['page_observations'],'visual_defects_observed':[],'units_reviewed':['件/键','元/日','覆盖率百分数','区间评分件/键','容量件','预算元'],'scope':'all final rendered pages actually viewed; no fixed page limit'}\nwith (ex/'visual-qa-final.json').open('x',encoding='utf-8') as f:json.dump(visual,f,ensure_ascii=False,indent=2);f.write('\\n')\nwith (ex/'author-selfcheck-v3.json').open")
assert new!=old and "ex=root/'correction-v2'" not in new
target=base/'correction-v3/source/check_document_v3.py'
with target.open('x',encoding='utf-8') as f:f.write(new)
print(str(target))
