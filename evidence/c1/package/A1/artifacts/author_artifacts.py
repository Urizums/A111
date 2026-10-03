from pathlib import Path
import json

root = Path("/workspace/scratch/73714494ad2f/forge-protocol-comparison-20261003/package/A1/artifacts")
actions = [
    {
        "task": "更新部署文档",
        "owner": "赵宁",
        "due": "周五",
        "source_quote": "赵宁负责更新部署文档，截止周五。"
    },
    {
        "task": "补充回归用例",
        "owner": "许静",
        "due": "2026-10-09",
        "source_quote": "许静负责补充回归用例，截止2026-10-09。"
    },
    {
        "task": "补充日志告警",
        "owner": None,
        "due": None,
        "source_quote": "决定补充日志告警。"
    }
]
business = {
    "outcome": "ok",
    "artifacts": {
        "actions": actions
    }
}
(root / "actions.json").write_text(
    json.dumps(business, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)
explanation = """根据会议纪要，提取出 3 项明确行动：

1. 赵宁更新部署文档，截止时间保留原文中的相对日期“周五”。
2. 许静补充回归用例，截止时间为“2026-10-09”。
3. 会议决定补充日志告警，但未说明负责人或截止日期，因此两项均为 null。

“建议以后考虑更换配色”属于建议，未作为承诺列入；“本周没有新增外部通知”不是行动项。
"""
(root / "解释.md").write_text(explanation, encoding="utf-8")
