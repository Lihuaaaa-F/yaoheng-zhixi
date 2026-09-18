# 评测报告 / Evaluation Report

> 运行 `release_20260918_5974275`（代码提交 5974275，分支 `codex/core-industry-20260917`，**正式 verify=PASS，七维度全绿，模型合同 7/7**）。
> 七场景 = 原题 S1/S2/S3/Q2 + 机械/化工/制药合成三包。本报告汇总赛题"评测要求"四项指标
> 与自动维度回执；真人评分一律 PENDING，AI 不代填。
> **English** — Evaluation for run `release_20260918_fa3c968` covering the four contest metrics
> (structure completeness, human attribution score, RPA trigger success rate, three-step format
> correctness) plus automatic receipts. Human scoring remains pending by design.

## 1. 评测场景 / Scenarios

| 场景 | 上下文 | 产品 | 期间 | 类型 |
|---|---|---|---|---|
| S1 | pharmaceutical:competition | 银黄口服液 | 2026-05 | 月度 |
| S2 | pharmaceutical:competition | 板蓝根颗粒 | 2026-05 | 专题 |
| S3 | pharmaceutical:competition | 六味地黄胶囊 | 2026-03 | 月度 |
| Q2 | pharmaceutical:competition | 原题核心产品 | 2026-Q2 | 季度 |
| mechanical | mechanical_demo:synthetic-mechanical | DEMO-01 | 2026-06 | 月度 |
| chemical | chemical_demo:synthetic-chemical | DEMO-01 | 2026-06 | 月度 |
| pharma_synthetic | pharmaceutical:synthetic-pharma | 合成制剂甲 | 2026-06 | 月度 |

模型溯源（三段式，均可核验）：
① 静态交付报告的解释 = `delivery_20260918_47c5806`（队友 DeepSeek 实调，随 release_20260918_6ff894f 发布）；
② 提示词 v18 的 GLM 验证 = `bonus_20260918_glm_v18b`（glm-5.3-flash 新鲜生成 7/7 合同 PASS，身份 VERIFIED；decision 路由 glm-4.5-air）；
③ 本运行 `release_20260918_26efd3a_air2` = 缓存复用运行（模型新增调用 0），绑定当前代码提交并正式 verify PASS。
环境：Windows 11 · Git Bash · Python 3.12 · LibreOffice 26.8。

## 2. 赛题评测指标 / Contest Metrics

### 2.1 报告结构完整度 / Structure Completeness — **程序判定 7/7 PASS**

- DOCX/PDF 双格式 7/7 生成成功；模板全部固定章节（封面/总览/要素明细/专项/总结建议）齐备。
- 验收器扫描无未解析插槽（`no_unresolved_slots=true`）；Word/PDF 页数与目录回填一致。
- 说明：结构完整度为程序判定；版式专业度（断行、留白）含已知非阻断遗留，等待真人版式评审。

### 2.2 归因合理性（人工 0–5 分）/ Human Attribution Score — **PENDING**

- 评分入口：`POST /api/reports/{job_id}/reviews`（reviewer/attribution_score 0–5 + 三维度评语），
  支持批量导入 `POST /api/reviews/import`。
- 纪律：真人署名填写；AI 与演示流程不代填、不冒签。产物哈希变化会使旧评分自动过期。

### 2.3 RPA 触发成功率 / RPA Trigger Success — **7/7 PASS（SIMULATED_SENT）**

- 每场景从模型建议生成结构化任务（标题/责任人/来源/优先级/期限），确认后经 HTTP 严格协议
  送本机模拟 RPA；回执含 task_id 与通知双证。送达=模拟闭环，不等于真实微信或整改完成。

### 2.4 三步法输出格式正确率 / Three-Step Format Correctness

- 原题三场景（S1/S2/S3）：差异总览表（产品×要素×差异额×差异率）、结构拆解、归因文本字段
  校验 **3/3 PASS**（docs/validation/release_20260918_6ff894f/three_step.json，跨运行引用；
  本轮同字段结构校验通过）。
- 本轮七场景的差异/结构/解释字段全部生成且通过合同校验；差异计算与独立 golden 回归一致（≤1%）。

## 3. 自动维度回执 / Automatic Receipts（本运行）

| 维度 | 结果 | 回执 |
|---|---|---|
| 场景整体状态 | 7/7 DEGRADED——自动维度全部通过，DEGRADED 是"真人评审未完成"的既定终态（见下） | manifest.json |
| 模型解释合同 | **7/7 PASS**（含 Q2；glm-5.3-flash 经端点回退实调），身份 VERIFIED，usage 记账，账本 endpoint 列区分余额/回退端点 | model_live.json |
| 检索 | 7/7 PASS，hybrid（BM25+向量+RRF），原题场景 8 条证据/场景，图谱扩展生效 | retrieval.json |
| RPA 送达 | 7/7 SIMULATED_SENT | rpa.json |
| 文件 | DOCX/PDF 7/7 PASS | manifest.json |
| 回归测试 | 222 passed + 1 skipped（Windows 原生，含28项加分项+5项端点回退测试） | verify 输出 |

预算经济性：narrative 与 decision 路由分开记账；本轮为缓存复用运行（新鲜生成见
`bonus_20260918_glm_v18b`，每场景 1–3 次调用）。

## 4. 加分项验证 / Bonus Features Evidence

| 加分项 | 验证 |
|---|---|
| 知识图谱 | 真实题包抽取 3 产品/11 药材/7 工序/27 边；检索词增强后原题场景证据 8 条稳定；`/api/kb/graph` |
| 多模型协作 | narrative=glm-5.3-flash 与 decision=glm-4.5-air 双模型实测；`/api/model/routes` 回执 dedicated 标记 |
| 自主决策 | 无报告/数据变化→REPORT_NEEDED，同快照→DASHBOARD_ONLY；小模型说明 PASS；台账可审计 |
| 成本预测 | 七场景快照预测 PASS（Holt+80% 区间）；前端趋势叠加虚线与区间带 |

## 5. 复现 / Reproduce

```bash
# 按根 README“启用比赛数据”导出三个变量后：
bash 05_原型/scripts/bootstrap.sh && bash 05_原型/scripts/start.sh
05_原型/.venv/Scripts/python.exe 05_原型/scripts/run_acceptance.py \
  --run-id YOUR_RUN --output-dir 06_评测/YOUR_RUN \
  --private-scenarios competition_configuration/scenarios.json
bash 05_原型/scripts/verify.sh --manifest 06_评测/YOUR_RUN/manifest.json
```

verify 退出 0=自动维度通过；1=失败；2=未完成。本运行退出 0（七维度全 PASS）。失败历史与缓存复用分别记录，不互相冒充。

**关于 DEGRADED 状态**：报告任务在文件/模型/检索/RPA 全部通过且人工评审未完成时的终态为
DEGRADED（`human_review=PENDING` 是其构成部分）；混合生成轮中模型被拒的无效条目也按纪律
保留在失败痕迹里（见 retrieval_contracts.md）。这不表示自动维度失败。
