# 药衡智析（yaoheng-zhixi）独立全量审查报告

- **审查日期**：2026-09-23
- **审查对象**：https://github.com/Lihuaaaa-F/yaoheng-zhixi @ commit **1f78b2f**（origin/main，全部 9 个特性分支已并入 main，0 提交领先——main 即最新成果）
- **审查方式**：portable/manual 模式执行 Trail of Bits `audit-context-building` + `spec-to-code-compliance`（技能 rev `32e34f81`，全文加载于 WSL 缓存目录，见 STATE.json）；辅助 Matt Pocock `codebase-design`（架构建议用语）。11 个互不覆盖的子代理分模块深读落盘（EVIDENCE/agent_*_findings.md），主审亲读核心引擎 8 文件并复核全部 P0/P1 发现（含动态复现、哈希重算、CI 配方核查）。**不冒充原生工作流，不冒充独立多代理复核**——跨发现反证由主审完成。
- **审查者能力边界**：审查者无视觉理解能力。本报告所有结论限于源码/文本/结构/元数据/隔离运行动态证据；凡涉版式美观、视频画面、PPT 渲染效果一律转 VISUAL_HANDOFF.md，未看即未判。
- **未提交改动单列**：主工作区另有 8 个未提交修改文件（api.py/reports.py/Analysis.tsx/App.tsx/Benchmark.tsx/DecisionCard.tsx/NarrativePanel.tsx/style.css，+223/-32）与若干探针脚本，**不在本次审查基线内**，见 STATE.json 清单。
- **动态验证**（隔离 worktree，详见 STATE.json）：后端 387 passed/1 skipped（CI 配方）；前端 npm ci+build 通过；独立数值对拍 11/11 零误差；P0 两项均动态/静态亲证。

## 一、总体判断

代码本体（尤其核心数值引擎与诚实性合同）质量显著高于常见参赛原型：Decimal 全程、公式版本化、来源哈希贯穿、降级诚实标注、数字纪律禁止模型改数、幂等与产物哈希闸门齐备，388 个测试实跑绿且红旗稀少。**当前最大的风险不在代码，而在两处**：①数据中心的业务数据自助导入把题包"元/盒"单位成本列当绝对金额发布（总成本错 4.5 万倍且校验零警告，本轮已动态复现）；②交付/评测证据链断裂——交付目录 6 份产物与 manifest 哈希零匹配、第三场景无回执、评测主文档停在两个 run 之前、人工 0-5 评分全 PENDING。前者直接违背用户"完善 Web 业务数据接入"要求，后者使赛题必交的评测报告无法支撑当前 HEAD 的任何结论。

非视觉审查完成；比赛整体验收仍有列明的待验证项（视觉与人工评分项见 VISUAL_HANDOFF.md）。

## 二、问题统计

| 级别 | 数量 | 编号 |
|---|---|---|
| P0 | 2 | AUD-IMP-01，AUD-DEL-01 |
| P1 | 5 | AUD-IMP-02，AUD-IMP-03，AUD-DEP-01，AUD-DEL-02，AUD-DEL-03 |
| P2 | 18 | AUD-IMP-04~07，AUD-REP-01，AUD-NAR-01，AUD-RAG-01，AUD-RAG-02，AUD-FE-01，AUD-FE-02，AUD-MDL-01(部署条件)，AUD-DEP-02~05，AUD-DEL-04，AUD-DEL-06，AUD-DEL-09，AUD-TST-02，AUD-TST-03 |
| P3 | 26 | 见各模块表（含 1 项待验证 AUD-IND-07） |
| INFO/满足项 | 30+ | 见各模块表（必须列出以证明覆盖） |
| 已反证排除 | 2 | "前端单测不在CI"（CI 实际运行 node --test）；"空库 /api/catalog 500"（实测 200，降待验证） |

状态口径：已确认=本轮实测或静态三头对死；待验证=静态线索成立但未能复现或需外部环境；待实测=需真实模型/Docker/人工。

## 三、按模块审查表（五列）

### 模块 A：核心数值引擎（主审亲读：metrics.py/attribution.py/dashboard.py/decision.py/forecasting.py/metric_contract.py/config.py）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| AUD-CORE-01【INFO】环比/同比/预算偏差 | REQ-M2-01（5.2.1 强制） | `metrics.analyze` Decimal 计算；缺月不补零（`_aggregate` 要求月集齐否则 None）；基期缺失/为0 显式 reason（metrics.py:42-46）；季度取季末月聚合3个月（:49-60） | **满足**（本轮实测：银黄 2026-06 三比较零误差） | 建议保持；在当前约束与已验证范围内未发现值得实施的改进 |
| AUD-CORE-02【INFO】贡献度公式 | REQ-M2-02（5.2.1 强制） | `contribution`=要素变动额/总变动额×100（metrics.py:19-22）；分母0/缺失→None+原因；负值与>100% 不裁剪；单位/总额双口径（unit_contribution/total_contribution+comparisons 全基期） | **满足**（本轮实测三要素 60.71/10.71/28.57 零误差） | 建议保持 |
| AUD-CORE-03【INFO】±10% 严格阈值 | REQ-M2-08（5.2.3 强制） | `threshold_alert`：abs(rate)>10 严格大于（metrics.py:27）；dashboard.py:56 同口径；alert_id 哈希去重；单位+总额双 basis 告警（:129-134） | **满足**（静态确认+边界=10 不触发有单测） | 阈值判断在 metrics.py:27 与 dashboard.py:52-56 双份维护（AUD-NAR-08），收敛为单点引用 |
| AUD-CORE-04【INFO】对标三步法数值 | REQ-M3-01/02/04、REQ-M3-06（5.3 强制，误差≤1%） | `benchmark()`：同产品同期配对、左−右差异金额+以右厂为分母的差异率、方向显式声明（metrics.py:354）；要素层拆解+贡献度；`benchmark_partner` 主数据指定优先+产品感知回退（:292-321） | **满足**（本轮实测：差异金额/率零误差；11/11 对拍通过） | 建议保持；评测对拍表需按赛题三场景逐项落表（归 FIX-B） |
| AUD-CORE-05【INFO】Agent 自主决策（加分） | REQ-B3（6.2 加分） | decision.py 确定性策略（4优先级：无终态报告/快照过期/产物损坏→REPORT_NEEDED）；模型仅选信号不可翻转决策（:117-147 身份+形状+信号白名单校验）；SQLite 台账可回放（:155-209） | **满足**（静态确认；策略版本化） | 建议保持 |
| AUD-CORE-06【INFO】成本预测（加分） | REQ-B4/D6（6.2 加分） | forecasting.py Holt(α=0.6,β=0.3)+OLS 初始化；滚动原点留出 MAE 对比上期值朴素基线（:71-84）；缺月/不足3点→INSUFFICIENT_HISTORY 不伪造（:109-116）；负预测点告警；CAVEAT 强制携带 | **满足**（静态确认；v3 留出误差实测记录在案） | 建议保持 |
| AUD-CORE-07【INFO】口径一致性 | REQ-E1（工程） | 单一确定性指标快照：API/图表/报告共用 metrics 产物；metric_contract.py 锁制药/通用双路径共有结构（核心键/单位/公式/N/A必带原因） | **满足**（静态确认；合同有专项测试） | 建议保持 |
| AUD-CORE-08【P3】材料贡献度分母耦合 | 工程 | `materials_summary` 分母取 `elements[0]`（metrics.py:255）——假设 ELEMENTS 首键为材料 | 部分满足（当前契约顺序成立；换契约静默错分母） | 最小修复：按 key 显式取材料要素而非下标0；验收：构造乱序契约测试 |

