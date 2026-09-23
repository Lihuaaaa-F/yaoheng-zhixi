# 药衡智析（yaoheng-zhixi）独立全仓审查报告

- **审查日期**：2026-09-23
- **审查对象**：`github.com/Lihuaaaa-F/yaoheng-zhixi`，main 分支提交 **1f78b2f**（本地与远端一致，其余分支均早于该提交）
- **审查方式**：Trail of Bits `audit-context-building` + `spec-to-code-compliance` 技能方法论，**portable/manual 模式**（当前客户端无原生斜杠工作流；技能文本已按指定版本 32e34f8 显式加载并全程应用其"跟随调用链/证据留痕/absent 须有搜索记录/独立反证"规则）；辅以 Matt Pocock codebase-design 词汇做架构评价。重要发现由独立子任务反证复核（非同一推理上下文）。
- **审查执行人**：GLM-5.3（ZCode 会话）。视觉/人工评分项一律移交 VISUAL_HANDOFF.md，未由本模型代判。
- **隔离验证环境**：Windows 10 + Git Bash；detached worktree `D:\tmp\yaoheng_audit_wt_1f78b2f`（HEAD=1f78b2f，干净）；全部动态验证使用独立 `PHARMA_RUNTIME_DIR`/`PHARMA_ARTIFACTS_DIR`/独立 SQLite，未触碰正式运行数据。复用主工作区 `.venv` 依赖（版本即 requirements.lock 锁定集）与本机已下载的 bge 向量模型资产（只读）。
- **未提交改动单列**：主工作区有 8 个文件的未提交修改（backend/pharma/reports.py、api.py，frontend 5 个文件，+217/−31 行）与若干未跟踪探针文件——**全部不计入本轮审查基线**，本轮结论仅针对提交 1f78b2f。

## 一、本轮实测记录（全部为本轮执行，非沿用旧回执）

| # | 验证 | 命令/脚本 | 结果 |
|---|---|---|---|
| V1 | 后端全量测试 | `pytest -q tests`（隔离 runtime） | **387 passed, 1 skipped**，28.9s，退出码 0 |
| V2 | 关度达成，其中 6 项初次"失败"系本审查脚本方键数值独立复算 | EVIDENCE/verify_metrics.py + verify_engine_compare.py（期望值直接从题包原始 CSV 以 Decimal 推导，不经被测引擎） | **81/81 一致**：单位成本/环比/同比/预算偏差/三要素变动与贡献度/严格±10%告警/预算桥三分解/原料排序/对标差异与差异率（≤1%精向假设相反，经显式方向复验全对——见 AUD-BENCH-02） |
| V3 | RPA 闭环端到端 | EVIDENCE/verify_rpa_e2e.py（题包**原版 mock_rpa_server.py** 真实起服务） | 同载荷草稿幂等（同 id）；确认→QUEUED→deliver→**SENT**，回执 notification=SIMULATED_SENT（status_history 证明）；重复投递不重发；refresh 远端 task_id 回显一致 |
| V4 | RAG 实测 | 隔离 runtime 冷构建 + 三模式检索 | 知识索引 **PASS：180 分块/11 源/0 失败/向量无错**（48s）；hybrid/bm25/vector 均返回带来源定位结果（产品配方文档_银黄口服液.pdf 第1页）；产品范围过滤生效；关向量后 hybrid → status=DEGRADED + reason=VECTOR_DISABLED（诚实降级） |
| V5 | 模型连通 | `model_settings.test_connection('analysis')`（1 次短调用，密钥不回显） | **PASS**：glm-5.3，返回 model 身份 VERIFIED_EXACT，结构化输出 true，1.45s |
| V6 | 报告全链端到端 | 隔离环境入队真实 report 任务（含真实模型调用） | 终态 DEGRADED（人工维度待评所致，符合设计）；narrative **PASS**、model_live=true、身份 VERIFIED、3 次调用、generation_mode=llm；**docx PASS、pdf PASS（13 页）**；验收八维中文件可开/计算一致/证据适用/任务可执行/模型参与全 PASS，章节完整/可读性/视觉=PENDING（待真人） |
| V7 | 前端 | 未运行浏览器测试（本机 Playwright/Chromium 可复用，但本轮时间预算优先后端链路）；静态审查全部 27 个源文件 | 标注为验证缺口，见 VISUAL_HANDOFF |
| V8 | Docker 构建 | 未构建镜像（构建耗时长且属改变系统状态的操作）；静态审查 Dockerfile/Compose/entrypoint/launcher | CI 无 Docker 构建步骤；镜像正确性依据：静态审查 + README 记载的 2026-09-20/21 净机构建实测记录。**标注为待实测** |
| V9 | GitHub 可达性 | 匿名内容 API 读取 README（ref=main） | 成功，内容与本地 1f78b2f 一致；"公开可见性"建议浏览器无痕窗口最终确认 |

## 二、总体判断

