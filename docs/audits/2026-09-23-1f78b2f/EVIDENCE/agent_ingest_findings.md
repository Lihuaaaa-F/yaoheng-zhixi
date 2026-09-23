# 数据导入链路审查证据（agent_ingest）

- 审查对象：worktree `D:/yaoheng-audit-wt-1f78b2f`（仓库 yaoheng-zhixi @ 1f78b2f），只读审查。
- 范围文件（全部完整读完）：
  - `药衡智析_增量源码交接/public_source_candidate/05_原型/backend/pharma/data_import.py`（765 行）
  - `药衡智析_增量源码交接/public_source_candidate/05_原型/backend/pharma/import_pipeline.py`（459 行）
  - `药衡智析_增量源码交接/public_source_candidate/05_原型/backend/pharma/ingestion.py`（307 行）
  - `药衡智析_增量源码交接/public_source_candidate/05_原型/backend/pharma/local_validation.py`（30 行）
- 交叉证据（只读）：`00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据/01_成本明细数据/*.csv`、`02_行业参考数据/*.csv`、`industry_packs/pharmaceutical/source_contract.json`、`industry.py`、`api.py`、`worker.py`、`config.py`、`tests/test_data_import.py`、`tests/test_import_v2.py`。
- 方法：逐函数记录职责/前提/异常路径/调用关系；判定分级（满足/部分/不满足/未实现/待验证+静态确认/待实测）；疑似缺陷先反证（查调用方、查测试、查下游消费）。
- 日期：2026-09-23。

---

## 0. 原始数据事实（对照基准）

实测（utf-8-sig 读取）：

| 文件 | 行数 | 月份 | 关键列 |
|---|---|---|---|
| 中药一厂_成本汇总_2025年1-6月 / 2026年1-6月 | 18/18 | 2025-01..06 / 2026-01..06 | 产量(盒)、直接材料(元/盒)、直接人工(元/盒)、制造费用(元/盒)、单位成本(元/盒)、总成本(元) |
| 中药二厂_成本汇总_2025/2026 | 18/18 | 同上 | 同上 |
| 中药一厂_预算数据_2026年 | 18 | 2026-01..06 | 预算产量(盒)、预算直接材料(元/盒)…、预算单位成本(元/盒)、预算总成本(元) |
| 中药一厂_原材料消耗明细 | 108 | 2026-01..06 | 原材料名称、单位消耗成本(元/盒)、原材料总成本(元)、占总材料成本比例 |
| 中药一厂_制造费用明细 | 90 | 2026-01..06 | 费用类别（每产品每月 5 类）、单位费用(元/盒)、费用总额(元) |
| 中药一厂_人工工时明细 | 18 | 2026-01..06 | 直接人工总额(元)、总工时/人数/天数 |

要点：**成本汇总与预算的要素列均为"元/盒"（单位成本），只有 总成本(元)/预算总成本(元) 是绝对额**；明细三类文件的金额列（原材料总成本(元)/费用总额(元)/直接人工总额(元)）为绝对额。样例：2026-01 一厂银黄口服液 产量45000、直接材料 6.83 元/盒、总成本 481500 元（45000×10.7）。
行业参考：行业成本基准（P25/P50/P75/本厂水平，百分数）、药材市场价格（1-6月价格宽表）。
`source_contract.json` 的 fields 与上述实际表头逐一相符（set 相等校验可通过）。

---

## 1. 逐函数记录

### 1.1 data_import.py

