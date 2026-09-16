# 检索与受约束生成

## 实施接口与证据边界

`Knowledge.build()`：PyMuPDF逐页解析PDF；python-docx按段落/表格解析DOCX；TXT按真实行段。保存原文、清洗文本、来源SHA256、页码/位置和知识版本。正文上限500字（匹配BGE最大512 tokens，避免正文被大幅截断），优先换行/句号分割、80字重叠；短页保持原页。只有低质量页报告OCR未执行，不对正常页引入OCR。解析失败保留旧CURRENT。分版SQLite FTS和Chroma完成后原子发布。

`Knowledge.search(query, product=None, mode='hybrid', limit=5)`：同一jieba词典入库和查询；SQLite bm25按ASC；各路前20候选以k=60排名RRF融合。通用工艺/设备/GMP不被产品过滤。LlamaIndex Core的BaseRetriever真正执行已融合排名，返回TextNode和NodeWithScore；不会创建隐式OpenAI模型。可传可关闭的reranker；重排故障保留融合，向量故障返回DEGRADED。BM25单路通过不代表混合RAG通过。

CPU embedding：Xenova/bge-small-zh-v1.5，固定HF SHA `75c43b069aac4d136ba6bc1122f995fedcfd2781`，单个22.8MB量化ONNX + tokenizer；ONNX Runtime CPU，CLS向量L2归一化，查询加BGE中文检索提示。路径`05_原型/.runtime/models/bge-small-zh-v1.5`，manifest记录文件哈希。基础模型MIT，一手[基础模型卡](https://huggingface.co/BAAI/bge-small-zh-v1.5)及[转换模型卡](https://huggingface.co/Xenova/bge-small-zh-v1.5/tree/75c43b069aac4d136ba6bc1122f995fedcfd2781)。不安装torch/CUDA。

## 模型网关

`generate(snapshot, evidence)`返回`status/model/model_live/generation_mode/findings/usage/cost/cache_hit`。Finding含claim_type、metric_refs、evidence_refs、evidence_quotes、hypothesis、missing_evidence、suggestion及程序注入的rendered_text。

数值事实必须使用指标插槽，显示文本最终由权威快照注入；文档事实必须逐字摘录对应位置，避免仅凭有效ID判定支持。成本原因假设必须同时含指标、原文摘录、相同主题与缺证项，禁止确定因果语句。词面主题检查是保守工程约束，不等同完整语义证明；真人归因评分仍待进行。来源文档中的建议不是生产/GMP变更授权。

默认DeepSeek `deepseek-flash`（V4.1 Flash）；安全读取`PHARMA_API_KEY_FILE`或`PHARMA_API_KEY`，默认文件在用户指定api目录，不打印密钥。OpenAI兼容chat/completions与Anthropic messages可由`PHARMA_MODEL_PROTOCOL`、`PHARMA_MODEL_BASE_URL`、`PHARMA_MODEL`配置。实际模型列表与联调结果单独落盘，协议夹具成功不冒充其他供应商实际通过。

默认生成上限20次（持久化SQLite计数）、连接15秒/读取55秒；错误结构最多2次修复，网络超时停止本次生成并规则降级。单worker配合SQLite事务限制调用次数；不充值。每次调用记录模型、协议、耗时、usage、失败类别、提示版本；费用缺计价核对时`UNKNOWN`。缓存哈希含数据快照、知识/模型/提示/模板版本和协议端点，命中返回来源时间。

## 独立评测与TDD

`06_评测/retrieval_gold.jsonl`首跑前冻结28道来源页码问题，20开发/8保留集；另5道无答案、冲突、注入、错误别名负例。保留集不参与调参。`run_retrieval.py`比较BM25/向量/混合Recall@5与MRR，独立重开源PDF验证golden原文位置，目标0.85与实测分开。负例在生成接口验证，不以搜到相关文档认定能回答。

技能：已按共享原文读取TDD及codebase-design，用公开检索和生成接口做测试；真实最初缺模块失败和最小排序成功日志见`rag_tdd_red.log/green.log`；生成约束的首次失败见`narrative_tdd_red.log`。最终pytest与检索实测以运行产物为准。

## 本轮实际结果（2026-09-15）

- 真实索引PASS：7PDF、116页、129切片，零解析失败，ONNX/Chroma/LlamaIndex全链实际执行。
- 最终产品范围校验后28题全量Recall@5：BM25 0.8929、向量 0.7143、混合 0.7857；8题保留集混合0.7500，未达0.85自选目标。该修复由实际报告错误触发，未按保留集调参；通用GMP继续可检索。
- 28条golden位置和129个切片对原PDF位置独立复核100%。详见retrieval_results.json、retrieval_details.json；冷/热耗时另见retrieval_performance.json。
- 模块pytest 8项通过。默认pytest临时路径出错，固定TMPDIR=/tmp并关闭fd捕获后正常；没有修改测试期望或skip。
- DeepSeek官方/models实际列出deepseek-flash。首轮真实响应被支持检查拒绝，保留失败计数；修正提示为只输出指标事实与带原文主题的假设，并反馈具体校验原因，未放松验证。提示版本constrained-evidence-slots-v2的S3真实生成一次通过，输入4650/输出532 tokens，费用UNKNOWN。模型正文与证据记录在私有runtime/评测目录。
- Anthropic格式通过本地HTTP合同夹具，未使用其他供应商真实账号，因此仅标协议兼容已测，不能标其真实服务PASS。

### 集成审查修复

真实S3旧报告暴露单位重复（`元/盒元/盒`、`%%`）和事件局部减产可能被误读为本月净减产。按实际旧输出先增加失败回归，再修复：插槽渲染仅消费紧随插槽的同单位副本；净月产量上升时，减产假设必须明确“不等于本月净减产”，直接矛盾的月度陈述被拒绝。日志见`narrative_unit_tdd_red/green.log`及`narrative_event_tdd_red/green.log`。合并模块测试10项通过。

当前提示版本`constrained-evidence-slots-v3`，提供必要的季度/月度产量比较与`benchmark_context`，要求对标生成使用既有分母、结构差异和缺证项。此前v2模型probe是真实历史联调，不自动视为v3新产物验收；最新报告/对标以worker实际记录为准。该次修复没有增加额外模型probe调用。

### 实际v3误拒与v4合同修正

v3四场景响应的numeric_fact含合法数值槽，但附带有效文档引用，被实现中额外的“numeric事实不得含文档引用”条件误拒。此限制不来自业务合同。现允许通过逐字原文/位置校验的补充文档引用；numeric_fact要求非空合法metric_refs，直接以其作为结构化数值槽，显示文字完全由程序生成，继续拒绝自由数字和未知指标。失败/通过日志见`narrative_numeric_contract_red/green.log`。

同时实际raw10/raw17暴露“产量环比”插入绝对产量的语义错误，新检查拒绝比例标签与非百分比指标错配；`narrative_slot_semantics_red/green.log`保留真实模式回归。合并13项测试通过。v4提示提供最短可用JSON示例，假设仅引用metric_refs不写数字，文档引语优先单行连续短句。可通过`PHARMA_MODEL_MAX_REPAIRS=0`为最终每场景限制一次调用；默认上限仍为两次修复。

保存的真实模型响应已按原snapshot/evidence离线重验，S1 raw11、S2 raw14、S3 raw15、季度raw20均有合格输出；`model_revalidated.json`明确标REVALIDATED和new_live_call=false，不混成新实时联调、不自动写报告缓存。当前版本的新实时报告以主worker最后实测为准。


## 最终v5与产品范围门禁
最终冻结：FINAL_STATUS=PARTIAL。42项合并测试通过；S1/S3/Q2为真实DeepSeek生成通过，S2专题因未绑定文档数字触发严格拒绝而明确规则降级。四份DOCX/PDF均通过，原文与原数据哈希未变。跨产品设备误引已补校验，原错误S2已撤回，不能下载冒充通过。
完整JSON示例与allowed_quotes减少转写错误，数值仍由程序插槽渲染。设备别名按原设备文档关联产品，混合设备表中的胶囊计量盘不能作为板蓝根事件依据。两项新增回归及真实红绿日志见narrative_product_tdd_*。调用账保留30条（含早期连接失败），费用UNKNOWN。默认累计上限40，为用户本地演示保留最多10次；本轮不再调用。用户可通过PHARMA_MODEL_MAX_CALLS显式调整本地上限，该配置不代表充值或供应商余额。
