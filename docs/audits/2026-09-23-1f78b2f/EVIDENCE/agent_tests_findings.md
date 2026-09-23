# 测试有效性审查（agent_tests）— yaoheng-zhixi @ 1f78b2f

范围：`药衡智析_增量源码交接/public_source_candidate/05_原型/tests/`（37 个 test_*.py + conftest.py，共 4618 行）+ `frontend/record_demo_20260918.test.mjs`（23 行）。
背景：CI 声称 374 绿。`scripts/verify.py:57` 的 regression 维度 = `pytest -q tests/`，即 374 仅指后端 pytest。
审查者无视觉能力；只读审查，未运行测试。所有行号以 1f78b2f worktree 为准。

统计：304 个顶层 `def test_` + 34 处 `@pytest.mark.parametrize` 展开 ≈ 374，与声称数量级一致（**待主审实跑确认**）。
全局扫描：**无 xfail、无 `assert True`、无 `except: pass`、无 pytest.mark.skip**；仅 1 处环境条件 skip（见 R1）。

---

## 一、逐文件记录表

| 文件 | 测什么 | 有效性评价 | 红旗 |
|---|---|---|---|
| conftest.py (11行) | 清空 API key 环境变量、固定模型名/端点 | 满足。防测试继承开发者凭据，autouse 全局生效 | INFO-1：先 `import pharma.config` 再删环境变量，config 模块内已固化的值不回滚——但各测试均显式隔离，未见实际泄漏面 |
| test_local_validation.py (12) | require_loopback 拒外网/带凭据/0.0.0.0；simulation 必须显式；禁重定向 | 满足。真实负例断言 ValueError | — |
| test_recovery.py (23) | JobStore 断电重建后 checkpoint/快照/evidence 复原；TOC 更新期 NOT_FINAL 禁下载 | 满足。真实 SQLite 状态重建 | — |
| test_concurrency.py (31) | 16 线程 Barrier 同入队/同 draft 收敛为单 job；`from test_actions import ActionStore` | 满足。真实并发，非 mock | INFO-2：测试文件互相 import（test_concurrency→test_actions、test_trust_regressions→test_integration_safety、test_integration_safety→test_report_version_cache），耦合为 P3 |
| test_verifier_provenance.py (36) | verify.py 的 documentation_only_since / check_receipt 绑定 run/commit/job/bytes | 满足。真实临时 git 仓库 + 篡改回执负例 | — |
| test_source_revision.py (43) | 源码指纹不搜父级 git、私有文件（.env/secret/交付物/dist）不入指纹；显式 git root 走 commit | 满足。monkeypatch Path.read_bytes 断言禁读清单；Windows 无法建符号链接时跳过该攻击面（诚实注明） | — |
| test_benchmark_integration_contract.py (46) | 竞赛 benchmark 走绑定检索（scoped snapshot 传入 retrieve）；reference worker 把跨厂指标 metric_refs 一并传给 generate | 满足。mock 打在 api.selected_context/benchmark_analysis 边界，断言"传入的正是 snapshot 的 analysis_context"，属接线验证非自洽 | — |
| test_knowledge_source_selection.py (47) | 企业知识入口只读显式 JSON 不扫目录；同 ID 双文件版本不同；显式文件不复用他人索引 | 满足。真实 Knowledge 构建 | — |
| test_demo_deck_binding.py (52) | build_demo_deck 只加载哈希绑定的 report；未完成场景显示"待生成"；篡改 bytes/snapshot/回执 run/attempt/job 均拒绝 | 满足。四组篡改负例 | — |
| test_private_configuration.py (57) | 私有术语/主数据 JSON schema 校验、动态生效、版本指纹变化；quote_matches_product 不误匹配 | 满足 | — |
| test_knowledge_supplement.py (58) | 竞赛默认上下文合并补充知识目录（进指纹、可检索、带来源）；显式 source_dir/files 不追加 | 满足 | — |
| test_integration_safety.py (61) | Action edit 合同拒不可执行载荷；失败通知不算已发；畸形远端不抹已验证送达；DEGRADED 复用完成结果；review 哈希读产物字节；outbox 在报告线程阻塞时仍推进 | 满足。MockTransport/httpx 层故障注入真实 | — |
| test_settings_security.py (62) | key_file 只许 RUNTIME/keys 内文件名（防任意读取外发）；base_url 覆盖限 https/回环；API token 401/放行 | 满足。含 `../../etc/passwd`、`C:/Users/secret.txt` 负例 | — |
| test_docx_compat.py (82) | 复刻 2026-09-22 事故（ET 往返改前缀致 Word 拒开）：校验器必须识别悬空 mc:Ignorable；干净不误报；install/normalize/render 产物过出厂校验 | 满足。故障复刻→闸门→管线三段完整 | — |
| test_trust_regressions.py (82) | API 层 PUT 错型返 4xx 且草稿不动；POST 回执须全量对账否则 CONFLICT；超时 POST→GET 查询保持已证回执；损坏缓存重建产物但复用已验叙事；评审同步投影 | 满足。高质量故障注入 | — |
| test_report_captions.py (85) | 表/图题注仅动态表加；数值列宽保护；核心结论无 None、缺数据跳过 | 满足。手写期望（614950.00/17.57/76.9% 来自 fixture 字面量） | — |
| test_repair_units_dates.py (86) | 叙事修复的不可变单元（已通过的解释冻结、仅修复失败 action）；月份规范化仅在界内；deadline 工作日类型化且 0/31/混合数字拒绝 | 满足。MockTransport 双轮对话真实 | — |
| test_native_toc.py (94) | 原生 TOC 域结构（不标 dirty 防弹窗）；H2 入目录 H3 不入；字号层级；截断补全；NBSP 非 U+FEFF | 满足。精确 XML 断言 | — |
| test_synthetic_plant2_details.py (94) | 合成明细默认停用（回纯题包口径）；显式启用后 ingest manifest 标注、二厂明细带 data_label、一厂不带 | 部分满足。**依赖真实题包数据与真实厂名（中药一厂/二厂、六味地黄胶囊）+ competition_configuration 外部目录**；`importlib.reload(config)` 真改全局模块状态（有 try/finally 恢复，但其他模块早先 `from config import X` 的引用不受 reload 影响，见 R2） | R2 |
| test_benchmark_explanation_contract.py (98) | 缺 benchmark 解释不能被其他 section 通过掩盖；跨厂 finding 只绑跨厂指标；无跨厂指标不回退月度指标；不可比上下文不许承诺对标归因；模糊/伪装证据文档拒收 | 满足。8 正例 + 9 负例参数化 | — |
| test_data_import.py (99) | 宽表上传→校验能力→发布全链；错误行指到文件行号；产量冲突；映射指纹复用；设置密钥不回显；URL 内联凭据拒绝 | 满足。真实注册链路（隔离 runtime） | — |
| test_graph.py (104) | 知识图谱：康熙部首归一（⻩→黄）、处方剂量抽取、工艺链（链首药材不作工序）、版本化缓存、扩展词排除查询词、未知产品/空图/NOT_BUILT | 满足。FakeKnowledge 仅提供 status+分片，图谱逻辑真实 | — |
| test_report_version_cache.py (105) | 报告缓存四版本（validator/parser/terminology/retrieval_policy）任一变化不命中；worker 拒变化版本；缺版本契约拒绝；archive 无父 git 发现 | 满足。`complete_with_artifacts` 内置护栏：ARTIFACTS 未隔离即 AssertionError——**历史桩文件污染交付目录问题已有代码级根治** | — |
| test_actions.py (108) | 确认幂等；超时对账不重发（POST 恰一次）；400 冲突/422/断网/远端重启不重发；编辑须重新确认；draft 重建不覆盖 | 满足。RPA 关键路径故障注入最完整的文件 | — |
| test_rounded_metric_binding.py (115) | 注册值四舍五入简写唯一绑定（方向词/符号/单位族匹配），整数简写不能洗分数值、歧义不绑、ISO 日期不当数字；编造数字仍拒 | 满足。expected 全手写字面量（-15.2152.../76.923.../35000），独立于被测函数 | — |
| test_dashboard.py (123) | 焦点分析双阈值+零基期不算变动；模型队列显式配置+失败不重排；产品月网格缺月 MISSING、精确值不丢精度；focus opt-in；版本化缓存 | 满足。`Decimal(result)==Decimal('10.0001')` 精确断言 | — |
| test_reviews.py (124) | 评审必填校验；有效评审解锁人工维度；无评审 PENDING 且总体如实 FAIL；产物哈希变化失效；逐条证据适用性替代聚合布尔；FAIL 理由禁"全部通过"；草稿/正式下载合同 | 满足 | — |
| test_purpose_retrieval.py (127) | 目的检索：事件记录顶替通用头不扩 limit；错产品/期/厂/无日期不补；已覆盖不额外查询；行业不继承制药查询；策略拒无界查询；图谱扩展只改关键词查询不改向量查询 | 满足。计数 stub 断言调用序列，语义真实 | — |
| test_forecasting.py (133) | 线性序列保斜率（14/15 手写）；平序列零区间；跨年月份；不足历史如实报；horizon 界；重复/乱序月拒绝；NaN 阻断；负预测告警；快照级覆盖要素；10-20-30→40；缺月 NON_CONTIGUOUS；OLS 初始化抗次月尖峰；滚动留出 MAE 如实报告；真实题包银黄序列留出 MAE<0.219 回归锚 | 满足。expected 全部手写独立推导 | — |
| test_attribution.py (147) | JSD 已知值（ln2 对称）；两因子 Shapley 精确可加+顺序无关；局部化 EP=100%（材料+1.00→UC+1.00）；总额 Shapley 拆分 350=5×150−4×100；DiD τ̂=1.0000+安慰剂<0.05；无对照厂 UNAVAILABLE；价格信号有界 30/41.7≈0.72；排序降序+标签；同输入同输出；缺基期 ValueError | 满足。**expected 全部手写独立算术，未调用被测引擎复算** | — |
| test_reference_report_contract.py (147) | 渲染即绑定 PASS；核心数字互换/附录修复→FAIL（手写期望 ['3600.00 元','120.00 件','30.00 元/件']）；专用指标值与单位都查；正确数字错位置 FAIL；环比/要素/单位/重复行负例；对标表绑 comparison；同比 N/A 无 %；冻结模板不重载；keep_with_next | 满足。篡改式测试证明 verify 非纯自洽 | R3（见红旗节） |
| test_gateway_failover.py (169) | 1113 额度耗尽切 Coding Plan 且记录 endpoint；无备用立即失败不重试；普通 429 同端点退避；400 不切；主成功不碰备用；他厂牌不fallback；Coding 覆盖不得收主凭据；失败尝试留痕无密钥；路由不能借他人凭据；GLM env key 按供应商作用域；不随重定向、查询串密钥不落日志；网络失败留痕 | 满足。模型网关故障注入最完整的文件 | — |
| test_decision.py (175) | 确定性决策（缺报告/同快照/过期/他选/失败任务不算）；advisory 形状校验、坏形状不改决策、无 key 降级、未验证身份拒绝、反方向自由文本拒绝、未绑定/捏造 signal 拒绝；台账绑定；路由回退与环境覆盖 | 满足 | — |
| test_report_layout_direction.py (216) | 数字-单位 NBSP 组保 run 与书签；style_reader 不覆盖模板样式；对标方向跟随实际左右（禁"二厂减一厂"硬编码）；图例跟随方向；模板身份按角色清洗；页脚重建；模型缺证文本绑实际 section 且移入表格不能通过；verify_docx 删正文 FAIL；模板散文重写不改插入文本；季度对标保留 0.0022 小差异；真实 PDF 数字不折行+页脚间隙 | 满足。含 matplotlib legend monkeypatch 但断言的是最终图例文本 | R1（195 行 LibreOffice skip） |
| test_evidence_contracts.py (298) | 缺证声明禁伪装确定结论；BM25 先过滤范围再截断（注入 101 chunk 证明目标产品排第 100 也命中）；每条 alert（含 total 基）须模型解释；部分覆盖不能 PASS；action 字段类型化渲染拒残留占位符；同 evidence_id 按企业+行业隔离；生成缓存 9 种输入变化逐一失效；向量查询只收适用候选 id；原子构建失败保留旧快照；并发同产品同文档 id 隔离；三参考包端到端（mock 解释）语义合法短语白名单 | 满足。含直接操纵 fts.sqlite 的白盒测试（依赖实现细节，但断言的是排序语义） | — |
| test_correctness_fixes.py (394) | fix1-9 定向回归：对标单位随口径且校验器能抓单位错标；kb/search 完整传递工厂与模式；验收合同版本化（未知版本/旧别名 fail-closed）；叙事路由贯穿指纹；DEGRADED 重试建新 job 留旧结果；决策检查产物健康且异常 fail-closed；任务列表先范围后分页（120/30 用例防全局前 100 吞历史）；启动须 worker 心跳（真起 HTTPServer）；指标合同跨路径成立且能抓单位漂移 | 满足。含真实题包数据 `analyze('中药一厂','银黄口服液')`（数据在仓库内，合理） | — |
| test_import_v2.py (411) | 类型化上传与错型拒绝；预览 table/text/pdf；解析流水线发布+进度+消息合同；失败消息合同；**汇总与明细防双计（金额以汇总为准）**；知识构建流水线（_FakeKnowledge 桩 build）；模板解析安装/缺章节失败；模型注册表厂商/档位/努力映射；错档拒绝；向量切换缺路径/缺分析模型消息；目录默认赛题不含合成；路由密钥跨主机存活；None 清理；向量维度惰性探测 | 部分满足。多数真实；但 knowledge.build 与 _extraction_mapping/_analysis_hypotheses/_template_binding_analysis 均被桩替换（见 R4） | R4、R5 |
| test_industry.py (463) | 金标算术手写（3600/120/30、2400/12/3、9400/320/29.375、季度对标 58.75/29.375/100、环比 -15/30/-50.0）；NaN/Infinity 拒绝；单位转换需证据（t→kg=1000 允许，件→kg 拒）；混币拒绝；产量不被 join 重复计；冲突产量/汇总-明细混层/WIP/政策版本/单位不一致全拒绝；空导入不能替换活动快照；CSV 往返+失败不覆盖；零产量=未定义非零成本；包装转换需产品绑定证据+范围校验；对齐桥（单位+政策）显式才允许且因子/范围校验；多企业同包同产品同 evidence_id 隔离；驱动单位转换（分钟→小时、MWh→kWh）不改语义；无效 optional 拒绝；重复驱动导出不双计专用指标；对象级覆盖检查；策略输出单位校验；预算重建源模式不可比；跨厂仅放宽厂不放宽源模式；同 id 不同导出算子拒；模板冻结与漂移拒；金标环比锚 -50.0 | 满足。手工金标 + 溯源结构双轨 | R3 |
| frontend/record_demo_20260918.test.mjs (23) | 录制脚本 requireLoopback 拒外网/凭据/file://；validateHealth 拒外网/非模拟/未验证模式；validateJob 绑 run/选择/双产物哈希、FAILED/缺 pdf 拒 | 满足（就其自身而言）。**但不在任何 CI 入口**：package.json 无 test script，verify.py 只跑 pytest | R0 |

