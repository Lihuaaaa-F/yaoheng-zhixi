# RAG/知识库子系统审查纪要（agent_rag）

- 审查对象：worktree `D:/yaoheng-audit-wt-1f78b2f`（yaoheng-zhixi @ 1f78b2f），只读。
- 范围：`药衡智析_增量源码交接/public_source_candidate/05_原型/backend/pharma/` 下 `knowledge.py`（461行，全文读完）、`graph.py`（227行，全文读完）、`vector_switch.py`（156行，全文读完）。
- 方法：Trail of Bits audit-context-building + spec-to-code-compliance（手工移植版）。逐函数记录职责/前提/异常路径/调用关系；判定分级：满足 / 部分满足 / 不满足 / 未实现 / 待验证（+静态确认 or 待实测）；疑似缺陷先做反证；严重度 P0–P3/INFO。
- 对照知识源（只读核验）：题包 7 PDF（3配方 + 生产工艺_中药一厂 + 车间设备清单_中药一厂 + GMP全文 + GMP摘要）、`competition_configuration/knowledge_supplement/`（4 TXT）、`02_知识库/`（01_解析 7 md、03_索引 chunks.jsonl 116 行）、`05_原型/industry_packs/pharmaceutical/`。
- 说明：未执行任何构建/检索（会写 `.runtime`，违反只读约束）；运行时行为相关项标"待实测"。

---

## 1. 逐函数记录

### knowledge.py

