"""Create data-bound Chinese manuscript, figures and PDFs from checked runs."""
from main import ROOT,dump,csvwrite,readitems
import json,csv,math,collections,html,re,os,platform,time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import fitz
font=FontProperties(fname='C:/Windows/Fonts/simsun.ttc');plt.rcParams['font.family']=font.get_name();plt.rcParams['axes.unicode_minus']=False
pdfmetrics.registerFont(TTFont('Chinese','C:/Windows/Fonts/simsun.ttc',subfontIndex=0))
S=json.loads((ROOT/'results/final/summary.json').read_text(encoding='utf8')); selected=[r for r in S['runs'] if r['method']=='column_patterns_MILP'];baseline=[r for r in S['runs'] if r['method']=='equal_priority_columns'];items=readitems(ROOT/'data/items.csv');vs=json.loads((ROOT/'data/vehicles.json').read_text(encoding='utf8'));types=json.loads((ROOT/'data/types.json').read_text(encoding='utf8'))
with (ROOT/'experiments/experiments.csv').open(encoding='utf-8-sig') as f:E=list(csv.DictReader(f))
def rd(p):
 with Path(p).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
names={'q1_all_v1':'仅车型1','q1_all_v2':'仅车型2','q2_vehicles':'混合最少车','q2_cost':'混合最低成本'}
colorset={'G1':'#477dba','G2':'#74bdaa','G3':'#edaa51','G4':'#b96d91','G5':'#8f7ebd'}
def save(name):plt.tight_layout();plt.savefig(ROOT/'figures'/name,dpi=170,bbox_inches='tight');plt.close()
fig,axs=plt.subplots(1,2,figsize=(9,3.7))
for ax,v in zip(axs,vs):
 pts=[r for r in S['singles'] if v['type_id'] in r['scenario']]
 ax.plot([r['volume_utilization']*100 for r in pts],[r['weight_utilization']*100 for r in pts],'o',color='#326b98');ax.set_title(v['type_id']+' 搜索非支配集');ax.set_xlabel('名义空间利用率/%');ax.set_ylabel('载重利用率/%');ax.grid(alpha=.3)
save('single_frontier.png')
fig,axs=plt.subplots(1,3,figsize=(11.5,3.4));x=np.arange(4);axs[0].bar(x-.16,[r['vehicle_count'] for r in baseline],.32,label='同类竖列基线');axs[0].bar(x+.16,[r['vehicle_count'] for r in selected],.32,label='新增几何模式');axs[0].set_ylabel('车辆/辆');axs[0].legend(fontsize=8)
axs[1].bar(x,[r['cost_yuan'] for r in selected],color='#477dba');axs[1].set_ylabel('当前成本/元每批')
axs[2].bar(x-.16,[r['volume_utilization']*100 for r in selected],.32,label='空间');axs[2].bar(x+.16,[r['weight_utilization']*100 for r in selected],.32,label='载重');axs[2].set_ylabel('总体利用率/%');axs[2].legend(fontsize=8)
for ax in axs:ax.set_xticks(x,[names[r['scenario']] for r in selected],rotation=22);ax.grid(axis='y',alpha=.25)
save('fleet_compare.png')
q=ROOT/'results/final/selected/q2_cost';valid=json.loads((q/'validation.json').read_text(encoding='utf8'));pp=rd(q/'placements.csv');ss=valid['vehicles'];representative=max(ss,key=lambda r:(sum(r.get(t,0)>0 for t in colorset),-r['item_count']));vid=representative['vehicle_id'];p=[r for r in pp if r['vehicle_id']==vid];v=next(v for v in vs if v['type_id']==representative['vehicle_type'])
fig=plt.figure(figsize=(10,6));ax=fig.add_subplot(111,projection='3d')
for r in p:
 x,y,z,dx,dy,dz=[float(r[k])/10 for k in ['x_mm','y_mm','z_mm','dx_mm','dy_mm','dz_mm']];corners=np.array([[x,y,z],[x+dx,y,z],[x+dx,y+dy,z],[x,y+dy,z],[x,y,z+dz],[x+dx,y,z+dz],[x+dx,y+dy,z+dz],[x,y+dy,z+dz]]);faces=[[corners[i] for i in a] for a in [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[1,2,6,5],[0,3,7,4]]];ax.add_collection3d(Poly3DCollection(faces,facecolors=colorset[r['cargo_type']],edgecolors='#444444',linewidths=.2,alpha=.56))
