"""Seal executor handoff after all scientific processes and actual page review finish."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys

E=Path(__file__).resolve().parent.parent; ROOT=E.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    receipt=E/'evidence/018-final-package.json'
    check=json.loads((E/'evidence/selfcheck.json').read_text()); visual=json.loads((E/'evidence/visual_review.json').read_text())
    assert check['pass'] and visual['all_pages_actually_viewed'] and visual['verdict']=='pass'
    pdf=E/'delivery/paper/paper.pdf'; assert sha(pdf)==visual['pdf_sha256']
    records=[]
    for p in sorted((E/'evidence').glob('0*.json')):
        if p==receipt:continue
        j=json.loads(p.read_text()); assert j['state']=='finished',p
        assert 'end'in j and 'stdout_base64'in j and 'stderr_base64'in j; records.append({'path':p.relative_to(E).as_posix(),'exit_code':j['exit_code'],'begin':j['begin'],'end':j['end']})
    put(E/'evidence/process_terminal.json',{'all_recorded_processes_terminal':True,'records':records,'active_manifest_receipt_excluded_until_wrapper_exit':receipt.relative_to(E).as_posix(),'unknown_running_calls':[]})
    summary=json.loads((E/'delivery/results/run_summary.json').read_text())
    version=json.loads((E/'delivery/environment.json').read_text())
    mapping=[
      ('C1','Q1 口径可靠性',['data/audit.json','data/final_snapshot.csv','data/snapshot_boundaries.csv'],'原行去重与最高可用revision；origin和available_at筛选；逐原点训练数和later_changed_train_labels','2 / 表2',[],'身份与时间口径，不证明预测能力'),
      ('C2','Q1 日期、商品、门店规律',['data/descriptive_panel.csv','results/descriptive_service_date.csv','results/descriptive_weekday_monday_zero.csv','results/descriptive_item_id.csv','results/descriptive_store_id.csv','results/descriptive_holiday.csv'],'最终原点快照按service_date sum；各组demand_units mean，holiday独立日期nunique','3',['01_daily.png','02_groups.png'],'相关描述，不解释因果'),
      ('C3','Q1 选模、外样本误差及覆盖',['results/backtest_metrics.csv','results/historical_predictions_plans.csv','results/selection.json','results/holdout_by_horizon.csv','results/holdout_by_item.csv','results/holdout_by_store.csv'],'选模stage=selection,policy=stochastic按model均值loss；保留stage=holdout；MAE=mean abs(actual-point), inclusive interval coverage','4-5 / 表3-4',['03_holdout_horizon.png','04_holdout_item.png'],'时间冻结且保留未调参；无未来覆盖保证'),
      ('C4','Q1 全期预测和分布',['results/future_predictions.csv','uncertainty/future_scenarios.csv','uncertainty/residual_vectors.csv','uncertainty/residual_lineage.csv','data/final_feature_lineage.csv'],'1344笛卡尔键，point加同日外样本error向量非负截断；ready<=origin；等权归一；经验分位数端点10位小数','5 / 7',[],'同日相关被保留，跨日场景依赖只是压力约定'),
      ('C5','Q2 整数方案、求解及分配',['results/future_replenishment.csv','results/decision_summary.csv','results/solver_evidence_future.csv','results/solver_evidence_history.csv','data/optimizer_tests.json','results/allocation_item_id.csv','results/allocation_store_id.csv'],'由raw成本与max核对q；g平均缺货+waste；每日件量sum q与sum c*q；按店/商品sum；solver objective/bound/gap','6-7 / 表5-6',['05_future_resources.png','06_allocation.png'],'只证明经验分布下优化及硬可行性'),
      ('C6','Q2 风险与资源取舍',['results/sensitivity.csv','results/decision_summary.csv'],'case holiday/weather为指定需求倍数的固定计划与重优化期望；case resource按capacity/budget比较；q_l1_change=sum abs(q_alt-q)','8 / 表7-8',['07_sensitivity.png'],'压力假设非观测；改变资源行不替代原约束'),
      ('C7','Q3 完整论文与可复现',['paper/paper.md','paper/paper.pdf','environment.json','results/run_summary.json'],'同一report块生成源稿与PDF；013/014从原件完整重跑；015全表重算；016-017最终11页逐页核查','9 / 表9',[],'作者接收不是独立通过')]
    registry=[]
    for cid,question,paths,calc,loc,figures,limit in mapping:
        registry.append({'claim_id':cid,'original_requirement':question,'results':[{'path':'delivery/'+p,'sha256':sha(E/'delivery'/p)} for p in paths],'columns_filter_computation':calc,'paper_location':loc,'figures':[{'path':'delivery/figures/'+p,'sha256':sha(E/'delivery/figures'/p)} for p in figures],'raw_origin':'runs/R20/inputs/raw/ with hashes in delivery/data/audit.json','status':'author_recomputed','limitation':limit})
    put(E/'claim_evidence_map.json',registry)
    readme=f'''# R20 鲜食建模完整执行交付

正式产物在 `delivery/`。这是一份原创合成数据离线研究，并非正式赛题或真实商业收益。所有结果由附件重建，执行者自检不等同独立验收。

## 阅读与使用

- 完整中文论文：`delivery/paper/paper.md`（可编辑），`delivery/paper/paper.pdf`（正式渲染版，{check['pdf_pages']}页，全部页面已实际查看）。
- 未来预测：`delivery/results/future_predictions.csv`，1344个唯一日期/门店/商品键，点预测、非负90%边际区间及名义水平。
- 整数备货：`delivery/results/future_replenishment.csv`，同样1344键，q_units为非负整数。每日1600件，采购不超过6000元，逐店品不超过raw商品上限。14日合计22400件，采购78851元。
- 历史实验、损失分项、未来每日资源与情景损失、按店/商品分配、压力方案均在`delivery/results/`。
- 场景与残差来源在`delivery/uncertainty/`；训练/评价分离、特征发布时间、原行号和内容哈希在`delivery/data/`。
- 图表及由同一块结构生成的公式图在`delivery/figures/`；claim_registry.json把论文主张映射到机器结果。

## 从原附件重跑的一条主入口

在仓库根目录`{ROOT.as_posix()}`运行：

```powershell
py -3.12 -X utf8 -B scripts/record_command.py --out runs/R20/execution/evidence/your-unique-rerun-record.json -- py -3.12 -X utf8 -B runs/R20/execution/code/run.py --out runs/R20/execution/your-empty-output
```

选择一个尚不存在的输出目录和命令记录路径，避免覆盖历史。入口一次从raw生成审计、全部历史实验、完整未来预测/备货、不确定性、压力表、七幅分析图、Markdown与PDF。执行代码由相对路径定位原件`runs/R20/inputs/raw/`、`input-lock.json`、`design-lock.json`和冻结设计包；它校验设计文件身份，但不消费设计smoke或其他阶段结果。迁移时须保留这一仓库相对布局及冻结锁所列文件，不能仅移动单一脚本。程序无网络或外部账号依赖。

实际Python 3.12.8；依赖为{', '.join(n+' '+v for n,v in version['packages'].items())}。绘图/PDF使用Windows中文字体`C:/Windows/Fonts/simhei.ttf`。当前宿主实测可用，其他平台字体路径和未指定产物格式能力未知，未承诺通用跨平台。渲染工具为实际可用Poppler pdftoppm。

```powershell
py -3.12 -X utf8 -B runs/R20/execution/code/selfcheck.py --out runs/R20/execution/your-empty-output --compare runs/R20/execution/delivery
pdftoppm -r 100 -png runs/R20/execution/your-empty-output/paper/paper.pdf runs/R20/execution/your-empty-output/paper/page
```

作者真实的两次同版本完整重跑是013（delivery）和014（clean_rerun），均exit0。最终015重新从raw核对快照、全部预测与计划键、精确采购约束、14日情景损失、32组历史指标、真实晚到及修订拒绝、所有可用性lineage，并比较全部同路径CSV（求解秒数是运行测量，明确忽略）。独立新上下文接收仍由root完成。

## 数字与概率约定

CSV以10位小数保存浮点数；点需求不用整数。区间端点在计算覆盖前统一舍入10位小数，保存和重算的包含关系一致。有限值与比较的冻结数值容差为1e-7；件量为精确整数，采购成本用原件与Decimal精确重算，不用容差放宽硬预算。83个等权场景的理论权重为1/83，CSV权重和有微小舍入误差；读入后先核验非负有限和在1e-7内，再归一化用于期望，检查器保持目标重算1e-6元容差。

## 时间、选模与适用范围

实验配置在任何性能测量前冻结。7/8启动误差池；7/22、8/5、8/19选模；9/2补充校准；9/16保留验证；所有原点18:00一次预测14天。训练需求先按available_at筛选再取最高revision；历史最终后到标签只评价，完整同日误差向量ready<=原点才校准。settlement和天气实况都未进入预测。远期未知促销由当原点最近56日训练商品平均折扣代替，并保留unknown指示。

当前方案是{summary['selected_model']}，选择准则为历史同约束日均损失，最终83个可用同日误差向量等权构造分布。未来区间覆盖未知；历史天气无同批14日长预报、历史只有两个单日节假日。天气变量未用于预测，±10%全期需求和假期±20%是明确假设的压力代理，不能解释为估计的雨量弹性或新观测。场景保留同日96维相关；同一向量沿14日重复是压力依赖约定，不声称已识别跨日联合分布，不报告14日总损失尾部保证。求解器的最优性只针对经验分布目标；未来真实损失和收益没有真值可验。比较随机政策与点贪心同时改变分布处理与优化方式，不能把全部政策改善归因于不确定性。

## 失败、修复和版本

001起命令保存真实开始/结束、完整输出、退出码；最初阅读与建目录只有宿主记录，未事后伪造。002嵌套旧PowerShell读取出现中文乱码，后续明确UTF-8阅读恢复，原文件不变。

004初始研究误将上一窗末端未到达标签放入校准，已撤回；旧代码与output_initial保留。005修复ready边界并全量重跑。007第一版论文已逐页查看，发现标题孤立和一个单位用语误写；原report源码与页面保留。008较早完整运行的report导入在分页修正前已完成，输出仍见原问题，故不作为最后论文；013/014使用固定修正版本。010因CSV概率未归一化重算失败，012修复后发现区间浮点整数边界覆盖漂移；013/014统一端点精度重跑。所有失败输出与repair-001至004保留，不按两次错误中止，也不降低原题接收标准。

`output/`、`output_initial/`、`output_corrected/`、`final/`是过程或被替代版本，`clean_rerun/`是同版本复现；只有`delivery/`是交付。code/archive保存真实迭代源版本。manifest覆盖这些历史文件，以便检查，不能把文件存在当成结果被接受。

## 接收与停止状态

执行者完成T01–T07及作者接收/清洁重跑。T08新上下文独立接收和T09最终判定尚由root负责。evidence/selfcheck.json、visual_review.json、process_terminal.json记录实际范围和终态；模型/tokens/cost未知为null。完整manifest列全部执行域文件大小与SHA256，排除manifest自体和其生成时尚活动的018记录（该记录在工具返回后已终态，root最终冻结可覆盖）。没有外部联系、发布或后台继续任务。完成封装后停止写入等待root冻结。
'''
    (E/'README.md').write_text(readme,encoding='utf-8')
    ids=['T01','T02','T03','T04','T05','T06','T07','T08','T09','NEXT']
    accept={'T01':'source hash, raw snapshot, actual capability','T02':'availability lineage, finite/unit/keys and true late-row rejection','T03':'before-performance config and baseline','T04':'1344 forecasts, history metrics, empirical uncertainty','T05':'1344 integers, exact raw-resource feasibility, objective and oracle','T06':'same-information comparisons, demand/resource sensitivity and allocation','T07':'complete Chinese paper, true figures, all final pages reviewed','T08':'fresh independent receiving checks','T09':'root final decision and freeze','NEXT':'root start independent receiving T08'}
    ledger=[]
    for id in ids:
        done=id in ids[:7]
        ledger.append({'id':id,'depends_on':[] if id=='T01' else (['T07'] if id=='T08' else ['T08'] if id=='T09' else ['T01'] if id=='T02' else [ids[ids.index(id)-1]] if id!='NEXT' else ['T07']),'owner':'executor' if done else 'root','write_domain':'runs/R20/execution/' if done else 'root-assigned independent receiving domain','status':'done_author_scope' if done else 'pending_root','acceptance':accept[id],'evidence':['delivery/','evidence/selfcheck.json','evidence/visual_review.json','evidence/process_terminal.json'] if done else [],'blocker':None,'next_action':'root independent acceptance' if done else 'root dispatch clean original+actual artifact bundle without expected outcomes'})
    put(E/'ledger.json',ledger)
    put(E/'checkpoint.json',{'state':'executor complete; independent acceptance pending','entrypoint':'README.md','authoritative_artifact_root':'delivery/','input_lock':'runs/R20/input-lock.json','design_lock':'runs/R20/design-lock.json','model':None,'tokens':None,'cost':None,'processes':'all scientific and rendering calls terminal; packaging wrapper finalizes after script','unknown_call_states':[],'next_task_id':'T08','next_owner':'root','next_action':'freeze execution then dispatch fresh independent receiver with original inputs and actual delivery, no expected ranking/author diagnosis','executor_will_stop_writing':True})
    files=[]
    for p in sorted(E.rglob('*')):
        if not p.is_file() or p in [E/'manifest.json',receipt]:continue
        files.append({'path':p.relative_to(E).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha(p)})
    manifest={'schema':'r20-complete-execution-manifest/1','created_at':datetime.now(timezone.utc).isoformat(),'scope':'all execution files including failed/superseded versions; authoritative final result is delivery/','excluded':['manifest.json','evidence/018-final-package.json'],'files':files,'telemetry':{'model':None,'tokens':None,'cost':None},'acceptance':'author checks complete; independent acceptance pending'}
    put(E/'manifest.json',manifest)
    print(json.dumps({'entrypoint':str(E/'README.md'),'manifest':str(E/'manifest.json'),'manifest_sha256':sha(E/'manifest.json'),'file_count':len(files),'bytes':sum(x['size_bytes'] for x in files),'pdf_sha256':sha(pdf),'pdf_pages':check['pdf_pages'],'process_records_terminal':len(records),'author_checks_pass':True,'independent_acceptance':'pending','stop_writing_after_wrapper_terminal':True},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
