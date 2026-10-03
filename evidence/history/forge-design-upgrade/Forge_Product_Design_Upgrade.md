# 架构、体验与动效能力升级

2026-10-02。用户补充的视觉重心、布局密度、配色、交互与组件动效已纳入本轮。独立 **Product Experience Design** 已创建并安装，**Agent Flow Forge** 已更新；两者的已保存文档、方法和资产内容已核对。三个新任务交付的是设计规格与待执行验收计划，没有实现三个应用。

## 职责与交叉关系

这些是便于研发审查的责任视角，各团队的名称和划分可能不同。

| 视角 | 主要决定 | 需要共同审查的影响 |
| --- | --- | --- |
| 系统架构 | 进程、部署、依赖、容量、观测、备份、恢复和信任边界 | 加载策略、预取、重试会改变运行负担与数据访问 |
| 应用架构 | 业务职责、数据归属、状态、不变量、接口、权限和幂等 | 草稿、提交、冲突与反馈必须对应真实业务状态 |
| 前端工程 | 路由、组件、视图/服务端状态、请求生命周期、缓存与渲染 | 取消、陈旧响应、焦点和动效不能破坏状态归属 |
| 体验与视觉设计 | 用户任务、导航、功能分区、主控区、密度、线条、间距、字体、配色与可发现性 | 布局和颜色共同引导注意力；审美偏好需与实际任务表现分别验证 |
| 动效设计 | 组件入场/退出、展开、方向、侧滑、斜向和弹性候选 | 打断、反向、焦点、输入、模态层、性能和减少动态效果替代必须一起定义 |

例如，复核系统要突出“当前需要我处理什么”：区域位置、字号、间距和分隔可以建立非色彩层级；语义颜色再帮助识别状态。高密度列表是否更快、弹性侧栏是否更舒服，都只能先列为假设，需在目标产品中验证。

## 已保存的能力