### 模块 B：数据接入与数据质量（agent-ingest 全读+主审亲证）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| **AUD-IMP-01【P0】自助导入量纲错误** | REQ-U4（用户要求：完善Web业务数据接入）；工程正确性 | 数据中心上传题包《成本汇总》/《预算》CSV：预设映射把 `直接材料(元/盒)` 等单位成本列按**绝对金额**入 facts（data_import.py:60-64,403-448）；`总成本(元)` 映射的 total_cost 角色不产 fact（:449-451 仅发要素）；下游 `industry.aggregate` total=Σ要素→**总成本=10.70元（真值481500元）**，校验 VALID 零警告。本轮已用题包真 CSV 经 UI 同款链路（_mapping_for→_options_for→validate→publish→analyze_reference）动态复现（EVIDENCE/repro_import_dimension.py） | **不满足**（本轮实测确认；静默错误结果） | FIX-A 最小修复：①映射角色带单位语义——(元/盒) 列发布时乘以行产量转金额（或映射为 unit 角色由聚合层换算）；②`总成本(元)` 落地为事实并在与 Σ要素不一致时硬失败；③发布前加不变量校验（与 AUD-IMP-02 合并实施）。验收：题包成本汇总导入后 analyze 的 total=481500、单位成本=10.70；篡改列值可被拦截。工作量：小（映射+校验约1天+测试） |
| **AUD-IMP-02【P1】自助导入缺 5 类不变量校验** | REQ-U4；工程要求（出题方数据合同） | `validate_business`（data_import.py:245-343）无"单位成本=三要素和、总成本=产量×单位成本、材料占比100%、5类费用=汇总制造费用、明细-汇总父子"校验（仅 ingestion 打包路径有）——正是 P0 漏过的原因 | **不满足**（静态确认：搜索无一命中算式） | 并入 FIX-A：把 ingestion.py 的不变量规则抽公共函数用于自助导入校验；违反→INVALID 带行定位。验收：构造违反逐条规则的 CSV 各被拒绝且错误指向行/列 |
| **AUD-IMP-03【P1】再发布非原子** | REQ-U4；工程（数据版本） | facts.json/enterprise.json 先写盘、register_enterprise 后验（data_import.py:452-464）；enterprise_id 由(企业名,pack)哈希定→同名重导覆盖同目录，注册失败时旧注册条目指向已覆盖数据（:720-732） | 部分满足（首次导入正确；重导+失败的组合破坏旧版本） | 最小修复：写临时目录→校验通过→`os.replace` 原子换名+注册表后写；或 enterprise_id 纳入数据哈希。验收：同名重导中途失败后旧上下文仍可分析 |
| AUD-IMP-04【P2】发布后归因异常→整批 PARSE_FAILED | 工程（状态诚实性） | import_pipeline.py:298-321：发布成功后归因概览阶段抛错→整批标 PARSE_FAILED/FAILED，但企业与数据实际已生效 | 部分满足 | 把归因概览失败降级为该批 warning（数据已发布的事实不变）；验收：模拟归因抛错，批次状态=PARSED+警告 |
| AUD-IMP-05【P2】上传记录永久卡 PARSING | 工程（可靠性） | api.py:311 入队即置 PARSING；worker 崩溃后 waiting 只认 UPLOADED/PARSE_FAILED（data_import.py:583），无复位端点 | 部分满足 | waiting 增补 PARSING 超时回收（心跳/时间戳判死）；验收：杀 worker 重启后卡住记录可被重新领取 |
| AUD-IMP-06【P2】同文件重复主键行仅告警累加 | 工程（数据质量） | data_import.py:320-322：同文件重复(factory,product,period)→warning 且金额累加（重导汇总行双计）；跨文件才硬失败 | 部分满足 | 同文件重复主键默认硬失败+显式"合并"选项；验收：重复行被拒 |
| AUD-IMP-07【P2】知识 docx 忽略表格 | REQ-M1-05（Word 格式支持） | publish_knowledge docx 只取段落（data_import.py:482-485），表格内容静默缺失（check_template 却专门扫表格） | 部分满足（正文入池；表格知识丢失） | 最小修复：docx 解析补表格文本（与 reports 渲染同法）；验收：含表格 docx 导入后可检到表格内文本 |
| AUD-IMP-08【P3】XLSX/CSV 边界组 | 工程 | XLSX 无缓存公式静默为空、sheet 静默回落首个；CSV 公式注入(=+-@)未消毒（无导出端点，现风险低）；50MB 限制在整读内存后 | 部分满足 | 低成本补：公式单元格计数告警+sheet 名透出+上传前大小检查前置；CSV 导出功能若上线必须先消毒。当前保持亦可接受（记录在案） |
| AUD-ING-01【INFO】ingestion 打包路径完备 | REQ-M2-01 等 | 竞赛主数据路径：全不变量校验+原子快照(os.replace)+可回滚+TOCTOU 复查+masterdata 哈希门禁（metrics.py:200） | **满足**（静态确认；正式演示不受 P0 影响） | 建议保持 |

