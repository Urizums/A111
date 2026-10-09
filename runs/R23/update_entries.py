"""Update mutable entries only after actual bounded closure, retaining old history."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=json.loads((ROOT/'state/continuation.json').read_text(encoding='utf-8'));tasks={t['id']:t for t in s['tasks']}
assert all(tasks[k]['status']=='done' for k in ['R23-01','R23-02','R23-03','R23-04']) and tasks['R23-next']['status']=='cancelled'
paragraph='当前R23定界支线已完成，R23-next按目标完成取消、没有虚构R24启动。新上下文自主设计首次漏掉每方法未来交付；首判j1失败、Root严格j4未验证及全部原件保留。原任务一次知情重启后，另版契约与窄字段接收包经新接收者j1–j4范围内通过，192行单日点预测独立复算吻合；未产出/接收该工作流完整42日区间、备货或新论文。C13仍九份纯Markdown、零产品脚本/测试，源条款决定及证据见R23综合。不是Level1–4重跑、skill因果增益或获奖证明；原项目/失败/预算、L3 partial、前端宿主拒绝、正式十月规则未知保持。'
for name in ['START_HERE.md','CODEX_HANDOFF.md']:
    p=ROOT/name;parts=p.read_text(encoding='utf-8').split('\n\n',2);assert parts[1].startswith('当前前沿 R23-02')
    parts[1]=paragraph;p.write_text('\n\n'.join(parts),encoding='utf-8')
p=ROOT/'runs/R23/REPORT.md';text=p.read_text(encoding='utf-8');old='接下来完成R23-04来源综合及定界支线关闭。';assert old in text;text=text.replace(old,'R23-04来源综合已完成，R23-next按定界目标完成取消；没有伪造R24实际启动。');p.write_text(text,encoding='utf-8')
p=ROOT/'runs/R23/TODO.md';p.write_text('''# R23 TODO

- [x] R23-01 中性输入冻结与实际原CSV审计。
- [x] R23-02 新上下文实际工作流创建；原44份设计不追认完整首次通过。
- [x] R23-03 消费一日96键×两方法；首次failed保持，一次知情重启后新独立j1–j4范围内pass。
- [x] R23-04 原件来源综合，确认本轮违反已有义务，保留C13九Markdown，不造无依据升级。
- [ ] R23-next 启动下一阶段任务：**cancelled**，本定界目标已完成，无新实质目标则不制造重复阶段；未标done/未创建R24。

没有当前actor或后台调度。32份当前独立接收、首次30份失败判定、55份原消费、16份知情契约修订与所有原过程已锁；原任务R23-03 repairs_used=1/limit=null，局部命令与实现错误单列保留。未覆盖完整42日区间/优化/最终方法注册表/敏感性/论文与可靠性。

总项目及旧R08/R16/R19/前端/赛事规则分支保持原状态，75份非本轮任务身份保护不改。入口和checkpoint保存定界结束，不承诺后台运行，不把旧CI当新发布CI。
''',encoding='utf-8')
print(json.dumps(dict(entries=2,R23_todo_and_report_current=True,bounded_probe_closed=True)))
