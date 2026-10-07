from pathlib import Path
import hashlib,json,datetime

root=Path.cwd()
out=root/'runs/R19/levels/L1/review/initial'
rows=[]
for lockname in ['runs/R19/levels/L1/review/preparation-lock.json','runs/R19/levels/L1/execution-lock.json']:
    lock=json.loads((root/lockname).read_text(encoding='utf-8'))
    for row in lock['files']:
        p=root/row['path'];exists=p.is_file()
        digest=hashlib.sha256(p.read_bytes()).hexdigest() if exists else None
        size=p.stat().st_size if exists else None
        rows.append({'path':row['path'],'lock':lockname,'size':size,'sha256':digest,'match':digest==row['sha256'] and size==row['size_bytes']})
post={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'file_count':len(rows),'all_match':all(r['match'] for r in rows),'files':rows}
(out/'post-review-lock-verification.json').write_text(json.dumps(post,ensure_ascii=False,indent=2),encoding='utf-8')
assert post['file_count']==260 and post['all_match']

def assertion(id,status,evidence,reason,limits):
    return {'id':id,'status':status,'evidence':evidence,'reason':reason,'limits':limits}

result={
 'schema':'R19-L1-independent-initial-review/1',
 'status':'initial_review_complete_mandatory_failure',
 'review_phase':'initial_blind_review_of_frozen_complete_artifacts',
 'informed_re_review':False,
 'frozen_method':'runs/R19/levels/L1/review/preparation-lock.json',
 'received_artifacts_lock':'runs/R19/levels/L1/execution-lock.json',
 'locks_received_and_post_review_match':True,
 'official_inventory':{'items':3000,'mass_kg':41100,'volume_cm3':287350000},
 'complete_paper_produced':True,
 'paper_pages':16,
 'complete_paper_substantive_conclusion':'完整论文已产出；原件绑定数值方案及主要论证可复现，质量仍有F1失败保护缺口，整体验收未通过。',
 'overall_mandatory_pass':False,
 'a1_a6':[
  assertion('a1','pass',['frozen-final-independent-audit.json','extra-source-history-audit.json','paper-crosscheck.json'],'所有原主问题与技术报告/程序交付；附件2可选几何及缺口有源。','有限候选最优范围明示；附件2完整业务数据不足不强加。'),
  assertion('a2','pass',['frozen-final-loads.csv','independent-bounds-pool.json','independent-pool-cost-cut.json'],'原件单位/目标/累计载荷/支撑/方向兑现；独立有效界和有限池求解。','静态均匀密度及保守支撑模型；不证明原几何全局最优。'),
  assertion('a3','pass',['raw-reproduce-receipt.json','raw-rerun-independent-audit.json','zip-raw-reproduce-receipt.json','zip-raw-rerun-independent-audit.json','selected-replay-independent-audit.json','paper-crosscheck.json'],'从官方原件两种原版入口真实重跑七组；全部关键主数值独立复算。','选中配方复算不等于全历史搜索重演；ZIP研究历史命令不齐全。'),
  assertion('a4','fail',['independent-boundary-tests.json','independent_boundary.py','independent-experiment-audit.json'],'F1:源G3易碎属性可被输出category=standard绕过，实际受压非法布局被原检查器接受。','现有冻结布局全合法；其余边界/参数/界证据不能抵消该失败。'),
  assertion('a5','pass',['paper-crosscheck.json','paper-pdf-extraction.json','paper-pages/'],'完整中文论文和16页PDF实读，主表/图源/坐标/逐车数值一致，科学论证完整。','小处图间距可改善；历史绝对耗时不独立复现。'),
  assertion('a6','pass',['raw-reproduce-receipt.json','zip-raw-reproduce-receipt.json','extra-source-history-audit.json','process-terminal-and-events.json'],'新接收者无需设计者私有解题提示可启动；smoke/full分离；角色和旧失败/修正保留。','a6通过不等于检查器无漏洞；历史调用身份/绝对时间仅保留产物支持。')
 ],
 'quality_diagnosis':[
  {'dimension':'problem fidelity','status':'achieved','evidence':['frozen-final-independent-audit.json','paper-crosscheck.json','extra-source-history-audit.json'],'material_gap':None},
  {'dimension':'mathematical justification','status':'achieved','evidence':['frozen-final-loads.csv','independent-bounds-pool.json','independent-pool-cost-cut.json'],'material_gap':None,'scope':'静态模型与有限候选；原几何最优未知是已披露限制。'},
  {'dimension':'empirical sufficiency and fair alternatives','status':'partial','evidence':['independent-boundary-tests.json','independent-experiment-audit.json','selected-replay-independent-audit.json'],'material_gap':'F1 source-category false acceptance','next_action':'源类别绑定及有效/无效成对测试和相关完整布局回归。'},
  {'dimension':'reproduction and result-to-paper traceability','status':'achieved','evidence':['raw-rerun-independent-audit.json','zip-raw-rerun-independent-audit.json','paper-crosscheck.json'],'material_gap':None,'scope':'关键结果复现；未称ZIP可重演全部研究历史。'},
  {'dimension':'clarity and completeness of scientific argument','status':'achieved','evidence':['paper-pdf-extraction.json','paper-pages/','paper-crosscheck.json'],'material_gap':None,'optional_polish':'T1布局图坐标标签与下方标题间距。'},
  {'dimension':'workflow transferability and autonomous gap resolution','status':'achieved','evidence':['extra-source-history-audit.json','raw-reproduce-receipt.json','zip-raw-reproduce-receipt.json'],'material_gap':None,'next_action':'接收检查补入F1；不抹去当前整体失败。'}
 ],
 'findings':[{
  'id':'F1','severity':'material','mandatory_assertion':'a4','status':'open',
  'source_locator':'official Attachment1 DOCX body14 and body22 G3 row',
  'code_locator':'runs/R19/levels/L1/execution/src/check.py:28,45,46; source checks:15-18',
  'witness_file':'independent-boundary-tests.json','witness_index':14,
  'witness':'T1: G3 original70x50x40 at0,0,0, G1 60x40x30 at0,0,40; only G3 output category changed to standard, type_id/config unchanged.',
  'author_checker_valid':True,'independent_valid':False,
  'impact':'源明确禁止的易碎受压可被检查器误放行；不推翻已独立证实的冻结布局。',
  'repair':'以type_id从配置恢复类别并拒绝矛盾元数据，核对方向/支撑类别分支，补有效与无效成对测试及相关完整布局回归。',
  'requires_new_solver':False
 }],
 'independent_coverage':{
  'frozen_final_layout_sets':7,'all_valid':True,'full_batch_tasks':4,'items_each_full_batch':3000,
  'scenario_configs':32,'scenario_fleets_audited':128,'scenario_fleets_all_valid':True,
  'raw_original_reproduce_sets':7,'zip_original_reproduce_sets':7,'rerun_exact_geometry_and_metrics':True,
  'fresh_selected_scenarios':5,'fresh_selected_fleets':20,'single_candidates_regenerated':32,
  'patterns_independently_audited':99,'restricted_pool_count_optimum':10,'restricted_pool_cost_optimum':7000,
  'controlled_boundary_tests':15,'independent_expected_matches':15,'author_expected_matches':14,
  'missing_business_input_rejected':True,
  'paper_crosscheck_groups':17,'paper_crosschecks_match':True,
  'attachment2_single_geometric_fits':64,'attachment2_business_optimization_verified':False,
  'not_rerun':['27 remaining parameter scenario solver paths (their128 total frozen fleets nevertheless all independently audited)','full12 baseline strategy batch search and6 module historic execution','all historical exact wall times'],
  'not_proved':['original continuous geometry global optimum','arbitrary new cargo identifiers/general business data','dynamic road/material stability','complete research history from ZIP alone']
 },
 'global_bounds':{'T1_vehicle_count':[16,20],'T2_vehicle_count':[7,10],'mixed_vehicle_count':[7,10],'mixed_cost_yuan':[4900,7000],'restricted_pool_proof_only':True},
 'read_order':'own raw-bound final7 and all32/128 scenario audits completed before author self-check JSON and failure logs; author checker later invoked as tested object',
 'source_files_changed':False,'production_artifacts_changed':False,'preparation_changed':False,
 'runtime_adaptations':['exact full copy in initial/sandbox','experiments.ROOT redirected into initial; selected five original cases','ZIP extracted into new initial directory'],
 'resource_events':{
  'tool_recovery_count':1,'tool_recovery':'combined final exited-PID Get-Process probe exit1 retained; structured followup confirms absent processes',
  'reviewer_production_substantive_repairs':0,
  'normal_research':'original costMILP limit60 returnedstatus1; justified verified-upper-bound cut separately returnedstatus0, both retained',
  'historical_parent_quota_errors':'not directly observed by this reviewer; no retrospective success claim'
 },
 'all_reviewer_launched_processes_terminal':True,
 'process_evidence':'process-terminal-and-events.json',
 'pending_calls':[],'spawned_child_agents':[],
 'actual_model':None,'token_usage':None,'cost':None,
 'award_prediction':None,'cross_level_or_general_capability_claim':None,
 'report':'report.md','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()
}
(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
assert {a['id'] for a in result['a1_a6']}=={'a1','a2','a3','a4','a5','a6'}
assert len(result['quality_diagnosis'])==6
for a in result['a1_a6']:
    for f in a['evidence']:assert (out/f).exists(),f
for q in result['quality_diagnosis']:
    for f in q['evidence']:assert (out/f).exists(),f
w=json.loads((out/'independent-boundary-tests.json').read_text(encoding='utf-8'))['tests'][14]
assert w['author_checker_valid'] and not w['independent_valid']
print(json.dumps({'status':result['status'],'locks_checked':len(rows),'all_locks_match':True,'a1_a6':{a['id']:a['status'] for a in result['a1_a6']},'quality_count':6,'f1_witness_name':w['name'],'all_processes_terminal':True},ensure_ascii=False))
