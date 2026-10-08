"""Update mutable entry points to the actual successor frontier, retaining history."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation as ctl

with ctl.locked(ROOT):
    state = ctl.load(ROOT)
    old = json.loads((ROOT / 'runs/R19/before/task-identities.json').read_text(encoding='utf-8'))
    assert all(ctl.identity(ctl.task_map(state)[k]) == v for k, v in old.items())
    assert ctl.task_map(state)['R19-05']['status'] == 'done'
    assert ctl.task_map(state)['R19-next']['status'] == 'done'
    assert ctl.task_map(state)['R20-01']['status'] == 'in_progress'
    header = ('R19最新现场：L1–L4诊断、来源绑定汇总和R19-next已实际done；'
        'L1/L2/L4当前六门pass，L3当前a1–a5 pass/a6 partial，原首次失败和预算保留。'
        'C12九份Markdown、包内零脚本/测试，仅修验收/建模引用；新原创小题由两个新上下文'
        '实际生产与独立首审，b1–b5在本材料范围pass，完整中文及8页最终PDF实际检查。'
        '不作通用、因果或竞赛能力认证。R20-01已真实取得并逐页核读本届官方七页报名通知/章程，'
        '详细提交/AI补充规则及实际题面数据仍待核实；前沿见runs/R20/REPORT.md和checkpoint。'
        '四层C11/旧失败/锁/预算不变，CI与论文判定分开。')
    for relative in ['START_HERE.md', 'CODEX_HANDOFF.md']:
        path = ROOT / relative
        content = path.read_text(encoding='utf-8').splitlines()
        assert content[2].startswith('R19最新现场：')
        content[2] = header
        text = '\n'.join(content) + '\n'
        if relative == 'START_HERE.md':
            text = text.replace('成品方向为Forge meta-workflow，当前候选C10是九份纯文档：',
                '成品方向为Forge meta-workflow。当前受检C12及四层实测入口：\n'
                '[C12技能入口](runs/R19/final/candidate/C12/forge-agent-flow/SKILL.md)、\n'
                '[C12纯文档包](runs/R19/final/package/Forge-C12-meta-workflow-candidate.zip)、\n'
                '[四层论文与独立诊断](runs/R19/final/PAPERS.md)、\n'
                '[来源综合及受影响行为验证](runs/R19/final/SYNTHESIS.md)、\n'
                '[当前R20前沿](runs/R20/REPORT.md)。\n\n'
                '前阶段C10九份纯文档和政策交付原件仍保留：')
        path.write_text(text, encoding='utf-8')
    path = ROOT / 'runs/R19/TODO.md'
    content = path.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(content):
        if line.startswith('- [ ] 汇总四层') or line.startswith('- [ ] 根据实测') or line.startswith('- [ ] 启动下一阶段'):
            content[i] = line.replace('- [ ]', '- [x]', 1)
    content += ['', '终态接续：来源比较/SYNTHESIS与C12新题b1–b5独立首判均已冻结，'
        'R19-05/R19-next实际done。R20计划、官方原件取得/全文逐页阅读及真实首步已保存；'
        'R20-01仍进行中，详细提交/AI条款及真实数据状态未补成通过。没有后台actor。']
    path.write_text('\n'.join(content) + '\n', encoding='utf-8')
    path = ROOT / 'runs/R19/REPORT.md'
    with path.open('a', encoding='utf-8') as stream:
        stream.write('\n## 汇总和下一阶段实际终态\n\n'
            'R19-05已实际done：四层原诊断来源绑定，C12两引用窄修订、九Markdown/零包内脚本。'
            '新题40非缓存生产/83独立接收文件冻结，新消费者四命令复跑、自有目标/约束/8参数'
            'oracle、23接收配对和4入口失败、全部8页PDF与完整中文论证支持首判b1–b5 pass。'
            '这不是原四层三角色实验复刻或C12相对C11因果提升，旧所有失败及L3 a6 partial不变。\n\n'
            'R19-next实际done：保存R20明确计划，并实际取得当前官方2026秋季报名通知/章程原件、'
            '逐页阅读七页及来源事实/未知，不是计划代替首步。当前R20-01进行中，详细提交/AI'
            '补充规则与实际题面/数据仍待核实。源cf0c4e9对应CI37821436629三作业实际success，'
            '只证明该提交的源码/工件检查；本次后续源状态另见publication观察。\n')
    path = ROOT / 'runs/R20/TODO.md'
    with path.open('a', encoding='utf-8') as stream:
        stream.write('\n实际首步已结束：当前官方一份七页合并原件（两个入口同字节）已取得/完整看图；'
            'R20-01仍进行中，继续详细提交/AI补充条款和数据状态。旧首步research工件锁定，'
            '后续审计写新域/新版本，不覆盖桥接证据。\n')
    cp_path = ROOT / 'state/checkpoint.json'
    cp = json.loads(cp_path.read_text(encoding='utf-8'))
    cp.update(current_frontier_task='R20-01', current_report='runs/R20/REPORT.md',
        current_native_pending=[], R19_status='closed_with_actual_R20_first_step',
        candidate_status='C12_scoped_forward_first_reception_pass',
        next_action='Continue R20-01 current submission/AI supplements and raw-data status; append new audit evidence, then freeze original data task for fresh workflow transfer.',
        unpublished_work=True)
    ctl.write_json(cp_path, cp)
print(json.dumps(dict(actual_frontier='R20-01', R19_closed=True, old_tasks_unchanged=len(old))))
