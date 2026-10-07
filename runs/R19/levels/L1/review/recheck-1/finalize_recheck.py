from pathlib import Path
import json,hashlib,datetime,difflib,os
ROOT=Path.cwd();OUT=ROOT/'runs/R19/levels/L1/review/recheck-1';OLD=OUT.parent/'initial';V2=ROOT/'runs/R19/levels/L1/execution-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for name in ['review/preparation-lock.json','execution-lock.json','execution-v2-lock.json']:
    lp=ROOT/'runs/R19/levels/L1'/name
    for x in read(lp)['files']:
        p=ROOT/x['path'];rows.append({'path':x['path'],'expected_sha256':x['sha256'],'actual_sha256':sha(p),'match':p.stat().st_size==x['size_bytes'] and sha(p)==x['sha256']})
post={'count':len(rows),'all_match':all(r['match'] for r in rows),'files':rows}
(OUT/'post-review-lock-verification.json').write_text(json.dumps(post,ensure_ascii=False,indent=2),encoding='utf-8');assert post['all_match']
adapt=[];diff=[]
for name in ['independent_audit.py','audit_experiments.py','paper_crosscheck.py','run_receipt.py']:
    a=OLD/name;b=OUT/name;sa=a.read_text(encoding='utf-8');sb=b.read_text(encoding='utf-8')
    note='identical mathematical method text, normalized line endings; output parent naturally recheck-1'
    if name=='independent_audit.py':note='execution-root path; compare config physical fields independent of informational version label (3.0 versus3.1-informed-F1); no tolerance/constraint change'
    if name=='run_receipt.py':note='execution-root path only; outputs naturally recheck-1'
    adapt.append({'file':name,'initial_sha256':sha(a),'current_sha256':sha(b),'adaptation':note})
    diff.extend(difflib.unified_diff(sa.splitlines(True),sb.splitlines(True),fromfile='initial/'+name,tofile='recheck-1/'+name))
