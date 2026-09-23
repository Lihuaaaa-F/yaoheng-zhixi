# 前端审查证据（agent_frontend_findings）

- 审查对象：worktree `D:/yaoheng-audit-wt-1f78b2f`（yaoheng-zhixi @ 1f78b2f74aad）
- 项目根：`药衡智析_增量源码交接/public_source_candidate/05_原型/`
- 范围：`frontend/src/` 全部 24 文件 + `index.html` `vite.config.ts` `package.json` `tsconfig.json` `echarts-gl.d.ts` + `e2e-*.mjs` `record-demo*.mjs`（只读）+ 交叉对照 `backend/pharma/api.py`（574 行，只读）
- 方法：逐文件完整阅读；判定分级：满足 / 部分 / 不满足 / 未实现 / 待验证(静态确认) / 待实测。审查者无视觉能力，不对美观/渲染下结论。
- 行号均为文件内实际行号（文件为长行密集格式，一行含多个语句）。

---

## 1. 页面 / 按钮 / 表单 / 筛选器 / 下载入口 全量清单及 API 对照

导航（App.tsx:19-23）：数据中心(业务数据/知识库数据/报告模板) → 工作台(数据分析/跨厂对标/报告生成/问题整改) → 模型配置(数据提取模型/数据分析模型/向量模型)，共 10 页，`page` 索引驱动（App.tsx:115 aria-current）。

