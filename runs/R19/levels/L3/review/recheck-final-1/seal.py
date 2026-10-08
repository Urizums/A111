"""Final own review result, source immutability checks, terminal receipt and manifest."""
from pathlib import Path
import json,hashlib,datetime,time,ast,psutil
H=Path(__file__).resolve().parent;B=H.parents[5];L=H.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):
    (H/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
t=time.perf_counter();now=datetime.datetime.now(datetime.UTC).isoformat()
start=json.loads((H/'lock-start.json').read_text(encoding='utf-8'));final=[]
for record in start['locks']:
    lock=Path(record['lock']);j=json.loads(lock.read_text(encoding='utf-8-sig'));bad=[]
    for f in j['files']:
        p=B/f['path']
        if not p.is_file() or sha(p)!=f['sha256'] or p.stat().st_size!=f['size_bytes']:bad.append(f['path'])
    # Preserve actual scope from the known frozen lock name; do not enumerate root siblings.
    lock_rel=lock.relative_to(L).as_posix().replace('-lock.json','')
    actual={p.relative_to(B).as_posix() for p in (L/lock_rel).rglob('*') if p.is_file()}
    listed={f['path'] for f in j['files']}
    row={'lock':str(lock),'count':len(listed),'hash_errors':bad,'set_matches':actual==listed,'start_lock_hash_same':sha(lock)==record['lock_sha256'],'lock_sha256':sha(lock)}
    assert not bad and row['set_matches'] and row['start_lock_hash_same'],row
    final.append(row)
save('lock-end.json',{'utc':now,'locks':final})
source=json.loads((H/'raw-reread.json').read_text(encoding='utf-8'))['source_locks']
source_final=[]
for r in source:
    j=json.loads((B/r['lock']).read_text(encoding='utf-8-sig'));f=next(x for x in j['files'] if x['path']==r['path']);ok=sha(B/f['path'])==f['sha256'];assert ok;source_final.append({'path':r['path'],'matches':ok})
save('source-lock-final.json',source_final)
orig=json.loads((L/'execution-lock.json').read_text(encoding='utf-8-sig'))
copy_ok=all(sha(H/'consumer/execution'/Path(f['path']).relative_to('runs/R19/levels/L3/execution'))==f['sha256'] for f in orig['files'])
assert copy_ok
run=json.loads((H/'consumer-run.json').read_text(encoding='utf-8'))
initial=json.loads((L/'review/initial/result.json').read_text(encoding='utf-8'))
observed=[]
for p in (H/'consumer/execution-v2/attempts').glob('*/receipt.json'):
    j=json.loads(p.read_text(encoding='utf-8'))
    if not j.get('pid'):continue
    # Includes already-frozen producer receipts retained in consumer copy.
    try:proc=psutil.Process(j['pid']);live=abs(proc.create_time()-j['process_create_time'])<.01 and proc.is_running()
    except psutil.NoSuchProcess:live=False
    assert not live,(p,j['pid']);observed.append({'receipt':p.relative_to(H).as_posix(),'pid':j['pid'],'same_identity_live':False})
assert not (H/'consumer/execution-v2/logs/active_child.json').exists()
assert not (H/'consumer/execution-v2/logs/launch_guard').exists()
own_bindings=[]
for name in ['independent_checker.py','independent_review.py','independent-source-audit.json']:
    old=L/'review/initial'/name;assert sha(old)==sha(H/name);own_bindings.append({'file':name,'sha256':sha(old),'byte_equal_to_frozen_own_initial':True})
save('final-check.json',{'utc':now,'original_consumer_numerical_base_byte_unchanged':copy_ok,'numeric_base_count':len(orig['files']),'own_checker_dependencies':own_bindings,'observed_receipt_process_identities_terminal':observed,'pending_calls':[],'active_self_started_processes':[],'source_locks_match':True})
reasons=[
('a1','pass',['raw-to-current-input.json','consumer-run.json','report.md'],'原六目标、完整技术报告、程序和附2有界范围直接回答，主输入与正式库存未改变。',['只接受所声明静态可行候选；原全局最优及附2完整业务批次未证。']),
('a2','pass',['raw-reread.json','text-and-source-audit.json','numeric/','adapter-and-observation.md'],'原单位、源数值、支撑/质量/目标公式与数学解释相符，六任务独立逐件复算成立。',['单支持、均匀质量、静态与易碎朝向均为明确解释；不能推广道路安全。']),
('a3','pass',['lock-start.json','lock-end.json','consumer-run.json','pdf-regeneration.json','numeric-identity.json'],'组合版本真正接收，当前消费者六正式任务实际干净重求，自有checker复核；图表、正文和PDF可追溯，副本导出14页文本/像素同新版。',['168/348/四库/4508等未本次全部再跑，引用自己首次实查与同字节身份；历史64/1674未完全复跑。']),
('a4','pass',['consumer-run.json','producer-receipt-audit.json','review/initial evidence identity','report.md'],'原真实边界、比较和界保留，当前非法输入/流程负路径实际执行；正文没有升级最优性、公平预算或泛化主张。',['一基准对27重启及后续研究努力不同；连续Pareto、原3D全局最优、多支持/动态工程仍未证。']),
('a5','pass',['text-and-source-audit.json','pdf_visual/','pdf-regeneration.json','adapter-and-observation.md','report.md'],'完整新中文论文与报告问题—假设/选模—实验—图表—结论链充分，重要单位和平方/负幂实际可见；750单元按顺序保真，82结果表行保持首次数值。',['视觉为全部14页总览、4页放大及31科学局部行；文本匹配只是转录证据，科学/中文判断另由全文实读及源算支持。']),
('a6','partial',['consumer-run.json','producer-receipt-audit.json','failures.json','report.md'],'当前唯一attempt原流/PID和活跃后继阻止、超时及退出保留真实改善；原三CLI原流/PID丢失和两次并行目标偏离不可追认恢复。',['真正监视器崩溃后退出子进程reconcile分支未实验；整体历史峰值内存未知null；当前改善不使首次a6变pass。']),
]
qualities=[
('problem fidelity','achieved',['raw-reread.json','raw-to-current-input.json','report.md'],'原问题与数据解释完整；权威包装规则/完整附2业务输入尚缺。','取得权威规则或新业务输入后只重算受影响范围。'),
('mathematical justification','achieved',['numeric/','text-and-source-audit.json','report.md'],'保守模型数学充分支持所述结果，原最优、多支持/动态工程未知。','若提升研究质量，研究联合支持与更紧有效界；不作为固定配额。'),
('empirical sufficiency and fair alternatives','achieved',['numeric-identity.json','consumer-run.json','report.md'],'单题、声明配置的实证充分；比较努力不同，历史局部研究未全复跑。','若提出同预算因果优势或更广泛化，先补目标相应的新实证再提高主张。'),
('reproduction and result-to-paper traceability','partial',['consumer-run.json','text-and-source-audit.json','pdf-regeneration.json','producer-receipt-audit.json'],'当前源算/表图/正文/PDF一致；历史三CLI原始流不可恢复，峰值内存未知。','保留未知，每新attempt保留原始流，不补造旧证据。'),
('clarity and completeness of scientific argument','achieved',['adapter-and-observation.md','pdf_visual/','report.md'],'全文理解与推理链充分、PDF科学语义正确；没有必须继续修复的表达缺陷。','货物表跨页/末附录空白可选优化，无页数/改句配额。'),
('workflow transferability and autonomous gap resolution','partial',['consumer-run.json','producer-receipt-audit.json','report.md'],'前瞻接收与进程机制实测改善；历史资源/原流缺口及崩溃分支未验证。','未来有需求时独立有界实测崩溃接续，保留真实退出未知。'),
]
result={'task_id':'R19-C11-L3-first-substantive-informed-recheck','role':'/root/r19_l3_reviewer','phase':'first_substantive_informed_recheck','write_boundary':'runs/R19/levels/L3/review/recheck-final-1/','status':'partial_acceptance_historical_a6_limit','current_summary':{'pass':5,'fail':0,'partial':1},'quality_summary':{'achieved':4,'partial':2,'missing':0},'first_review_unchanged':{'status':initial['status'],'a1_a6':initial['a1_a6'],'quality_diagnosis':initial['quality_diagnosis'],'summary':{'pass':4,'fail':1,'partial':1}},'a1_a6':[{'id':i,'status':s,'evidence':e,'reason':r,'limits':ls} for i,s,e,r,ls in reasons],'quality_diagnosis':[{'dimension':d,'status':s,'evidence':e,'material_gap':g,'next_action':a} for d,s,e,g,a in qualities],'a5_required_repair_closed':True,'current_required_chinese_semantic_repairs':[],'historical_unrecoverable_limit_preserved':True,'past_receipts_reconstructed':False,'combined_packet_required':['execution','execution-v2'],'current_actual_checks':{'frozen_original_files':3723,'frozen_revision_files':354,'frozen_initial_files':3052,'frozen_recheck_preparation_files':9,'source_locks':23,'raw_to_current_input_groups':7,'formal_tasks_freshly_run':6,'formal_pairs_independently_checked':2380553,'small_instance_CLI_runs_independently_checked':2,'invalid_input_actual':1,'registry_probe_actual_children':3,'producer_child_stream_receipts_identity_checked':9,'final_PDF_pages_visually_observed':14,'full_size_pages':4,'science_crop_lines_observed':31,'ordered_md_pdf_units':750,'result_table_rows_bound':82,'actual_export_runs':1,'regenerated_page_text_and_pixels_equal':14},'reused_initial_studies_not_rerun_this_time':['168 comparisons','348 parameter solves /116 recommendations','four restricted MILPs/4508 library entries','40 Attachment2 fits and original method controls'],'not_verified':initial['not_verified']+['genuine crashed-monitor exited-child reconciliation experiment'],'source_changed':False,'original_execution_changed':False,'prior_review_or_preparation_changed':False,'network_used':False,'software_installed':False,'uploaded':False,'submitted':False,'author_messaged':False,'root_shared_state_modified':False,'model':None,'token_usage':None,'cost':None,'award_or_score_prediction':None,'whole_task_deadline':None,'whole_task_compute_budget':None,'pending_calls':[],'active_self_started_processes':[],'child_agents':[],'all_own_calls_terminal':True,'finished_at_utc':now,'next_action':'Root freezes this completed review. Preserve historical a6 partial; no further required scientific/PDF/Chinese repair identified in current delivered scope.'}
save('result.json',result)
ledger={'phase':'completed_informed_recheck','calls':['receive.py exit0 7.1657679s tool wall','exercise_consumer.py attempt1 exit1 6.2084237s: own source dependency omission after formal CLI exit0','exercise_consumer.py recovery exit0 4.634376s: reused known terminal receipts','text_source_audit.py exit1 1.8546243s: successful audits written, GBK console print only','persisted audit read exit0; no repeated audit','PDF export wrapper exit0 1.6461674s tool wall; exporter child .9410247s','producer receipt audit and raw-input comparison synchronous exit0','seal.py terminal on normal return; no pending sessions'],'runtime_receipts':'runtime/','registered_child_receipts':'consumer/execution-v2/attempts/','consumer_outer_CLI_calls':run['calls'],'formal_CLI_seconds':5.578952800002298,'consumer_registered_numerical_children':4,'registry_probe_children':3,'PDF_export_children':1,'per_registry_child_limit_seconds':120,'timeout_probe_seconds':.15,'outer_CLI_receipt_wait_seconds':135,'aggregate_memory_peak_bytes':None,'OS_memory_enforcement':False,'model':None,'token_usage':None,'cost':None,'whole_task_deadline':None,'unknown_calls_restarted':False,'failures_and_recovery':'failures.json','pending_calls':[],'active_self_started_processes':[],'child_agents':[],'all_calls_terminal_on_normal_return':True}
save('runtime-ledger.json',ledger)
json_count=0;py_count=0
for p in H.rglob('*.json'):
    json.loads(p.read_text(encoding='utf-8-sig'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));json_count+=1
for p in H.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));py_count+=1
save('seal-receipt.json',{'finished_at_utc':datetime.datetime.now(datetime.UTC).isoformat(),'strict_json_files':json_count,'python_AST_files':py_count,'elapsed_seconds':time.perf_counter()-t,'exit_code':0,'pending_calls':[],'active_self_started_processes':[]})
# Nested immutable manifests are payloads; only this review root manifest excludes itself.
files=sorted(p for p in H.rglob('*') if p.is_file() and p!=H/'manifest.json')
manifest={'schema':'R19-L3-informed-independent-recheck/1','phase':'first_substantive_informed_recheck_terminal','generated_at_utc':datetime.datetime.now(datetime.UTC).isoformat(),'payload_count':len(files),'payload_bytes':sum(p.stat().st_size for p in files),'files':[{'path':p.relative_to(H).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in files],'manifest_excludes_itself':True,'pending_calls':[],'active_self_started_processes':[]}
save('manifest.json',manifest)
assert all(sha(H/f['path'])==f['sha256'] for f in manifest['files'])
print(json.dumps({'status':result['status'],'current_summary':result['current_summary'],'quality_summary':result['quality_summary'],'payload_count':len(files),'payload_bytes':manifest['payload_bytes'],'manifest_sha256':sha(H/'manifest.json'),'strict_json_files':json_count,'python_AST_files':py_count,'all_terminal':True},ensure_ascii=True))