### 模块 C：报告生成（agent-reports 全读 1660 行）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| AUD-REP-02【INFO】模板解析与占位符 | REQ-M1-01/02/03（5.1.1 强制） | 题给模板 101 唯一占位符（108 处）全量映射（EVIDENCE/agent_reports_findings.md 对照表）；章节 6 章全渲染；残留占位符三重防线（NA 兜底→verify 残留检查→PDF 文本扫描） | **满足**（静态确认） | 建议保持 |
| AUD-REP-01【P2】legacy findings 路径致任务 FAILED | REQ-M1-08 | explanation_presence 只认 3.1/3.2/3.3/5.3 四节（reports.py:525-548）；narrative.py:1013-1015 允许模型 legacy `{"findings":…}` 返回 section='summary'/'actions' → 校验失败→整任务 raise FAILED 而非降级。主路径（explanations，section 限定要素键+benchmark）不受影响 | 部分满足（窄触发：仅模型返回 legacy 形状） | 最小修复：explanation_presence 对 'summary'/'actions' 段落也建索引（正文任意位置匹配），或 legacy 路径强制 section 重映射；验收：构造 legacy 返回的集成测试不再 FAILED |
| AUD-REP-03【P3】固定文案章节 | REQ-M1-08（大模型分析文本） | "需关注问题"（reports.py:478）与 3.3"变动说明"（:404）为程序固定文案非模型文本 | 部分满足（结构在；"大模型生成"成分弱，人工评分可能扣分） | 模型可用时将这两处改为受合同约束的模型文本（数字仍程序拼装）；模型不可用维持现状并标注。验收：origin=model 文本出现在对应章节 |
| AUD-REP-04【P3】convert_pdf TOC 回填后未复检 | REQ-M1-09a | reports.py:919-920 `d.save(path)` 后未再跑 validate_word_compat | 部分满足（全 lxml 构造，前缀丢失根因不适用；防线缺口在） | 回填后再跑一次 validate_word_compat（毫秒级）；验收：篡改回填产物可被拦截 |
| AUD-REP-05【P3】verify_docx 自洽校验 | REQ-E4（测试有效性） | expected 用同一 build_bindings 复算（reports.py:809）——绑定公式口径错时验收双通过（能发现丢替换/舍入/残留/错位，不能发现口径错） | 部分满足 | 金标绑定表（手工独立算一组银黄 2026-06 的 8-10 个关键占位符期望值）作为第二验收源；验收：故意改坏 build_bindings 一个公式，金标测试变红 |
| AUD-REP-06【P3】normalize_template 硬编码段号 | 工程 | reports.py:234 硬编码 document.xml 段 235 替换 '100%'（已解包实证该段为贡献度合计单元格，双条件防误换） | 部分满足（当前模板正确；换版静默退化为字面 100%） | 改为按上下文文本定位（合计行+{{总环比}}邻接关系）；验收：用重排段落模板测试 |
| AUD-REP-07【待实测/INFO】贡献度展示口径 | REQ-M2-02 | 引擎双口径齐备（单位/总额），模板 2.2 表头为"金额(元/盒)"→报告绑定单位口径，与模板一致 | 待验证（赛题 5.2.1 字面"总成本变动额"，评测标准答案口径未知；产量不变月两口径相等） | 保持双口径输出；评测对拍时按标准答案口径选择展示列（FIX-B 一并确认） |

### 模块 D：LLM 叙事与降级（agent-narrative 全读 1099 行）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| AUD-NAR-02【INFO】数字纪律与降级诚实 | REQ-M2-07（5.2.3 强制） | numeric_fact 程序全文拼装（narrative.py:629-630）；告警数字程序前置；自由数字整体拒绝；四舍五入简写唯一匹配绑定留痕；缓存只在有模型产出时写；身份 MISMATCH 即 DEGRADED；origin/model_live/reader_status/页眉/验收五处一致标注；赛题"不合格例"会被两类合同拒绝 | **满足**（静态确认；最终质量待人工 0-5 评分） | 建议保持 |
| AUD-NAR-03【INFO】阈值告警自动重点分析 | REQ-M2-08 | 触发链完整：api.py:105-121→focus.job_id→前端轮询（agent-frontend 静态确认） | **满足**（静态确认；有模型环境实跑待实测） | 建议保持 |
| AUD-NAR-01【P2】检索未传文档版本 | 工程（版本隔离） | context_services.py:71-79 scope 无 document_version（knowledge.py:397 支持该参数但报告/对标两个调用点都未传）→被替代旧版文档单独命中时可被引为"适用" | 部分满足 | FIX-D：两个调用点补传当前知识版本；验收：旧版文档不再单独进入报告证据（多版本同命中排除逻辑已有） |
| AUD-NAR-04【P3】可用性探测与生成网关不一致 | 工程 | api.py:116 用 `ModelGateway()` 直构，生成用 `for_route('analysis')`——路由 env 指向别家时 focus 显示可用、实跑 MODEL_KEY_NOT_SET 降级（降级文案诚实，仅 UI 状态误导） | 部分满足 | 探测处改用 for_route 同源构造；验收：路由指向无钥端点时 focus 状态=NO_MODEL |
| AUD-NAR-05【P3】注入过滤正则偏窄 | 工程（提示注入） | narrative.py:978/610 过滤偏中文祈使句；反证：系统声明+7字段白名单+数字纪律+槽位 fail-closed 四层兜底压低危害 | 部分满足 | 补英文祈使模式（ignore previous/disregard 等）；低优先 |
| AUD-NAR-06【P3】DOCX 不区分实调 vs 缓存 | 工程（诚实性） | 报告页只有两档文案（reports.py:1474）；cache_hit 仅在结果 JSON/API 层 | 部分满足 | 页脚/元数据加第三档"缓存复用（生成于 <时间>）"；验收：缓存命中报告可辨识 |
| AUD-NAR-07【P3】缓存键不含 system prompt/effort | 工程 | narrative.py:955-956 缓存键缺 system prompt 全文；reasoning_effort 不进版本指纹（与 AUD-MDL-04 同根因，FIX-F） | 部分满足 | 并入 FIX-F：soft_items 增加 effort 项+缓存键纳入 PROMPT_VERSION 常量（已存在，确认覆盖 system 变更） |
| AUD-NAR-08【P3】阈值逻辑双份维护 | 工程 | metrics.py:25-27 与 dashboard.py:52-56 各写一遍"严格>10" | 部分满足（当前一致） | dashboard 改引 metrics.threshold_alert；验收：单点修改测试 |