| 页面/区域 | 控件（文件:行） | API | 判定 |
|---|---|---|---|
| 全局 | 数据范围 select（App.tsx:130） | GET `/api/industry/catalog`(App:59)、切值触发 GET `/api/catalog?context_id`(App:71) | 满足 |
| 工作台筛选 | 产品/工厂/月份/报告范围 select + 成本口径 aria-pressed 按钮组（App.tsx:136-140） | 触发 POST `/api/analyses`（effect App:80-88） | 满足 |
| 季度切换 | changeRange 对齐季度末月（App.tsx:102-106）；无季末月时 option disabled（App:139） | — | 满足 |
| 数据分析 | 指标卡 4 枚=button 点击开证据抽屉（Analysis.tsx:51） | — | 满足 |
| 数据分析 | 桥接口径 select 环比/同比/预算（Analysis.tsx:72） | —（前端重算瀑布） | 满足 |
| 数据分析 | 根因定位面板（Analysis.tsx:54-62） | GET `/api/attribution?context_id&factory&product&month&basis`（Analysis:39-42） | 满足；仅 `pharmaceutical:competition` 上下文可用，其余返回 UNAVAILABLE+原因（api.py:479-480），前端有 notice 空态 |
| 数据分析 | 预测面板（Analysis.tsx:67-69） | GET `/api/forecast?...`（Analysis:32-35） | 满足；PASS/ERROR/其他三分支 |
| 数据分析 | NarrativePanel 生成/重新生成按钮（NarrativePanel.tsx:13） | POST `/api/reports`（NarrativePanel:11，DEGRADED 时附 retry:true） | 满足 |
| 数据分析 | DecisionCard 按决策生成报告 / 生成决策说明（DecisionCard.tsx:47-48） | GET `/api/agent/decision?...&with_advisory`、POST `/api/agent/decision/{id}/apply`（DecisionCard:27,34） | 满足；apply 后 onApplied→refresh |
| 数据分析 | 产品×月份热力图 + 成本要素 select + 单元格 button（ProductMonthHeatmap.tsx:21） | GET `/api/dashboard/heatmap?context_id&factory&month&basis`（:10） | 满足；点击单元格回写 selection（App:154） |
| 跨厂对标 | 分析/基准工厂 select（互斥 disabled）+ 交换方向按钮（App.tsx:156-160, Benchmark.tsx:11） | GET `/api/benchmarks?context_id&product&month&left&right&analysis_type&basis`（App:93-94） | 满足；left===right 有 effect 守卫（App:90）与后端双保险（api.py:138） |
| 跨厂对标 | 假设"查看依据与缺证项"、证据"查看来源位置"（Benchmark.tsx:11） | —（用返回数据） | 满足 |
| 报告生成 | 生成报告/重新生成（忽略缓存）按钮（ReportGeneration.tsx:31-34） | POST `/api/reports`（附 retry） | 满足；见 F1 快照陈旧问题 |
| 报告生成 | 历史记录 checkbox（ReportGeneration.tsx:37） | —（本地过滤 jobs） | 满足 |
| 报告生成 | Word/PDF/机器审计附件下载 `<a download>`（ReportGeneration.tsx:46-51） | GET `/api/artifacts/{id}`（api.py:211） | 满足；仅 SUCCEEDED/DEGRADED 出链接 |
| 问题整改 | 任务草稿表单（责任人/部门/角色/优先级/问题/核查对象/预期证据/建议/期限依据/截止日期）+ 生成/保存草稿（Rectification.tsx:44-59） | POST `/api/actions`、PUT `/api/actions/{id}`（:57-58） | 满足；必填校验与后端 ActionRequest(min_length) 对齐 |
| 问题整改 | 载入当前报告建议 select（Rectification.tsx:37-42） | —（读 jobs 数据） | 满足 |
| 问题整改 | 编辑草稿 / 确认并发送模拟通知 / 查询模拟通知状态（Rectification.tsx:84-96） | POST `/api/actions/{id}/confirm`{payload_hash}、`/refresh`（:93,96） | 满足；人工确认门=仅 DRAFT/PENDING_CONFIRMATION 显示 |
| 问题整改 | 登记责任人确认（姓名必填+备注）（Rectification.tsx:99-107） | POST `/api/actions/{id}/acknowledge`（:104） | 满足 |
| 问题整改 | 任务看板三统计（Rectification.tsx:33） | GET `/api/actions?context_id`（hooks.ts:27） | 满足 |
| 业务数据 | 5 类型上传 + 解析数据 + 预览（BusinessData.tsx / ImportWorkflow.tsx） | POST `/api/imports/uploads`(FormData kind,data_type,file)、GET `/api/imports?kind`、GET `/api/imports/{id}/preview`、POST `/api/data/parse` | 满足；见 F3 校验/发布未接 |
| 知识库数据 | 3 类型上传 + 构建知识索引 + 检索表单 + 图谱（KnowledgeData.tsx / Evidence.tsx） | POST `/api/kb/build`、GET `/api/kb`、POST `/api/kb/search`{query,product,month,factory,mode,context_id}、GET `/api/kb/graph` | 满足 |
| 报告模板 | 3 类型上传 + 解析报告模板 + 已安装模板表（TemplateCenter.tsx） | POST `/api/templates/parse`、GET `/api/templates` | 满足 |
| 模型配置 ×2 | ModelConfigForm：接入方式/厂商/型号(datalist)/BaseURL/密钥/协议/推理强度滑块 + 获取模型列表/测试连接/保存（ModelConfigForm.tsx:108-157） | GET `/api/settings/models`、GET `/api/settings/models/presets`、PUT `/api/settings/models`、POST `/api/settings/models/test?route`、GET `/api/settings/models/list?route&base_url` | 满足；档位不符前端预警（:64-71） |
| 向量模型 | 目录输入 + 确认 + 切换进度（ModelPages.tsx:22-64） | GET `/api/settings/vector-model`、POST `/api/settings/vector-model/switch`{path} | 满足 |
| 全局 | 任务/整改轮询（报告生成/问题整改页 2s，其他页 -1 不轮询）（App.tsx:55, hooks.ts:21-37） | GET `/api/jobs?context_id` + `/api/actions` | 满足 |
| 全局 | 解析进度（百分比/阶段/时间线）（JobProgress.tsx） | GET `/api/jobs/{id}`（1.2s 轮询，终态停） | 满足；jobs 表确有 progress/detail 列（jobs.py:21-22） |
| 全局 | 错误重试（App.tsx:144,174） | 递增 reload 触发 effect 重取 | 满足 |

未接后端的控件：未发现（全部交互控件均有 API 或纯本地过滤，均有真实数据流）。

## 2. 成本看板（赛题 5.2）ECharts 配置对照