| 函数/类 | 行 | 职责 | 前提（谁建立） | 异常路径 | 调用关系 |
|---|---|---|---|---|---|
| `_string_list` | 21 | 校验字符串列表（非空、≤200、去重） | 调用方传入 JSON 字段 | `ValueError('INVALID_TERMINOLOGY_'+label)` | `pharmaceutical_terminology` |
| `pharmaceutical_terminology` | 27 | 加载术语表：环境变量→仓库赛题原件→industry_packs 兜底；形状/大小(≤1MB)白名单校验 | 文件存在且为 .json（默认路径 `competition_configuration/pharmaceutical_terminology_original.json`，静态确认存在） | 各类 `INVALID_TERMINOLOGY_*` | `terminology_hash`/`tokenize`/`product_matches`/graph/`search` |
| `terminology_hash` | 50 | 术语内容 sha256，进版本指纹与漂移检测 | 同上 | 透传 | `_build`、`search`、`versions.hard_items` |
| `_term_tokenizer` | 54 | jieba Tokenizer + tokenizer_terms 加词，lru_cache(8) | jieba 可导入（requirements jieba==0.42.1） | Import 链由调用方兜 | `tokenize` |
| `source_snapshot` | 62 | source_dir 内 pdf/docx/txt 指纹 + 术语哈希 → 快照哈希 | 目录存在 | `iterdir` 异常上抛 | `resolve_context`(industry.py:351)、`context_services.retrieve` 校验 |
| `reciprocal_rank_fusion` | 68 | 加权 RRF（k=60），并列按 id 排序保证确定性 | rankings 为 id 列表 | nothing found | `search` |
| `tokenize` | 76 | jieba 切词 + 过滤（含 `\w` 或汉字）+ 小写 | 术语已加载 | 同上 | `_build`（索引侧）、`search`（查询侧） |
| `CpuEmbedding.__init__/encode` | 81 | bge ONNX 量化 CPU 推理，CLS+L2 归一化，查询加指令前缀，批16，截断512 | `model_dir` 含 model_quantized.onnx+tokenizer.json（`model_settings.embedding_dir()` 解析；vector_switch 探测保证） | 构造/编码异常由 `search`/`_build`/`_probe_local` 捕获 | `_model`、`vector_switch._probe_local` |
| `parse_document` | 108 | 按 suffix 分派：PDF=fitz 逐页(sort=True, 真实页号)；DOCX=段落+表格(' \| ' 连接, 继承标题, page=None)；JSON=list 记录(page 强制 None, 防 pack 假页码)；TXT=12行分块(utf-8-sig) | nothing found（.doc 旧格式不支持） | 上抛给 `_build` 记 failures | `section_blocks` |
| `section_blocks` | 143 | 制药 PDF 的作用域解析：元数据正则（版本/文档编号/生效日期/工厂=中药N厂）；"一、二、"标题继承并声明产品 scope；维修历史行按 `20\d{2}-` 拆事件并抓 event_period（含两行换行日期回退） | industry_id∈(None,'pharmaceutical')（否则透传 parse_document） | 无（纯生成器） | `_build` |
| `Knowledge.__init__` | 190 | 定位根/命名空间：context 与 source_files 进 namespace 哈希→`runtime/knowledge/<ns>`；source_files 白名单校验（后缀/重名/非空）；`extra_dir`(补充知识)/`ingest_dir`(用户上传 .txt) **仅当 `not self.context and source_files is None and source_dir is None`** 时启用 | RUNTIME/PACKAGE 可写 | `SOURCE_FILES_MUST_BE_SEQUENCE` 等显式失败 | 所有调用方 |
| `version/status` | 233 | CURRENT 文件指向版本目录；读 manifest | nothing found | 缺失返回 NOT_BUILT | 全链 |
| `_model` | 244 | 惰性单例嵌入器 | 模型资产在位 | 首次失败在 search/build 的 try 内 | `search`/`_build` |
| `build/_build` | 249 | 排它锁→源收集（题包目录 + 条件性 extra/ingest）→指纹+embedding_sha+PARSER_VERSION+context+术语 → 版本哈希；幂等（PASS 或 关向量且无 failures 直接切 CURRENT）；逐块过滤（封面/文档控制行跳过、<15有效字符=LOW_TEXT_QUALITY; OCR_NOT_RUN）；500字切块+80字重叠；FTS5(tmp+os.replace 原子)；chroma upsert 批32；manifest 记 PASS/DEGRADED+failures+vector_error；**仅 `not failures` 才切 CURRENT** | 锁目录可写 | 源级异常→failures；术语构建中变更→ValueError | worker、search 自愈、graph.load、vector_switch |
| `product_matches` | 365 | 产品适用：声明产品严格匹配；scope=general 放行；非制药行业不给回退；文本唯一提及回退 | chunk 已带 products/scope | 无 | `evidence_applicability` |
| `evidence_applicability` | 375 | 通用适用性合同：上下文五键匹配、产品、工厂/规格/文档版本（不匹配才排除，缺文档值→limits 背景）、event_period 区间、生效日期不晚于期间末 | chunk 元数据来自 section_blocks | 无（返回 reasons/limits） | search、narrative.generate（二次执行）、context_services._matching_event |
| `search` | 397 | 主检索：context 一致性守卫；术语漂移/缺 CURRENT 自愈重建（失败→FAILED 返回或 TERMINOLOGY_REBUILD_FAILED）；全量 chunks 载入内存→适用性过滤→eligible（event_only 再限事件块）；BM25=FTS5 引号转义 OR 查询池 max(20,limit)；向量=chroma `where evidence_id $in eligible`；RRF 融合（lexical_anchor 正则→[0.75,0.25] 否则 [0.5,0.5]，披露 fusion_weights）；可选 reranker（越界即拒）；llama-index BaseRetriever 适配输出；返回 status/knowledge_version/mode/evidence(含 source/location/page/score/applicability)/reason/retriever_version/embedding_version 等 | CURRENT 存在或可建 | 向量异常→error→DEGRADED（mode=vector 且错→ids=[]）；无快照→FAILED | context_services.retrieve、api /api/kb/search、vector_switch 验证 |

### graph.py

