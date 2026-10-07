from independent_audit import OUT,ROOT,EXEC
from run_receipt import run
from pathlib import Path
import json,zipfile,hashlib,fitz,datetime
from PIL import Image,ImageDraw
def sha(b):return hashlib.sha256(b).hexdigest()
dest=OUT/'zip-sandbox'
assert not dest.exists(),'new extraction required'
dest.mkdir();records=[]
with zipfile.ZipFile(EXEC/'algorithm_bundle.zip') as z:
    for zi in z.infolist():
        p=(dest/zi.filename).resolve();assert p.is_relative_to(dest.resolve()) and not Path(zi.filename).is_absolute()
        if zi.is_dir():continue
        b=z.read(zi);source=ROOT/zi.filename
        records.append({'entry':zi.filename,'zip_sha256':sha(b),'frozen_sha256':sha(source.read_bytes()) if source.is_file() else None,'matches':source.is_file() and sha(b)==sha(source.read_bytes())})
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
manifest=json.loads((dest/'runs/R19/levels/L1/execution-v2/bundle_manifest.json').read_text(encoding='utf-8'))
payload=[{'entry':name,'match':(dest/name).is_file() and sha((dest/name).read_bytes())==digest} for name,digest in manifest['payload_sha256'].items()]
(OUT/'zip-content-audit.json').write_text(json.dumps({'entries':records,'all_entries_match_frozen':all(r['matches'] for r in records),'manifest_payload_matches':all(r['match'] for r in payload),'manifest_payload_checks':payload,'archive_bytes':(EXEC/'algorithm_bundle.zip').stat().st_size,'archive_sha256':sha((EXEC/'algorithm_bundle.zip').read_bytes())},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'zip_entries':len(records),'all_match_frozen':all(r['matches'] for r in records),'manifest_matches':all(r['match'] for r in payload)},ensure_ascii=False))
r=run('zip-raw-reproduce',['py','-3.12','-X','utf8','-B',str(dest/'runs/R19/levels/L1/execution-v2/src/reproduce.py'),'--out',str(OUT/'zip-raw-rerun')],dest,180)
print(json.dumps(r,ensure_ascii=False))
pages=OUT/'paper-pages';pages.mkdir(exist_ok=False);doc=fitz.open(EXEC/'paper/paper.pdf');texts=[];images=[]
for k,p in enumerate(doc):
    pix=p.get_pixmap(matrix=fitz.Matrix(1.35,1.35),alpha=False);fn=pages/f'page-{k+1:02d}.png';pix.save(fn)
    im=Image.open(fn).convert('RGB');im.thumbnail((420,600));images.append(im)
    blocks=p.get_text('blocks');outside=[list(b[:4]) for b in blocks if b[0]<-1 or b[1]<-1 or b[2]>p.rect.width+1 or b[3]>p.rect.height+1]
    texts.append({'page':k+1,'text':p.get_text(),'rect':list(p.rect),'out_of_page_text_blocks':outside})
for start in range(0,len(images),4):
    contact=Image.new('RGB',(840,1240),'#cccccc');draw=ImageDraw.Draw(contact)
    for j,im in enumerate(images[start:start+4]):
        x=j%2*420;y=j//2*620;contact.paste(im,(x,y+20));draw.text((x+8,y+2),f'PAGE {start+j+1}',fill='black')
    contact.save(pages/f'contact-{start//4+1}.png')
(OUT/'paper-pdf-extraction.json').write_text(json.dumps({'pages':texts,'page_count':len(doc),'no_out_of_page_text_blocks':all(not p['out_of_page_text_blocks'] for p in texts),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False,indent=2),encoding='utf-8')
print('pdf_pages',len(doc),'all_text_blocks_inside',all(not p['out_of_page_text_blocks'] for p in texts))
