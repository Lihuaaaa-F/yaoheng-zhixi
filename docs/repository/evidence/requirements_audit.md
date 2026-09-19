# 2026-09-19 最新分支赛题覆盖、交付证据与迁移成熟度审计

审计对象：`Lihuaaaa-F/yaoheng-zhixi`，工作分支 `codex/core-industry-20260917`，固定提交 `cdd9cb90d1f2e38fac429e82d89e46765e2317d2`。应用根为 `药衡智析_增量源码交接/public_source_candidate`。本文路径除特别说明均相对此应用根。赛题依据为原始企业出题 DOCX 的文字提取 `repo_audit_20260917/competition_original.txt`。本轮读取完整 Git 树（419 项，未截断）、本地固定提交源码及归档验收 JSON；未执行应用、调用模型、重跑浏览器、重做数值核算或逐页审读媒体。其他专项审计的实测结论应另列来源。

## 1. 当前判断

最新分支已经显著超过 9 月 17 日初始实现：参考行业包、统一上下文服务、增强验收、知识图谱、运行时双模型路由、规则式任务决策、成本预测、任务计数和视频/PPT 文件均真实存在。不能因为 `main` 仍停在 `acc4693` 而说这些功能没有实现。

当前定位应是“具备较完整比赛主线和若干加分原型，自动验收有归档证据，但尚未形成一致、完整的参赛验收证据链”。不得称为所有要求满分或已完成一等奖验收：赛题没有给出可据此换算总分的权重；真人 0–5 归因评分仍空；热力图与原题指定交叉维度不一致；阈值后的自动段落触发尚不完整；视频脚本没有执行 RPA 发送；当前运行索引与具体任务不一致。

`docs/current_run.json` 绑定受测代码 `5974275ca90d8ba5dd524c5320845c3906348dfa`。本轮直接执行 `git diff --stat 5974275... cdd9cb9...`，差异仅为 9 份文档或验收回执；没有新增应用代码差异。因此原代码自动测试存档仍有参考意义，不能因 HEAD 变化一概作废，也不能把存档说成本审计新跑通过。

## 2. “七维度全绿”的逐维解释

来源：`docs/validation/release_20260918_5974275/verification.json` 及同目录各回执。该记录顶层 `status=PASS`，同时 `human_review=PENDING`、`competition_ready=false`。

| 自动维度 | 实际归档证据 | 可以支持的结论 | 不能据此推定 |
|---|---|---|---|
| environment | 退出码 0、PASS | 当时运行环境探针通过 | 用户 WSL2 Ubuntu 24.04 已安装依赖；所有机器一键可用；当前机新验证通过 |
| regression | 退出码 0；current_run 记 222 passed、1 skipped | 受测版本已执行一组回归 | 222 个赛题条款通过；覆盖所有业务边界；此前 256 项与当前范围一致 |
| scenarios | 七场景任务、DOCX/PDF 状态 PASS，任务 DEGRADED | 七份报告流水线到达可交付文件状态 | 所有章节专业内容合理、布局优秀、人工归因 ≥某分 |
| retrieval | 原题四场景各 8 条、三个合成场景各 2 条；hybrid、BaseRetriever/TextNode、RECALLED | 这些调用经过混合检索适配器且得到证据 | Recall@K=100%、图谱提高召回、未见真实问题有效、证据足以确认所有因果 |
| rpa | 七场景 `SIMULATED_SENT`，人工确认 `NOT_ENTERED` | 模拟通知送达 7/7；符合题目模拟服务范围 | 真实微信成功、负责人已确认、整改已完成；更广样本的可靠性概率 |
| browser | 8 组真实 API UI 检查＋10 组 mocked 合同检查；1440×1000、390×844 | 所列流程和视口已有归档执行证据 | 所有页面/分辨率/Edge均通过；mocked责任确认等同真人；此处证明模型/文件/RPA质量 |
| model_live | 七场景 `generation_mode=llm`、模型身份 VERIFIED、usage、失败与修复痕迹 | 最终解释合同 7/7；实际返回模型名为 glm-5.3-flash | 首次成功 7/7；专业原因正确；无需校验；模型评估等同人工评分 |