(OUT/'method-adaptations.json').write_text(json.dumps(adapt,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'independent-method-differences.diff').write_text(''.join(diff),encoding='utf-8')
from independent_audit import raw_config
base=read(V2/'configs/base.json');raw=raw_config();physical=lambda c:{k:v for k,v in c.items() if k!='version'}
version_comparison=read(OUT/'numerical-version-comparison.json')
history={n:sha(V2/'history'/('initial_review_'+n))==sha(OLD/n) for n in ['report.md','result.json']}
history['original_result.json']=sha(V2/'history/original_result.json')==sha(ROOT/'runs/R19/levels/L1/execution/result.json')
failed=read(V2/'history/repair_regression_attempt_01_failed.json')
history_report={'base_physical_fields_equal_raw':physical(base)==physical(raw),'all_final_and_scenario_results_identical_to_initial':all(r['identical'] for r in version_comparison if r['relative']!='configs/base.json'),'base_only_difference':'version3.0 ->3.1-informed-F1','initial_review_history_copies_match':history,'first_author_regression_passed':failed['passed'],'first_author_regression_total':failed['total'],'first_author_regression_failed_cases':[t for t in failed['tests'] if not t['pass_self_check']],'author_final_regression_total':read(V2/'review/repair_regression.json')['total'],'author_final_regression_passed':read(V2/'review/repair_regression.json')['passed'],'author_claim_limit':'compact retained log, not reviewer platform tool transcript','source_binding_read_before_author_selfcheck':True}
(OUT/'source-history-consistency.json').write_text(json.dumps(history_report,ensure_ascii=False,indent=2),encoding='utf-8')
receipts=[read(OUT/(n+'-receipt.json')) for n in ['raw-reproduce','zip-raw-reproduce','zip-make_paper','zip-render_paper']]
assert all(r['process_terminal'] and r['exit_code']==0 for r in receipts)
terminal={'all_launched_subprocess_receipts_terminal':True,'receipts':receipts,'numeric_exec_sessions':{'87404':'finished exit0','48083':'finished exit0','29101':'finished exit0'},'pending_calls':[],'spawned_child_agents':[],'reviewer_tool_failures':0,'reviewer_production_repairs':0,'actual_model':None,'tokens':None,'cost':None,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/'process-terminal-and-events.json').write_text(json.dumps(terminal,ensure_ascii=False,indent=2),encoding='utf-8')
boundary=read(OUT/'independent-source-boundary-tests.json');affected=read(OUT/'affected-layout-independent-recheck.json');zipr=read(OUT/'zip-paper-rebuild-audit.json');paper=read(OUT/'paper-crosscheck.json')
assert boundary['test_count']==boundary['independent_expected_matches']==boundary['revised_expected_matches']==83
assert affected['total_layout_sets']==235 and affected['all_independently_valid'] and affected['all_revised_checker_valid']
assert zipr['all_payloads_identical'] and zipr['pdf_page_texts_match'] and zipr['pdf_raster_pixels_match'] and paper['all_checks_match']
f1=next(r for r in boundary['tests'] if r['name']=='source category relabel conceals load above G3');rules=sorted({r['rule'] for r in f1['revised_errors']})
assert not f1['revised_valid'] and {'category_source_mismatch','fragile_loaded'}<=set(rules)
initial=read(OLD/'result.json');assert not initial['overall_mandatory_pass']
def a(id,evidence,why,scope):return {'id':id,'status':'pass','evidence':evidence,'reason':why,'scope':scope}
result={
 'schema':'R19-L1-independent-informed-re-review/1','status':'informed_re_review_complete_pass','informed_re_review':True,'round':'recheck-1',
 'same_reviewer':True,'frozen_method_unchanged':True,'frozen_method':'runs/R19/levels/L1/review/preparation-lock.json','reviewed_execution':'runs/R19/levels/L1/execution-v2-lock.json',
 'original_initial_status_preserved':initial['status'],'original_initial_a1_a6':initial['a1_a6'],'original_initial_quality_diagnosis':initial['quality_diagnosis'],'original_initial_overall_pass':False,
 'initial_failure_retroactively_passed':False,'overall_mandatory_pass':True,'complete_paper_produced':True,'paper_pages':17,
 'a1_a6':[
 a('a1',['frozen-final-independent-audit.json','independent-experiment-audit.json','paper-crosscheck.json','../initial/report.md'],'全部原问题链和合法主方案保持。','原PDF附件2可选；完整业务输入不足，不强加业务解。'),
 a('a2',['frozen-final-loads.csv','affected-layout-independent-recheck.json','source-differences.diff','../initial/independent-bounds-pool.json','../initial/independent-pool-cost-cut.json'],'物理模型/算法未改变；原数学与模式池证明适用，来源约束修复。','静态均匀密度/保守支撑模型，原连续几何最优仍未证明。'),
 a('a3',['raw-reproduce-receipt.json','raw-rerun-independent-audit.json','zip-raw-reproduce-receipt.json','zip-raw-rerun-independent-audit.json','zip-paper-rebuild-audit.json'],'修订代码和ZIP从原件真实重建七方案；独立几何/指标吻合；图文真实重建。','不称为重新运行全部历史搜索或原题全局求解。'),
 a('a4',['independent-source-boundary-tests.json','affected-layout-independent-recheck.json','../initial/selected-replay-independent-audit.json','../initial/independent-single-pool-replay.json'],'F1实拒且物理违规仍检出；自构83检查匹配预期，235布局独立及修订验证有效。','有限反例/参数证据，不保证任意恶意输入/所有数值尺度；原最优界范围不变。'),
 a('a5',['paper-crosscheck.json','paper-pdf-extraction.json','paper-pages/','zip-paper-rebuild-audit.json'],'17页成稿及修订论证实读，17组主数值与全部图文重建一致。','未核验年度模板/AI规则/提交接口；完整练习论文与算法附件。'),
 a('a6',['source-history-consistency.json','source-differences.diff','raw-reproduce-receipt.json','zip-raw-reproduce-receipt.json','process-terminal-and-events.json'],'新接收者实际启动，初审F1和67/68回归失败保留，接收合同源绑定，作者自检与知情复审区别明确。','单actor历史由保留产物支持，不推断全部历史工具身份/绝对时间。')],
 'quality_diagnosis':[
  {'dimension':'problem fidelity','status':'achieved','evidence':['frozen-final-independent-audit.json','paper-crosscheck.json'],'scope':'沿用初审原题/附件2解释，来源原库存及规则保持。','remaining_gap':None},
  {'dimension':'mathematical justification','status':'achieved','evidence':['source-differences.diff','affected-layout-independent-recheck.json','../initial/independent-bounds-pool.json','../initial/independent-pool-cost-cut.json'],'scope':'原数学模型与有限池证据；原几何全局最优未知且公开。','remaining_gap':None},
  {'dimension':'empirical sufficiency and fair alternatives','status':'achieved','evidence':['independent-source-boundary-tests.json','affected-layout-independent-recheck.json','../initial/selected-replay-independent-audit.json','../initial/independent-single-pool-replay.json'],'scope':'F1关闭使初审partial转achieved；沿用初审真实公平候选/关键参数/有效界证据；不主张穷尽反例或统计泛化。','remaining_gap':None},
  {'dimension':'reproduction and result-to-paper traceability','status':'achieved','evidence':['raw-rerun-independent-audit.json','zip-raw-rerun-independent-audit.json','paper-crosscheck.json','zip-paper-rebuild-audit.json'],'scope':'原件最终方案与图文复现；ZIP含新增构建依赖，不是所有过去历史自动重演。','remaining_gap':None},
  {'dimension':'clarity and completeness of scientific argument','status':'achieved','evidence':['paper-pdf-extraction.json','paper-pages/','source-differences.diff'],'scope':'17页完整论文、首次失败与修订范围解释克制。','remaining_gap':None,'optional_polish':'第13页因整张参数表移到下一页而留白；可调整排版，不影响读数/论证。'},
  {'dimension':'workflow transferability and autonomous gap resolution','status':'achieved','evidence':['source-history-consistency.json','raw-reproduce-receipt.json','zip-raw-reproduce-receipt.json'],'scope':'同一案例实际接收/修正/失败保留，不作跨层因果或一般能力宣称。','remaining_gap':None}
 ],
 'findings':[{'id':'F1','initial_status':'open_initial_a4_fail','current_status':'closed_in_execution_v2','witness':'independent-source-boundary-tests.json','same_original_witness':True,'revised_valid':False,'rules':rules,'initial_unchanged':True}],
 'added_independent_checks':{'source_boundary_controls':83,'original_boundary_cases':15,'layout_sets':235,'final_tasks':7,'patterns':99,'scenarios':32,'scenario_fleets':128,'smoke':1,'raw_copy_rerun_tasks':7,'zip_raw_rerun_tasks':7,'zip_entries':145,'paper_numeric_groups':17,'pdf_pages_visually_reviewed':17,'zip_paper_texts_and_pixels_match':True},
 'inherited_initial_checks':['raw-bound mathematical and source interpretation','five critical parameter solver reruns','32 single candidate regeneration and dominance','independent99-pool count/cost proofs with original60s timeout preserved','attachment2 raw64 geometry pairs and business missing fields','retained initial failures and process probe recovery'],
 'not_repeated':['all32 parameter solver optimization paths','full12 baseline batch/6 module historic search','MILP optimality proofs already validated for byte-identical99-pattern pool','dynamic road/material/door loading scenarios without original inputs','all historical absolute times'],
 'remaining_nonmandatory_limits':['original continuous geometry optimum unproved: T1[16,20],T2/mixed[7,10],cost[4900,7000]','arbitrary new cargo identity/schema and malicious input scales not validated','attachment2 full business optimization lacks fields','single case and deterministic scenarios do not establish general statistical performance'],
 'all_received_and_post_review_locks_match':True,'locked_entries_checked':656,'original_execution_changed':False,'v2_execution_changed':False,'preparation_or_initial_changed':False,
 'author_selfcheck_used_as_independent_evidence':False,'actual_model':None,'token_usage':None,'cost':None,'award_prediction':None,
 'reviewer_tool_recoveries':0,'reviewer_production_substantive_repairs':0,'all_reviewer_processes_terminal':True,'pending_calls':[],'spawned_child_agents':[],
 'report':'report.md','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()
}
(OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
for a in result['a1_a6']:
    for p in a['evidence']:assert (OUT/p).exists(),p
for q in result['quality_diagnosis']:
    for p in q['evidence']:assert (OUT/p).exists(),p
print(json.dumps({'status':result['status'],'locked_entries':len(rows),'a1_a6':{a['id']:a['status'] for a in result['a1_a6']},'F1_rejection_rules':rules,'quality_statuses':[q['status'] for q in result['quality_diagnosis']],'all_processes_terminal':True},ensure_ascii=False))
