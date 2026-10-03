# Ticket Approval 前端参考资料包

研究对象：桌面工单审批工具；高频往返待处理队列与详情，审批/退回；需要可见的加载、失败和重试状态。检索日期：2026-10-02。研究启动约 05:06 UTC（启动秒级时间未采集，按首个可用时钟记录回估）；结束 2026-10-02T05:11:00Z（UTC）。

## 来源与观察

1. [Refero Styles：Workflow](https://styles.refero.design/style/71451d9e-9a8a-4858-9a91-fbe44047e110)（web open，ref `turn18view0`）。读取页面抽取文本及组件/token说明；未打开其所链接的 workflow.design 产品。可见纸白/雾灰画布、细线分隔、Inter UI、Sage `#547e69` 状态描边、4/8/12px 圆角；有审批状态 pill、评论面板、Share/Approve 行。页面注明尺寸已归一化、角色建议含解释，HTML 示例是重建组件。截图通过图片链接取回，但普通网页 screenshot 不可用，未核验截图内真实状态/操作。条款与精确版本未核验；仅观察，不复制其代码、资产或设计稿。
2. [Microsoft Fluent 2：React List](https://fluent2.microsoft.design/components/web/react/core/list/usage)（ref `turn27view0`）、[Skeleton](https://fluent2.microsoft.design/components/web/react/core/skeleton/usage)（`turn21view2`）、[Message bar](https://fluent2.microsoft.design/components/web/react/core/messagebar/usage)（`turn21view1`）。官方 Web/React 组件指导页面正文可读；预览区显示 Loading，内嵌示例图仅见占位说明，未核验目标应用。List 指引说列式信息用 DataGrid/Table；含次级动作时键盘可用方向键进入、Enter/Space触发，Left/Esc返回父容器。Skeleton 适合超过1秒、结构已知且不应阻塞其他区域的加载；保持动效同步，并保留辅助技术标签/焦点。Message bar：错误需有能解决问题的按钮或链接；放在页面或对应内容容器顶部，文案简短具体，问题未解决时重新显示。文档未说明本工具的后端或实际重试成功契约。

## 候选与适配

- **队列与详情（推断）**：若工单有相同字段，队列用可扫读的列式表格；行内突出编号、提交者、更新时间、状态，头部放筛选/排序。选行后用保留队列上下文的详情侧栏，关闭/Esc回到原行并恢复焦点，可支持连续处理。列式选择来自 Fluent 指引；侧栏、字段及返回行为没有在 Refero 页面中观察到，需由目标 app 验证。若每项只有标题/摘要且无对齐字段，改用平行结构列表。
- **审核动作（推断）**：详情标题与关键字段优先；底部或顶部固定“批准”“退回”，退回需要意见输入。Refero 的 sage 描边批准 pill、评论面板可作低彩度视觉参考；不要把其营销页式宽松留白直接套入高密度队列。成功后明确状态更新，再移到下一项；失败保留当前工单与未提交输入，展示具体错误及“重试”。这些是建议状态契约，非来源观察。
- **加载/失败**：固定导航与筛选不做骨架；队列/详情已知结构加载超过1秒时用对应行/字段 skeleton，避免全页遮罩。网络或操作失败在受影响容器顶部给可读消息与“重试”；明确重试对象（刷新队列/重新提交审批），避免仅用短暂 toast。骨架波纹/同步有 Fluent 指引；是否后台刷新、失败后能否安全重放审批，需核验业务接口。
- **待核验**：实际桌面 viewport、数据密度、分页/搜索、退回是否必填、批量操作、并发状态变化、审批提交能否幂等、失败后的焦点去向及键盘路径。Fluent 资料适用于 Web React 组件层；原生桌面栈需另查对应平台。以上为观察与候选，不代表已实现或符合目标 app 行为。
