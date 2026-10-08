"""Root integration of closed diagnostics and frozen forward inputs; no grading."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl

header = ('R19最新现场：L1–L4完整诊断已实际done；L1/L2/L4当前六门pass，'
          'L3当前a1–a5 pass、a6 partial，旧调用/并发缺口保留。'
          '首次失败、partial和预算均不追认或重置。R19-05已实际启动：四层证据汇总及'
          'C12新候选（九份Markdown、无包内脚本/测试），仅修订验收与建模两份引用。'
          '原创小题的工作流/程序/完整中文论文及8页PDF已冻结，'
          '新的独立消费者正在正式接收，尚无C12行为通过结论。'
          '四层原C11字节不变；下一阶段R20尚未启动。'
          '发布及CI实际状态以checkpoint/publication观察为准，CI不代替论文验收。')

with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    old = json.loads((ROOT / 'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
    assert all(ctl.task_map(state)[f'R19-L{k}']['status'] == 'done' for k in range(1, 5))
    assert (ROOT / 'runs/R19/final/forward/production-lock.json').exists()
    for relative in ['START_HERE.md', 'CODEX_HANDOFF.md']:
        path = ROOT / relative
        content = path.read_text(encoding='utf-8').splitlines()
        assert content[2].startswith('R19最新现场：')
        content[2] = header
        path.write_text('\n'.join(content) + '\n', encoding='utf-8')
    path = ROOT / 'runs/R19/TODO.md'
    content = path.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(content):
        if line.startswith('- [ ] L4：'):
            content[i] = ('- [x] L4完整诊断：原417生产/164首审/4知情方法/840知情修订/'
                          '854知情复审分别冻结；首次4pass/1fail/1partial保留。'
                          '当前六门pass、六维在报告有限范围achieved；真实ZIP原件重跑、'
                          '自有数值/来源/几何控制及全部12+3页论文检查支持该判定。'
                          '旧丢失坐标/遥测、启发式和全局最优未知仍保留。')
    if not any('C12新任务验证正在进行' in line for line in content):
        content += ['', 'C12新任务验证正在进行：四层来源绑定比较在final/comparison.json，'
                    '源头分析在final/SYNTHESIS.md。C12只有两份引用修改；独立方法准备'
                    '22个控制不等于生产验收。须等冻结生产、独立重跑及完整中文/PDF审查，'
                    '再关闭R19-05并启动下一阶段。']
    path.write_text('\n'.join(content) + '\n', encoding='utf-8')
    path = ROOT / 'runs/R19/REPORT.md'
    content = path.read_text(encoding='utf-8')
    marker = '## 四层终态及C12实际前沿'
    if marker not in content:
        content += ('\n' + marker + '\n\nL4的854文件知情复审已终态冻结：当前六门pass、'
                    '六维在报告限定范围achieved。独立ZIP原件主复跑136.8259859秒，'
                    '96接收CLI控制加4正式接收路径、21坐标组和8静力代表车、39主表行及'
                    '64附件2几何值、12+3页PDF及完整中文论证均实际检查。原首次NaN误接收'
                    '失败及缺失遥测/失败坐标保持。四层诊断完成，L3当前a6仍partial；'
                    '不将四层平均成全部通过。\n\n'
                    'R19-05已实际启动，四层诊断字节绑定比较在final/comparison.json。'
                    '新C12九份Markdown、包内零脚本，仅改evaluation/modeling：被选smoke'
                    '实际激活条件、接收来源/有限值绑定、科学表达及最终消费格式一致性。'
                    'C11及所有旧判定冻结不动。新原创小题由新生产上下文实际执行，另一个'
                    '新独立上下文只完成事前方法准备（22控制）；当前无C12行为终态。'
                    '该两上下文小切片不等于原四层三角色实验或十月大数据表现。\n')
        path.write_text(content, encoding='utf-8')
    index_path = ROOT / 'state/revision-locks.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    sources = ['runs/R19/final/candidate/C12-lock.json',
               'runs/R19/final/package/package-lock.json',
               'runs/R19/final/forward/inputs/input-lock.json']
    acceptance = ROOT / 'runs/R19/final/forward/acceptance.json'
    evaluation_lock = ROOT / 'runs/R19/final/forward/evaluation-lock.json'
    if not evaluation_lock.exists():
        data = acceptance.read_bytes()
        ctl.write_json(evaluation_lock, dict(schema='forge-revision-lock/1',
            revision='C12-forward-original-external-assertions', frozen_at=ctl.stamp(),
            original_assertions_frozen_at=json.loads(data)['frozen_at'],
            claim='Catalog registration after dispatch; assertions authored/frozen before dispatch, unchanged.',
            files=[dict(path=acceptance.relative_to(ROOT).as_posix(), size_bytes=len(data),
                        sha256=hashlib.sha256(data).hexdigest())]))
    sources.append(evaluation_lock.relative_to(ROOT).as_posix())
    for relative in sources:
        lock = json.loads((ROOT / relative).read_text(encoding='utf-8'))
        for entry in lock['files']:
            data = (ROOT / entry['path']).read_bytes()
            assert len(data) == entry['size_bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256']
        if relative not in index['locks']:
            index['locks'].append(relative)
    ctl.write_json(index_path, index)
    state['execution'].update(current_candidate='runs/R19/final/candidate/C12-lock.json',
        frozen_four_level_candidate='runs/R19/candidate/C11-lock.json',
        candidate_status='targeted_forward_independent_review_in_progress')
    ctl.write_json(ROOT / 'state/continuation.json', state)
    ctl.synchronize(ROOT, state)
    cp_path = ROOT / 'state/checkpoint.json'
    cp = json.loads(cp_path.read_text(encoding='utf-8'))
    cp.update(current_frontier_task='R19-05', current_candidate='runs/R19/final/candidate/C12-lock.json',
        frozen_four_level_candidate='runs/R19/candidate/C11-lock.json',
        R19_status='four_diagnostics_done_C12_actual_independent_review_in_progress',
        next_action='Receive actual C12 forward review; preserve first verdict, then close evidence synthesis and start justified R20 with a real first step.',
        current_native_pending=state['execution']['current_native_pending'], unpublished_work=True)
    ctl.write_json(cp_path, cp)
print(json.dumps(dict(old_tasks_unchanged=len(old), registered_frozen_sources=sources,
                      four_diagnostics_closed=True, forward_accepted=False)))
