import json,csv,math,html,re,os,datetime,hashlib
from pathlib import Path
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parents[1]/'.cache/matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.pagesizes import A4
from solver import E,save,instance
TASKS=['Q1-S1','Q1-S2','Q1-F1','Q1-F2','Q2-N','Q2-C']
def csvsave(p,rows):
 with Path(p).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def pct(x):return f'{x*100:.2f}%'
def mdtable(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(str(x) for x in r)+' |' for r in rows)
def figures(ms,sens,ex):
 f=E/'figures';f.mkdir(exist_ok=True);fp=Path('C:/Windows/Fonts/msyh.ttc')
 if fp.exists():font_manager.fontManager.addfont(str(fp));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(fp)).get_name()
 plt.rcParams['axes.unicode_minus']=False;plt.rcParams['font.size']=10
 fig,axs=plt.subplots(1,2,figsize=(11,4),constrained_layout=True);scatter=[]
 for ax,t in zip(axs,TASKS[:2]):
  rr=[r for r in ex if r['task']==t];ax.scatter([r['Uv']*100 for r in rr],[r['Uw']*100 for r in rr],alpha=.5,label='全部合法候选');m=ms[t];ax.scatter([m['Uv']*100],[m['Uw']*100],marker='*',s=180,c='crimson',label='推荐非支配点');ax.set(xlabel='名义空间利用率 (%)',ylabel='载重利用率 (%)',title=t+' 单车有限库存');ax.grid(alpha=.2);ax.legend(fontsize=8);scatter.extend(rr)
 fig.savefig(f/'single_frontier.png',dpi=180);plt.close(fig);csvsave(f/'single_frontier.csv',scatter)
 fig,axs=plt.subplots(2,1,figsize=(11,6),constrained_layout=True);bars=[]
 for ax,t in zip(axs,['Q1-F1','Q1-F2']):
  vv=ms[t]['vehicles'];x=np.arange(len(vv));ax.bar(x-.18,[r['Uv']*100 for r in vv],.36,label='空间利用率');ax.bar(x+.18,[r['Uw']*100 for r in vv],.36,label='载重利用率');ax.set(xticks=x,xticklabels=[r['vehicle_id'] for r in vv],ylabel='利用率 (%)',title=t+' 逐车实际装载');ax.tick_params(axis='x',labelsize=7);ax.legend();bars.extend({'task':t,**{k:r[k] for k in ['vehicle_id','vehicle_type','items','volume_m3','weight_kg','Uv','Uw']}} for r in vv)
 fig.savefig(f/'fleet_utilization.png',dpi=180);plt.close(fig);csvsave(f/'fleet_utilization.csv',bars)
 labels=[];ns=[];cs=[];comparison=[]
 for t in ['Q1-F1','Q1-F2','Q2-N','Q2-C']:
  rr=[r for r in ex if r['task']==t];base=next(r for r in rr if r['method']=='baseline');best=min(rr,key=lambda r:(r['C'],r['N']) if t=='Q2-C' else (r['N'],r['C']))
  for name,m in [('基准',base),('多启动',best),('最终',ms[t])]:labels.append(t+'\n'+name);ns.append(m['N']);cs.append(m['C']);comparison.append({'task':t,'method':name,'N':m['N'],'C_yuan':m['C']})
 fig,ax=plt.subplots(figsize=(12,4),constrained_layout=True);x=np.arange(len(labels));ax.bar(x,ns,color=['gray','steelblue','seagreen']*4);ax.set(xticks=x,xticklabels=labels,ylabel='运输车辆数 (辆)',title='同一附件1：基准、候选比较和最终自检可行方案');ax.grid(axis='y',alpha=.2);fig.savefig(f/'method_comparison.png',dpi=180);plt.close(fig);csvsave(f/'method_comparison.csv',comparison)
 sr=[r for r in sens if r['task']=='Q2-C'];fig,axs=plt.subplots(2,2,figsize=(13,9),constrained_layout=True)
 groups=[('geometry','几何参数'),('load','载荷参数'),('cargo_geometry','货物尺寸'),('demand','需求参数')]
 for ax,(g,title) in zip(axs.flat,groups):
  rr=[r for r in sr if r['group']==g];x=np.arange(len(rr));ax.bar(x,[r['C'] for r in rr]);ax.axhline(7000,color='crimson',ls='--',label='同实验基准7000元');ax.set(xticks=x,xticklabels=[r['scenario'] for r in rr],ylabel='候选运输成本 (元)',title=title);ax.tick_params(axis='x',rotation=35,labelsize=8);ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2)
 fig.savefig(f/'sensitivity.png',dpi=180);plt.close(fig);csvsave(f/'sensitivity.csv',sr)
 cols=list(csv.DictReader((E/'plans/Q1-F2/selected/placements.csv').open(encoding='utf-8-sig')));cols=[r for r in cols if r['vehicle_id']=='V001'];palette={'G1':'#4c78a8','G2':'#f58518','G3':'#e45756','G4':'#72b7b2','G5':'#54a24b'};fig=plt.figure(figsize=(10,6));ax=fig.add_subplot(111,projection='3d')
 for r in cols:
  x,y,z=[float(r[k+'_cm']) for k in 'xyz'];dx,dy,dz=[float(r['d'+k+'_cm']) for k in 'xyz'];ax.bar3d(x,y,z,dx,dy,dz,color=palette[r['cargo_type']],alpha=.35,edgecolor='#333333',linewidth=.2,shade=True)
 ax.set(xlim=(0,680),ylim=(0,245),zlim=(0,250),xlabel='x 朝车头 (cm)',ylabel='y 朝左侧 (cm)',zlabel='z 向上 (cm)',title='Q1-F2 第一车：标准支撑与易碎顶层');ax.set_box_aspect((680,245,250));ax.view_init(25,235);fig.tight_layout();fig.savefig(f/'placement_3d.png',dpi=180);plt.close(fig);csvsave(f/'placement_3d.csv',cols)
 return comparison
