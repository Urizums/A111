"""Consume fixed replay tables into one coherent Chinese MD/PDF research report."""
from pathlib import Path
import json,hashlib,html
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether
from reportlab.lib.pagesizes import A4
ex=Path('runs/R22/execution');science=ex/'science-v1';out=ex/'report-v1';out.mkdir(exist_ok=False);fig=out/'figures';fig.mkdir()
fontfile='C:/Windows/Fonts/simhei.ttf';plt.rcParams['font.family']=FontProperties(fname=fontfile).get_name();plt.rcParams['axes.unicode_minus']=False;plt.rcParams['font.size']=10
pdfmetrics.registerFont(TTFont('CN',fontfile))
def read(name):return pd.read_csv(science/'results'/name)
overall=read('group_overall.csv');stages=read('group_stage.csv');bands=read('group_band.csv');act=read('group_activity.csv');astage=read('group_activity_stage.csv');ab=read('group_activity_band.csv');daily=read('daily.csv');pair=read('paired_daily.csv');stores=read('group_store.csv');items=read('group_item.csv');combined=read('combined_first_two.csv');keys=read('keys.csv');solver=read('solver_daily.csv');bounds=pd.read_csv(science/'data/boundaries.csv');audit=json.loads((science/'data/audit.json').read_text());checks=json.loads((ex/'author-selfcheck-v1/selfcheck.json').read_text());origins=overall.origin.drop_duplicates().tolist();methods=['shared_ridge10','weekly_mean56'];labels={'shared_ridge10':'R：共享岭回归','weekly_mean56':'W：近56日星期均值'};cs={'shared_ridge10':'#176b8a','weekly_mean56':'#d2742a'}
def save(name):plt.savefig(fig/name,dpi=180,bbox_inches='tight',facecolor='white');plt.close();return name
f,axes=plt.subplots(1,3,figsize=(12,3.5));x=np.arange(3)
for m in methods:
    z=overall[overall.method_id==m]
    for ax,col,title,unit in zip(axes,['mae','loss_per_day','interval_score'],['点预测 MAE','每日两项损失','90%区间评分'],['件/键','元/日','件/键']):ax.bar(x+(-.18 if m==methods[0] else .18),z[col],.34,color=cs[m],label='R' if m==methods[0] else 'W');ax.set_title(title);ax.set_ylabel(unit);ax.set_xticks(x,['07-22','09-02','09-19']);ax.grid(axis='y',alpha=.2)
axes[0].legend();f.suptitle('图1 三个固定原点的42日总体表现');f.tight_layout();save('01_overview.png')
f,axes=plt.subplots(3,2,figsize=(10,8))
for i,o in enumerate(origins):
    for j,col in enumerate(['mae','loss_per_day']):
        ax=axes[i,j]
        for m in methods:
            z=bands[(bands.origin==o)&(bands.method_id==m)];ax.plot(z.band,z[col],'-o',color=cs[m],label='R' if m==methods[0] else 'W')
        ax.set_xticks(range(1,7),['1-7','8-14','15-21','22-28','29-35','36-42']);ax.set_title(o[:10]+'：'+('MAE' if j==0 else '每日损失'));ax.set_ylabel('件/键' if j==0 else '元/日');ax.grid(alpha=.2);ax.tick_params(axis='x',labelsize=8)
axes[0,0].legend();f.suptitle('图2 六个7日步长带：误差与损失并非同向');f.tight_layout();save('02_bands.png')
f,axes=plt.subplots(1,2,figsize=(10,4))
for m in methods:
    z=overall[overall.method_id==m];axes[0].plot(z.width,z.coverage,'-o',color=cs[m],label='R' if m==methods[0] else 'W')
    for _,r in z.iterrows():axes[0].annotate(r.origin[5:10],(r.width,r.coverage),fontsize=8,xytext=(2,5),textcoords='offset points')
    for i,o in enumerate(origins):
        a=act[(act.origin==o)&(act.method_id==m)];axes[1].scatter(i+(-.15 if m==methods[0] else .15),a[a.holiday==0].coverage,color=cs[m],marker='o');axes[1].scatter(i+(-.15 if m==methods[0] else .15),a[a.holiday==1].coverage,color=cs[m],marker='x',s=70)
axes[0].axhline(.9,color='gray',ls='--');axes[0].set_xlabel('平均区间宽度（件/键）');axes[0].set_ylabel('实测覆盖比例');axes[0].legend();axes[1].axhline(.9,color='gray',ls='--');axes[1].set_xticks(range(3),['07-22','09-02','09-19']);axes[1].set_ylabel('实测覆盖比例');axes[1].set_title('圆点：普通日；叉号：活动日');f.suptitle('图3 区间宽度、覆盖和活动分层');f.tight_layout();save('03_intervals.png')
f,axes=plt.subplots(3,1,figsize=(10,7))
for ax,o in zip(axes,origins):
    z=pair[pair.origin==o];ax.axhline(0,color='gray',lw=1);ax.plot(z.horizon,z.loss_W_minus_R,color='#485c70');a=z[z.holiday==1];ax.scatter(a.horizon,a.loss_W_minus_R,color='#d2742a',label='活动日');ax.set_title(o[:10]+'：W减R同日损失差');ax.set_ylabel('元/日');ax.set_xlabel('预测步长（日）');ax.grid(alpha=.2)