---

## 二、红旗与发现（含反证）

**R0（P1）前端唯一单测不在 CI 口径内。** `frontend/record_demo_20260918.test.mjs` 存在且有效，但 `frontend/package.json` scripts 无 `test`，`scripts/verify.py:57` regression 仅 `pytest -q tests/`。反证：搜索 package.json/verify.py/CI 脚本均无 `node --test` 调用 → 374 绿不含它；RPA 录制链路（loopback 守卫、job 绑定）实际无自动化验证。

**R1（P2）一处环境条件 skip。** `test_report_layout_direction.py:195` `pytest.skip('LibreOffice unavailable')`。这是全部测试中唯一的 skip，但它是真实 PDF 渲染测试（数字不折行、页脚间隙）；若评测/CI 机无 LibreOffice，该测试静默消失且 verify.py 的 regression 维度仍绿（pytest 默认 skip 不算失败）。反证：属工具链可用性问题而非测试造假，且是尾端呈现性检查；但"374 绿"无法证明它实际执行过 → 待主审在评测环境跑 `pytest -rs` 确认 skip 数。

**R2（P2）reload 型 fixture 的全局状态污染面。** `test_synthetic_plant2_details`、`test_data_import`/`test_import_v2` 的 `isolated_runtime` 都 `importlib.reload(config)`。config 重载后，其他模块若曾 `from pharma.config import X`（模块级常量绑定）不会跟随更新——测试作者自己也知道（data_import.py fixture 注释了 ENTERPRISE_REGISTRY "reload 不会跟随 config 更新"）。反证：这些文件均用 try/finally 恢复 + monkeypatch 隔离 ENTERPRISE_REGISTRY/RUNTIME_TEMPLATES/jobs.ARTIFACTS，且 test_report_version_cache 里 guard 直接断言 ARTIFACTS 未指向真实目录；未发现当前有测试因 reload 泄漏而误绿的具体用例 → 定性为脆弱性而非现行错误。

