# 2026-09-19 后端与行业核心只读审计

## 基线、范围与证据强度

- 审计对象：`Lihuaaaa-F/yaoheng-zhixi` 分支 `codex/core-industry-20260917`，固定提交 `cdd9cb90d1f2e38fac429e82d89e46765e2317d2`。已核验新 worktree HEAD；没有用旧 `acc4693` 代码冒充最新版。
- 应用根：`药衡智析_增量源码交接/public_source_candidate`。以下后端行号均相对其 `05_原型/backend/pharma/`。已读适用 `AGENTS.md`、README、`docs/current_run.json`、`docs/implementation_status.md` 与行业 ADR 0004。
- 已读本轮 `industry/industry_rules/metrics/ingestion/knowledge/narrative/forecasting/decision/graph`；API、actions、jobs、worker、reviews 的专项核验见 `api_backend_notes.md`。没有把只读代码核验写成全应用测试。
- 已执行 `backend_repro.py`：直接导入新 worktree 的真实函数及 Pydantic 模型，用独立 namespace 和替换后的 config 隔离运行状态，httpx 为不可联网替身。机械示范反例使用仓库自带合成数据，其余使用独立合成输入。原数据、业务源码与交付物均未修改。
- API 专项执行 `api_isolated/repro.py`：真实状态存储类、隔离 SQLite 和合成文件，假 HTTP；审核函数使用固定 ref 原始 AST。没有模型调用、真实 RPA 发送、密钥读取或文件删除。
- 环境副作用披露：首次从 worktree 导入函数时，Python 自动生成 `pharma/__pycache__` 下 7 个 `.pyc`；未改变业务源码。它们已保留供最终统一清理审批，未删除；审计脚本随后设置 `sys.dont_write_bytecode=True` 防止后续写入。
- 本轮不安装依赖、不跑完整 pytest、真实模型、浏览器、完整 Word/PDF 验收。缺少这些运行条件不等于系统未实现对应功能。

## 结论

当前代码已经从单一制药原型推进到真实的通用成本合同、行业包、企业配置和上下文绑定。旧版的空归因通过、非有限数字入库、检索候选先截断后过滤、季度对标参数遗漏等问题已有实际修复；不能继续照抄旧缺陷清单。新增机械与化工包是独立合成迁移证明，未实现真实行业生产系统，也未宣称完整 ERP、联副产品或在制品引擎。

仍有下列可复现的实质问题，应在下一轮业务修复中优先处理：行业对标的数字正确但证据元数据错误；RPA 回执未完整绑定已确认载荷；失效报告仍命中缓存；预测初始化和缺月处理错误；决策模型说明缺少身份和语义一致性门。它们不能通过改验收文案解决。本轮仅记录，不直接修改业务实现。

## 已确认的当前缺陷

### B01 · P2 · 跨厂指标继承了左厂原指标的分子、分母和来源行

位置：`industry.py:721–730`；同类来源限制在 `industry.py:636–641`。

真实合成机械样例，`mechanical_demo:synthetic-mechanical`、`DEMO-01`、2026-06、示范工厂 A 对 B：材料单位成本分别为 15 与 30 元/件，跨厂差异率 `-50.0%` 正确。但是其 `benchmark:示范工厂A:示范工厂B:materials:rate` 指标同时存储：

| 字段 | 当前值 | 应表达的值或范围 |
|---|---|---|
| formula | `(左厂−右厂)/右厂×100` | 保留该方向 |
| numerator | `1800` | `-15`（15−30） |
| denominator | `120` | `30`（右厂单位材料成本） |
| comparison_period | null | 2026-06 同期 |
| row_keys | 只有 A 厂当月成本行 | 两厂实际参与运算的成本行及独立产量行 |

按照存储的分子/分母重算得到 `1500%`，与显示值 `-50%` 冲突。原因是字典复制了 A 厂原材料指标后只覆盖显示值/公式，保留了原先“金额/产量”的证据绑定。delta/contribution 也使用相同复制路径。`metric()` 的普通环比/同比/预算指标虽分子分母另行指定，但来源行固定为 current cost rows，未包含基期或独立产量行，无法完成精确行级重演。

影响是证据抽屉、报告数字引用及审计合同自相矛盾；不是跨厂表格的 `-50%` 本身算错。修复须按 delta/rate/contribution 分别生成完整 metric，对应分母独立定义，绑定左右/本基期成本与产量行。验收应从保存的 metric 证据重算，而不是只比较显示值。

### B02 · P2 · Holt 初始化漏掉第二个观测，缺月后仍按等距月份输出 PASS

位置：`forecasting.py:27–44`、`:55–76`。

