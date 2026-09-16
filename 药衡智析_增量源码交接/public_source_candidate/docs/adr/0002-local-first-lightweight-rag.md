# ADR 0002：本地CPU混合RAG与不可变知识版本

状态：Accepted；原决定2026-08-26，按实现更新2026-09-15。

现有7份PDF共116页都有可提取文本，使用PyMuPDF逐页解析；Word按段落/表格，TXT按行段保留真实位置。无需Docling/OCR平台。切片初值500中文字、80字重叠；真实索引129片。SQLite FTS5入库与查询统一jieba分词，BM25升序；BGE量化ONNX CPU＋本地Chroma产生语义候选，RRF仅融合排名。

选择小型CPU embedding避免GPU训练栈和独立搜索服务。向量失败显示DEGRADED并可使用BM25；解析失败保留旧知识版本，不能把BM25回退标为完整RAG通过。通用GMP/设备/工艺文档不因产品过滤丢失。

检索使用LlamaIndex Core的最小适配，详见ADR 0003。没有建设关系图、知识图谱、Qdrant或GraphRAG。当前实测混合全量Recall@5为0.8571、保留集0.7500；融合存在收益和损失，不预设优于BM25。

许可证限制和转换权重来源独立记录在 `docs/third_party_reuse.md`，不把PyMuPDF或整个依赖集合标为MIT。


## 2026-09-16增量验证
索引v4：154片，产品标题跨页继承，维修分事件期，纯标题/文控不入索引。最终固定历史已见集混合Recall@5=.928571，BM25=1.0；结果见本轮retrieval/v4_final。不是未见泛化评估，未调融合参数迎合保留集。