**R3（P2，属"自洽校验"边界的系统性弱点）数值链的"中段"多为引擎自洽重算。** 分层看：
- 手写独立金标（好）：test_industry 金标 3600/120/30/29.375/58.75/-50.0、test_attribution 全手写、test_forecasting 全手写、test_reference_report_contract 表格字面量、test_report_captions 字面量。
- 自洽重算（弱）：`test_industry.py:375-408` `test_benchmark_metric_evidence_recomputes_display_and_both_sources` / `test_period_evidence_distinguishes_rate_and_contribution` 用 `Decimal(metric['numerator'])/Decimal(metric['denominator'])` 重算 display——numerator/denominator 与 display 同由 industry 引擎产出，若 numerator 本身算错（如求和口径错），这两组测试不报警；同理 `test_correctness_fixes.py:378` 用引擎自己的 `metric_contract.validate_snapshot` 验真实题包数据。
- 缓解（反证）：原始行→numerator 的链有独立锚（手写金标值直接对 `metrics[..]['value']` 断言，value=numerator/denominator；test_industry 大量 `_mutated_reference` 变异测试从 facts 原料注入篡改并断言拒绝/语义不变）。残余风险收窄为"题包真实数据的要素层算术"只有 metric_contract + fix9 一层引擎自检 + test_synthetic_plant2_details 的结构断言。判定：非 P0/P1 造假，是覆盖深度问题。