### 模块 E：RAG 与知识库（agent-rag 全读）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| AUD-RAG-03【INFO】混合检索与来源标注 | REQ-M1-06（5.1.2 强制） | BM25(FTS5)+向量(chromadb) 加权 RRF(k=60, 0.75/0.25，权重披露且声明未拟合金)；真实 PDF 页码/DOCX/TXT 不造页；向量不可用→retrieval_status=DEGRADED 诚实降级不冒充混合；行情/基准 CSV 确定性查表优先（metrics.py:199/attribution.py:93） | **满足**（静态确认；召回质量待实测） | 建议保持 |
| AUD-RAG-04【INFO】知识图谱增强（加分） | REQ-B1 | graph.py 真实构建配方/工艺图谱并作 BM25 查询扩展（进 keyword_query，不改向量与适用性合同）；标注 experimental/gain=NOT_ESTABLISHED；图谱不作成本归因证据 | **满足**（加分项实现真实；收益未声称） | 建议保持 |
| AUD-RAG-01【P2】报告链知识库与交互库分裂 | REQ-M1-04（三类知识） | 报告/对标检索 `Knowledge(context=...)` 仅含 7 份题包 PDF；4 份补充知识（行情/基准/异常处理/对标基线）与用户上传知识只进交互式 /api/kb/search（knowledge.py:214, context_services.py:69）。反证：三类知识在报告链各有 PDF 路径、行情/基准数字走 CSV 确定性链路，故 P2 非 P1 | 部分满足（修复 #7 "入库"未覆盖报告链） | FIX-E：报告链 Knowledge 的 extra_dir 并入补充目录+用户知识（带来源标注）；注意防重复证据（去重按 evidence_id）。验收：异常处理记录内容可出现在报告引用 |
| AUD-RAG-02【P2】DEGRADED 构建知识静默过期 | 工程 | knowledge.py:360 任一解析失败→DEGRADED 快照永不替换 CURRENT；search 仅术语漂移/缺 CURRENT 时重建（:402）；worker.py:59 build() 返回值丢弃→源变更+部分失败组合下索引静默陈旧 | 部分满足（坏快照不替换好快照是故意设计；缺口在"源变化+部分失败"的静默性） | 最小修复：DEGRADED 时携带 per-file 失败清单并在 /api/kb 状态透出"索引落后于源 N 个文件"；验收：删一个 PDF 触发重建失败后状态可见 |
| AUD-RAG-05【P3】document_version 过滤空转 | 工程 | specification 无解析器写入（grep 0 命中）→过滤参数空转 | 部分满足 | 与 FIX-D 同批：解析入库时写版本元数据或移除空参数（防假象） |
| AUD-RAG-06【P3】embedding_version 恒报常量 | 工程 | knowledge.py:18,460 硬编码；反证：generation key 含 knowledge_version 内嵌真实模型指纹→不产生陈旧缓存，仅溯源标注失真 | 部分满足 | 从向量库实际指纹读取；低优先 |
| AUD-RAG-07【P3】向量切换回滚窗口 | 工程 | vector_switch.py:116-150 检索验证失败回滚后 CURRENT 仍指新模型索引；反证：下次 build() 幂等切回自愈 | 部分满足 | 回滚分支同步切回 CURRENT 指针；低优先 |
| AUD-RAG-08【P3】图谱节点共享/单位硬编码 | 工程 | graph.py:169-172 process 节点全局共享致跨产品工序顺序边污染（检索扩展只消费成分/工序边不受污染）；剂量单位硬编码 'kg'（题包处方表头实为 kg，当前数据无错标） | 部分满足 | process 节点加产品前缀；单位从数据读取；低优先 |
| AUD-RAG-09【未实现→标注诚实】OCR | REQ-M1-05（PDF/Word/TXT） | 扫描件 PDF 解析为空时显式 KNOWLEDGE_PARSE_EMPTY"扫描件需先OCR，系统不自动宣称成功"（data_import.py:494） | 不适用（赛题未要求 OCR；未实现但诚实标注，题包 7 PDF 均文本层可解析） | 建议保持现状；换含扫描件数据集前再评估 |

### 模块 F：模型接入（agent-models 全读）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| AUD-MDL-02【INFO】双通道+路由+身份 | REQ-T1（6.1 强制）、REQ-U5、REQ-B2（加分） | 云 API+本地 OpenAI 兼容端点；extraction/analysis/vector 三路由 7 消费点；连接测试真实短生成+身份回显；容器地址 host.docker.internal 白名单+提示；缓存/账本三表可区分实调/缓存/降级 | **满足**（静态确认；真实外呼待实测） | 建议保持 |
| AUD-MDL-03【INFO】密钥安全 | REQ-E3 | 密钥独立文件不入 JSON/DB；不回显前端；日志脱敏；测试桩全假钥；settings 读取白名单 | **满足**（静态确认） | 建议保持 |
| AUD-MDL-01【P2·部署条件】key_file 任意路径 | 工程（安全） | save_settings 仅查 is_file（model_settings.py:154）→可指任意本机文件；test_connection 将文件内容作 Bearer 发往用户配的 https 端点。反证：默认部署安全（compose 绑 127.0.0.1、token 可选默认关） | 部分满足（默认部署=P3；改暴露端口/配token=P2） | 最小修复：key_file 限定运行时密钥目录白名单；验收：指向外部路径被拒。若维持默认部署形态亦可后置，但需在部署文档写明 |
| AUD-MDL-04【P3】effort 不进版本指纹 | 工程 | 页面改 reasoning_effort 后实际请求变但同指纹任务命中旧缓存（narrative.py:955/api.py:178 env-only；gateway 本身含 settings 来源） | 部分满足 | FIX-F：versions.soft_items 增 effort；验收：改档后任务不命中旧缓存 |
| AUD-MDL-05【P3】网络错误零重试 | 工程 | Timeout/ConnectError 直接降级（narrative.py:856-858）；重试仅 429/5xx | 部分满足（延迟取舍合理但未文档化） | 补 1 次退避重试或至少在降级原因注明"网络错误（未重试）"；低优先 |
| AUD-MDL-06【P3】调用预算无重置 | 工程 | count 终身累计，满 40 次永久 MODEL_CALL_BUDGET_REACHED（narrative.py:802；grep DELETE FROM calls 无命中） | 部分满足 | 提供 reset 端点或按日滚动窗口；低优先（演示前手动清库亦可，写进运行手册） |
| AUD-MDL-07【P3】overrides 带 vendor 即 500 | 工程 | FIELDS 含 vendor 但构造器无该形参（model_settings.py:31 vs narrative.py:668/767）；前端只发 4 字段不触发 | 部分满足 | 构造器补参数或 FIELDS 去除；低优先 |

