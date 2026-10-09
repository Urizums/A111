"""Traceable Chinese scientific paper, common content tree for Markdown and PDF."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,html,hashlib
import numpy as np,pandas as pd
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from pypdf import PdfReader
ap=argparse.ArgumentParser();ap.add_argument('--science',required=True);ap.add_argument('--inspection',required=True);ap.add_argument('--selfcheck',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--newout',required=True);a=ap.parse_args()
sc=Path(a.science);ins=Path(a.inspection);out=Path(a.newout);out.mkdir(parents=True,exist_ok=False);(out/'figures').mkdir();(out/'figure_data').mkdir();(out/'equations').mkdir()
def read(n):return pd.read_csv(sc/n)
summary=json.loads((sc/'results/science_summary.json').read_text('utf-8'));info=json.loads((ins/'inspection.json').read_text('utf-8'));freeze=json.loads(Path(a.freeze).read_text('utf-8'));checks=json.loads(Path(a.selfcheck).read_text('utf-8'));sel=json.loads((sc/'results/selection.json').read_text('utf-8'))
S=summary['historical_stage_metrics'];R='shared_ridge10';W='weekly_mean56';short={R:'R',W:'W'};aud=info['audit'];rr=aud['raw_rows'];color={R:'#165a83',W:'#d26b27'}
fp=FontProperties(fname='C:/Windows/Fonts/simhei.ttf');plt.rcParams.update({'font.family':fp.get_name(),'axes.unicode_minus':False,'font.size':9,'figure.dpi':140,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
from matplotlib import font_manager
font_manager.fontManager.addfont('C:/Windows/Fonts/simhei.ttf')
def plot_save(fig,name,data):
    fig.tight_layout();fig.savefig(out/f'figures/{name}.png',dpi=180);plt.close(fig);data.to_csv(out/f'figure_data/{name}.csv',index=False)
hist=read('results/historical_predictions_plans.csv');val=hist[(hist.stage=='validation')&(hist.policy=='stochastic')];daily=read('results/daily_history.csv');fd=read('results/future_daily_summary.csv')
# Figure 1 uses as-of decision snapshot, never the later scoring labels.
desc=read('results/descriptive_service_date.csv');panel=read('data/descriptive_panel.csv');dd=desc.merge(panel.groupby('service_date').holiday.max().reset_index(),on='service_date')
fig,ax=plt.subplots(figsize=(7.1,2.65));ax.plot(pd.to_datetime(dd.service_date),dd['sum'],color=color[R],lw=1,label='决策时可见历史需求');h=dd.holiday==1;ax.scatter(pd.to_datetime(dd.loc[h,'service_date']),dd.loc[h,'sum'],s=13,color=color[W],label='业务活动日');ax.set(ylabel='全网需求 (件/日)',xlabel='历史服务日期');ax.legend(loc='upper left',ncol=2,frameon=False);plot_save(fig,'fig1_history',dd)
# Figure 2 observed historical losses only.
vv=daily[(daily.stage=='validation')&(daily.policy=='stochastic')].copy();vv=vv.merge(val.groupby('service_date').holiday.max().reset_index(),on='service_date')
fig,ax=plt.subplots(figsize=(7.1,2.8))
for n,z in vv.groupby('method_id'):ax.plot(pd.to_datetime(z.service_date),z.loss_yuan,label=short[n],color=color[n],lw=1.2)
for d in vv.loc[vv.holiday==1,'service_date'].unique():ax.axvspan(pd.Timestamp(d)-pd.Timedelta(hours=12),pd.Timestamp(d)+pd.Timedelta(hours=12),color='#ddd6c5',alpha=.5)
ax.set(ylabel='实测缺货+报废损失 (元/日)',xlabel='历史验证日期');ax.legend(frameon=False,ncol=2);plot_save(fig,'fig2_validation_loss',vv)
trade=read('results/interval_tradeoff.csv').query("stage=='validation'").groupby(['method_id','nominal_level'])[['coverage','width_units']].mean().reset_index()
fig,ax=plt.subplots(figsize=(7.1,2.8))
for n,z in trade.groupby('method_id'):
    ax.plot(z.width_units,z.coverage*100,'o-',color=color[n],label=short[n]);
    for row in z.itertuples():ax.annotate(f'{row.nominal_level:.0%}',(row.width_units,row.coverage*100),xytext=(4,4),textcoords='offset points',fontsize=8)
ax.axhline(90,ls='--',color='#888',lw=.8);ax.set(xlabel='平均边际区间宽度 (件)',ylabel='历史实际覆盖率 (%)',ylim=(76,98));ax.legend(frameon=False);plot_save(fig,'fig3_interval_tradeoff',trade)
hg=pd.read_csv(ins/'validation_horizon.csv');ec=val[val.method_id==R].groupby('horizon').agg(activity_keys=('holiday','sum'),keys=('holiday','size')).reset_index();ec['activity_days']=ec.activity_keys/96
fig,(ax,bx)=plt.subplots(1,2,figsize=(7.1,2.65),gridspec_kw={'width_ratios':[2,1]})
for n,z in hg.groupby('method_id'):ax.plot(z.horizon,z.mae,'o-',ms=3,color=color[n],label=short[n])
ax.set(xlabel='预测步长 (日)',ylabel='历史 MAE (件/店品日)',xticks=[1,4,7,10,14]);ax.legend(frameon=False);bx.bar(ec.horizon,ec.activity_days,color='#888');bx.set(xlabel='预测步长 (日)',ylabel='活动日数量 (日)',yticks=[0,1,2],xticks=[1,7,14]);plot_save(fig,'fig4_horizon',hg.merge(ec,on='horizon'))
fig,(ax,bx)=plt.subplots(2,1,figsize=(7.1,4.2),sharex=True)
for n,z in fd.groupby('method_id'):
    ax.plot(pd.to_datetime(z.service_date),z.point_total_units,color=color[n],label=f'{short[n]} 点预测');bx.plot(pd.to_datetime(z.service_date),z.q_units,color=color[n],label=f'{short[n]} 备货')
bx.axhline(1600,color='#888',ls='--',lw=.8,label='日产能上限');ax.set_ylabel('全网预测需求 (件/日)');bx.set_ylabel('全网整数备货 (件/日)');bx.set_xlabel('未观测未来服务日期');ax.legend(ncol=2,frameon=False);bx.legend(ncol=3,frameon=False);plot_save(fig,'fig5_future_plan',fd)
elements=[];claims=[]
def add(kind,**kw):elements.append(dict(kind=kind,**kw))
def p(t):add('paragraph',text=t)
def h(t):add('heading',text=t)
def table(title,headers,rows,source,widths=None):add('table',title=title,headers=headers,rows=rows,source=source,widths=widths);claims.append({'kind':'table','title':title,'source':source,'displayed_rows':rows})
def fig(title,name,source):add('figure',title=title,path=f'figures/{name}.png',source=source);claims.append({'kind':'figure','title':title,'data':f'figure_data/{name}.csv','source':source})
def eq(latex,explain):
    name=f'equation{sum(e["kind"]=="equation" for e in elements)+1}';f=plt.figure(figsize=(7.1,.65));f.text(.03,.5,'$'+latex+'$',fontsize=14,ha='left',va='center');f.savefig(out/f'equations/{name}.png',dpi=200,bbox_inches='tight',pad_inches=.08);plt.close(f);add('equation',latex=latex,path=f'equations/{name}.png',explain=explain)
def m(stage,n,policy='stochastic'):return S[f'{stage}|{n}|{policy}']
def f(x,n=2):return f'{float(x):.{n}f}'
add('title',text='公布时点约束下的生鲜需求预测与整数备货')
add('subtitle',text='12 店 × 8 品 × 42 日的离线决策研究 | R21 首次交付')
p('摘要：本研究在 2026 年 10 月 31 日 18:00 固定信息集下，为 11 月 1 日至 12 月 12 日制定生鲜网络备货。需求报告具有公布时点和修订版本，训练使用各预测原点已公布的最高版本；历史计分固定采用 11 月 4 日截止的成熟历史标签，残差入池仍逐日审查所用 96 个版本是否已全到齐。比较预先固定的共享 ridge10 政策与 56 日同店品星期均值，均以完整日残差构造非负需求情景，并最小化缺货与报废金额。42 个选择日支持保留 ridge10；在另 42 个滚动验证日，其日均实测损失为 '+f(m('validation',R)['loss_yuan_per_day'])+' 元，星期均值为 '+f(m('validation',W)['loss_yuan_per_day'])+' 元；两者预测 MAE 为 '+f(m('validation',R)['mae'],3)+' 与 '+f(m('validation',W)['mae'],3)+' 件。ridge10 的名义 90% 区间实际覆盖 '+f(m('validation',R)['coverage90']*100)+'%，平均宽度 '+f(m('validation',R)['width_units'])+' 件，活动日覆盖更低。最终两候选各交付 4032 行预测和整数计划，主路线共备货 64537 件、采购 226028 元，逐日满足 1600 件和 6000 元限制。该总采购额是逐日用量之和，不可作为合并预算。未来真实需求尚未开放，情景损失不是实测收益；尤其 15-42 日步长与未来更密集的活动制度仍缺直接验证。')
p('关键词：按时点版本；滚动验证；完整日残差；名义区间；两资源整数优化。方法标识：R = shared_ridge10，W = weekly_mean56。论文中的金额均为人民币元，需求和备货均为件。')
h('1 问题、信息边界与数学抽象')
p('每一服务日有 96 个店品坐标，12 家门店分属 3 个区域、各销售 8 种商品。决策在一个固定原点作出，未来 42 日期间不读取新需求调整。没有库存结转，超出备货的需求流失、当日剩余报废。采购单价 c_i 只进入预算约束；缺货金额 a_i 和报废金额 b_i 才构成损失。原始需求可以超过备货上限，预测与情景可以是非负实数，整数限制只作用于备货 q_i。')
eq(r'\ell(q,d)=\sum_{i=1}^{96}\{a_i(d_i-q_i)_+ + b_i(q_i-d_i)_+\}', '其中 (x)_+ = max(x,0)，i 为店品坐标，d_i 是需求，q_i 是备货。缺货与报废不可相互抵消。')
eq(r'q_i\in\{0,1,\ldots,55\},\quad \sum_iq_i\leq1600,\quad\sum_i c_iq_i\leq6000', '三个条件分别是店品上限、网络日产能和日采购预算；每日独立应用。')
items=pd.read_csv('runs/R21/inputs/raw/items.csv')
table('表 1 商品参数（每件金额，全部门店通用）',['商品','采购 c_i','缺货 a_i','报废 b_i','日上限'],[[row.item_id,f(row.procurement_yuan),f(row.shortage_yuan),f(row.waste_yuan),str(row.daily_max_units)] for row in items.itertuples()], '原件 raw/items.csv；目标仅含 a_i、b_i。')
p('本研究将原题的硬约束、政策迁移约定和可逆研究假设区分记录。时区解释、每日约束、历史标签版本和基准参数来自题目及澄清；W 的 56 日窗口、三段一次性滚动验证以及诊断扰动在首次拟合前固定。未来真实覆盖率、真实损失及获益均不属于当前可观察对象。本研究没有读取竞赛答案，也没有外部模型或生成数据替代原始附件。')
h('2 数据审计与按时点接口')
table('表 2 原始附件规模、单位与处置',['附件','行数','含义 / 审计结论'],[['demand_reports',str(rr['demand_original_rows']),'需求、结算额、revision、available_at；10 行完全重复导出折叠'],['stores','12','店与区域，唯一维表'],['items','8','每件金额与每日上限，均为有限非负数'],['calendar','226','服务日期、星期、业务活动指示，星期与日期一致'],['promotions','21696','店品日折扣比例 [0,1] 与 announced_at'],['weather','1230','预报 / 事后观测；17 个雨量缺失']], 'science-v1/data/audit.json 与 audit_extended.json；需求折叠后 21599 个版本、17664 个唯一历史键。',[95,50,365])
p('需求服务期为 5 月 1 日至 10 月 31 日，共 184 日 × 96 键，原始需求范围 0-36 件。修订号为正整数，同键同修订不存在冲突内容；版本公布时点随修订号单调不减。只有所有业务字段完全相同的导出行才折叠，原行号、解析字段哈希和原始 CSV 行字节 SHA-256 均保留。重复导出不增添样本权重。键、连接基数、非有限数、非法折扣、日期星期和商品上限均已检查；未发现需要猜测修补的需求记录。')
eq(r'y_{t,i}^{(o)}=y_{t,i,r^*},\quad r^*=\max\{r:\ A_{t,i,r}\leq o\},\quad t<\mathrm{date}(o)', 'o 为预测原点，A 是该版本实际公布时间。训练按最高可见修订选版，而不是文件最后一行；未公布版本和原点当日标签均不能进入训练。')
p('所有无偏移时间戳按 Asia/Shanghai 解释。最终训练含 5 月 1 日至 10 月 30 日的 17568 个标签、183 个完整日；10 月 31 日需求在决策时不可用，已单列为拒用报告。11 月 4 日截止的最高成熟版本仅用于历史计分及确定残差所用标签。它们不能反向覆盖早期训练。例如 7 月 8 日训练有 42 个修订号与成熟版不同，其中 14 个需求数值不同；10 月 14 日仍有 44 个版本、10 个需求数值不同。记录这种差异是避免后见数据泄漏的必要步骤。')
p('促销只在 announced_at 不晚于预测原点时可用。R 对未知促销使用该原点训练期最近 56 日、同品类已公布促销均值，若均值不存在则用零；未知与已知无促销通过 promo_known 区分。最终未来 4032 键中仅 960 键促销已公布。天气只审查原点已发布的预报，不使用事后 observed；未来仅 1344 键有可用预报，另外 2688 键雨量缺报。两候选均不把天气或结算额用于预测，所以缺报未被擅自补成零雨量或反事实观测，也不能据此估计天气需求效应。')
fig('图 1 决策时可见的历史全网需求与业务活动日（件/日，183 日）','fig1_history','data/final_train_snapshot.csv、results/descriptive_service_date.csv；橙点是题目定义的活动，非官方节日。')
p('holiday 是虚构两日业务活动。可见历史共有 20 个活动日，而未来每周二、三有一次两日活动，共 12 个活动日。历史活动的日期分布与未来的每周固定制度不同，这是比随机噪声更重要的迁移风险。日历活动可预知并不等于其需求效应已被可靠识别。')
h('3 预先冻结的比较与选型设计')
p('实验和科学源码由真实命令在 UTC '+freeze['actual_frozen_at_utc']+' 冻结，记录包含输入、工作流、澄清、代码与配置哈希。随后才首次拟合。旧参考代码以原字节副本保留，并调用其中固定政策的特征、预测和优化函数；旧目录硬编码 main 未运行。路径、最终日期、成熟标签截止日、历史原点延长和未来 42 日长度的迁移差异见 prospective 配置。没有调整基准 alpha、特征、情景公式、等权权重或目标。')
rows=[]
for b in info['boundaries']:
    pool=next((z['sum'] for z in info['pool_by_origin'] if z['calibration_origin']==b['origin'] and z['method_id']==R),0)
    purpose={'precalibration':'残差种子，不计策略分','selection':'选择，按实测日均损失','calibration':'校准及诊断，不选择','validation':'一次性验证，参数不回调'}[b['stage']]
    rows.append([b['origin'][:10],str(b['train_rows']),str(pool),purpose])
table('表 3 时间顺序实验边界（原点均为当地 18:00，预测随后 14 日）',['原点','训练键数','合格残差日','用途'],rows,'data/snapshot_boundaries.csv、uncertainty/pool_membership_all_origins.csv；原点间隔 14 日，R/W 入池日期相同。',[85,70,90,265])
p('选择期覆盖 7 月 23 日至 9 月 2 日，共 42 个不重叠服务日。主指标为情景整数备货在成熟历史需求上的缺货加报废日均损失，精确相等时按候选顺序 R、W 决胜。9 月 2 日另一个 14 日窗口只用于校准诊断。三个验证原点覆盖 9 月 17 日至 10 月 28 日，共 42 日，未参与选型；允许后面的验证原点训练时使用此前已公布标签，路线与超参数均不改变。它检验的是冻结政策的滚动部署，而不是保持同一拟合参数不变。')
p('两候选共用同样的可用原件、时点快照、14 日历史预测网格、残差来源日及版本规则、整数求解器、资源和损失。R 使用政策允许的趋势、促销、星期和活动；W 刻意只使用近期需求与星期，以测试更简单的局部统计是否足够。可用信息相同不要求模型采用完全相同的特征。均在同一 CPU 进程串行运行，没有候选专属资源上限。8 个历史原点累计拟合和预测时间 R 为 '+f(info['fit_runtimes_by_method'][0]['sum'],3)+' 秒、W 为 '+f(info['fit_runtimes_by_method'][1]['sum'],3)+' 秒；这包含特征构造和实现开销，不能当作算法复杂度定理。全科学运行耗时 '+f(summary['runtime_seconds'])+' 秒。实际宿主模型、token 与费用没有观测数据，均记 null。')
h('4 预测方法与完整日不确定性')
p('R 的 169 列设计矩阵由 96 个店品截距、56 个品类星期项、8 个品类 time30、8 个品类促销和 1 个缩放为 0.3 的全局活动项组成。time30 是服务日距离 2026 年 5 月 1 日的天数除以 30。模型不另拟合截距，alpha 固定为 10，预测下截到零。共享品类斜率可以借用门店间信息，但只允许线性趋势，无法保证活动强度和长期趋势稳定。')
eq(r'\hat\beta=\arg\min_\beta\{\|y-X\beta\|_2^2+10\|\beta\|_2^2\},\quad \hat d_{t,i}=\max(x_{t,i}^{T}\hat\beta,0)', 'X 为当原点可用特征矩阵，y 为对应按时点标签。最终 X 的数值秩 161，低于 169 列，因截距与星期项有依赖；正则项使解唯一，但不能将某个系数解释为因果效应。')
eq(r'\hat d^{W}_{t,i}=\frac{1}{|B_{o,i,w(t)}|}\sum_{u\in B_{o,i,w(t)}}y_{u,i}^{(o)}', 'B 是原点前最近 56 天中相同店品、相同星期且可用的历史集合；空组回退到该店品全训练均值。56 日窗口在看表现前固定，不从验证集搜索。')
p('W 通常有八个同星期重复，易解释且避免将品类趋势向 42 日外推；其假设是近期水平及星期模式足够稳定。代价是忽略已知活动、促销和长期漂移。它既是可执行候选，也检验这些额外结构是否值得保留；若无改善也可作为研究结论，而不是强行增加模型。')
eq(r'e_{u,i}=y^{\mathrm{mature}}_{u,i}-\hat d^{(o_u)}_{u,i},\quad T_u=\max_i A_{u,i,r_i}', 'e_u 是严格较早原点 o_u 的完整 96 维整日残差；y^mature 是固定 11 月 4 日历史截止所选的具体最高修订，T_u 是这些具体版本最后一个公布的时点。')
p('新原点 o 的残差池只接纳 o_u < o、服务日 u 已结束且 T_u ≤ o 的整日向量。即使 14 日窗口的其他日尚未合格，也可接纳已完成的一日；不能用较早版本替代迟到的成熟版以凑齐 96 坐标。首选择原点 14 个潜在日只合格 11 日，后续合格数依次为 25、39、53、67、81、95；最终 10 月 31 日，7 月 9 日至 10 月 28 日的 112 个整日全合格。每一坐标保留源行、版本、available_at、原预测原点、训练快照哈希、点预测和误差，入池 / 排除理由单独保存。')
eq(r'D^{(s)}_{t,i}=\max(\hat d_{t,i}+e_{u_s,i},0),\quad s=1,\ldots,N_o', '从合格日向量等权取情景，同一历史日的 96 坐标保留在一起，避免破坏店品间共同冲击。')
eq(r'I_{t,i}^{90}=[Q_{0.05}(D_{t,i}),\ Q_{0.95}(D_{t,i})]', 'Q 为 numpy 线性插值经验分位，端点保留 10 位小数。区间是各店品的边际名义 90%，不是 96 维联合 90%。')
p('同一个历史日向量沿全部未来日期重复，沿袭当前政策的压力依赖约定；本题每日独立优化，不因此改变每日期望目标，但它不能识别跨日联合风险。残差等权和加性同分布假设也未获有限样本覆盖保证。早期池小、时间漂移和未来活动频率改变均可能降低覆盖。两方法使用同样的残差来源日，各自误差由各自预测产生，以相同构造比较完整政策。')
h('5 整数备货与优化器核验')
eq(r'\min_q\ \frac{1}{N_o}\sum_{s=1}^{N_o}\ell(q,D_t^{(s)})', '对每个服务日分别求解，约束见式中每日上限；42 日之间不共享库存或资源。')
p('对坐标 i、整数 k = 0,...,55，预先计算平均情景损失 g_i(k)。相邻减少量 Δ_i(k) = g_i(k-1)-g_i(k) 随 k 不增，因为绝对折线损失是离散凸的。仅为正收益单位设置 0/1 变量，每单位消耗 1 件产能及 c_i 元预算。相同坐标每个单位的资源相同，因此较后单位不能优于较早单位；并列时按数量聚合仍能恢复同目标的前缀备货。求解后以原情景重算目标核对聚合，不以求解器返回数代替业务目标。')
p('实现采用 scipy.optimize.milp / HiGHS，相对 MIP gap 1e-9，保存状态、目标、对偶界、gap、节点和秒数。一个含三个有效坐标、三个含合法小数的情景、产能 4 件、预算 14 元的小实例枚举 23 个可行整数方案，枚举与 MILP 最小损失均为 11.970833 元。零需求和零资源产生零备货；负情景、NaN、无穷、不完整坐标、分数备货、越界备货、超预算 / 产能及负资源不可行情形均被拒绝。有限非负的小数情景被正常接受，它们不是整数需求原件。')
p('全部两候选未来 84 个日问题均返回 status 0，gap 在设定容差内；重算缺货与报废分项和最优界一致。这支持在给定有限经验情景下的数值最优，而不意味着对未知真实分布最优。优化器修复、数据审计和模型效果是三个不同判断，本次科学首跑未产生需要覆盖的失败结果。')
h('6 历史实测比较与解释')
rows=[]
for stage,label in [('selection','选择'),('calibration','校准诊断'),('validation','验证')]:
    for n in [R,W]:
        z=m(stage,n);rows.append([label,short[n],f(z['mae'],3),f(z['rmse'],3),f(z['coverage90']*100),f(z['width_units']),f(z['loss_yuan_per_day'])])
table('表 4 各阶段预测、区间与情景策略实测损失',['阶段','方法','MAE 件','RMSE 件','覆盖 %','宽度 件','损失 元/日'],rows,'results/group_stage_method_id_policy.csv；同日成熟历史标签；stochastic 策略；选择 / 验证各 42 日，校准 14 日。',[63,37,71,71,75,75,118])
p('选择期 R 的日均损失 665.01 元低于 W 的 724.01 元，实际选型记录在验证开始前写入。因此最终主路线为 R，W 的全量未来输出同时保留。验证期 R 相比 W 少 '+f(m('validation',W)['loss_yuan_per_day']-m('validation',R)['loss_yuan_per_day'])+' 元/日，约 '+f((m('validation',W)['loss_yuan_per_day']-m('validation',R)['loss_yuan_per_day'])/m('validation',W)['loss_yuan_per_day']*100)+'%。R 的平均预测偏差为 +0.416 件/键，W 为 -0.361 件/键；两者总偏差方向不同，不能只凭接近零的偏差选模。')
table('表 5 验证期两项损失与库存利用（42 个历史日）',['方法 / 策略','缺货 元/日','报废 元/日','合计 元/日','备货 件/日'],[[short[n]+' / '+('情景' if pol=='stochastic' else '仅点'),f(m('validation',n,pol)['shortage_yuan_per_day']),f(m('validation',n,pol)['waste_yuan_per_day']),f(m('validation',n,pol)['loss_yuan_per_day']),f(m('validation',n,pol)['q_units_per_day'])] for n in [R,W] for pol in ['stochastic','point_only']], 'results/group_stage_method_id_policy.csv；仅点策略使用相同 MILP、资源和单一需求情景，是不确定性诊断，未作为最终候选选路。',[112,97,97,103,101])
p('R 的情景策略相对仅点策略将缺货从 490.99 降至 371.44 元/日，同时报废从 197.66 增至 260.36 元/日，总损失下降 56.84 元/日。W 也表现为增加备货缓解缺货，却承担更大报废。选择期 R 的情景策略损失 665.01 元/日，反而高于仅点诊断的 656.34 元/日，所以不能宣称情景化在所有历史阶段均改善。仅点诊断没有成为事后更换主路线的理由，正式路线和选择规则仍保持冻结。')
fig('图 2 历史验证期每日实测损失（元/日，阴影为业务活动日）','fig2_validation_loss','results/daily_history.csv、historical_predictions_plans.csv；R/W 为各自情景整数策略，全部需求是历史观察。')
p('按验证原点，R/W 的日均损失依次为 610.04/691.65、611.89/667.31、673.50/735.22 元。三段均保留 R 的优势，但末段损失上升并非预测 MAE 同步变差，说明损失还受活动、成本权重和资源拥挤影响。42 个日损失配对差 W-R 均值 66.25 元，2000 次独立日重采样的描述区间为 [43.31,92.09] 元；日间相关和共享训练 / 校准使独立假设可疑，所以该区间只作稳定性描述，不作因果或严格显著性证据。')
fig('图 3 区间宽度与历史覆盖的权衡（验证 42 日；各点标注名义水平）','fig3_interval_tradeoff','results/interval_tradeoff.csv；各原点同样 1344 键，三段等权；80/90/95% 是预定诊断，未回调交付90%。')
p('R 的名义 80/90/95% 区间在验证期覆盖约 79.59/88.99/93.11%，宽度 7.91/10.14/11.80 件；扩大区间提高覆盖但损失可读性。W 的名义 90% 覆盖 88.89%，宽度 10.95 件，覆盖接近 R 却更宽。R 在 90% 区间下低于下端占 3.00%、高于上端占 8.01%，上侧漏出更多。区间诊断说明加性历史残差并不精确校准，不应以输出 interval_level=0.9 推断已保证 90% 覆盖。')
h('7 活动、步长、门店与品类异质性')
ag=info['activity_groups']
table('表 6 业务活动分组的历史验证（同一 42 日）',['方法','日类 / 天数','MAE 件','覆盖 %','损失 元/日','缺货 元/日'],[[short[z['method_id']],('活动 / ' if z['holiday'] else '非活动 / ')+str(z['days']),f(z['mae'],3),f(z['coverage90']*100),f(z['loss_yuan_per_day']),f(z['shortage_yuan_per_day'])] for z in ag], 'results/group_stage_method_id_policy_holiday.csv；每活动日 96 键，共 5 活动日，37 非活动日。',[40,104,70,76,110,110])
p('活动日 R 的 MAE 2.912 件、覆盖 85.21%，W 为 3.720 件、76.04%；R 在 5 个活动日均备货至 1600 件，仍有较高缺货。W 不使用活动特征，活动日预测平均低估 2.822 件/键。R 的活动关联项有业务价值，但这是观察比较：活动、促销、星期及资源饱和不能从这五天中分别识别因果效应。未来活动频率从历史约每 19 日一组改为每 7 日一组，构成实际制度变化，不能将历史活动优势外推为保证。')
fig('图 4 验证期按步长的误差及活动分布（R/W，同一 42 日）','fig4_horizon','inspection-v1/validation_horizon.csv；每步长 3 日 ×96 键；右图活动日数量用于显示混杂。')
lg=info['lead_groups'];table('表 7 分段步长的历史验证（每格 2016 键）',['方法','步长 日','MAE 件','覆盖 %'],[[short[z['method_id']],z['lead_group'],f(z['mae'],3),f(z['coverage']*100)] for z in lg], 'historical_predictions_plans.csv 按 horizon≤7 分组；没有 15-42 日实测回测。')
p('R 的 1-7 日 MAE 2.477 件，8-14 日为 2.437 件，W 为 2.772 与 2.647 件。这个差异很小且受活动落在不同步长、不同原点训练规模影响，不支持“越远越准确”的规律。每一具体步长只有三个服务日，活动样本更稀；不能稳定分离活动与步长效应。最终 15-42 日需要外推线性趋势、未知促销均值和短步长残差，其区间宽度没有随步长扩张，正是应在未来真值开放后优先验证的风险。')
for col,title in [('item_id','品类'),('store_id','门店')]:
    z=pd.DataFrame(info['validation_'+col]);pivot=z.pivot(index=col,columns='method_id',values=['mae','loss_per_day','covered']);rows=[]
    for k,row in pivot.iterrows():rows.append([k,f(row[('mae',R)],3),f(row[('mae',W)],3),f(row[('loss_per_day',R)]),f(row[('loss_per_day',W)]),f(row[('covered',R)]*100)])
    table('表 '+('8' if col=='item_id' else '9')+' '+title+'分组验证（全部 42 日）',[title,'R MAE','W MAE','R 元/日','W 元/日','R 覆盖 %'],rows,f'inspection-v1/validation_{col}.csv；MAE 单位件/店品日，损失为该组每日金额，R/W 情景策略。',[58,79,79,99,99,96])
p('R 的门店 MAE 从 S04 的 2.298 至 S08 的 2.602 件，门店损失并非仅由误差大小排序；品类 K08 的日均损失最高，为 114.95 元，K07 为 102.36 元，与高缺货系数及需求水平有关。所有店、品的 R 日均损失均低于 W，但分组非独立重复试验，不能将每个小格解释为另一次显著证据。完整日残差保留同日跨店品关联，是比独立逐键扰动更合乎网络资源争用的描述。')
h('8 未来固定计划：模型产物而非实测表现')
p('最终仅使用 10 月 31 日 18:00 快照重拟合 R/W，主路线身份仍为选择期确定的 R。两候选各自有独立 method_id、4032 行点预测 / 名义 90% 区间及 4032 行整数备货。最终残差池均为 112 日；每个候选的情景是自己的误差，不读取任何 11 月 1 日及之后真实需求。未来全量键、区间域和逐日约束已通过作者重算，自检不能替代独立接收。')
rows=[]
for z in info['future_resource']:
    n=z['method_id'];fs=summary['future_summary'][n];rows.append([short[n],str(fs['total_q_units']),f(fs['total_procurement_yuan'],0),str(z['capacity_binding_days']),str(z['budget_binding_days']),f(z['mean_shortage_scenario']),f(z['mean_waste_scenario'])])
table('表 10 未来 42 日计划与条件情景损失（未观测）',['方法','备货合计 件','采购合计 元','产能满 日','预算满 日','情景缺货 元/日','情景报废 元/日'],rows,'results/future_daily_summary.csv；情景分项不能称为未来实测；合计采购仅逐日相加。',[40,88,91,65,65,80,81])
p('R 每日备货 1425-1600 件，共 64537 件，采购合计 226028 元；24 日产能达到上限，所有日期采购预算均有余量，最高每日采购 5611 元。W 总备货 64590 件，采购 226038 元，12 日产能到顶。R 的日均条件情景损失 603.97 元，W 为 696.60 元，但两者情景分布依赖各自预测，因此不能用这组未来情景损失证明真实效果优劣；可靠的公平效果比较来自同一成熟需求上的历史验证。')
fig('图 5 未观测未来的全网点预测与整数备货（R/W，42 日）','fig5_future_plan','results/future_daily_summary.csv；图内没有未来实际需求曲线，虚线为日产能1600件。')
table('表 11 主路线逐周计划摘要（未来未观测）',['周','服务日期','点预测合计 件','整数备货合计 件'],[[str(z['week']),str(pd.Timestamp('2026-11-01')+pd.Timedelta(days=7*(z['week']-1)))[:10]+' 至 '+str(pd.Timestamp('2026-11-01')+pd.Timedelta(days=7*z['week']-1))[:10],f(z['total_point_units']),str(z['total_q_units'])] for z in info['future_week_allocation']], 'inspection-v1/future_allocation_shared_ridge10_week.csv；周汇总不合并每日约束。',[45,200,133,132])
pred=read('future/shared_ridge10/predictions.csv');plan=read('future/shared_ridge10/replenishment.csv');sample=pred.merge(plan,on=['service_date','store_id','item_id','method_id']).query("service_date=='2026-11-03' and store_id=='S01'")
table('表 12 主路线输出示例：11 月 3 日 S01（活动日，未观测）',['品类','点预测 件','90%下端 件','90%上端 件','整数 q 件'],[[z.item_id,f(z.demand_point_units),f(z.lower90_units),f(z.upper90_units),str(z.q_units)] for z in sample.itertuples()], 'future/shared_ridge10/predictions.csv、replenishment.csv；论文显示四舍五入，CSV保留10位小数。')
p('点预测不是需要取整的采购量，q 由成本不对称、需求尾部与资源竞争共同决定。每件缺货相对报废都更昂贵，因此无网络限制时偏向较高需求分位；在产能紧张日期，则按边际减损在店品间分配。论文仅给可读摘要，执行依据是两个候选各自全量 CSV，不能据示例表替代剩余 4024 键。')
h('9 假设扰动与资源稳健性')
stress=info['sensitivity'];table('表 13 主路线条件情景的预定压力实验（未来未观测）',['情形','产能 / 预算','重新优化 元/日','备货变化 L1 件','原计划可行'],[[z['case'].replace('resource_','资源 ').replace('activity_','活动 ×').replace('all_demand_','全需求 ×'),str(z['capacity'])+' / '+str(z['budget']),f(z['reoptimized_scenario_loss_yuan_per_day']),str(z['q_l1_change_total']),'是' if z['fixed_original_plan_feasible'] else '否'] for z in stress], 'results/sensitivity.csv；L1 为全部4032键绝对备货变化之和；约束削减后的原计划损失不作可行策略比较。',[130,100,100,105,75])
p('在相同原情景下，资源缩至 1440 件 / 5400 元，重新优化损失从 603.97 增至 758.54 元/日，改为 1440 件 / 6000 元得到相同值，说明此处产能主导而非预算。放宽至 1760 件 / 6600 元可将条件损失降至 555.39 元/日；这不是当前允许方案，只揭示扩容的条件机会。单独预算降至 5400 元即改变 1361 件分配并升至 639.16 元/日，现预算有余量不意味着任何削减都无影响。原计划在收紧资源时可能不可行，必须重优化，不能用其旧损失当可执行对照。')
p('将活动日情景需求乘 1.2，固定原计划条件损失 849.80 元/日，重优化后仍为 830.02 元/日；备货总量基本不变，但跨店品重分配 1766 件，反映产能饱和。活动 ×0.8 可重优化至 548.25 元/日，备货变动 2244 件。全需求 ×1.1 时重优化损失 812.87 元/日、平均备货1595.74件，几乎日日触及产能。这些扰动检验决策对需求规模和活动迁移的敏感性，不是天气效应估计，也没有作为新预测候选或事后重选路线。')
h('10 局限、业务含义与后续评价')
p('第一，原件是虚构离线案例，不能外推真实市场效益。历史成熟标签是评价信息，而非原点知识；模型对较早版本训练后仍存在修订不确定性。第二，仅两个有依据的固定候选，研究结论是此协议下保留现政策，不是证明 ridge 对所有方法占优。第三，活动因果效应、天气需求效应及长步长效应不能从当前设计识别；未来每周两日活动显著更密，线性趋势和等权加性残差都可能失稳。')
p('第四，边际经验区间没有联合或分布无关保证，112 日历史残差与未来未必可交换，15-42 日宽度不扩张可能低估外推风险。第五，MILP 的数值最优仅对应保存的有限情景和两项损失，未计服务水平、供应可靠性、采购额入目标或结转库存；这些不在原题中，擅自添加会改变所求问题。第六，日配对重采样忽略时间相关，只是诊断。第七，作者自检不是独立验收，交付后的接收和未来真值评分需要不同上下文完成。')
p('业务上可采纳已经冻结的 R 全量整数计划，并重点关注产能达到 1600 件的日期及 K07、K08 高缺货成本品。当前数字支持“在同一历史需求上保留现政策”，没有发现替代方法改善，因此不以创新措辞掩盖零提升。若未来真值开放，应先按首交付原件评分：逐键 MAE / RMSE、90% 覆盖及上下漏出、逐日缺货 / 报废、活动与15-42日步长分组；评分后见结果另写有清晰日期的附录，不回改本交付选择、参数、区间或计划。')
h('附录 A 可复现材料与主张定位')
table('表 A1 需求、主张与可核验产物',['对象','关键证据','限制'],[['按时点数据','data/train_*.csv、evaluation_labels_fixed.csv、raw_row_identities.csv','成熟计分不倒灌训练'],['完整日残差','uncertainty/residual_coordinates_all.csv、pool_membership_all_origins.csv','记录具体96版本、原预测和快照'],['选路与历史实验','results/selection.json、historical_predictions_plans.csv、group_*.csv','验证与未来未用于选择'],['未来逐键输出','future/shared_ridge10/ 与 future/weekly_mean56/','每候选预测4032行、计划4032行'],['优化与稳健性','results/solver_*.csv、sensitivity.csv、validation/optimizer_tests.json','有限情景最优；压力非实测'],['论文与图表','paper.md、paper.pdf、figure_data/*.csv、claims.json','共享内容树，最终PDF逐页核验'],['复现与真实命令','source/v1/config.json、run_science.py、reference_policy.py、commands/*.json','原命令stdout/stderr字节base64保留']], '相对目录以 execution/science-v1 为科学产物根；论文位于 execution/paper-final-v4；源码、冻结与命令在 execution 根。',[82,288,140])
p('复现入口显式接受原始目录、配置文件和新输出目录；新输出目录存在即拒绝，避免覆盖首跑或失败。命令为：py -3.12 -X utf8 -B source/v1/run_science.py --raw <原件raw> --config source/v1/config.json --newout <全新目录>。在本任务原始运行中所有写入均在 execution/，没有共享状态、Git、技能或原件编辑。逐键 CSV 为 UTF-8，数值保留 10 位小数；NPZ 情景含残差日、42 个服务日、坐标顺序和等权向量；方法及最终原点见各模型元数据，重算可直接恢复缺货与报废。')
p('配置 SHA-256：'+freeze['source_hashes']['config.json']+'。科学适配源码 SHA-256：'+freeze['source_hashes']['run_science.py']+'。原政策副本 SHA-256：'+freeze['source_hashes']['reference_policy.py']+'。输入身份完整列表见 prospective-freeze.json 与 science-v1/run_identity.json；SHA-256 证明身份，不单独证明科学有效。')
p('首次工具恢复：误读嵌套锁路径后由协调者提供 R21 根的规范锁路径，未拟合、未改数据，记录于 recovery-log.json。科学首跑 exit 0，未发生科学失败或调参修复；论文首轮公式绘图因 mathsf 写法与本机解析器不兼容而 exit 1，源码、部分图像与原始命令全部保留于 paper-v1 和 source/build_paper_v1.py；新版本仅修复公式转置符号的显示和元数据说明，不改科学结果。当前作者自检 '+str(len(checks['checks']))+' 项在其计算范围内通过，独立接收待进行。后续任务为协调者冻结首次交付字节后，由不同接收上下文依据原题验收；未将这个待执行步骤伪写为完成。')
h('附录 B 来源与方法说明')
p('本研究的业务规则、原始数据、基准算法和时点接口直接来自锁定输入 PROBLEM.md、REQUEST.md、reference/BASELINE.md、reference/run.py 及事前 CLARIFICATION.md。旧 experiment.json 仅为参考方案，没有复用旧输出或旧选型结论。计算环境、库版本和实际秒数另存 environment.json / solver 记录。采用平方损失岭回归、经验分位和离散凸边际 MILP，数学定义与实际实现均已在本文给出；没有依赖外部答案、未运行的实验或宣称竞赛获奖。')
# Shared content serializes to editable Markdown and printable PDF.
md=[]
for e in elements:
    k=e['kind']
    if k=='title':md.append('# '+e['text'])
    elif k=='subtitle':md.append(e['text'])
    elif k=='heading':md.append('## '+e['text'])
    elif k=='paragraph':md.append(e['text'])
    elif k=='table':
        table_lines=['| '+' | '.join(e['headers'])+' |','| '+' | '.join(['---']*len(e['headers']))+' |']+['| '+' | '.join(map(str,row))+' |' for row in e['rows']]
        md += [e['title'],'\n'.join(table_lines),'来源：'+e['source']]
    elif k=='figure':md += ['!['+e['title']+']('+e['path']+')',e['title'],'来源：'+e['source']]
    elif k=='equation':md += ['$$\n'+e['latex']+'\n$$',e['explain']]
with (out/'paper.md').open('x',encoding='utf-8') as fpmd:fpmd.write('\n\n'.join(md)+'\n')
with (out/'paper_elements.json').open('x',encoding='utf-8') as fe:json.dump(elements,fe,ensure_ascii=False,indent=2)
with (out/'claims.json').open('x',encoding='utf-8') as fc:json.dump({'scope':'tables/figures generated from persisted source; prose rounded to displayed precision','claims':claims},fc,ensure_ascii=False,indent=2)
pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/simfang.ttf'));pdfmetrics.registerFont(TTFont('CNHead','C:/Windows/Fonts/simhei.ttf'))
styles={'body':ParagraphStyle('body',fontName='CN',fontSize=10.5,leading=16,spaceAfter=7,wordWrap='CJK'), 'head':ParagraphStyle('head',fontName='CNHead',fontSize=13.5,leading=19,spaceBefore=10,spaceAfter=7,keepWithNext=True,wordWrap='CJK'), 'title':ParagraphStyle('title',fontName='CNHead',fontSize=20,leading=27,spaceAfter=12,alignment=TA_CENTER), 'sub':ParagraphStyle('sub',fontName='CNHead',fontSize=9.5,leading=14,spaceAfter=14,alignment=TA_CENTER,textColor=colors.HexColor('#526271')), 'caption':ParagraphStyle('caption',fontName='CNHead',fontSize=9.4,leading=13,spaceBefore=7,spaceAfter=5,wordWrap='CJK',keepWithNext=True), 'source':ParagraphStyle('source',fontName='CN',fontSize=8.5,leading=12,spaceAfter=9,wordWrap='CJK',textColor=colors.HexColor('#526271')), 'cell':ParagraphStyle('cell',fontName='CNHead',fontSize=8.5,leading=12,wordWrap='CJK')}
flow=[];PW=510
def para(t,sty):return Paragraph(html.escape(str(t)).replace('\n','<br/>'),styles[sty])
for e in elements:
    k=e['kind']
    if k in ['title','subtitle','heading','paragraph']:flow.append(para(e['text'],{'title':'title','subtitle':'sub','heading':'head','paragraph':'body'}[k]))
    elif k=='table':
        flow.append(para(e['title'],'caption'));data=[[para(v,'cell') for v in row] for row in [e['headers']]+e['rows']];width=e.get('widths') or [PW/len(e['headers'])]*len(e['headers']);t=Table(data,colWidths=width,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef3')),('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#173c55')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#657f91')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#c9d3da')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f9fb')])]));flow.append(t);flow.append(para('来源：'+e['source'],'source'))
    elif k in ['figure','equation']:
        im=Image(str(out/e['path']));ratio=im.imageHeight/im.imageWidth;w=min(PW,im.imageWidth*.72);im.drawWidth=w;im.drawHeight=w*ratio;im.hAlign='CENTER'
        if k=='figure':flow.append(KeepTogether([im,para(e['title'],'caption'),para('来源：'+e['source'],'source')]))
        else:flow.append(KeepTogether([im,para(e['explain'],'body')]))
def foot(c,d):
    c.saveState();c.setStrokeColor(colors.HexColor('#c8d3da'));c.line(42,36,552,36);c.setFont('CNHead',8);c.setFillColor(colors.HexColor('#526271'));c.drawString(42,23,'生鲜网络预测与备货 | 首次交付：未来实绩未知');c.drawRightString(552,23,str(d.page));c.restoreState()
doc=SimpleDocTemplate(str(out/'paper.pdf'),pagesize=(595.28,841.89),rightMargin=42.28,leftMargin=42,topMargin=42,bottomMargin=47,title='公布时点约束下的生鲜需求预测与整数备货',author='R21 执行者',allowSplitting=True);doc.build(flow,onFirstPage=foot,onLaterPages=foot)
reader=PdfReader(out/'paper.pdf');texts=[pg.extract_text() for pg in reader.pages]
with (out/'pdf_text_checks.json').open('x',encoding='utf-8') as fx:json.dump({'pages':len(texts),'chars_by_page':[len(t) for t in texts],'contains_title':'公布时点约束下' in ''.join(texts),'contains_selection':'665.01' in ''.join(texts),'contains_validation':'631.81' in ''.join(texts),'contains_future_q':'64537' in ''.join(texts),'method_ids_present':all(x in ''.join(texts) for x in [R,W]),'visual_inspection':'pending rendered-page inspection, not substituted by extraction'},fx,ensure_ascii=False,indent=2)
print(json.dumps({'paper_md':str(out/'paper.md'),'paper_pdf':str(out/'paper.pdf'),'pages':len(texts),'characters':len(''.join(texts)),'figures':5,'tables':sum(e['kind']=='table' for e in elements),'pdf_sha256':hashlib.sha256((out/'paper.pdf').read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
