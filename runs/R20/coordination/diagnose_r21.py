"""Actual first diagnostic; standard-library Decimal arithmetic, no fitting."""
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
base = ROOT / 'runs/R21'
out = base / 'diagnostic'
assert not out.exists()
out.mkdir()
sources = json.loads((base / 'source-inputs.json').read_text(encoding='utf-8'))
for row in sources['files']:
    b = (ROOT / row['path']).read_bytes()
    assert len(b) == row['size_bytes'] and hashlib.sha256(b).hexdigest() == row['sha256'], row['path']
def table(rel):
    with (ROOT / rel).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))
def keyed(rows, keys):
    result = {}
    for r in rows:
        k = tuple(r[x] for x in keys)
        assert k not in result, k
        result[k] = r
    return result
keys = ['service_date','store_id','item_id']
pred = keyed(table('runs/R20/execution/delivery/results/future_predictions.csv'), keys)
plan = keyed(table('runs/R20/execution/delivery/results/future_replenishment.csv'), keys)
truth = keyed(table('runs/R20/evaluation/holdout_truth.csv'), keys)
items = keyed(table('runs/R20/inputs/raw/items.csv'), ['item_id'])
calendar = keyed(table('runs/R20/inputs/raw/calendar.csv'), ['service_date'])
decision = json.loads((ROOT/'runs/R20/inputs/raw/decision.json').read_text(encoding='utf-8'))
assert pred.keys() == plan.keys() == truth.keys() and len(pred) == 1344
cells = []
for k, p in sorted(pred.items()):
    y, m, lo, hi, q = (Decimal(v) for v in [truth[k]['demand_units'],p['demand_point_units'],p['lower90_units'],p['upper90_units'],plan[k]['q_units']])
    assert all(x.is_finite() for x in [y,m,lo,hi,q]) and y >= 0 and q >= 0 and lo <= m <= hi
    assert q == q.to_integral_value() and y == y.to_integral_value()
    item = items[(k[2],)]
    assert q <= Decimal(item['daily_max_units'])
    shortage = max(y-q, Decimal(0))*Decimal(item['shortage_yuan'])
    waste = max(q-y, Decimal(0))*Decimal(item['waste_yuan'])
    horizon = (date.fromisoformat(k[0])-date.fromisoformat(decision['origin'][:10])).days
    cells.append(dict(service_date=k[0],store_id=k[1],item_id=k[2],holiday=calendar[(k[0],)]['holiday'],
        horizon_band='1-7' if horizon <= 7 else '8-14', covered=int(lo<=y<=hi), below=int(y<lo), above=int(y>hi),
        error=m-y, absolute_error=abs(m-y), shortage=shortage,waste=waste,loss=shortage+waste,width=hi-lo,
        purchase=q*Decimal(item['procurement_yuan']),q=q))
def metrics(rs):
    n = len(rs)
    def total(field): return sum((r[field] for r in rs),Decimal(0))
    return dict(rows=n,distinct_dates=len({r['service_date'] for r in rs}),covered=sum(r['covered'] for r in rs),
        below=sum(r['below'] for r in rs),above=sum(r['above'] for r in rs),coverage=float(Decimal(sum(r['covered'] for r in rs))/n),
        bias=float(total('error')/n),MAE=float(total('absolute_error')/n),mean_width=float(total('width')/n),
        loss_yuan=float(total('loss')),shortage_yuan=float(total('shortage')),waste_yuan=float(total('waste')),
        procurement_yuan=float(total('purchase')),q_units=int(total('q')))
aggregate = metrics(cells)
reference = json.loads((ROOT/'runs/R20/review/initial/holdout_independent_result.json').read_text(encoding='utf-8'))['metrics']
for ours, theirs in [('coverage','90_interval_coverage_fraction'),('bias','bias_pred_minus_truth_units_per_store_item_day'),
    ('MAE','MAE_units_per_store_item_day'),('loss_yuan','total_two_part_loss_yuan'),('mean_width','mean_interval_width_units')]:
    assert abs(aggregate[ours]-reference[theirs]) < 1e-7, (ours, aggregate[ours], reference[theirs])
groups = []
for field in ['service_date','holiday','horizon_band','store_id','item_id']:
    partitions = defaultdict(list)
    for r in cells: partitions[r[field]].append(r)
    rows = [dict(group_by=field,group=key,**metrics(rs)) for key,rs in sorted(partitions.items())]
    assert sum(r['rows'] for r in rows) == len(cells)
    if field == 'service_date':
        assert len(rows) == 14
        assert all(r['q_units'] <= decision['capacity_units_per_day'] and Decimal(str(r['procurement_yuan'])) <= Decimal(str(decision['procurement_budget_yuan_per_day'])) for r in rows)
    groups.extend(rows)
assert all((r['holiday']=='1') == (r['horizon_band']=='1-7') for r in cells), 'Re-evaluate confounding statement for changed data.'
with (out/'groups.csv').open('x', encoding='utf-8', newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(groups[0])); w.writeheader(); w.writerows(groups)
with (out/'result.json').open('x', encoding='utf-8') as f:
    json.dump(dict(aggregate=aggregate,groups=groups,reference_metrics_match=True,
        holiday_and_horizon_confounded=True,source_identity_verified=True,model_tuned=False,
        independent_reception=False,new_unseen_test=False,model=None,tokens=None,cost=None),f,ensure_ascii=False,indent=2)
holiday = [r for r in groups if r['group_by']=='holiday']
lines=['# 冻结方案的已见合成未来诊断','',
    f"原1344键全量重算：覆盖 {aggregate['covered']}/1344={aggregate['coverage']:.2%}，下端漏出{aggregate['below']}，上端漏出{aggregate['above']}；偏差{aggregate['bias']:.4f}件，MAE{aggregate['MAE']:.4f}件，两项损失{aggregate['loss_yuan']:.2f}元。采购与目标分开。与首次独立评价数值一致，未训练或改变模型。",'',
    '| 日类 | 店品日数 / 日期数 | 覆盖 | 下端 / 上端漏出 | 偏差（件） | 损失（元） |',
    '| --- | --- | --- | --- | --- | --- |']
for r in holiday:
    lines.append(f"| {'节日' if r['group']=='1' else '普通日'} | {r['rows']} / {r['distinct_dates']} | {r['coverage']:.2%} | {r['below']} / {r['above']} | {r['bias']:.4f} | {r['loss_yuan']:.2f} |")
lines+=['','全部14日、12店、8品及步长组见groups.csv；分组多次观察只是描述性线索。每日96键之间可能相关，只有14个日期，不能把1344键当独立重复。当前节日与前7步完全重合，因此差异不能归因为节日或步长因果效应。','',
    '真值已在R20首次首锁后见过；这里再次读取只定位冻结版本的误差，不能给新方案未见测试背书。不据它挑参、扩大区间或挑选最好模型。下一项应先设计新原创数据与事前公平比较，将新真值留在接收端；覆盖、宽度与业务损失共同解释，零改进也保留。','',
    'root诊断不是独立接收，也不是论文旧判定改判、真实比赛表现或获奖证明。来源逐字节绑定source-inputs.json和原锁，实际命令另有终态收据。']
(out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(actual_first_step='source-bound subgroup diagnostic completed',aggregate=aggregate,
    groups=len(groups),source_verified=True,known_truth_diagnostic_only=True,holiday_horizon_confounded=True),ensure_ascii=False))
