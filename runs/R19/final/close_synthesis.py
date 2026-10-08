"""Bind actual four diagnoses and terminal forward reception; no historical regrade."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl

def read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))

def row(relative):
    data = (ROOT / relative).read_bytes()
    return dict(path=relative, size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

review = read('runs/R19/final/forward/review/result.json')
assert review['state'] == 'complete_stopped' and review['first_verdict']
assert {r['id'] for r in review['mandatory']} == {f'b{i}' for i in range(1, 6)}
assert all(r['verdict'] == 'pass' and r['evidence'] and r['limits'] for r in review['mandatory'])
assert review['production_modified'] is False
comparison = read('runs/R19/final/comparison.json')
assert [r['level'] for r in comparison['trials']] == [1, 2, 3, 4]
for trial in comparison['trials']:
    assert row(trial['diagnostic_path'])['sha256'] == trial['sha256']
locks = ['runs/R19/candidate/C11-lock.json', 'runs/R19/final/candidate/C12-lock.json',
         'runs/R19/final/package/package-lock.json', 'runs/R19/final/forward/inputs/input-lock.json',
         'runs/R19/final/forward/evaluation-lock.json',
         'runs/R19/final/forward/review-preparation-lock.json',
         'runs/R19/final/forward/production-lock.json',
         'runs/R19/final/forward/production-ephemera-lock.json',
         'runs/R19/final/forward/review-lock.json']
for relative in locks:
    for entry in read(relative)['files']:
        assert row(entry['path']) == entry, entry['path']
with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    old = read('runs/R19/before/task-identities.json')
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
    assert not state['execution']['current_native_pending']
    task = ctl.task_map(state)['R19-05']
    assert task['status'] == 'in_progress'
    path = ROOT / 'runs/R19/final/SYNTHESIS.md'
    content = path.read_text(encoding='utf-8')
    content = content.replace('（前瞻验证进行中）', '（前瞻接收已完成）')
    content = content.replace('独立结果尚未产生，不能宣称C12已行为通过。',
        '独立首判已终态，b1–b5在这份原始材料和实际检查范围内通过；不能据此作通用或竞赛能力认证。')
    content += ('\n## C12实际前瞻终态\n\n'
        '两个新上下文完成设计/生产与独立消费，没有生产修复。40个非缓存生产文件及'
        '83个独立接收文件分别冻结；作者清单中的3运行缓存原字节另行归档，不作为源依赖。'
        '独立从原raw按交接执行四命令，自有逻辑核身份、有限值、几何、支撑与递归外载、'
        '载重和原字典序目标；8个参数结果与自有四件oracle一致；23实际接收配对和4实际'
        '入口失败保存。完整中文源稿和全部8页重新渲染PDF实际阅读，关键科学表格与131'
        '有效源文行核对一致。首判b1–b5均pass，报告逐项给出原件条款、证据及限制。\n\n'
        '这支持将C12作为下一阶段受检候选，保持九份纯文档；不证明其优于C11、未来全部'
        'smoke不会减弱、通用核验器无缺陷或十月表现。四层C11首次失败和当前L3的a6 partial'
        '不变，未知旧物证不得补造。下一阶段应核实十月官方赛事/数据并开展新的数据语义任务。\n')
    path.write_text(content, encoding='utf-8')
    path = ROOT / 'runs/R19/final/PAPERS.md'
    content = path.read_text(encoding='utf-8').replace(
        'C12新题生产已冻结，独立消费者正在正式接收，尚无终态行为判定。',
        'C12新题[独立首判](forward/review/report.md)已终态，b1–b5在本材料范围内通过；'
        '其[8页论文](forward/production/paper.pdf)是新的受影响行为小切片，不能充作四层结果。')
    path.write_text(content, encoding='utf-8')
    result = dict(task_id='R19-05', attempt_id=task['attempts'][-1]['id'],
        requirements_hash=task['attempts'][-1]['requirements_hash'],
        criteria=[dict(id='t1', status='pass', evidence=[
            'runs/R19/final/comparison.json', 'runs/R19/final/SYNTHESIS.md', *locks,
            'runs/R19/final/forward/review/report.md', 'runs/R19/final/forward/review/result.json'])],
        source_revision='C12', changed_references=['evaluation.md', 'modeling.md'],
        historical_verdicts_regraded=False, historical_budgets_reset=False,
        forward_verdict=review['mandatory'],
        effect=dict(target='Sparse-request meta-workflow source design and actual affected behavior',
            hypothesis='Explicit smoke activation, source/value binding and final scientific expression support the affected handoff; bounded forward evidence only.',
            baseline='Four actual C11 level diagnoses, first failures and same-actor informed revisions all preserved.',
            conditions='Four original level trials on one official spring task; separate C12 original four-item task with two fresh contexts, not a matched causal comparison.',
            observations=dict(four_diagnostics_closed=True, latest_L3_a6='partial',
                candidate_markdown_files=9, bundled_scripts=0, changed_references=2,
                forward_first_verdict='b1_b5_pass', actual_forward_checks=review['actual_checks']),
            limits='No original/global/generalized algorithm, level/candidate causal ranking, official score/prize, industrial safety or October readiness certification; retain all reviewer limits.',
            metrics=dict(original_level_trials=4, new_targeted_trials=1,
                         tokens=None, cost=None)),
        next_action='R19-next: justified October data-workflow plan and actual primary-source first step.')
    assert not (ROOT / 'runs/R19/final/result.json').exists()
    ctl.write_json(ROOT / 'runs/R19/final/result.json', result)
    lock_path = 'runs/R19/final/synthesis-lock.json'
    ctl.write_json(ROOT / lock_path, dict(schema='forge-revision-lock/1', revision='R19-final-evidence-synthesis',
        frozen_at=ctl.stamp(), files=[row(p) for p in [
            'runs/R19/final/comparison.json', 'runs/R19/final/SYNTHESIS.md',
            'runs/R19/final/PAPERS.md', 'runs/R19/final/result.json']],
        claim='Actual source-bound synthesis and scoped first forward reception; historical verdicts unchanged.'))
    index = read('state/revision-locks.json')
    index['locks'].append(lock_path)
    ctl.write_json(ROOT / 'state/revision-locks.json', index)
print(json.dumps(dict(actual_forward_first_pass=True, four_diagnostics_bound=True,
                      candidate_documents=9, old_tasks_unchanged=len(old))))
