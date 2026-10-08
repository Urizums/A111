import fitz,json
from PIL import Image,ImageDraw
from solver import E,save
out=E/'pdf_qa';out.mkdir(exist_ok=True);receipts=[]
for name in ['paper','technical_report']:
 d=fitz.open(E/(name+'.pdf'));thumbs=[]
 for i,p in enumerate(d):
  pix=p.get_pixmap(matrix=fitz.Matrix(1.1,1.1));path=out/f'{name}_page_{i+1:02d}.png';pix.save(path);im=Image.open(path).convert('RGB');im.thumbnail((248,351));thumbs.append(im)
 sheet=Image.new('RGB',(4*260,((len(thumbs)+3)//4)*380),'#bbbbbb');draw=ImageDraw.Draw(sheet)
 for i,im in enumerate(thumbs):
  x=(i%4)*260;y=(i//4)*380;sheet.paste(im,(x+6,y+20));draw.text((x+6,y+4),name+' page '+str(i+1),fill='black')
 sheet.save(out/(name+'_contact.png'));receipts.append({'file':name+'.pdf','pages':len(d),'all_pages_rendered':True,'characters':sum(len(p.get_text()) for p in d),'empty_pages':[i+1 for i,p in enumerate(d) if len(p.get_text().strip())<20]})
save(out/'render_receipt.json',receipts);print(receipts)
