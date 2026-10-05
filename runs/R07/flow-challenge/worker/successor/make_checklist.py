#!/usr/bin/env python3
"""Turn a local allocation run into a duty-staff missing-information checklist."""
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument("--results",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 data=json.loads(a.results.read_text(encoding="utf-8")); rows=[x for x in data["requests"] if x["status"]=="needs_info"]
 lines=["# 器材申请缺失资料收集清单","","来源：本地调配建议结果；请值班员逐项核实并回填。此清单不代表审批或通知。","","| 完成 | 请求/源行 | 优先级 | 现有记录 | 需收集/核实 | 回填与复核 |","|---|---|---|---|---|---|"]
 for x in rows:
  r=x["record"]; why=x["reason"]
  if "missing room" in why: action="请申请方补充使用房间/场地。"
  elif "unknown equipment_id" in why: action=f"请核对器材代码 {r.get('equipment_id','')} 对应名称，并确认器材台账及本次可用数量。"
  else: action="请核对以下缺失资料并补齐。"
  rec=f"器材 {r.get('equipment_id','')}；数量 {r.get('units','')}；日期 {r.get('date','')}；房间 {r.get('room','')}；原因 {why}"
  lines.append(f"| ☐ | {r.get('request_id','')} / 第{x['source_row']}行 | {x.get('priority','')} | {rec} | {action} | 回填：________；复核：________ |")
 if not rows: lines.append("| — | 无 | — | 未发现缺失资料 | — | — |")
 lines += ["","处理后：更新原申请/设备清单并重新运行本地工具；未核实前不要把缺失项当作已分配。"]
 text="\n".join(lines)+"\n";a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(text,encoding="utf-8");print(json.dumps({"checklist":str(a.out),"needs_info_count":len(rows)},ensure_ascii=False));return 0
if __name__=="__main__":raise SystemExit(main())