- 连续线性输入 `[2026-01:10, 2026-02:20, 2026-03:30]` 的下一月为 `37.8`；按该文件声明的首两点初始化和 Holt 线性更新，线性不变性基准应为 `40`。代码把 level 留在第一个点 10，却从第三个点开始更新，产生人为的一步残差 10 和非零预测区间。
- 输入 `[2026-01:10, 2026-02:null, 2026-03:30, 2026-04:40]` 先丢掉二月，再把一月到三月当作一步，仍返回 `PASS` 与五月 `57.8`。只检查重复/排序，没有检查月份有效性、连续性。

应统一初始化时点与循环起点，增加有解析期望值的常量/线性测试；按月预测须拒绝缺月或提供明确的时间间隔模型，不能静默压缩时间轴。修复后更新 forecast_version。当前“80%”来自样本内残差 RMS，同一宽度用于所有预测期，且没有覆盖率校准；应标为实验性估计区间，不能描述成已验证的 80% 可靠覆盖能力。基础成本报告不应依赖该加分模块通过。

### B03 · P2 · 决策说明与确定性动作相反、响应身份不符仍标 PASS

位置：`decision.py:102–111`。`narrative.ModelGateway.complete` 返回身份元数据；`decision.advise` 将 `_identity` 丢弃，只检查 rationale 形状、长度和数字。

隔离替身返回错误模型身份 `MISMATCH`，以及“无需生成报告，仅更新看板即可。”；输入确定性决策为 `REPORT_NEEDED`、原因“本期间无报告”。当前输出保留 `REPORT_NEEDED`，但把相反的说明标为 `advisory_status=PASS`，并把请求型号写为 `advisory_model`。

实际决策枚举没有被改写，不能夸大为模型擅自执行相反动作。问题是用户看到与动作相反的解释，模型身份也没有进入成功门。应复用主报告身份校验并返回 requested/returned/status；说明改成决策与信号 ID 的受限选择、由程序生成动作短句，或者对相反动作表述降级，避免仅靠提示词约束。

### B04 · P2 · RPA POST 快速成功路径没有对账用户确认的完整载荷

位置：`actions.py:221–223`；GET 路径 `:193–194` 已有更完整对账。详见专项 N01。

同 task_id 的 fake POST 200 返回合法送达回执，但把收件人和建议替换为其他内容，结果仍为 `SENT/SIMULATED_SENT`，GET 对账次数为 0。旧版把 `failed` 字符串当作成功的问题已修，这个反例针对新的独立缺口。POST/GET 应共用确认载荷一致性检查；若 POST 不返回全部字段，进入 GET 对账，不得仅凭 task_id 判定已按确认内容送达。

### B05 · P2 · 人审状态与实际审核矛盾，失效报告仍复用缓存

位置：`worker.py:88–90`、`api.py:212–214`、`jobs.py:38`；详见专项 N03。

隔离人审使 acceptance=PASS 后，job.status 仍 DEGRADED 且 result.human_review_status 仍 PENDING。产物字节被改动后，现有 A03 防线正确使审核失效，但再次相同 key 入队仍返回同一破损报告。

应区分 execution、capability、acceptance 状态并保持投影一致；缓存命中检查产物健康、有效审核绑定，失效时创建有来源关系的重建任务。不能为修缓存而恢复“所有 DEGRADED 每次重跑模型”。生成时 record 与当前人审记录可分开，但必须显式说明时点并提供统一当前状态。

### B06 · P2 · 编辑错误结构触发 500

位置：`actions.py:134,142,146` 在统一校验 `:147` 之前调用未验证字段的 `.get/.strip`。详见专项 N02。

`assignee='bad'`、`finding=null`、`suggestion=[]` 各产生 AttributeError；API 仅处理 ValueError/KeyError，因此为 500。事务回滚后仍 DRAFT，未发送。应先验证编辑 schema 再合并完整动作，返回稳定 4xx；保留已修好的必填检查和确认 payload_hash。

### B07 · P2 · 查询超时覆盖历史已证实发送回执

位置：`actions.py:198,200`、`:178`、`:104`；详见专项 N04。

隔离成功发送后 `http_accepted=true/notification=SIMULATED_SENT`，一次 GET 网络异常将其变为 `REMOTE_UNKNOWN/remote=null/http_accepted=false/notification=UNKNOWN`。状态事件只记状态/错误，没有保存被覆盖的完整回执。应保留 last_confirmed_remote/delivery，另记最新查询错误与时间；不应为查询未知自动重发。

## 旧问题修复状态与已保留的能力

