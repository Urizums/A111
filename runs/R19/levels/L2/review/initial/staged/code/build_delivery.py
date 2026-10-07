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
 ax.plot([r['volume_utilization']*100 for r in pts],[r['weight_utilization']*100 for r in pts],'o-',color='#326b98');ax.set_title(v['type_id']+' 搜索非支配集');ax.set_xlabel('名义空间利用率/%');ax.set_ylabel('载重利用率/%');ax.grid(alpha=.3)
save('single_frontier.png')
fig,axs=plt.subplots(1,3,figsize=(11.5,3.4));x=np.arange(4);axs[0].bar(x-.16,[r['vehicle_count'] for r in baseline],.32,label='同类竖列基线');axs[0].bar(x+.16,[r['vehicle_count'] for r in selected],.32,label='平台模式改进');axs[0].set_ylabel('车辆/辆');axs[0].legend(fontsize=8)
axs[1].bar(x,[r['cost_yuan'] for r in selected],color='#477dba');axs[1].set_ylabel('改进成本/元每批')
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
 rr=[r for r in E if r['parameter']==key and r['status']=='validated' and float(r['factor'])<=1.2];rr=sorted(rr,key=lambda r:float(r['factor']));ax.plot([float(r['factor']) for r in rr],[float(r['cost_yuan']) for r in rr],'o-');ax.scatter([1],[float(baseexp['cost_yuan'])],marker='s',color='#ca7665');ax.set_title(label);ax.set_xlabel('相对原值倍数');ax.set_ylabel('批运输成本/元');ax.grid(alpha=.3)
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
paper=f'''# 满足支撑与累计承载约束的多场景货物装箱优化

## 摘要

针对附件1的{allcount}件刚性长方体货物，本文建立以右后下角为原点的统一三维装载模型，将车辆尺寸、额定载重、姿态、易碎禁压、定向局部重心和累计承载同时纳入可行性约束。在单车场景，采用标准化体积和重量加权扫描，保留搜索获得的非支配可行装载；在全运场景，先用同类竖列建立完整可行基线，再针对易碎品地板占用构造标准件网格平台，生成可检查装载模式，并以整数模式选择严格满足五类库存。不同实现的几何与传载检查器重新计算每件位置、接触和逐车指标。

原始货物总体积{totalvolume:.2f}m³、总重量{totalmass:.0f}kg。最终可行方案仅用车型1时为{selected[0]['vehicle_count']}辆，仅用车型2时为{selected[1]['vehicle_count']}辆；混合最少车与最低成本两个目标均得到{mix['vehicle_count']}辆、{mix['cost_yuan']:.0f}元，构成为{fleetcount.get('V1',0)}辆车型1与{fleetcount.get('V2',0)}辆车型2。两目标一致是本次候选库和运价条件下的结果。容量松弛给出的原问题下界分别为16辆、7辆、7辆和4900元，故这些数值是已验证可行上界，并非已证明的全局最优值。{len(E)}组真实重求解实验中{sum(r["status"]=="validated" for r in E)}组通过逐件检查，1组极端低车厢案例失败并保留。研究显示易碎朝向、车辆横向尺寸与货物尺度会显著改变费用；±10%载重和承压阈值扰动在本搜索配置内未改变车队。程序、完整坐标、原始输入身份和PDF随附，可离线重放。

关键词：三维装箱；装载模式；整数规划；易碎支撑；累计承载；非支配可行集

## 1 问题与数据审计

本研究回答三组问题。问题1需要分别研究两种车型的单车体积及重量双目标，随后在各自单车型条件下运完全部库存并减少车次，并输出每件坐标和姿态。问题2允许车型混用，分别优化车辆数量和运输费用。问题3将模型与实际实验转化为管理者可理解的技术方案。四个全运场景相互独立，不能以一个单车装载替代全量运输，也不能假设费用最小等价于车辆最少。

数据来自题目PDF三页、附件1.docx段落与表1、附件2.xlsx三张工作表。对照冻结lock计算SHA-256均一致。内部使用mm、kg和元每趟；货物原cm尺寸乘10。附件1数据如下。

{mdtable(['货物','类别','长×宽×高/mm','单重/kg','件数','密度/kg每m³'],[[t['cargo_type'],t['category'],'×'.join(map(str,t['dims'])),t['weight'],t['count'],f"{t['weight']/(math.prod(t['dims'])/1e9):.2f}"] for t in types])}

车型1内尺寸4200×2100×2200mm、载重6000kg、450元每趟；车型2为6800×2450×2500mm、10000kg、700元每趟。名义容积分别为19.404m³和41.650m³；3cm间隙使可用几何容积分别为19.1394m³和41.1502m³。库存总密度约{totalmass/totalvolume:.2f}kg/m³，低于两车载重/名义容积比，预示本实例总体偏空间约束，但这种总体判断不能代替逐车重量检查。

附件2只给油品包装尺寸和车型尺寸资料。化验与仓库值不同，部分仓库值是区间；重量、订单数量、货物类别和车型载重缺失，部分车型非封闭长方体，运价又使用元/1000km。因此本文审计和保留原单元格，不补0，不把附件2称为完整真实订单的通用性验收数据。规模实验采用明确标注的附件1合成复制订单。

## 2 假设、符号与适用范围

取车厢右后下角为原点，x朝车头、y朝车厢左侧、z朝上。货物坐标为最小角点，姿态orientation_id为原始长宽高索引的置换，例如012表示原姿态、102表示长宽交换。标准件允许六种轴置换去重；定向件仅012。易碎件保持原底面，允许绕z轴90度转向；严格固定朝向作为敏感性分支。

货物质心取几何中心，这是均匀密度假设。主模型对全部货物采用底面完全支撑的保守条件；对易碎品仅允许地板或标准件共面顶面并集充分覆盖，且其上方不能受压。易碎“单层”解释为不互叠，主构造中的普通竖列易碎在地板、平台易碎在标准层顶面，可能出现不同z。若客户将单层解释为所有易碎必须同一高度，应采用严格分支或重新生成模式，不能直接沿用主结果。

每个上件的总向下荷载是自重加更上层传载，按接触面积比例分配到直接下件。每条接触及下件顶面平均受载均不超过500kg/m²，地板不受这一货物上限。此分担模型属于明确的工程近似，未模拟材料局部刚度、动态加速度或叉车操作；更宽部分支撑及力矩平衡没有用于全局最优证明。

符号：i为货物，v为车辆，t为货物类别，p为完整装载模式；(x_i,y_i,z_i)为位置，(d_xi,d_yi,d_zi)为允许姿态后尺寸；m_i为质量；L_v,W_v,H_v、P_v、c_v分别为内尺寸、载重和每趟费用；g为间隙，b为承压阈值；a_ij为上件i与下件j的接触面积，F_i为向下累计荷载；n_p为模式使用次数。

## 3 统一三维几何与承载模型

### 3.1 边界、互斥和方向

每件仅分配到一个车辆，全运时所有ID恰好出现一次，单车选择时库存为上限。坐标与尺寸满足：

0 ≤ x_i，x_i+d_xi ≤ L_v；0 ≤ y_i，y_i+d_yi ≤ W_v；0 ≤ z_i，z_i+d_zi ≤ H_v-g。

任意同车两件i、j至少在一轴区间内部不相交，即x_i+d_xi≤x_j或x_j+d_xj≤x_i，或y方向两个条件之一，或z方向两个条件之一。边界相切允许，正交摆放和姿态集合在每件层面检查，不通过缩小尺寸或放大容差规避碰撞。

每车总质量Σm_i≤P_v。名义空间利用率U_V=Σ(d_xi d_yi d_zi)/(L_v W_v H_v)，载重利用率U_W=Σm_i/P_v。混合车队使用总货量除总容量，不对不同车型百分比作简单平均；几何约束使用H_v-g，但名义满容率仍按题意使用H_v。

### 3.2 接触覆盖与定向局部重心

当z_i>0时，直接下件j须满足z_j+d_zj=z_i，接触面积为xy投影矩形交集面积。支持件已经两两不重叠，故同高度接触矩形内部互不重叠；检查Σa_ij=d_xi d_yi实现完整覆盖。易碎i的所有下件必须为标准件，任意货物均不得由易碎下件承载。定向下件j还要求每个直接上件i的质心xy投影位于j的投影内，这比只检查整车质心更贴合附件1的局部约束。

### 3.3 累计承载与单位换算

支持关系按z严格向下，构成有向无环图。由高到低递推：F_i=m_i+Σ_k T_ki；T_ij=F_i a_ij/(Σ_j a_ij)。每条接触压力T_ij/(a_ij/10^6)≤b；每个下件累计受载Σ_i T_ij除其顶面面积也≤b。面积由mm²转换为m²，避免把500kg/m²误写为每件500kg。地板收到所有列的累计荷载，检查地板载荷之和等于整车质量。

手算锚：1m²底面上有300kg中层和300kg顶层，底层承受600kg/m²，虽然每个直接上件单重均小于500，也必须拒绝；将顶层降为200kg，则底层恰等500，接受。实际用例同时检验了标准件多支撑并集及每条传载，见checks/boundary_tests.json。

## 4 目标与分解求解

### 4.1 单车双目标

对于库存内选货，目标为同时提高(U_V,U_W)。除单独最大化两率的权重端点外，扫描α=0,0.1,…,1，用每件标准化价值αV_i/(LWH)+(1-α)m_i/P指导构造，并加入候选模式库中所有合法单车。删除在两指标上同时不优且至少一项严格差的点，得到搜索非支配集。有限扫描及受限几何模式不能证明完整Pareto前沿，更不能称单车同时达到两个独立全局最大值。

### 4.2 全量运输的整数模式主问题

每个模式含车型、五类数量A_tp以及每件局部坐标。求解Σ_p A_tp n_p=N_t（对每类t），n_p为非负整数。使用等式而不是“至少需求”，因此不会通过多运虚构货物满足订单。最少车辆目标为minΣn_p，以成本作次级；最低成本为minΣc_p n_p，以车数作次级。代码用足够小的、依库存和最大费用计算的ε实现确定性次级目标，其总次级项小于主目标一个整数单位。

每个模式的几何、质量和传载由检查器实际验证，主问题组合后将模式位置复制到车辆并逐类重新分配唯一ID，再次检查全量守恒。整数求解器Optimal状态只证明当前模式库主问题，不能扩展为原三维装箱全局最优。

### 4.3 必要下界和可行上界

单车型下界为ceil(总货物体积/[LW(H-g)])与ceil(总重量/P)的较大值。混合车型枚举非负(n1,n2)，要求总体积及总重量不超过相应聚合容量，再分别最小化n1+n2或450n1+700n2。聚合容量不等于真实三维可装，但任何真实装载都满足它，所以提供合法必要下界。易碎可以在标准平台上，不把全部易碎面积除地板面积草率作为原问题下界。

候选布局给上界，本文采用(上界-下界)/上界报告相对界差距。该差距不是求解器库内mip_gap；两者独立列示。单车体积利用率上界为100%。另由不重叠和最大货物密度得到重量上界：Σm_i≤ρ_max ΣV_i≤ρ_max LW(H-g)。实际ρ_max={max(t["weight"]/(math.prod(t["dims"])/1e9) for t in types):.2f}kg/m³；车型1载重利用率不超过59.81%，车型2不超过77.16%。这是一条适用于原题更宽几何可行域的必要上界，说明本库存无论怎样搭配都不能让这两车达到100%满载；搜索点仍未证明达到该上界。

## 5 算法与真实检查设计

### 5.1 可解释基线

将同类同姿态货物组成底面完全一致的竖列；列高取顶部间隙、库存和累计压力允许的最大层数，易碎只能一层。车厢地板用不重叠的guillotine矩形分割，每放一个列块，将剩余矩形切为两个互不重叠区域。用相同类别优先值选择单位地板面积价值最大的列；装满或无可放候选时开下一车，空车仍装不进时明确返回构造失败。这给所有必答的可行起点。

### 5.2 瓶颈驱动的平台模式改进

竖列初轮发现大量易碎件消耗低矮地板区域，造成高处空间闲置。改进引入完整标准件网格平台：G1采用2×3底层格，G2采用4×2格，按原尺寸重复多层，再在完整标准顶面上铺易碎件；易碎原底面平面可转向。平台高度按车高和压力限制，所需标准件不足时不制造不完整平台。其余位置仍可放定向竖列。平台每个组件坐标均输出，检查器不相信构造器提供的支撑关系。

候选生成使用固定seed=19；类别全等、体积、质量三种权重，加22组预先冻结的随机对数权重，对仅车型1、仅车型2和混合车队分别构造模式。完整可行车队的所有模式及尾车均进入库，数量向量去重；最终模式库{S['library_size']}个。模式整数求解每场景声明60秒限制，保存实际状态、耗时和界，未使用联网或新安装求解器。

### 5.3 实质检查与失败路径

validate.py不导入构造器，独立从CSV及源items读取尺寸、姿态、车辆参数，检查全部同车两两碰撞，再重建支持图、传载、数量和指标。16个实际边界用例全部符合预期，包含合法相切、恰等顶部间隙、压力等式、易碎多标准支撑，及1mm重叠、超高、错误定向、易碎空洞、定向托易碎、易碎压货、累计超压、重复、遗漏、缺重量拒绝。15件原始五类子集产生真实smoke产物。独立代码实现由同一作者执行，不冒充独立上下文验收。

## 6 问题1：单车与单车型全运结果

### 6.1 双目标搜索结果

{mdtable(['方案ID','G1,G2,G3,G4,G5件数','空间/%','载重/%','验证'],single_rows)}

![单车搜索非支配点](../figures/single_frontier.png)

图1只表示实际搜索所得非支配点。若某车型仅剩一个点，说明这一候选集中一个装载同时支配其他装载，而不表示数学上两个目标总能一致。推荐点可按企业空间或载重偏好选取；全部坐标位于results/final/single/各方案目录。不使用库存外无限同类货物，也不引入货物运输收入。

### 6.2 单车型全运

车型1基线{baseline[0]['vehicle_count']}辆，平台模式改进{selected[0]['vehicle_count']}辆、{selected[0]['cost_yuan']}元，减少{baseline[0]['vehicle_count']-selected[0]['vehicle_count']}辆。车型2基线{baseline[1]['vehicle_count']}辆，改进{selected[1]['vehicle_count']}辆、{selected[1]['cost_yuan']}元，减少{baseline[1]['vehicle_count']-selected[1]['vehicle_count']}辆。每个全运场景恰好包含3000个源ID，无遗漏、无重复；每车货物坐标姿态都通过独立代码检查。

## 7 问题2：混合两目标及逐车方案

{mdtable(columns,rows)}

![车队目标与总体利用率](../figures/fleet_compare.png)

图2展示相同库存、相同规则的真实基线与平台改进。混合最少车辆与最低运输成本重新运行不同目标，最终在候选库中均选{mix['vehicle_count']}辆，其中{fleetcount.get('V1',0)}辆车型1、{fleetcount.get('V2',0)}辆车型2，成本{mix['cost_yuan']}元。与混合最少车基线相比减少{baseline[2]['vehicle_count']-mix['vehicle_count']}辆；与混合成本基线相比节省{baseline[3]['cost_yuan']-mix['cost_yuan']}元（{(baseline[3]['cost_yuan']-mix['cost_yuan'])/baseline[3]['cost_yuan']*100:.2f}%）。不能据此推论其他费用比例或库存结构下两目标相同。

代表车选择{vid}、车型{representative['vehicle_type']}，包含{len(p)}件。完整车队逐车统计如下；G1-G5数量求和等于原库存。

{mdtable(['车ID','车型','G1','G2','G3','G4','G5','质量/kg','空间/%','载重/%'],[[r['vehicle_id'],r['vehicle_type'],*[r.get(t,0) for t in colorset],f"{r['weight_kg']:.0f}",f"{r['volume_utilization']*100:.1f}",f"{r['weight_utilization']*100:.1f}"] for r in ss])}

![代表车三维装载](../figures/representative_3d.png)

![代表车俯视与侧视](../figures/representative_views.png)

图3-4统一使用cm、右后下原点及类别颜色。投影视图会因不同层投影重叠，不能作为三维碰撞判断。逐件ID与精确mm坐标在placements.csv，姿态从原轴置换解释。最低成本车队最大实际接触压力{maxpressure:.2f}kg/m²，最小实际顶间隙{minclear:.0f}mm；每车地板接收到的累计荷载与质量相等。压力余量不能抵销易碎禁压或方向违约。

## 8 问题3：性能、参数与管理机制

### 8.1 实测性能与实验口径

环境为Intel Core i7-14650HX（16核、24逻辑处理器）、Windows 11、Python 3.12.8，NumPy/SciPy/Matplotlib等版本记录在logs/preflight.json。主实例3000件，最终模式库{S['library_size']}个，四场景基线、改进、单车候选及验证总耗时{S['seconds']:.2f}秒。单场景整数求解耗时分别为{', '.join(f"{r['solver']['seconds']:.2f}" for r in selected)}秒；库内求解状态全部Optimal，原问题容量界差距见表。输入身份及最终main.py SHA-256为{S['code_sha256']}。

模型构造是受限启发式：全库没有包含所有三维可行布局。碰撞检查在每车n_v件上进行O(n_v²)配对，支持重建亦为二次规模；3000件分布多车而不是一辆。整数主问题有5条需求等式与{S['library_size']}个整数变量，较逐件三维混合整数模型小，但限制了可搜索几何范围。该分解体现可行性和计算成本的折中，不能以库内最优替代全局最优。

参数实验原先声明32例，保留原设置后，为检验口径增补1例易碎地板同高分支，并在执行前声明7、29、41三个额外种子；最终36例。每个方向两个水平，多数取0.9/1.1；订单数量和重泡构成为0.8/1.2；间隙0/2倍；二维交互为宽度与车型1费用的四个组合。采用同一seed=19、5组随机启动、模式求解8秒限时，基础参照是同配置的14辆9300元，而不是22启动主结果。每个扰动都重新构造、求解、独立检查并保存输入、车辆、配置和模式。低搜索预算导致个别趋势受候选库变化影响，故图上不强行修成单调曲线。种子重复的实际车数与费用均列于结果表，不能仅凭一个seed称稳定。

### 8.2 全部参数实际结果

{mdtable(['参数','相对倍数','状态','车辆','成本/元','全流程秒'],exp_rows)}

![几何、数量与构成敏感性](../figures/sensitivity.png)

![费用及实测时间](../figures/cost_and_performance.png)

车长增加10%使该配置费用从参照9300降至8400元，车长缩小10%升至10500元；车宽缩小10%为10700元。货物三轴同比放大10%会使体积增至1.331倍，费用升至11850元；缩小10%体积为0.729倍，费用7450元。这些台阶变化同时包含标准平台能否放入和尾车余量，不能用体积比例线性预测车数。

载重、货重和承压阈值±10%各组均为14辆9300元，说明在本局部范围和搜索配置下对应约束不是改善车队的主要瓶颈，但500仍是必须满足的硬限制。间隙由30降至0mm得14辆8800元，提高到60mm为15辆9250元；同一个件的离散层数能改变模式组合，车数与费用可能有不同方向变化。

固定易碎姿态得到17辆9900元，相比同配置原底面可90度转向的14辆9300元增加600元。该分支检验朝向歧义。另外要求所有易碎都在地板同一z且禁用平台的严格分支，得到14辆、9800元，说明易碎同高解释也会影响运输策略。该地板分支对易碎满足单一地板支撑，未宣称更严口径全局最优。车型1费用下降10%时16辆9135元，车型2费用下降10%时14辆8460元；最低费用可通过切换车队构成实现，而不必维持主方案辆数。

重泡构成实验把G1、G2、G5数量乘给定倍数，G3、G4乘2减该倍数，避免把密度差异和零质量混淆；它改变总库存，属于合成结构研究，不能作为同总货量收益对照。两倍订单6000件为29辆18300元；该结果仅支持这一个合成复制规模的运行能力。极端车高0.1倍时可用高度190mm/220mm，小于标准件最小允许高度250mm和其他类别高度，因此具有尺寸必要不可装入证据；求解失败日志原样保留，不删除以提高可行率。

### 8.3 管理建议

本批货物应优先协调易碎顶部保护与标准平台支撑，采用允许范围内的底面90度转向；不能为了追求满容而取消间隙、叠压易碎或错误转向定向件。调度可先选13辆8850元方案作为可执行上界，并根据装卸设备及客户对单层的解释复核现场条件。当前全局车辆下界7、费用下界4900很松，继续研究的主要价值在缩小几何模式限制，而不是把8850元写成保证最低报价。

生产接口要求提供逐件ID、类别、尺寸、重量和车型内尺寸/载重/每趟费；区间尺寸宜按保守上界求解并说明测量含义。审核器必须独立重算后才导出装载指令。官方评阅I/O协议未知，当前CSV/JSON格式可明确离线运行，后续取得协议后再适配。没有进行真实车辆装卸或动态安全实验。

## 9 可信性、优点与局限

优点是所有必答均有真实可行坐标，载荷累计及面积换算显式可重算，整数需求等式保障3000件守恒，原始失败和模型迭代完整保留，图表从同一被选run生成。平台改进对本实例节省车辆和费用具有实际计算证据。

局限包括：仅搜索同类竖列及两种网格平台，原问题最优性未建立；全部底面充分支撑和逐下件定向重心是保守口径，原题某些规则有歧义；接触面积比例分担未模拟实际包装材料；没有轴荷、动态加速度、门宽、装卸路径或顺序数据，未悄悄加为题设硬约束；附件2不具完整订单条件；最终复核为作者重算与不同代码路径，无独立上下文正式验收；未核实赛事投稿规则、AI披露格式、评阅接口或投稿授权。

## 10 结论

统一几何及累计承载模型完成了附件1两车型单车非支配候选、两单车型全运与混合两目标运输方案。平台装载模式改进取得25辆车型1、13辆车型2和13辆8850元混合方案；独立代码逐件检查通过。这是具有可运行附件与清晰界差距的可行研究结果，尚不能宣布原问题全局最优。{len(E)}组参数实验给出可追溯的几何、费用、规则与规模机制，失败案例、解释边界及现场条件均应保留于企业部署决策。

## 参考资料

[1] 2026年第十六届MathorCup数学应用挑战赛题目，D题，提供原始PDF，共3页。

[2] 附件1.docx，车辆段3-10、约束段13-19、表1；本研究原始数据。

[3] 附件2：验证数据集.xlsx，箱装产品尺寸、车型尺寸、Sheet3；仅结构资格审计。

本研究离线原创推导，无外部论文检索；没有虚构期刊、DOI或文献内容。SciPy/ReportLab等是实际运行软件而不是人为补造的理论证据。

## 附录A：复现接口与坐标电子附表

从execution目录运行：py -3.12 -X utf8 -B code/main.py --raw ../../../inputs/raw --output results/replay。更稳妥的仓库根命令见README.md。无网、无安装，seed/config固定；main.py --items、--vehicles、--scenario、--config、--output提供CSV/JSON接口，所有scenario均保存placements、vehicles_summary、supports、validation、run。

完整电子坐标附表包括四个全运场景各3000行及所有单车子集。placements.csv每行含run_id、scenario_id、vehicle_id、vehicle_type、item_id、cargo_type、x_mm/y_mm/z_mm、orientation_id、dx_mm/dy_mm/dz_mm。代表车的前12件精确坐标如下，其余不省略于电子附件。

{mdtable(['item_id','类别','x/mm','y/mm','z/mm','姿态','dx×dy×dz/mm'],[[r['item_id'],r['cargo_type'],r['x_mm'],r['y_mm'],r['z_mm'],r['orientation_id'],'×'.join(r[k] for k in ['dx_mm','dy_mm','dz_mm'])] for r in p[:12]])}

## 附录B：失败、修正与资源

首轮同类竖列结果保留results/main；平台研究迭代保留results/improved；最终原件再生成保留results/final。工具错误包括一次导入行误缩进（运行前读回发现）及一次修补上下文拒绝，恢复后真实执行；没有用两轮错误作为整任务停止规则。账号/会话中断后原求解会话不可用，进程核查未见本任务运行；主结果已完成，参数仅完成13组，按checkpoint续跑余下组，未重置已完成记录或预算。

实验具体时间、原始异常、声明求解时限和实际状态保存在logs与experiments。时间限制只约束模式MILP，不含库生成与验证；实际总耗时可超过它，不能将总时间截断至8或60秒。真实模型身份、token、cost无宿主遥测，全部为null。写域是协作约定，不代表OS隔离。程序不投稿、不上传，也不保证获奖或评分。
'''
(ROOT/'paper/paper.md').write_text(paper,encoding='utf8')
report=f'''# 企业货物装载与调度技术报告

## 决策与适用条件

本批附件1订单3000件、{totalvolume:.2f}m³、{totalmass:.0f}kg，当前可执行混合方案为{fleetcount.get('V1',0)}辆车型1加{fleetcount.get('V2',0)}辆车型2，共{mix['vehicle_count']}辆、{mix['cost_yuan']}元。全部货物恰好一次运输，布局、累计承重和费用均已重算。报价是可行上界，原问题最低费用仅有4900元容量松弛下界，尚未证明8850元全局最低。

{mdtable(columns,rows)}

## 装载作业依据

采用右后下原点，x朝车头、y朝左、z朝上；每件最小角坐标与姿态以电子CSV为准。标准件允许正交旋转，定向件必须原姿态，易碎底面可90度转向但绝不可受压。标准件网格平台能托住易碎，其下各层传载要累计，不能只检查最上件单重。主车队最大接触压力{maxpressure:.2f}kg/m²，最小实际顶间隙{minclear:.0f}mm。现场若要求所有易碎同一高度、叉车留道或轴荷限额，必须补充约束重求解。

## 模型和程序如何工作

第一步从原件规范化3000个唯一ID及两车参数；第二步把货物构成同底面竖列或标准网格平台，逐块输出完整几何；第三步生成{S['library_size']}个不同数量模式，以整数规划精确等式满足五类需求；第四步用与构造器不同的validate.py重算边界、互斥、方向、易碎支撑、定向重心、累计压力、载重、库存和成本。只有验证通过才输出可执行方案。

同类竖列成本基线为{baseline[3]['cost_yuan']}元，平台模式下降至{mix['cost_yuan']}元，节省{baseline[3]['cost_yuan']-mix['cost_yuan']}元。主实例完整算法及检查实际{S['seconds']:.2f}秒，模式整数求解每场景设置60秒，详细状态保存。库内Optimal不是整个三维问题最优，不可写成保证报价。

## 参数影响和风险

{len(E)}组重求解保留全部结果，{sum(r["status"]=="validated" for r in E)}组合法，极端车高10%组不可装入。较低搜索预算参照为14辆9300元；车长缩小10%为10500元，增加10%为8400元；货物尺寸三轴放大10%为11850元，缩小10%为7450元。载重、货重、承压阈值±10%局部没有改变该配置车队，不能因此取消硬约束。固定易碎方向为17辆9900元，说明合同中旋转解释具有经济影响。两倍6000件合成复制订单29辆18300元，仅证明该规模案例可运行。

附件2缺订单数量、重量、类别、车型载重，车型尺寸及费用单位亦有歧义。当前只审计尺寸，不能作为真实订单通用性验收。生产输入要明确全部必填项；尺寸区间建议保守上界，并标明测量来源。

## 部署接口、审计与验收

入口main.py支持--items、--vehicles、--scenario、--config、--output；items.csv逐件ID、类型、类别、尺寸mm、重量kg；vehicles.json内尺寸、载重、元/趟费用、间隙mm。输出逐件placements.csv、逐车vehicles_summary.csv、接触supports.csv、validation.json、run.json。非法缺重量或方向/压货布局返回非成功状态，不默默补0。

在本地Windows现有Python3.12及科学库离线运行；完整命令、源hash、边界检查、干净复跑及图表生成步骤见README。官方测试I/O未知，当前接口不假称官方兼容；未进行真实装卸、动态强度或独立上下文验收。现场部署前补充操作条件并用源订单重跑；研究交付不授权赛事投稿。

## 建议的企业执行决定

先用已检查的13辆8850元方案作本批调度预算；由现场确认易碎底面转向和平台承载、保持3cm间隙及朝向标记，按逐件CSV装载。若现场解释更严，使用已保存的严格分支重新规划。继续研发优先扩充更细的可行几何模式与加强下界，保留所有失败，不以满容率图代替安全审计。
'''
(ROOT/'report.md').write_text(report,encoding='utf8')
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
pdf_from_md(paper,ROOT/'paper/paper.pdf');pdf_from_md(report,ROOT/'report.pdf')
render=ROOT/'paper/render';render.mkdir(exist_ok=True);render_report=ROOT/'paper/report_render';render_report.mkdir(exist_ok=True)
qa=[]
for path,folder in [(ROOT/'paper/paper.pdf',render),(ROOT/'report.pdf',render_report)]:
 d=fitz.open(path)
 for ix,page in enumerate(d):
  pix=page.get_pixmap(matrix=fitz.Matrix(1.25,1.25));pix.save(folder/f'page_{ix+1:02d}.png');qa.append({'file':str(path.relative_to(ROOT)),'page':ix+1,'chars':len(page.get_text()),'width':page.rect.width,'height':page.rect.height,'rendered':True})