| 函数 | 行 | 职责 | 前提 | 异常路径 | 调用方 |
|---|---|---|---|---|---|
| `detect_encoding` | 75-84 | BOM→utf-8-sig，再按 utf-8/gb18030/big5 试解码 | 字节非空 | 全失败 `ValueError('UNSUPPORTED_FILE_ENCODING')` | create_upload |
| `normalize_period` | 87-97 | 2026年3月/2026-03/2026/3/202603/2026-3→YYYY-MM；月限 1-12 | — | 不匹配返回 None（调用方转行级错误） | validate/publish |
| `parse_number` | 100-108 | 去千分位（半/全角逗号）→Decimal；'-','—','N/A'→None；拒绝非有限值 | — | InvalidOperation→None | 全链路 |
| `_connect`/`_row`/`_save` | 111-136 | imports.sqlite3 CRUD；meta JSON 列 | 目录可写 | KeyError('IMPORT_NOT_FOUND') | 内部 |
| `_folder` | 139-142 | `imports/<id>/` 目录 | id 为哈希前缀（无穿越面） | — | create_upload |
| `create_upload` | 147-182 | kind/data_type 校验、空文件、50MB 上限、扩展名×kind 白名单、按内容哈希幂等、保留原始字节、建预览 | — | EMPTY_FILE / FILE_TOO_LARGE / UNSUPPORTED_FILE_TYPE_FOR_KIND / UNKNOWN_DATA_TYPE_FOR_KIND / 编码不支持 | api.import_upload |
| `_read_table` | 185-200 | CSV 解码+csv.reader；XLSX openpyxl **data_only=True**（公式取缓存值）、按 sheet 或静默回落首个 sheet；空行过滤 | 表头在第 1 行 | UNSUPPORTED_TABLE_SUFFIX | 预览/校验/发布 |
| `_build_preview` | 203-220 | business 建表头/8 行样例/建议映射/表头指纹；knowledge/template 仅存原件 | — | 非表格式报错 | create_upload |
| `suggest_mapping` | 223-231 | 指纹命中复用已存方案，否则 PRESET_WIDE_MAPPING | — | — | _mapping_for / api |
| `save_mapping` | 234-240 | 按指纹落 `mappings/<fp>.json` | — | — | api.import_mapping |
| `validate_business` | 245-343 | 结构/类型校验（详见 §2 规则清单） | 原始文件未被动过（幂等重读） | 不抛异常，错误聚合返回 | run_data_parse / api / publish 前置 |
| `_capabilities` | 346-362 | 按数据开放能力（总成本/单位成本/环比/同比/预算/量价分解） | — | — | validate_business |
| `publish_business` | 367-467 | 单文件发布：重新校验→逐行聚合→facts.json+enterprise.json→register_enterprise | validation VALID | IMPORT_VALIDATION_FAILED | api.import_publish |
| `publish_knowledge` | 470-505 | pdf(fitz)/docx(仅段落)/csv(整表转文本)/txt→文本；<30 字符显式失败 | — | KNOWLEDGE_PARSE_EMPTY | run_kb_build / api |
| `check_template` | 508-535 | docx 章节识别（Heading1 或 一、二、…编号）+ 占位符（段落+表格）；6 章节前缀匹配 | docx 可解析 | 由调用方兜底 | run_template_parse / api |
| `preview_original` | 540-571 | 原件只读预览（表 200 行/docx 文本/txt/pdf 内嵌） | 原件存在 | ORIGINAL_FILE_MISSING / UNSUPPORTED_PREVIEW_SUFFIX | api |
| `original_path` | 574-578 | 返回原件路径 | — | ORIGINAL_FILE_MISSING | api.import_file / 模板安装 |
| `waiting_imports` | 581-583 | UPLOADED+PARSE_FAILED 列表 | — | — | api.data_parse 等 |
| `mark_import_status` | 586-590 | 状态机置位（无迁移合法性校验） | — | UNKNOWN_IMPORT_STATUS | 流水线/api |
| `publish_business_batch` | 593-738 | 多文件合并发布：逐文件校验→优先级合并（cost_summary 0 > budget 1 > 明细 2）→facts+注册 | 全部 VALID | IMPORT_VALIDATION_FAILED / IMPORT_QUANTITY_CONFLICT / IMPORT_AMOUNT_CONFLICT | run_data_parse |
| `write_knowledge_source` | 741-752 | 知识文本落 `imports/knowledge/<类型>__<净化文件名>.txt`（文件名正则净化，无穿越） | — | — | run_kb_build |
| `get_import`/`list_imports` | 755-765 | 查询 | — | IMPORT_NOT_FOUND | api/流水线 |

### 1.2 import_pipeline.py