该仓库是一个**工程完成度和诚实度都显著高于一般比赛原型**的系统：确定性 Decimal 成本引擎、有界生成合同（模型只写定性结论、数字全部程序绑定并审计留痕）、版本化知识检索（适用性前置过滤+RRF 融合+诚实降级）、事务性 RPA outbox（幂等/对账/人工确认分离）、三服务 Docker 部署（worker 心跳就绪判据）与桌面启动器，均有真实实现并经本轮隔离实测验证。赛题四大模块的强制功能路径全部可走到端，且系统自身持续区分"机器可证 / 待真人"，从不冒充人工验收。

本轮**未发现 P0/P1 级问题**。确认的缺陷集中在"用户自导入数据"路径（赛题 CSV 不受影响）：XLSX 公式单元格金额静默丢失（P2）与能力预览矛盾+发布顺序缺陷（P2，同根因）。另有 6 项 P3。比赛整体验收仍有列明的待验证项（真人 0–5 评分、视觉版式、净机 Docker 构建、视频画面人工确认）。

---

## 三、审查表（按模块）

> 列定义：①审查项（AUD-ID/名称/严重度）②对应赛题要求（REQ-ID/来源/类别）③当前实现与关键路径 ④是否完美满足要求（可证明状态+证据类型）⑤最优改进方案。
> 证据类型缩写：实测=本轮动态验证；静态=本轮代码通读；复核=独立子任务反证。

### A. 模块一：智能报告生成

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-M1-01 模板解析（Word 章节标题+动态占位符）·INFO | REQ-M1-01｜DOCX §5.1.1｜赛题强制 | `reports.normalize_template()`（reports.py:221）逐 XML 部件解析题包 docx，占位符打书签（YH_*），生成 placeholder_map.json（原文 unique/occurrences/语义映射）；`data_import.check_template` 兼容 Heading1 与中文编号两种标题形态并扫表格内占位符 | **满足**（静态+V6 实测渲染成功） | 建议保持；在当前约束与已验证范围内未发现值得实施的改进 |
| AUD-M1-02 六章节完整 ·INFO | REQ-M1-02｜§5.1.1｜赛题强制 | 模板六章节（含第五对标章）；`verify_docx`（reports.py:828）硬校验 headings==6、tables>=11、images>0、residual 占位符=0；V6 报告 13 页 PASS | **满足**（实测） | 建议保持 |
| AUD-M1-03~05 三类知识入库 ·INFO | REQ-M1-03/04/05｜§5.1.2｜赛题强制 | 题包 7 份 PDF 自动入库 + `competition_configuration/knowledge_supplement`（行情/基准转文本、异常处理记录、对标基线，2026-09-21 修复#7）+ 数据中心三类（产品/行业/企业内部）Web 上传入库（data_import.publish_knowledge→KNOWLEDGE_INGEST_DIR，文件哈希进知识版本指纹） | **满足**（静态+V4：11 源 180 块含补充目录） | 建议保持；企业内部知识依赖补充目录，若后续新增内部文档走数据中心上传即可 |
| AUD-M1-06 PDF/Word/TXT 格式支持 ·INFO | REQ-M1-06｜§5.1.2｜赛题强制 | `knowledge.parse_document`（knowledge.py:108）：PDF 按页(fitz)、DOCX 段落+表格、TXT 12 行块、JSON 记录；低文本质量记 LOW_TEXT_QUALITY;OCR_NOT_RUN 显式失败不冒充 | **满足**（静态+V4）；OCR 未实现但显式声明 | 建议保持：题包均为文本型 PDF，OCR 按需后置（标注于限制，不算缺陷） |
| AUD-M1-07 混合检索+来源标注 ·INFO | REQ-M1-07｜§5.1.2｜赛题强制 | jieba+FTS5 BM25 与 Chroma 向量（bge ONNX 本地）双路，候选先过产品/工厂/期间/规格/文档版本/上下文适用性过滤，RRF 融合（词法锚定 0.75/0.25 否则 0.5/0.5，固定权重不拟合金标）；LlamaIndex BaseRetriever 真实执行；每条证据带 source/location/applicability | **满足**（实测 V4） | 建议保持 |
| AUD-M1-08 三种分析主题 ·INFO | REQ-M1-08｜§5.1.3｜赛题强制 | `_months()`（metrics.py:49）：monthly/special 单月、quarterly 强制季末月且三月产量加权聚合（缺月不补零直接 NO_COMPLETE_PERIOD_DATA）；前端报告范围选择器联动季末月过滤；未装季度模板回退月度模板改写口径词 | **满足**（静态+测试套件） | 建议保持 |
| AUD-M1-09 模板+数据+RAG+模型四要素融合 ·INFO | REQ-M1-09｜§5.1.3｜赛题强制 | worker.process_job 链：固定快照→Knowledge.build 幂等→context_services.retrieve→generate（模型）→render_docx（模板+程序数字）→convert_pdf；V6 全链实测 | **满足**（实测） | 建议保持 |
| AUD-M1-10 双格式导出 ·INFO | REQ-M1-10｜§5.1.3｜赛题强制 | DOCX 渲染+LibreOffice headless 转 PDF（字体 fontconfig 指向内置 NotoSansSC），产物入 artifacts 表按哈希登记；Docker 镜像内置 LibreOffice | **满足**（实测 V6：docx/pdf 双 PASS） | 建议保持 |
| AUD-M1-11 专业排版（页眉页脚/表格/图表）·P3（视觉部分待验） | REQ-M1-11｜§5.1.3｜赛题强制 | 结构层可证：页脚 PAGE/NUMPAGES 域（rebuild_report_footer）、页眉模板水印保留、表格统一样式（灰底表头/跨页重复/列宽自适应 noWrap/红绿涨跌）、matplotlib 图表（中文字体/图几-几编号）、原生 TOC 域可跳转、数字-单位 NBSP 防断行；视觉实际效果（无遮挡/字体正常/换行）**待人工** | **部分满足**（结构=静态+实测；视觉=待人工，见 VISUAL_HANDOFF V-01） | 保持结构实现；视觉按 VISUAL_HANDOFF 逐页人工核验后收口 | 
| AUD-M1-12 3 场景结构完整度评测 ·INFO | REQ-M1-12｜§5.1.4｜赛题评测 | verify_docx 结构六项硬校验已在本轮 V6 单场景实测；历史上 release_20260918_5974275 存档七场景结构 PASS（开发者记录，非本轮重跑） | **满足**（本轮 1 场景实测+历史记录；未本轮重跑 3 场景） | 交付前用 `scripts/run_acceptance.py --private-scenarios` 对 3 个正式场景重跑一轮并绑定新 run_id |
| AUD-M1-13 归因人工评分 0-5 ·待验证 | REQ-M1-13｜§5.1.4｜赛题评测 | ReviewStore 只收真人署名评分，绑定产物哈希（内容变更自动过期）；AI 不能代签；assess_report 人工三维永 PENDING | **待人工**（机制已实测正常工作=评分缺失时保持 PENDING） | 按 VISUAL_HANDOFF V-02 由真人完成三场景评分 |

