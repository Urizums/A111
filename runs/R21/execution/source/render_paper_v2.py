from pathlib import Path
import argparse,subprocess,json,hashlib,shutil
from pypdf import PdfReader
from PIL import Image,ImageOps,ImageDraw
ap=argparse.ArgumentParser();ap.add_argument('--paper',required=True);ap.add_argument('--newout',required=True);a=ap.parse_args();paper=Path(a.paper);out=Path(a.newout);out.mkdir(parents=True,exist_ok=False)
renderer=shutil.which('pdftoppm');assert renderer
subprocess.run([renderer,'-r','125','-png',str(paper),str(out/'page')],check=True)
pages=sorted(out.glob('page-*.png'));count=len(PdfReader(paper).pages);assert len(pages)==count
rows=[]
for j,p in enumerate(pages,1):
    im=Image.open(p);rows.append({'page':j,'image':str(p),'pixels':list(im.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for start in range(0,len(pages),4):
    sheet=Image.new('RGB',(920,1320),'#dce2e6');d=ImageDraw.Draw(sheet)
    for j,p in enumerate(pages[start:start+4]):
        im=Image.open(p).convert('RGB');im.thumbnail((440,625));x=10+(j%2)*460;y=25+(j//2)*660;sheet.paste(im,(x,y));d.text((x,y-18),f'Page {start+j+1}',fill='black')
    sheet.save(out/f'contact-{start//4+1}.png')
with (out/'render_manifest.json').open('x',encoding='utf-8') as f:json.dump({'renderer':renderer,'pdf_sha256':hashlib.sha256(paper.read_bytes()).hexdigest(),'dpi':125,'pages':rows,'visual_status':'awaiting actual image inspection'},f,ensure_ascii=False,indent=2)
print(json.dumps({'pages_rendered':len(pages),'renderer':renderer,'images':rows},ensure_ascii=False,indent=2))