模型回执累加为 13 次调用、270,262 total_tokens。只有机械、化工两项没有记录修复失败，其余五场景保留了被拒条目和修复痕迹。这是“有界修复后最终通过”，不是全部首次成功；不能据此精确计算首轮条目成功率。账本中的决策路由调用另计，不能与这 13 次报告调用混作一次测量。

**运行关联缺陷必须修复。** 同为 `release_20260918_5974275`，current_run 中七个 job_id 与 manifest/verification 七个 job_id 全不相同。例如 mechanical 为 `a882b52a...` vs `bd269b40...`，S1 为 `28c10acc...` vs `e2f1bdf2...`。同目录 model_live/retrieval/rpa 未携带 job_id 和报告内容哈希，仅凭这些摘要不能闭合具体报告→解释→送达的完整关联。应从同一不可变运行生成 current 索引，逐条绑定 run、scenario、job、snapshot、DOCX/PDF 哈希、模型调用ID、RPA action_id；缺失原始证据只能标未绑定，不能改摘要追认。

## 3. 基础要求矩阵

| 赛题条款 | 源码/产物证据 | 本轮状态判断与验收边界 |
|---|---|---|
| 5.1.1 Word模板固定章节＋动态占位符，至少五类章节 | `backend/pharma/reports.py`；`docs/template_parsing.md`；原题报告静态文件 | 已实现并有结构/插槽归档验证；专业章节内容、原模板展示效果须绑定具体产物审读 |
| 5.1.2 产品、行业、企业三类知识 | 原题配方/工艺/GMP/设备PDF与行情/基准；knowledge模块 | 覆盖多类知识；题包缺历史异常整改档案，不得伪造原有事件库；结构化行情/成本应保持确定性查询 |
| 5.1.2 PDF/Word/TXT；向量＋BM25；来源标注 | `knowledge.py`、`context_services.py`；真实回执为hybrid/llama-index-core接口 | 实现及示例运行有证据；支持格式不等于所有扫描版/复杂表格已实测；仅2条合成知识召回不能证明新行业质量 |
| 5.1.3 月度/季度/专题与用户选择条件 | `api.py`、`metrics.py`、`industry.py`；S1/S2/S3/Q2 | 已实现且季度真实浏览器回执包含双向跨厂对比；旧版丢analysis_type结论不能直接沿用 |
| 5.1.3 模板＋确定性数据＋RAG＋大模型 | worker统一检索/生成/渲染；model_live七场景最终llm | 原型主线已具备，最终合同有归档证据；当前任务索引不一致需先校正；真人质量仍待评 |
| 5.1.3 Word/PDF专业排版 | `reports.py`、`reference_report.py`、convert_pdf；七对静态报告与38页PNG | 双格式产物存在；公开静态报告来源47c，不能称其为597 GLM生成；部分断行/来源页留白已有记录，最终排版需真人审读 |
| 5.1.4 三个场景结构完整度＋人工0–5评分 | evaluation_report；ReviewStore及API；归档human_review=PENDING | 结构程序检查已有；**人工评分缺口仍是必交评测缺口**。不能填AI分或把模型合同分代替 |
| 5.2.1 环比/同比/预算偏差/贡献度 | 集中metrics、industry聚合与对照测试 | 源码实现、有回归存档；缺月/零分母/负贡献等边界由数值专项审计确认，不把标准公式存在当已验证 |
| 5.2.2 ECharts近六月趋势、瀑布、结构图 | `frontend/src/Analysis.tsx`；browser回执与截图 | 三类强制图已实现；精确表格回退存在；当前归档两视口未直接覆盖1366×768 |
| 5.2.3 大模型归因段落 | `narrative.py`；NarrativePanel复用报告文本 | 报告生成后可展示；最终解释按合同受限，不能宣称已确认净原因；详细专业质量须真人 |
| 5.2.3 成本要素环比严格超过±10%自动重点分析 | snapshot.alerts、required_alerts、model_live.alert_coverage | 阈值及报告内全告警覆盖已有代码/回执；**无既有报告时看板不自动生成重点段落**，仍需手点“生成分析报告”，见下文 |
| 5.3 找差异→拆结构→拆原因、差异表/建议 | metrics.benchmark_analysis、industry.benchmark_reference、Benchmark UI | 原题/参考同产品跨厂对比链存在；新季度/双厂参数已进入API；二厂无原料明细要明确不可下钻，不能补造 |
| 5.3.3 三步法字段正确率、误差≤1% | tests中的独立golden；6ff归档three_step.json原题3/3 | 当前字段生成有证据；evaluation_report引用旧运行3/3，需明确历史归档，不能写本轮独立重测；数值专项另验 |
| 5.4.1 任务标题/负责人/来源/优先级/期限 | ExecutableAction、ActionStore及编辑/负例合同 | 已实现结构化任务；岗位/实际责任人应区分，建议专业可执行性需真人审阅 |
| 5.4.2 HTTP模拟RPA、模拟微信通知、前端状态 | actions、synthetic_rpa、worker独立dispatch_loop；七条SIMULATED_SENT | 模拟闭环归档7/7；这满足模拟性质，不要求真实微信；真人确认/整改完成不得由送达状态推定 |
| 6.1 Python/Web/ECharts/OpenAI兼容/部署文件 | FastAPI/React、依赖锁、启动脚本、ModelGateway | 栈与一键入口存在；WSL依赖/离线/重启/容错实测由部署专项负责 |
| 6.3 引用来源与许可证 | docs/third_party_reuse及ADR等 | 有清单；不新增ERP框架依赖；许可正确性与所有依赖覆盖不以README自动判定 |