axes[0].legend();f.suptitle('图4 同日期配对差：正值表示R损失较低');f.tight_layout();save('04_daily_pair.png')
counts=ab[ab.method_id==methods[0]].pivot(index='origin',columns=['holiday','band'],values='days');mat=np.array([[counts.loc[o,(1,b)] for b in range(1,7)] for o in origins]);f,ax=plt.subplots(figsize=(9,3));im=ax.imshow(mat,cmap='YlOrBr',vmin=0,vmax=4,aspect='auto');ax.set_xticks(range(6),['1-7','8-14','15-21','22-28','29-35','36-42']);ax.set_yticks(range(3),[o[:10] for o in origins]);ax.set_xlabel('预测步长（日）')
for i in range(3):
    for j in range(6):ax.text(j,i,str(int(mat[i,j]))+'日' if mat[i,j] else '0日\n不可估计',ha='center',va='center',fontsize=10)
f.colorbar(im,ax=ax,label='活动日期数');ax.set_title('图5 活动×步长带的样本覆盖：0日不是0误差');f.tight_layout();save('05_activity_support.png')
f,axes=plt.subplots(2,1,figsize=(11,5.7))
for ax,df,dimension in [(axes[0],stores,'store_id'),(axes[1],items,'item_id')]:
    pv=df.pivot(index=['origin',dimension],columns='method_id',values='loss_per_day');pv['difference']=pv.weekly_mean56-pv.shared_ridge10;z=pv['difference'].unstack(dimension);ma=max(abs(z.to_numpy().ravel()));im=ax.imshow(z,cmap='RdBu_r',vmin=-ma,vmax=ma,aspect='auto');ax.set_xticks(range(len(z.columns)),z.columns);ax.set_yticks(range(3),[o[:10] for o in origins]);ax.set_title('店分层' if dimension=='store_id' else '品分层')
    for i in range(len(z)):
        for j in range(len(z.columns)):ax.text(j,i,f'{z.iloc[i,j]:.1f}',ha='center',va='center',fontsize=8)
    f.colorbar(im,ax=ax,label='W减R（元/日）')