**R4（P2）关键流水线的模型段全部桩化。** test_import_v2 中 `_extraction_mapping`/`_analysis_hypotheses`/`_template_binding_analysis` 被替换为确定性桩、`Knowledge` 用 `_FakeKnowledge`。被测语义是"流水线编排/进度/消息合同"，模型行为另由 narrative 合同测试覆盖——mock 未改变被测语义（桩打在模块边界且测试明确注明"真实网关行为另有合同测试"）。反证成立 → 不算过度 mock，但意味着"导入向导的 LLM 映射建议质量"零自动化验证（仅 UI 手工路径）。

**R5（P3）一处近恒真断言。** `test_import_v2.py:410-411` `assert model_settings._probe_dimension_cached(model_dir) is None or isinstance(..., int)`——返回值不是 None 就是 int 时恒过，仅等价于"不抛错"。注释自认（stub 探测失败→None 展示降级）。反证：stub onnx 无法真探测，作者意图就是冒烟；但断言强度接近零，宜改为固定桩返回形状。

**INFO-3（根治确认）历史"桩文件落真实交付目录"问题。** 多处测试（test_report_version_cache.py:91-105 guard、test_reviews.py:76-84、test_integration_safety.py:29-35、test_correctness_fixes._complete_degraded）均先 `monkeypatch jobs.ARTIFACTS → tmp_path`，且 complete_with_artifacts 有运行时护栏 `AssertionError('测试产物根未隔离…')`。反证：护栏在每次调用时比较 `jobs.ARTIFACTS` 与 `config.ARTIFACTS`，绕过需两值 resolve 相同才触发 → 根治可信。