### 模块 G：通用框架与行业扩展（agent-industry 全读）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| AUD-IND-02【INFO】通用性分层真实 | REQ-X1（加分）、REQ-U6/U9 | 单后端多行业包，无复制后端；chemical 第4要素 energy 纯配置生效（有测试）；模板章节随包变化；上下文全链隔离；需改码项（驱动策略/叙事钩子/映射预设/多术语表）已列明 | **满足**（静态确认+golden 独立核算一致） | 建议保持 |
| AUD-IND-01【INFO】二厂明细诚实处理 | REQ-M3-02、用户要求（不伪造二厂明细） | 合成明细默认停用（config.py:29-31 显式 env 才启用）；停用时对标"拆结构止于要素层+证据支持假设表述"（metrics.py:350-353）；启用时四层合成声明齐全 | **满足**（静态确认） | 建议保持 |
| AUD-IND-03【INFO】演示数据边界 | REQ-U7、REQ-C1 | chemical/mechanical 仅 tests 引用、默认不可达；竞赛数据授权记录在案 | **满足**（静态确认） | 建议保持 |
| AUD-IND-04【P3】导入要素 id 单复数不一致 | 工程 | 导入企业 element_id=material（单数）vs 包 elements 键 materials（复数）→要素名回退英文 id（data_import.py:60+industry.py:696；有测试断言该行为为有意） | 部分满足（纯显示层） | 发布时映射到包规范键或包侧做别名；低优先 |
| AUD-IND-05【P3】导入企业误标"合成演示" | 工程 | 导入企业（真实数据）快照 limits/data_label 取 pack.data_label（industry.py:621,710,730-733）——真实数据被保守标为合成 | 部分满足（方向保守但误导评委） | 导入上下文单独 data_label="用户导入数据"；演示前修复（若评委查看导入数据报告） |
| AUD-IND-06【P3】解析流水线硬编码制药包 | REQ-U6 | import_pipeline.py:298-299 固定发布 pharmaceutical；旧 API 仍收 pack_id | 部分满足（与 U7"演示仅制药"一致；跨行业接入需改码，已在扩展边界文档口径内） | 后置（跨行业 UI 接入属新需求，按 ADR-0004 演进） |
| AUD-IND-07【P3·待验证】空库 catalog 500 | 工程 | agent 静态推演 selected_context→None.split（api.py:75-77+industry.py:615）；主审 TestClient 实测默认路由 200（题包上下文兜底） | 待验证（默认部署未复现；极端状态难构造） | 若复现：context_catalog 空时返回显式错误码；先留档 |

### 模块 H：API、任务与 RPA 闭环（agent-api 全读）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| AUD-API-01【INFO】整改任务生成与生命周期 | REQ-M4-01（5.4.1 强制） | LLM findings→服务端组装 RPA 字段规范逐项对齐（narrative.py:315-336）；人工确认门；幂等（business_hash/版本指纹 cache_key UNIQUE）；outbox SENDING→reconcile 不盲重发；job 检查点续跑 | **满足**（静态确认） | 建议保持 |
| AUD-API-02【INFO】RPA 调度与微信回执 | REQ-M4-02/03（5.4.2 强制） | POST→127.0.0.1:8090（与赛题约定一致）；HTTP200+code200+远端回显逐字段匹配+status=sent+微信回执四重判定（actions.py:233-243）；notify_status 落库+前端"已发送至XX责任人"；8 态区分 SENT/ACCEPTED/DELIVERY_UNKNOWN 送达≠整改完成 | **满足**（静态确认+单测故障注入；实发待实测） | 建议保持 |
| AUD-API-06【INFO】路由全景 | 工程 | 52 条路由统一错误体（ValueError→422/KeyError→404）；分页仅 /api/jobs（context 过滤+limit≤500）；路径穿越三重防线（DB 索引+is_relative_to+哈希）；上传文件名不进路径 | **满足**（静态确认） | 建议保持 |
| AUD-API-03【P3】FAILED/CONFLICT 任务死端 | 工程 | actions.py:133,143,249：终态失败任务同内容无 delete/reset 路由（grep 0 hits），仅改字段绕过 | 部分满足 | 增加"作废重开"端点或允许同内容强制重试（带确认）；低优先 |
| AUD-API-04【P3】设 token 后自带前端全 401 | 工程 | api.py:22 X-API-Token 中间件可选；前端无 token 机制（grep 0 hits）；默认关闭不影响演示 | 部分满足 | 文档写明"启用 token 需配反代注入"；或前端加 token 输入；低优先 |
| AUD-API-05【P3】杂项 | 工程 | _recalc_acceptance 读改写无事务（终态唯一写者，GET 重算可收敛）；_reject_active_parse 仅扫最近60条+TOCTOU（单 worker 串行，需≥60任务间隔）；/api/benchmarks month 无 pattern 校验（下游有兜底） | 部分满足 | 各自低成本补齐（事务包裹/全量扫描/正则校验）；低优先 |
| AUD-API-07【INFO】worker 就绪与恢复 | 工程 | manage.py 心跳门控+冷启动顺序 rpa→api→worker；try/finally 停 dispatcher；文件锁单例；/health 含 worker.alive（心跳<180s）语义正确 | **满足**（静态确认） | 建议保持 |

