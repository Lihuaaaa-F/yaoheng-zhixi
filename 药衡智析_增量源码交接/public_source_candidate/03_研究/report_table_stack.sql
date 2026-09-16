WITH stack_decisions(层级, 选择, 理由, 经济性, 排序) AS (
  VALUES
    ('前端','Vue 3 + TypeScript + Element Plus + ECharts','比赛周期内成熟、中文生态好、交互和图表实现快','开源；无需额外硬件',1),
    ('API','FastAPI 模块化单体','契约清晰、异步任务适配好、避免微服务运维成本','MIT；单进程即可演示',2),
    ('分析','Polars + DuckDB','列式计算快、嵌入式 SQL、便于复算与测试','MIT；零服务器依赖',3),
    ('状态','SQLite WAL','任务、配置、审计够用；支持幂等与恢复','内置部署',4),
    ('RAG','BM25 + BGE + RRF + 可选重排','兼顾术语精确匹配与语义召回；每条答案带页码','116切片本地检索，无需向量库',5),
    ('解析','Docling/PyPDF + PaddleOCR回退','结构化解析；只对低文本页OCR','按需运行，避免全库OCR',6),
    ('模型','OpenAI兼容适配器 + 主/备模型','DeepSeek、GLM、Kimi、GPT可切换；规则控制升级','缓存、预算上限、仅高价值调用强模型',7)
)
SELECT 层级,选择,理由,经济性 FROM stack_decisions ORDER BY 排序;