f.suptitle('图6 店与品的每日损失差：各分组是网络总损失的一部分');f.tight_layout();save('06_store_item.png')
blocks=[]
def heading(t,level=1):blocks.append(('heading',t,level))
def p(t):blocks.append(('paragraph',t))
def table(headers,rows,caption):blocks.append(('table',headers,rows,caption))
def image(name,caption):blocks.append(('image',name,caption))
def fmt(v,n=3):return '不可估计' if pd.isna(v) else f'{v:.{n}f}'
def route(r):return r.origin[5:10]+'/'+('R' if r.method_id==methods[0] else 'W')
heading('固定42日需求预测与整数备货：三历史原点回放研究')
p('R22-02 中文技术研究报告 | 固定政策 R(alpha=10) 与 W(window=56) | 时区 Asia/Shanghai | 虚构离线生鲜网络案例')
heading('摘要',2)
p('本研究比较两条预先固定的统计与备货路线，在2026年7月22日、9月2日、9月19日18时分别预测并规划次日起连续42日。每窗包含12店×8品×42日，共4032个键；两路线共享信息可得规则、评价标签、情景构造、每日资源和损失目标。训练只采用原点当时已公布修订；评价采用11月4日18时可见最高修订。残差来自更早的原14日源预测，逐键回溯并以已发表10位小数点预测重算，只纳入全部96坐标所用成熟修订都已到达的整日。')
p('三窗R的MAE为2.938、2.566、2.546件/键，W为2.708、2.698、2.647件/键；R的两项平均每日损失为689.39、621.52、634.16元，W为738.59、683.20、677.79元。第一窗W点预测更准确，而R备货损失较低，说明平均绝对误差不足以替代非对称损失下的决策评价。名义90%区间实测覆盖均低于90%，R为77.98%、86.56%、88.76%，W为76.76%、88.00%、89.88%；较宽的区间也需结合漏出距离与区间评分判断。')
p('早晚步长差别随窗口变化。第一窗R远期MAE明显增大且偏高，第三窗普通日早晚差别很小，不能概括为普遍的42日外推恶化。每窗只有4个活动日且分布不均，第一与第三窗早期活动格为空，活动与期限的作用无法充分分离。前两窗84个日期可描述性合并；第三窗与第二窗重叠25日，单独作为端点压力回放。此为曾被使用过历史的知情固定策略回放，不是新盲测、部署选路、因果试验或未来实际覆盖保证。')
heading('1 问题、变量和研究边界',2)
p('一个键为服务日d、门店s、商品k；需求D(d,s,k)和行动q(d,s,k)的单位均为件。采购c(k)、缺货a(k)、报废b(k)的单位均为元/件，取items.csv原值。holiday仅指本虚构案例的业务活动，不能解释为官方节日。每天重新备货，没有跨日库存；未满足需求流失，超量报废。模型给出需求点预测、90%中心分位区间，以及整数备货行动；采购费只约束预算，不进入损失目标。')
p('每键0≤q≤55且q为整数，每日全网络sum(q)≤1600件、sum(cq)≤6000元。真实日损失定义为L(q,D)=sum[a(k)max(D-q,0)+b(k)max(q-D,0)]，单位元/日。两项分别称缺货与报废损失。若资源有限，某商品即使点预测较高也未必得到同样比例的备货；商品的损失系数及资源占用会改变分配。')
p('研究问题有三层：固定42日期限内的点预测误差、区间覆盖与漏出如何；这些需求情景支持的整数行动在同历史标签上损失如何；早期1-14日、远期15-42日、活动、店品和同日期配对比较能支持什么解释。策略原样固定，无模型选择、调参或胜出配额。原固定未来规划11月1日至12月12日的实际需求未在本研究输入中开放，本报告不提供该未来的实测结论或现实采购建议。')
heading('2 原始数据审计与信息时间',2)
p(f'原需求CSV有{audit["demand_original_rows"]}行，10行完全重复出口被折叠，剩余{audit["raw_rows"]["demand_reports"]}条修订记录，覆盖{audit["demand_unique_keys"]}个唯一需求键。每键同修订若有内容冲突则拒绝，修订必须为正整数且到达时点随版本非递减。需求非负整数；促销折扣在[0,1]；商品费用和上限有限非负；维度唯一，星期与日期一致。天气原件1230行，其中17行雨量缺失，保留其缺失，不把缺失改成已知零雨量。')
p('原始无偏移时间按Asia/Shanghai解释。训练快照T(o)从available_at≤o的报告选每键最高revision，再要求service_date<原点日期；不是简单按服务日截断后使用最终版本。评价标签Y*在2026-11-04 18:00前可见版本中选最高revision，服务日截至2026-10-31。这些成熟评价标签只能用于评分及合法到达的源残差，不作为该原点尚不可见的训练或特征。所有训练、预测特征、促销填补源、成熟标签及原CSV行字节哈希均随计算留存。')
table(['原点18时','训练日期数/键数','训练最大服务日','固定目标范围','活动日'],[[r.origin[:10],f'{r.train_days}/{r.train_rows}',r.max_train_service,f'{r.first_target} 至 {r.last_target}',str(r.activity_days)] for _,r in bounds.iterrows()],'表1 三窗训练与目标边界（均为当地时间）')
p('训练近56日内与原点前已公布促销相交，按品取均值填补未知促销，若该品没有可用源才回退0。已知促销及其announced_at、原行源保留。天气接口仅采用原点前已公布forecast的最新版本，并保留weather_available_at、weather_known及雨量缺失；observed天气不冒称当时已知。天气不进入两条预测政策，这仍不免除接口时点核对。预测特征和训练特征都由原件重建，没有复制旧评分结果。')
heading('3 固定统计政策与残差来源',2)
p('R使用共享岭回归：beta_hat=argmin_beta{sum[(D_i-x_i beta)^2]+10 sum(beta_j^2)}，不加额外截距。设计矩阵共169列：96个店品指示、56个品×星期指示、8个品×time30、8个品×促销、1个全局活动项×0.3。time30=(服务日-2026-05-01)/30。预测P=max(x beta_hat,0)，负值截为0。不同列尺度和alpha=10均沿用原政策，活动缩放会影响正则化程度；本轮没有针对三窗结果重调。')
p('W对同店同品同星期，在训练快照中取服务日不早于原点减56日的需求均值；若无该星期记录则回退同店品全部训练均值。它保留局部水平但不显式外推时间趋势，不直接使用促销和活动项。两路线使用可得预测变量的不同子集，属于预先冻结的政策差异；比较的训练、目标网格、标签、资源与损失相同。')
p('不确定性池采用R21首锁的14日源预测轨迹，不添加本轮42日新残差。每个源坐标记录源原点、服务日、店品、训练快照哈希、成熟标签版本/原行/到达时点和已发表point。程序从原件重建原训练、训练特征、目标特征、促销填补源并核对原CSV字节身份；R原预测用冻结系数和重建特征重算，W从原训练重算。作者另对六个合法源原点R重新拟合，系数与原系数最大差小于2.47×10^-11。')
p('误差定义为e(v,s,k)=Y*(v,s,k)-P_published(v,s,k)，P_published为原CSV已经发表的10位小数接口；不信任该CSV的error列或demand_units列作真值。重算原预测与发表point的差只属于明确的精度迁移，不声称内部未舍入预测逐位相同。所用标签revision、raw_row、raw_hash及available_at逐项匹配原始报告。')
p('残差日v可用，当且仅当：源原点严格早于新原点o、v严格早于原点日期、该日恰有96个唯一坐标，且全部所用成熟版本的max(available_at)≤o。一个14日源窗中其他日期尚未全部就绪，不排除已经齐全的某个日；同日不可重复加权。三窗每路线分别纳入11、53、70个整日向量，两路线同窗使用同源日期与到达规则。已公布旧版本并不意味着最终用于残差的较新版本已可见。')
heading('4 情景、区间和整数优化',2)
p('对目标日d和合格残差日v，情景为S(v,d,s,k)=max[P(o,d,s,k)+e(v,s,k),0]；同日96维向量整体迁移，向量等权1/N。S可以是非负实数，q必须是整数。按同一情景逐键计算numpy linear分位Q0.05和Q0.95，并输出10位小数。这里的90%是名义中心分位等级，不是校准保证。残差有偏时中心区间可以不含点预测，本轮共有126个这样的键；这不是非法预测，也没有把端点裁到点预测来隐藏偏差。')
p('每个目标日独立解：min_q (1/N)sum_v sum_s,k[a(k)max(S(v,d,s,k)-q,0)+b(k)max(q-S(v,d,s,k),0)]，约束如第1节。期望损失是情景平均而非未来真实期望的已知值。实现枚举每坐标整数数量的凸损失增量，将正边际收益的单位作为二元MILP变量，使用SciPy/HiGHS，mip_rel_gap=1e-9。收益随数量非增；将选中单位聚合为q后，另以原损失公式重算情景目标，检查整数、上限与两项资源。')
p('保留每次solver的status、bound、gap、节点数和目标重算值。252个日级求解均status=0，报告gap=0；目标与下界的最大数值差约1.00×10^-10元，作者重新计算的目标与保存目标一致。这支持当前有限离散情景模型的求解结论，不能把它外推为需求分布正确、真实经营最优或已部署可靠性。')
heading('5 评价定义与预定比较',2)
p('对一个分组G，MAE=mean|P-Y*|，RMSE=sqrt(mean(P-Y*)^2)，偏差=mean(P-Y*)；正偏差表示预测高于成熟需求。覆盖=mean[lo≤Y*≤hi]，下侧漏出=mean[Y*<lo]，上侧漏出=mean[Y*>hi]，平均宽度=mean(hi-lo)。区间评分IS90=(hi-lo)+20max(lo-Y*,0)+20max(Y*-hi,0)。MAE、RMSE、偏差、宽度、区间评分的单位都是件/键，覆盖与漏出为比例，分数越小越好。')
p('分组平均每日损失为该组所有缺货与报废损失之和除以该组不同日期数，单位元/日；采购与备货分别为元/日、件/日。按店或品分组时这些金额是网络总量的一部分，不能再误解释为整个网络日损失。每窗总损失=42×平均每日损失。预定表包含42日总体、1-14/15-42、六个7日带、活动/普通、活动×早晚/带/单步、每个单步、12店、8品及同日期W减R的损失与评分。')
p('分组样本为0时输出0日期、0键、not_estimable及空数值，并在正文称不可估计，绝不将其当作0误差、0损失或通过。本轮六步长带的活动空格见图5及表6；逐单步活动交叉也完整保留。每窗同日96个店品及连续日期存在依赖，因此不把4032行当成4032个独立样本，不给显著性或因果检验。')
heading('6 三窗42日总体结果',2)
table(['窗/路线','MAE','RMSE','偏差','覆盖%','宽度','区间评分'],[[route(r),fmt(r.mae),fmt(r.rmse),fmt(r.bias),fmt(100*r.coverage,2),fmt(r.width),fmt(r.interval_score)] for _,r in overall.iterrows()],'表2 点预测与区间（误差、偏差、宽度、评分：件/键；覆盖：%）')
table(['窗/路线','下漏%','上漏%','缺货','报废','总损失','采购','备货'],[[route(r),fmt(r.below*100,2),fmt(r.above*100,2),fmt(r.shortage_per_day,2),fmt(r.waste_per_day,2),fmt(r.loss_per_day,2),fmt(r.procurement_per_day,2),fmt(r.q_per_day,2)] for _,r in overall.iterrows()],'表3 每日网络决策结果（缺货/报废/总损失/采购：元/日；备货：件/日）')
image('01_overview.png','数据来自三窗group_overall.csv；R/W从同一成熟标签与预定资源评分。')
p('7月22日窗R相对W的MAE高0.230件/键，却少损失49.20元/日。R正偏差1.640件/键、W略负偏差；R的缺货较少而报废略多，二者合计仍较低。9月2日窗R在MAE、区间评分和总损失上均较低；9月19日窗也如此，但W覆盖较高且更宽。覆盖更接近90%不能单独判断整体区间优劣：两后窗W平均宽度比R多约0.950和0.832件/键，同时区间评分仍较高。')
p('全部三窗R每日损失低于W的描述性差依次为49.20、61.68、43.63元。该结果不能追认原点当时选了R，也不授权新选路。R的9月19日窗缺货350.96元/日高于W的337.71元/日，但报废283.20低于W的340.08元/日，总和较低；只报告缺货会遗漏实际权衡。采购额始终低于6000元并非约束都宽松：部分日1600件容量绑定，采购预算另有松弛。')
heading('7 早期与远期：窗口依赖的证据',2)
table(['窗/路线','阶段','日期/键数','MAE','偏差','覆盖%','日损失'],[[route(r),r.stage,f'{r.days}/{r.rows}',fmt(r.mae),fmt(r.bias),fmt(100*r.coverage,2),fmt(r.loss_per_day,2)] for _,r in stages.iterrows()],'表4 早期1-14日与远期15-42日；每个值按本组日期/键计算')
image('02_bands.png','六带均为7日、672键；各窗单列，不将重复目标日期当新独立样本。')
p('第一窗R从早期MAE2.458上升到远期3.177，偏差从+0.378升到+2.271件/键，表现与固定时间趋势的远期外推偏高相容，但仅为解释性假说，未做因果识别。W的MAE从2.559升到2.782，偏差由-0.592变为+0.017。R远期虽然更不准，其平均每日损失692.04仍低于W的747.48；以原点训练均值与残差形成的行动并不等于将点预测四舍五入。')
p('第二窗R的MAE仅从2.454到2.622，第三窗从2.511到2.564；W分别从2.652到2.720、从2.666到2.637。远期不必机械更差，第三窗W远期MAE略低。六带曲线也不是单调增长：第一窗末带损失明显较高，而中间带可较低；第二窗R第35日前后的带较不准，第三窗最晚带损失较高但MAE并非最高。日历位置、活动与需求水平差异都与期限混在一起。')
p('活动混杂可由普通日层直接检查。第一窗R普通日远期MAE3.107仍高于早期2.458，说明不能完全归因于远期4个活动日；第三窗R普通日早期MAE2.511、远期2.467，几乎不支持普通日随期限恶化。原点更新后的训练增长、促销可得性和残差池变化均同时发生，跨窗改善不能只归因于残差数量增加。固定每原点不更新42日内信息，也不同于每日滚动重拟合的运行方式。')
heading('8 活动、区间漏出与可估计性',2)
table(['窗/路线','日类','日期','MAE','覆盖%','区间评分','日损失'],[[route(r),'活动' if r.holiday else '普通',str(r.days),fmt(r.mae),fmt(100*r.coverage,2),fmt(r.interval_score),fmt(r.loss_per_day,2)] for _,r in act.iterrows()],'表5 活动与普通日的描述性分层；活动各窗仅4日、384键')
image('03_intervals.png','同窗宽度和覆盖都须结合上下漏出与区间评分；虚线为名义0.90。')
p('所有窗活动MAE高于普通日，覆盖低于普通日。第一窗W活动覆盖仅56.77%、上侧漏出40.63%，明显低估高需求活动；R活动覆盖69.01%，仍不足。后两窗W活动上侧漏出为21.35%和20.83%，R分别5.21%和7.03%，但R仍有下侧漏出10.94%和10.42%，体现活动效果与残差迁移都可能失配。R活动每天达到1600件容量上限，需求情景提升不能消除总量瓶颈。')
p('活动不必同程度推高总损失：第二窗R活动651.16元/日、普通618.40元/日，差较小；第一和第三窗活动损失分别1260.30和1117.93元/日，远高于普通629.30和583.24。活动日的需求分配、各品损失系数与容量共同决定日损失，不能从一个统一活动系数推导同质经营效应。每窗只有4个活动日期，即使384个键也不等于384次独立活动。')
table(['原点','1-7','8-14','15-21','22-28','29-35','36-42'],[[o[:10]]+[str(int(mat[i,j]))+'日/'+str(int(mat[i,j])*96)+'键' if mat[i,j] else '0日/0键\n不可估计' for j in range(6)] for i,o in enumerate(origins)],'表6 活动×步长带支持数，两路线相同；空格为不可估计')
image('05_activity_support.png','整日活动分布直接来自原calendar及固定网格；没有为完善表格补活动样本。')
p('第一窗活动落在15-21和36-42日，早期活动0日期/0键不可估计；第三窗早期同样空缺，活动集中15-21、29-35、36-42日；第二窗仅第8-14日带有1个活动日，其余3个分散在第15-21与29-35带。第二窗活动早期R覆盖84.38%、远期83.68%，但早期只有1日，不能据此估计稳定的活动×期限效应。第一和第三窗早期活动缺失使完整交互比较不可识别；报告给出支持数和描述，不用伪零均值填空。')
heading('9 同日期配对与跨窗合并',2)
image('04_daily_pair.png','paired_daily.csv同时保留每日W减R损失和区间评分；图中只画损失差。')
for o in origins:
    z=pair[pair.origin==o];p(f'{o[:10]}窗同日期W减R平均损失差{z.loss_W_minus_R.mean():.2f}元/日，范围{z.loss_W_minus_R.min():.2f}至{z.loss_W_minus_R.max():.2f}元/日；42日中{int((z.loss_W_minus_R>0).sum())}日R较低、{int((z.loss_W_minus_R<0).sum())}日W较低、{int((z.loss_W_minus_R==0).sum())}日相同。W减R平均区间评分差{z.score_W_minus_R.mean():.3f}件/键。这是逐日事实，不给总体胜率或独立检验意义。')
