"""Create a new report renderer; compute displayed money from CSV decimal text."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R22'
original=BASE/'execution/correction-v2/source/build_report_v2.py'
target=BASE/'execution/correction-v3/source/build_report_v3.py'
assert not target.exists()
s=original.read_text(encoding='utf-8')
s=s.replace('import json,hashlib,html','import json,hashlib,html,csv')
assert s.count("out=ex/'correction-v2/report'")==1
s=s.replace("out=ex/'correction-v2/report'","out=ex/'correction-v3/report'")
needle="def fmt(v,n=3):"
assert s.count(needle)==1
helper='''def decimal_rows(name):
    with (science/'results'/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
money_groups={name:decimal_rows(name) for name in ['group_store.csv','group_item.csv','paired_daily.csv']}
def money_difference(name,origin,dimension,group):
    rows=[r for r in money_groups[name] if r['origin']==origin and r[dimension]==group]
    values={r['method_id']:Decimal(r['loss_per_day']) for r in rows}
    assert set(values)==set(methods)
    return values['weekly_mean56']-values['shared_ridge10']
def paired_money(origin):
    values=[Decimal(r['loss_W_minus_R']) for r in money_groups['paired_daily.csv'] if r['origin']==origin]
    assert len(values)==42
    return sum(values,Decimal(0))/Decimal(len(values)),min(values),max(values)
'''
s=s.replace(needle,helper+needle)
old='fmt(r.weekly_mean56-r.shared_ridge10,2)'
assert s.count(old)==2
s=s.replace(old,"fmt(money_difference('group_store.csv',o,'store_id',s),2)",1)
s=s.replace(old,"fmt(money_difference('group_item.csv',o,'item_id',s),2)",1)
old="z=pair[pair.origin==o];p(f'"
assert s.count(old)==1
s=s.replace(old,"z=pair[pair.origin==o];money_mean,money_min,money_max=paired_money(o);p(f'")
for before,after in [('z.loss_W_minus_R.mean():.2f','fmt(money_mean,2)'),('z.loss_W_minus_R.min():.2f','fmt(money_min,2)'),('z.loss_W_minus_R.max():.2f','fmt(money_max,2)')]:
    assert s.count('{'+before+'}')==1
    s=s.replace('{'+before+'}','{'+after+'}')
s=s.replace('展示表从公开CSV值按Decimal ROUND_HALF_UP统一舍入；','展示表从公开CSV值按Decimal ROUND_HALF_UP统一舍入；展示金额差值及配对日均值、极值先从CSV十进制文本运算，再统一舍入；')
needle="heading('12 解释、局限与可支持结论',2)"
assert s.count(needle)==1
s=s.replace(needle,"p('文档修正阶段保留首稿独立h6失败和v2作者自检失败。v2仅修显示舍入，派生差值仍先作浮点相减，因此本版改为CSV十进制文本运算。作者等待修正时调用代理清单，工具意外返回其他已完成代理的摘要，包括非本修正文档所需的未来结果与首判摘要；作者声明未据此改变科学源或结论，冻结字节仍核对一致。此暴露不追溯污染此前已冻结的科学生产，但文档修正与复审均为知情过程，不宣称全程未见其他摘要。')\n"+needle)
# Clarify original-production scope; correction waiting exposure is reported separately above.
s=s.replace('本轮未读取R21/evaluation、旧论文/报告','原首次科学生产未读取R21/evaluation、旧论文/报告')
target.parent.mkdir(parents=True,exist_ok=True)
with target.open('x',encoding='utf-8',newline='') as f:f.write(s)
meta=dict(original_renderer=dict(path=original.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(original.read_bytes()).hexdigest()),new_renderer=dict(path=target.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(target.read_bytes()).hexdigest()),
    repair_number=2,prior_author_failure='runs/R22/execution/correction-v2/receipts/0006-full-document-selfcheck.json',
    scope='Document-only Decimal derived monetary arithmetic; original scientific production and both earlier failed reports preserved.',
    context_exposure='Actual v2 author disclosure retained in ATTEMPT_STATUS and v3 paper; no claim of context blindness.',actual_model=None,tokens=None,cost=None)
with (target.parent.parent/'CHANGE.json').open('x',encoding='utf-8') as f:json.dump(meta,f,ensure_ascii=False,indent=2)
print(json.dumps(meta,ensure_ascii=False))