| 赛题要求 | 实现（文件:行） | 配置要点 | 判定 |
|---|---|---|---|
| 趋势图：近 6 个月单位成本折线 | Analysis.tsx:63 | line 系列；xAxis=历史月+预测月；yAxis name=costLabel（由 metric.unit/quantity_unit/currency 推导，Analysis:44）；历史实线+area、预测虚线 diamond、区间带 stack；tooltip 值+单位 | 满足（静态）；trend 为后端全量序列未截 6 个月，头部标注"可用 N 个月" |
| 精确值 | "查看精确趋势数据"表（Analysis.tsx:65）、热力图下表（ProductMonthHeatmap:21）、图 tooltip | 原始 Decimal 串保留（presentation.tsx:2 注释） | 满足 |
| 瀑布图：成本变动分解 | Analysis.tsx:46-48 | 透明底 stack 桥接；升 #bd673f / 降 #227c81；首尾柱 label 精确值；环比/同比/预算三口径 select；comp.base 为空 → "N/A · 原因"空态 | 满足；F4 缺 comparisons 时平桥 |
| 结构图：本月构成 | Analysis.tsx:66 | pie radius['48%','70%'] 环形 + legend + tooltip 占比；按口径切 unit/total | 满足 |
| 热力图：产品×月份×要素（加分） | ProductMonthHeatmap.tsx:21 | heatmap + visualMap；成本要素 select（elements 来自后端 dashboard.py:121-129）；**单位一致性守卫**（不同物理单位拒绝共刻度，:15-17）；缺失格保留空格+reason；点击联动 selection | 满足；后端固定近 6 个自然月（dashboard.py:97） |
| 要素环比热力图（附加） | Analysis.tsx:83-88 | 要素×{单位成本,总成本} 环比 %，±bound 对称色阶 | 满足 |
| 单位/口径标注 | snapshot-line 产量单位（Analysis:52）、季度口径注释（App:142）、总额口径提示（Analysis:72） | — | 满足 |
| 筛选联动 | selection 变化→effect 重取（AbortController），热力图 onSelect 回写 | — | 满足（竞态见 §4） |
| 缺数据/加载/错误 | analysisLoading role=status（App:145）、ErrorBox role=alert+重试（App:144,174）、热力图三态（ProductMonthHeatmap:21） | 趋势图本身无独立空态（t 空时显示空图+"可用 0 个月"） | 部分满足（P3） |
| 模型可用时自动重点分析 | 后端 POST /api/analyses → focus_analysis(enqueue 报告)（api.py:105-121，PHARMA_AUTO_EXPLAIN 默认 true）→ focus.job_id 返回（dashboard.py:81）→ NarrativePanel effect 取 active job 或 focus.job_id → 2s 轮询至完成（NarrativePanel:9-10） | 触发链代码完整 | 待验证(静态确认)；实际入队依赖运行时模型密钥，待实测 |

## 3. 契约差异清单（前端 ↔ backend/pharma/api.py）

逐参数核对结论：

1. POST `/api/analyses`：前端 Selection 6 字段与 AnalysisRequest(extra='forbid') 精确匹配 — 一致。
2. GET `/api/benchmarks`：后端 product/month/left/right 必填（api.py:134）；前端保证非空且互斥 — 一致。
3. GET `/api/dashboard/heatmap`：month 必填带 pattern（api.py:125）；前端 month 空串（catalog.months 全空）时 422 — 理论边界（P3）。
4. **不一致**：GET `/api/kb` 非竞赛上下文返回 `{'status':'READY',...}` 且无 `sources`（api.py:414-417），前端只认 `'PASS'` 且读 `status.sources`（Evidence.tsx:12）→ 显示"已登记来源 0 份；索引需要复核"误导（P3，竞赛上下文 manifest 含 sources+status PASS，knowledge.py:355）。
5. GET `/api/kb/graph`：status PASS/EMPTY/NOT_BUILT/DEGRADED + nodes/edges/stats/rules_version（graph.py:177-180）↔ 前端 PASS 门控+全部消费 — 一致。
6. POST `/api/actions`：前端 deadline 额外字段被 pydantic 默认忽略（ActionRequest 未设 forbid，api.py:43-45）— 兼容。
7. PUT `/api/actions/{id}`：后端收任意 dict（api.py:441），前端发完整 payload — 兼容。
8. **后端有、前端零调用**（grep `validate|/mapping|/publish|template-check|reviews` 于 frontend/src 零命中）：
   `/api/imports/{id}/mapping`、`/validate`、`/publish`、`/file`、`/template-check`；`/api/reports/{id}/reviews`(POST/GET)、`/api/reports/{id}/acceptance`、`/api/reviews/import`；`/api/model/routes`；`/api/actions/{id}`(GET)；`/api/analyses/{id}`；`/api/artifacts/{id}?preview`；`/api/imports`(POST)。
   → 前端走一键 `/api/data/parse` 流水线替代 granular 流程（见 F3）；人工评审提交无 UI。