| 函数/类 | 行 | 职责 | 前提 | 异常路径 | 调用关系 |
|---|---|---|---|---|---|
| `normalize_entity` | 23 | 康熙部首归一（⻩→黄等8字），实体/产品互匹配 | nothing found | 无 | 全文件 |
| `_RECIPE_ROW` | 29 | 处方行：序号+2-16字名+剂量+**剂量后须还有列内容**（v18b 口径注释） | 配方表有"序号 药材 数量"文本形态（题包 PDF 满足，02_知识库/01_解析 佐证） | 不匹配即跳过 | `_build` 第一遍 |
| `_ARROW_SPLIT/_STEP_INLINE` | 31 | 箭头链切分 + 段首 2-14 字工序名 | 工艺路线含 ─→ 等箭头 | 同上 | `_build` 第二遍 |
| `_is_material` | 35 | 药材名判定：2-8 汉字，排除合计等 | 同上 | 无 | 同上 |
| `_clean_step` | 40 | 工序名清洗，句子/流向词不建节点 | 同上 | 无 | 同上 |
| `KnowledgeGraph.__init__` | 55 | 图目录=knowledge.path/graph | knowledge.path 已建 | 无 | api /api/kb/graph、context_services |
| `version_key/load` | 62-88 | 图版本=知识版本+规则版本哈希；未建图先触发知识构建（异常→DEGRADED 图）；临时文件+uuid 防并发，replace 原子 | chunks.json 存在 | 知识 FAILED→NOT_BUILT 图 | load/expansion_terms |
| `_build` | 96 | 两遍扫描 chunks：配方源→成分边(dose,unit='kg'硬编码,source,location)；工艺源→工序边(order)+相邻工序顺序边；节点全局去重；stats+PASS/EMPTY | chunk.products 或源文件名含产品名（product_of 回退） | 无（缺结构→EMPTY 诚实） | load |
| `expansion_terms` | 185 | 取该产品药材（按剂量降序）+工序（按 order）→去查询已有词→≤6 个 BM25 补充词；O(V·E) 标签查找 | 图 PASS | 图非 PASS→原状态返回 | **context_services.retrieve（真实检索增强入口）** |
| `graph_for_context` | 219 | 按上下文定位 Knowledge（空/无行业→裸构造） | nothing found | 无 | api.py:519 |

### vector_switch.py

| 函数/类 | 行 | 职责 | 前提 | 异常路径 | 调用关系 |
|---|---|---|---|---|---|
| `SwitchFailure` | 24 | 步骤化失败（step+reason） | 无 | 无 | 全文件 |
| `_probe_local` | 31 | 本地校验：目录、ONNX 资产（3种布局）、tokenizer.json、config 解析容错；**真实加载模型编码 2 条样本**取维度与有限性；产出指纹 | CpuEmbedding 可用 | 缺资产/编码失败→SwitchFailure('本地校验') | run_vector_switch |
| `_model_adaptation` | 68 | 数据分析模型 API 评估适配，JSON 结论校验；不可适配即失败（程序不硬切） | gateway.key 已配置 | 未配置/调用失败/不可适配→SwitchFailure('数据分析模型API') | 同上 |
| `run_vector_switch` | 97 | 流水线：本地校验→API评估→(env PHARMA_EMBEDDING_DIR 存在则拒写)→set_vector_model→Knowledge() 重建（进度映射45-90%）→FAILED 即失败→vector 检索验证→成功/DEGRADED 落账 | 各步前置 | SwitchFailure→**回滚 model_settings**；其他异常→FAILED+回溯 | jobs（VECTOR_SWITCH 任务） |

---

## 2. 检索管线图（静态）

