"""Producer receiving QA: exact displayed text, science tokens and every rendered page."""
from pathlib import Path
import json,re,datetime,hashlib
import fitz
from PIL import Image,ImageOps,ImageDraw
from export_pdf import displayed_units
V2=Path(__file__).resolve().parents[1]
def norm(s):return re.sub(r'\s+','',s.replace('**',''))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    out=V2/'qa/pdf';out.mkdir(exist_ok=False);results={}
    for name in ['paper','technical_report']:
        md=V2/(name+'.md');pdf=V2/(name+'.pdf');doc=fitz.open(pdf)
        dest=out/name;dest.mkdir();texts=[];bounds=[];fonts=[];pages=[]
        for n,page in enumerate(doc,1):
            txt=page.get_text();texts.append(txt)
            (dest/f'page-{n:02d}.txt').write_text(txt,encoding='utf-8')
            page.get_pixmap(matrix=fitz.Matrix(1.7,1.7),alpha=False).save(dest/f'page-{n:02d}.png')
            for b in page.get_text('dict')['blocks']:
                for line in b.get('lines',[]):
                    for s in line['spans']:
                        x0,y0,x1,y1=s['bbox']
                        if x0<43 or x1>page.rect.width-43 or y0<25 or y1>page.rect.height-15:bounds.append({'page':n,'bbox':s['bbox'],'text':s['text']})
                        fonts.append({'page':n,'font':s['font'],'text':s['text'],'bbox':s['bbox']})
            pages.append({'page':n,'width':page.rect.width,'height':page.rect.height,'characters':len(txt),'image':str(dest/f'page-{n:02d}.png')})
        # Remove generated footers before matching paragraphs which cross page boundaries.
        body=[]
        for txt in texts:
            body.append(re.sub(r'L3 知情修订 · 静态条件可行方案 · 全局最优未证\s*\d+\s*$','',txt))
        joined=norm(''.join(body));units=displayed_units(md)
        unit_checks=[{'unit':i,'text':s,'present_in_pdf':norm(s) in joined} for i,s in enumerate(units)]
        science=[]
        for i,line in enumerate(md.read_text(encoding='utf-8').splitlines(),1):
            for m in re.finditer(r'kg·m⁻³|kg/m²|(?:cm|m)[²³]|O\([^\n)]*\)|α(?:=[0-9.,、]+)?|z\+h≤H−3',line):
                token=m[0];matching=[j+1 for j,txt in enumerate(texts) if norm(token) in norm(txt)]
                science.append({'md_line':i,'token':token,'md_excerpt':line,'pdf_pages':matching,'exact_unicode_present':bool(matching)})
        missing=[r for r in unit_checks if not r['present_in_pdf']]
        assert not missing,(name,missing)
        assert not bounds,(name,bounds)
        assert all(r['exact_unicode_present'] for r in science),(name,science)
        # Three pages per contact sheet; full-size files retained for actual visual inspection.
        for start in range(0,len(pages),3):
            thumbs=[]
            for p in pages[start:start+3]:
                im=Image.open(p['image']).convert('RGB');im.thumbnail((500,720));tile=Image.new('RGB',(520,750),'#d9dfe4');tile.paste(im,((520-im.width)//2,22));ImageDraw.Draw(tile).text((10,5),f'{name} page {p["page"]}',fill='black');thumbs.append(tile)
            sheet=Image.new('RGB',(520*len(thumbs),750),'white')
            for j,tile in enumerate(thumbs):sheet.paste(tile,(520*j,0))
            sheet.save(dest/f'contact-{start+1:02d}.png')
        # Enlargements of every old-failure notation location.
        crops=[]
        for n,page in enumerate(doc,1):
            for token in ['kg·m⁻³','kg/m²','m³','m²','O(R²)','O(n_k²)']:
                for j,rect in enumerate(page.search_for(token)):
                    box=fitz.Rect(max(0,rect.x0-75),max(0,rect.y0-12),min(page.rect.width,rect.x1+100),min(page.rect.height,rect.y1+12))
                    fn=dest/f'science-{len(crops)+1:03d}.png'
                    page.get_pixmap(matrix=fitz.Matrix(3,3),clip=box,alpha=False).save(fn)
                    crops.append({'page':n,'token':token,'bbox':list(box),'path':str(fn)})
        # Crops are also combined to inspect every occurrence efficiently, with no resampling.
        for start in range(0,len(crops),12):
            ims=[]
            for c in crops[start:start+12]:
                im=Image.open(c['path']).convert('RGB');tile=Image.new('RGB',(max(1000,im.width),im.height+24),'#e7edf2');tile.paste(im,(0,24));ImageDraw.Draw(tile).text((5,5),f'page {c["page"]} crop {Path(c["path"]).stem}',fill='black');ims.append(tile)
            sheet=Image.new('RGB',(max(im.width for im in ims),sum(im.height for im in ims)), 'white');y=0
            for im in ims:sheet.paste(im,(0,y));y+=im.height
            sheet.save(dest/f'science-contact-{start+1:03d}.png')
        results[name]={'md_sha256':sha(md),'pdf_sha256':sha(pdf),'pages':pages,'whole_display_units_checked':len(unit_checks),'missing_display_units':missing,'science_occurrences':science,'science_crops':crops,'outside_page_spans':bounds,'unit_checks':unit_checks,'font_spans':fonts}
    save(V2/'qa/pdf_semantic_checks.json',{'producer_self_check':True,'utc':datetime.datetime.now(datetime.UTC).isoformat(),'scope':'Every displayed paragraph, heading, code line and table cell; every scientific token; every page rendered. Actual visual inspection recorded separately.','documents':results})
    print(json.dumps({n:{'pages':len(r['pages']),'display_units_checked':r['whole_display_units_checked'],'science_occurrences':len(r['science_occurrences']),'missing':len(r['missing_display_units']),'science_crops':len(r['science_crops'])} for n,r in results.items()}))
if __name__=='__main__':main()