def write_docs(ms,sens,ex,comparison):
 data=instance();vc={v['vehicle_type']:v for v in data['vehicles']};vals=[]
 for t in TASKS:
  m=ms[t];b=m.get('bounds');vals.append([t,f"{m['n1']}T1+{m['n2']}T2",m['N'],m['C'],pct(m['Uv']),pct(m['Uw']),'—' if not b else b['count_lower_bound']])
 main_table=mdtable(['任务','车型组成','车辆数','费用/元','空间利用率','载重利用率','车辆下界'],vals)
 ctable=mdtable(['货物','类别','尺寸/cm','单重/kg','数量','体积/m³','密度/kg·m⁻³'],[[c['cargo_type'],{'standard':'标准','fragile':'易碎','directional':'定向'}[c['category']],f"{c['l_cm']}×{c['w_cm']}×{c['h_cm']}",c['weight_kg'],c['quantity'],f"{math.prod([c[k+'_cm'] for k in ['l','w','h']])*c['quantity']/1e6:.2f}",f"{c['weight_kg']/(math.prod([c[k+'_cm'] for k in ['l','w','h']])/1e6):.2f}"] for c in data['cargo']])
 compare_table=mdtable(['任务','方法','车辆数','费用/元'],[[r['task'],r['method'],r['N'],r['C_yuan']] for r in comparison])
 st=[r for r in sens if r['task']=='Q2-C'];stable=mdtable(['参数场景','T1数量','T2数量','总车数','费用/元','空间利用率','载重利用率'],[[r['scenario'],r['n1'],r['n2'],r['N'],r['C'],pct(r['Uv']),pct(r['Uw'])] for r in st])
 valrecords={t:load(E/f'plans/{t}/selected/validation.json') for t in TASKS};paircount=sum(s['pair_count'] for t,v in valrecords.items() for s in v['vehicles']);maxp=max(s['max_pressure_kg_m2'] for v in valrecords.values() for s in v['vehicles']);mintop=min(s['min_top_gap_cm'] for v in valrecords.values() for s in v['vehicles'])
 ext=load(E/'extension/summary.json');replay=load(E/'replay/fresh1/receipt.json');calls=load(E/'logs/actual_solver_calls.json');nondoms={t:load(E/f'plans/{t}/pareto.json')['points'] for t in TASKS[:2]}
 dp=[load(E/f'deep_columns/{v}/receipt.json') for v in ['T1','T2']]
 runtimes=[r['runtime_seconds'] for r in ex];ratio=(12600-9000)/12600*100;ratio2=(9800-7000)/9800*100
 paper=f'''# 多场景、多目标货物运输装箱策略优化

## 摘要

针对 2026 年第十六届 MathorCup D 题附件1的 3000 件混合货物，本文先区分单车双目标选货、单车型整批配送和混合车型两类目标，再建立带朝向、支撑、累计承压和顶部间隙的三维装箱模型。原始货物总体积为 287.35 m³，总质量为 41100 kg。采用可独立复核的嵌套底面竖列，将空间构造与运输目标相连接；比较断头式分割基准、最大剩余矩形多启动构造、最小占地列模板整数规划及成对重装。全部正式方案按逐件坐标重建支撑和载荷，检查库存、边界、姿态、重叠和承压。推荐单车车型1的空间/载重利用率为 {pct(ms['Q1-S1']['Uv'])}/{pct(ms['Q1-S1']['Uw'])}，车型2为 {pct(ms['Q1-S2']['Uv'])}/{pct(ms['Q1-S2']['Uw'])}。全批次仅用车型1得到 20 车、9000 元可行方案，仅用车型2得到 10 车、7000 元；允许混合车型时，最少车辆与最低费用搜索均选出 10 辆车型2。对应总体体积/重量松弛下界分别为16车和7车，混合成本下界4900元，本文不宣称原三维问题的全局最优。348次参数求解揭示：尺寸、易碎需求和朝向解释比额定载重的小幅变化更容易改变车数。本文交付六类逐件方案、可运行程序、重新计算记录及面向企业的独立技术报告。

关键词：三维装箱；有限库存；双目标；支撑列；累计承压；车辆组成；可行上界

## 1 问题理解与任务联系

题目背景中的利润和运输费用相同不足以建立每件利润模型，缺少运价和收入数据。因此本研究只优化题目明列的利用率、运输车辆数及每趟成本。单车任务允许从有限库存选取子集，未装货不构成丢失；整批任务必须使全部3000件恰好出现一次。两类利用率分别以名义车厢体积和额定载重为分母，不能将车数、费用或利用率相互替代。

Q1-S1、Q1-S2分别是车型1、车型2的单车双目标任务；Q1-F1、Q1-F2分别要求只用一种车型运完全部货物；Q2-N以车辆总数最少为主目标，同车数以费用择优；Q2-C以运输费用最低为主目标，同费用再以车数择优。问题3依据这些真实输出讨论模型、程序性能及参数影响。Q1-F不能简单复制单车选货结果，否则某些货物会始终没有运走。问题2的两个目标共享全部合法方案，各自排序；二者最终相同是本实例的观测结果，不能先假设二者等价。

各任务的输入均为附件1库存、长宽高、重量、类别及两种车型容量与费用；输出包括车辆归属、每件坐标和原轴置换、支撑关系、类型覆盖、逐车利用率和目标值。附2只有尺寸与若干费用片段，不能替代正式库存，也不能凭尺寸造出整批运输最优结果。

## 2 原材料审计与数据分析

三份指定原文件均核对 SHA-256，全部核心字段对照 DOCX 段落和表格、PDF逐问及XLSX单元格。审计副本见 data/raw_audit.json，规范化表见 data/cargo.csv、vehicles.csv。附件1未发现缺值、负值或重复类型，故不虚构数据清洗步骤。件号采用 G1-0001 等可复核序列。除明确人工场景外，输入原值不改变。

{ctable}

车型1为420×210×220cm、6000kg、450元/趟，车型2为680×245×250cm、10000kg、700元/趟。顶部3cm间隙后的有效体积为19.1394m³和41.1502m³，但计算满容率仍使用名义体积19.404m³和41.65m³。G4占96m³，是最大体积来源；G3不能承受上层货物，G5必须保持40×40×60方向，这些规则造成空隙，不能只做体积装箱。

所有货物的最大密度为G5的187.5kg/m³。若任何合法单车装载体积不超过有效车厢体积，则其重量不超过187.5倍有效体积，因此车型1载重利用率理论上不超过59.81%，车型2不超过77.16%。该界甚至没有考虑库存和几何损失，已经排除了本批货物使单车同时达到100%满容和100%满载的可能。提升载重指标不应被误写为实现满载。

## 3 坐标、假设和约束解释

坐标原点固定在车厢右后下，x朝车头、y朝左侧、z向上，单位厘米。质量单位千克，面积由cm²除10000转换为m²，费用单位元/趟；数值容差1e-7cm。

标准件和主场景易碎件允许去重后的正交轴置换；定向件只允许原始长宽高。易碎“仅单层/不可堆叠”解释为易碎件之上不再放置任何货物，易碎件本身可在地板或标准件顶面，并完整贴合。主场景使用一个下层箱体完整覆盖上层底面，属于可核验的保守子空间；多个标准顶面共同支撑在本算法中不利用。普通非地板件也采用完整单底面支撑，避免未经验证的悬空。

质量均匀、重心在几何中心是缺少重心数据时的假设。嵌套底面保证定向件直接上层的重心在其投影范围内。下层承压按实际接触面积和上方累计重量计算，地板仅检查总额定载重，题面没有地板局部承压值。基准承压不计本件自重，另运行计入自重场景。所有货物满足z+h≤H-3，而非只将顶层厚度减3。

允许易碎六种置换不等于附件明示易碎可倒置，因此保持原高度另列情景。如果实际包装要求“向上”，应采用更严格场景。本研究保留这项歧义而不将研究假设改写为题目事实。现实车辆加速度、绑扎摩擦、叉车作业顺序及道路振动没有输入，本模型证明的是所述静态几何与荷载条件下的可行性。

## 4 数学模型

### 4.1 决策变量与几何条件

设i为逐件货物，k为候选车辆，o为货物允许的原轴置换。a(i,k)为是否装入车辆k的0/1变量，b(k,t)为车型变量；单车子集有选择变量s(i)，整批任务固定s(i)=1。坐标为x(i)、y(i)、z(i)，置换尺寸为d_x(i)、d_y(i)、d_z(i)。同车两件必须在至少一个轴分离；接触允许相等，正体积相交禁止。

```text
sum_k a(i,k) = s(i)
0 <= x(i); x(i)+d_x(i) <= L(k)
0 <= y(i); y(i)+d_y(i) <= W(k)
0 <= z(i); z(i)+d_z(i) <= H(k)-3
sum_i m(i)*a(i,k) <= M(k)
same vehicle pair (i,j): at least one of
x(i)+d_x(i)<=x(j), x(j)+d_x(j)<=x(i),
y(i)+d_y(i)<=y(j), y(j)+d_y(j)<=y(i),
z(i)+d_z(i)<=z(j), z(j)+d_z(j)<=z(i)
```

这些公式定义原目标的几何可行域；程序用明确坐标构造代替同时求解所有连续变量的大规模混合整数模型，从而使每个候选都可检查。算法限制进一步缩小原可行域，故构造最少车不代表原连续三维空间最少车。

### 4.2 支撑图、累计荷载与承压

每件非地板货物仅有一个直接支持者parent(i)，满足上下表面同高且下层投影包含其底面；下层不得易碎，易碎货物下层必须标准。按高度从高到低传播载荷：T(i)是包括i自重的整条上方子树重量，A(i)为i与支持者的接触底面积。界面压强采用质量面密度：

```text
T(i) = m(i) + sum_{{j:parent(j)=i}} T(j)
p(parent(i),i) = T(i) / A(i) <= 500 kg/m²
A(i) = d_x(i)*d_y(i)/10000
sum_{{floor item i}} T(i) = total vehicle cargo mass
```

这不是只检查直接上一层。柱列中上层重量必须一路累加到每个下层接触面。计本件自重分支将parent(i)自重加入界面分子。由于采用单支持链而非多点分配，载荷守恒可以直接验证；复杂多支持分配尚未纳入可认证输出。

### 4.3 六类目标

```text
Uv(k) = cargo volume in k / [L(k)*W(k)*H(k)]
Uw(k) = cargo mass in k / M(k)
single vehicle: maximize (Uv, Uw) in nondominated order
fleet Uv = total cargo volume / sum_k nominal vehicle volume(k)
fleet Uw = total cargo mass / sum_k rated capacity(k)
Q1-F1, Q1-F2, Q2-N: min N = n1+n2; tie-break by C
Q2-C: min C = 450*n1 + 700*n2; tie-break by N
```

单车搜索中的质量偏好参数α=0、0.5、1只引导候选生成，最终比较仍按(Uv,Uw)非支配关系；它不替代题目的双目标。按采样候选，车型1/2分别剩一个独特非支配点，不能据此推断真正Pareto前沿只有一个点。推荐采用空间利用率优先、相同空间时载重优先的公开偏好，所有样本及拒载类型数均保留。整批车队利用率按总容量加权定义，绝不直接平均逐车比率。

### 4.4 下界与最优性范围

同车型以总有效体积和总重量守恒求向上取整下界；混合场景枚举非负整数车型数，使总有效体积和总额定载重至少满足全批需求，再分别最小化N和C。该松弛给车型1至少16车、车型2至少7车、混合至少7车、成本至少4900元。由21或20车构造、10车构造均不能证明达到这些界。

列模板整数规划另有变量u(p)表示合法列p使用次数，约束 sum_p count(t,p)*u(p)=q(t)，目标最小 sum_p area(p)*u(p)。它在冻结模板库内求最小占地，随后仍须实际二维装入车辆并展开三维坐标。模板库MILP最优不等于原问题最优，最小占地也不直接等于最少车。

## 5 方法比较与求解实现

先设计满足约束的嵌套竖列：底层类型与姿态、同类层数、可包含的顶层另一类型及其层数，由车高和累计承压过滤；易碎出现后停止。车型1/2的初始库分别401/536列，模板记录逐层尺寸、姿态、类型数量、重量、体积及占地。

基准按底面面积优先选列，用断头式矩形分割管理地板剩余空间，无法回收跨分割片的大矩形。第二方法使用最大剩余矩形，对每个合法列与剩余片计算高度密度、体积/质量偏好、边长贴合、易碎优先级及轻度固定种子扰动，选入后分割相交矩形并删除包含片。全量时保留足够G1支持剩余G3，避免先用光标准件而迫使易碎全部占地板。该策略由真实烟测未覆盖易碎支持关系触发，并记录在失败/改进日志。

比较预算提前固定为每次120秒、阶段900秒，种子0、11、23，α为0、0.5、1，易碎优先级1、3、6，每任务27种多启动候选加1种基准，共168次。全部合法性以独立编写的checker.py从坐标计算，搜索代码的accepted字段不作为证据。实际单次构造耗时范围{min(runtimes):.4f}至{max(runtimes):.4f}秒；该数不含文件写出和检查时间，不冒充端到端性能。整个168候选阶段实测约45.65秒。

进一步求解精确库存的最小占地模板MILP，再用多种排序及固定种子二维最佳匹配装车。初始模板库最小占地分别163.5575m²和150.4875m²，HiGHS返回库内最优。这意味着该库二维面积下界为19辆T1、10辆T2；实际构造分别20、10辆。为检验两类型模板是否过于狭窄，再向兼容顶面逐层添加新类型、最多四轮/30000状态，扩展到{dp[0]['library_size']}和{dp[1]['library_size']}列。扩展库的最小占地未进一步下降，64次二维装车也未改进20/10车，这一未改善结果一并保留，不能被隐藏成新最优声明。

最后对成对车辆的合并货物重新构造，在相同约束下尝试替换以降低车数/费用。车型1按体积必要条件排除不可能合并对，运行54次；混合两个目标分别810次，共1674次，均未进一步改进。它只说明指定邻域与种子下未找到改善，不是局部乃至全局最优证明。保留MILP改善车型1的20车方案。

{compare_table}

相对原基准，车型1由28车降到20车，费用降低{ratio:.2f}%；车型2由14车降到10车，费用降低{ratio2:.2f}%。这是同一原始库存与解释下的描述性比较，不能据单个题目泛化为所有物流数据都改善同样百分比。

![同条件方法比较](figures/method_comparison.png)

## 6 六类实际方案与结果

{main_table}

所有整批任务均运输G1=800、G2=1000、G3=300、G4=400、G5=500，全部3000件，未运数均为0。费用仅包含附件1每趟450/700元，不增加未提供的路线、里程和库存成本。

### 6.1 单车选货与非支配样本

车型1推荐装入G1=89、G2=268，合计357件、18.133m³、3212kg；未装G1=711、G2=732、G3=300、G4=400、G5=500。车型2推荐装入G5=408，合计408件、39.168m³、7344kg，未装G1=800、G2=1000、G3=300、G4=400、G5=92。单车有限库存任务允许不装某类别，因此推荐点不必人为强迫“每类都装”；它仍受方向、重量和堆叠约束。车型2推荐只装G5，是在所搜样本中两指标都较高的事实，也说明背景的搭配说法不应变为无依据的配比硬约束。

两车型在采样池分别有{len(nondoms['Q1-S1'])}和{len(nondoms['Q1-S2'])}个独特非支配点，全部候选散点见图。点集来源为28次构造，每个点保留实际坐标。前沿尚未被精确证明；未来可用更强单车epsilon约束搜索扩充。

![单车有限库存候选与推荐点](figures/single_frontier.png)

### 6.2 整批单车型配送

T1的20车名义容量合计388.08m³、120000kg，车队空间利用率{pct(ms['Q1-F1']['Uv'])}，载重利用率{pct(ms['Q1-F1']['Uw'])}。T2的10车名义容量合计416.5m³、100000kg，车队空间利用率68.99%，载重利用率41.10%。T1的总空间利用率较高却费用较高，说明“平均更满”不能替代低费用目标。逐车利用率不同，末车和某些易碎车存在低层空隙；逐车数据完整保留在vehicle_summary.csv。

![单车型方案逐车利用率](figures/fleet_utilization.png)

### 6.3 混合车型目标对比

原费用450/700下，搜索得到的最少车辆候选和最低费用候选均为10T2、7000元，相对20T1节省2000元（22.22%）。不能将这写成任何费用比例下两目标均同解。在后文T2费用1000元场景，最少车搜索仍10T2、10000元，成本候选变为12T1+4T2、16车、9400元，出现增加车辆降低费用的权衡。该场景仍是给定启发式池内的可行推荐，未证全局成本最优。

### 6.4 逐件坐标与装卸实施

完整坐标分散于 plans/六任务/selected/placements.csv，包含task_id、vehicle_id、vehicle_type、item_id、cargo_type、x/y/z、dx/dy/dz、orientation及support_ids。orientation例如yxz表示车长轴取原宽、车宽轴取原长、车高轴取原高。每车先摆地板箱，再按z由低到高摆放，易碎支持列先放标准底层，最后放易碎；支撑件不得在卸货时提前抽出。

图示Q1-F2第一车，每个箱体均来自真实坐标；整批正文不逐个画3000件，但附件提供逐件CSV，代码能重算并制图。单车与整批件号在各任务内独立，不能跨任务相加库存。

![完整配送第一车的三维坐标图](figures/placement_3d.png)

## 7 结果核验、小实例与程序性能

### 7.1 从坐标独立重算的生产者自检

checker.py不导入构造器，从原始尺寸和姿态重建箱体，逐车检查所有货物对，并从接触面找支持者，不盲信support_ids。按从上到下累加子树质量，检查每层承压和地板荷载守恒。正式六类方案检查了{paircount}对货物，全部通过本研究自检；最大界面累计承压为{maxp:.2f}kg/m²，最小顶部间隙为{mintop:.2f}cm，均满足声明场景。库存、单车选货数量、车辆类型和(Uv,Uw,N,C)也由检查器重新计算。

这是一位生产者独立实现检查职责的自检，不能改名为独立验收。另一个新上下文审查者将接收终态材料，本文写作时其结论尚未产生。真实动态运输安全也不由本静态检查认证。

小批烟测使用G1/G2/G3/G4/G5数量8/8/2/4/6，共28件，包含标准支撑易碎及定向堆叠。故意将一件x坐标改成9999cm，检查器以边界违反拒绝；将承压阈值改为1kg/m²，累计压力检查拒绝。首次烟测虽然几何合法但未产生易碎标准支撑，之后加入支持库存保留和显式关系断言，保留原失败。错误案例不能被作为正常正式方案。

### 7.2 小实例精确界与六任务重新计算

另构建保持G1原尺寸/单重的人工小实例：车厢60×40×63cm，间隙3cm，库存4件G1。有效体积144000cm³恰好是单件72000cm³的两倍，所以任何姿态最多两件；程序实际叠两件达界，且承压通过。它精确验证该小实例的体积界和构造链路，不证明原批次最优。

在全新 replay/fresh1 目录中，从规范化原数据重新计算全部六任务；T1整批重新求模板MILP及二维布局，其余任务按冻结种子/偏好重新构造。六任务N、费用、利用率、体积、重量及库存与正式输出一致，坐标字节比较记录保留在receipt.json。该复跑不读取正式placements作为计算答案，只用冻结配置和程序；{replay['seconds']:.3f}秒包含计算、写出及自检，是本机一次端到端六任务重放观测。

### 7.3 复杂度与环境

列生成的状态数受车型高度、姿态数和截断规则限制。地板构造每次比较列与剩余矩形，约O(P×R×K)量级，P为列数、R为剩余片数、K为选列数；包含片删除的朴素实现为O(R²)。检查器在车k上使用O(n_k²)轴向比较，支持搜索也为O(n_k²)，适合本批千件数量级。外层模板MILP是整数优化，不能由小样本耗时保证大规模多类型速度。

Python3.12.8，numpy1.26.4、scipy1.17.1、matplotlib3.10.9及本地DOCX/XLSX/PDF解析库，全部离线，无安装、上传或投稿。计算前声明3600秒窗口和1800MB内存目标；后者不是OS强制，模型/token/费用遥测未知，保持null。资源日志保留两次并发目标偏离，其中MILP与参数阶段最小重叠约1.84秒；小实例验证也曾与局部重装运行重叠，违反自声明单求解进程目标。相应阶段不宣称严格串行时间可比。源路径错误、numpy诊断序列化、文档脚本引号/花括号错误与补丁构造错误为工具恢复，列库和重装为研究迭代，未清零任何失败历史。

## 8 参数影响与解释稳健性

每个人工场景保持其他字段不变，用相同最大矩形构造、α=0.2、易碎优先级3、种子0/11/23重新优化Q1两个单车及Q2两个目标。29场景共348次调用，配置、逐件坐标及检查均保存。两个Q2目标从相同已检验的可行候选池选择；这一共享选择修正了成本启发式有时被车数启发式支配的结果，原未修正记录仍保留。表中“费用最小”指池内费用最小，没有将有限搜索改称全局最优。

{stable}

### 8.1 车厢尺寸与间隙

长、宽、高分别±10%，费用不变，是不同车厢净尺寸的情景而非官方更换车型报价。缩短10%得到12车8150元，缩窄10%成本推荐为3T1+10T2、13车8350元；该场景最少车候选为12T2、8400元，展示真实目标差别。加大尺寸10%三种场景均得到1T1+9T2、6750元。空间比率的分母也随着车型体积改变，因此大车方案更低利用率不意味着运输效率必然变差。

间隙0/6/10cm是研究场景，0cm不满足正式原题3cm，因此不能用它替代正式方案。0cm时出现9T2+1T1、6750元，6/10cm仍10T2、7000元。整数层数由高度阈值控制，微小空间变化能使标准列或顶层件数跳变，不能拟合为连续线性成本趋势。

### 8.2 额定载重、单重与承压

额定载重降低50%时需11T2、7700元，车队重量利用率74.73%；提高50%时仍10T2，但利用率降至27.40%，证明加大载重不是当前主瓶颈。货物单重独立±20%而几何固定，仍10T2；重量利用率分别32.88%和49.32%。500kg/m²降为300时需1T1+10T2、7450元，提高至700仍10T2。其机制是承压改变可堆叠层数，而不是把500解释成单件重量上限。

计下层自重的替代承压解释仍得到10T2、7000元。这是重新构造后的条件结果，不能证明所有旧坐标在所有承压解释下都通过，也不能证明这项解释对其他库存不敏感。

### 8.3 货物尺寸、数量和类型比例

尺寸独立缩小10%、重量不变时得到8T2、5600元，扩大10%得到13T2、9100元；固定密度分支同时将重量乘尺寸比例三次方，车数与费用在此次搜索中相同，但重量利用率明显不同。两种物理情景单独记录，避免把形状变化和质量变化混成同一实验。

需求整体0.5倍和1.5倍得到5T2、3500元与15T2、10500元。本题观察近似比例，不是任意需求下严格线性定律。仅易碎需求减半时8T2、5600元；增加50%时12T2、8400元，空间利用率从79.94%降至61.69%，反映低层/不可承载区域的重要性。

### 8.4 费用比例和双目标分离

当T2成本改为450元，仍10T2、4500元；改为1000元时最低费用样本为12T1+4T2、9400元，总车数16，而最少车样本为10T2、10000元。成本改变只作用目标，不改变任何几何规则；本实验重新运行相同搜索，不仅计算已有方案的新价格。仍应在更强全局算法中验证车型组合极小值。

### 8.5 易碎解释的条件结论

G3保持原高度40cm时允许平面转动，底面为70×50或50×70，不能由单个G1或G2完整支持，故主模型中易碎必须在地板。该场景得到1T1+14T2、15车10250元。允许置换但易碎强制地板为11T2、7700元；主规则允许标准支持时10T2、7000元。差异具有决策意义，企业需要确认包装朝向规则，再使用相应方案，不能把不同解释的低费用混进同一正式结论。

![同条件参数重新求解成本](figures/sensitivity.png)

## 9 附件2的可支持扩展

附件2的仓库区间按上端转cm，车型净尺寸按区间下端转cm，化验尺寸另存，不混合择取有利端点。8类产品、5行可视为封闭箱体的公路车型，共40个单件正交几何适配组合，在人工假设可任意正交旋转和3cm间隙下均适配。解析产物保留原单元格与区间上下端。

缺重量、数量、类别、额定载重和运输距离，故不输出伪造“官方大批次最优运输”。元/1000km不能直接作为元/趟。铁路/水路行费用口径不完整，栏板高度不等于封闭净高，阶梯车厢不是长方体，均排除相应装箱模型。这里验证的是解析与单件适配通道，不能推断大规模整批泛化性能。

## 10 企业建议、模型局限与结论

在本研究主解释与当前可行候选下，全批运输建议10辆车型2、7000元，名义空间利用率68.99%、载重利用率41.10%；若车辆只允许车型1，采用20辆、9000元。生产执行前核实易碎朝向和实际可承压区域，按CSV由低到高装载，标准支持件必须先放并保留到上件卸下。需要单车选择时使用相应推荐点，不将其重复作为整批配送。

本研究优点是每个结果都有完整坐标、姿态、库存与荷载证据，程序可在本地从原数据重新计算，失败和未改善实验均保留。局限是单支持嵌套列缩小了原可行域，二维启发式受碎片化影响，未覆盖所有正交非列布局；下界仍宽，原问题最优性未知。车型1可行上界20与下界16相差4辆，车型2/混合上界10与下界7相差3辆；相对下界的车数差为25.00%和42.86%。混合费用7000与下界4900相差2100元、42.86%。这些是上界-下界差，不是实际最优误差的精确测量。

后续有依据的改进方向是多标准件联合支持的接触并集模型、更多空间模式与更紧的几何下界，以及经过明确解释的精确单车epsilon约束；目前没有这些证据时不提高论文措辞。无需为了追求满载增加未提供的高密度货物，也不将运输费用最低等同利润最大。

## 参考材料

[1] 指定原文件《2026年第十六届MathorCup数学应用挑战赛题目—D题.pdf》，3页，原始SHA-256记录见data/raw_audit.json。

[2] 指定原文件《附件1.docx》，车辆参数段落4—10，类别段落13—16，承压/间隙段落18—19及货物表1。

[3] 指定原文件《附件2：验证数据集.xlsx》，箱装产品尺寸、车型尺寸、Sheet3。未引用或借用外部论文，未虚构文献。

## 附录：可复现程序与证据索引

程序入口：src/solver.py（六任务通用构造）、src/checker.py（坐标自检）、src/column_milp.py和deep_columns.py（研究库）、src/local_search.py（重装）、src/reproduce.py（六任务干净重算）。原始字段规范化、解释表和实验配置位于data/、logs/；所有候选和失败均保留，不只保留最好一次。

程序附件运行命令、通用JSON格式、错误退出状态及机器可读输出见README.md。六类正式方案位于plans/，参数原始结果位于sensitivity/，逐图数据与PNG位于figures/。要求—公式—运行—坐标—检查—正文的连接见evidence.csv，生产者自检状态和原题未解最优性见result.json及TODO.md。本文PDF由paper.md导出并逐页渲染核查，不代表任何比赛提交格式已经合规；未收到竞赛提交规则，不自动上传。
'''
 (E/'paper.md').write_text(paper,encoding='utf-8')
 report=f'''# 物流企业装载与车型选择技术报告

## 适用范围与管理结论

本报告针对附件1原库存3000件、287.35m³、41100kg，使用每趟车型1成本450元、车型2成本700元。在允许易碎件正交置换、易碎件可以被一个标准件完整支持、下层累计承压500kg/m²且顶部留3cm的研究主场景下，建议采用10辆车型2，运输费用7000元，名义空间利用率68.99%、载重利用率41.10%。若只能使用车型1，采用20辆、9000元方案，空间利用率{pct(ms['Q1-F1']['Uv'])}、载重利用率{pct(ms['Q1-F1']['Uw'])}。每一件都有实际坐标并经生产者自检，方案无需靠总体体积猜测可装下。

这些方案是已找到的合法上界，尚未证明原问题全局最优。总有效体积/重量给车型1至少16车、车型2或混合至少7车，混合成本至少4900元。上述界宽，不能据程序成功结束宣布最少车或最低费用已经精确达到。

## 六个任务的具体答案

{main_table}

单车有限库存任务允许只装一部分货物：车型1装89件G1和268件G2，车型2装408件G5。两者的有限采样池中均留下一个独特非支配点；未证明连续三维Pareto前沿完整。全批任务均覆盖五类全部原库存，不能重复单车结果代替全量运输。原费用下，混合两个目标推荐相同；费用比例改变时目标可能分离。

## 模型与程序怎样工作

坐标以右后下为原点，x向车头、y向左、z向上。程序先生成合法竖列，逐层确保底面完全支撑、方向正确、上层累计压力不过限、易碎件上方不承载；再把列的底部矩形排入车底，展开每件箱体位置。对所有正式输出，另一段检查代码从坐标重建支撑关系，逐对检查重叠，逐层传播重量，核验整车载重、库存和顶部空隙。

较简单的断头式矩形分割基准得到28辆T1、14辆T2；最大剩余矩形、多启动及模板占地整数规划分别改善到20辆T1、10辆T2。T1费用相对基准降低28.57%，T2降低28.57%，这是该批次一次有控制条件的比较。列模板整数规划只保证当前库内占地最小，实际车数与原三维最优仍由空间排列影响。成对重装1674次未再找到改善，不能将未找到解释为已经证明最优。

程序用Python3.12.8与现有科学库，离线运行。168次基础候选比较约45.65秒，单次构造不含写出和核验约{min(runtimes):.4f}—{max(runtimes):.4f}秒，六正式任务一次重新计算/写出/检查约{replay['seconds']:.3f}秒；这些是本机观测，不能保证任意大规模数据速度。检查复杂度随每车件数平方增长，多类型模板生成与整数规划也会增加费用。

## 参数变化对经营决策的影响

29个参数场景共348次求解，每场景固定搜索策略与种子组并重新核验。详细表如下；“最低费用”仅指共享的已检验候选池中费用最小，不是全局最优认证。

{stable}

车厢尺寸关系到地板可拼排和整数层数：缩窄10%成本推荐13车8350元，而最少车候选12车8400元，实际出现“多1车少50元”。间隙0cm的6750元结果属于研究场景，不能违反原题3cm间隙使用。尺寸同比变化、固定质量与固定密度两种假设分别计算，不能混淆。

提高额定载重50%没有减少车数；降低50%则增加到11车7700元。这批货物主要受几何与易碎区域限制，不建议仅通过升级载重吨位解决装载问题。承压限值降到300kg/m²增加到11车7450元。标准支撑件的数量和可用底面是必须检查的现场条件。

易碎货数量减半得到8车5600元，增加50%得到12车8400元。若G3必须保持原高度且底面70×50cm，则无法由单个标准箱完整支持，本保守模型得到15车10250元。企业必须确认朝向，不能直接将主场景7000元当作所有包装规则下的承诺。

T2单价改为1000元时，最少车候选10T2费用10000元；费用候选12T1+4T2费用9400元、16车。在“有限司机/场地”和“预算控制”之间需先确定经营目标，不能只比较平均满容率。

## 落地操作与交付程序

使用plans/任务/selected/placements.csv，每行一个实际箱体，按vehicle_id分车，按z从低到高装入；orientation定义原轴到车轴的置换，support_ids指明必须先摆放的承重件。易碎件最后放，卸载时先移除上件再抽支持箱。载重利用率不是支撑承压，二者均需检查。

README.md提供正式六任务重算及通用输入运行命令。data/是规范化原值，experiments/保留同条件比较，sensitivity/保留参数坐标和检查，replay/fresh1保留干净重放。可用 src/checker.py 单独检验方案，不以生成器的自称合法作凭据。若新箱体尺寸、重量或方向发生变化，先更新输入再重新运行，禁止手工缩放旧坐标后沿用合法标签。

附件2仅验证8类产品与5种封闭公路车的40个单件尺寸适配，不含完整质量和数量，不能据其编造运输费用最优。栏板与阶梯车厢需独立几何模型，不能强行套用长方体净尺寸。

## 风险与保留事项

以上通过的是明确静态假设下的生产者自检，新上下文独立审查尚未发生。本模型没有多支撑载荷分配、道路动态、摩擦和绑扎输入，仍需现场工程核实。全球最优性、官方易碎朝向解释与真实提交规则保持未闭合；本地研究没有联网、安装、上传或投稿。
'''
 (E/'technical_report.md').write_text(report,encoding='utf-8')
 save(E/'logs/publication_metrics.json',{'tasks':{t:{k:ms[t][k] for k in ['N','n1','n2','C','Uv','Uw']} for t in TASKS},'formal_pairs_checked':paircount,'max_pressure_kg_m2':maxp,'min_top_gap_cm':mintop,'producer_self_check':True,'independent_acceptance':None})
