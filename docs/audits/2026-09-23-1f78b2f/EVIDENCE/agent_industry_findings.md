# 行业包/通用性/企业配置 专项审查（agent_industry）

- 审查对象：worktree `D:/yaoheng-audit-wt-1f78b2f`（yaoheng-zhixi @ 1f78b2f，只读）
- 范围根：`药衡智析_增量源码交接/public_source_candidate/05_原型/`（下文 `05_原型/` 简写）+ `public_source_candidate/competition_configuration/`
- 方法：Trail of Bits audit-context-building + spec-to-code-compliance；逐文件完整阅读；每函数记录职责/前提/异常路径/调用关系；判定分级（满足/部分/不满足/未实现/待验证+静态确认/待实测）；疑似缺陷先反证。
- 日期：2026-09-23。审查者无视觉能力，未运行带副作用的命令；数值核算用独立 python 只读脚本完成。

---

## 1. 逐函数记录：`05_原型/backend/pharma/industry.py`（795 行，全部通读）

前提（谁建立）：`PACKS=APP/'industry_packs'`（config.py:4 `APP=ROOT/'05_原型'`）；`ENTERPRISE_REGISTRY=RUNTIME/'enterprise_registry.json'`（config.py:15，默认 `.runtime/`）。无进程级"当前行业"——每次分析经 `AnalysisContext` 绑定不可变输入。

