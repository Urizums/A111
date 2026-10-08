from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;R=O.parents[5];PRE='runs/R19/levels/L4/review/recheck-1/';OLD='runs/R19/levels/L4/review/initial/'
def read(name):return json.loads((O/name).read_text(encoding='utf8'))
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def identity(p):return {'path':p.relative_to(R).as_posix(),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
critical=read('critical-coordinate-review.json');controls=read('controls-summary.json');trace=read('numerical-trace.json');cli=read('full-cli-receipts.json');frozen=read('frozen-control-review.json');clean=read('clean-rerun-receipt.json')
assert critical['all_valid'] and critical['all_summary_metrics_match'] and critical['source_rebuilt_fields_match_fresh_raw_contract']
assert controls['all_assertions_passed'] and frozen['all_assertions_passed'] and all(x['assertion_passed'] for x in cli)
assert clean['exit_code']==0 and trace['all_geometry_match'] and trace['all_paper_numeric_rows_match']
locks=[]
for loc in ['runs/R19/levels/L4/execution-v2-lock.json','runs/R19/levels/L4/execution-lock.json','runs/R19/levels/L4/review/initial-lock.json','runs/R19/levels/L4/review/preparation-lock.json','runs/R19/levels/L4/review/recheck-preparation-lock.json','runs/R19/inputs/raw-lock.json','runs/R19/evaluation-lock.json','runs/R19/levels/L4/design-lock.json']:
    lock=json.loads((R/loc).read_text(encoding='utf-8-sig'));checks=[]
    for f in lock['files']:
        a=identity(R/f['path']);checks.append({'path':f['path'],'match':all(a[k]==v for k,v in f.items())})
    assert all(x['match'] for x in checks);locks.append({'lock':loc,'files':len(checks),'all_match':True,'checks':checks})
save('end-integrity.json',locks)
unchanged=read('old-new-identities.json');initial=json.loads((O.parent/'initial/result.json').read_text(encoding='utf8'))
limitations=[
 'This is the same reviewer after disclosed first-review feedback, not a second blind trial or an independent fresh actor.',
 'All17 historical parameter optimizations and all three historical method optimizations were not rerun; exact dependency identities delimit reused independent evidence.',
 'Original failing decimal-coordinate artifact and lost supplemental first-review subprocess telemetry remain unavailable; current successful calls do not restore or certify those historical bytes/receipts.',
 'Finite heuristic candidates and restricted-column MILP states do not prove original global optima or a complete Pareto frontier.',
 'Attachment2 lacks quantities, masses, classes, payloads and distance/cost semantics; only its64 dimension interval geometry tests are supported.',
 'Single full support, uniform static center and two-segment columns are declared conservative assumptions, not field vibration/axle load/unloading certification.',
 'Finite/range controls cover the disclosed mechanism and material input contract; no universal robustness probability is inferred.',
 'Numeric-equivalent float source reconstruction changes raw CSV bytes; normalized coordinates and independently recomputed goals are equal.',
 'Historical method timings retain historical scope and are not a universal performance promise.',
 'Minor PDF linear formula and long experiment-ID cell/pagination polish remains optional; mathematical conditions and full labels are explicit in the complete text.'
]
ea=[PRE+x for x in ['source-audit.json','source-contract.json','critical-coordinate-review.json','numerical-trace.json','reading-render.json','affected-diffs.json']]
items=[
 ('a1','All original single/fleet/mixed/report duties still have explicit source-bound artifacts; eight frozen final schemes and nine new full-route schemes independently feasible; Attachment2 remains honestly bounded.',ea,limitations[3:6]),
 ('a2','Fresh unit/source and bound calculations agree; original objective, cumulative/contact load and support mathematics were unchanged by the finite-value/preflight patch. Same-budget historical comparison and mechanism arguments remain attributable to unchanged dependencies.',ea+[PRE+'reuse-parameter-evidence.json',OLD+'report.md'],limitations[3:6]),
 ('a3','Actually extracted new package ran to exit0 using reviewer raw-rebuilt input freshly matched to direct originals; every new complete fleet and single scheme independently checked. Four goals and full normalized rows reproduce;39 table rows and64 geometry pairs agree.',ea+[PRE+'archive-reception.json',PRE+'clean-rerun-receipt.json'],[limitations[1],limitations[7],limitations[8]]),
 ('a4','96 actual paired CLI controls plus4 actual complete receiving calls and35 frozen independent coordinate controls substantiate finite/range rejection without rejecting valid floor/touch/stack/zero-class cases. Impossible1001cm item returns clear exit3 failure without success summary. Material NaN false-acceptance defect is absent in this frozen version; retained methods/bounds/parameter counterfactuals remain substantive.',[PRE+'controls-summary.json',PRE+'controls-progress.json',PRE+'frozen-control-review.json',PRE+'full-cli-receipts.json',PRE+'critical-coordinate-review.json',PRE+'controls/solver_impossible_1001_cube/receipt.json',OLD+'defect-controls.json'],[limitations[1],limitations[6]]),
 ('a5','Actually reread both full Chinese manuscripts, inspected all15 page layouts and enlarged affected pages; argument/assumptions/actual method comparison/parameter interpretation/limits stay coherent. Changed repair and historical/new receipt statements are consistent with actual program and preserved first verdict; critical rows and figures retain trace.',ea+[OLD+'report.md'],[limitations[3],limitations[9]]),
 ('a6','Same reviewer as a new consumer independently received the new archive and ran raw-source full and altered-inventory paths without designer explanation. New finite receiving and explicit infeasibility branches preserve original constraints. Original actor, failures, old first verdict and informed correction are explicitly distinguished; smoke is not full acceptance.',[PRE+'archive-reception.json',PRE+'clean-rerun-receipt.json',PRE+'full-cli-receipts.json',PRE+'controls-summary.json',PRE+'affected-diffs.json',PRE+'old-new-identities.json',OLD+'report.md',OLD+'result.json'],[limitations[0],limitations[2],limitations[6]])
]
qa=[
 ('problem fidelity','Original goal chain, inventory, coordinates and units remain intact; consequences of fragile orientation/full support and Attachment2 missing fields are explicit.','Confirm actual fragile rotation permission before field use; rerun the declared conservative branch if needed.'),
 ('mathematical justification','Shared geometry, support load recursion, objective distinctions, density and relaxed lower bounds remain coherent, with conservative model restrictions and method-choice rationale explicit.','A future composite-support or field-mechanics model needs new geometry/force data and checks.'),
 ('empirical sufficiency and fair alternatives','Historical fair96/12/90 comparison,17 counterfactuals, seeds, valid bounds and negative mechanism evidence are reused only under exact dependencies. New96 controls,4 whole receiving cases and21 independent groups close the actual finite receiving gap.','Keep control artifacts and extend targeted controls only for a newly observed mechanism; do not infer universal reliability.'),
 ('reproduction and result-to-paper traceability','New zip source hashes match frozen code, direct originals match reviewer input, actual clean full run and independent critical schemes agree;39 main rows/64 geometry values and unchanged figure sources trace.','Preserve source/config/code identities and historical/new timings separately.'),
 ('clarity and completeness of scientific argument','Both complete Chinese texts are readable and scientifically connected. Models, method choice, results, validations, interpretation and limitations are substantive; repair prose discloses first failure rather than rewriting it.','Optional formula/table-label/page polish; retain finite-candidate and physical assumptions.'),
 ('workflow transferability and autonomous gap resolution','Actual new-consumer full execution and varied-input computation work without designer intervention. Finite receiving and understandable no-fit correction have real paired evidence, and original failures/actors are retained honestly.','Historical missing failing-coordinate bytes and old lost telemetry remain disclosed and must never be backfilled as original evidence.')
]
result={
 'task_id':'R19-C11-L4-informed-recheck-1','actor':'/root/r19_l4_reviewer','review_type':'informed_recheck','informed_by_prior_verdict':True,'status':'informed_recheck_accepted','mandatory_all_pass':True,
 'summary':'Frozen v2 materially repairs the observed NaN receiving defect and unclear infeasibility branch; actual new-package full execution, paired controls and independent critical feasibility/paper checks support this informed acceptance. Initial review remains unchanged.',
 'original_initial_verdict':{'status':initial['status'],'a1_a6':[{'id':x['id'],'status':x['status']} for x in initial['a1_a6']],'retained_unmodified':True,'retrospectively_changed':False},
 'a1_a6':[{'id':id,'status':'pass','reason':reason,'evidence':ev,'limitations':lim} for id,reason,ev,lim in items],
 'quality_diagnosis':[{'dimension':dim,'status':'achieved','reason':reason,'evidence':ea+[PRE+'controls-summary.json',PRE+'reuse-parameter-evidence.json',OLD+'report.md'],'material_gap':None,'next_action':nxt} for dim,reason,nxt in qa],
 'source_binding':{'direct_original_reread':True,'pdf_pages':3,'docx_paragraphs':22,'docx_tables':1,'xlsx_all_sheets':3,'reviewer_rebuilt_input':'prior own independently rebuilt source input reused, then each official field freshly independently parsed and matched; not author data accepted by flag','source_fields_match':critical['source_rebuilt_fields_match_fresh_raw_contract'],'end_integrity':[{k:x[k] for k in ['lock','files','all_match']} for x in locks]},
 'performed_checks':{'actual_cli_controls':controls['cases'],'legal_control_cases':controls['legal_cases'],'all_control_assertions_passed':True,'frozen_independent_coordinate_controls':len(frozen['checks']),'all_frozen_control_assertions_passed':True,'actual_whole_fleet_receiving_cli_calls':len(cli),'independent_coordinate_groups':len(critical['results']),'groups_by_origin':{name:sum(x['origin']==name for x in critical['results']) for name in sorted(set(x['origin'] for x in critical['results']))},'frozen_static_LP_representative_trucks':sum(len(x['frozen_representative_checks']) for x in critical['results']),'new_archive_main_receipt':clean,'critical_fresh_comparisons':critical['fresh_comparisons'],'paper_rows_checked':trace['paper_trace_rows'],'geometry_pairs_checked':trace['attachment2_pairs'],'both_full_manuscripts_actually_read':True,'all_pdf_page_layouts_viewed':15,'affected_full_page_views':['paper1','paper9','enterprise2','enterprise3']},
 'confirmed_final_values':[dict(x['metrics'],scenario=x['scenario']) for x in critical['results'] if x['origin']=='new_frozen_selected'],
 'evidence_reuse':{'identical_original_production_files':len(unchanged['same_files']),'changed_original_production_files':len(unchanged['changed_or_missing']),'identity_file':PRE+'old-new-identities.json','parameter_independent_calculations_reused':17,'dependencies_file':PRE+'reuse-parameter-evidence.json','new_run_is_not_all_historical_research_rerun':True,'historical_missing_artifacts_restored':False,'old_first_review_replaced':False},
 'retained_historical_gaps':[limitations[2]],'new_observed_material_defects':[],'failures_and_recovery':{'expected_bad_input_rejections_retained':True,'expected_infeasible_input_receipt_retained':True,'new_reviewer_unexpected_tool_errors':[],'prior_errors_not_rewritten':[OLD+'result.json','runs/R19/levels/L4/review/preparation/result.json']},
 'resources':{'provider':None,'model':None,'tokens':None,'cost':None,'whole_review_elapsed_seconds':None,'environment':initial['resources']['environment'],'measured_new_full_solve_seconds':clean['elapsed_seconds'],'measured_control_subprocess_sum_seconds':controls['actual_sum_subprocess_seconds'],'measured_four_receiving_subprocess_sum_seconds':sum(x['elapsed_seconds'] for x in cli),'network_searches':0,'installs':0,'subagents_spawned':0,'whole_review_short_deadline':None,'no_generic_two_error_stop':True},
 'boundaries':{'write_domain':PRE,'producer_or_initial_or_preparation_modified':False,'other_levels_or_root_synthesis_read':False,'author_pass_as_truth':False},
 'termination':{'known_async_sessions':[{'id':19604,'state':'finished','exit_code':0},{'id':64933,'state':'finished','exit_code':0}],'pending_session_ids':[],'all_synchronous_subprocess_calls_returned':True,'background_processes_started':0,'subagents_started':0,'finalizer_exit0_receipt_required':True,'stop_writing_after_manifest':True},
 'limitations':limitations,'frozen_at':datetime.now(timezone.utc).isoformat()
}
save('result.json',result)
report='''# L4 知情复审报告

本次状态 `informed_recheck_accepted`，a1— a6均为pass，原六质量维度在本次明确范围内为achieved。新版冻结附件已实际修复首审发现的NaN坐标误放行与不可装输入说明不足；新程序包从自身原件重建输入完成全量主路径，关键全方案独立约束/原目标重算及消费稿核对成立。判定来自本接收者的真实调用和独立计算，不来自作者checks。

这是同一接收者获知首审反例后的informed_recheck，不是新的盲审。首审 `initial_review_not_fully_accepted`、a4 fail、a6 partial及真实NaN反例永久保持原字节；本轮不追改首审，也不宣称旧接收器当时正确。

## 身份、输入与冻结接收

验收者 `/root/r19_l4_reviewer`，方法在新版正式交接前冻结。接收新版840文件、首审164文件、复审准备4文件、官方原件3文件、评价2文件、设计7文件锁全部匹配；终态另复核原生产417文件与原准备17文件等八锁，均无变化。只读授权自身L4、C11、官方原件、冻结评价及本轮新旧冻结产物；没有读取其他层、共享REPORT/root综合、其他判定或旧题解，没有联网、安装或另派agent。写入仅recheck-1。

直接重新读取官方3页PDF、DOCX22段/库存表及XLSX3个工作表。原件单位为cm/kg/元每趟，附件2产品mm、车辆m；载荷面积由cm²除10000转m²。自身首审原件重建JSON在消费者副本沿用，并与本轮直接解析的两车型/五类各字段逐项核对，全部相符；没有把作者的valid标记当输入真值。原库存、易碎/定向、3cm间隙、500kg/m²、原UV/UW分母与整批计费口径不变。

新旧417同位置文件中393字节相同、24变更。解压新版program_attachment.zip到自身consumer目录；全部压缩包核心源码与新冻结code匹配，包括numeric_contract.py。安全解压和各文件身份见archive-reception.json、old-new-identities.json。源码差异明确限定为求解前输入有限性/范围和单件可装检查、接收前数值检查及清楚失败回执；几何放置、模式目标、库存需求等式及载荷算法没有被放宽。

## 实际修复控制与完整新执行

本轮96个真实CLI控制保存逐项命令、退出码、stdout/stderr、结果和实测秒数；没有只运行作者自测。合法原地板G1、合法0坐标、相邻边界接触、标准件完整支撑链及一类零库存均通过。x/y/z/l/w/h六字段各NaN/+Inf/-Inf全部非零且valid=false，拒绝发生于几何/支撑/载荷/指标前，未生成可消费成功汇总。另实测负坐标、非正尺寸、空/非数值、正体积重叠、安全高度不足；货物尺寸/单重、车辆尺寸/载重/费用、数量与gap/压力/容差的代表性非有限/范围值均正确拒绝。负/非整数/布尔/字符串库存没有截断补齐。对应35组坐标/合法控制另由事前冻结独立检查器复算，断言一致。

求解CLI的非法单重/间隙返回exit2；全部字段仍合法但一件1001cm立方体、其余库存0的控制返回exit3、INFEASIBLE_INPUT，failure.json明确指出G1在许可姿态、间隙和载重下不能进任一车型，无成功summary，无旧矩阵traceback。它是实际不可装实例，未强加私有错误措辞。另用库存[20,25,7,10,12]、12模式/2起点/8秒小预算实际求解四目标，独立验证每件/支撑/费用，分别形成单车型1车以及混型1辆T1；总重1011kg、体积7.06575m³。这是新输入计算，不能替代原完整主路径。

新版压缩包完整主路径在自身原件重建3000件、原96/12/90配置上实际结束exit0，耗时136.8259859秒。对四个冻结整批另真实调用新版validator CLI，全部通过；这与独立校核分开。独立检查共21组：4冻结整批、4冻结选中单车、4新完整复跑整批、5新完整复跑单车、4改变库存整批。逐件原尺寸/方向、库存有效ID、每车可能相交对、边界/间隙、重量、完整单父支撑、易碎/定向、累计外载/接触压力、support_loads及原定义UV/UW/费用均重算，全部有效且汇总一致。8个新/冻结代表最大件数车再以事前冻结静力/力矩检查器核验。

| 原完整目标 | 本轮独立值 | 整体UV | 整体UW |
| --- | --- | --- | --- |
| 仅T1整批 | 20辆，9000元 | 74.044% | 34.250% |
| 仅T2整批 | 10辆，7000元 | 68.992% | 41.100% |
| 混型最少车 | 1T1+9T2，10辆，6750元 | 72.884% | 42.812% |
| 混型最低费 | 1T1+9T2，10辆，6750元 | 72.884% | 42.812% |

四个新完整整批与冻结选中方案的所有规范化行字段相同，原CSV字节不同来自等值原尺寸的int/float写法，不能称字节复现。原总体积287.35m³、总重41100kg以及松弛下界15/7/7辆和4900元本轮独立重算。密度187.5kg/m³导出UW上界59.810625%/77.156625%，双100%不能实现；有限档案、受限模式MILP和上述可行值都不是原问题全局最优证明。

## 科学方法、证据复用与最终消费稿

原三路线96模式/12起点/90秒比较、17组24/4/8参数研究、3种子及机制反证的独立首审证据按具体身份复用，未重演全部旧优化。17参数各input/summary/placements/support_loads逐字节对照且对应配置/实验与图源身份未变；复用记录明确列在reuse-parameter-evidence.json。求解/接收差异没有改动原柱/模式搜索或那些有限结果的几何/受力意义。新4整批/4单车仍另外独立复算，复用不是替代新接收。旧33作者复查只作为作者材料，未充当本轮独立真值。

完整重读最终两篇中文MD，实际打开/render两个PDF共12+3页、查看全部页布局并放大论文1/9页与报告2/3页变更内容。论文的原问题链、假设及保守后果、统一几何/载荷/目标、柱与排布方法、整数需求等式、有限候选质量、实际方法公平比较、参数机制解释、现场条件和报告建议仍形成可独立理解的完整论证。随机扰动没有整批必胜优势的结果仍保留，经典最大空闲矩形选择依据实际效果/成本/解释性，不用模型数量代替依据。

39行论文主表/逐车/单车/参数/附件2数值本輪核对一致；其中17参数的独立几何计算明确复用旧身份，其余关键目标/单车/载荷本轮重新算。附件2原XLSX区间/单位重新解析，64组保守/乐观格点值重算一致；缺批量/单重/类别/载重/距离只能支持尺寸几何结论。图源文件字节不变并与表图讨论绑定，投影和3D图只说明而不证明可行。

新摘要/7.3/7.4和企业报告6节真实区分历史复跑、当前作者复跑、首审失败与待知情接收；原a4/a6失败没有被文稿改写成当时通过。README的有限数字合同、合法零数量、退出1/2/3、单件不可装说明与实测一致。PDF无实质正文裁切/缺字，长实验ID单元及线性公式可继续润色，全文和讨论已明确完整条件，不以页数或表格匹配单独判论文质量。

## a1— a6与六维判定

| id | 本轮status | 实质理由 |
| --- | --- | --- |
| a1 | pass | 原各问目标及附件/报告/全部坐标仍覆盖，关键最终方案独立源绑定可行，材料不足有边界 |
| a2 | pass | 原数学/单位/载荷/下界/目标及同预算方法理由成立；补丁未改变原可行域与科学解释 |
| a3 | pass | 新包实际原件主路径与新输入执行、关键目标约束独立重算、数值表图定位成立 |
| a4 | pass | 实测合法/非法配对、有限及值域、明确不可装、新完整场景填补本版本接收缺口；旧界/比较/参数实质证据保留 |
| a5 | pass | 完整中文论证、消费稿实际阅读及关键值一致，修订诚实标原错误和informed范围 |
| a6 | pass | 新消费者实际运行无需设计者干预，数值拒收及不可装纠正明确，smoke/full和原角色/错误/首审/本轮分开 |

| 原冻结dimension | 本轮status | 证据与范围 |
| --- | --- | --- |
| problem fidelity | achieved | 原目标链、逐件交付和材料约束仍保持；歧义/不足影响明确 |
| mathematical justification | achieved | 共享数学、合法界、压力与方法结构有实质依据，保守后果明确 |
| empirical sufficiency and fair alternatives | achieved | 原公平研究依身份保留，新真实反例与完整检查关闭本版有限接收缺口；非普遍可靠性结论 |
| reproduction and result-to-paper traceability | achieved | 新原件主路径实际运行和关键新复算，39行/64几何及图源一致 |
| clarity and completeness of scientific argument | achieved | 完整中文文本/消费稿实际读，结果解释及受限结论成立 |
| workflow transferability and autonomous gap resolution | achieved | 实际消费者全路径及新输入、明确拒收/不可装纠正成立，原缺失物证诚实保留 |

这些achieved不将旧首审追认为全通过，不证明通用能力/竞赛得分或其他层因果优劣。仍需现场核实易碎旋转、外包装和承重；多支撑、轴载、振动或装卸若新增，须另建数据与力学证据。算法启发式限制和下界差距是论文公开的结论范围，不靠修validator消除。

## 保留缺口、真实调用与终态

原小数失败坐标未保存、首审补充包装器遗失的旧子调用退出码/stdout/timing均仍未知，原输入/错误/修复记录及初审serializer/pid错误保留。新成功调用不是那些旧调用的恢复，不补造或追认证据；本轮没有未预期工具错误，所有故意非法与不可装非零输出逐项保存。

provider/model/token/cost及整轮总耗时不可得，保持null。已知136.826秒完整调用、96控制实测合计及4接收调用实测合计分别列回执。无联网、安装、另派agent、整体短deadline或通用两错停止规则。本轮两异步session19604、64933均真实exit0，其他同步子调用均返回；无自己启动后台进程或未决会话。终态八锁复核一致，result/report与相对工作根逐文件manifest在最后保存；manifest排除自身，随后停止写入。
'''
(O/'report.md').write_text(report,encoding='utf8')
save('manifest.json',{'schema':'relative-workroot-payload-manifest/1','workroot':str(R),'files':[identity(p) for p in sorted(O.rglob('*')) if p.is_file() and p!=O/'manifest.json']})
manifest=O/'manifest.json';print(json.dumps({'status':result['status'],'a1_a6':[{'id':x['id'],'status':x['status']} for x in result['a1_a6']],'quality':[{k:x[k] for k in ['dimension','status']} for x in result['quality_diagnosis']],'manifest_files':len(read('manifest.json')['files']),'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'all_known_sessions_finished':True,'pending_sessions':[],'stop_writing':True},ensure_ascii=False,indent=2))
