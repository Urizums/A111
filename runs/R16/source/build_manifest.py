from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
root=Path('runs/R16/source')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
files=[]
for p in sorted(root.rglob('*')):
    if not p.is_file() or p.name in {'source-manifest.json','fetch_official.py','list_archives.py','extract_official.py','inspect_workbooks.py','inspect_d_docx.py'}:
        continue
    files.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
manifest={
 'schema':'mathorcup-official-source-packet/1',
 'created_utc':'2026-10-06T17:46:36Z',
 'retrieved_utc':[
  {'url':'https://www.mathorcup.org/uploads/files/20260417/1776438403640865.zip','file':'D_corrected.zip','http_status':200,'content_type':'application/zip','content_length_header':156307,'bytes':156307,'sha256':'d417f99dd790d576b89f9c7b8b0fd7ba22ff324414884f801c07431b0e2a039a','retrieved_utc':'2026-10-06T17:39:33.868666+00:00'},
  {'url':'https://mathorcup.org/uploads/files/20260417/1776383723989262.zip','file':'all_questions.zip','http_status':200,'content_type':'application/zip','content_length_header':2755960,'bytes':2755960,'sha256':'950ea755182a0f4d6ba32fa9c904817a042ff367f9f2bcf7512dc6e7fe7621d8','retrieved_utc':'2026-10-06T17:39:34.519720+00:00'}],
 'official_pages':[
  {'url':'https://mathorcup.org/detail/2487','title':'〖赛题发布〗2026年第十六届MathorCup数学应用挑战赛','date':'2026-04-17','facts':'官网公告竞赛于2026-04-17 08:00至2026-04-21 09:00举行；本科组可选题范围因院校类型而异；附件为2026年第十六届MathorCup数学应用挑战赛赛题.zip。'},
  {'url':'https://www.mathorcup.org/detail/2488','title':'〖D赛题信息修改通知〗2026年第十六届MathorCup数学应用挑战赛','date':'2026-04-17','facts':'公告勘误：题面将货物“满载率（货物占用空间与整个空间之比）”改为“满容率”；问题1目标句改为单车同时达到满容率与满载率最大化；附件1货物数量列改为原先10倍；官网附最新D题ZIP。'}],
 'recommended_question':{'id':'D','title':'多场景、多目标货物运输装箱策略优化','basis':'官方修订题面与修订ZIP、任务数据附件及验证数据附件均完整取得；问题和附件构成封闭的物流装箱应用任务，题面要求根据附件数据计算，并有附件2供更大规模测试。适合由下一阶段在现有CPU/Python环境开展完整离线试解。实际求解可行性、耗时与质量未测。'},
 'files':files,
 'retrieval_scope':'仅官方域名 mathorcup.org、www.mathorcup.org、files.mathorcup.org；未获取或阅读任何参赛/获奖解法、论文、社区答案，也未访问9月国赛材料。',
 'failures_preserved':[
  {'attempt':'inventory command 1','error':'本地归档清单的一行式表达式引用未定义名称 n，Python抛出 NameError；未访问外部资源、未写出原始附件。后续以受限脚本成功生成 inventory-receipt.json。原命令/错误摘要保存在 attempt-01-inventory-error.txt。'},
  {'attempt':'archive extraction 1','receipt':'extract-receipt.json','error':'首次解压在完成首个成员写入后，打印路径时对相对 root 调用 Path.relative_to(绝对路径)，触发 ValueError；原错误回执保留。一次修订脚本后解压成功，回执 extract-receipt-retry.json。'}],
 'execution_metadata':{'model':None,'tokens':None,'cost':None,'note':'Unavailable; recorded as null.'},
 'command_receipts':['fetch-receipt.json','inventory-receipt.json','extract-receipt.json','extract-receipt-retry.json','workbook-receipt.json','docx-receipt.json']}
(root/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
