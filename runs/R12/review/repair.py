"""Preserved corrective round for the same protocol review, never an old business rerun."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))


def save(name,value):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def revise():
    source=(ROOT/'runs/R12/protocol/evaluation-protocol.md').read_text(encoding='utf-8')
    overrun='若事后发现实际已用次数超过上限，保留真实总数（例如3/2），不得截断、清零或改分母。立即停止该案例的后续纠正，保存已产生的草稿和回执，在同一台账列出已计数尝试、发现越界的位置及可确认的经过；不能确定的顺序明确未知。不要为了补齐台账继续修复或重跑耗尽案例。\n\n'
    provenance='对影响判定的陈述，区分直接观察、原因推断和未来预期。直接观察给出稳定来源路径/身份与实际检查；推断说明依据、假设和仍可能成立的其他解释；未来效果写明尚需什么实际验证。不要把“可能减少记录负担”写成已测得改进。标注可嵌入原记录，不要求新的文档或框架。\n\n'
    assert source.count('## 判定与交接\n\n')==1 and source.count('采用一份紧凑记录即可；')==1
    updated=source.replace('## 判定与交接\n\n',overrun+'## 判定与交接\n\n').replace('采用一份紧凑记录即可；',provenance+'采用一份紧凑记录即可；')
    p=ROOT/'runs/R12/protocol/v2/evaluation-protocol.md';p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(updated)
    request=json.loads((ROOT/'runs/R12/review/request.json').read_text(encoding='utf-8'))
    request['allowed_reads']=[s.replace('runs/R12/review/request.json','runs/R12/review/v2/request.json')
        .replace('runs/R12/review/frozen-lock.json','runs/R12/review/v2/frozen-lock.json')
        .replace('runs/R12/protocol/evaluation-protocol.md','runs/R12/protocol/v2/evaluation-protocol.md') for s in request['allowed_reads']]
    request['output_directory']='runs/R12/review/v2/independent/'
    request['request']=request['request'].replace('runs/R12/review/independent/','runs/R12/review/v2/independent/')
    request['cumulative_case_corrections_used']=2
    save('runs/R12/review/v2/request.json',request)
    files=[]
    for name in request['allowed_reads']:
        if name=='runs/R12/review/v2/frozen-lock.json':continue
        raw=(ROOT/name).read_bytes();files.append(dict(path=name,size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    save('runs/R12/review/v2/frozen-lock.json',dict(schema='forge-design-review-lock/1',review_task='R12-02',files=files,
         repair_limit=2,cumulative_repairs_used=2,previous_lock='runs/R12/review/frozen-lock.json'))
    failure=dict(round=1,kind='failed_corrective_patch_construction',error='apply_patch verification failed: Failed to find expected lines in runs/R13/manage.py: R13_current_budget=dict(author_used=0,limit=2),',files_changed=False,child_process_started=False)
    save('runs/R12/review/repair-ledger.json',dict(task_id='R12-02',cumulative_used=2,limit=2,attempts=[failure,
         dict(round=2,kind='corrective_recovery_and_protocol_source_revision',previous='runs/R12/protocol/evaluation-protocol.md',current='runs/R12/protocol/v2/evaluation-protocol.md',
              changes=['Explicit claim provenance','Explicit actual above-limit total and stop/preserve/report'],requirements_changed=False,primary_records_changed=False)],
         limits='A failed corrective construction counts even without mutations; no further correction allowed after this round'))
    p=ROOT/'runs/R13/manage.py';old=p.read_text(encoding='utf-8')
    assert old.count("sys.path.insert(0,str(ROOT/'scripts')))")==1
    new=old.replace("sys.path.insert(0,str(ROOT/'scripts')))","sys.path.insert(0,str(ROOT/'scripts'))")
    new=new.replace('runs/R12/protocol/evaluation-protocol.md','runs/R12/protocol/v2/evaluation-protocol.md')
    new=new.replace('runs/R12/R12-02-result.json','runs/R12/R12-02-result-v2.json')
    new=new.replace('runs/R12/review/independent/result.json','runs/R12/review/v2/independent/result.json')
    new=new.replace('repairs_used=0,repair_limit=2','repairs_used=2,repair_limit=2')
    new=new.replace('metrics=dict(repairs_used=0,tokens=None,cost=None)','metrics=dict(repairs_used=task[\'repairs_used\'],tokens=None,cost=None)')
    new=new.replace('R12_current_budget=dict(author_used=0,reviewer_used=0,limit=2','R12_current_budget=dict(cumulative_case_used=2,reviewer_internal_used=0,limit=2')
    new=new.replace('R13_current_budget=dict(author_used=0,limit=2)','R13_current_budget=dict(author_used=task[\'repairs_used\'],limit=2)')
    compile(new,str(p),'exec')
    p.write_text(new,encoding='utf-8',newline='\n')
    save('runs/R13/authoring/repair-ledger.json',dict(task_id='R13-01',cumulative_used=2,limit=2,
        attempts=[failure,dict(round=2,kind='source_correction_and_recovery',detail='Remove observed extra closing parenthesis before helper execution; keep before-source, no old business execution')]))
    print(json.dumps(dict(revised='protocol/v2',cumulative_corrections=2,limit=2,criteria_and_original_records_unchanged=True)))


def start():
    import continuation as ctl
    with ctl.locked(ROOT):
        state=ctl.load(ROOT);task=ctl.task_map(state)['R12-02']
        assert task['status']=='failed' and task['repairs_used']==0
        task['inputs']=['runs/R12/review/v2/request.json','runs/R12/review/v2/frozen-lock.json','runs/R12/protocol/v2/evaluation-protocol.md']
        task['repairs_used']=1
        attempt=ctl.begin(state,ROOT,task['id'],'runs/R12/review/v2/revise-command.json')
        assert task['repairs_used']==2
        state['execution'].update(native_pending=[dict(worker='/root/r12_protocol_review',state='same_actor_revision_review_pending')],
             current_native_pending=[dict(worker='/root/r12_protocol_review',state='same_actor_revision_review_pending')])
        state['events'].append(dict(at=ctl.stamp(),command='same_protocol_correction_start',result=dict(attempt=attempt,repairs_used=2,ledger='runs/R12/review/repair-ledger.json')))
        ctl.write_json(ROOT/'state/continuation.json',state)
        p=ROOT/'state/phases/R12.json';ctl.write_json(p,ctl.phase_view(json.loads(p.read_text()),state));ctl.synchronize(ROOT,state)
    print(json.dumps(dict(task='R12-02',status='in_progress',repairs_used=2)))


def finish():
    import continuation as ctl
    directory='runs/R12/review/v2/independent/'
    report=json.loads((ROOT/(directory+'result.json')).read_text(encoding='utf-8'))
    adoption=json.loads((ROOT/'runs/R12/review/adoption-review-v2.json').read_text(encoding='utf-8'))
    save('runs/R12/review/native-terminal-v2.json',dict(worker='/root/r12_protocol_review',same_actor=True,state='final_return_received',result=directory+'result.json',authenticated_exact_model=None,tokens=None,cost=None))
    with ctl.locked(ROOT):
        state=ctl.load(ROOT);task=ctl.task_map(state)['R12-02'];attempt=task['attempts'][-1]
        assert task['repairs_used']==2
        paths=[directory+'result.json',directory+'review.md','runs/R12/review/adoption-review-v2.json','runs/R12/review/repair-ledger.json','runs/R12/review/native-terminal-v2.json']
        result=dict(task_id=task['id'],attempt_id=attempt['id'],requirements_hash=attempt['requirements_hash'],
            criteria=[dict(id='a1',status='pass' if adoption['adoptable'] else 'fail',evidence=paths),dict(id='a2',status='pass',evidence=paths+['runs/R12/PLAN.md'])],
            effect=dict(target='Same independent protocol design review after bounded corrections',hypothesis='The narrow documentation changes satisfy the original review criteria',
             baseline='Original protocol, original failed review and unchanged primary records',conditions='Same requested-Luna actor, unchanged review requirements, two cumulative source/orchestration correction attempts',
             observations=adoption['observation'],limits='Design review only; no historical business, C8 behavior or measured improvement acceptance',
             metrics=dict(repairs_used=2,repair_limit=2,reviewer_internal_repairs=adoption['reviewer_internal_repairs'],tokens=None,cost=None)),
            next_action='R13-01 actual adoption if passed; otherwise stop exhausted protocol review')
        save('runs/R12/R12-02-result-v2.json',result);outcome=ctl.finish(state,ROOT,task['id'],'runs/R12/R12-02-result-v2.json')
        state['execution'].update(native_pending=[],current_native_pending=[],session_state='R12_same_actor_review_terminal_received')
        state['execution'].setdefault('completed_native_R12',[]).append(dict(worker='/root/r12_protocol_review',evidence='runs/R12/review/native-terminal-v2.json'))
        state['events'].append(dict(at=ctl.stamp(),command='finish',result=outcome));ctl.write_json(ROOT/'state/continuation.json',state)
        p=ROOT/'state/phases/R12.json';phase=ctl.phase_view(json.loads(p.read_text()),state)
        if outcome['status']=='blocked':phase['tasks'][-1].update(status='blocked',blocker='Protocol review exhausted its two-correction budget',evidence=['runs/R12/R12-02-result-v2.json'],next_action='Preserve failure, no substitute reviewer')
        ctl.write_json(p,phase);ctl.synchronize(ROOT,state)
    print(json.dumps(outcome))


if __name__=='__main__':
    dict(revise=revise,start=start,finish=finish)[sys.argv[1]]()