### B. 模块二：看板与归因

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-M2-01~04 数据层四组指标 ·INFO | REQ-M2-01..04｜§5.2.1｜赛题强制 | metrics.analyze：时间序列、环比（上月/上季）、同比（2025 同月）、预算偏差（同月预算），全部 Decimal；缺月/零分母显式 N/A+原因 | **满足**（实测 V2 81 项独立复算一致） | 建议保持 |
| AUD-M2-05 贡献度公式 ·INFO | REQ-M2-05｜§5.2.1｜赛题强制 | `contribution=Δ要素/Δ总×100`（metrics.py:19）；允许负值与超 100% 不裁剪；总变动为 0 → None+原因 | **满足**（实测） | 建议保持 |
| AUD-M2-06~09 ECharts 四图 ·INFO | REQ-M2-06..09｜§5.2.2｜赛题强制 | echarts/core 按需注册；趋势折线（近 6 月）、瀑布（透明底堆叠浮柱，web 版）/零线双区（报告版）、环形结构图；Chart 组件生命周期/ResizeObserver/dispose 正确 | **满足**（静态；渲染效果属视觉待验 V-03） | 建议保持 |
| AUD-M2-10 热力图（加分）·P3 | REQ-M2-10｜§5.2.2｜赛题加分 | `ProductMonthHeatmap`：产品×月份网格（要素下拉切换 all/材料/人工/制造费用，单位不一致拒绝共色标）+ `ElementHeatmap`：要素×口径环比热图；有 snapshot_id 缓存（修复#6） | **部分满足**：三维数据以"要素可切换的二维×2"覆盖，无单一三维交叉视图；系统文档已诚实标注此差距 | 可选：将 x=月份、y=产品、颜色=选定要素扩展为 ECharts heatmap 三维数据集单图（工作量小）；或保持现状并在方案文档明确"三维交叉以要素维度切换实现" |
| AUD-M2-11 模型生成可入报告的归因段落 ·INFO | REQ-M2-11｜§5.2.3｜赛题强制 | focus_analysis 确定性变化说明（±10%严格超限项）+ 报告链 narrative.generate 有界生成（模型只写 hypothesis/insufficient_evidence，数字程序绑定；行情/工艺证据+缺证清单+可执行建议）；V6 实测 model_live=true | **满足**（实测；"质量对标赛题合格示例"的最终判定属人工评分 V-02） | 建议保持 |
| AUD-M2-12 波动阈值 ±10% 严格超限 ·INFO | REQ-M2-12｜§5.2.3｜赛题强制 | `threshold_alert: abs(rate)>10`（metrics.py:27）；industry 路径复用同函数；dashboard.focus_analysis `<=10 continue`；复核子任务全仓扫描确认**无任何 ≥ 路径**，恰好 10.0% 不触发 | **满足**（静态+复核+实测边界） | 建议保持 |
| AUD-M2-13 归因方法论（额外功能）·INFO | 非——《归因方法评估》自加 | attribution.py：ADtributor 式 EP+JSD、二因子 Shapley、对照厂 DiD+安慰剂检验、行情价格传导（有界估计）、假设排序；全部确定性可单测，UNAVAILABLE 显式 | 满足（测试覆盖+前端实测调用）；系统自标"估计类输出显式标注假设" | 建议保持 |