### 模块 I：前端（agent-frontend 全读 27 文件）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| AUD-FE-03【INFO】看板四图与竞态防护 | REQ-M2-03/04/05/06 | ECharts：近6月单位成本折线（含预测带）、瀑布图（环比/同比/预算三口径）、环形结构图、产品×月份×要素热力图（后端固定近6自然月 dashboard.py:97）；全数据流 AbortController+aborted 检查；单位一致性守卫 | **满足**（静态确认；渲染效果待视觉） | 建议保持 |
| AUD-FE-04【INFO】RPA 前端闭环 | REQ-M4-03/04 | 人工确认门+payload_hash；三统计看板（已生成/已送达/确认） | **满足**（静态确认） | 建议保持 |
| AUD-FE-09【INFO】可访问性基线 | 工程 | label 全覆盖、aria-pressed/current、focus-visible、reduced-motion | **满足**（代码层可证明部分） | 弹窗焦点圈闭与图表键盘替代见 AUD-FE-07 |
| AUD-FE-01【P2】报告/整改页快照陈旧 | 工程 | 分析 effect 以 isAnalysisPage 为闸（App.tsx:81），此二页改筛选不重取 snapshot；生成按新 selection 提交但任务卡默认按旧 snapshot_id 过滤（ReportGeneration.tsx:16-17,32）→新任务默认列表不显示 | 部分满足（勾"查看历史"可见；回分析页恢复） | FIX-G：任务列表过滤键改用当前选择参数（factory/product/month/type）而非 snapshot_id；或进入报告页时强制重取。验收：改产品→生成→任务卡默认可见 |
| AUD-FE-02【P2】e2e/demo 脚本半数陈旧 | 工程（回归能力） | e2e-context/e2e-live/record-demo/record_full_demo_20260920 引用三模块改版前选择器，当前 UI 首步即超时；e2e-dashboard/e2e-knowledge-graph 用现行选择器正常 | 部分满足 | 演示录制前刷新脚本选择器（对照 e2e-dashboard 写法）；或明确废弃旧脚本删除入口 |
| AUD-FE-05【P3】图表边界 | 工程 | 瀑布图 yoy/budget 缺 comparisons 渲染全零平桥而非 N/A（Analysis.tsx:46-48）；趋势图 yAxis min:0 截断负值预测点（:63，表格保留负值+警示） | 部分满足 | 缺比较期→显式"无可比期"；yAxis min 仅在最小值≥0 时设置；低工作量 |
| AUD-FE-06【P3】kb READY 无 sources 误导 | 工程 | 非竞赛上下文 /api/kb READY 无 sources，前端只认 PASS→显示"0份来源/索引需复核"（Evidence.tsx:12） | 部分满足 | 前端按 sources 为空单独文案"该上下文无知识源"；低优先 |
| AUD-FE-07【P3】焦点圈闭/键盘替代 | 工程 | 弹窗无焦点圈闭；图谱/图表 tooltip 无键盘替代 | 部分满足 | 低优先渐进补 |
| AUD-FE-08【P3】granular 导入端点无 UI | REQ-U4（错误行定位体验） | /imports/{id}/mapping\|validate\|publish\|template-check 前端零调用（本轮 grep 复核确认）；UI 走一键 parse 全流水线，失败仅显 parse_error 前120字 | 部分满足（主流程在；行级定位 UI 未实现——后端能力已具备） | 校验错误行表在 ImportWorkflow 渲染（后端已返回 errors 带行号）；演示前可选 |

### 模块 J：Docker/Compose/启动器/CI（agent-deploy 全读+主审核查）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| AUD-DEP-07【INFO】部署正面项 | REQ-T5/D1a、REQ-U1 | /health 语义正确（Web存活≠业务就绪）；.dockerignore 白名单精简（题包原件5.5MB不进上下文）；卷持久化+心跳门控顺序；worker 强杀后非终态 job 自动重跑；密钥仅文件路径注入；端口默认 127.0.0.1；action pin SHA | **满足**（静态确认；实机待测） | 建议保持 |
| **AUD-DEP-01【P1】requirements.lock 缺 openpyxl** | REQ-T5（一键启动可靠性） | CI/bootstrap 按 lock 安装（application.yml:36）；lock 129 行 0 命中 openpyxl、requirements.txt 有→lock 环境"数据中心 xlsx 导入"ImportError（data_import.py:192 懒加载）；check_dependencies 探针不含它、测试无 xlsx 用例→CI 绿是覆盖假象。本轮 grep 亲证 0/1 命中 | **不满足**（对 lock 部署链路） | FIX-C：openpyxl 补入 requirements.lock（版本对齐 requirements.txt）；Docker 镜像装 requirements.txt 反而可用但与 CI 分叉（见 AUD-DEP-02）。验收：lock 新环境 `pip install -r requirements.lock && python -c "import openpyxl"` 通过+补一条 xlsx 上传单测 |
| AUD-DEP-02【P2】Dockerfile 用 txt 非 lock+镜像源空许 | 工程 | Dockerfile:39-40 用 requirements.txt（范围约束）→镜像不可复现且与 CI 依赖集分叉；compose 注释称"配国内镜像"但无 pip/npm 镜像配置（仅 apt 换源；grep PIP_INDEX_URL/.npmrc 0 命中） | 部分满足 | FIX-C：Dockerfile 改 `pip install -r requirements.lock`；国内源要么真配要么删注释。验收：两次构建依赖集一致 |
| AUD-DEP-03【P2】bootstrap.sh CRLF | 工程 | 以 CRLF 提交（git i/crlf）→原生 Linux 按 README"方式二"必败；Git Bash 可跑（cygwin 剥 CR）掩盖 | 部分满足 | 最小修复：文件转 LF+.gitattributes 强制 eol=lf；验收：`bash bootstrap.sh` 在 Linux 容器内可跑 |
| AUD-DEP-04【P2】容器 root+无资源限制 | 工程 | Dockerfile 无 USER；compose 无 deploy.resources | 部分满足（本地演示风险低） | 加非 root 用户与基础 limits；演示前可选 |
| AUD-DEP-05【P2】CI 零部署面覆盖 | 工程 | CI 不构建镜像、不跑 docker compose config——本地一键启动走 compose 而 CI 不触碰 | 部分满足 | CI 加 `docker build` + `docker compose config -q` 两步（不跑容器，分钟级）；验收：compose 语法破坏时 CI 红 |
| AUD-DEP-06【P3】启动器边界组 | REQ-U2 | launcher.ps1:39 硬编码 Ubuntu-20.04（他发行名→误导"未装Docker"）；WSL 引擎未运行时补救动作无效；首启 embedding 同步下载（数百MB）+150s/180s 超时叠加慢网走失败提示（可恢复）；Dockerfile 无 CMD（裸 docker run 退出）；升级路径缺失（拉新版双击仍跑旧镜像） | 部分满足（主链路 Windows+Docker Desktop 静态一致） | 发行名改探测（wsl -l 解析）；加 `docker compose build` 的"更新"入口；低风险渐进 |
| AUD-DEP-08【待实测】中文/空格路径全链路 | REQ-U2 | bat→ps1→compose→WSL /mnt 换算静态核对未发现穿越问题，但未在真实 Windows+Docker Desktop 实测 | 待验证 | 净机实测（VISUAL_HANDOFF 收录操作步骤） |

