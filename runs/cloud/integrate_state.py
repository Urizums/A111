"""Root-owned phase integration after actual audit and smoke closure."""
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads((ROOT / path).read_text())


def save(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def task(id, title, dependencies, evidence, acceptance, status='done'):
    return dict(id=id, title=title, owner='coordinator', depends_on=dependencies,
                write_paths=['runs/', 'state/'], acceptance=acceptance,
                status=status, evidence=evidence, blocker=None,
                next_action='Preserve original evidence and review the recorded scope.' if status == 'done' else title)


def phase(id, goal, tasks):
    return dict(schema='forge-phase-todo/1', phase_id=id, goal=goal, tasks=tasks, updated_at=NOW)


def transition(id, dependencies, next_phase, todo, first, evidence):
    value = task(id, '启动下一阶段任务', dependencies, evidence,
                 ['下一阶段 TODO 已保存，首项已真实执行且证据存在'])
    value['transition'] = dict(next_phase_id=next_phase, todo_path=todo,
                               first_task_id=first, start_evidence=evidence)
    return value


assert read('runs/S01/final-review.json')['status'] == 'completed_with_historical_gaps'
assert read('runs/S03/validation.json')['status'] == 'passed_after_bounded_repair'
assert (ROOT / 'runs/cloud/VERIFICATION_REPORT.md').exists()

s01 = read('state/history/phase-todo-before-cloud.json')
for row in s01['tasks']:
    if row['id'] == 'S01-02':
        row.update(status='done', blocker=None, next_action='Audit complete; retain historical failures and blind-review limits.')
        row['evidence'] += ['runs/S01/cloud-audit/worker/audit.json', 'runs/S01/cloud-audit/worker/report.md', 'runs/S01/final-review.json']
    if row['id'] == 'S01-03':
        row.update(status='done', evidence=['runs/S01/final-review.md', 'runs/S01/final-review.json', 'runs/S01/root-csv-command.json'],
                   next_action='C1 performance remains inconclusive; preserve original partial tracks.')
s01['tasks'][-1] = transition('S01-next', ['S01-01', 'S01-02', 'S01-03'], 'S02',
                              'state/history/S02-todo.json', 'S02-01', ['runs/S02/source-inspection.json'])
s01['updated_at'] = NOW
s01['integration_note'] = 'S02/deployment preparation and S03 testing overlapped the read-only S01 audit; original event times are preserved. Phase closure is integrated now, not backdated.'
save('state/history/S01-todo.json', s01)

s02 = phase('S02', 'Version and qualify a revised recording contract without changing immutable baseline.', [
    task('S02-01', '检查原方法并冻结修订要求', [], ['runs/S02/source-inspection.json', 'runs/S02/requirements.json'], ['R01–R06 和新候选范围已冻结']),
    task('S02-02', '保存新候选并修复记录器缺陷', ['S02-01'], ['runs/S02/candidate-lock.json', 'runs/S02/repair-1.json'], ['原技能与旧失败保留，新候选有哈希及有界修复记录']),
    task('S02-03', '资格验证与控制器回归', ['S02-02'], ['runs/S02/qualification-after-fix.json', 'runs/S02/candidate-regression.json'], ['五项 recorder 检查与 368 项候选回归通过']),
    transition('S02-next', ['S02-01', 'S02-02', 'S02-03'], 'S03', 'state/history/S03-todo.json', 'S03-01', ['runs/S03/native/freeze.json', 'runs/S03/native/logs/002-setup.json'])
])
save('state/history/S02-todo.json', s02)
s03 = phase('S03', 'Preserve original smoke and one bounded conformance retest on identical inputs.', [
    task('S03-01', '冻结新烟测并建立原 bridge', [], ['runs/S03/native/freeze.json', 'runs/S03/native/logs/002-setup.json'], ['新业务输入、验收、实际设置与预算已冻结']),
    task('S03-02', '执行原始烟测并保留失败', ['S03-01'], ['runs/S03/native/create-return.json', 'runs/S03/validation-initial.json', 'runs/S03/repair-plan.json'], ['保存实际原生返回及业务验收；不把协调端采集缺口隐藏为通过']),
    task('S03-03', '有界修正与同标准复测', ['S03-02'], ['runs/S03/validation.json', 'runs/S03/repair-1/source-review.md', 'runs/S03/final-validation-command.json'], ['输入与验收不变、预算不重置，两次均保留；复测闭环并写明限制']),
    transition('S03-next', ['S03-01', 'S03-02', 'S03-03'], 'D00', 'state/phase-todo.json', 'D00-01', ['runs/cloud/install-revised.json', 'runs/cloud/smoke-revised/report.json'])
])
save('state/history/S03-todo.json', s03)
delivery = phase('D00', 'Deliver the requested cloud installation, source, reports and fork dev PR.', [
    task('D00-01', '云端 CLI 安装与搬迁验证', [], ['runs/cloud/install-revised.json', 'runs/cloud/archive-install-fixed.json', 'runs/cloud/python310-install-cli.json'], ['已连接云端环境有可运行 CLI；解压包可在不同路径安装']),
    task('D00-02', '修复复测并整理完整交付内容', ['D00-01'], ['runs/cloud/VERIFICATION_REPORT.md', 'runs/cloud/issues.json', 'runs/cloud/archive-smoke-fixed/report.json', 'runs/cloud/python310-smoke/report.json'], ['原失败及修复前后记录完整；源码和报告可打包；本地冒烟通过']),
    task('D00-03', '推送 fork dev 并向原仓库提交 PR', ['D00-01', 'D00-02'], ['runs/cloud/github-access-resolved.json', 'runs/cloud/PULL_REQUEST.md'], ['waw1w1/A111 dev 包含最终文件；PR 指向 Urizums/A111 main 并附验证说明'], 'in_progress'),
    task('D00-next', '启动下一阶段任务', ['D00-01', 'D00-02', 'D00-03'], [], ['目标交付完成后记录终态；不自动扩大为新性能实验'], 'planned')
])
save('state/phase-todo.json', delivery)
checkpoint = read('state/history/checkpoint-before-cloud.json')
checkpoint.update(updated_at=NOW, active_phase='D00', next_task_id='D00-03',
                  next_action='Publish final dev to waw1w1/A111 through the authorized GitHub API and open PR to Urizums/A111 main.',
                  remaining_audit_checks=[], lifecycle='active',
                  c1_audit='completed_with_historical_gaps; efficacy remains inconclusive',
                  historical_handoff_repair_scope='Existing functional_repairs fields describe S00 only; current candidate budgets are separate.',
                  current_delivery_repair_budgets={'C2_recorder': {'used': 1, 'limit': 2}, 'handoff_validator': {'used': 2, 'limit': 2}, 'cloud_smoke_harness': {'used': 1, 'limit': 2}, 'S03_coordinator': {'used': 1, 'limit': 2}},
                  native_calls_in_current_delivery=[{'worker':'/root/luna_forge_5630af6429d8','purpose':'fresh offline audit'}, {'worker':'/root/luna_forge_fe59e381cb4d','purpose':'original smoke; coordinator capture failed'}, {'worker':'/root/luna_forge_d847e131cd3a','purpose':'bounded conformance retest'}],
                  current_validation='S01 offline audit; C2 recorder and original controllers; S03 native source review; CLI on Python 3.10/3.12',
                  termination='No permanent background scheduler; finish requested publication, then save delivered checkpoint.')
save('state/checkpoint.json', checkpoint)

project = read('state/history/project-todo-before-cloud.json')
for row in project['todo']:
    if row['id'] == 'host_protocol_overhead_comparison':
        row['evidence'] += ['runs/S01/final-review.json', 'runs/S01/cloud-audit/worker/audit.json']
        row.update(audit_progress='A01-A05 completed with explicit missing evidence and independent-review limits; all eight original samples retained.',
                   next_action='Any later efficacy trial must be newly frozen; C1 remains partial/inconclusive and is never rerun to improve its score.')
    if row['id'] == 'host_protocol_measurement_capture_and_scope':
        row['evidence'] += ['runs/S02/candidate-lock.json', 'runs/S02/qualification-after-fix.json', 'runs/S03/validation.json']
        row.update(status='done', verified_scope='Versioned C2 candidate, qualified recorder, real native source-review loop and one explicitly retained coordinator repair. Scope restrictions are instruction-only; no complete worker host trace or provider identity proof.',
                   next_action='Use the C2 candidate for a separately frozen future study; do not infer performance or global enforcement.')
project['todo'].append(dict(id='cloud_deployment_and_delivery', owner='/root', status='in_progress',
    depends_on=['host_protocol_measurement_capture_and_scope'], write_paths=['scripts/', 'docs/', 'runs/', 'state/'],
    goal='Deploy to the attached cloud environment; smoke, repair, package all source/reports and publish fork dev PR.',
    acceptance=['Versioned CLI installation and portable archive validated', 'Issues and failure/repair evidence retained', 'Fork dev PR opened against upstream main'],
    evidence=['runs/cloud/brief.json', 'runs/cloud/VERIFICATION_REPORT.md', 'runs/cloud/issues.json'],
    blocker=None, next_action='Publish final fork dev and PR.'))
project.update(updated_at=NOW, next_action=checkpoint['next_action'],
               development_status='cloud_cli_and_C2_verified; S01_audit_closed_with_gaps; original_C1_performance_inconclusive; fork_PR_pending')
project['revisions'].append(dict(at=NOW, reason='Current user requested cloud continuation, smoke/fixes and complete fork-dev PR. Preserve all original history, failure evidence and unrelated partial/UI tracks.'))
save('state/project-todo.json', project)
print(json.dumps({'active_phase':'D00', 'next_task_id':'D00-03', 'historical_phases':['S01','S02','S03']}))