### C. 模块三：对标三步法

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-M3-01 找差异（差异金额+差异率总览表）·INFO | REQ-M3-01｜TABLE2｜赛题强制 | metrics.benchmark：同产品同期、方向显式"左−右，以右为分母"、summary（单位成本/总成本/产量）+elements（三要素）差异额/率/占跨厂总差额贡献度；metric_refs 全量登记 | **满足**（实测：显式方向下与独立复算完全一致） | 保持；注意 AUD-BENCH-02 缺省方向易误读 |
| AUD-M3-02 拆结构（可下钻原材料）·INFO | REQ-M3-02｜TABLE2｜赛题强制 | 一厂侧有原料明细可下钻（materials_summary 排序+贡献度）；二厂仅有汇总——2026-09-22 起默认停用合成明细，结构归因到要素层为止，更深层以"证据支持假设/证据不足"输出，**不伪造二厂明细**；合成明细启用时全程标注 data_label | **满足（诚实口径）**：真实数据支持范围内的下钻完整；二厂明细缺失是题包事实而非实现缺口 | 建议保持；不建议重新默认启用合成明细 |
| AUD-M3-03/05 拆原因（RAG+模型，分段论述）·INFO | REQ-M3-03/05｜TABLE2/§5.3.2｜赛题强制 | /api/benchmarks：检索（产品工艺差异查询）→generate → benchmark 章节假设分条输出（claim_type 标注+缺证清单）；报告 5.3 章插入 | **满足**（静态+V6 同链路） | 建议保持 |
| AUD-M3-04 差异对比表含数据 ·INFO | REQ-M3-04｜§5.3.2｜赛题强制 | 差异总览表+要素结构表+报告 5.1 动态表（模板列结构） | **满足** | 建议保持 |
| AUD-M3-06 建议可转 RPA 指令 ·INFO | REQ-M3-06｜§5.3.2｜赛题强制 | Finding.recommendation 携带 suggestion/verification_target/expected_evidence/department/priority/deadline_basis；前端"载入当前报告建议"一键转任务草稿（实测链路 V3） | **满足** | 建议保持 |
| AUD-M3-08 差异计算误差≤1% ·INFO | REQ-M3-08｜§5.3.3｜赛题评测 | 本轮独立复算：两产品 delta/rate 与引擎小数级一致（相对误差 0%）；题包二厂数据本身即标准答案来源 | **满足**（实测） | 建议保持 |
| AUD-BENCH-01 对标页同步模型调用 ·P3 | 工程要求（可靠性/UX） | GET /api/benchmarks 在 sync 路由（线程池）内调 generate：首访可数分钟；有全版本指纹缓存+退避重试+确定性降级兜底；前端有等待秒数提示 | 部分满足（不构成可用性缺陷；属慢 UX）——复核子任务确认三重缓解齐全 | 最小改进：对标页默认 with 检索+确定性假设即时返回，模型解释改走报告队列异步补全（复用现有 focus_analysis 模式）；或保持现状并在 UI 标注首次等待 |
| AUD-BENCH-02 benchmark() 缺省方向 ·P3 | 工程要求（可维护性） | `metrics.benchmark(product,month)` 无参时 left=factories[1]（二厂）−factories[0]（一厂），与报告/worker 路径显式传入的"一厂−二厂，以二厂为分母"方向相反；API 层强制显式 left/right 故无用户可见错误 | 满足（用户路径无影响）；易在直接调用/新测试中误读——本轮审查脚本即中招 | 最小修复：`_benchmark_factories` 缺省改用 `benchmark_partner`（主数据 designated=二厂为基准），或在 docstring/返回 direction 首行标明缺省方向；验收：补一条方向断言测试 |

### D. 模块四：RPA 整改闭环

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-M4-01 结构化任务 JSON 五要素 ·INFO | REQ-M4-01｜§5.4.1｜赛题强制 | ExecutableAction 校验（标题/责任人 name+department/来源 analysis_type+month+product+finding/优先级枚举/截止日）+四项行动字段（核查对象/预期证据/责任角色/期限依据）；占位符残留整体拒绝 | **满足**（实测 V3 payload 字段齐全） | 建议保持 |
| AUD-M4-02/03 HTTP 发送与 200 判定 ·INFO | REQ-M4-02/03｜§5.4.2｜赛题强制 | 事务 outbox：确认→QUEUED→deliver_one POST /api/rpa/tasks；协议校验（code==200+status==sent+载荷逐字段匹配+回执证明）才置 SENT；协议错→对账查询不盲重发；SENDING 崩溃恢复走 reconcile；本地模拟服务回环强制（local_validation） | **满足**（实测 V3 对题包原版 mock） | 建议保持 |
| AUD-M4-04 发送状态+前端"已发送至XX" ·INFO | REQ-M4-04｜§5.4.2｜赛题强制 | notification_proven 校验"已发送至 X(Y)"回执或 sent 历史；前端任务卡显示 责任人·部门、模拟通知=SIMULATED_SENT、"送达不等于整改完成" | **满足**（实测） | 建议保持 |
| AUD-M4-05 任务追踪看板（加分）·INFO | REQ-M4-05｜§5.4.3｜赛题加分 | 企业任务看板三计数（已生成/模拟送达/责任人确认）按任务 ID 去重，确认须署名+时间；状态九态与人工确认分离 | **满足** | 建议保持 |