```
交互式 KB 检索（api.py /api/kb/search, competition 分支）
  └─ Knowledge()（裸构造，namespace=None → runtime/knowledge/）
       sources = 7 PDF + knowledge_supplement 4 TXT + imports/knowledge/*.txt（用户上传）
       └─ search(**SearchRequest: query,product,mode,month→period,factory,specification,document_version)

报告生成 / 跨厂对标（worker.py:58 / api.py:144）
  ├─ Knowledge().build()          ← 裸根预构建（结果丢弃；对 competition 实际检索无用）
  └─ context_services.retrieve(snapshot, query)
       ├─ competition → Knowledge(context=ctx)（namespace=hash(ctx) → runtime/knowledge/<ns>）
       │    sources = 仅 7 PDF（extra_dir/ingest_dir=None）★F1
       ├─ 其他行业包 → Knowledge(context, source_files=(pack knowledge.json,))  allowlist
       ├─ 图谱扩展（graph_enabled 且 industry=pharmaceutical）
       │    KnowledgeGraph(knowledge).expansion_terms(product,query)
       │    → effective = query + 图谱药材/工序词（≤6，仅进 BM25 keyword_query；向量用原 query）★6.2真实接入
       ├─ search(query, product/factory/period/specification/mode/limit, keyword_query=effective)  ★无 document_version
       │    eligible = 适用性过滤(产品/工厂/规格/版本/期间/上下文) [+ event_only 事件块]
       │    BM25: FTS5 引号转义 OR, 池 max(20,limit)
       │    Vector: chroma where evidence_id ∈ eligible（向量禁用→VECTOR_DISABLED；异常→error）
       │    RRF k=60, weights=[0.75,0.25] if lexical_anchor(含\d) else [0.5,0.5]
       │    → llama-index BaseRetriever 适配 → evidence(+source/location/page/applicability/score)
       └─ purpose retrieval（pack retrieval.json 策略）：事件已在证据→ALREADY_COVERED；否则补充一次
            event_only 检索，匹配事件顶替保留（reserved_slots=1）；知识版本中途变更即抛

图谱可视化（api.py /api/kb/graph）→ graph_for_context(context).load()
  竞赛上下文 → Knowledge(context)（namespaced，7 PDF）→ 产品-药材(剂量)-工序(顺序)图
```

## 3. 过滤参数传递链（spec 5.1.2/6.1 要求的产品/工厂/期间/规格/版本）

| 过滤维度 | 交互式 API（/api/kb/search, competition） | 报告链（retrieve→search） | chunk 侧数据源 | 实效 |
|---|---|---|---|---|
| product | 传（api.py:39→435） | 传（scope, context_services.py:79） | section_blocks 标题声明/文件名/唯一提及回退 | 生效（严格+回退） |
| factory | 传 | 传 | `中药[一二三]厂` 正则（仅题包两份带厂名 PDF 会命中） | 部分（多数 chunk 无 factory→仅 limits） |
| period(month) | month→{start,end}（api.py:435 前一行） | 传 snapshot.period | event_period（维修事件行）+effective_date | 生效（事件外推+生效日校验） |
| specification | 传 | 传 | **无任何解析器写入（grep 0 命中）** | 空转（永不排除，只产 limits） |
| document_version | 传 | **不传（scope 无此键）** | 元数据正则（版本:…） | API 链生效；报告链缺位；narrative 兜底同编号多版本冲突排除（narrative.py:940-944） |
| analysis_context（5键） | — | 构造时绑定 + search 守卫 MISMATCH | chunk.analysis_context | 生效 |

---

## 4. 发现（按严重度）

### F1 [P2] 竞赛上下文的报告/对标检索库不含补充知识与用户上传知识（双知识库分裂）
- 位置：`knowledge.py:214`（`if not self.context and self.source_files is None and source_dir is None:` 才设 extra_dir/ingest_dir）、`context_services.py:69-70`（competition → `Knowledge(context=context)`，namespaced 根仅收录 7 PDF）、`worker.py:58-60`（先裸根 build 再 retrieve 用 namespaced 根，裸根构建对该报告无效）。
- 后果：`knowledge_supplement/` 4 份文档（药材行情/行业基准/历史异常处理/对标基线）与数据中心"知识库数据"用户上传，只进入交互式 `/api/kb/search`（competition 分支走裸 `Knowledge()`）与 worker 的预构建；报告生成与跨厂对标解释（api.py:144）的证据库=仅 7 份 PDF。修复 #7（提交 e9669b6）宣称"补齐赛题5.1.2三类知识…入库"，实际未到达报告链路。
- 反证（为何不是 P0/P1）：①三类知识在报告链仍各有 PDF 路径（产品=配方/工艺 PDF、行业=GMP 全文+摘要、企业内部=车间设备清单含维修历史）；②行情/基准**数字**经确定性 CSV 链路（ingestion._kind→market/industry 行；metrics.py:199、attribution.py:93-97 直接查表带 source_hash）仍进报告；③test_knowledge_supplement.py 仅断言裸构造——测试与代码一致但与提交意图/双入口一致性相悖。残留影响：对标基线、异常处理记录 prose 及用户上传知识不出现在报告证据与溯源中。
- 判定：三类知识接入=部分满足；待实测项：无（静态可判）。