ax.set_xlim(0,v['dims'][0]/10);ax.set_ylim(0,v['dims'][1]/10);ax.set_zlim(0,v['dims'][2]/10);ax.set_xlabel('x 朝车头/cm');ax.set_ylabel('y 朝左/cm');ax.set_zlabel('z 向上/cm');ax.set_title(f"{vid} {v['type_id']}：右后下原点，{len(p)}件");ax.set_box_aspect(v['dims']);save('representative_3d.png')
fig,axs=plt.subplots(1,2,figsize=(10.5,4))
from matplotlib.patches import Rectangle,Patch
for r in p:
 x,y,z,dx,dy,dz=[float(r[k])/10 for k in ['x_mm','y_mm','z_mm','dx_mm','dy_mm','dz_mm']]
 for ax,yy,hh in [(axs[0],y,dy),(axs[1],z,dz)]:ax.add_patch(Rectangle((x,yy),dx,hh,fc=colorset[r['cargo_type']],ec='white',lw=.25,alpha=.42))
axs[0].set_ylim(0,v['dims'][1]/10);axs[1].set_ylim(0,v['dims'][2]/10)
for ax in axs:ax.set_xlim(0,v['dims'][0]/10);ax.set_xlabel('x/cm');ax.set_aspect('equal');ax.grid(alpha=.15)
axs[0].set_ylabel('y/cm（俯视投影）');axs[1].set_ylabel('z/cm（侧视投影）');axs[0].set_title('重叠投影用于观察；碰撞由三维检查');axs[1].legend(handles=[Patch(color=c,label=t) for t,c in colorset.items()],ncol=3,fontsize=8);save('representative_views.png')
fig,axs=plt.subplots(2,3,figsize=(11,6));parameters=['vehicle_length','vehicle_width','vehicle_height','cargo_size','quantity','dense_share'];labels=['车辆长度','车辆宽度','车辆高度','货物尺度','订单数量','重货占比']
baseexp=next(r for r in E if r['parameter']=='baseline')
for ax,key,label in zip(axs.flat,parameters,labels):
 rr=[r for r in E if r['parameter']==key and r['status']=='validated' and float(r['factor'])<=1.2];rr=sorted(rr,key=lambda r:float(r['factor']));ax.plot([float(r['factor']) for r in rr],[float(r['cost_yuan']) for r in rr],'o');ax.scatter([1],[float(baseexp['cost_yuan'])],marker='s',color='#ca7665');ax.set_title(label);ax.set_xlabel('相对原值倍数');ax.set_ylabel('批运输成本/元');ax.grid(alpha=.3)
save('sensitivity.png')
fig,axs=plt.subplots(1,2,figsize=(9.5,3.5));keys=['cost_v1','cost_v2','payload','cargo_weight','pressure','clearance'];labs=['车型1费用','车型2费用','载重','货重','承压阈值','安全间隙'];xx=np.arange(6)
lo=[];hi=[]
for k in keys:
 rr=[r for r in E if r['parameter']==k and r['status']=='validated'];lo.append(float(rr[0]['cost_yuan']));hi.append(float(rr[1]['cost_yuan']))
axs[0].bar(xx-.18,lo,.36,label='低水平');axs[0].bar(xx+.18,hi,.36,label='高水平');axs[0].set_xticks(xx,labs,rotation=23);axs[0].set_ylabel('运输成本/元');axs[0].legend(fontsize=8)
rr=[r for r in E if r['status']=='validated'];axs[1].scatter([int(r['items']) for r in rr],[float(r['seconds']) for r in rr],color='#477dba');axs[1].set_xlabel('货物件数');axs[1].set_ylabel('生成+求解+检查耗时/秒');axs[1].grid(alpha=.3);save('cost_and_performance.png')
columns=['场景','车辆','成本/元','空间/%','载重/%','松弛下界','相对界差距/%']
rows=[]
for r in selected:
 ub=r['cost_yuan'] if r['objective']=='cost' else r['vehicle_count'];lb=r['bounds']['lower_bound'];rows.append([names[r['scenario']],str(r['vehicle_count']),str(r['cost_yuan']),f"{r['volume_utilization']*100:.2f}",f"{r['weight_utilization']*100:.2f}",str(lb),f'{(ub-lb)/ub*100:.2f}'])
