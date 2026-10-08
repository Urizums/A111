"""Build the Chinese technical paper PDF from its editable Markdown source."""
import argparse, html, re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, KeepTogether

class LoadDiagram(Flowable):
    def __init__(self):
        super().__init__(); self.width=470; self.height=234
    def draw(self):
        c=self.canv; c.setFont('Chinese',9)
        ox,oy,scale=80,22,58
        c.setStrokeColor(colors.HexColor('#566778')); c.setLineWidth(1)
        c.rect(ox,oy,2.4*scale,3.2*scale)
        c.setDash(3,3); c.line(ox,oy+3.1*scale,ox+2.4*scale,oy+3.1*scale); c.setDash()
        for label,x,z,fill in [('S1',0,0,'#DBEAFE'),('F1',0,1,'#FDE4D2'),('S2',1,0,'#DBEAFE'),('S3',1,1,'#DBEAFE')]:
            c.setFillColor(colors.HexColor(fill)); c.rect(ox+x*scale,oy+z*scale,scale,scale,fill=1)
            c.setFillColor(colors.HexColor('#132C46')); c.drawCentredString(ox+(x+.5)*scale,oy+(z+.5)*scale,label)
        c.setFillColor(colors.HexColor('#132C46'))
        c.drawString(ox-35,oy-4,'z=0'); c.drawString(ox-35,oy+scale-4,'z=1'); c.drawString(ox-35,oy+2*scale-4,'z=2')
        c.drawString(ox,oy-17,'x=0'); c.drawString(ox+scale-8,oy-17,'x=1'); c.drawString(ox+2*scale-8,oy-17,'x=2')
        c.drawString(ox+2.4*scale+15,oy+3.2*scale-3,'车内高 3.2 m')
        c.drawString(ox+2.4*scale+15,oy+3.1*scale-19,'虚线：有效高 3.1 m')
        c.drawString(ox+2.4*scale+15,oy+2*scale-3,'货物最高顶面 2 m')
        c.drawString(ox+2.4*scale+15,oy+1.5*scale,'实际顶部间隙 1.2 m')
        c.drawString(ox+2.4*scale+15,oy+scale,'所有箱体 y∈[0,1] m')
        c.drawString(ox+2.4*scale+15,oy+scale-17,'图示是 x-z 截面')
        c.drawString(ox+2.4*scale+15,oy+10,'边框表示车厢内部')

def build(source,output,font):
    pdfmetrics.registerFont(TTFont('Chinese',font))
    text=Path(source).read_text(encoding='utf-8-sig')
    cmap=pdfmetrics.getFont('Chinese').face.charToGlyph
    missing=sorted(set(c for c in text if ord(c)>32 and ord(c) not in cmap))
    if missing: raise ValueError(f'Font lacks source glyphs: {missing}')
    styles={
        'body':ParagraphStyle('Body',fontName='Chinese',fontSize=10.3,leading=16,wordWrap='CJK',spaceAfter=7),
        'title':ParagraphStyle('Title',fontName='Chinese',fontSize=18.5,leading=27,wordWrap='CJK',alignment=TA_CENTER,spaceAfter=18),
        'h1':ParagraphStyle('H1',fontName='Chinese',fontSize=14,leading=21,wordWrap='CJK',spaceBefore=12,spaceAfter=9,keepWithNext=True,textColor=colors.HexColor('#123451')),
        'h2':ParagraphStyle('H2',fontName='Chinese',fontSize=11.7,leading=18,wordWrap='CJK',spaceBefore=8,spaceAfter=6,keepWithNext=True,textColor=colors.HexColor('#123451')),
        'table':ParagraphStyle('Cell',fontName='Chinese',fontSize=8.5,leading=12,wordWrap='CJK'),
        'th':ParagraphStyle('Header',fontName='Chinese',fontSize=8.5,leading=12,wordWrap='CJK',textColor=colors.white),
        'code':ParagraphStyle('Code',fontName='Chinese',fontSize=8.4,leading=12.4,wordWrap='CJK',backColor=colors.HexColor('#F1F5F9'),borderPadding=7,spaceAfter=7)
    }
    story=[]; lines=text.splitlines(); pos=0
    def para(s,kind='body'):
        return Paragraph(html.escape(s).replace('  ','&nbsp;&nbsp;'),styles[kind])
    width=A4[0]-104
    while pos<len(lines):
        line=lines[pos].strip()
        if not line: pos+=1; continue
        if line.startswith('```'):
            code=[]; pos+=1
            while pos<len(lines) and not lines[pos].strip().startswith('```'):
                code.append(lines[pos]); pos+=1
            story.append(Paragraph('<br/>'.join(html.escape(s) for s in code),styles['code'])); pos+=1; continue
        if line.startswith('|'):
            rows=[]
            while pos<len(lines) and lines[pos].strip().startswith('|'):
                cells=[s.strip() for s in lines[pos].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',s) for s in cells): rows.append(cells)
                pos+=1
            n=len(rows[0]); lengths=[max(len(row[c]) for row in rows) for c in range(n)]
            weights=[max(5,min(v,21)) for v in lengths]
            widths=[width*v/sum(weights) for v in weights]
            cells=[[para(s,'th' if ri==0 else 'table') for s in row] for ri,row in enumerate(rows)]
            table=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#123451')),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F6F8')]),
                ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#CDD6DE')),('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
                ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            story.extend([table,Spacer(1,10)]); continue
        if line.startswith('# '): story.append(para(line[2:],'title'))
        elif line.startswith('## '): story.append(para(line[3:],'h1'))
        elif line.startswith('### '): story.append(para(line[4:],'h2'))
        elif line.startswith('图 1'):
            story.append(KeepTogether([LoadDiagram(),para(line)]))
        else:
            block=[line]; pos+=1
            while pos<len(lines) and lines[pos].strip() and not lines[pos].strip().startswith(('#','|','```')):
                block.append(lines[pos].strip()); pos+=1
            story.append(Paragraph('<br/>'.join(html.escape(s) for s in block),styles['body'])); continue
        pos+=1
    def page(canvas,doc):
        canvas.saveState(); canvas.setFont('Chinese',8.2); canvas.setFillColor(colors.HexColor('#536578'))
        canvas.drawString(46,A4[1]-31,'固定方向小批次运输装箱 | 原始离线材料建模')
        canvas.drawRightString(A4[0]-46,26,f'{doc.page}')
        canvas.setStrokeColor(colors.HexColor('#CDD6DE')); canvas.line(46,40,A4[0]-46,40)
        canvas.restoreState()
    doc=SimpleDocTemplate(output,pagesize=A4,rightMargin=46,leftMargin=46,topMargin=53,bottomMargin=53,
        title='固定方向小批次运输装箱的支撑链精确枚举与可行性核验',author='本次任务生产者',subject='给定离线装箱数学建模')
    doc.build(story,onFirstPage=page,onLaterPages=page)
    print(f'PDF produced: {output}; source glyph coverage complete')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--source',required=True); p.add_argument('--output',required=True)
    p.add_argument('--font',default=str(Path(__file__).resolve().parent/'assets'/'NotoSansSC-Regular.ttf'))
    a=p.parse_args(); build(a.source,a.output,a.font)


