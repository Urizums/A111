import fitz,json
from PIL import Image,ImageDraw
from pathlib import Path
H=Path(__file__).resolve().parent;E=H.parents[5]/'runs/R19/levels/L3/execution';out=H/'pdf_visual';out.mkdir(exist_ok=True)
info=[]
for name in ['paper','technical_report']:
 pages=[]
 with fitz.open(E/(name+'.pdf')) as pdf:
  for i,p in enumerate(pdf):
   dest=out/f'{name}-{i+1:02d}.png';p.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(dest)
   pages.append({'page':i+1,'text':p.get_text(),'png':str(dest.relative_to(H)),'dimensions':list(p.rect),'span_bounds_outside_page':[list(s['bbox']) for b in p.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['bbox'][0]<0 or s['bbox'][1]<0 or s['bbox'][2]>p.rect.width or s['bbox'][3]>p.rect.height]})
 for n in range(0,len(pages),6):
  section=pages[n:n+6];thumbs=[]
  for p in section:
   im=Image.open(H/p['png']).convert('RGB');im.thumbnail((420,600));thumbs.append((p['page'],im))
  canvas=Image.new('RGB',(1260,630*((len(section)+2)//3)),'#dddddd');draw=ImageDraw.Draw(canvas)
  for j,(pn,im) in enumerate(thumbs):x=(j%3)*420;y=(j//3)*630;canvas.paste(im,(x,y+25));draw.text((x+10,y+5),f'{name} page {pn}',fill='black')
  canvas.save(out/f'{name}-contact-{n//6+1}.png')
 info.append({'name':name,'pages':pages})
(out/'pdf-inspection.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print([(x['name'],len(x['pages']),sum(len(p['span_bounds_outside_page']) for p in x['pages'])) for x in info])
