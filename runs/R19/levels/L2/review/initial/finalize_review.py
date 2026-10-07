from pathlib import Path
import json, hashlib, datetime

B = Path.cwd()
O = B / 'runs/R19/levels/L2/review/initial'
E = B / 'runs/R19/levels/L2/execution'
def read(name):
    return json.loads((O / name).read_text(encoding='utf-8'))
def save(name, obj):
    (O / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

raw_records = read('environment-and-raw-final.json')['raw_hashes_after_review']
zip_rows = []
for row in raw_records:
    p = O / 'zip_staged/raw' / row['file']
    zip_rows.append({'file': row['file'], 'zip_raw_sha256': digest(p), 'official_sha256': row['sha256'], 'matches': digest(p) == row['sha256']})
code_rows = []
for name in ('main.py', 'validate.py', 'check_cases.py'):
    paths = [O / 'zip_staged/code' / name, O / 'staged/code' / name, E / 'code' / name]
    hashes = [digest(p) for p in paths]
    code_rows.append({'file': name, 'zip_staged_execution_sha256': hashes, 'matches': len(set(hashes)) == 1})
assert all(x['matches'] for x in zip_rows + code_rows)
save('zip-scope-audit.json', {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'raw_files': zip_rows, 'code_files': code_rows, 'actual_execution_scope': 'ZIP15-item q2_cost smoke; byte-identical staged code additionally replayed official3000-item full pipeline', 'limits': ['ZIP not independently rerun full3000 a second time', 'unknown official judge I/O and arbitrary instance geometry not verified']})

common_limits = ['原三维问题全局最优未证明；库内最优和必要容量界分别限定', '更宽部分支撑/力矩、真实材料/动态/装卸路径未验证', '未知正式官方I/O和提交规则、附件2缺失完整订单及总体泛化未验证']
gates = [
 {'id':'a1','status':'pass','evidence':['independent-frozen-audit.json','paper-figures-audit.json','report.md','zip-scope-audit.json'],'reason':'完整回应Q1单车双目标及两单车型全运、Q2混合两目标和Q3技术报告；原件逐字段/库存/坐标姿态两率独立核算，附件2原单元格资格审计且完整扩展为原题可选。','limits':common_limits},
 {'id':'a2','status':'pass','evidence':['independent-frozen-audit.json','independent-objective-frontier.json','producer-checker-controls.json','parameter-replay-audit.json'],'reason':'官方单位、约束、累计传载/压力、间隙和类别条件进入独立几何检查，支撑/易碎/重心假设明确，双目标与库内/全局范围有数学区分。','limits':['完全支撑为声明的保守可行子域，不能据其拒绝推断更宽原题不可行','接触面积比例分担是静态模型假设']},
 {'id':'a3','status':'pass','evidence':['full_raw_reproduction.receipt.json','reproduction-independent-audit.json','parameter-replay-audit.json','zip_smoke_reproduction.receipt.json','paper-figures-audit.json','staging.json'],'reason':'从官方raw真正完整重跑并由不同程序核11套布局；9关键成功/1必要高度失败真实重放；ZIP独立烟雾，6图再生和73行数值原件追溯均成立，不以作者validation或退出码为真值。','limits':['26保存成功参数例未再次调用求解，全部当前输入/布局/目标已独立复算','旧历史调用未捕获的代码身份/UTC/遥测仍未知，未补造','ZIP full3000没有重复第二次求解；同代码在staged full3000真实执行']},
 {'id':'a4','status':'pass','evidence':['independent-frozen-audit.json','independent-objective-frontier.json','producer-checker-controls.json','parameter-replay-audit.json','reviewer-failures.json'],'reason':'实际基线、36成功/失败实验、易碎分支、种子/规模/承压/几何扰动和有意义边界反证齐备；独立有效上下界及候选最优核算准确限定，未把失败或宽松界变成原题最优结论。','limits':['仍有大原问题解质量区间及受限几何库，实验充分性质量维度为partial','25源宽口径布尔控制24一致，1部分支撑合法控制被声明保守模型拒绝，原差异保留']},
 {'id':'a5','status':'pass','evidence':['paper-pdf-text.txt','report-pdf-text.txt','pdf-render-audit.json','paper-figures-audit.json','paper-regeneration.diff.txt','report.md'],'reason':'完整中文科学论文11页与企业报告2页已实际逐页/六图查看，73行表值和6图独立一致；题意、模型、方法、验证、结果、局限链完整，摘要与正文范围相符。','limits':['排版/图表连线和日志式附录有可选表达改进，不构成事前门缺失','未预测分数、奖项或真实材料安全']},
 {'id':'a6','status':'pass','evidence':['workflow-observations.json','received-locks.json','immutability-final.json','staging.json','reviewer-failures.json','environment-and-raw-final.json'],'reason':'冻结交接使独立reviewer无需设计者私有解释从原件执行完整流程及关键分支，smoke与full区分、恢复/错误/checkpoint/未知资源字段真实保留；作者同上下文多角色未被当独立验收。','limits':['只验证本次L2单个交接，不证明通用工作流能力或层级因果','claim_evidence的Q3原32例描述需同步最终36例；属于可追溯元数据残余','外部host全部事件真实性及未知provider遥测未另行审计']}
]
quality = [
 {'dimension':'problem fidelity','status':'achieved','evidence':['independent-frozen-audit.json','paper-figures-audit.json','report.md'],'material_gap':None,'remaining_gap':'原附件2完整订单缺字段，资格限制准确保留。','scope/limits':'原附件1与明确合成扰动；更宽订单泛化未知'},
 {'dimension':'mathematical justification','status':'achieved','evidence':['independent-frozen-audit.json','independent-objective-frontier.json','producer-checker-controls.json'],'material_gap':None,'remaining_gap':'真实材料/动力与宽部分支撑力矩未验证，论文作静态保守假设。','scope/limits':'原件约束和声明模型内独立几何/累计压力及库内目标；没有原题全局最优证明'},
 {'dimension':'empirical sufficiency and fair alternatives','status':'partial','evidence':['independent-frozen-audit.json','independent-objective-frontier.json','parameter-replay-audit.json','paper-figures-audit.json'],'material_gap':'主混合车辆必要界7与方案13、费用4900与8850区间仍大；受限同类列/网格平台和易碎尾车可能实质改变解质量；组合改进未独立定位单一平台机制因果收益。','remaining_gap':'针对易碎与尾车建立更强合法界或同预算几何模式控制，保留当前实验，不新增无来源算法数量配额。','scope/limits':'36保存案例全独立检查、9成功关键案例新求解和1新失败；只支持明确预算/候选范围'},
 {'dimension':'reproduction and result-to-paper traceability','status':'achieved','evidence':['reproduction-independent-audit.json','parameter-replay-audit.json','paper-figures-audit.json','paper-regeneration.diff.txt','zip-scope-audit.json'],'material_gap':None,'remaining_gap':'旧调用身份/UTC未捕获保留null，26保存成功参数例未重复求解；Q3追溯元数据原32例应注明36终版。','scope/limits':'实际原件完整新运行、全部当前布局和73行/6图独立核对；未知历史与正式评阅I/O未验证'},
 {'dimension':'clarity and completeness of scientific argument','status':'achieved','evidence':['paper-pdf-text.txt','report-pdf-text.txt','pdf-render-audit.json','paper-figures-audit.json','report.md'],'material_gap':None,'remaining_gap':'图表连线避免暗示连续插值、可简化日志式附录及末页留白。','scope/limits':'全部11+2源PDF页及六图实际目视，科学链和现有证据对应；没有页数硬门'},
 {'dimension':'workflow transferability and autonomous gap resolution','status':'achieved','evidence':['workflow-observations.json','reviewer-failures.json','immutability-final.json','environment-and-raw-final.json'],'material_gap':None,'remaining_gap':'Q3原32例追溯描述同步为36；外部host完整事件和provider遥测未知。','scope/limits':'一次新上下文独立交接与恢复实际成功，不外推通用能力/层级效果；model/token/cost null'}
]
assert all((O / p).is_file() for g in gates + quality for p in g['evidence'])
assert read('immutability-final.json')['all_frozen_preparation_execution_unchanged']
result = {'status':'completed','review_round':'initial','actor':'r19_l2_reviewer','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method_frozen_before_receipt':True,'report':'report.md','a1_a6':gates,'quality_diagnosis':quality,'overall_mandatory_pass':all(g['status']=='pass' for g in gates),'complete_paper_produced':True,'complete_technical_report_produced':True,'mandatory_defects_found':[],'actual_coverage':{'frozen_files_received_and_rechecked':710,'final_layouts_independently_checked':11,'successful_saved_parameter_cases_fully_checked':35,'saved_failed_cases_necessary_height_checked':1,'pattern_layouts_independently_checked':213,'new_weighted_single_layouts_checked':22,'fresh_full_raw_cases':'all11 output layouts from official3000-item pipeline','fresh_successful_parameter_solver_cases':9,'fresh_expected_failed_parameter_solver_cases':1,'parameter_successes_not_fresh_solver_replayed_but_fully_checked':26,'zip_smoke_items':15,'paper_table_rows_independently_checked':73,'figures_regenerated_byte_equal_and_visually_checked':6,'pdf_pages_visually_checked':13,'analytical_source_wide_controls_matching_producer':24,'analytical_controls_total':25,'declared_conservative_scope_difference':1,'real_cli_controls':3},'failure_evidence':'reviewer-failures.json','limits':common_limits,'resources':{'model':None,'token':None,'cost':None,'actual_environment':'environment-and-raw-final.json','actual_call_receipts':'individual *.receipt.json retained','network_used':False,'installed_packages':False},'terminal':{'all_launched_calls_collected':True,'pending_calls':[],'ongoing_review_write_processes':[],'process_observation':'terminal-process-check.json'},'scope_statement':'First independent substantive review of frozen R19/C11/L2 only. No author/root expected judgment used. Required gates do not assert global optimum or contest award. Quality empirical dimension remains partial.'}
save('result.json', result)
assert read('result.json')['overall_mandatory_pass'] == all(g['status']=='pass' for g in read('result.json')['a1_a6'])
print(json.dumps({'result_saved':True,'all6_pass':result['overall_mandatory_pass'],'quality_partial':[q['dimension'] for q in quality if q['status']=='partial'],'zip_raw_and_code_hashes_match':True}, ensure_ascii=False))