### 需要优先修正的基础触发缺口

`frontend/src/NarrativePanel.tsx:9–14` 初次只查询既有报告/任务；如果没有 narrative，则显示按钮“生成分析报告”，只有按钮回调才 POST `/reports`。`Analysis.tsx:44` 仅渲染“重点分析”标签，未把 `snapshot.alerts.fact_summary` 作为重点分析段落显示。七场景告警覆盖回执证明“报告生成流程中覆盖全部触发项”，没有证明“看板阈值触发即自动给出重点段落”。

修复应控制预算：立即展示每个告警的确定性变化段落、口径与缺证提示；在用户已启用的自动解释策略下，以 snapshot_id/alert_id/模型及知识版本作幂等键排队有界解释，复用已有任务。没有配置模型时清楚降级，不能声称LLM已执行；避免每次筛选或刷新都请求模型。对恰好±10%、多要素同时触发、无基期、无密钥和重复进入页面给出端到端证据。

## 4. 加分项与创新成熟度

| 项目 | 实际实现 | 成熟度判断 | 形成可辩护亮点仍缺什么 |
|---|---|---|---|
| 5.2.2 产品×月份×成本要素热力图 | `Analysis.tsx:49–54` ElementHeatmap的轴为“成本要素×单位成本/总成本”，值为本期环比 | 有热力图组件，**未完整满足题目指定交叉维度** | 保留现有图但准确命名；新增产品×月份网格，成本要素/口径选择器，精确值、缺数空格及联动；跨产品样本不可只用1个参考产品 |
| 5.4.3 生成/送达/确认状态看板 | Tasks.tsx按任务ID去重计数，模拟送达与署名确认独立 | 功能已实现；有mocked确认与实际送达证据 | 使用独立演示身份可模拟确认，但不能冒签真人；真实确认无须为比赛强造 |
| 知识图谱增强RAG | graph.py规则抽取产品/药材/工序、剂量与页码；有限邻居查询扩展、图可视化 | 轻量图谱原型已实现；不是完整GraphRAG多跳推理 | 构图规则正确性/作用域/剂量单位须专项验证；图谱开关消融应在冻结未见问题上比召回、错引用、延迟；“8条稳定”不是质量提升 |
| 多模型协作 | ModelGateway.for_route；报告glm-5.3-flash、决策解释glm-4.5-air | 已有运行时双模型任务路由，不只是开发过程用了两模型 | 同模型对照与大小模型组合的质量、费用、延迟测量；不要仅模型数多就声称更准确或更省钱 |
| Agent自主决策 | decision.evaluate基于是否有同快照报告选择REPORT_NEEDED/DASHBOARD_ONLY；小模型仅复述说明；apply入队 | 可解释的规则式任务决策原型，贴合赛题示例；**模型不拥有决策权** | 展示规则、拒绝/降级、重复应用及数据变更行为；不能包装成多步自主规划、工具自治或“模型判断后自动执行一切” |
| 成本预测 | 固定α=.6、β=.3 Holt，至少3有效点，1–6月外推；残差估算区间；前端叠加 | 实验性时序外推已实现，PASS只代表输出合同 | 缺月处理、不同预测期区间、短序列局限及独立回测；和朴素/季节朴素基线对照MAE等，不能把当前80%标签说成已校准覆盖率 |
| 横向行业扩展 | 公共行业合同＋机械/化工参考包、同上下文服务/网关/导出/任务链 | 有实质迁移原型证据，优先可展示的工程亮点 | 一次由新开发者按冻结接口完成的独立迁移、真实授权行业数据、未见知识问答、业务专家认可；不能称完整行业产品 |
| 确定性数值＋证据限制＋报告绑定＋RPA回执 | metrics/industry、narrative validator、reports、outbox等已有 | 目前最值得优先讲清的主线创新 | 与无校验RAG基线比较错误数字/不适用证据/遗漏告警拦截，绑定真实反例；发现的边界缺陷修复后再给可靠性结论 |