**[Product Experience Design](https://chatgpt.com/skills?skill_id=6abf2e4f5eac81918006e6d1a19615d3)** 可单独用于设计、改进或审查界面，也可衔接现有前端实现。它包含任务/受众方法、参考抽样记录、语义配色与组件状态、动效规格，以及原创 CSS/HTML 样板。[SKILL.md](skill://flora-skills/root/.codex/skills/remote-skills/skill-6abf2e4f5eac81918006e6d1a19615d3/SKILL.md)

动效规格要求记录用途、触发和前后状态、方向、时间/曲线依据、打断与反向、按触发者定义的焦点进出、模态/背景交互、减少动态效果替代和实际验收。时长及曲线没有平台依据时必须标为可调假设。普通文档滚动与组件入场分别处理。斜向等效果纳入选择方法；样板仅演示无入场动画、轻侧滑和轻弹性三种入口选项，没有实现全部动效类型，也没有声称物理弹簧仿真。

样板提供 Clear/Night 两套原创色板、独立的布局密度与动效选择，以及详情、重跑、筛选、刷新/取消/重试、空结果恢复和删除状态。它是局部原型候选，未证明可直接覆盖任意业务产品。

**[Agent Flow Forge](https://chatgpt.com/skills?skill_id=6ab323b7c2a081919b95502e8e7297f0)** 保留系统/应用/前端工程的架构方法、同一份项目 TODO、编排、集成与验收；通过薄衔接合同调用设计能力，没有复制完整设计模块或建立互相调用循环。[SKILL.md](skill://flora-skills/root/.codex/skills/remote-skills/skill-6ab323b7c2a081919b95502e8e7297f0/SKILL.md)

重要要求需落实到决策、接口/组件、实施任务和验收证据。小修只检查受影响的范围，无界面服务无需增加前端设计。对于重放工作，架构方法增加了操作身份、内容和配置版本的绑定；对于设计审查，增加了输入路由、焦点触发者、模态层和迟到结果的反例检查。

## 参考资源实际读取范围

Refero Styles 被设为优先设计线索，但仍需读取具体相关材料。参考目录、截图、源码、授权和目标产品的验收分别记录。

| 来源 | 本轮证据范围 |
| --- | --- |
| [Refero Styles](https://styles.refero.design/) | 目录页面可读，介绍 DESIGN.md 的颜色、字体、间距和组件材料；没有复制其特定产品设计文档 |
| [Mobbin](https://mobbin.com/) | 官方产品介绍可读；未观看某个具体完整流程 |
| [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/) | 获取正文不足，未据此声称核验了具体 Apple 规则 |
| [Android Design](https://developer.android.com/design) | 官方入口与 system-bars 指南可读；实际设备适配未验 |
| [CollectUI](https://collectui.com/) | 灵感页面可读，未把静态画面当交互证据 |
| [Pageflows](https://pageflows.com/) | 页面访问未成功；官方搜索描述只作未验证线索 |
| W3C、[MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion)、shadcn/ui | 读取相关官方说明；选定色值计算与 reduced-motion 源码检查不能代替整屏或真实交互验收 |

开源或成熟 DESIGN.md 的复用需核对具体版本、适用许可和通知；未知时根据观察制作原创方案。本轮预设没有复制第三方画面、CSS 或资产。

## 实际检查与修订

| 检查 | 实际结果 | 能证明的范围 |
| --- | --- | --- |
| 旧协议回归 | 236 项通过，测试报告耗时 2.554 秒；相关脚本未改动 | 既有协议/控制器回归，不是 UI 或生产系统验收 |
| 样板针对性复验 | 33 条断言通过 | Node 手工 DOM/event fixture 执行真实内联 JS；不模拟浏览器布局或原生 dialog |
| 选定色值 | 22 项配对重算；Clear 最低 5.98:1，Night 最低 7.04:1 | 仅选定源码 token 配对，不是全部状态或 WCAG 合规结论 |
| Skill 结构 | 两个 skill 校验通过；相对链接检查无缺失 | 元数据与资源存在，不是产品质量结论 |
| 保存核对 | 两者方法/资产与保存前锁定内容一致；平台格式化的元数据已检查 | 已保存内容与当前受测资产一致 |
| 新任务设计 | 三类任务实际交付，独立审查的九项发现已在设计/任务/验收中处理 | 小样本设计审查，不是实现、运行时可靠性或普遍泛化认证 |

初次样板审查发现详情与重跑的 workflow 不一致、搜索范围与提示不一致、无结果缺少恢复入口；还修复了取消后普通刷新未恢复取消按钮的问题。复验期望正确行为，未把最初成功复现缺陷的 17 条断言当产品通过。

三个新上下文 Luna 任务及独立复核：

- **手持盘点**：补齐扫码/数量编辑/保存的输入路由，以及复核包丢回执后的稳定提交身份和唯一性。[设计](sandbox:/workspace/scratch/73714494ad2f/forge-design-upgrade/trial-mobile-inventory/design.md) · [验收计划](sandbox:/workspace/scratch/73714494ad2f/forge-design-upgrade/trial-mobile-inventory/acceptance-plan.md)
- **无界面导入服务**：补齐相同投递 ID 不同内容的冲突处理、批次固定解析配置，以及权限验收到任务的绑定。[设计](sandbox:/workspace/scratch/73714494ad2f/forge-design-upgrade/trial-import-service/design.md) · [验收计划](sandbox:/workspace/scratch/73714494ad2f/forge-design-upgrade/trial-import-service/acceptance.md)
- **长文阅读与批注**：补齐按打开入口区分的焦点、抽屉互斥/模态、陈旧搜索响应和迟到保存结果的归属。[设计](sandbox:/workspace/scratch/73714494ad2f/forge-design-upgrade/trial-document-motion/design.md) · [验收计划](sandbox:/workspace/scratch/73714494ad2f/forge-design-upgrade/trial-document-motion/acceptance.md)

作者与审阅者使用分开的写入目录；针对性复核保留原审阅。首轮审阅的一次静态 ID 盘点包含额外 check-record.md 文本，未用于引用或判断，因此不把该轮称完全盲测。三个任务没有执行待验收用例。实际耗时记录包含运行工具故障和能力探测，没有受控前后对照；token 和成本数据不可得，不能推断研发速度或费用改善。

## 尚未验证与后续任务

真实浏览器路径已尝试：Chromium 启动缺少二进制，下载未成功；云浏览器拒绝 data URL 原型入口后停止该路径，没有绕过。因此当前没有截图、真实点击、原生弹窗焦点、响应式布局、动效渲染、设备扫码或应用性能的通过证据。CSS 未做浏览器解析与渲染验收。

首次样板审查保留了报告、脚本与哈希，但没有保留原始源文件快照，无法从当前修复版重新运行原始缺陷。这一可复现性缺口已如实记录，并加入 skill 方法：修复前保留确切版本/快照及原始结果。

现有 [project-todo.json](sandbox:/workspace/scratch/73714494ad2f/forge-upgrade/project-todo.json) 保留了历史，并把本轮设计能力升级标为完成、真实 UI 验收标为能力阻塞。后续优先在真实目标前端与允许的访问路径可用时运行计划中的浏览器/设备旅程；再扩展带来源、版本和实际验收记录的组件/流程预设。原有真实 agent 执行器与必需用例判定集成仍是单独的后续研发任务，本轮未实施。

具体记录：[样板复验](sandbox:/workspace/scratch/73714494ad2f/forge-design-upgrade/preset-audit/RECHECK.md) · [导入复核](sandbox:/workspace/scratch/73714494ad2f/forge-design-upgrade/design-review/import-recheck.md) · [手持端复核](sandbox:/workspace/scratch/73714494ad2f/forge-design-upgrade/design-review/mobile-recheck.md) · [动效设计复核](sandbox:/workspace/scratch/73714494ad2f/forge-design-upgrade/design-review/motion-recheck.md)