**INFO-4 conftest 隔离。** conftest 仅删凭据环境变量+固定模型名，不共享任何可变 fixture；每个测试自带 tmp_path 存储。未发现测试间共享状态（除测试文件互相 import 的 helper，为纯函数/子类）。

---

## 三、故障注入清单核对（任务要求逐项）

| 要求的注入 | 是否存在 | 位置 |
|---|---|---|
| 除零/零基期 | 是 | test_dashboard 零基期不告警；test_industry 零产量 unit_cost=None；test_industry:424 分母 0/缺分母双分支 |
| 缺期 | 是 | test_forecasting 缺月/不足历史 NON_CONTIGUOUS_HISTORY；test_industry INCOMPLETE_PERIOD；test_attribution BASE_PERIOD_DATA_MISSING |
| 缺预算 | 是 | test_industry:141 chemical 2026-01 mom 无基期 value=None+reason；test_dashboard MISSING 单元格 |
| 负数 | 是 | test_forecasting 负预测 negative_warning |
| 模型超时 | 是 | test_actions/test_trust_regressions ReadTimeout（HTTP 层模拟模型端超时）+ test_gateway_failover ConnectError |
| 模型限流 | 是 | test_gateway_failover 429(1113 切换/1302 同端点退避) |
| 模型格式错误 | 是 | test_repair_units_dates/test_benchmark_explanation_contract/test_evidence_concontracts 大量坏形状/编造数字/伪装文档拒收；test_decision 坏 advisory 形状 |
| RPA 断网 | 是 | test_actions ConnectError→DELIVERY_UNKNOWN 且不重发 |
| RPA 超时 | 是 | test_actions ReadTimeout→对账不二次发送（POST 恰一次） |
| RPA 重复提交 | 是 | test_actions 超时后重复 deliver_one posts==1；重复 400/422 区分 |
| RPA 重启恢复 | 是 | test_actions 404 restart→refresh 保持 SENT；test_integration_safety 畸形远端不抹已验证送达 |
| 损坏产物闸门 | 是 | test_report_version_cache/trust（缺文件/哈希变→重建）；test_demo_deck REPORT_HASH_MISMATCH；docx_compat 悬空前缀闸门 |
| 企业隔离 | 是 | test_evidence_contracts 同 evidence_id 跨企业/行业不适用；test_industry 多企业同包隔离；test_knowledge_source_selection 版本隔离 |