| 函数 | 行 | 职责 | 备注 |
|---|---|---|---|
| `DETAIL_TYPE_MAPPINGS` | 29-50 | budget/material/manufacturing/labor 四类明细固定映射 | budget 将 预算直接材料(元/盒)→element:material（单位值当金额，见 F-1） |
| `TYPE_PRIORITY` | 52 | 汇总 0 > 预算 1 > 明细 2 | 合并防双计核心 |
| `StepFailure` | 57-63 | 携带步骤名异常→终态消息"…报错：…" | 消息合同 |
| `_parse_json_object` | 66-77 | 模型输出剥代码栅栏取 JSON 对象 | — |
| `_fail` | 80-88 | 全部记录标 PARSE_FAILED + job FAILED | 见 F-9 |
| `_extraction_mapping` | 92-127 | 小模型建议映射；**数值性防护**（金额/产量列需 ≥60% 样例可解析） | 无 key→确定性回退 |
| `_mapping_for` | 130-156 | 明细类型固定映射（缺角色再请模型）；汇总/预算走预设+模型 | — |
| `_options_for` | 159-170 | budget→scenario=budget；表头含"万元"→scale=10000；`产量(单位)`→单位提示 | **无 元/盒 处理**（F-1 根因之一） |
| `_attribution_overview` | 173-209 | 发布后取 analyze_reference 告警→规则/大模型归因（仅定性） | 单个产品异常被捕获跳过 |
| `_analysis_hypotheses` | 212-238 | 大模型归因推测，失败回退 None | — |
| `run_data_parse` | 241-321 | 预处理→映射→质检→合并发布→归因→PARSED；StepFailure/泛型异常→FAILED | 见 F-1/F-8/F-9 |
| `run_kb_build` | 326-383 | 逐文档 publish_knowledge→write_knowledge_source→knowledge.build；DEGRADED 合同 | 解析失败→StepFailure |
| `_template_binding_analysis` | 388-408 | 占位符语义绑定（信息性） | 失败回退确定性语义 |
| `run_template_parse` | 411-459 | 章节结构(6 章节)→占位符(≥20)→绑定分析→install_template→PARSED | records 为空安全（条件表达式短路） |

### 1.3 ingestion.py（赛题打包数据管线）

| 函数 | 行 | 职责 | 备注 |
|---|---|---|---|
| `source_contract` | 25-56 | 读 source_contract.json；可选合并主数据 JSON（工厂/规格/基准厂），形状严格校验 | 部署不再依赖外部绝对路径 |
| `inspect_zip` | 72-93 | zip 名修复/穿越/软链/大小/压缩比防护 | **全仓库无调用方（死代码）** |
| `_kind` | 96-102 | 按文件名关键词分类 7 类 | 未知→UNKNOWN_DATA_FILE |
| `_read` | 105-127 | rglob *.csv，utf-8-sig 读取；表头重复/SCHEMA_CONFLICT（set 相等）/行字段数/空值→行级错误；记录 sha256、BOM 标记 | 与实际 CSV 表头逐一相符 |
| `audit` | 130-242 | 全部算术不变量+主键+月份+连续性（详见 §2） | 错误含 row_key=file:line |
| `ingest` | 245-292 | 读→(合成明细并入)→audit→快照版本=hash(VERSION+files+contract)；INVALID→rejected-*.json+抛错；VALID→临时目录 staging→duckdb parquet→**os.replace 原子换 current.json**；TOCTOU 复查 MASTERDATA_CHANGED_DURING_INGESTION | 快照按内容哈希保留（可回滚） |
| `load_rows` | 295-307 | 读 current manifest→parquet；resolve 父目录校验 | — |

### 1.4 local_validation.py（与数据导入无关：RPA 自动化 URL 门禁）

- `require_loopback`（7-19）：scheme 白名单 http/https、拒绝 userinfo/query/fragment、仅回环 IP 或 'localhost'，或环境变量显式 opt-in 的内部模拟服务（需同时 PHARMA_RPA_SIMULATION=1 且主机名全等）。`127.0.0.1.evil.com` 类域名不通过（非 IP 且非 localhost）。DNS 重绑定未防护但仅字面量 IP/localhost 可过，面窄。
- `NoRedirect`/`local_opener`（21-25）：禁止重定向、禁用系统代理。
- `require_simulation`（27-30）：要求服务端 health 声明 simulation 且 rpa_mode=local_simulator。
- 判定：**满足**（就其窄目的）；文件名与职责不符（INFO）。