## 4. 竞态与状态一致性（静态分析）

- 分析/对标/热力图/归因/预测/知识检索/任务轮询均使用 AbortController + aborted 检查后 setState（App:57-98、Analysis:32-42、ProductMonthHeatmap:10、Evidence:8-10、hooks:21-37、NarrativePanel:9-10、JobProgress:12-34、FilePreview:9-18）——快速切换筛选/月份不会陈旧覆盖新结果。e2e-dashboard.mjs:35 另有刷新不触发报告/模型的回归断言（mock 环境）。
- hooks.refresh 用 currentContext ref 防跨上下文写入（hooks:17）。
- **F1（见 §5）为唯一状态一致性缺陷**：分析 effect 以 isAnalysisPage 为闸（App:81），报告生成/问题整改页上筛选变化不重取 snapshot。

## 5. 发现清单（严重度分级）

| # | 严重度 | 判定 | 问题 | 位置 | 反证/缓解 |
|---|---|---|---|---|---|
| F1 | P2 | 部分 | 报告生成/问题整改页快照陈旧：筛选（产品/月份等）变化时分析 effect 因 `!isAnalysisPage` 早退不重取（App.tsx:81）；`生成报告` 按新 selection POST（ReportGeneration.tsx:32），但任务卡默认列表按旧 `snapshot?.snapshot_id` 过滤（ReportGeneration.tsx:16-17）、整改页 `visibleActions`/`availableFindings` 同样绑旧 snapshot（Rectification.tsx:17-19）→ 新提交任务在默认视图不出现、页头展示新选择与实际不符 | App.tsx:80-88,162-163; ReportGeneration.tsx:16-32; Rectification.tsx:17-19 | 勾选"查看历史报告及失败记录"可见全部；回到数据分析页即恢复一致；功能可完成，属一致性缺陷 |
| F2 | P2 | 部分 | e2e/demo 脚本半数陈旧：e2e-context.mjs、e2e-live.mjs、record-demo.mjs（`npm run e2e`、`npm run demo:record`）、record_full_demo_20260920.mjs 引用 2026-09-22 三模块改版前的选择器/文案（'行业包'、'数据与证据'、'报告与任务'、'当前企业任务看板'、'02跨厂对标'、'03报告与整改'、'报告已提交，请查看当前报告的分项验收。'），对当前 UI 第一步即定位失败超时 | e2e-context.mjs:32-37; e2e-live.mjs:12-19; record-demo.mjs:19-27; record_full_demo_20260920.mjs:158,182 | e2e-dashboard.mjs 与 e2e-knowledge-graph.mjs 全部使用现行选择器，证明是遗留未更新而非 UI 回归 |
| F3 | P2 | 未实现 | 数据导入"预览—校验—发布"的校验/发布环节与错误行定位无前端：后端 granular 端点（mapping/validate/publish/template-check，api.py:377-410）无调用方；失败仅显示 `meta.parse_error` 前 120 字符（ImportWorkflow.tsx:92）+ 任务阶段时间线；validate_business 的行级结果无 UI 呈现路径。搜索词 `validate\|/mapping\|/publish\|template-check` 于 frontend/src 零命中 | api.py:377-410 ↔ frontend/src 全部 | UI 改走一键 `/api/data/parse` 全流水线（进度+终态提示完整），并非流程缺失，而是 granular 自助路径未暴露 |
| F4 | P3 | 部分 | 瀑布图空态判定只看 `comp.base`：同比/预算口径缺 `comparisons` 时 changes 回退 0 → 渲染全零平桥而非 N/A（同表内变动额列显示 N/A，图与表不一致） | Analysis.tsx:46-48 | comp.base 为 null 时正确显示 N/A；仅"base 有值但要素比较缺"的组合出现 |
| F5 | P3 | 部分 | 趋势图 `yAxis min:0` 会截断负值预测点；后端预测存在负值场景（negative_warning 字段，Analysis.tsx:67 表格有提示），图上不可见 | Analysis.tsx:63 | 预测表保留精确负值与警示文案 |
| F6 | P3 | 部分 | 非竞赛上下文 /api/kb 契约显示误导（见 §3.4） | Evidence.tsx:12 ↔ api.py:414-417 | 竞赛上下文（主要演示对象）不受影响 |
| F7 | P3 | 未实现 | 人工评审提交无 UI：Acceptance 显示"待真人评审/归因评分待评"（presentation.tsx:31），但 `/api/reports/{id}/reviews` 无前端调用，评审只能走 API/import | presentation.tsx:28-32 ↔ api.py:268-284 | 展示侧（Acceptance 8 维）完整，录入侧设计为 API |
| F8 | P3 | 部分 | 知识库数据页检索范围取全局 selection 默认值且该页无筛选器可调（分析筛选仅工作台渲染，App.tsx:135）；页面明示"核查范围"值 | App.tsx:135,148; Evidence.tsx:12 | 值透明展示，非隐藏 |
| F9 | P3 | 部分 | 抽屉/预览弹窗无焦点圈闭（无 focus trap/inert；Tab 可越至背景），Esc 关闭+autoFocus 关闭按钮已有 | Evidence.tsx:120-124; FilePreview.tsx:19 | 键盘可达性基本满足（native dialog 语义 role=dialog aria-modal） |
| F10 | P3 | 部分 | 知识图谱/图表交互仅鼠标路径：3D 悬停 tooltip（Chart3D onHover）与 ECharts tooltip 无键盘替代；canvas role=img 仅标题级 aria-label | Chart3D.tsx:37-59; Evidence.tsx:88-116 | 静态信息（图谱统计、说明段）有文本可读 |
| F11 | P3 | 部分 | 重试后上下文重置：`reload` 递增重跑 catalog effect，闭包 `contexts.length` 恒 0（App.tsx:63）→ contextId 重置默认，丢用户当前选择（仅 context 加载失败后的重试场景） | App.tsx:57-66 | 场景罕见（首次加载失败才出现 ErrorBox） |
| F12 | INFO | — | 顶栏"本地服务"为硬编码静态文本，未接 GET /health（frontend 零调用 /health）；后端宕机时仍显示 | App.tsx:122 | — |
| F13 | INFO | — | 死代码：`{c.context_id === 'pharmaceutical:competition' ? '' : ''}` 两分支均为空 | App.tsx:131 | — |
| F14 | INFO | — | Chart3D 测试钩子 `window.__chart3d` Map 在 dispose 时不清条目（仅本页内存滞留） | Chart3D.tsx:27-32 | — |
| F15 | INFO | — | catalog.months 全空时 month='' 传 /dashboard/heatmap 会 422（数据全空才触发） | ProductMonthHeatmap.tsx:10 ↔ api.py:125 | App:73 月末兜底 `?? ''` |