table(['路线','日期/键','MAE','RMSE','覆盖%','区间评分','日损失'],[['R' if r.method_id==methods[0] else 'W',f'{r.days}/{r.rows}',fmt(r.mae),fmt(r.rmse),fmt(r.coverage*100,2),fmt(r.interval_score),fmt(r.loss_per_day,2)] for _,r in combined.iterrows()],'表7 前两个非重叠窗的84日描述性合并')
p('前两窗目标分别7月23日至9月2日、9月3日至10月14日，恰为84个不同日期；其合并R日损失655.46元，W710.89元，差55.44元/日，但W合并MAE2.703仍略低于R2.752。第三窗9月20日至10月31日与第二窗重叠9月20日至10月14日共25日，故不和前两窗混成126个独立日期。虽然其原点较晚、训练与源残差有新合法信息，重叠日期依然是同一批成熟需求。此窗只作为端点压力回放，观察不同信息条件下固定政策的表现。')
heading('10 店品分层与资源约束',2)
image('06_store_item.png','group_store.csv和group_item.csv中的日损失按本组日期数计算；颜色正值表示该分组R损失较低。')
p('店与品的分层揭示总体差值来自哪些部分。图6有正负单元，某些店品部分可由W较低损失贡献，即使网络总和R较低；附录逐窗给出全部12店和8品的R/W日损失及差值。分组与网络共享资源，不能把某店的改进独立外推为孤立门店最优策略。品上采购、缺货、报废金额不同，因此件误差相同也可能导致金额损失明显不同。')
table(['窗/路线','最小容量松弛','最大容量松弛','最小预算松弛','最大预算松弛','容量绑定日'],[[o[5:10]+'/'+('R' if m==methods[0] else 'W'),str(int(g.capacity_slack.min())),str(int(g.capacity_slack.max())),fmt(g.budget_slack.min(),2),fmt(g.budget_slack.max(),2),str(int((g.capacity_slack==0).sum()))] for (o,m),g in solver.groupby(['origin','method_id'])],'表8 每日资源松弛（容量：件；预算：元）')
p('最小预算松弛仍为356元或更多，而所有路线均存在容量绑定日。这说明本样本的1600件上限比6000元预算更常成为约束；并不意味着改变价格或未来需求后预算也不重要。行动不超过55件/键且整数，损失从成熟需求与行动逐键重算。未来经营可得数据、商品范围、成本和资源一旦改变，当前数值不构成保持表现的保证。')
heading('11 作者验证、复现与错误保留',2)
p('科学源、config和实际执行WORKFLOW在2026-10-09T09:10:35.864263+00:00独占冻结，冻结命令终态结束早于首次实际计算命令的begin.utc。原件与C13/协议/源预测接口身份均绑定。所有实际命令经record_command.py保存开始、结束、完整stdout/stderr及退出状态；每个运行进程已等终态。科学源冻结后未改。执行域仅为runs/R22/execution，本地目录约定不是操作系统隔离；实际模型、token、cost未知为null。')
p('小规模oracle将3个非零坐标嵌入96维，用3个含小数需求的情景、4件容量和14元预算枚举23个可行行动，穷举最小值与MILP同为11.9708333333元。其余坐标需求0，报废费用非负，0行动存在不增损的最优解，因此可核对嵌入问题。测试接受实数情景，拒绝负数/NaN/Inf及95坐标情景；拒绝非整数、负值、超55、非有限及超容量/预算行动；零需求和零资源行动为0。非有限预测被拒绝，点在中心区间外的合法例子被接受。')
p('到达边界实际运行：原需求2026-05-01/S01/K03修订在公布前一秒不可选，恰到时可选；96坐标整日恰到原点可用，删到95坐标不可用，最后一个所用版本晚一秒不可用。等新原点的source_origin及原点当日服务日不可入池。同源窗组合一个就绪日和一个未就绪日，已齐的2026-07-09仍被接纳，未加完整源窗限制。边界证据和实际源坐标重建均留存，不能只把规则写成清单。')
p('作者在全新clean-v1目录完整重跑同一显式入口，比较所有CSV的关键数值/字段、情景NPZ数组、模型及语义JSON，排除运行时间和输出路径导致的合理差异后结果一致。原件快照/源预测回溯与当前代码重跑是不同证据：同源复现只说明可重复，作者原件重建也仍是自检，不是独立验收。接收者需从冻结协议和原件独立重建与判断，root冻结首交域后再执行。')
p('保留两条非零退出收据：0002最初读取误用了不存在的runs/R21/prospective-freeze.json，是路径恢复，随后经确认读实际execution/prospective-freeze.json；0011故意向已存在science-v1请求输出，入口在写入前以FileExistsError拒绝，是边界测试的预期非零退出。没有科学计算失败、源码实质修复或改写原失败；不采用通用两次错误停止规则。原C13九份Markdown未变，计算代码属于本次研究产物。')
heading('12 解释、局限与可支持结论',2)
p('R的趋势和活动项可在一些远期或活动条件下提高备货的非对称损失表现，但第一窗也有明显正偏差，未能统一改善点预测。W在普通日表现更接近局部均值，但活动时易低估并产生上侧漏出。对当前三个固定窗，R的每日两项总损失均较低，是可复算的描述性结果；并不能证明在其他原点、数据机制、成本或资源下普遍较优。两个策略和协议已经在先前历史工作中存在，本轮历史亦曾被R21使用，必须称知情固定策略历史回放。')
p('残差池规模11、53、70不是独立试验次数。向量保留同日店品关系，但把过去不同日期向量等权迁移到各未来日，只形成边际情景；没有识别42日序列联合分布，不能据此保证长期总损失尾部或解释日间相关。区间不随期限额外膨胀，覆盖可随目标分布漂移。首窗池小、后窗池扩展且训练增长，同时存在原点及日历变化，无法分离各因素的作用。')
p('三窗活动都只有4日，而原11月1日至12月12日固定未来规划的活动频度不同。相同42日期限只保证评价长度一致，不保证相同业务机制或分布。活动与步长空格限制交互推断；三个原点不是对所有历史起点的随机抽样。成熟评价允许事后标签用于评分，但不容许回灌原点输入；后原点训练合法包含较早目标已公布标签，这是历史信息接口，不是模型选择授权。')
p('全部数据是虚构离线案例，零跨日库存、确定商品成本和每日资源是问题假设；实际经营中的损耗过程、补货周期、跨日库存和需求不可观测等变化均未建模。不作显著性、因果、名义90%保证、比赛/奖项或现实采购结论；正式赛事题、专项AI及提交规则未知，本报告只是固定协议下完整研究交付。')
heading('13 文件、可重复入口与来源',2)
p('从仓库根运行：py -3.12 -X utf8 -B scripts/record_command.py --out <新收据路径> -- py -3.12 -X utf8 -B runs/R22/execution/source/v1/run_replay.py --raw runs/R21/inputs/raw --config runs/R22/execution/source/v1/config.json --newout <不存在的新输出目录>。源码和配置身份以execution/prospective-freeze.json为准，已存在输出目录拒绝。外部接收重跑应使用接收者写域，不能覆盖作者首交域。')
p('授权原始来源：runs/R21/inputs及input-lock；科学基线：R21/execution/source/v1四个冻结文件；原预测来源接口：science-v1/uncertainty/residual_coordinates_all.csv，以及指定train、train_features、predict_features、promotion_imputation_sources和coefficients文件。本轮未读取R21/evaluation、旧论文/报告、既有结果/selfcheck/诊断或R22/audit。R22/protocol及acceptance定义本轮标准；C13纯文档定义工作流与接收责任。没有外部论文引文或检索的事实主张。')
p('本轮science-v1/results/keys.csv保留逐键预测、真实标签源、区间、行动、误差和损失；predictions和plans为六组完整4032键接口。data保存原件行源、训练及特征和目标成熟标签；uncertainty保存逐源坐标回溯、日成员、向量及情景。results/group_*.csv保存全部预定分组，daily/paired_daily保存同日比较，solver_daily保存目标、bound/gap与资源。图1-6均由这些表生成，图形数据和文档源随交付留存。正文表为便于阅读而四舍五入，逐键接口保留10位小数。')
heading('附录A 全部门店的日损失',2)
p('每行是指定窗某门店的42日总损失除以42，单位元/日；W减R正值表示该门店部分R较低。12门店行相加等于相应网络日损失。')
for o in origins:
    z=stores[stores.origin==o].pivot(index='store_id',columns='method_id',values='loss_per_day');table(['原点','门店','R日损失','W日损失','W减R'],[[o[:10],s,fmt(r.shared_ridge10,2),fmt(r.weekly_mean56,2),fmt(r.weekly_mean56-r.shared_ridge10,2)] for s,r in z.iterrows()],o[:10]+'门店分层')
