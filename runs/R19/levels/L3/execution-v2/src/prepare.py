from pathlib import Path
import json,hashlib,shutil,datetime
V2=Path(__file__).resolve().parents[1]
OLD=V2.parent/'execution'
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 now=datetime.datetime.now(datetime.UTC).isoformat()
 save(V2/'logs/resources.json',{'repair_window_seconds':2400,'declared_at':now,'purpose':'PDF scientific fidelity, complete Chinese editorial review, receiving checks and prospective receipt/process behavior','per_child_limit_seconds':120,'concurrent_children_limit':1,'memory_target_MB':1200,'memory_enforcement':'not OS enforced','original_window_seconds':3600,'original_consumed_seconds':1929.69895,'original_parallel_target_deviations':2,'old_missing_CLI_details':[{'pid':None,'stdout':None} for _ in range(3)],'original_peak_memory_MB':None,'tokens':None,'model':None,'cost':None,'new_numerical_main_solves_planned':0,'previous_interrupted_repair':'only input reads and font probe; no execution-v2 numerical output/pending solver existed at resume'})
 manifest=json.loads((OLD/'manifest.json').read_text(encoding='utf-8'));bad=[]
 for r in manifest['files']:
  p=OLD/r['path']
  if not p.exists() or p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:bad.append(r['path'])
 assert not bad,bad
 init=V2.parent/'review/initial';lockpath=V2.parent/'review/initial-lock.json';lock=json.loads(lockpath.read_text(encoding='utf-8'));byname={Path(r['path']).name:r for r in lock['files']}
 anchors=[OLD/'paper.md',OLD/'technical_report.md',OLD/'paper.pdf',OLD/'technical_report.pdf',OLD/'src/publication.py',OLD/'logs/resource_final.json',OLD/'logs/failures.json',OLD/'logs/invocations.json',OLD/'result.json',init/'report.md',init/'result.json',init/'figure-paper-audit.json',init/'pdf_visual/pdf-inspection.json',V2.parent/'REPAIR_FOLLOWUP.md',lockpath]
 source=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in anchors]
 for p in [init/'report.md',init/'result.json',init/'figure-paper-audit.json',init/'pdf_visual/pdf-inspection.json']:
  matched=[r for r in lock['files'] if Path(r['path']).as_posix().endswith('/'+p.relative_to(init).as_posix())]
  assert len(matched)==1 and matched[0]['sha256']==sha(p)
 for p in sorted((OLD/'figures').glob('*')):
  if p.is_file():dest=V2/'figures'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(p,dest);assert sha(p)==sha(dest)
 save(V2/'logs/source_bindings.json',{'authoritative_execution':str(OLD),'old_manifest_sha256':sha(OLD/'manifest.json'),'original_3722_payloads_match':len(manifest['files'])==3722 and not bad,'initial_review_lock_sha256':sha(lockpath),'initial_review_file_count':len(lock['files']),'anchors':source,'numerical_program_sha256':{p.name:sha(p) for p in [OLD/'src/solver.py',OLD/'src/checker.py',OLD/'src/column_milp.py',OLD/'src/reproduce.py']},'data_sha256':sha(OLD/'data/instance.json'),'selected_config_sha256':{t:sha(OLD/f'plans/{t}/selected/config.json') for t in ['Q1-S1','Q1-S2','Q1-F1','Q1-F2','Q2-N','Q2-C']},'repair_does_not_modify_numerical_program_or_parameters':True})
 save(V2/'checkpoint.json',{'phase':'source reconciled; full manuscript revision and new exporter next','original_status':'a1-a4 pass in stated scope; a5 fail; a6 partial; initial verdict unchanged','known_tool_session97122':'read-only source read, exited0','pending_child_processes':[],'pending_tool_sessions':[],'child_agents':[],'new_write_domain':str(V2),'next':'write manuscript revision and actual font/semantic proof'})
 (V2/'TODO.md').write_text('''# L3 知情修复检查点

当前：原材料/原执行/首审只读身份已核对。首审a5科学记号缺陷与a6历史限制均保留；正在修订完整中文论证与PDF导出。

- [x] 接续核对：execution-v2开始前不存在；原读会话97122已退出；未重复原求解。
- [x] 原执行3722 payload逐字节核对；首次首审报告/结果/反例对锁核对。
- [x] 完整读原论文、报告和最新语言要求；字体实测显示旧单字体缺科学字符，新微软雅黑有²/³、缺⁻，Segoe符号字体覆盖⁻。
- [ ] 全文修订：问题—模型—方法—实验—解释衔接；统一单位/术语；主要原句/改句/理由/证据记录。
- [ ] 新字体导出PDF，全部科学记号和全文PDF语义对照，逐页视觉与关键放大核查。
- [ ] 按attempt保存调用/输出与活动进程接续，实际检验不覆盖及不跨未决进程启动。
- [ ] 同一原数值/表/图/配置绑定，组合接收入口与新域复跑写域说明。
- [ ] 终态result/manifest，停止全部写入/子进程后通知root冻结。

资源：本轮追加2400秒窗口，单子进程，上限120秒/子调用，内存目标1200MB非OS强制。原3600秒窗口已耗1929.69895秒另列，不清零；旧两次并发偏离与3个CLI PID/stdout=null无法恢复。本轮模型/token/cost亦未知null。前次额度中断前只做只读准备，未生成执行-v2数值产物。

未闭合：原全球最优/完整Pareto、动态运输工程、附2官方完整批次、权威易碎规则、原日志缺口；新知情复审待root。作者自检不冒独立复审。
''',encoding='utf-8')
 print(json.dumps({'old_payloads_checked':len(manifest['files']),'review_payloads_locked':len(lock['files']),'new_write_domain':str(V2),'declared_at':now},ensure_ascii=False))
if __name__=='__main__':main()