**但注意**：以上 RPA 注入全部打在 actions 投递层（httpx MockTransport）；`backend/pharma/synthetic_rpa.py`（本地模拟器本体）无任何直接测试；录制脚本守卫仅 mjs 测试覆盖而 mjs 不在 CI（R0）。

---

## 四、后端模块覆盖矩阵（tests/ 视角）

| 模块 | 行数 | 覆盖 | 判定 |
|---|---|---|---|
| reports.py | 1660 | captions/native_toc/layout_direction/docx_compat | 部分（最大模块，图表渲染/convert_pdf 主链、_fit 深层参数仅部分；PDF 真渲染靠 R1 的条件 skip） |
| narrative.py | 1099 | evidence_contracts/repair_units/rounded/gateway/decision | 满足（最厚） |
| industry.py | 795 | test_industry + 各处 analyze_reference | 满足 |
| data_import.py | 765 | data_import/import_v2 | 满足 |
| api.py | 574 | settings_security/trust/correctness/dashboard/version_cache | 部分：/api/catalog、/api/actions、/api/kb/search、/api/reports、/api/jobs、/api/analysis(focus) 有；**报告下载/评审提交/knowledge 端点/管理端点未见专门测试** |
| knowledge.py | 460 | 多文件 | 满足 |
| import_pipeline.py | 459 | import_v2 | 部分（编排+消息合同有，模型建议桩化 R4） |
| model_settings.py | 391 | settings_security/data_import/import_v2 | 满足 |
| metrics.py | 380 | 仅经 analyze()/analyze_reference 间接 + metric_contract | 部分：**环比/贡献度对真实题包数据无直接手写金标单测**（合成包有）；预算对比 price-volume 无 |
| ingestion.py | 307 | private_configuration/source_contract + plant2 manifest | 部分：解析器对脏 Excel/编码错位/列名变体无直接故障注入（经 data_import CSV 层部分覆盖） |
| attribution.py | 294 | test_attribution | 满足 |
| actions.py | 250 | actions/integration_safety/trust/concurrency | 满足 |
| graph.py | 226 | test_graph | 满足 |
| decision.py | 209 | test_decision | 满足 |
| model_registry.py | 187 | import_v2 | 满足 |
| forecasting.py | 186 | test_forecasting | 满足 |
| reference_report.py | 184 | reference_report_contract/correctness_fixes | 满足 |
| vector_switch.py | 155 | import_v2（仅 2 个失败路径） | 部分：成功切换路径未测 |
| worker.py | 151 | version_cache/benchmark_integration/integration_safety | 部分：dispatch_loop 有；**worker 崩溃恢复/多 job 串行语义未见**（job 恢复在 test_recovery 的 store 层有） |
| jobs.py | 138 | recovery/version_cache/correctness | 满足 |
| dashboard.py | 132 | test_dashboard | 满足 |
| context_services.py | 123 | purpose_retrieval/benchmark_integration | 满足 |
| reviews.py | 78 | test_reviews/trust | 满足 |
| docx_compat.py | 60 | test_docx_compat | 满足 |
| revision.py | 56 | test_source_revision | 满足 |
| metric_contract.py | 53 | correctness_fixes | 部分（引擎自检性质，见 R3） |
| **locks.py** | 45 | **无任何测试引用** | 未实现 |
| **industry_rules.py** | — | **无任何测试引用** | 未实现（间接可能被 industry 覆盖，无直接断言） |
| **versions.py** | 34 | 无直接（各版本常量经 version_cache 参数化覆盖） | 部分 |
| **synthetic_rpa.py** | — | **无任何测试引用** | 未实现（仅 mjs 测其消费端，且不在 CI） |