图谱实施细节与说明存在潜在不一致：`context_services.py:86–88` 把扩展后的 `effective` 作为整个 `Knowledge.search` 查询传入；注释写“只补BM25、向量不变”。应核对实际search是否同样用该query做向量嵌入，统一说明或拆成独立query参数。该问题由源码专项进一步确认。

预测源码 `forecast_series` 先删除缺失值，再检查月份去重/递增，没有直接检查月连续；当前区间宽度对每个horizon相同。应作为实验能力与数学实现审查项，不能因为8个测试/七场景PASS就宣称可靠预测。这些技术缺陷的最终复现结论以数值专项为准。

## 5. 机械、化工是否使用同一条系统链路

**结论：使用同一条应用链，存在有意保留的源数据/模板适配分支；不是复制两个后端或只换产品名称。**

- API `resolved_analysis` 与 get_benchmark按完整context_id选择原题适配或 `analyze_reference/benchmark_reference`；同一请求合同进入JobStore。
- `worker.process_job` 统一取不可变快照、校验上下文版本，调用 `context_services.retrieve` → `narrative.generate` → `reports.render_docx` → `convert_pdf` → 验收和产物登记。参考数据与原题分别计算跨厂指标，随后合入相同解释合同。
- `reports.render_docx:342–349` 对非比赛上下文调用reference_report，这属于模板适配；随后仍走解释正文绑定检查与同一PDF转换。三个合成包并非共享制药原模板强改标题。
- `context_services.retrieve` 对参考企业读取各自knowledge.json，绑定knowledge_snapshot，然后使用相同Knowledge/主流框架适配、BM25/向量和适用性验证。任务来自共同ActionStore/outbox模拟发送流程。
- `tests/test_industry.py` 明确包含相同产品/文档ID隔离、多企业同包、月季独立golden、任意工厂对、单位/政策/生产对象语义、原子发布及模板冻结测试；本轮仅检查测试源码，是否全部通过以具体受测记录为准。