### F2 [P3] `embedding_version` 恒报硬编码常量，模型切换后溯源失真
- 位置：`knowledge.py:18,460`（search 返回 `embedding_version: EMBEDDING_SHA` 常量）、`versions.py:34`（报告硬合同 `('embedding', EMBEDDING_SHA)`）。真实指纹在 manifest.embedding.sha（model_settings.embedding_fingerprint），未透出。
- 反证：generation cache key 含 knowledge_version（其哈希含 embedding_sha）→ 不会读到陈旧缓存的报告；故仅溯源标注失真，不影响正确性 → P3。
- 判定：版本切换可追溯性=部分满足。

### F3 [P2] DEGRADED 构建永不切 CURRENT → 知识静默过期，且链路无告警
- 位置：`knowledge.py:360-362`（`if not failures:` 才切 CURRENT）、`search:402-404`（仅在术语漂移或 CURRENT 缺失时重建；**源文件增删改不触发**）、`worker.py:59`（`Knowledge().build()` 返回值丢弃）。
- 场景：任一源出现一个 LOW_TEXT_QUALITY 块（如扫描页/印章页）→ 新版本 DEGRADED → CURRENT 停留旧版本；报告继续用旧知识且证据包无"知识未更新"提示（仅 knowledge_version 可供事后比对发现）。worker.py:57-58 注释宣称"补充知识目录增删改后报告链路自动纳入新版本"——仅在构建零失败时成立，注释过强。
- 反证：注释明示故意设计（"Parsing failure must not replace the last valid knowledge snapshot"——防坏快照替换好快照，安全取向合理）；术语漂移路径会显式 `TERMINOLOGY_REBUILD_FAILED` 抛错（诚实）。缺口仅在"源变化+部分失败"组合下的静默性 → P2。
- 判定：解析失败降级=满足（failures 明细保留、不覆盖好快照）；增量更新时效=部分满足；待实测：真实 7 PDF 是否零 failures 构建（静态看封面/文档控制行已被 300-305 行跳过，倾向零失败）。

### F4 [P3] 报告链不传 document_version；specification 过滤空转
- 位置：`context_services.py:79-80`（scope 五键无 document_version）；`knowledge.py` 全文件无写入 `specification` 键（搜索词 `specification` 仅命中过滤与签名处）。
- 反证：API 链完整传递（api.py:40,435）；narrative.generate 对同文档编号多版本做冲突排除（940-944）补上了版本安全；specification 在证据中始终落 "limits=未在文档中明确" 属诚实标注而非隐瞒 → P3。
- 判定：过滤传递=部分满足。

### F5 [P3] 向量切换失败回滚后，CURRENT 指向新模型索引的窗口期错配
- 位置：`vector_switch.py:116-150`——`set_vector_model(new)` 后 build PASS 已切 CURRENT；若随后"检索验证"（128-130）失败触发回滚，恢复旧模型目录，但 CURRENT 仍指向按新模型指纹构建的索引。旧模型编码查询新模型 chroma：维度不同→异常→DEGRADED（诚实）；维度相同→语义空间错位（静默低质召回）。
- 反证：下一次任何 `build()`（worker 每报告必调，worker.py:59）按当前（旧）模型指纹命中既有旧版本 manifest 并把 CURRENT 切回（knowledge.py:277-283 幂等分支）→ 自愈；仅窗口期受影响 → P3。
- 判定：版本切换失败处理=部分满足（回滚本体、env 优先级拒写、维度探测均满足）。