| 主题 | 新版结论 | 核验强度 |
|---|---|---|
| C01 空归因/“证据不足”掩盖确定性因果 | Finding 非空约束、具体缺证记录约束、确定因果拒绝、解释任务注册与覆盖已加入 | 本轮空文本及原无依据因果反例均拒绝；其他语义路径为源码核验 |
| C02 Infinity 数值入库 | ingestion 对数值统一执行 finite 检查 | 总工时 Infinity 本轮返回 INVALID/NON_FINITE_NUMBER |
| C03 检索先取 100 再应用企业/产品过滤 | 先生成 eligible 集合，FTS 与向量查询前应用过滤 | `knowledge.py:372–385` 源码；未运行真实向量模型 |
| 主报告模型身份 | 请求与返回模型分类记录、聚合身份门和失败降级保留 | `narrative.py:711–715,904–923`；本轮未实调模型；新决策分支另见 B03 |
| A01 季度对标参数遗漏 | 前后端已传 analysis_type，响应包含 period | 源码链路确认，未跑季度浏览器 E2E |
| A02 所有 DEGRADED 重跑 | 相同 key 复用已修 | 隔离复现；产物健康与人审状态仍见 B05 |
| A03 变更产物仍保持审核通过 | 实际文件字节 hash 进入审核绑定 | 修改隔离 DOCX 后 acceptance FAIL、active_review null、expired_count 1 |
| A04 空字段编辑绕过 | 草稿/编辑/确认共用 ExecutableAction，空验证目标/空预期证据/非法日期拒绝 | 隔离复现；错误结构见 B06 |
| A05 failed 当成功 | 失败字符串降 ACCEPTED/UNKNOWN 并查询对账 | 隔离复现；POST 完整对账见 B04 |
| A06 JSON [] 崩溃 | 协议形状检查并保留降级 | 隔离复现；网络异常清回执见 B07 |
| 重复确认、SENDING 重启恢复 | 重复确认只有一条 outbox；SENDING 恢复只 GET，不再次 POST | 隔离复现 |

## 通用性与 RAG 的实际边界

- 已有 Pydantic 不可变 AnalysisContext，数据/知识/模板/政策版本参与绑定，企业配置独立于行业。规范金额与独立产量分表聚合；检查单位、币种、产品版本、政策、期间、生产对象、父子成本重复计入，拒绝不支持的 WIP 口径。并非把制药名称替换后复制三个后端。
- 已有 pharmaceutical、mechanical_demo、chemical_demo 三包，其中新增行业迁移是机械与化工两个合成参考包；没有电子制造包。基础要素动态化；机时/件与能耗/kg 是可信代码注册的两个具体策略，不是任意上传代码插件。
- 同比/季度/预算能力受期间和字段约束；在制品、联副产品自动分配和严格价量分解明确 unavailable，而非自动填零。缺驱动、混合单位等条件已有能力降级。标准场景合同存在，不代表所有看板/正式报告都已提供完整标准差异分解。
- 知识库已有 PDF/DOCX/TXT 与包内 JSON 解析、版本化分片与定位、FTS/BM25 + 可选向量融合/重排、当前上下文过滤。OCR 与外置向量/重排能力需按环境显示，不能把源码存在等同本轮实际跑通。
- 图谱是制药配方/工艺规则抽取及有限词扩展，保留知识版本，召回仍经原适用性过滤。它不是制造行业通用图谱、净因果模型或已经量化证明的检索增益。源码默认剂量 unit=kg、工序规则依赖文档形状；扩展文档时应做单位与实体/来源边界测试。
- 多模型是分任务路由，决策 Agent 是有限确定性策略加说明；当前有代码实现，不应继续写成“仅设计”。但质量/费用提升需独立对照，功能存在不自动构成已验证效果。

## 当前验收与历史存档不能混写

`docs/current_run.json` 当前 run 为 `release_20260918_5974275`，代码 revision `5974275ca90d8ba5dd524c5320845c3906348dfa`，不是本轮 HEAD cdd9cb9。其记录七个场景（机械、化工、合成制药、S1/S2/S3/Q2）自动项及 DOCX/PDF 通过，human_review=PENDING、competition_ready=false，作业 DEGRADED。该记录是仓库已有证据，本轮没有重新执行、没有代填人审，也不将其当作 HEAD 全量通过。

当前索引还明确保留 `delivery_20260918_47c5806` 静态交付与其他历史失败/视觉记录。历史报告可用于追踪，不可按新版本重新命名成当前验收结果。文档中仍出现旧轮次统计时，应绑定对应 run/revision，避免与 current_run 唯一当前入口冲突。

## 可复现证据文件

- `backend_repro.py`、`backend_repro_results.json`：B01/B02/B03、C01/C02 的本轮函数级实测。
- `api_backend_notes.md`、`api_isolated/repro.py`、`api_isolated/result.json`、`api_isolated/blob_check.json`：API/RPA/审核专项及固定 ref 核验。
- `fetched_backend/` 为早期只读副本；与新 worktree 源码逐文件比较仅差导出附加的末尾空行。反例脚本实际导入新 worktree，不依赖副本执行。

建议顺序：先修 B01/B04/B05 的证据与确认合同，再修 B06/B07 错误恢复；B02/B03 加分模块在修复前明确实验/降级。每项以对应隔离反例转为回归测试为完成标准，再重建绑定新 revision 的当前验收。不得删除历史文件、清队列或覆盖原始数据来制造通过。