无 P0/P1 发现：核心流程（导入→分析→对标→报告→整改）前后端契约一致、竞态防护完备、空/错/载态齐备。

## 6. RPA 任务流 / 报告生成 / 数据导入 前端核查结论

- 人工确认门：仅 DRAFT/PENDING_CONFIRMATION 显示"编辑草稿/确认并发送模拟通知"，confirm 携带 payload_hash（Rectification.tsx:83-95 ↔ api.py:442-443）— 满足。
- 状态展示：10 态 taskLabel + 接口请求/模拟通知/整改进度三字段显式区分"远端接收/模拟送达/整改完成"语义（Rectification.tsx:6,79-81）— 满足。
- 任务追踪看板：已生成(ID 去重)/模拟通知送达(SIMULATED_SENT)/责任人确认(CONFIRMED+署名+时间戳) 三统计（Rectification.tsx:28-33）— 满足。
- 报告主题/月份/产品：经全局工作台筛选（报告范围含月度/季度/专题；季度末月对齐逻辑 App:102-106），页头回显当前选择（ReportGeneration.tsx:30）— 满足（受 F1 一致性影响）。
- 生成进度/下载/DEGRADED：job 卡 status+progress%（2s 轮询）；Word/PDF/审计附件 download 链接仅 SUCCEEDED/DEGRADED；DEGRADED 双处标注（jobLabel ReportGeneration:6 + AnalysisStatus presentation:24 + Acceptance 8 维 presentation:26-31）— 满足。
- 数据导入：五类业务/三类知识/三类模板上传（accept 限制）→ 列表（类型/文件名/格式/大小/状态徽章/时间/预览）→ 一键解析 → 进度（百分比/阶段/时间线）→ 成功(15s 自动消隐)/失败提示 — 满足；预览 FilePreview（表格前 200 行/PDF iframe/docx 段落+表格/纯文本）— 满足；校验/发布/错误行定位 — 见 F3。