### E. 技术路线与加分项

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-T-01 OpenAI 兼容模型接入 ·INFO | REQ-T-01｜TABLE3｜赛题强制 | ModelGateway：openai/anthropic 协议、配置（显式→env→设置文件→默认）、厂商推理强度映射、1113 额度耗尽双端点切换（用户 2026-09-18 授权政策）、预算台账、身份核验、缓存版本指纹；V5 实测 PASS | **满足**（实测） | 建议保持 |
| AUD-T-02 RAG 框架+向量库 ·INFO | REQ-T-02｜TABLE3｜赛题强制 | LlamaIndex BaseRetriever 真实执行 + ChromaDB 持久化 + FTS5；非仅依赖声明 | **满足**（实测 V4） | 建议保持 |
| AUD-T-03/04 Web+ECharts+Python 后端 ·INFO | REQ-T-03/04｜TABLE3｜赛题强制 | React+Vite+ECharts 前端 / FastAPI 后端 | **满足** | 建议保持 |
| AUD-T-05 Dockerfile+一键启动 ·INFO（净机构建待实测） | REQ-T-05｜TABLE3｜赛题强制 | 两阶段 Dockerfile（LibreOffice+Noto CJK 内置）+三服务 Compose+桌面启动器；本地开发路径 bootstrap/start；README 双方式 | **满足（静态+历史记录）**；本轮未构建镜像 | 交付前净机执行一次 `docker compose up`（见 VISUAL_HANDOFF V-06） |
| AUD-T-06 知识图谱增强（加分）·INFO | REQ-T-06｜§6.2｜赛题加分 | graph.py 确定性抽取产品-药材-工序；检索时把所选产品药材/工序名补进 **BM25 查询词**（bm25_only 作用域，显式标 experimental/gain NOT_ESTABLISHED）；三维可视化前端；"图中关系不构成归因结论" | **满足（实现真实）**；检索增益未对照验证（系统自标） | 建议保持；增益对照属研究性工作，比赛阶段后置合理 |
| AUD-T-07 多模型协作（加分）·INFO | REQ-T-07｜§6.2｜赛题加分 | extraction/analysis 双路由（registry 档位限制+专属密钥+routes_status 回执）；import 映射/决策说明/向量适配评估走 extraction；未配置确定性回退不伪造 | **满足** | 建议保持 |
| AUD-T-08 Agent 自主决策（加分）·INFO | REQ-T-08｜§6.2｜赛题加分 | decision.py 确定性策略（报告缺失/快照过期/产物损坏三信号）+模型仅选信号+台账可回放+apply 幂等；产物健康联动 JobStore.artifacts_healthy | **满足**（策略确定性，评分文档自标"非模型自主规划"诚实） | 建议保持 |
| AUD-T-09 成本预测（加分）·P3（实验性自标） | REQ-T-09｜§6.2｜赛题加分 | forecasting.py Holt（v3 OLS 初始化修复）+朴素基线对照+一步 MAE+滚动原点留出评估+缺月不补+负值警告+实验性区间；前端全量披露 caveat | **满足（作为实验性加分项）**；区间覆盖率未验证（自标） | 建议保持实验性标注；勿在答辩宣称"经验证的预测能力" |

### F. 数据接入与数据质量

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-DATA-01 XLSX 公式单元格金额静默丢失 ·**P2** | 工程要求（正确性）＋REQ-U-04 | `_read_table` openpyxl `data_only=True`：无缓存值公式→空串→validate_business **静默跳过不报错**（data_import.py:310-317）；部分金额为公式→发布成功且该数据无声消失；全部为公式→VALID 通过后发布端才被 industry.register_enterprise 的 EMPTY_DATASET 拒绝（迟报），且企业目录文件已先写（孤儿目录）。赛题 CSV（文本）不受影响 | **不满足（该路径）**——复核子任务证实无任何兜底 | FIX-DATA-01：① `_read_table` 记录空单元格计数并在 validate 结果给出"第 N 行 X 列为空（公式无缓存值或漏填）"警告级提示；② publish 前若 cost_cells==0 或关键列空值率超阈值则 INVALID；③ 企业文件写入移到 register_enterprise 成功之后。验收：构造含无缓存公式单元格的 xlsx 反例，断言出现显式错误 |
| AUD-DATA-02 能力预览矛盾+发布顺序 ·**P2** | 工程要求＋REQ-U-04 | `_capabilities` 中 total_cost_analysis `available` 恒 True（data_import.py:353），amounts 空时显示"可用+无成本数据"自相矛盾；能力口径（有金额即可）宽于注册口径（costs 与 quantities 须同时非空）→用户按预览发布会撞 EMPTY_DATASET；publish_business 先写 facts/enterprise.json 再注册 | **部分满足**（预览误导真实可达，复核证实） | FIX-DATA-01（同根因合并修复）：available 改为 `bool(amounts)`，reason 语义对齐注册口径（缺产量时明示"发布需独立产量"）；发布顺序调整为注册成功后落盘。验收同上 |
| AUD-DATA-03 上传安全（类型/大小/路径/重复）·INFO | 工程要求（安全） | 50MB 上限、后缀×kind 白名单、内容哈希幂等、filename 不进文件系统路径（复核证实无穿越）、编码探测（utf-8-sig/gb18030/big5）、zip 检查（穿越/软链/压缩比/大小）仅用于知识 zip 场景 | **满足** | 建议保持 |
| AUD-DATA-04 行级错误定位 ·INFO | REQ（错误定位到行）｜工程 | 预览→映射→质检→发布四段；错误含 文件/工作表/行号/中文原因；产量冲突/金额重复/期间无法识别均带行号 | **满足**（除 AUD-DATA-01 的空单元格例外） | 随 FIX-DATA-01 补空单元格行级提示 |
| AUD-DATA-05 产量独立与防双计 ·INFO | 工程要求（口径正确） | 长表产量只独立计一次（seen_quantity_rows）；多文件合并优先级 汇总>预算>明细，同优先级冲突整体失败；industry.aggregate 产量是独立关系不随要素联接；层级 HIERARCHY_DOUBLE_COUNT/DETAIL_SUMMARY 双计数防护 | **满足**（静态+测试） | 建议保持 |