---

## 2. 校验规则清单（两条流水线对照）

| # | 规则 | ingestion.audit（打包数据） | data_import.validate_business（用户自助导入） |
|---|---|---|---|
| R1 | 表头/schema 与合同一致 | ✔ set 相等 + 重复表头（SCHEMA_CONFLICT/INVALID_HEADERS） | ✘ 无（未实现；搜索 `headers` 去重/重复列：仅 ingestion.py:112 命中） |
| R2 | 行字段数/必填空值 | ✔ MISSING_OR_EXTRA_FIELDS（行级） | 部分：仅当维度三元组不全时整行跳过（不报错）；数字列空值静默跳过 |
| R3 | 数值可解析/非负/有限 | ✔ INVALID_NUMBER/NEGATIVE_INPUT/NON_FINITE_NUMBER（行+列） | 部分：INVALID（行级+列名）；负数不查（产量≤0 有查） |
| R4 | **单位成本=材料+人工+制造费用** | ✔ cost/budget_unit_sum（容差 1e-6） | ✘ 未实现（搜索 `单位成本`：data_import.py 无一致性算式命中） |
| R5 | **总成本=产量×单位成本** | ✔ cost/budget_total | ✘ 未实现 |
| R6 | **材料明细合计=汇总直接材料** | ✔ materials_unit_rollup/total_rollup | ✘ 未实现（跨文件仅优先级覆盖+warning） |
| R7 | **材料占比合计=100%** | ✔ materials_share（行）+share_rollup（组，按展示精度容差） | ✘ 未实现 |
| R8 | **制造费用 5 类合计=汇总制造费用** | ✔ expenses_unit_rollup/total_rollup | ✘ 未实现 |
| R9 | 人工明细=汇总直接人工×产量 | ✔ labor_total | ✘ 未实现 |
| R10 | 明细行必须有同键汇总父行 | ✔ MISSING_PARENT | ✘ 未实现（明细可独立导入） |
| R11 | 主键重复 | ✔ DUPLICATE_PRIMARY_KEY | 部分：同键金额重复仅 warning 并累加；产量冲突报错 |
| R12 | 月份格式 | ✔ strptime('%Y-%m') 行级 INVALID_MONTH | ✔ normalize_period 支持 2026年5月/2026-05 等，失败行级报错 |
| R13 | 期间连续性 | ✔ 连续性分组缺口检测 | ✘ 未实现 |
| R14 | 工厂/规格对主数据 | ✔ UNKNOWN_FACTORY_PRODUCT_OR_SPECIFICATION | ✘ 未实现（任意工厂字符串可入库） |
| R15 | 行业分位数单调 | ✔ INVALID_INDUSTRY_QUANTILES | —（行业文件走 knowledge 路径，无数值校验） |
| R16 | 产量与成本独立、同键产量冲突 | ✔（join 校验 *_quantity_join） | ✔ 冲突产量报错（含跨文件 IMPORT_QUANTITY_CONFLICT） |
| R17 | 币种/单位一致 | ✔（run 时 ENTERPRISE_UNIT/CURRENCY_CONFLICT 在注册处） | ✔ register_enterprise 注册时统一校验 |

## 3. 错误定位能力对照

- ingestion：`row_key = 文件名:行号`（`_read` line 118，enumerate 起点 2）+ field 列名 → **文件/行/列** 齐。
- data_import：错误 dict 含 `file/sheet/row(1 基，含表头偏移)/reason(中文含列名)`（data_import.py:265-333）→ **文件/表/行/列** 齐；tests/test_data_import.py::test_error_rows_point_to_file_row_and_reason 实证 row=3 定位正确。
- run_data_parse 终态消息：`数据处理失败，{步骤}报错：{前 3 条原因}（共 N 个错误）`（import_pipeline.py:284-285,317-319）；tests/test_import_v2.py::test_data_parse_failure_message_contract 实证。

---

## 4. 发现列表（含反证）