### 模块 K：测试有效性（agent-tests 全读 38 文件+主审实跑）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| AUD-TST-01【INFO】总体有效性 | REQ-E4 | 38 文件 388 用例实跑 387 绿；全局无 skip 造假/assert True/except:pass；篡改式负例、真实并发 Barrier、故障注入（超时/断网/429/重启）普遍；手写金标算术存在（3600/120/30 等）；conftest 隔离干净；桩污染已代码级根治（complete_with_artifacts 护栏） | **满足**（高于平均水准） | 建议保持；两处系统性弱点见下 |
| AUD-TST-02【P2】PDF 真渲染测试无处执行 | 工程 | test_report_layout_direction.py:195 唯一 skip（LibreOffice unavailable）——CI ubuntu-24.04 未装 LibreOffice（workflow 无安装步骤，本轮核查）→该测试在任何环境都未跑过 | 部分满足 | CI 加 `apt-get install libreoffice`（或容器带 LO）使该测试真执行；验收：CI 日志显示该测试 passed 非 skipped |
| AUD-TST-03【P2】数值链中段自洽重算 | REQ-E4 | test_industry.py:375-408 用引擎自产分子分母复算 display——numerator 算错不报警；raw→numerator 有手写金标+变异注入双缓解，风险收窄到"题包要素层算术仅 metric_contract 引擎自检一层" | 部分满足 | 补题包真实数据的独立金标（本轮 EVIDENCE/repro_numeric_independent.py 的 11 项可直接转测试：expected 硬编码独立推导值）；验收：故意改坏贡献度公式该测试变红 |
| AUD-TST-04【P3】杂项 | 工程 | record_demo mjs 一处近恒真断言（:410）；reload 型 fixture 全局污染面（均带 try/finally 未发现误绿）；synthetic_rpa.py/locks.py 零引用（synthetic_rpa 为本地 RPA 模拟器仅 runtime 引用、locks 有 worker 单例语义——确认非死代码但无直接单测） | 部分满足 | 恒真断言改实质断言；低优先 |
| AUD-TST-05【INFO·已反证】"前端单测不在 CI" | 工程 | agent 报 R0/P1；主审核查 application.yml:41 CI 明确运行 `node --test frontend/record_demo_20260918.test.mjs`——**该发现不成立** | 满足（CI 覆盖在） | 无需动作（已反证，记录防再犯） |

### 模块 L：交付物、评测与文档（agent-delivery 全读+主审哈希对拍）

| 审查项 | 对应赛题要求 | 功能及实现方法 | 是否完美满足要求 | 最优改进方案 |
|---|---|---|---|---|
| **AUD-DEL-01【P0】交付证据链断裂** | REQ-D3、REQ-M1-10、REQ-M3-05（必交评测报告） | delivery_20260921/ 现有 10 文件（3产品×docx+pdf+audit）与 manifest.json（run=delivery_20260921, commit=ded9267）记录的 6 个 docx/pdf 哈希**零匹配**（本轮 sha256 亲证）；S3 板蓝根从未进入 manifest/verification/current_run；产物是 ded9267 后 24 提交重制的但回执未刷新 | **不满足**（评测报告无法支撑当前产物） | FIX-B：在 HEAD 重跑三场景交付+评测流水线，重新生成 manifest/verification/评测文档并使场景编号三处（scenarios.json/current_run/CSV）统一；验收：逐文件 sha256 对拍全 MATCH、S1/S2/S3 齐备 |
| **AUD-DEL-02【P1】交付物早于重大修复** | REQ-D2/D3 | 交付报告生成于 29377b6，早于 Word 损坏根治 4c63335、TOC/版式修复 a5b06d3/09b2ba2、确定性归因引擎 6b9a8b8；docs/数据全流程_20260922 以新引擎为叙述基础→方法论与交付物不一致 | **不满足**（交付物不代表当前能力） | 并入 FIX-B：HEAD 重制全部交付产物；旧目录加"已被 <新run> 取代"README 头 |
| **AUD-DEL-03【P1】评测报告三缺口** | REQ-D3、REQ-M1-11、REQ-M3-05/06 | ①评测主文档停 0919（声称 run=5974275，落后 current_run 两个 run、HEAD 51 提交）；②人工 0-5 评分 CSV 全 PENDING（赛题硬性人工评分未做）；③三场景仅 2 个有回执且场景编号三处互斥；差异≤1% 黄金值仅覆盖合成行业包，赛题三场景无逐指标独立对拍表 | **不满足**（评测报告要素缺） | FIX-B：HEAD 重跑+人工评分执行（VISUAL_HANDOFF 列评分材料）+三场景逐指标对拍表（可复用本轮独立复算脚本方法学） |
| AUD-DEL-04【P2】prompt 文档滞后 | REQ-D2 | prompt_design.md 自称 v18/校验 v9，代码实际 v21/v10（narrative.py:28-29） | 部分满足 | 文档同步 v21/v10 并加"版本以代码常量为准"注记 |
| AUD-DEL-06【P2】许可证未决 | REQ-C2（开源标注） | 无根 LICENSE（自有代码许可未决，LICENSE_STATUS.md 如实披露）；PyMuPDF AGPL-3.0 分发影响未决（third_party_reuse.md 已警示） | 部分满足（披露诚实；比赛代码公开仓库建议加 MIT/Apache 根 LICENSE） | 补根 LICENSE（团队决定许可种别）；PyMuPDF 分发路径评估（服务分发 vs AGPL 义务）；验收：LICENSE_STATUS 与实际一致 |
| AUD-DEL-09【P2】视频/PPT 绑定旧提交 | REQ-D4a、REQ-D5 | 视频绑定 03a5a30、verification media_freshness=PENDING、录制时报告为缓存命中（回执如实）；PPT 自 0918 未刷新且 README 自认缺三场景结果页；169.8s≤5min 合规、回执流程覆盖五环节 | 部分满足（时长/流程合规；绑定陈旧+画面未人工看过） | 并入 FIX-B：交付链刷新后重录；PPT 补三场景结果页并绑定新数据 |
| AUD-DEL-05【INFO】数据边界合规迹象 | REQ-C1、REQ-U8 | 授权记录/合成标注/停用开关齐备；07_交付 业务报告与测试数据隔离护栏在 | **满足**（静态确认） | 建议保持 |
| AUD-DEL-07【待验证】GitHub 公开可见性 | REQ-D1b | 本审查经 SSH 访问；匿名 HTTP 可见性未测 | 待验证 | 浏览器无痕访问 github.com/Lihuaaaa-F/yaoheng-zhixi 确认 public |
| AUD-DEL-08【INFO】技术方案六要素一致 | REQ-D2 | 架构/RAG流程（BM25+RRF k=60、0.75/0.25、bge-large-zh MIT）/模板解析/API 文档 21 路由抽查 8/8 与代码一致 | **满足**（抽查口径；prompt 版本滞后单列） | 建议保持 |

