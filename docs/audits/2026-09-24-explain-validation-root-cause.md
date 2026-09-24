# 「部分解释未通过数字与证据自动校验」根因分析与解决方案（待审批）

- 日期：2026-09-24
- 状态：**已实施**（2026-09-24 用户审批通过，commit 见 git log）
- 影响面：分析报告/跨厂对标页顶部"解释来源…部分解释未通过数字与证据自动校验，已降级为基础分析"；`narrative.status=DEGRADED`

## 一、现象

2026-09-24 实测：该导入企业上下文（pharmaceutical:imp-c262c19d）**全部 14 个报告任务均为 DEGRADED**，
`failure_reasons` 首条即 `RuntimeError: MODEL_CALL_BUDGET_REACHED`，伴随 3 个要素
`NECESSARY_EXPLANATION_MISSING` 与 3 条 `ALERT_EXPLANATION_MISSING`。

## 二、根因链（按因果顺序）

### 直接根因：模型调用预算耗尽（占当前问题的 100%）

- 位置：`backend/pharma/narrative.py` ModelGateway，`max_calls = int(os.getenv('PHARMA_MODEL_MAX_CALLS','40'))`。
- 预算是**进程级累计**：后端服务由看门狗长期保活（重启用 `scripts/manage.py stop/start` 才清零），
  而生成一次完整报告需要多次模型调用（每要素 hypothesis+修复循环≤2 次、告警覆盖、汇总等，
  实测一次报告消耗约 20+ 次调用）。**正常运行 1～2 份报告即把 40 次预算耗尽**，
  之后所有报告直接 `MODEL_CALL_BUDGET_REACHED` → 零模型解释 → 全部降级。
- 结论：这不是"算法校验错误"，而是**预算参数与长时服务形态不匹配**。2026-09-24 18:30 重启后
  仅两轮报告即再次耗尽，复现闭环。

### 连锁反应（预算耗尽后必然出现）

1. `model_findings` 为空 → 每个有差额的要素报 `NECESSARY_EXPLANATION_MISSING`；
2. 每条 ±10% 告警无模型解释引用 → `ALERT_EXPLANATION_MISSING`；
3. `narrative.status=DEGRADED` → 前端显示"部分解释未通过数字与证据自动校验"（该文案实为
   status!=='PASS' 的统一展示，见 `presentation.tsx` AnalysisStatus）；
4. DEGRADED 结果按版本指纹写入缓存（`narrative.py:1195` 附近），重启前一直复用；
   "重新生成（忽略缓存）"（retry=true）可绕过，但预算未恢复时依旧失败。

### 深层原因（预算充足时仍可能误伤合法解释，属第 9 项所述"算法问题"的其余部分）

校验器 `validate_findings`（narrative.py:512-659）的以下合同对模型输出过于严苛：

| # | 规则 | 误伤场景 |
|---|------|---------|
| 1 | 自由数字禁令：扣除槽位/期间/引文后残留任何阿拉伯数字或"中文数词+单位"即拒（含年份） | "2026 年以来…"这种背景句直接判失败 |
| 2 | 四舍五入简写绑定（:446-509）：仅当百分号/单位一致、ROUND_HALF_UP 唯一匹配时放行 | "约 77%"对应 76.92% 的整数简写被拒；一位小数简写不支持；多候选歧义即拒 |
| 3 | 证据引用必须在**本次检索命中集合**内（:540-550） | 文档库中存在但检索未召回的证据 → "unknown evidence"，即使引用真实存在 |
| 4 | 引文须逐字（≥4 字）包含于证据原文 | 模型做任何转述/标点/空白差异即拒 |
| 5 | hypothesis 合同：须同时有 metric_refs+evidence_refs+missing_evidence；正文须含"可能/尚不能/待核"等词；与引文共享二字词；缺证项≥4 字无句读且含具体记录名词 | 句式稍自然的假设即被拒 |
| 6 | insufficient_evidence 合同：**每个分句**都须含"不能/无法/不足/缺少/需核…"之一 | 正常书面语几乎必然违反 |
| 7 | 身份白名单 `VERIFIED_ALIASES` 仅含 `glm-5.3-flash`（:32） | 换模型（如 glm-5.3、DeepSeek 做 analysis 路由）时返回 model 字段不在白名单 → MISMATCH → 整体降级 |

## 二·五、实施记录（2026-09-24 已获批）

### A 止血
- `narrative.py` ModelGateway：`PHARMA_MODEL_MAX_CALLS` 默认 40→300（按自然日窗口保持不变，该窗口语义由并行审查轮已落地的"按日计数"实现，等价于方案 B 的"不再永久锁死"意图）。
- 前端 `presentation.tsx` 新增 `readableFailureReasons`：failure_reasons 分类翻译（预算耗尽/缺解释要素/告警未覆盖/身份未核验/知识库异常/参数被拒），AnalysisStatus 展示可读原因列表。