def pdf_export(md,pdf):
 pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));styles=getSampleStyleSheet()
 styles.add(ParagraphStyle(name='CN',fontName='STSong-Light',fontSize=10.3,leading=16,spaceAfter=7,wordWrap='CJK'))
 styles.add(ParagraphStyle(name='CNH1',fontName='STSong-Light',fontSize=18,leading=25,spaceAfter=14,spaceBefore=6,alignment=TA_CENTER))
 styles.add(ParagraphStyle(name='CNH2',fontName='STSong-Light',fontSize=14,leading=20,spaceBefore=13,spaceAfter=9,keepWithNext=True))
 styles.add(ParagraphStyle(name='CNH3',fontName='STSong-Light',fontSize=11.5,leading=17,spaceBefore=10,spaceAfter=7,keepWithNext=True))
 styles.add(ParagraphStyle(name='CNT',fontName='STSong-Light',fontSize=8,leading=11,wordWrap='CJK'))
 lines=Path(md).read_text(encoding='utf-8').splitlines();flow=[];i=0
 def para(s,style='CN'):return Paragraph(html.escape(s).replace('**',''),styles[style])
 while i<len(lines):
  ln=lines[i].strip()
  if not ln:i+=1;continue
  if ln.startswith('```'):
   i+=1;block=[]
   while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
   flow.append(Paragraph('<br/>'.join(html.escape(x) for x in block),styles['CNT']));flow.append(Spacer(1,7));i+=1;continue
  if ln.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    raw=lines[i].strip().strip('|').split('|');cells=[x.strip() for x in raw]
    if not all(re.fullmatch(r'[-: ]+',x) for x in cells):rows.append([para(x,'CNT') for x in cells])
    i+=1
   cols=len(rows[0]);width=475
   if cols==7:
    htext=[c.getPlainText() for c in rows[0]]
    if '尺寸/cm' in htext:ws=[38,42,85,50,42,60,80]
    elif htext[0]=='任务':ws=[70,92,45,65,77,77,49]
    else:ws=[120,42,42,44,65,81,81]
    ws=[w*width/sum(ws) for w in ws]
   elif cols==4:ws=[120,180,80,95]
   else:ws=[width/cols]*cols
   tb=Table(rows,colWidths=ws,repeatRows=1,hAlign='CENTER');tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef4')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#aab4be')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]));flow.extend([tb,Spacer(1,9)]);continue
  if ln.startswith('!['):
   m=re.match(r'!\[(.*?)\]\((.*?)\)',ln)
   if m:
    path=Path(md).parent/m[2];im=Image(str(path));scale=min(475/im.imageWidth,300/im.imageHeight);im.drawWidth=im.imageWidth*scale;im.drawHeight=im.imageHeight*scale;flow.extend([im,para(m[1],'CNT'),Spacer(1,9)])
   i+=1;continue
  if ln.startswith('# '):flow.append(para(ln[2:],'CNH1'))
  elif ln.startswith('## '):flow.append(para(ln[3:],'CNH2'))
  elif ln.startswith('### '):flow.append(para(ln[4:],'CNH3'))
  else:flow.append(para(ln))
  i+=1
 def footer(c,d):
  c.setFont('STSong-Light',8);c.setFillColor(colors.HexColor('#666666'));c.drawString(60,30,'离线原创试解 · 生产者自检 · 最优性未证');c.drawRightString(A4[0]-60,30,str(d.page))
 doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=60,leftMargin=60,topMargin=48,bottomMargin=48,title=Path(md).stem,author='R19-L3 offline producer');doc.build(flow,onFirstPage=footer,onLaterPages=footer)
def main():
 ms={t:load(E/f'plans/{t}/selected/metrics.json') for t in TASKS};sens=load(E/'sensitivity/results.json');ex=load(E/'experiments/summary.json');comp=figures(ms,sens,ex);write_docs(ms,sens,ex,comp);pdf_export(E/'paper.md',E/'paper.pdf');pdf_export(E/'technical_report.md',E/'technical_report.pdf');print('publication created')
if __name__=='__main__':main()