### F-1 【P0】用户自助导入把"元/盒"单位成本列当绝对金额发布；映射的 总成本(元) 被静默丢弃 → 发布后所有绝对金额错误约"产量"倍
- 证据链：
  1. 预设映射 `data_import.py:60-64` 将 `直接材料(元/盒)/直接人工(元/盒)/制造费用(元/盒)` → `element:*`；`总成本(元)`→`total_cost`。预算同（`import_pipeline.py:33-35`）。
  2. `publish_business`/`publish_business_batch` 仅发布 `elements_present`（排除 `__total__`）的要素事实（`data_import.py:433-448, 703-716`）；`amounts['__total__']`（即 481500 这类真总成本）**从不生成任何 fact**，只进从未被发布的 `totals`。
  3. 下游 `industry.aggregate()`（industry.py:433-437）按 `total=Σ要素amount`、`unit_cost=total/quantity` 计算。导入 2026-01 一厂银黄：material=6.83、labor=1.52、overhead=2.35 → total_cost=10.70 元、unit_cost=10.70/45000≈0.000238 元/盒；真实值 481500 元 / 10.70 元/盒。
  4. 合并优先级 cost_summary=0 最高：明细文件的正确绝对额（如人工 68400 元）被汇总的单位值（1.52）覆盖并仅记 warning（`data_import.py:674-680`）。
  5. 数据中心把全部待解析业务文件合成一个批次一个企业（`api.py:304-311` waiting_imports 全取），2025 年数据仅存在于汇总文件 → 同一数据集内绝对额与单位值混流。
- 反证（均已排除）：① `_options_for` 是否处理 元/盒？否——只查"万元"与产量单位提示（import_pipeline.py:159-170）。② 下游是否乘产量？`industry.aggregate` 只做 Σ与÷；乘产量的只有 ingestion/metrics 的原始 CSV 路径（metrics.py:76，作用于 r['data'] 原始行而非导入 facts）。③ 是否有其他发布路径保留 total？`publish_business` 与 batch 两处均无。④ 测试是否锁定了正确量纲？tests/test_import_v2.py::test_summary_and_detail_no_double_count 仅断言 fact 数量=1，未断言金额值（材料 2026-02 发布值 3.50 而非 21800/54540 量级）。⑤ 要素占比（share）因分子分母同为单位值而"碰巧正确"，环比率也大体保持——但 report 展示的 总成本/单位成本 绝对值全错，属静默错数。
- 影响：数据中心（自助接入）主流程对题包标准 成本汇总/预算 文件必然产生错误金额；报告 `Σ金额/Σ独立产量`、`Σ成本明细金额` 直接错误。

### F-2 【P1】自助导入校验完全缺失题面已知算术不变量（R4-R10、R13、R14）
- `validate_business`（data_import.py:245-343）只做结构/类型/产量冲突检查；搜索 `单位成本|总成本.*产量|100|rollup` 于 data_import.py/import_pipeline.py：无一命中一致性算式。不变量仅存在于 ingestion.py（打包数据路径）。
- 违反时行为：自助导入对"总成本≠产量×单位成本""材料占比≠100%""5 类费用合计≠汇总制造费用"的文件**照常发布**；F-1 正是因为缺 R4/R5 才未被拦截。
- 反证：register_enterprise 只校验单位/币种/版本/层级（industry.py:280-318），无数值一致性；已排除。

### F-3 【P1】再发布非原子：企业数据文件先写、注册后验，失败即破坏旧版本
- `publish_business(_batch)` 直接写 `enterprises/<id>/facts.json`、`enterprise.json`（data_import.py:452-463, 720-731），之后才 `register_enterprise` 做完整合同校验（含 aggregate 试算，可能抛 INCOMPLETE_PERIOD/EMPTY_DATASET 等）。enterprise_id 由 (enterprise_name, pack_id) 哈希决定（:380,:614）——同名重导（流水线还会自动生成同名"中药一厂（导入）"，import_pipeline.py:291-293）**覆盖同一目录**。注册失败时旧注册条目仍指向已被覆盖的目录 → 旧可用数据被破坏，且导入路径无快照/回滚（快照仅 ingestion parquet 路径有）。
- 反证：注册表写入本身原子（industry.py:312-318 tempfile+os.replace+锁），docstring 声称"注册表在写入前完成全部校验"——但被写的注册表条目校验先于**注册表**写入成立，数据文件却在调用注册**之前**已被覆盖；该反证不成立，缺陷成立。首次发布失败仅留孤儿目录（无害），唯再发布场景破坏旧数据。