### F6 [P3] 图谱两处口径瑕疵：跨产品工序顺序边污染；剂量单位硬编码 'kg'
- 位置：`graph.py:169-172`（`process:<step>` 节点全局共享，两产品同名工序会产生互串的"工序顺序"边——可视化/结构口径失真）；`graph.py:148`（`unit='kg'` 不从表头解析）。
- 反证：检索增强只消费 `成分`/`工序` 边（expansion_terms 185-216），污染边不影响召回；题包配方 2.1 处方量表头确为 "(kg)"（02_知识库/01_解析/产品配方文档_*.md 静态确认），2.2 单袋折算(g)行无序号列不会被 `_RECIPE_ROW` 命中 → 当前数据集无实际错标，风险在换数据集 → P3。
- 判定：图谱构建=满足（含 v18b 口径注释、部首归一、溯源属性）；数据集泛化=部分。

### 通过项（INFO，含反证要点）
1. **向量不可用诚实降级**：hybrid 降级返回 BM25 结果但 `status=DEGRADED`+`reason=异常类名`+`retrieval_status=DEGRADED` 并透传 narrative 缓存键（narrative.py:958）；`mode='vector'` 且失败→`ids=[]`；`vector_enabled=False`→`VECTOR_DISABLED`。不以纯关键词冒充混合 ✔（knowledge.py:425-446）。
2. **维度探测**：`_probe_local` 真实加载模型编码 2 条样本取维度+有限性（vector_switch.py:52-61）；另有 `model_settings._probe_dimension_cached`（ONNX 输出形状惰性探测）✔。
3. **索引中断恢复**：exclusive 文件锁（locks.py，msvcrt/fcntl 双平台）、tmp+`os.replace` 原子写、CURRENT.tmp 原子切换、同版本幂等重入、chroma 按 id upsert 幂等、FTS tmp 先删后建 ✔。
4. **结构化行情/基准确定性优先**：CSV→market/industry 行入库（ingestion.py:96-99），metrics.py:199 / attribution.py:93-97 按药材名+月份直接查表并带 source_hash；补充 TXT 明示"不改写数值""市场参考价非采购价"仅作 RAG prose 侧写 ✔（满足赛题"确定性查询优先"要求）。
5. **图谱增强 RAG 真实且边界诚实**（赛题 6.2）：`context_services.py:85-94` 把图谱药材/工序词补进 BM25 keyword_query（向量与适用性合同不变），结果标注 `experimental/scope=bm25_only/gain_status=NOT_ESTABLISHED`；/api/kb/graph 提供结构可视化——非"只画图"；图谱不用于证明本期成本变动（归因走 attribution 程序计算，图谱仅扩召回）——证据边界正确 ✔。
6. **PDF/Word/TXT 真实解析**：pymupdf 1.28.2 逐页 `get_text(sort=True)` 带真实页号；python-docx 段落+表格（' | ' 行连接、标题继承、page=None 不造页）；TXT utf-8-sig 12 行块；JSON 记录 page 强制 None 防 pack 假页码（knowledge.py:136）✔。局限：.doc 旧格式不支持（INFO）；PDF 表格退化为坐标排序文本、结构靠正则（部分满足）。
7. **OCR 按需**：未实现（搜索词 `ocr|tesseract|paddle` 仅命中 `OCR_NOT_RUN` 标注与 data_import 的显式拒绝 `扫描件需先OCR，系统不自动宣称成功`）；题包 7 PDF 均为文本层（02_知识库/03_索引 corpus_build_summary: ocr_queue_documents=0）→ 本数据集不阻塞；未实现但诚实标注 ✔。
8. **重复内容**：evidence_id 绑定源哈希+位置+标题+期间+索引+文本（同源同位置稳定）；GMP 全文与摘要并存为双源（合理）；api.py:155-158 对 (source,location) 去重。跨源近重复不去重=部分满足。
9. **文档元数据与版本适用范围**：编号/版本/生效日期正则抽取进 chunk 并参与过滤；生效日晚于期间末→"文档尚未生效"排除；同编号多版本→narrative 冲突排除；缺值→"仅作背景"limits（诚实）✔。
10. **BM25 注入风险反证**：token 经 jieba+`[\w\u4e00-\u9fff]` 过滤后 `"x.replace('"','""')"` 双引号转义进 FTS5 引号串（串内字符字面化），无语法注入路径；最坏为多 token 短语化导致漏召回（保守方向）。
11. **RRF/权重披露**：k=60 标准式；lexical_anchor 含 `\d|[A-Z]{2,}` → 绝大多数成本查询走 [0.75,0.25]；代码注释声明"fixed weights are not fit on gold"并在结果中披露 fusion_weights ✔。
12. **期间过滤实现**：event_period 'YYYY-MM' 与 period.start/end 同格式字符串比较（零填充月份下正确）；api month→{start=month,end=month} ✔。