## 7. 可访问性（代码层可证明部分）

满足：全部 input/select/textarea 均有 label 包裹或 aria-label（逐控件核对 App/ImportWorkflow/Rectification/ModelConfigForm/ProductMonthHeatmap/Evidence）；native button；nav aria-current；口径/接入方式按钮 aria-pressed；focus-visible 全局 outline（style.css:1）；prefers-reduced-motion（style.css 尾）；role=status/alert 广泛使用；抽屉 role=dialog aria-modal+Esc+autoFocus（Evidence.tsx:120-124）；热力图单元格为带 aria-label 的 button（ProductMonthHeatmap.tsx:21）；图表容器 role=img+aria-label（Chart.tsx:17, Chart3D.tsx:59）。
不足：F9 焦点圈闭、F10 图表/图谱键盘替代、Chart aria-label 仅标题（无数据摘要）。

## 8. e2e / record-demo 脚本（只描述脚本将做什么，不声称任何视频画面已完成的事项）

- e2e-dashboard.mjs：mock 全部 /api（合成双产品 6 个月夹具）→ 断言重点分析四位小数精确渲染、不可比要素说明、热力图要素切换/单元格点击联动 analyses(analysis_type=monthly)、口径切换改单位、reload 不触发 /api/reports 与 with_advisory=true、1440/390 无横向溢出且零 console 错误。
- e2e-knowledge-graph.mjs：连 127.0.0.1:8765 真实服务 → 断言图谱 canvas 尺寸、全屏切换、左键旋转/滚轮缩放/右键或中键平移（截图 md5 变化+相机参数）、全图扫描 .kg-tooltip、拖拽后零 pageerror。
- e2e-context.mjs / e2e-live.mjs / record-demo.mjs / record_full_demo_20260920.mjs：脚本意图分别为（mock 契约回归：上下文切换竞态/对标/检索范围/任务确认计数）、（真实服务冒烟：行业包数值/季度/对标/检索/报告提交）、（录制合成包演示视频+README 回执）、（带光标特效的全流程演示录制）——但四者选择器对应改版前 IA，当前构建无法走通（F2）。
- record_demo_20260918.mjs(.test.mjs)：录制驱动库（requireLoopback/validateHealth/validateJob：回环地址、本地模拟、工件 sha256 绑定校验）+ node:test 纯函数单测（可在无浏览器环境运行，断言逻辑自洽）。

## 9. 判定统计与残留

统计：满足 22 项 / 部分 8 项 / 不满足 0 / 未实现 2 项（F3 错误行定位 UI、F7 评审提交 UI）/ 待验证(静态确认) 1 项（自动重点分析实际入队，代码链完整）/ 待实测：全部渲染与交互效果、模型真实调用、RPA 模拟送达（超出静态审查范围）。

残留（本审查未覆盖）：package-lock 完整性、public/ 静态资源、后端 worker/narrative 等非 api.py 模块内部逻辑、TypeScript 编译与 lint 实际通过性（未运行构建）、跨浏览器行为。