### G. 版本与企业隔离

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-ISO-01 数据快照与原子发布 ·INFO | 工程要求 | ingestion 哈希版本快照+临时目录+os.replace 原子切换；rejected 清单保留；load_rows 路径 confinement | **满足** | 建议保持 |
| AUD-ISO-02 上下文/任务/缓存键隔离 ·INFO | 工程要求 | AnalysisContext 冻结全部版本哈希；Knowledge namespace 按上下文分目录；任务 cache_key 含全版本指纹；检索 KNOWLEDGE_CONTEXT_MISMATCH；同文档多版本冲突证据整体排除 | **满足**（静态+测试） | 建议保持 |
| AUD-ISO-03 旧结果防误用 ·INFO | 工程要求 | worker 硬校验 CONTEXT/TEMPLATE/DATA_VERSION_CHANGED_RESUBMIT；soft/hard 版本键单一来源 versions.py；审核绑定产物哈希过期机制；决策按口径匹配报告 | **满足** | 建议保持 |

### H. 模型接入与安全

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-MODEL-01 anthropic max_tokens 不对称 ·P3 | 工程要求 | openai 8192 vs anthropic 2500（narrative.py:810） | 满足（当前仅用 openai 协议）；若切 anthropic 长解释可能被截断 | 最小修复：anthropic 分支 max_tokens 同读 PHARMA_MODEL_MAX_TOKENS |
| AUD-MODEL-02 密钥安全 ·INFO | 工程要求（安全） | 内联密钥写 RUNTIME/keys 受限文件、设置只存路径、对外只回显 key_set、覆盖参数 key_file 白名单 basename、非回环端点强制 https、跨厂商路由密钥隔离、错误信息不携带凭据 | **满足** | 建议保持 |
| AUD-MODEL-03 调用账本/预算/缓存诚实 ·INFO | REQ（缓存不冒充实调） | calls+call_attempts 双表、max_calls 预算、响应留档 model-response-*.json、身份核验 VERIFIED/MISMATCH、cache_hit 显式返回、model_live 需身份一致 | **满足**（实测 V5/V6） | 建议保持 |
| AUD-MODEL-04 提示注入防护 ·INFO | 工程要求（安全） | 文档"不可信证据"合同；引用白名单短句+适用性过滤；untrusted instruction 正则拒绝（忽略指令/system prompt/api key/curl/URL）；evidence_quotes 仅限 allowed_quotes 逐字 | **满足** | 建议保持 |

### I. 报告链与验收器

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-RPT-01 生成器/验收器协议一致 ·INFO | 工程要求 | verify_docx 用本次渲染占位符清单（2026-09-22 修复）逐书签核对数值绑定（≥70 项）+解释落位章节校验+残留占位符/重复单位检查；reference_report 路径合同自带 expected_bindings 下限（不硬编码）；验收器独立于生成器逐 claim 复核证据适用性 | **满足**（V6 计算一致 PASS） | 建议保持 |
| AUD-RPT-02 Word 兼容出厂闸门 ·INFO | 工程要求 | docx_compat：mc:Ignorable 前缀作用域校验（2026-09-22 lxml 事故根治）；所有 docx 出厂强制过闸 | **满足** | 建议保持 |
| AUD-RPT-03 TOC/孤行/页码回填 ·INFO | 工程要求 | 原生 TOC 域（无 dirty 标记，避免 Word/WPS 询问框）+LibreOffice 分页回填循环≤5 轮+孤行 keep-with-next；14/14 报告页码一致记录 | **满足**（V6 PDF 13 页转换 PASS） | 建议保持 |
| AUD-TPL-01 安装模板同比补绑定硬编码 ·P3 | REQ-U-04（模板接入） | install_template→_relayout_front_section 对"总成本概览"表 rows[4:7]/列 4-5 硬编码补占位符（题包表结构假设）；用户模板行序不同会写错单元格；check_template 不校验行序 | 部分满足（题包同构模板可用；异构模板有错绑风险） | 最小修复：补绑定时按表头文字定位（"去年同月/同比"列、材料/人工/制造费用行）而非索引；或行序不匹配时跳过补绑定并在安装回执标注。验收：构造行序打乱模板反例 |