### F-4 【P2】发布成功后归因阶段失败会把已发布数据整体标为失败
- `run_data_parse`：`publish_business_batch`（:298）成功注册后才 `_attribution_overview`（:301）；若 catalog/分析抛出未被逐产品捕获的异常 → 泛型 except → `_fail` 把**全部** import 记录标 PARSE_FAILED、job FAILED（:318-321），但企业已注册生效。状态与事实不一致；重试会重导（幂等覆盖，因 F-3 面again）。
- 反证：`_attribution_overview` 内仅捕获 (ValueError,KeyError,IndexError)（:190）；`scoped_catalog`=context_catalog 在 enterprise 刚注册成功后一般不抛——风险低但存在（如磁盘/序列化异常），维持 P2。

### F-5 【P2】api.data_parse 先行批量置 PARSING，作业崩溃后记录永久卡死
- api.py:311 在 enqueue 后立即把所有 waiting 记录标 PARSING；若 worker 未运行/进程重启，记录停留在 PARSING，而 `waiting_imports` 只认 UPLOADED/PARSE_FAILED（data_import.py:583）→ 无任何端点可将其复位，数据滞留。
- 反证：worker 正常路径会在失败时改 PARSE_FAILED；但"作业未被执行"场景（崩溃/重启）无恢复路径；未发现 reset 端点（搜索 api.py 无 PARSING 复位）。

### F-6 【P2】validate_business 的 total_by_key 计算依赖列序（潜伏）
- data_import.py:323-329：`__total__` 先入 dict 则要素再**加到总成本上**。当前题包列序（总成本在最后）不触发；该值现仅用于产量≤0 检查的键枚举（:330-333）未外泄——故降为潜伏缺陷（publish 两处的 totals 已用第二轮显式覆盖修正，:415-422, 683-690）。若未来复用 total_by_key 做校验会出错。

### F-7 【P2】同文件内重复主键行仅 warning 并累加（口径依赖用户自查）
- data_import.py:320-322：同键金额重复→warnings+累加（长表重复导入汇总行会双计，仅一句"请确认"）。跨文件同优先级异值会硬失败（:671-673）✔；ingestion 对主键重复硬失败（R11）——自助路径为"部分"。

### F-8 【P2】publish_knowledge 的 docx 解析忽略表格
- data_import.py:482-485 只取 paragraphs；同文件 `check_template`（:521-525）却专门扫表格（注释称题包 88 个占位符在表格内）。知识型 docx 的表格内容全部丢失，且 ≥30 字符门槛可能仍通过（正文有文字）→ 静默内容缺失。

### F-9 【P3】批量失败把所有入选文件（含未到出错步骤的）统一标 PARSE_FAILED
- `_fail`（import_pipeline.py:80-88）对 `records` 全量置败；重试语义 OK（全部重跑），但无法区分哪个文件致败（终态消息只含首个文件前 3 条，:610-612 首个失败文件名会带上 ✔ 部分定位）。

### F-10 【P3】XLSX 公式无缓存值时静默为空；sheet 静默回落首个
- `_read_table` data_only=True（:193）取缓存值——未计算公式→None→''→该值按缺失跳过，无告警；`target = sheet if sheet in names else names[0]`（:195）选错 sheet 无提示。

### F-11 【P3】CSV 注入（=、+、-、@ 前缀）未做任何消毒
- 单元格原样进入 SQLite meta/preview 响应/knowledge 文本/facts（数值角色会因 parse_number 失败而报错 ✔，但文本/知识路径原样落盘）。反证：仓库内未发现 CSV/Excel 导出端点（api.py 无 text/csv 导出），前端框架默认 HTML 转义 → 现状风险低（INFO~P3）。

### F-12 【P3】上传大小限制在读入内存之后
- api.py:355-357 `await file.read()` 全量入内存后才由 create_upload 判 50MB（data_import.py:155-156）——超大请求先耗内存（FastAPI>1MB 落磁盘临时文件，风险有限）。

