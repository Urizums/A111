"""Freeze a new-context original-goal pilot. Does not invoke any native worker."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];kind=sys.argv[1];base=ROOT/'runs/R06/handoff';run=base/kind;run.mkdir();worker=run/'worker';worker.mkdir()
C=ROOT/'runs/R06/candidate/C5/forge-agent-flow/scripts';material=base/'materials'/(kind+'.json');original=json.loads(material.read_text())
def save(path,obj):
 with path.open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def call(label,args):
 r=subprocess.run([sys.executable,ROOT/'scripts/record_command.py','--out',run/(label+'.json'),'--',sys.executable,*map(str,args)],cwd=ROOT,capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 return json.loads(r.stdout)
goals=original['goal'];plan={'schema_version':'forge-project-plan/1','id':'pilot_'+kind,'goal':goals,'deliverable_kind':'scoped_task' if kind=='simple' else 'software_system','requirements':[{'id':'req_source','text':goals,'origin':'explicit','basis':str(material),'acceptance_ids':['a_original']}],'acceptance':[{'id':'a_original','assertion':'Original goal/material satisfied with actual output/runtime evidence, correct path selection and no budget reset','required':True,'level':'review'}],'tasks':[{'id':'work','title':goals,'depends_on':[],'owner':'gpt-6-luna','write_paths':['worker/'],'acceptance_ids':['a_original']}]}
inputs=[material,ROOT/'runs/R06/candidate/C5-lock.json']
if kind=='complex':inputs += [ROOT/'runs/R06/approval/approval.py',ROOT/'runs/R06/approval/contract.json',ROOT/'runs/R06/approval/policy.json',base/'materials/manual-review-rules.json']
prompt='原始目标：'+goals+'\n原始材料：'+str(material)+'\n先读取固定版本技能 '+str(C.parent/'SKILL.md')+'。版本锁 '+str(ROOT/'runs/R06/candidate/C5-lock.json')+'。自主选择与目标匹配的路径；只读取该技能公开文件、原材料，以及材料明确指向的本地应用/契约/规则，不读 Root 测试、报告、答案、共享状态或其他 worker。\n你负责独立执行与验证，不改核心、skill 或目标应用。只写 '+str(worker)+'。除本地命令进程外没有外部副作用授权。每项冻结验证最多两次修正；使用 C5 的实际记录机制，并保留失败，不重置或换样本。简单材料直接交付；复杂任务可按实际必要性最多委派两个互不重叠、只写你目录子目录的验证子任务，给原要求，不能给答案。你的最终报告保留原始命令/结果、写域、分工、介入、失败/修正、接续首步和实际局限，未知 tokens/cost/model-active-time 为 null。\n返回 '+str(worker/'reply.json')+'，使用新请求 '+str(run/'job/request.json')+' 的身份与产物哈希；保留分开的不完整 draft 与实际 preflight。没有网络授权。'
work=dict(prompt=prompt,inputs={'material':str(material),'candidate_lock':str(ROOT/'runs/R06/candidate/C5-lock.json')},input_files=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs],write_paths=[str(worker)],reply_path=str(worker/'reply.json'))
save(run/'plan.json',plan);save(run/'work.json',work)
call('init-command',[C/'projectctl.py','init',run/'plan.json','--state',run/'state.json'])
call('prepare-command',[C/'hostbridge.py','prepare','--kind','project','--state',run/'state.json','--task','work','--work',run/'work.json','--job',run/'job','--parent','/root'])
# Exact state/input/criteria bytes before issue/native dispatch, including every bound input.
names=[str(p.relative_to(ROOT)) for p in inputs]+[str((run/f).relative_to(ROOT)) for f in ['plan.json','work.json','state.json','job/request.json','job/control.json','job/ledger.json']]
args=[C/'snapshot.py','capture','--root',ROOT,'--out',run/'pre-dispatch']
for n in names:args+=['--path',n]
call('snapshot-command',args);call('snapshot-verify',[C/'snapshot.py','verify',run/'pre-dispatch'])
issue=call('issue-command',[C/'hostbridge.py','issue','--job',run/'job']);save(run/'issue.json',issue);print(json.dumps(issue['spawn_arguments'],ensure_ascii=False,indent=2))