---

## 五、性质测试不变量质量（任务要求）

- 归一化幂等：style_reader 二次调用不变（test_report_layout_direction:23 `once=p.text;style_reader(doc);assert p.text==once`）——**真有**。
- 拆分汇总守恒：两因子 Shapley `c_a+c_b==总量变化` + 顺序无关（test_attribution:53-61）；汇总/明细不双计（test_import_v2:123）；重复导出不双计（test_industry:267）——**真有**。
- 单位转换一致：t→kg=1000、分钟→小时、MWh→kWh 语义不变、无证据换算拒绝、因子篡改拒绝（test_industry:43,144,153,246）——**真有**。
- 企业隔离：见故障注入表——**真有**。
- 确定性：attribution/forecasting/graph 同输入同输出断言——**真有**。

---

## 六、值得主审复核的点

1. 实跑 `pytest -q tests/ -rs` 于评测镜像：确认 374 数、确认 R1 的 LibreOffice skip 是否实际发生（PDF 呈现链是否真被验证过）。
2. 实跑 `node --test frontend/record_demo_20260918.test.mjs`（或确认它从未跑过）→ 决定 R0 定级。
3. metrics.py 对真实题包（银黄/六味）的环比/贡献度：抽 1-2 个月手算核对（当前只有引擎自洽 + 合成包金标）。
4. locks.py / synthetic_rpa.py / industry_rules.py 是否属"死代码"或隐藏关键路径（若 RPA 演示依赖 synthetic_rpa，其正确性完全无自动化验证）。
5. test_evidence_contracts 白盒直接写 fts.sqlite（:22-31, :114-135）依赖 chunks/search 表结构——schema 变更会静默改测试语义，可要求主审看其与 knowledge.py 当前 schema 一致性。