### F-13 【P3】杂项
- 同内容同 kind 不同 data_type 重传：幂等返回旧记录，data_type 不更新（data_import.py:166-167）。
- CSV 重复表头未检测（dict(zip) 折叠列）；表头固定第 1 行，无标题行偏移识别。
- 多列映射同一角色时静默后者覆盖（role_of 循环）。
- `mark_import_status` 无迁移合法性校验；'PUBLISHED' 定义了但全仓库无调用（api 单文件发布路径走 meta['published']，不置状态）。
- ingestion audit 容差 1e-6 对"总成本=产量×单位成本"过严：真实数据单位成本两位舍入时可能误报（题包数据构造为精确值，静态确认全部通过；实测样例 45000×10.7=481500.0 精确）。
- ingestion:158 负数仅对 kind='industry' 豁免（设计性豁免，无注释说明）。
- 连续性失败错误结构（group/months）与行级错误结构不一致。
- `inspect_zip` 为死代码（zip 防护从未接入上传链——上传仅 csv/xlsx/pdf/docx/txt，无 zip 面，风险关闭）。

### F-14 【INFO】满足项（正面确认）
- 编码：BOM/utf-8-sig→utf-8→gb18030（覆盖 GBK）顺序正确；XLSX 无需编码；GBK 文件可导入。
- 月份解析：2026年5月/2026-05/202603/2026/5 全支持；13 月、区间串（2026年1-6月）正确报行级错误。
- 50MB 上限、扩展名×kind 白名单、原始字节永久保留（original.* 不动）、哈希幂等重传。
- 来源追踪：facts 带 source_row（文件名:行 / batch:key）+source_snapshot（单文件=文件 sha256；批次=合并哈希）；导入记录存 filename/sha256/encoding/size。
- 产量独立事实：同键冲突产量硬失败（文件内+跨文件）；长表产量只计一次防重复聚合（data_import.py:303-309）。
- 合并防双计：优先级+同优先级异值硬失败+覆盖留痕（merge_warnings）。
- 能力预览由数据决定（缺产量不给单位成本、缺基期不给同比、无驱动事实不给量价分解）——诚实声明。
- 知识空解析显式失败（扫描件不谎报成功，:493-494）。
- ingestion 原子快照：staging→os.replace、内容哈希版本化 parquet 保留（可回滚）、TOCTOU 合同复查、load_rows 路径校验。
- 错误定位（两路径）文件/表/行/（列）齐备，且有测试锁定。
- local_validation SSRF 门禁满足其窄目的。
- XLSX 公式取值用 data_only=True（有缓存值时正确取值而非公式串）。

---

## 5. 判定统计

| 判定 | 数量 | 条目 |
|---|---|---|
| 满足 | 12 | 编码检测/月份解析/大小与类型白名单/原件保留与幂等/来源追踪/产量独立与冲突/跨文件防双计/能力预览/知识空解析显式失败/ingestion 原子快照与不变量（R1-R17 左列）/错误定位（两路径）/local_validation 门禁 |
| 部分满足 | 6 | R2 R3 R11（自助路径行级必填/负数/主键重复）；模板章节兼容（前缀匹配）；模型映射数值防护（仅护金额列）；docx 知识解析（缺表格） |
| 不满足 | 5 | R4-R10 R13 R14 于自助路径（F-2）；绝对金额量纲（F-1）；再发布原子性/导入路径快照回滚（F-3）；发布后失败状态一致性（F-4）；卡死 PARSING 恢复（F-5） |
| 未实现 | 3 | 长表（行存要素名）映射角色（搜索 `element` 角色/长表：仅 element:固定三要素命中）；XLSX 未算公式告警；zip 防护接入（inspect_zip 无调用） |
| 待实测 | 2 | GBK 编码题包文件导入端到端（静态确认 gb18030 路径正确）；真实舍入数据下 ingestion 1e-6 容差误报率（题包数据精确无此问题） |

严重度：P0×1（F-1）、P1×2（F-2、F-3）、P2×5（F-4..F-8）、P3×4（F-9..F-12 + F-13 杂项计 1 组）、INFO×1（F-14 及死代码等）。