def mdtable(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])
allcount=len(items);totalvolume=sum(math.prod(t['dims'])*t['count'] for t in types)/1e9;totalmass=sum(t['weight']*t['count'] for t in types);mix=selected[-1];fleetcount=collections.Counter(r['vehicle_type'] for r in valid['vehicles']);maxpressure=max(a['pressure_kg_m2'] for a in valid['supports']);minclear=min(next(vv for vv in vs if vv['type_id']==r['vehicle_type'])['dims'][2]-float(r['z_mm'])-float(r['dz_mm']) for r in pp);single_rows=[]
for r in S['singles']:single_rows.append([r['scenario'],','.join(map(str,r['counts'])),f"{r['volume_utilization']*100:.2f}",f"{r['weight_utilization']*100:.2f}",r['validation_status']])
exp_rows=[[r['parameter'],r['factor'],r['status'],r['vehicles'] or '-',r['cost_yuan'] or '-',f"{float(r['seconds']):.2f}"] for r in E]

def pdf_from_md(text,path):
 style=ParagraphStyle('body',fontName='Chinese',fontSize=10.5,leading=17,spaceAfter=8,wordWrap='CJK',allowWidows=0,allowOrphans=0);heads={1:ParagraphStyle('h1',parent=style,fontSize=18,leading=25,spaceBefore=12,spaceAfter=14,keepWithNext=True),2:ParagraphStyle('h2',parent=style,fontSize=13,leading=20,spaceBefore=12,spaceAfter=10,keepWithNext=True),3:ParagraphStyle('h3',parent=style,fontSize=11.5,leading=18,spaceBefore=8,spaceAfter=8,keepWithNext=True)};small=ParagraphStyle('small',parent=style,fontSize=7.3,leading=11,spaceAfter=0);story=[];ls=text.splitlines();i=0
 while i<len(ls):
  line=ls[i].strip()
  if not line:i+=1;continue
  if line.startswith('|'):
   rr=[]
   while i<len(ls) and ls[i].strip().startswith('|'):
    cols=[c.strip() for c in ls[i].strip().strip('|').split('|')]
    if not all(re.fullmatch('[-: ]+',c) for c in cols):rr.append([Paragraph(html.escape(c),small) for c in cols])
    i+=1
   n=len(rr[0]);chunks=[rr] if len(rr)<=20 else [[rr[0]]+rr[j:j+18] for j in range(1,len(rr),18)]
   for block in chunks:
    tbl=Table(block,colWidths=[(A4[0]-88)/n]*n,repeatRows=1,hAlign='LEFT');tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eff5')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#bbc8d3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([tbl,Spacer(1,10)])
   continue
  if line.startswith('!['):
   m=re.match(r'!\[(.*?)\]\((.*?)\)',line);fp=ROOT/'figures'/Path(m.group(2)).name
   im=Image(str(fp));scale=min((A4[0]-88)/im.imageWidth,300/im.imageHeight);im.drawWidth=im.imageWidth*scale;im.drawHeight=im.imageHeight*scale;story.extend([im,Paragraph(html.escape(m.group(1)),small),Spacer(1,12)]);i+=1;continue
  if line.startswith('#'):
   level=len(line)-len(line.lstrip('#'));story.append(Paragraph(html.escape(line[level:].strip()),heads.get(level,heads[3])));i+=1;continue
  story.append(Paragraph(html.escape(line),style));i+=1
 def footer(c,doc):c.saveState();c.setFont('Chinese',8);c.setFillColor(colors.HexColor('#596b7a'));c.drawString(44,26,'多场景货物装箱研究 | 已验证可行结果，未证全局最优');c.drawRightString(A4[0]-44,26,str(doc.page));c.restoreState()
 SimpleDocTemplate(str(path),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=43,bottomMargin=43,title='多场景货物运输装箱策略优化',author='R19 L2离线研究').build(story,onFirstPage=footer,onLaterPages=footer)

