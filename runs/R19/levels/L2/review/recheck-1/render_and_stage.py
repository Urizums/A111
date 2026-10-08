from pathlib import Path
import fitz,json,shutil,hashlib,datetime
from run_calls import O,E,B,dump
pages=[]
for label,p in [('paper',E/'paper/paper.pdf'),('report',E/'report.pdf')]:
 texts=[];d=O/'pdf_render'/label;d.mkdir(parents=True,exist_ok=True)
 with fitz.open(p) as doc:
  for ix,page in enumerate(doc):
   png=d/f'page_{ix+1:02d}.png';page.get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(png);texts.append(page.get_text())
   bad=[list(b[:4]) for b in page.get_text('blocks') if b[0]<0 or b[1]<0 or b[2]>page.rect.width+.1 or b[3]>page.rect.height+.1]
   pages.append({'document':label,'page':ix+1,'chars':len(texts[-1]),'outside_blocks':bad,'png':png.relative_to(O).as_posix()})
 (O/(label+'-pdf-text.txt')).write_text('\n\n'.join(texts),encoding='utf-8')
dump(O/'pdf-render-audit.json',{'source':'reviewer rendering frozen source PDF directly','pages':pages,'visual_inspection':'pending'})
S=O/'delivery_staged';S.mkdir(exist_ok=True)
for sub in ('code','data','results/final'):
 shutil.copytree(E/sub,S/sub,dirs_exist_ok=False)
for sub in ('paper','figures','checks','experiments','research/comparison','history/execution/paper','history/execution/results/final'):(S/sub).mkdir(parents=True,exist_ok=True)
for rel in ('experiments/experiments.csv','research/comparison/summary.json','research/comparison/guarded_summary.json','history/execution/paper/paper.md','history/execution/results/final/summary.json'):
 shutil.copy2(E/rel,S/rel)
dump(O/'delivery-staging.json',{'source':'frozen v2 data/results and raw paired time receipts for regen; independent numbers separately recomputed','copied_code_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (S/'code').glob('*.py')},'writes':'recheck-1/delivery_staged only'})
print(json.dumps({'pages':len(pages),'outside':sum(bool(p['outside_blocks']) for p in pages),'staged':True}),flush=True)