### C 校验合同放宽（narrative.py，PROMPT_VERSION v22 / VALIDATOR_VERSION claim-contract-v11-relaxed-evidence-quote）
- C1：`_rounded_metric_bindings` 去掉整数简写守卫（旧政策"77% 不能洗白 76.92%"按审批反转）；唯一匹配+方向符号+单位一致保持，歧义仍拒。
- C2：新增 `_normalized_text`/`_quote_supported`：引文比对去空白、统一引号破折号，支持"片段1……片段2"顺序省略拼接。
- C3：`validate_findings` 证据未进本次检索命中集合时查全库（新增 `Knowledge.evidence_in_library`，按上下文命名空间+版本缓存 by-id 映射）；库内存在且适用性通过→放行并写 `evidence_rescued` 留痕；库内不存在或不适用照旧拒绝。
- C4：`_insufficient_contract` 分句级→句级（逗号从句不再单独要求限定词，纯肯定因果句仍拒）；系统提示词同步。
- C5：身份白名单支持环境变量 `PHARMA_MODEL_VERIFIED_ALIASES`（"请求名:返回名,…"），静态探测白名单优先。
- C6：见 A 的前端分类翻译。

### 测试与验证
- 新增 `tests/test_relaxed_contracts_20260924.py`（13 项：简写绑定/引文归一化/句级合同/全库救援 monkeypatch/别名环境变量/预算默认值），改写 `tests/test_rounded_metric_binding.py` 三处 v10 断言为 v11 语义。
- 全量回归 548 passed + 1 skipped；前端 tsc 干净、`vite build` 成功。
- 端到端验证进行中（生成报告观察 narrative 状态与模型解释恢复）。

## 三、解决方案（供审批，按优先级）

### A. 立即止血（配置级，不改算法，约 5 分钟）

- 启动环境设置 `PHARMA_MODEL_MAX_CALLS=300`（或按日均报告量×25 估算），
  并在 `scripts/manage.py start` 或 `.env` 中固化；预算按"每任务"观察，超限时明确报
  "模型调用预算耗尽"而非笼统校验失败。
- 前端把 `MODEL_CALL_BUDGET_REACHED` 翻译成用户可读文案并给出"重启服务或调大预算"指引。

### B. 预算语义修正（小改，建议与 A 一起）

- `max_calls` 从"进程累计"改为"每任务（job）计数"，进程内超限告警但不跨任务累积；
  或改为滑动窗口（如每小时 N 次）。

### C. 校验合同放宽（算法修正主体，需配套测试）

1. 数字简写：允许整数与一位小数简写，前提是**唯一匹配**注册值且方向符号一致；方向词冲突仍拒。
2. 引文匹配：比对前做空白/引号/标点归一化；允许"片段 1…片段 2"式省略拼接。
3. 证据存在性：检索未命中但全库存在且适用性通过的引用，降级为"警告"而非"失败"。
4. insufficient_evidence 分句级 → 句级（每句含一个不确定词即可）。
5. 身份白名单：按"端点+模型族"核验（探测一次后缓存），或把已验证别名改为可配置清单。
6. 修好后把 `narrative` 的 `failure_reasons` 分类透传到前端，分别显示
   "预算耗尽 / 模型身份未核验 / 数字合同未过 / 证据引用未过"，不再笼统一句话。

### D. 演示增强（可选）

- 规则建议（recommendation）当前刻意不带证据引用；可为规则建议附上检索命中的
  参考文档（标注"参考依据，非因果证据"），让"查看证据依据"在规则模式下也有内容。

## 四、2026-09-24 已同步修复（与本问题相关联、不属于第 9 项审批范围）

- 知识库从未为导入上下文构建（`/api/kb` 返回 NOT_BUILT）→ 已构建，证据检索恢复
  `status=PASS`（3 个来源），证据适用分项由"未通过"转"通过"。
- 建议三条完全相同（narrative.py:989 硬编码）→ 已按要素差异化（材料/人工/制造费用各有专属建议），
  前端整改下拉按"建议+核查对象"去重。
- `material` 英文直出（industry.py:782 `pack.elements.get(key,key)` 回退，manifest 只有复数键）→
  三个行业包 manifest 均已补 `material` 单数别名，界面显示"材料"。

## 五、验证记录

- `MODEL_CALL_BUDGET_REACHED` 实证：jobs 列表 14/14 DEGRADED + failure_reasons 原文；
- 一次报告的模型调用次数：查 `.runtime/model_gateway.sqlite3` 的 `calls` 表（可复核）；
- 重启后首份报告证据链恢复：evidence=3、status=PASS（18:30 会话内实测）。