| 函数/类（行号） | 职责 | 前提/调用方 | 异常路径 | 判定 |
|---|---|---|---|---|
| `digest(30)` | JSON 规范化 sha256 | 全模块 | 无 | 满足 |
| `Contract(34)` | pydantic 基类：extra=forbid、frozen、非空字符串 | 所有模型 | 校验失败 ValueError | 满足 |
| `AnalysisContext(38)` | 任务级不可变上下文（企业/数据集/行业/策略/模板/知识/公式/企业配置 8 个版本指纹），`context_hash` 属性 | api/worker/jobs 经 resolve_context 建立 | frozen 防改（test_industry:40 断言） | 满足 |
| `FactScope(55)`→`CostFact(73)`/`QuantityFact(88)`/`OptionalFact(99)` | 类型化事实：period 正则、amount/quantity finite、optional 限定 9 种 kind 非负 | facts.json/CSV 导入 | NON_FINITE_NUMBER 等校验错 | 满足 |
| `NormalizedDataset(115)` | costs/quantities/optional 三关系 | `_read_dataset`/`import_csv` | — | 满足 |
| `PackManifest(121)` | 包清单：id 模式、core_compatibility、manufacturing_mode(discrete/process/hybrid)、capabilities 需求表、elements 显示名、strategies 必须已注册、6 个 entry 文件名 | `load_pack` | — | 满足 |
| `_production_key(139)` | 生产对象键（企业/厂/产品/版本/期/情景/对象/粒度） | `_optional_ratio`/`aggregate` | — | 满足 |
| `_optional_ratio(144-180)` | 单一驱动聚合：输出单位硬校验（'件' 或 kg/t/吨）；未知单位/孤儿对象/同对象同工序重复导出→拒绝；覆盖不全→value=None 带原因 | `_machine_hours`/`_energy`（analyze_reference:716-721） | STRATEGY_OUTPUT_UNIT_CONFLICT / OPTIONAL_UNIT_CONFLICT / OPTIONAL_OBJECT_NOT_IN_OUTPUT / CONFLICTING_OPTIONAL_FACT_ID / OPTIONAL_DUPLICATE_OBJECT_OPERATION / 覆盖不全降级 | 满足（单位换算 小时/分钟/秒/kWh/MWh/Wh 用精确有理数，test_industry 驱动单测佐证） |
| `_machine_hours(183)` / `_energy(189)` / `STRATEGIES(194)` | 仅注册 2 个策略：小时/件、kWh/kg。**策略注册表是封闭的，上传 JSON 不能新增**（138 行注释+industry_rules.py 文档） | manifest.strategies | 未注册策略名→UNREGISTERED_STRATEGY | 满足（有意信任边界）；见问题 I-6（单位绑定限制） |
| `load_pack(198-209)` | 读 manifest.json 并校验：包名字符、core_compatibility=='>=1,<2'、策略已注册、entry 文件名仅 basename | context_catalog/resolve_context/catalog/analyze_reference/narrative/reference_report | UNKNOWN_INDUSTRY_PACK / INCOMPATIBLE_CORE_VERSION / UNREGISTERED_STRATEGY / UNSAFE_PACK_ENTRY | 满足 |
| `list_packs(212)` | 枚举 PACKS/*/manifest.json | context_catalog | — | 满足 |
| `ProductConfig(216)`/`EnterpriseConfig(222)` | 企业配置：单位/币种/产品目录/版本/政策/职责/facts+knowledge entry（防路径穿越，须 .json） | `_load_enterprise_file` | UNSAFE_ENTERPRISE_ENTRY | 满足 |
| `_load_enterprise_file(242)` | 读 enterprise.json，附 `_base_dir`/`_config_file` | `_enterprises`/`register_enterprise` | — | 满足 |
| `_registered(250)` | 注册表读取；**死条目（文件已删）静默剔除而非致命**（注释解释：目录必须可用，同键可重导） | `_enterprises` | — | 满足（test_dead_registry… 佐证） |
| `_enterprises(258)` | 默认包企业 + 注册企业（按 industry 前缀过滤）；同 id 冲突→ENTERPRISE_REGISTRATION_CONFLICT | context_catalog/resolve_context/catalog | 冲突 ValueError | 满足 |
| `_enterprise(270)` | 按 id 取企业；未知→UNKNOWN_ENTERPRISE_CONTEXT | 多处 | — | 满足 |
| `_read_dataset(278-291)` | 读 facts.json 并交叉校验：单位==enterprise.quantity_unit、币种、enterprise_id、产品+版本、policy_version 全一致 | catalog/analyze_reference/register_enterprise/resolve_context | ENTERPRISE_UNIT_CONFLICT 等 5 类 | 满足（注意：不校验 element_id ∈ pack.elements——允许任意要素 id，见问题 I-2） |
| `register_enterprise(294-321)` | 可信本地企业注册：先全量校验（默认企业不可替换、数据非空、逐 (厂,产品,情景) aggregate 通过、knowledge scope 一致），再持锁原子写注册表（tempfile+os.replace） | data_import.publish_business:464 / publish_business_batch:732 | DEFAULT_ENTERPRISE_CANNOT_BE_REPLACED / EMPTY_DATASET / 校验链各类 / ENTERPRISE_REGISTRATION_CONFLICT | 满足（写前完成全部校验，失败不破坏现有数据——与 data_import.py:8 设计注释一致） |
| `knowledge_entry_for_context(324)` | 上下文→企业 knowledge.json 路径 | context_services.retrieve:74 | — | 满足 |
| `resolve_context(331-359)` | 上下文 ID→AnalysisContext。缺省取目录默认；无数据→显式 `NO_AVAILABLE_DATA_CONTEXT`（不回落合成演示）。`pharmaceutical:competition` 特判：snapshot=ingest()、知识指纹=03_制药知识文档、模板指纹=04_报告模板 docx 集、dataset_id='competition-private'、policy='pharmaceutical-original-1' | api.selected_context/analyze_reference | NO_AVAILABLE_DATA_CONTEXT / ingest 校验错 | 满足；注意 enterprise_config_version 对 competition 也取 synthetic-pharma 的 enterprise.json 哈希（企业配置指纹对赛题上下文语义为"包默认配置指纹"，INFO） |
| `generation_key(362)` | 生成缓存键=上下文+输入+prompt/model/provider/embedding/retriever/参数 | narrative/jobs | — | 满足 |
| `UnitConversion(367)`/`convert_quantity(376-386)` | 物理单位换算仅 t/kg/吨 精确表；其他换算须带产品绑定的证据对象并四字段 scope 匹配 | aggregate 前的竞对对齐、metrics | CONVERSION_EVIDENCE_REQUIRED / CONVERSION_SCOPE_MISMATCH | 满足（test_packaging_conversion… 佐证 盒→粒 需规格证据） |
| `_check_scope(389-395)` | 同批事实必须同企业/厂/产品/版本/政策/来源模式/期粒度/粒度/范围；非 completed→WIP_ALLOCATION_NOT_SUPPORTED | aggregate | 8 类 *_CONFLICT | 满足 |
| `aggregate(398-443)` | **核心口径**：按期间+情景过滤；期间必须完整覆盖（INCOMPLETE_PERIOD）；层级/汇总双计四重防护（HIERARCHY_DOUBLE_COUNT / DETAIL_SUMMARY_DOUBLE_COUNT / DUPLICATE_SUMMARY_FACT）；fact_id 重复同值去重异值拒绝；**产量按生产对象关系独立去重（不与要素 join）**，重复导出不放大；成本对象集合与产量对象集合必须相等（COST_QUANTITY_OBJECT_MISMATCH）；输出 `total_cost=Σ要素`、`quantity=Σ独立对象产量`、`unit_cost=total/quantity`（产量 0→None 不为 0） | analyze_reference/publish_snapshot/register_enterprise | 上述全部 | 满足（与赛题不变量关系见 §5.6） |
| `PolicyBridge(446)`/`ComparisonAlignment(459)`/`_align_base(464-490)` | 跨口径比较前显式对齐：单位换算（物理因子与证据一致否则 CONVERSION_FACTOR_CONFLICT）+政策桥（scope 八字段匹配+金额调整+证据引用），重算 unit_cost | compare | POLICY_BRIDGE_SCOPE_MISMATCH 等 | 满足（test_explicit_alignment… 佐证） |
| `compare(493-510)` | 五种比较（mom/yoy/budget/standard/factory）合同：同质字段一致、期间移位校验、情景配对（实际 vs 预算/标准）、factory 放宽厂但期间情景须同 | analyze_reference:666/benchmark_reference:753 | *_CONFLICT / INVALID_COMPARISON_PERIOD / INVALID_SCENARIO_COMPARISON 等 | 满足 |
| `publish_snapshot(513-529)` | 候选数据集先逐 (企业,厂,产品,情景) aggregate 全验证，再 staging+os.replace 原子发布 snapshot.json+current.json 指针 | import_csv | EMPTY_DATASET / ORPHAN_QUANTITY_COHORT / aggregate 各错（失败不落指针，test_empty_import… 佐证） | 满足 |
| `load_snapshot(532)` | 读指针+哈希校验 | tests/快照消费 | INVALID_SNAPSHOT_ID / SNAPSHOT_HASH_MISMATCH | 满足 |
| `import_csv(541)` | 规范 CSV 适配器；"字段映射属于包不属于引擎" | tests | — | 满足（未被数据中心 UI 使用——数据中心走 data_import→register_enterprise） |
| `capabilities(549-570)` | 能力探测：数据侧（costs/quantities/optional kinds）+服务侧（docx/libreoffice/模型凭据/rpa）；wip/联副产品/严格价量分解显式 unavailable+原因 | context_catalog/catalog/analyze_reference | — | 满足 |
| `_competition_available(573-580)` | 赛题上下文就绪判定：原始数据目录有 CSV 且主数据工厂含"中药一厂" | context_catalog | 异常吞掉返回 False | 满足 |
| `context_catalog(583-608)` | **目录过滤**：默认仅 pharmaceutical 包；包默认合成企业 synthetic-pharma 也排除；注册企业显示"用户导入数据（数据中心发布）"；赛题上下文在数据就绪时追加并设默认；`PHARMA_SHOW_TEST_CONTEXTS=1` 显式列出全部（测试/迁移） | api /api/industry/catalog、App.tsx | — | 满足（与"正式演示仅赛题制药数据"符合；deploy/docker-compose 与 .env.example 均未启用测试开关） |
| `catalog(611-621)` | 上下文数据目录（厂/产品/月份/快照/单位/币种/能力/数据标签） | api /api/catalog 等 | `context_id=None` 时 `.split` AttributeError（见问题 I-1，仅空部署直连 API 触发） | 部分满足 |
| `retrieve_reference(624)` | 包参考检索适配（scope 先于排序） | narrative/benchmark | — | 满足 |
| `analyze_reference(630-740)` | 通用分析入口：competition 特判走 metrics.analyze 并重算 snapshot_id（2026-09-21 修复注释）；通用路径：模板字节读取+哈希校验（TEMPLATE_SNAPSHOT_CHANGED）、aggregate 当期+三基期（INCOMPLETE_PERIOD 降级为 None 基期）、`metric()` 工厂给每个指标 sources/row_keys/formula/分母、要素明细+多基期比较+贡献、±10% 阈值告警（note 硬编码"合成演示阈值"）、optional 驱动评估、近 6 月趋势、details 显式 unavailable"不推算采购/BOM 明细"、limits 携带 pack.data_label、specialized_metrics | api/dashboard/benchmark_reference | 上述全部 + WIP_ALLOCATION_NOT_SUPPORTED（驱动事实非 completed 直接拒绝，713-715） | 满足（标签问题见 I-3） |
| `benchmark_reference(743-795)` | 同期跨厂对比：两次 analyze_reference、context_hash 一致性（CONTEXT_DRIFT）、comparison_scope 复用 compare('factory') 合同、逐要素差额/贡献、为每个差额生成带左右源证据的 metric、limits 声明"合成演示工厂…不推算成本净原因" | api /api/benchmark | DISTINCT_FACTORIES_REQUIRED / compare 各错 | 满足 |

## 2. 逐函数记录：`industry_rules.py` 与 `narrative_rules.py`

- `industry_rules.pharmaceutical_rules()`（16 行）：lru_cache(1) 从固定路径 `industry_packs/pharmaceutical/narrative_rules.py` 以 spec_from_file_location 装载 `append_findings`。注释明确：固定条目是受审源码；新代码策略需改码+受控重启，绝不经 eval/网络安装。前提：APP 目录存在该文件。**只注册了 pharmaceutical 一个行业钩子**——其他行业（含 demo 包）无叙事规则钩子。判定：满足（信任边界清晰），扩展点偏窄（新行业钩子需在此加条目，见 §5.2）。
- `narrative_rules.append_findings`（104 行，制药赛题规则，全部规则仅对 `enterprise_id=='competition'` 上下文生效——narrative.py:918-926 门控）：
  1. materials_summary 非零差异→事实+核查行动（价格/耗用未分开）；
  2. 材料×市场行情方向假设（同向→"价格传导可能性较高"，反向→单耗/收率/库存结构；全程绑行情引文+missing_evidence，经 `validate_findings` 合同）；
  3. 提取收率工艺限值→机制假设（明确"不能证明本期实际收率下降"）；
  4. 无明细但有要素→行动（"不按比例推算缺失工厂数据"）；
  5. budget_bridge→量/单位成本拆分事实（"产量影响不能全部解释为效率恶化"）；
  6. labor/overhead 单位差异→行动（题包折算口径警示、维修费不得重复计入）；
  7. 维修记录"计量盘磨损/装量/偏差"三词同现→假设（局部产出损失≠月度净减产）；
  8. benchmark_context→跨厂要素差额事实+行动（"缺少二厂原料明细时保留缺项"）。
  异常路径：每条候选规则 `validate_findings` 失败即 break/continue（不产非法 finding）。前提：snapshot 由 metrics.analyze（赛题管线）产出（materials_summary/budget_bridge/benchmark_context 仅该路径存在）。判定：满足——数字全部来自确定性指标，模型不做数值推断。

## 3. 包与配置文件清单、消费矩阵

### pharmaceutical 包（`05_原型/industry_packs/pharmaceutical/`）
| 文件 | 内容摘要 | 消费方（代码链） | 判定 |
|---|---|---|---|
| manifest.json | hybrid；elements materials/labor/overhead；strategies=[]；data_label 合成演示声明 | load_pack；analyze_reference(elements 名/strategies) | 满足 |
| enterprise.json | synthetic-pharma；盒/CNY/DEMO-01；source_mode=imported_cost | `_enterprise` 默认企业；`_read_dataset` 校验 | 满足 |
| facts.json | 72 costs+24 quantities，2 厂×6 月×actual/budget，batch 粒度，optional=0 | `_read_dataset`；golden 2026-06 实测 A 厂 1350/150/9 与 evaluation.json golden 一致（本审查独立核算） | 满足 |
| knowledge.json | 2 条合成知识（enterprise/industry 各一，scope 字段齐） | register_enterprise scope 校验；context_services 检索 | 满足 |
| template.json | 6 章节（四、产品专项分析与核查）；required_notice 合成声明 | analyze_reference:649（字节级冻结）；reference_report.render/verify | 满足 |
| mapping.json | canonical 格式声明+element_map 同名+禁双计声明 | **仅 load_pack 文件名安全校验，内容不被读取** | 未实现（声明性文件；实际映射在 data_import.PRESET_WIDE_MAPPING/import_pipeline.DETAIL_TYPE_MAPPINGS 硬编码）——见 I-5 |
| evaluation.json | dataset=synthetic、golden、unimplemented 清单 | **无运行时消费者**（golden 与 tests/test_industry.py 独立断言并存） | 未实现（验收元数据，声明用途可接受） |
| retrieval.json | 单一目的 current_period_maintenance：维修/停机/故障/磨损，reserved 1 槽 | context_services.retrieval_policy（bound 模型校验，词条黑名单校验） | 满足 |
| terminology.json | 合成制剂甲/乙、合成设备别名、tokenizer_terms（回退用） | knowledge.pharmaceutical_terminology——**优先级低于 competition_configuration/pharmaceutical_terminology_original.json**（赛题术语默认生效） | 满足（回退链正确），跨行业全局共享术语表见 I-7 |
| source_contract.json | 赛题 7 类 CSV 字段模式+common+elements+**合成兜底 specifications/factories（合成制剂甲/合成制药厂甲乙）** | ingestion.source_contract：读取后若存在 masterdata（默认 competition_configuration/pharmaceutical_masterdata.json）则覆盖 specifications/factories/benchmark_factory | 满足（fields 是赛题管线模式；合成兜底仅在无 masterdata 时生效，默认仓库内 masterdata 必在） |
| narrative_rules.py | 见 §2 | industry_rules 固定注册 | 满足 |

### chemical_demo / mechanical_demo 演示包
- 结构与 pharmaceutical 同构；manifest 差异：chemical(process, 4 要素含 energy, strategies=[energy_per_kg], capabilities 带 energy_per_kg)、mechanical(discrete, work_order 粒度, strategies=[machine_hours_per_piece])；enterprise 单位 kg/件；facts 96/72 costs + 24 quantities + **24 optional 驱动事实（energy_kwh / machine_hours，带 operation_id）**；template 第 4 章标题随行业变化（批次能耗分析/工序机时分析）；evaluation golden 与 tests/test_industry.py 断言一致（mechanical 2026-06 3600/120/30、Q2 9400/320/29.375；chemical 2400/200/12、能耗 3）。
- **代码引用**：仅 tests/（test_industry、test_correctness_fixes、test_benchmark_integration_contract、test_knowledge_source_selection）+ 包自身 JSON。后端运行时对 demo 包的唯一入口是 `context_catalog`，被 industry.py:593 `pack.id!='pharmaceutical' and not show_test` 过滤；test_import_v2.py:336 断言 demo 上下文不进目录。
- **用户可达性**：`PHARMA_SHOW_TEST_CONTEXTS` 在 deploy/docker-compose.yml、deploy/Dockerfile、.env.example 均为注释态（默认关闭）。前端上下文下拉仅渲染 `/api/industry/catalog` 返回项（App.tsx:59,131）。
- facts 数据为显式合成（data_label、企业名 synthetic-*、source_snapshot=…-synthetic-v1）。
- 判定：**满足"正式演示仅用赛题制药数据"**——demo 包保留为测试/迁移验证资产，默认不可被用户触达；包存在本身不违规。

### competition_configuration/（`public_source_candidate/competition_configuration/`）
| 文件 | 用途 | 消费链 | 判定 |
|---|---|---|---|
| pharmaceutical_masterdata.json | 赛题主数据：3 产品规格（银黄口服液 10ml×10支/盒 等）、工厂 中药一厂/中药二厂、benchmark_factory=中药二厂 | ingestion.source_contract 默认合并（可被 PHARMA_PRIVATE_MASTERDATA_FILE/PHARMA_COMPETITION_CONFIG_DIR 重定向）；metrics.analyze 规格校验；benchmark_partner 对标配对 | 满足 |
| pharmaceutical_terminology_original.json | 赛题术语（3 产品/别名/设备别名/tokenizer_terms 含金银花黄芩 GMP 等） | knowledge.pharmaceutical_terminology 默认优先 | 满足 |
| scenarios.json | S1/S2/S3/Q2 四场景（均 context_id=pharmaceutical:competition） | scripts/run_acceptance.py --private-scenarios（评测） | 满足 |
| knowledge_supplement/ 4 个 txt | 行情/基准/异常处理/对标基线补充知识（2026-09-21 修复 #7） | config.KNOWLEDGE_SUPPLEMENT_DIR→knowledge.py:211-215 并入赛题知识索引（哈希入知识版本） | 满足 |
| synthetic_detail_中药二厂/ 3 个 CSV（435 行） | **合成二厂明细**（原材料/制造费用/人工工时 2025-2026，文件名含"合成"） | config.py:29-31：默认 `SYNTHETIC_DETAIL_DIR=None`→`SYNTHETIC_DETAIL_FACTORIES=set()`；仅显式设 `PHARMA_SYNTHETIC_DETAIL_DIR` 时 ingestion.ingest:252-257 并入（manifest 每文件标 `synthetic:true`）。启用时 metrics.py:196-197 在 details 出口统一 data_label"合成演示数据：数值按题包二厂成本汇总精确校准（结构比例取自一厂），非真实二厂经营明细"；metrics.py:345-353 benchmark 假设/缺失证据文本随之切换为合成声明版。生成脚本 scripts/generate_synthetic_plant2_details.py 头注声明数据边界与方法（一厂结构比例×二厂汇总精确分解，audit 容差内） | **满足**用户"原料下钻必须受真实数据支持，不能伪造二厂明细"——默认停用；默认路径二厂无明细时 `details.available=False,'不按比例推算'`（metrics.py:187），归因按"证据支持假设/证据不足"输出（metrics.py:352）。残留：评测若显式启用该变量，合成数据进入正式管线，但全链路（manifest/明细/对标/报告）携带合成声明，且 missing_evidence 列明"现有为合成演示明细"。评级 INFO |

## 4. 配置能力矩阵（谁配置、谁消费）

| 能力 | 配置载体 | 运行时可配置？ | 需改代码？ |
|---|---|---|---|
| 成本要素集合与显示名 | pack manifest.elements | 部署时（包目录） | 否（aggregate 任意 element_id；chemical 4 要素即证） |
| 计量单位/币种 | enterprise.json | 是（导入向导 quantity_unit 参数；API 发布可传） | 否 |
| 字段映射 | **代码**：data_import.PRESET_WIDE_MAPPING + import_pipeline.DETAIL_TYPE_MAPPINGS（+保存的表头指纹方案 JSON 运行时复用 + 小模型建议） | 部分（表头指纹方案可存可复用；非制药表头靠模型建议或质检失败） | 新行业固定映射需改码 |
| 驱动策略（机时/能耗） | manifest.strategies 声明 + 代码 STRATEGIES 注册表 | 声明可配；**策略本体仅 2 个且输出单位硬编码 件/kg** | 新策略/新输出单位需改码 |
| 检索策略 | pack retrieval.json（有界合同模型校验） | 是 | 否 |
| 知识 | enterprise knowledge.json / 竞赛知识目录 / 数据中心上传知识（write_knowledge_source→全局索引） | 是 | 否 |
| 报告模板（通用路径） | pack template.json（6 章节标题+声明） | 部署时 | 否（reference_report 要求恰 6 章节） |
| 报告模板（赛题路径） | 04_报告模板 docx 工作副本 + 数据中心模板上传安装（install_template） | 是 | 否 |
| 行业叙事规则 | industry_rules.py 固定注册（仅 pharmaceutical） | 否 | **是**（新行业钩子需加条目+评审） |
| 术语表 | 全局单文件（赛题优先/包回退） | 部署时 | 跨行业多术语表需改码 |
| 企业接入 | 数据中心向导（UI）→register_enterprise | 是 | 见 §5.3 |

## 5. 重点核查结论

### 5.1 通用性分层是否真实（非伪装）
**判定：满足（分层真实），但"横向扩展"主张须限定为"改装复用"而非"即插即用"。**
- 真通用（代码层，单后端无按行业复制）：事实模型（Cost/Quantity/Optional）、aggregate/compare/convert_quantity 口径与合同、快照发布/加载、AnalysisContext 绑定、企业注册表、能力探测、analyze_reference/benchmark_reference 通用分析、reference_report 渲染骨架（pack.name+template.sections+strategies 标签）。
- 配置层（JSON）：manifest（要素名/能力/策略声明/制造模式）、enterprise.json（单位/币种/产品/政策）、template.json（章节/声明）、knowledge.json、retrieval.json、terminology.json（回退）、evaluation.json（未消费）、mapping.json（未消费）。
- 专业策略层（受信代码）：STRATEGIES（2 项）、narrative_rules.py（仅 competition 门控生效）、metrics.py 赛题专用管线、reports.py 赛题 docx 编译器。
- 反伪装证据：chemical 第 4 要素 energy 纯配置生效（test_industry:23 `len(chemical['elements'])==4`）；模板第 4 章标题随包配置变化；多包共享同一后端与同一 render 入口（ADR 0004 明确拒绝"逐行业复制后台"）；analysis_context 携带 industry_id 全链隔离（test_concurrent_same_product… 断言 evidence 上下文隔离）。

### 5.2 新企业/新行业接入路径
UI 路径（制药包内新企业，全流程运行时）：
1. 数据中心上传（business：成本汇总/材料明细/制造费用明细/人工工时/预算 CSV 或 XLSX；knowledge：txt/pdf/docx/csv；template：docx）→ imports.sqlite3+原始字节保留；
2. 解析任务（worker→import_pipeline.run_data_parse）：预处理→字段映射（固定映射+预设+小模型建议，数值列防幻觉校验 `_mostly_numeric`）→质检（行级中文错误）→口径合并（汇总>预算>明细，同优先级冲突整体失败，产量冲突失败）；
3. `publish_business_batch` 生成 facts.json/enterprise.json/knowledge.json('[]')→`register_enterprise` 全量校验→注册表原子写入→`context_catalog` 出现"用户导入数据"上下文。
API 路径：`POST /api/imports/{id}/publish`（ImportPublishRequest.pack_id 可任意传，api.py:347/399）——旧端点仍在但前端 v2 未用。
新行业接入（部署级）：复制 `industry_packs/<新id>/`（manifest 通过 load_pack 全部校验：core_compatibility、策略已注册、entry 安全）+ 默认企业四件套；**必须改代码项**：新驱动策略（超出机时/能耗 2 种或输出单位非 件/kg）、行业叙事钩子（industry_rules 加条目）、字段映射预设、多术语表。无"上传即新行业"路径（安全取舍：配置不能执行代码，industry.py 模块 docstring 与 ADR 支撑）。
**限制点（P3）**：import_pipeline.py:298-299 硬编码 `pack_id='pharmaceutical'`——数据中心 UI 无法向其他包接入企业（符合"正式演示仅制药"，但削弱"企业配置能力跨行业"演示面）。

### 5.3 制药特化是否被通用化削弱
**判定：满足（未削弱）。** 赛题四模块支撑：
- 占位符/模板：competition 报告走 04_报告模板 docx 工作副本（reports.py 编译器，88 占位符/表格扫描 data_import.check_template；模板指纹入上下文），包 template.json 仅服务通用路径；
- 归因规则：narrative_rules.py 8 组规则（§2）仅对 competition 生效（narrative.py:918-926），导入企业/演示上下文走通用降级叙事；
- 检索术语：赛题术语文件默认优先于包合成术语；知识补充目录入索引；
- 评估规则：source_contract.json 字段模式+masterdata 合并（benchmark_factory 指定对标厂）+scenarios.json 评测场景；ingestion.audit 精确校验（unit_sum/total/rollup/share/continuity）。

### 5.4 aggregate 口径与赛题不变量
**判定：满足。** `total_cost=Σ唯一 detail 要素金额`（industry.py:434-436，fact_id 去重+层级双计四重拒绝）；`quantity=Σ独立生产对象产量`（424-433，产量关系与要素不 join，重复导出不放大）；`unit_cost=total/quantity`（产量 0→None）。因此"总成本=产量×单位成本"在行业路径**按构造恒成立**（unit 由 total/qty 定义）；赛题路径在 ingestion.audit:201-202 独立校验 `产量×单位成本==总成本` 与 `Σ三要素单位成本==单位成本`（容差 1e-6），双侧一致。零产量语义：unit_cost 未定义非零成本（test_zero_quantity… 佐证）。

### 5.5 演示包可达性
见 §3 demo 包节：**满足**（默认不可达，仅测试引用）。

## 6. 问题清单（严重度+反证）

| # | 严重度 | 问题 | 位置 | 反证 |
|---|---|---|---|---|
| I-1 | P3（静态确认，待实测） | 空部署（无赛题数据且无导入企业）时 `GET /api/catalog` 500：selected_context 返回 None→catalog(None)→`None.split(':')` AttributeError（api.py 仅 ValueError/KeyError 处理器） | api.py:75-77,101-104；industry.py:611-615 | 前端 App.tsx:68 `if(!contextId) return` 不触发该调用；resolve_context 路径有干净报错（industry.py:336）。仅影响直连 API 的空库首访 |
| I-2 | P3 | 导入企业 element_id 为 material/labor/overhead（单数 material），pharmaceutical 包 elements 键为 materials（复数）→报告/界面要素名回退英文 id 'material' | data_import.py:60-64（element:material）；industry.py:696 `pack.elements.get(key,key)`；tests/test_import_v2.py:139 明确断言 element_id=='material'（行为有意） | aggregate/比较/贡献均按 element_id 透传，无数值影响；纯显示层 |
| I-3 | P3 | 导入企业（真实数据）分析快照仍携带合成标签：analyze_reference 的 limits[0]=pack.data_label"合成演示…不是赛题原件"、alerts note"合成演示阈值"、catalog() data_label=pack.data_label；而 context_catalog 对导入企业显示"用户导入数据"（industry.py:598）——同一企业两处标签不一致 | industry.py:621,710,730-733 vs 598 | 正式演示走 competition 上下文不受影响；报告声明偏保守方向（把真实数据标成合成）而非相反 |
| I-4 | P3 | 数据中心解析流水线硬编码发布到 pharmaceutical 包，UI 无法跨行业接入企业 | import_pipeline.py:298-299 | 与"正式演示仅制药"要求一致；旧 API 端点仍可传 pack_id；ADR 0004 定位为"改装复用" |
| I-5 | INFO | mapping.json/evaluation.json/enterprise.responsibilities/template.responsibility_roles/professional_limits 声明未消费（mapping/evaluation entry 仅文件名安全校验） | industry.py:207-208；grep 全仓无消费 | 声明性/验收元数据；实际映射在代码中且有防幻觉与质检兜底 |
| I-6 | INFO | 策略注册表仅 2 项且输出单位硬编码（件/kg）：'盒'等行业无法复用机时/能耗策略 | industry.py:152-156,183-191 | 有意信任边界（注释+industry_rules 文档）；pharmaceutical 包 strategies=[] 不受影响；test_strategy_requires_correct_output_dimension 佐证防护有效 |
| I-7 | INFO | 术语表/分词器全局单例（赛题优先，包回退），跨行业上下文共享制药术语 | knowledge.py:27-47,77；context_services.py:85-90 图谱扩展已按 industry_id 门控 | 导入企业 knowledge 为空数组，检索影响面小 |
| I-8 | INFO | competition 上下文的 enterprise_config_version 指向包默认 synthetic-pharma 的 enterprise.json 哈希（语义为"包默认配置指纹"而非赛题数据配置） | industry.py:339,359 | 不参与任何正确性校验，仅指纹组成 |
| I-9 | P3（设计边界，非缺陷） | synthetic_detail_中药二厂目录在仓库中随包分发；若部署者显式设 PHARMA_SYNTHETIC_DETAIL_DIR，合成明细将进入正式分析管线 | config.py:24-31；ingestion.py:252-257 | 默认停用；启用时 manifest/明细/对标/报告四层合成声明齐全（metrics.py:196-197,345-353）；.env.example:27-30 注释说明启用语义 |

未发现 P0/P1/P2 级问题。未实现项搜索记录：`evaluation_entry 消费`→命中仅 industry.py:134,207（无读取）；`mapping.json 读取`→命中 0（仅 manifest 声明）；`responsibility_roles`→命中仅 reference_report.py:131 的 required_notice（非该字段）。

## 7. 未覆盖/残留

- 未实测运行（无后端依赖环境）：I-1 的 500 复现、import_pipeline 全流程 E2E、worker 队列行为——均有对应测试文件（test_import_v2/test_industry/test_correctness_fixes）静态佐证。
- reports.py（赛题 docx 编译器，1400+ 行）与 metrics.py 前 150 行、dashboard.py、worker.py 仅按调用链抽读，未逐行（属其他审查者范围的可能性高）。
- 07_交付 与 00_赛题原始资料 未在本次范围。
- frontend 各分析页对导入上下文的降级展示未逐页核查（仅确认上下文下拉数据源）。
