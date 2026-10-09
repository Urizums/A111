"""Create a new renderer only; never edit or rerun the locked scientific production."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'runs/R22'
original=BASE/'execution/source/build_report_v1.py'
source=original.read_text(encoding='utf-8')
target=BASE/'execution/correction-v2/source/build_report_v2.py'
assert not target.exists()
source=source.replace('import json,hashlib,html','import json,hashlib,html\nfrom decimal import Decimal, ROUND_HALF_UP')
old="def fmt(v,n=3):return '不可估计' if pd.isna(v) else f'{v:.{n}f}'"
assert source.count(old)==1
source=source.replace(old,"def fmt(v,n=3):return '不可估计' if pd.isna(v) else format(Decimal(str(v)).quantize(Decimal(1).scaleb(-n),rounding=ROUND_HALF_UP),f'.{n}f')")
old="out=ex/'report-v1'"
assert source.count(old)==1
source=source.replace(old,"out=ex/'correction-v2/report'")
needle="逐键接口保留10位小数。"
assert source.count(needle)==1
source=source.replace(needle,needle+"展示表从公开CSV值按Decimal ROUND_HALF_UP统一舍入；同一指标的正文与表格遵循同一规则。旧稿首判h6失败及原报告保留，本版只修展示一致性，科学源码与结果未改。")
target.parent.mkdir(parents=True,exist_ok=True)
with target.open('x',encoding='utf-8',newline='') as f:f.write(source)
metadata=dict(original_renderer=dict(path=original.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(original.read_bytes()).hexdigest()),
    new_renderer=dict(path=target.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(target.read_bytes()).hexdigest()),
    first_verdict='runs/R22/review/initial/result.json',display_rule='Decimal ROUND_HALF_UP of published CSV values; unchanged scientific production.',
    scope='New report output only; original first production source/config/science/MD/PDF and first judgment stay immutable.',
    expected_recheck='Full Chinese MD/PDF and all repeated monetary values; all final pages actually viewed after rebuilding.',actual_model=None,tokens=None,cost=None)
with (BASE/'execution/correction-v2/CHANGE.json').open('x',encoding='utf-8') as f:json.dump(metadata,f,ensure_ascii=False,indent=2)
print(json.dumps(metadata,ensure_ascii=False))
