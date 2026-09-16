# 本次检索与解释回归（2026-09-16）

## 真实证据

- `red.txt`：修改前 6 个针对用户症状的失败测试。默认 TMP 在 Windows 挂载目录的 pytest 捕获故障先记录，之后用 `-s` 真实得到六个业务红例。
- `green.txt`：相关单元/真实本地文档集成回归。使用 `/tmp` 的 basetemp 避免 Windows 挂载目录 SQLite 临时文件异常。
- `retrieval_results.json`、`retrieval_details.json`、`evaluation.log`：本次实际 CPU ONNX + SQLite BM25 + Chroma + LlamaIndex 检索，原历史结果未覆盖。
- `historical_failure_audit.json`：原 S2 model-response-30 原件 SHA 和失败根因；原件仍在本项目受控 runtime 中，未改写历史模型名称。

## 本次结论与范围

原 BM25 Recall@5=0.892857、混合=0.785714；开发集分别0.9/0.8、历史保留集0.875/0.75。BM25 方向原本正确（升序），融合按排名，问题主要在跨页继承、PDF读取顺序、产品过滤及语义候选稀释明确关键词。

先按真实 PDF 章界和坐标顺序修切片，维修历史按四个真实日期行隔离；空标签不再默认通用。明确文档、规格、参数问句使用预先固定BM25/向量权重0.75/0.25，其他问题0.5/0.5。随后只运行一次历史集评测，未按结果回调权重。

本次混合Recall@5=0.928571（开发集0.95，历史保留集0.875），BM25=1.0，向量=0.785714；引用页码和切片位置检查均1.0。混合仍低于BM25。历史保留集之前已有公开结果，本次是已见集回归，不能声称独立泛化提高。新增产品串扰、跨期维修、工厂/规格/文档版本、缺证与不实因果负例由实际测试执行。

合法数字被分为已注册成本指标、上下文日期/规格、定位文档参数。模型可用类型插槽，完全匹配注册上下文/已引用短原文的合法字面量也可通过；仅数字相等不算绑定。业务金额、比例仍由程序渲染，非法自由成本仍拒绝。S2原“1个百分点”本身也没有连续引用证明，且85%为他产品，因此不把该历史输出伪造为成功。

章节有限修复保留有效模型条目；无应用密钥时明确基础版。基础版从现有计算快照输出贡献排序、板蓝根2.90→3.05及83.33%、预算131940=84000+47940、跨厂结构和具有核查对象/预期证据/责任角色/期限依据的建议。未将文件成功当模型通过。

GLM默认实际ID为`glm-5.3-flash`，中国通用端点为`https://open.bigmodel.cn/api/paas/v4`，禁止coding端点。合同测试只使用HTTP夹具；本机无应用凭据、ZCode在队员电脑，真实文本/结构化/工具/流式/限流/超时兼容均待队员在受控环境验收。`model_live`不能从这些夹具推定。人工归因0–5分和可读性评分仍待人工。

## 复现

```bash
PYTHONPATH=05_原型/backend 05_原型/.venv/bin/pytest -s -q --basetemp=/tmp/pharma_retrieval_verify 05_原型/tests/test_knowledge.py 05_原型/tests/test_narrative.py 05_原型/tests/test_retrieval_incremental.py
PYTHONPATH=05_原型/backend 05_原型/.venv/bin/python 06_评测/run_retrieval.py --output-dir /tmp/pharma_retrieval_evaluation
```

新交接包必须先按启动脚本配置原始知识资料和本地模型缓存；此目录仅是测试证据，不是独立运行系统。

## 追加可移植性与真实加载建议复核

Knowledge默认尊重PHARMA_DATA_PACKAGE/PHARMA_RUNTIME_DIR；PHARMA_EMBEDDING_DIR可指向受许可的外置模型资产。显式测试root参数保留原相对目录隔离。两项路径回归真实红→绿。发现并修复基础建议中文优先级与API英文枚举冲突，priority统一high/medium/low，提示版本升为v7。

进一步排除只有章标题或文控信息的切片，章节元数据继续向后继承，最终索引版本为v4。31项回归通过（final_green.txt）。worker_query_scope.json记录原宽问句与按材料论点聚焦问句的实际结果；正确板蓝根工艺第3页在聚焦问句中被检出。未重调融合权重，未重跑历史开发/保留集；本目录0.928571等全量统计属于此前v3索引，不能未经实测当作v4精确统计。

最终追加：主Agent授权后，v4完整历史集只再运行一次，结果独立保存v4_final，覆盖最终154片索引。混合Recall@5仍为0.928571（开发0.95、历史保留0.875）；BM25为1.0，向量0.892857，位置检查1.0；真实负例11项通过。此授权后的实测补足上段所述v4精确统计缺口，旧v3结果继续保留。

S3末次补充：依据本期设备检索命中新增有界维修机制假设，正文不打印事件数值/表格，仅描述磨损、装量偏差与待核查证据；局部事件损失不等同月度净减产。产品和期间不适用时不生成。s3_event_red/green保存红绿，30项相关测试通过；v8提示版本使该变更不复用旧报告缓存。索引及融合排序未变。

最终交付四报告引用审计见report_citation_audit.json，输入scenario_reports_delivery.json；旧四报告审计完整保留report_citation_audit_before_delivery.json。实际重新打开原PDF、业务DOCX/PDF，核对短引、可读来源、页码、产品、期间、版本和任务字段。S3最终已引用本期维修第4页，局部损失未被写成净减产；S2实际引用同产品配方第2页，正确工艺第3页也在本次检索中。全部为PASS_WITH_LIMITS，仍不替代人工归因/可读性或视觉验收。可用audit_report_citations.py复现。
