"""Chinese readable practice-paper PDF; render every page for QA."""
from pathlib import Path
import re,textwrap,json,html
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,Preformatted,KeepTogether
import fitz
from PIL import Image as PILImage,ImageDraw
from solve import ROOT

def render():
    pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/simsun.ttc',subfontIndex=0))
    pdfmetrics.registerFont(TTFont('CNHead','C:/Windows/Fonts/simhei.ttf'))
    styles={'body':ParagraphStyle('body',fontName='CN',fontSize=10.3,leading=17.5,spaceAfter=8,wordWrap='CJK',alignment=TA_JUSTIFY),
      'h1':ParagraphStyle('h1',fontName='CNHead',fontSize=20,leading=28,alignment=TA_CENTER,spaceBefore=8,spaceAfter=18,wordWrap='CJK'),
      'h2':ParagraphStyle('h2',fontName='CNHead',fontSize=14,leading=21,spaceBefore=15,spaceAfter=10,keepWithNext=True,wordWrap='CJK'),
      'h3':ParagraphStyle('h3',fontName='CNHead',fontSize=11.5,leading=18,spaceBefore=12,spaceAfter=7,keepWithNext=True,wordWrap='CJK'),
      'cell':ParagraphStyle('cell',fontName='CN',fontSize=8.1,leading=11.8,wordWrap='CJK'),
      'code':ParagraphStyle('code',fontName='CN',fontSize=8.2,leading=12,spaceBefore=5,spaceAfter=8,wordWrap='CJK'),
      'caption':ParagraphStyle('caption',fontName='CN',fontSize=9,leading=14,alignment=TA_CENTER,spaceAfter=10,wordWrap='CJK')}
    lines=(ROOT/'paper/paper.md').read_text(encoding='utf8').splitlines();story=[];i=0;width=A4[0]-96
    def para(s,style='body'):
      s=s.replace('10⁻⁷','1e-7').replace('⁻³','^-3').replace('²','^2').replace('³','^3')
      s=html.escape(s).replace('**','');return Paragraph(s,styles[style])
    while i<len(lines):
      line=lines[i].strip()
      if not line:i+=1;continue
      if line.startswith('```'):
        content=[];i+=1
        while i<len(lines) and not lines[i].startswith('```'):content+=textwrap.wrap(lines[i],width=97,break_long_words=False,replace_whitespace=False) or [''];i+=1
        for c in content:story.append(para(c,'code'))
        i+=1;continue
      if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
          values=[x.strip() for x in lines[i].strip().strip('|').split('|')]
          if not all(re.fullmatch(r':?-+:?',x) for x in values):rows.append([para(x,'cell') for x in values])
          i+=1
        n=len(rows[0]);widths=[width/n]*n
        if rows and n==8 and '情景' in ''.join(x.text for x in rows[0]):widths=[130]+[(width-130)/7]*7
        elif n==6 and '计时口径' in ''.join(x.text for x in rows[0]):widths=[35,135,40,40,65,width-315]
        t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#637b8d')),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d8e0e5')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([t,Spacer(1,10)]);continue
      m=re.match(r'!\[(.*?)\]\((.*?)\)',line)
      if m:
        p=(ROOT/'paper'/m.group(2)).resolve();im=PILImage.open(p);h=width*im.height/im.width;story.extend([Image(str(p),width=width,height=h),para(m.group(1),'caption')]);i+=1;continue
      if line.startswith('# '):story.append(para(line[2:],'h1'));i+=1;continue
      if line.startswith('## '):story.append(para(line[3:],'h2'));i+=1;continue
      if line.startswith('### '):story.append(para(line[4:],'h3'));i+=1;continue
      p=[]
      while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','```','![')):p.append(lines[i].strip());i+=1
      story.append(para(' '.join(p)))
    def page(c,doc):
      c.setFont('CN',8);c.setFillColor(colors.HexColor('#657784'));c.drawString(48,A4[1]-28,'三维装箱优化 · 官方D题离线练习稿');c.drawRightString(A4[0]-48,24,str(doc.page));c.setStrokeColor(colors.HexColor('#dce4e9'));c.line(48,35,A4[0]-48,35)
    pdf=ROOT/'paper/paper.pdf';SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=47,bottomMargin=48,title='全底面支撑与累计传力约束下的多场景三维装箱优化',author='离线建模执行').build(story,onFirstPage=page,onLaterPages=page)
    d=fitz.open(pdf);qa=ROOT/'paper/qa';qa.mkdir(exist_ok=True);items=[]
    for j,p in enumerate(d):
      pix=p.get_pixmap(matrix=fitz.Matrix(1.25,1.25),alpha=False);path=qa/f'page_{j+1:02d}.png';pix.save(path);items.append(path)
    for start in range(0,len(items),12):
      sheet=PILImage.new('RGB',(1000,390*3),'#e3e7eb');draw=ImageDraw.Draw(sheet)
      for k,p in enumerate(items[start:start+12]):
        im=PILImage.open(p);im.thumbnail((240,350));x=(k%4)*250+5;y=(k//4)*390+25;sheet.paste(im,(x,y));draw.text((x,y-18),f'Page {start+k+1}',fill='black')
      sheet.save(qa/f'contact_{start//12+1}.png')
    bad=[]
    for k,p in enumerate(d):
      for b in p.get_text('blocks'):
        if b[0]<40 or b[2]>A4[0]-40 or b[1]<10 or b[3]>A4[1]-10:bad.append({'page':k+1,'bbox':b[:4],'text':b[4][:50]})
    report={'pages':len(d),'all_pages_rendered':True,'out_of_page_text_blocks':bad,'visual_review':'pending; contact sheets plus full-resolution selected pages','embedded_fonts':['SimSun','SimHei'],'practice_format':True};(qa/'render_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':render()
