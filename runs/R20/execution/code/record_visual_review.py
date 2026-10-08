"""Record the executor's already completed native-image review; compare final media to clean rerun."""
from pathlib import Path
import hashlib,json
from pypdf import PdfReader

E=Path(__file__).resolve().parent.parent; D=E/'delivery'; C=E/'clean_rerun'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
observations={1:'题名、摘要、单位符号表及假设完整可读；数字与最终表一致。',2:'口径、公式、逐原点训练表和天气/促销解释可读；不再有孤立第3节标题。',3:'第3节与需求曲线同页；星期、商品、门店图轴和图注清楚；节假日局限完整。',4:'岭目标与169列模型方程无截断；时间分割、选择表和解释完整。',5:'不确定性方法、83日来源、保留表和步长图可读；88.62%与真结果一致。',6:'商品误差图及失效解释、原损失、双约束、边际整数式完整；L_sk已定义。',7:'无约束分位数、求解证据和损失分项解释可读；完整14日日计划表无裁切。',8:'未来资源和商品分配图清楚；商品表单位及金额、件量一致，正文正常跨页。',9:'假期和需求压力、资源压力图及两表清楚；已明确压力是假设、非观测。',10:'容量/预算取舍、真实节日加成、复现及作者检查和结论完整；每日件量用语已修正。',11:'原来源与复现定位表清楚；页码11，正文无占位文字。'}
pages=sorted((D/'paper').glob('page-*.png')); reader=PdfReader(D/'paper/paper.pdf')
assert len(pages)==len(reader.pages)==len(observations)
comparisons=[]
for p in [D/'paper/paper.md',D/'paper/paper.pdf']+sorted((D/'figures').glob('*.png')):
    q=C/p.relative_to(D); assert q.exists() and sha(p)==sha(q),(p,q)
    comparisons.append({'path':p.relative_to(D).as_posix(),'sha256':sha(p),'identical_to_clean_rerun':True})
report={'schema':'freshfood-author-visual-review/1','method':'executor actually viewed every rendered PNG using view_image; this script records those already-made observations and hashes, it is not an automated visual verdict','scope':'author final visual review, not independent acceptance','all_pages_actually_viewed':True,'pdf_sha256':sha(D/'paper/paper.pdf'),'render_receipt':'evidence/016-render-delivery-pages.json','pages':[{'page':i,'path':p.relative_to(E).as_posix(),'sha256':sha(p),'observation':observations[i],'verdict':'pass'} for i,p in enumerate(pages,1)],'source_pdf_figures_clean_rerun_hash_comparison':comparisons,'verdict':'pass','limitations':['visual QA covers this final PDF version and seven included analysis figures plus formulas','does not validate future realized demand or independent receiving acceptance']}
(E/'evidence/visual_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'all_pages_viewed':len(pages),'same_source_pdf_media_files':len(comparisons),'pdf_sha256':report['pdf_sha256'],'verdict':'pass author visual scope'},ensure_ascii=False,indent=2))
