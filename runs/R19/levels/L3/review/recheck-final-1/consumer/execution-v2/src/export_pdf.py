"""Render revised manuscripts only. No numerical solver or old-domain writes."""
from pathlib import Path
import html, re, json, hashlib, datetime, time
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.enums import TA_CENTER

V2=Path(__file__).resolve().parents[1]
FONTS={'L3Chinese':'C:/Windows/Fonts/msyh.ttc','L3Symbols':'C:/Windows/Fonts/seguisym.ttf'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def register():
    for name,p in FONTS.items():pdfmetrics.registerFont(TTFont(name,p,subfontIndex=0))
    pdfmetrics.registerFontFamily('CN',normal='L3Chinese')
def font_for(ch):
    for name in FONTS:
        if ord(ch) in pdfmetrics.getFont(name).face.charToGlyph:return name
    raise ValueError(f'No glyph for U+{ord(ch):04X} {ch!r}')
def marked(s):
    s=s.replace('**','')
    groups=[];last=None
    for ch in s:
        name=font_for(ch)
        if name==last:groups[-1][1]+=ch
        else:groups.append([name,ch]);last=name
    return ''.join(f'<font name="{name}">{html.escape(t)}</font>' for name,t in groups)
def blocks(md):
    lines=md.read_text(encoding='utf-8').splitlines();out=[];i=0
    while i<len(lines):
        s=lines[i].strip();i+=1
        if not s:continue
        if s.startswith('```'):
            r=[]
            while i<len(lines) and not lines[i].startswith('```'):r.append(lines[i]);i+=1
            i+=1;out.append(('code',r));continue
        if s.startswith('|'):
            rows=[]
            while True:
                cells=[x.strip() for x in s.strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+',x) for x in cells):rows.append(cells)
                if i>=len(lines) or not lines[i].strip().startswith('|'):break
                s=lines[i].strip();i+=1
            out.append(('table',rows));continue
        m=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',s)
        if m:out.append(('image',m.groups()));continue
        m=re.match(r'^(#{1,3}) (.*)$',s)
        if m:out.append(('h'+str(len(m[1])),m[2]));continue
        out.append(('text',s))
    return out
def displayed_units(md):
    result=[]
    for kind,data in blocks(md):
        if kind=='table':result.extend(c for row in data for c in row)
        elif kind=='code':result.extend(data)
        elif kind=='image':result.append(data[0])
        else:result.append(data)
    return result
def export(md,pdf):
    width=A4[0]-112
    styles={
        'text':ParagraphStyle('text',fontName='L3Chinese',fontSize=10.1,leading=16,spaceAfter=7,wordWrap='CJK'),
        'h1':ParagraphStyle('h1',fontName='L3Chinese',fontSize=17,leading=25,spaceAfter=13,alignment=TA_CENTER),
        'h2':ParagraphStyle('h2',fontName='L3Chinese',fontSize=13.5,leading=21,spaceBefore=11,spaceAfter=8,keepWithNext=True),
        'h3':ParagraphStyle('h3',fontName='L3Chinese',fontSize=11,leading=18,spaceBefore=9,spaceAfter=7,keepWithNext=True),
        'small':ParagraphStyle('small',fontName='L3Chinese',fontSize=8,leading=12,spaceAfter=0,wordWrap='CJK'),
        'code':ParagraphStyle('code',fontName='L3Chinese',fontSize=9,leading=14,spaceAfter=8,wordWrap='CJK',backColor=colors.HexColor('#f4f6f8'),borderPadding=6),
    }
    p=lambda s,k='text':Paragraph(marked(s),styles[k])
    flow=[]
    for kind,data in blocks(md):
        if kind=='code':flow.append(Paragraph('<br/>'.join(marked(s) for s in data),styles['code']));continue
        if kind=='table':
            cols=len(data[0])
            if cols==7:
                if '尺寸/cm' in data[0]:ws=[36,41,86,49,42,61,88]
                elif data[0][0]=='任务':ws=[69,87,47,61,78,78,63]
                else:ws=[131,40,40,42,64,82,84]
                ws=[x*width/sum(ws) for x in ws]
            elif cols==4:ws=[100,175,95,113];ws=[x*width/sum(ws) for x in ws]
            else:ws=[width/cols]*cols
            tb=Table([[p(c,'small') for c in row] for row in data],colWidths=ws,repeatRows=1,hAlign='CENTER')
            tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef4')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#aab4be')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
            flow.extend([tb,Spacer(1,9)]);continue
        if kind=='image':
            im=Image(str(md.parent/data[1]));scale=min(width/im.imageWidth,285/im.imageHeight)
            im.drawWidth=im.imageWidth*scale;im.drawHeight=im.imageHeight*scale
            flow.extend([im,p(data[0],'small'),Spacer(1,9)]);continue
        flow.append(p(data,kind))
    def footer(c,d):
        c.setFont('L3Chinese',8);c.setFillColor(colors.HexColor('#666666'))
        c.drawString(56,28,'L3 知情修订 · 静态条件可行方案 · 全局最优未证')
        c.drawRightString(A4[0]-56,28,str(d.page))
    SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=45,bottomMargin=45,title=blocks(md)[0][1],author='R19-L3 offline producer informed revision').build(flow,onFirstPage=footer,onLaterPages=footer)
def main():
    t=time.perf_counter();register();audit={}
    for name in ['paper','technical_report']:
        md=V2/(name+'.md');pdf=V2/(name+'.pdf')
        units=displayed_units(md);chars=sorted(set(''.join(units)))
        glyphs=[{'character':c,'codepoint':f'U+{ord(c):04X}','font':font_for(c),'glyph':pdfmetrics.getFont(font_for(c)).face.charToGlyph[ord(c)]} for c in chars]
        export(md,pdf)
        audit[name]={'md_sha256':sha(md),'pdf_sha256':sha(pdf),'display_units':len(units),'unique_characters':len(chars),'glyph_mapping':glyphs,'unsupported_characters':[]}
    save(V2/'logs/pdf_export.json',{'utc':datetime.datetime.now(datetime.UTC).isoformat(),'seconds':time.perf_counter()-t,'fonts':{n:{'path':p,'sha256':sha(p)} for n,p in FONTS.items()},'audit':audit,'numerical_solver_calls':0})
    print(json.dumps({k:{'display_units':v['display_units'],'unique_characters':v['unique_characters'],'unsupported_characters':v['unsupported_characters']} for k,v in audit.items()},ensure_ascii=False))
if __name__=='__main__':main()