### J. 前端

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-FE-01 页面/按钮/表单全接线 ·INFO | REQ-U-04/05 + §4.2 全景 | 10 个页面全部映射到真实 API（数据中心三页上传/预览/映射/解析、工作台四页分析/对标/报告/整改、模型配置三页设置/测试/切换）；无发现无效按钮或未接后端入口（27 文件逐一核对） | **满足**（静态）；浏览器交互待 V-03 | 建议保持 |
| AUD-FE-02 可访问性 ·INFO | 工程要求 | aria-label/role/alert/status/pressed 遍布；focus-visible 样式；Esc 关抽屉；reduced-motion；表单全部 label 包裹 | **满足**（静态） | 建议保持 |
| AUD-FE-03 竞态与陈旧结果 ·INFO | 工程要求 | AbortController 全覆盖+currentContext 守卫+快照 key 重挂载；自动解释入队按版本指纹幂等（重复浏览不重复计费）；失败态"重试"按钮 | **满足** | 建议保持 |

### K. 通用框架与扩展

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-GEN-01 行业可扩展性 ·INFO | REQ-D-07｜§十｜赛题加分说明 | 类型化事实合同（CostFact/QuantityFact/OptionalFact：scenario/scope/policy/version/grain）、受信策略仅代码注册、单位换算需证据（CONVERSION_EVIDENCE_REQUIRED，物理换算因子冲突拒绝）、政策桥、企业注册全量校验后原子写；机械/化工包共用核心验证迁移（默认不进正式目录）；数据中心免改码接入新企业实测 | **满足（通用框架真实）**；真实行业落地未证（自标） | 建议保持；不新增其他行业完整演示（符合 REQ-U-07） |
| AUD-GEN-02 制药特化不破坏通用性 ·INFO | REQ-U-06 | 公共核心无药名分支；制药术语/规则在 pharmaceutical 包（narrative_rules 经受信注册加载）；metric_contract 锁两路径共形 | **满足** | 建议保持 |

### L. 部署/CI/交付

| 审查项 | 赛题要求 | 当前实现 | 是否满足 | 最优改进方案 |
|---|---|---|---|---|
| AUD-DEP-01 Compose 三服务与健康检查 ·INFO | REQ-U-01/U-02 | web/worker/rpa；worker 就绪=心跳新鲜度（非进程存在）；web 健康=自身+worker 心跳；命名卷持久化；127.0.0.1 端口；密钥环境注入不落镜像；赛题原件只读挂载 | **满足**（静态；净机实测待 V-06） | 建议保持 |
| AUD-DEP-02 桌面启动器 ·INFO | REQ-U-02 | bat→ps1：Docker 定位（CLI→常见路径→WSL Ubuntu-20.04 集成+路径换算）、引擎自启等待 120s、compose up -d 幂等复用、就绪=worker 心跳+密钥状态披露、未装/未开/失败中文提示、启停状态日志菜单 | **满足**（静态+README 实测记录）；发行版名硬编码 Ubuntu-20.04 在换发行版时需改 | 可选：WSL 回退枚举 `wsl -l -q` 首个含 docker 的发行版而非固定名；其余保持 |
| AUD-DEP-03 CI ·INFO | 工程要求 | 双 workflow：应用回归（locked 依赖+pytest+前端构建+node 测试，空密钥无实调）与仓库契约；均 pinned action SHA | **满足**；**无 Docker 构建 CI 步骤** | 最小改进：application.yml 增加 `docker build` 步骤（不 push），防镜像漂移；工作量小 |
| AUD-DEL-01 代码公开仓库+一键启动 ·INFO | REQ-D-01｜TABLE4｜必交 | 远端可达（V9），README 双启动方式 | **满足**（可见性最终确认见 V-06 清单） | 建议保持 |
| AUD-DEL-02 技术方案文档五要素 ·INFO | REQ-D-02｜TABLE4｜必交 | docs/：architecture.md（mermaid 架构图）、rag.md+retrieval_contracts.md（切分/向量化/检索策略）、prompt_design.md、template_parsing.md、api_and_operations.md | **满足**（静态核对与实现一致） | 建议保持 |
| AUD-DEL-03 评测报告四指标 ·INFO | REQ-D-03｜TABLE4｜必交 | evaluation_report.md：四指标现状+来源+限界（历史存档绑定，competition_ready=false） | **满足**（诚实呈现）；三场景指标需新 run 绑定当前提交 | 交付前重跑 run_acceptance+verify 绑定 1f78b2f 系提交 |
| AUD-DEL-04 演示视频 ·INFO（画面待人工） | REQ-D-04｜TABLE4｜必交 | demo_20260920/yaoheng_full_demo_20260920.mp4（2分50秒≤5分钟，全流程顺序与赛题要求一致——README 记载；画面实际内容需人工确认 V-04） | **部分满足**（时长/流程顺序合规待画面人工核验） | 按 VISUAL_HANDOFF V-04 人工看片后收口 |
| AUD-DEL-05 决赛 PPT ·INFO | REQ-D-05｜TABLE4｜必交(决赛) | demo_20260918/药衡智析_演示与答辩稿.pptx 存在（10 页，README 记载需补实证页） | **满足（存在）**；内容与最新成果一致性待人工 | 人工核对 PPT 与 1f78b2f 能力清单一致 |
| AUD-LIC-01 开源标注与许可证 ·INFO | REQ-T-11｜§6.3｜赛题约束 | third_party_reuse.md 精确版本+许可证表（含 PyMuPDF AGPL 特别提示）、LICENSE_STATUS、字体 OFL | **满足** | 建议保持；注意 PyMuPDF AGPL 分发义务提示已记录 |
| AUD-SEC-01 数据保密边界 ·待验证（边界争议） | REQ-T-10｜§6.3｜赛题约束 | 完整题包数据已入公开仓库；团队持有用户 2026-09-18 明确授权记录（publication-authorization.md）；赛题同时要求"代码公开仓库"与"数据仅限大赛使用" | **待验证**：团队授权记录≠赛事方规则解释；建议向组委会书面确认"赛题模拟数据随公开代码仓库托管"是否被赛规接受 | 比赛前向官方 QQ 群书面确认并留证；若不允许则将题包转为私有子模块/发布包 |

