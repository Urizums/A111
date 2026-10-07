from independent_audit import OUT,EXEC
from run_receipt import run
import json,hashlib,fitz
root=OUT/'zip-sandbox';src=root/'runs/R19/levels/L1/execution-v2'
receipts=[]
for name in ['make_paper','render_paper']:
    r=run('zip-'+name,['py','-3.12','-X','utf8','-B',str(src/f'src/{name}.py')],root,120);receipts.append(r)
    if r['exit_code']!=0:break
rows=[]
for p in [EXEC/'paper/paper.md']+list((EXEC/'figures').glob('*.png')):
    q=src/p.relative_to(EXEC);rows.append({'relative':p.relative_to(EXEC).as_posix(),'identical_sha256':q.is_file() and hashlib.sha256(q.read_bytes()).hexdigest()==hashlib.sha256(p.read_bytes()).hexdigest()})
frozen=fitz.open(EXEC/'paper/paper.pdf');rebuilt=fitz.open(src/'paper/paper.pdf')
texts_match=len(frozen)==len(rebuilt) and all(a.get_text()==b.get_text() for a,b in zip(frozen,rebuilt))
pixels_match=len(frozen)==len(rebuilt) and all(a.get_pixmap().samples==b.get_pixmap().samples for a,b in zip(frozen,rebuilt))
result={'receipts':receipts,'paper_and_figure_payloads':rows,'all_payloads_identical':all(r['identical_sha256'] for r in rows),'pdf_page_count':len(rebuilt),'pdf_page_texts_match':texts_match,'pdf_raster_pixels_match':pixels_match,'pdf_binary_identity_required':False,'scope':'original ZIP scripts in new extraction; original metadata timestamp can differ'}
(OUT/'zip-paper-rebuild-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['receipts','paper_and_figure_payloads']},ensure_ascii=False))
