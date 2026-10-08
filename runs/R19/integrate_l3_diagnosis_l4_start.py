"""Integrate completed independent diagnosis and actual next-level dispatch."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
base = 'runs/R19/levels/L3/'
diagnosis = json.loads((ROOT / base / 'diagnostic-result.json').read_text(encoding='utf-8'))
review = json.loads((ROOT / base / 'review/recheck-final-1/result.json').read_text(encoding='utf-8'))
start = json.loads((ROOT / 'runs/R19/levels/L4/task-start-command.json').read_text(encoding='utf-8'))
assert start['state'] == 'finished' and start['exit_code'] == 0
assert diagnosis['latest_mandatory_pass'] is False
assert review['current_summary'] == {'pass': 5, 'fail': 0, 'partial': 1}
lead = ('R19最新现场：L1–L3完整诊断done，首次失败/partial保留。L3同一原作者354文件知情修订及同一原reviewer4271文件正式知情复审分别冻结；当前a1–a5 pass、a6 partial，科学记号及完整中文论证通过，旧三CLI原流/PID缺失和两次并发目标偏离不可补回。当前六维4achieved/2partial，不宣称全门通过；原首次a5 fail/a6 partial不变。L4已由中性输入检查和实际任务启动接续，两个新上下文分别执行自身原工作流和独立原件/方法准备，尚无论文或验收结论。四层C11不改，语言、数值、图表、实验及职责质量共同验收，不期待后续AI补齐本轮实质缺陷。源02b0a946已上传，CI实际观察见checkpoint/publication；后续4271文件复审及L4启动现场待本次发布。当前证据见runs/R19/REPORT.md、TODO.md和state/checkpoint.json，仓库CI不替代论文验收。')
for relative in ['START_HERE.md', 'CODEX_HANDOFF.md']:
    path = ROOT / relative
    paragraphs = path.read_text(encoding='utf-8').split('\n\n')
    assert paragraphs[1].startswith('R19最新现场：')
    paragraphs[1] = lead
    path.write_text('\n\n'.join(paragraphs), encoding='utf-8')
path = ROOT / 'runs/R19/TODO.md'
lines = path.read_text(encoding='utf-8').splitlines()
for i, line in enumerate(lines):
    if line.startswith('- [ ] L3：'):
        lines[i] = '- [x] L3完整诊断：9设计/3723原执行/21准备/3052首审/354知情修订/9复审准备/4271正式知情复审分别冻结。当前a1–a5 pass、a6 partial，完整中文论证、科学记号、真实六任务重跑/独立几何核查及14页PDF消费检查通过。首次4pass/1fail/1partial保持；旧原流/PID缺失和两次并发目标偏离不可修复，诊断完成不等于全门通过。'
    if line.startswith('- [ ] L4：'):
        lines[i] = '- [ ] L4：7设计冻结；L3诊断终态后实际中性身份检查/任务启动完成，新executor执行至论文、新reviewer只做独立原件方法准备。两者不读其他层结果，未交付/未验收；原构建解析失败保留。'
path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
path = ROOT / 'runs/R19/REPORT.md'
lines = path.read_text(encoding='utf-8').splitlines()
for i, line in enumerate(lines):
    if line.startswith('| L3 |'):
        lines[i] = '| L3 | 9份设计冻结 | 原执行3723/知情修订354分别冻结；11页论文/3页报告，科学记号及完整中文论证修订；数值底座/图表身份不变 | 21准备/3052首审/9复审准备/4271正式知情复审分别冻结；当前a1–a5 pass/a6 partial，六维4achieved/2partial，诊断done。首次a5 fail/a6 partial与历史不可补证缺口保留 |'
    if line.startswith('| L4 |'):
        lines[i] = '| L4 | 7份设计冻结，原解析恢复保留 | 原始输入检查及任务启动实际完成，新上下文按自身设计执行，尚无成稿 | 新独立上下文仅原件/方法准备，未接收生产、未判定 |'
lines += ['', 'L3正式知情复审终态：同一reviewer在review/recheck-final-1交付4271文件，9文件recheck-1仅是事前方法准备，不算另一轮实质验收。真实消费者六任务重求及自有源绑定checker核2380553货物对，原数值主解保持；82表行/五组图身份不变，原168比较/348参数独立初审证据按同字节引用，没有伪称全部本轮重跑。完整中文问题—选模—实验—验证—解释链独立阅读通过；两份最终PDF全部14页、31科学局部及750顺序显示单元独立检查，真实重新导出后文本/像素一致。当前a1–a5 pass/a6 partial，六维4achieved/2partial。原三CLI原流/PID不可恢复、两次原并发目标偏离、真正监视器崩溃退出接续分支未实验及整体峰值内存未知均保留。诊断已实际关闭，最新mandatory_pass=false；不平均成全通过，不追认首次科学表达失败。', '', '随后L4实际启动：先前中性输入身份检查无计算答案，L3关闭后task-start-command.json实际exit0。/root/r19_l4_executor与/root/r19_l4_reviewer用全新无历史上下文分别接手自身C11/原L4输入/冻结设计/官方原件及外部事前验收方法；生产者不收外部评分/先前诊断。当前仍是执行及准备，不是论文通过。语言与整体科学交付质量沿原冻结a5及六维评价，四层C11保持原字节，源头改进待四层完整诊断。']
path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
observation = {'level': 3, 'provenance': 'Root read same-reviewer frozen result/report; no regrading.', 'diagnostic': base + 'diagnostic-result.json', 'initial_review': base + 'review/initial/result.json', 'latest_review': base + 'review/recheck-final-1/result.json', 'initial_verdict': diagnosis['initial_scientific_verdict'], 'latest_verdict': diagnosis['latest_scientific_verdict'], 'initial_quality': diagnosis['initial_quality'], 'latest_quality': diagnosis['latest_quality'], 'latest_mandatory_pass': False, 'language': 'Full Chinese argument and final PDF scientific meaning independently accepted in informed revision. No sentence/page quotas or deferred later AI repair.', 'history': 'Missing original CLI streams/PIDs and two original concurrency target deviations remain partial; new calls do not repair history.', 'scope': 'One conditional original spring contest instance; no causal level ranking, prize claim or October big-data generalization.'}
path = ROOT / 'runs/R19/observations/L3.json'
assert not path.exists()
path.write_text(json.dumps(observation, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (ROOT / 'runs/R19/observations/synthesis-in-progress.md').open('a', encoding='utf-8') as stream:
    stream.write('\nL3正式独立知情复审现已终态并冻结4271文件，诊断done：a1–a5 pass/a6 partial，六维4achieved/2partial。上述中途“尚待独立判定”的状态已由真实全文阅读/科学局部/14页重导出和数值消费者复跑取代，首次a5 fail不变。L4原始工作流已实际启动两个新上下文，未向其发送本页或其他层诊断。不能从修订成功推断C11第一次输出无缺陷；语言改进应在实质交付内检查科学含义和读者理解，源头窄范围澄清仍待四层结果。\n')
with (ROOT / 'runs/R19/coordinator-attempts.md').open('a', encoding='utf-8') as stream:
    stream.write('\n- L4 reviewer初次物流提示误写runs/R19/raw-lock.json，实际文件为runs/R19/inputs/raw-lock.json。审查者真实报告不存在后root明确授权正确原锁路径，保留错误及恢复，不增加答案/评分或扩大其他层读域。这是协调者路径错误，不归入作者科学缺陷或旧预算。\n')
print(json.dumps({'L3_diagnostic': 'done_with_historical_a6_partial', 'L4_actual_started': True, 'C11_unchanged': True}))