## 四、共享根因与修复包（FIX-ID）

| FIX | 根因 | 覆盖审查项 | 推荐顺序 |
|---|---|---|---|
| **FIX-A 导入单位语义与不变量** | 角色映射无单位维度+校验缺数据合同 | AUD-IMP-01(P0)/02(P1)/06(P2) 部分 | **第1**（比赛数据接入可信度的根） |
| **FIX-B 交付与评测证据链重建** | 交付产物重制后回执/评测/媒体未刷新 | AUD-DEL-01(P0)/02(P1)/03(P1)/09(P2)、REP-07 对拍口径 | **第2**（赛题必交物） |
| **FIX-C 依赖锁定一致性** | txt 与 lock 分叉+镜像源注释空许 | AUD-DEP-01(P1)/02(P2) | **第3**（半天内可完成） |
| FIX-D 检索版本过滤 | scope 未传 document_version | AUD-NAR-01(P2)/RAG-05(P3) | 第4 |
| FIX-E 报告链知识库统一 | 双 Knowledge 构造入口 | AUD-RAG-01(P2) | 第5 |
| FIX-F 指纹/缓存键完整性 | effort 与 system prompt 不进键 | AUD-MDL-04/NAR-07(P3) | 第6 |
| FIX-G 前端快照刷新 | 报告/整改页分析 effect 闸门 | AUD-FE-01(P2) | 第7 |

其余 P3 项独立小修，按模块表"最优改进方案"列执行；均为低风险局部修复，无需架构变动（符合 REQ-U9 复用约束）。

## 五、推荐修复顺序（比赛视角）

1. FIX-B（评测/交付证据链——必交物当前不可用）与 FIX-A（数据导入 P0）并行启动；FIX-C 半天顺手完成。
2. 演示前：AUD-IND-05（导入企业误标合成）、AUD-FE-01（任务卡不可见）、AUD-DEP-06 启动器发行名探测。
3. 人工 0-5 归因评分执行（AUD-DEL-03②，需真人，材料见 VISUAL_HANDOFF）。
4. 其余 P2（IMP-04/05/07、REP-01、RAG-02、DEP-03/04/05、DEL-04/06、TST-02/03）按赛程余量排期；P3 项赛后清理亦可。

## 六、要求覆盖统计

- 赛题强制项（含交付评测）：REQ-M1/M2/M3/M4/T/C/D 共 **42 条**——满足 30、部分满足 9（M1-04/08/10、M3-02/05、M1-11 不满足计入部分/不满足列）、不满足 2（M1-11 人工评分 PENDING、D3 评测断链）、待人工视觉 2（M1-09b、D4a 画面）
- 赛题加分项：6 条（M2-06 热力图、M4-04 看板、B1 图谱、B2 多模型、B3 Agent、B4/D6 预测）——**全部实现且静态确认**，另 X1 扩展性满足
- 用户确认要求：9 条——满足 7、部分满足 1（U2 启动器边界）、不满足 1（U4 业务数据导入因 P0）
- 工程要求：4 条——满足 3、部分满足 1（E4 测试有效性两处系统性弱点）

## 七、本轮不能下的结论

1. "具备一等奖竞争力"——人工归因评分（0-5）尚未执行，交付评测链断裂未修复前无法评估。
2. 报告版式"专业排版"最终成立——需真人打开 Word/PDF 查看（结构层已确认）。
3. 演示视频"完整展示端到端流程"——录制脚本与回执合规，但画面未经人工审阅。
4. 一键启动在净机 Windows 的实际成功率——部署链静态一致，未实测。

以上对应 VISUAL_HANDOFF.md 全部条目。

## 八、证据索引（EVIDENCE/）

- brief_original_extract.txt / report_template_extract.txt —— 赛题原文与模板全文提取（带段落定位）
- agent_{api,reports,narrative,ingest,rag,models,industry,frontend,deploy,tests,delivery}_findings.md —— 11 模块逐函数/逐要求详证
- symbols_backend.txt —— AST 符号清单（479 函数）
- repro_import_dimension.py —— P0 量纲复现（含输出）
- repro_numeric_independent.py —— 独立数值对拍（11/11 零误差）
- file_list.txt —— 539 文件全清单（COVERAGE.csv 数据源）