heading('附录B 全部商品的日损失',2)
p('每行是指定窗某商品全部12店42日损失除以42，单位元/日；8品行相加等于网络日损失。各品MAE、RMSE、覆盖、漏出和区间评分保留在group_item.csv，店分组同样完整。')
for o in origins:
    z=items[items.origin==o].pivot(index='item_id',columns='method_id',values='loss_per_day');table(['原点','商品','R日损失','W日损失','W减R'],[[o[:10],s,fmt(r.shared_ridge10,2),fmt(r.weekly_mean56,2),fmt(r.weekly_mean56-r.shared_ridge10,2)] for s,r in z.iterrows()],o[:10]+'商品分层')
heading('附录C 活动×早晚空格与区间诊断',2)
table(['窗/路线','阶段','活动日/键','MAE','覆盖%','日损失'],[[route(r),r.stage,f'{r.days}/{r.rows}',fmt(r.mae),fmt(100*r.coverage,2),fmt(r.loss_per_day,2)] for _,r in astage[astage.holiday==1].iterrows()],'活动×早晚：空样本数为0，指标明确不可估计')
p('下侧漏出并不等于缺货：区间端点是需求不确定性描述，缺货由q与真实需求比较。区间评分也不是金额损失，件/键与元/日不能直接相加。训练、成熟标签和原源预测的精度边界均有独立字段；本文没有把原已发表10位point和内部浮点值视为同一个逐位接口。')
# Shared block stream drives both complete Markdown and PDF.
md=[];story=[]
normal=ParagraphStyle('body',fontName='CN',fontSize=10,leading=16,spaceAfter=8,wordWrap='CJK',textColor=colors.HexColor('#24313b'))
head1=ParagraphStyle('title',parent=normal,fontSize=20,leading=28,spaceBefore=6,spaceAfter=14)
head2=ParagraphStyle('section',parent=normal,fontSize=14,leading=21,spaceBefore=14,spaceAfter=9,keepWithNext=True,textColor=colors.HexColor('#176b8a'))
captionstyle=ParagraphStyle('caption',parent=normal,fontSize=8.5,leading=13,textColor=colors.HexColor('#526574'))
cellstyle=ParagraphStyle('cell',parent=normal,fontSize=8.3,leading=12,spaceAfter=0)
for block in blocks:
    kind=block[0]
    if kind=='heading':
        t,level=block[1:];md.append('#'*level+' '+t);story.append(Paragraph(html.escape(t),head1 if level==1 else head2))
    elif kind=='paragraph':md.append(block[1]);story.append(Paragraph(html.escape(block[1]),normal))
    elif kind=='table':
        h,rows,caption=block[1:];md.extend([caption,'|'+'|'.join(h)+'|','|'+'|'.join(['---']*len(h))+'|']+['|'+'|'.join(str(c).replace('\n','<br>') for c in row)+'|' for row in rows]);story.append(Paragraph(html.escape(caption),captionstyle));cells=[[Paragraph(html.escape(str(c)).replace('\n','<br/>'),cellstyle) for c in row] for row in [h]+rows];t=Table(cells,colWidths=[(A4[0]-88)/len(h)]*len(h),repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f1f5')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#ced9df')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f6f8fa')]),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([t,Spacer(1,10)])
    elif kind=='image':
        name,caption=block[1:];md.append('!['+caption+']('+str((fig/name).resolve()).replace('\\','/')+')');md.append(caption);im=Image(str(fig/name));ratio=min((A4[0]-88)/im.imageWidth,330/im.imageHeight);im.drawWidth=im.imageWidth*ratio;im.drawHeight=im.imageHeight*ratio;story.extend([im,Paragraph(html.escape(caption),captionstyle),Spacer(1,10)])
    md.append('')
(out/'REPORT.md').write_text('\n'.join(md),encoding='utf-8')
def footer(canvas,doc):
    canvas.saveState();canvas.setFont('CN',8);canvas.setFillColor(colors.HexColor('#637784'));canvas.drawString(44,26,'R22 固定42日历史回放 | 中文技术研究报告');canvas.drawRightString(A4[0]-44,26,str(doc.page));canvas.restoreState()
SimpleDocTemplate(str(out/'REPORT.pdf'),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=38,bottomMargin=43,title='固定42日需求预测与整数备货：三历史原点回放研究',author='R22-02 executor').build(story,onFirstPage=footer,onLaterPages=footer)
# Bound critical tables and plotting sources for document reception.
manifest={'report_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'critical_tables':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((science/'results').glob('*.csv'))],'figures':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(fig.glob('*.png'))],'body_blocks':len(blocks),'author_selfcheck_only':True}
(out/'document-data-bindings.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Created complete Chinese Markdown/PDF and',len(manifest['figures']),'figures; blocks',len(blocks))