| 维度 | 机械包 | 化工包 | 证明范围 |
|---|---|---|---|
| 主数据/期间 | 1产品DEMO-01、2厂、6个月、actual+budget | 1产品DEMO-01、2厂、6个月、actual+budget | 同ID隔离有用；没有覆盖多产品组合复杂度 |
| 事实数量 | 72 CostFact、24 QuantityFact、24 OptionalFact | 96 CostFact、24 QuantityFact、24 OptionalFact | 非改名题包；有独立产量和驱动关系 |
| 粒度/单位 | work_order、件、机时/件 | batch、kg、kWh/kg、第四能源要素 | 有真实的结构语义差异，不等于完整制造成本核算 |
| 独立示例答案 | 六月3600/120=30；机时60/120=.5；Q2 9400/320=29.375 | 六月2400/200=12；能耗600/200=3 | 基础可复现样例，不是行业基准或生产实践经验值 |
| 知识 | 2条合成条目，第二条复用主体规程文字 | 同样仅2条，含批次/能耗边界 | 能证明格式和隔离，不能证明高质量行业知识检索 |
| 运行归档 | model_live最终llm、hybrid、双导出、SIMULATED_SENT | 同左 | 合成场景全链路存档；公开current任务关联需修 |

目前 `mapping.json` 是规范入口说明，`import_csv` 只接收Pydantic规范列名，**不是任意ERP列自动映射**。manifest具备版本与可信策略声明，但策略仍由公共代码STRATEGIES白名单注册，不是允许任意上传代码的插件市场。现有数量/政策对齐合同可以复用；WIP、联副产品分摊、真实ERP接口、密度推断、采购价量因果、OEE等未实现，应继续明确拒算或能力不足。

### 留给 GLM 行业深化工作的明确边界

1. 在选定细分行业调查真实流程、可合法使用的数据、企业成本政策、产品/版本/单位/期间、所需知识证据和验收人；记录一手来源、引用许可及适用性。不能从“机械”“化工”标签推导所有企业使用相同政策。
2. 默认改动范围为 `industry_packs/<新包>/`、对应 `tests/test_<新包>.py` 和 `docs/industry/research-ledger.md`；新包先写独立golden及缺失/冲突反例，再接同一链路。至少增加真实多产品、两个企业同ID隔离、字段映射方案及更丰富的公开/授权知识集，不能以复制两条模板知识当行业调研。
3. 不直接改API/outbox/worker/通用数值及隔离合同。现有接口表达不了某种事实时，提出最小数据反例、必要合同变更及回归清单，由核心维护者一次修公共接口；不复制新引擎绕过合同。
4. 量化迁移新增文件、核心改动、实际工时与操作步骤；不能用模型响应时间冒充迁移开发时间。当前迁移过程曾修改核心，不能宣称零核心改动扩展已获证明。
5. 专业归因0–5、正式版式、真实任务确认保留给真人；GLM可提出评审草稿及需要证据，不能替用户签署结论。加分功能先保持可关闭，不影响制药强制功能与降级能力。

## 6. 必交材料矩阵与视频实际缺口