### M. 测试与旧问题复验

| 审查项 | 要求 | 现状 | 判定 | 改进方案 |
|---|---|---|---|---|
| AUD-TEST-01 测试套件有效性 | 工程要求 | 隔离环境 **387 通过/1 跳过**（V1）；conftest 剥离开发凭据；抽查 metric_contract 反例注入、benchmark 合同、RPA 幂等测试写法独立（期望非同引擎生成）；本轮 81 项独立复算与套件结论一致 | **满足** | 建议保持；1 skipped 项建议标注原因 |
| AUD-TEST-02 历史风险复验（单位标注/检索范围/验收协议/模型路由/降级重试/损坏产物/分页/worker 就绪） | 旧审计清单 | 逐项静态复验：单位标注（metric_contract 锁两路径）✅已修；检索范围（适用性前置过滤+fix2 工厂贯穿）✅；验收协议版本化（generic-v2-role-bound）✅；模型路由贯穿（for_route 同源 fix4）✅；降级重试（retry 键+复用已验算）✅；损坏产物（artifacts_healthy+STALE 过期）✅；分页（SQL 内先过滤 fix7）✅；worker 就绪（心跳）✅ | **本版已修（8/8）** | 建议保持 |

---

## 四、缺陷汇总与修复顺序

**P0：0 项。P1：0 项。**

| 级别 | AUD-ID | 一句话 | 共享根因 |
|---|---|---|---|
| P2 | AUD-DATA-01 | XLSX 无缓存公式单元格金额静默丢失（部分丢失发布成功无提示） | FIX-DATA-01 |
| P2 | AUD-DATA-02 | 能力预览 available 恒真矛盾；发布先写盘后注册留孤儿目录 | FIX-DATA-01 |
| P3 | AUD-BENCH-01 | 对标页 GET 同步模型调用首访慢（有缓存/降级缓解） | — |
| P3 | AUD-BENCH-02 | benchmark() 缺省方向与报告路径相反，易误读 | — |
| P3 | AUD-TPL-01 | 安装模板同比补绑定按行/列索引硬编码，异构模板错绑 | — |
| P3 | AUD-MODEL-01 | anthropic 分支 max_tokens=2500 不对称 | — |
| P3 | AUD-KB-01 | knowledge.search 每次全量载入分块（题包规模无碍） | — |
| P3 | AUD-M2-10 | 热力图"三维交叉"以要素切换的二维实现（加分项部分满足，已自标） | — |

**推荐修复顺序**：
1. **FIX-DATA-01**（P2×2，一次改动同根因收敛）：空单元格行级提示 + available 语义修正 + 注册成功后落盘 + xlsx 反例测试。约 0.5–1 天。
2. AUD-TPL-01（表头文字定位补绑定）+ AUD-BENCH-02（缺省方向/文档）：各 <0.5 天。
3. AUD-MODEL-01、AUD-DEP-03（CI 加 docker build）、AUD-M2-10（可选三维单图）：小改。
4. 比赛收口动作（非代码）：三场景真人评分、视觉逐页核验、净机 compose 实测、视频画面人工确认、数据公开边界向组委会确认。

## 五、结论

**非视觉审查完成；比赛整体验收仍有列明的待验证项。** 在本轮可静态与隔离动态验证的范围内：赛题四大模块强制功能全部真实实现且数值经独立复算一致；技术栈与部署满足必选要求；加分项均有真实实现并诚实标注限界。未发现阻止关键流程或造成严重错误结果的问题。剩余缺口集中在人工环节（评分/视觉/净机实测/官方边界确认）与用户自导入数据的两个 P2 缺陷。

*本报告不构成获奖水平判断；覆盖与证据边界见 COVERAGE.csv 与 STATE.json。*