---

## 5. 判定统计（对照赛题 5.1.2 / 6.1 / 6.2 条目）

| # | 核查项 | 判定 |
|---|---|---|
| 1 | 三类知识接入路径（产品/行业/企业内部） | 部分（报告链 7 PDF 三类齐备但补充+上传未入；交互链齐备）—F1 |
| 2 | PDF/Word/TXT 真实解析 | 满足（.doc 旧格式不支持 INFO） |
| 3 | 扫描件 OCR 按需 | 未实现（诚实标注；本数据集 0 扫描件）|
| 4 | 表格处理 | 部分（DOCX 表格管道化；PDF 表格为排序文本+正则） |
| 5 | 解析失败降级 | 满足（failures 明细、不覆盖好快照）；静默过期见 F3 |
| 6 | 重复内容处理 | 部分 |
| 7 | 文档元数据 | 满足 |
| 8 | 版本与适用范围 | 满足（API 链）/部分（报告链 F4） |
| 9 | 语义+BM25 混合、融合与权重 | 满足（加权 RRF，权重披露，未拟合金标注明） |
| 10 | 来源+页码标注 | 满足（PDF 第N页真实；DOCX/TXT 不造页） |
| 11 | Top-K | 满足（默认5/8，池20后融合截断） |
| 12 | 产品/工厂/期间/版本过滤传递 | 部分（specification 空转、报告链缺 document_version —F4） |
| 13 | 向量不可用诚实降级 | 满足 |
| 14 | 向量维度探测 | 满足 |
| 15 | 索引构建中断恢复 | 满足 |
| 16 | 版本切换失败处理 | 部分（回滚自愈窗口 F5） |
| 17 | 结构化行情/基准确定性优先 | 满足 |
| 18 | 知识图谱增强 RAG（6.2，非只画图） | 满足（真实 BM25 扩展+诚实标注；图谱不冒充成本归因证据）；口径瑕疵 F6 |

统计：满足 12 / 部分 5 / 未实现 1（OCR，诚实标注）/ 不满足 0。P0=0，P1=0，P2=2（F1、F3），P3=4（F2、F4、F5、F6），INFO 若干。

## 6. 未覆盖残留
- 未运行任何构建/检索/测试（只读约束）：DEGRADED-vs-PASS 的真实构建结果、RRF 权重实测召回质量、chroma 1.5.9 大列表 `where $in` 性能、jieba 对题包 PDF 实文的分词覆盖、图谱对真实 chunks 的节点/边数量——均待实测。
- 前端展示（页码/来源标注的 UI 呈现）与 narrative 下游消费质量不在本子任务范围。
- `02_知识库/`（01_解析/02_清洗/03_索引）为仓库预加工产物，与运行时 knowledge.py 索引是两套体系；本审查以运行时链路为准，仅用前者佐证 PDF 文本形态。