| 必交项 | 最新实际文件 | 结论与待补内容 |
|---|---|---|
| 完整代码、部署文件、一键Web、公开仓 | 最新工作分支代码/脚本/锁文件确实存在 | 已有交付基础；main与分支版本需说明，最终提交链接必须指向正确提交；本审计未发布或合并 |
| 架构图、RAG、Prompt、模板、API文档 | architecture.md、rag.md、prompt_design.md、template_parsing.md、api_and_operations.md | 文件完整度已提升；运行/模型/授权表述有冲突，需原位统一 |
| 三场景评测：结构、真人归因、RPA率、三步法格式率 | evaluation_report.md与多轮JSON | 自动数据存在；**真人评分未填**，当前任务索引不一致，三步法率引用旧轮需标历史，不能交付成“所有项通过” |
| 5分钟内端到端视频 | `07_交付/demo_20260918/yaoheng_demo_narrated.webm`；另有release目录旧mp4 | 文件已存在，README记2分52秒；**脚本不能证明完成发送RPA过程，需核看/补录**；本审计未测视频时长或观看成片 |
| 决赛PPT | demo目录10页PPTX、阅读PDF、LibreOffice渲染PDF/PNG；release旧稿 | 已有文件及渲染记录，不能沿用旧结论说缺PPT；是否内容一致/能支撑答辩需审读，真人评分不得写成完成 |
| 可选预测 | forecasting代码、UI、文档/测试 | 已有实验原型，研究质量与边界仍待完善，不影响强制主线优先级 |

视频录制脚本 `05_原型/frontend/record_demo_20260918.mjs` 有以下明确证据缺陷：

- 场景⑧仅调用caption描述“经模拟RPA送达”，没有创建/编辑/确认任务、POST发送、等待送达回执等动作。展示历史任务看板不是完整展示“发送RPA任务”。
- 提交报告后轮询遇 `SUCCEEDED/DEGRADED/FAILED` 都break；等待超时也不抛失败；随后一律展示“Word/PDF已生成”字幕，末尾receipt固定PASS。因此脚本中的PASS不构成报告实际完成断言。
- `.click().catch(()=>{})`、waitForResponse失败返回null允许缺少提交也继续。应修复脚本并录制真实当前快照任务，等待正确终态和两种文件均可下载，实际创建/确认/发送一条任务，显示关联scenario/job/action与SIMULATED_SENT。
- 保持≤5分钟；实际生成较长可清楚标注等待片段缩短或使用同版本缓存，但不能凭字幕宣称执行，不能把责任人确认冒签为真人。

## 7. 文档原位修订清单与顺序

1. 首先修当前索引和回执关联，再更新README、evaluation_report、implementation_status、migration-evidence和演示README的“当前”段落。evaluation_report目前同时出现5974275、英文fa3c968、26efd3a_air2缓存复用PASS和v18b新鲜生成；current_run却正确把air2记为6/7、退出1。不得通过把历史失败改绿消除矛盾。
2. 明确四类版本：HEAD源码、受测源码、模型实调来源、静态报告/视频来源。静态报告47c与最新597 GLM都可保留，但不要把旧产物哈希归给新模型；现有视频README写air2 verifyPASS应修正。
3. README写“Coding Plan凭据禁止应用运行时”，current_run记录用户9/18授权特定1113端点回退；按用户当前授权与实际配置统一项目说明，保留适用范围。这里不擅自扩大凭据用途，也不重新要求已给出的授权。
4. 先完成阈值自动段落、必要核心缺陷及当前证据绑定，完成真人评审表和视频实际发送闭环；随后补题意一致热力图。图谱/预测/多模型的质量或成本提升未经对照就降低宣传措辞，不以增加模型请求数量替代验收。
5. 可用一句准确的竞赛状态：**“四大模块与多个加分原型已实现；固定版本七场景自动回执通过，当前报告索引、视频闭环及少数功能边界待修，人工归因/可读性/版式待评。”** 修复后根据新证据更新，不预先写为已通过。

主要固定来源：[最新工作提交](https://github.com/Lihuaaaa-F/yaoheng-zhixi/tree/cdd9cb90d1f2e38fac429e82d89e46765e2317d2)、应用根docs/current_run.json、docs/validation/release_20260918_5974275/、docs/industry/development.md、docs/industry/migration-evidence.md、05_原型/backend/pharma/{api,worker,context_services,industry,reports,reference_report,decision,graph,forecasting}.py、05_原型/frontend/src/{Analysis,NarrativePanel,Tasks}.tsx、05_原型/frontend/record_demo_20260918.mjs。
