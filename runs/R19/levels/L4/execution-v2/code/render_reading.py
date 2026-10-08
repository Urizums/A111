from pathlib import Path
import fitz,json
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parents[1];out=E/'checks/reading';out.mkdir(exist_ok=True);records=[]
for name in ['paper','enterprise_report']:
    doc=fitz.open(E/'paper'/(name+'.pdf'));thumbs=[];pages=[]
    for pi,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(1.3,1.3));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.save(out/f'{name}_{pi+1:02d}.png')
        text=page.get_text();outside=[]
        for block in page.get_text('dict')['blocks']:
            if block['type']!=0:continue
            x0,y0,x1,y1=block['bbox']
            if x0<40 or x1>page.rect.width-39 or y0<25 or y1>page.rect.height-12:outside.append(block['bbox'])
        pages.append({'page':pi+1,'text_characters':len(text),'outside_safe_bounds':outside,'width_pt':page.rect.width,'height_pt':page.rect.height})
        thumb=im.copy();thumb.thumbnail((390,552));tile=Image.new('RGB',(404,579),'#eef1f4');tile.paste(thumb,((404-thumb.width)//2,21));ImageDraw.Draw(tile).text((12,5),f'{name} p{pi+1}',fill='black');thumbs.append(tile)
    for start in range(0,len(thumbs),6):
        sub=thumbs[start:start+6];sheet=Image.new('RGB',(808,579*((len(sub)+1)//2)),'#dce2e8')
        for n,im in enumerate(sub):sheet.paste(im,((n%2)*404,(n//2)*579))
        sheet.save(out/f'{name}_contact_{start//6+1:02d}.png')
    records.append({'file':f'paper/{name}.pdf','pages':pages,'embedded_fonts':[f[3] for f in doc[0].get_fonts()],'all_pages_rendered':True,'no_text_outside_safe_bounds':all(not p['outside_safe_bounds'] for p in pages)})
(E/'checks/reading_render.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8');print(records)