# Data-bound manuscript follows below.

comparison=json.loads((ROOT/'research/comparison/guarded_summary.json').read_text())
fig,axs=plt.subplots(1,2,figsize=(10,3.7))
for i,method in enumerate(['A','B','C']):
 rr=[a for a in comparison if a['method']==method]
 axs[0].scatter([a['seed'] for a in rr],[a['q2_cost_cost'] for a in rr],marker=['o','s','^'][i],s=45,label=method)
 axs[1].scatter([a['total_outer_seconds'] for a in rr],[a['q2_cost_cost'] for a in rr],marker=['o','s','^'][i],s=45,label=method)
axs[0].set_xlabel('固定种子');axs[0].set_ylabel('最低费调用及候选保护/元');axs[1].set_xlabel('实际全流程及保护/秒');axs[1].set_ylabel('费用/元')
for ax in axs:ax.legend();ax.grid(alpha=.3)
save('method_comparison.png')
from manuscript_v2 import compose
paper,report=compose(globals())
(ROOT/'paper/paper.md').write_text(paper,encoding='utf8');(ROOT/'report.md').write_text(report,encoding='utf8')
pdf_from_md(paper,ROOT/'paper/paper.pdf');pdf_from_md(report,ROOT/'report.pdf')
qa=[]
for path,folder in [(ROOT/'paper/paper.pdf',ROOT/'paper/render'),(ROOT/'report.pdf',ROOT/'paper/report_render')]:
 folder.mkdir(exist_ok=True);d=fitz.open(path)
 for ix,page in enumerate(d):
  page.get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(folder/f'page_{ix+1:02d}.png')
  bad=[list(b[:4]) for b in page.get_text('blocks') if b[0]<0 or b[1]<0 or b[2]>page.rect.width or b[3]>page.rect.height]
  qa.append({'file':str(path.relative_to(ROOT)),'page':ix+1,'chars':len(page.get_text()),'width':page.rect.width,'height':page.rect.height,'rendered':True,'outside_blocks':bad})
dump(ROOT/'checks/pdf_render_manifest.json',qa)
claims=[]
for r in selected:claims.append({'requirement':'Q1-B' if r['scenario'].startswith('q1') else 'Q2-A' if r['scenario']=='q2_vehicles' else 'Q2-B','claim':str(r['vehicle_count'])+' vehicles; '+str(r['cost_yuan'])+' yuan','source':'PDF p2; 附件1','result':'results/final/selected/'+r['scenario'],'paper_section':'6/7','check':'all item geometry/load/inventory and objectives recomputed','limit':'feasible upper bound, not global optimum'})
claims.extend([{'requirement':'Q1-A','claim':'current searched nondominated discrete feasible points','source':'PDF p2 Q1(1)','result':'results/final/single','paper_section':'6.1','check':'candidate dominance and full geometry','limit':'not complete Pareto frontier'},{'requirement':'Q1-C','claim':'all per-item coordinates/orientation/utilizations','source':'PDF p2 Q1(2)','result':'placements.csv/vehicles_summary.csv','paper_section':'7/A','check':'source and metrics recomputed','limit':'right-rear-bottom min corner'},{'requirement':'Q3-A','claim':'36 actual current parameter cases incl failure; prior36 preserved; 9 paired methods + uniform protection; technical report','source':'PDF p3','result':'experiments/experiments.csv; research/comparison; report.md; history/execution','paper_section':'8','check':'current real reruns, prior inherited labeled','limit':'attachment1 synthetic perturbations, author checks pending informed review'},{'requirement':'P/U','claim':'replayable algorithm; complete Chinese paper/report/PDF','source':'PDF p3说明; L2.md','result':'code; README; paper; algorithm.zip','paper_section':'all','check':'raw full replay, ZIP, boundary, rendered pages','limit':'official I/O, contest rules, dynamic safety unknown'}]);csvwrite(ROOT/'claim_evidence.csv',claims)
print(json.dumps({'paper_chars':len(paper),'report_chars':len(report),'pdf_pages':len(qa),'figures':len(list((ROOT/'figures').glob('*.png')))},ensure_ascii=False))