dump(ROOT/'checks/pdf_render_manifest.json',qa)
claims=[]
for r in selected:claims.append({'requirement':'Q1-B' if r['scenario'].startswith('q1') else 'Q2-A' if r['scenario']=='q2_vehicles' else 'Q2-B','claim':str(r['vehicle_count'])+' vehicles; '+str(r['cost_yuan'])+' yuan','source':'PDF p2; 附件1','result':'results/final/selected/'+r['scenario'],'paper_section':'6/7','check':'all items geometry/load/inventory recomputed','limit':'feasible upper bound, not global optimum'})
claims.extend([{'requirement':'Q1-A','claim':'searched nondominated feasible points','source':'PDF p2 Q1(1)','result':'results/final/single','paper_section':'6.1','check':'independent implementation + candidate dominance','limit':'not complete Pareto frontier'},{'requirement':'Q1-C','claim':'per-item coordinates/orientation/utilizations','source':'PDF p2 Q1(2)','result':'placements.csv/vehicles_summary.csv','paper_section':'7/附录A','check':'geometry and metrics recomputed','limit':'right-rear-bottom convention'},{'requirement':'Q3-A','claim':'32 actual parameter cases incl. failure; technical report','source':'PDF p3','result':'experiments/experiments.csv; report.md','paper_section':'8','check':'actual reruns, not interpolations','limit':'attachment1 synthetic perturbations; author check'},{'requirement':'P/U','claim':'replayable algorithm and complete Chinese paper/PDF','source':'PDF p3说明; L2.md','result':'code; README; paper','paper_section':'all','check':'clean replay and rendered pages','limit':'official I/O and contest rules unknown'}]);csvwrite(ROOT/'claim_evidence.csv',claims)
print(json.dumps({'paper_chars':len(paper),'report_chars':len(report),'pdf_pages':len(qa),'figures':len(list((ROOT/'figures').glob('*.png')))},ensure_ascii=False))
