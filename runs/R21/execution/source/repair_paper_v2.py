from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
root=Path(__file__).resolve().parent.parent
src=root/'source/build_paper_v1.py';new=root/'source/build_paper_v2.py';text=src.read_text('utf-8')
assert r'^{\mathsf T}' in text
text=text.replace(r'^{\mathsf T}',r'^{T}')
text=text.replace('NPZ 情景含 method 对应原点、残差日、42 个服务日、坐标顺序和等权向量','NPZ 情景含残差日、42 个服务日、坐标顺序和等权向量；方法及最终原点见各模型元数据')
text=text.replace('科学首跑 exit 0，未发生科学失败或调参修复；此前源码及原始记录保留。','科学首跑 exit 0，未发生科学失败或调参修复；论文首轮公式绘图因 mathsf 写法与本机解析器不兼容而 exit 1，源码、部分图像与原始命令全部保留于 paper-v1 和 source/build_paper_v1.py；新版本仅修复公式转置符号的显示和元数据说明，不改科学结果。')
with new.open('x',encoding='utf-8') as f:f.write(text)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v={'utc':datetime.now(timezone.utc).isoformat(),'category':'tool/document rendering recovery','failure_command':'commands/006-paper-v1.json','failure':'matplotlib Unknown symbol mathsf in unbraced T exponent','old_source_sha256':sha(src),'new_source_sha256':sha(new),'old_outputs_preserved':'paper-v1/','change':'render equivalent plain T transpose exponent; correct NPZ contents explanation; disclose failed report rendering','scientific_configuration_changed':False,'scientific_results_changed':False}
with (root/'paper-repair-v2.json').open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(v,ensure_ascii=False,indent=2))
