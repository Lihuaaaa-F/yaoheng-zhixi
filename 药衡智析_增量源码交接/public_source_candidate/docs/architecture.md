# 系统架构 / System Architecture

> 本文档提供赛题技术方案要求的系统架构图、RAG 流程说明与关键链路图。
> This document provides the system architecture diagram, RAG pipeline and key
> flow diagrams required by the competition technical proposal.

## 1. 系统总体架构 / Overall Architecture

四层单体应用：React+ECharts 前端、FastAPI HTTP 层、确定性成本引擎与检索生成层、SQLite/DuckDB/Chroma 存储层。全部服务绑定 127.0.0.1，报告任务经持久队列由单 worker 串行处理，保证同输入可复现。

```mermaid
flowchart TB
    subgraph FE["前端 Frontend (React + ECharts)"]
        UI1["成本分析看板<br/>趋势/瀑布/结构/热力图/预测"]
        UI2["跨厂对标三步法"]
        UI3["报告与任务<br/>(RPA追踪)"]
        UI4["数据与证据<br/>+知识图谱"]
    end
    subgraph API["FastAPI (127.0.0.1:8765)"]
        R1["/api/analyses /api/benchmarks"]
        R2["/api/reports → JobStore 队列"]
        R3["/api/actions → Outbox"]
        R4["/api/forecast /api/agent/decision<br/>/api/kb/graph /api/model/routes"]
    end
    subgraph CORE["确定性成本引擎 + 检索生成"]
        M1["metrics/industry<br/>Decimal 环比/同比/预算/贡献度"]
        K1["knowledge<br/>FTS5(BM25)+Chroma 向量<br/>RRF 融合 + 适用性过滤"]
        G1["graph 知识图谱<br/>产品-药材-工序"]
        N1["narrative 有界生成<br/>任务合同+校验器"]
        F1["forecasting Holt 预测"]
        D1["decision 决策引擎"]
    end
    subgraph STORE["存储 Storage"]
        S1[("SQLite<br/>任务/审核/模型账本")]
        S2[("DuckDB/Parquet<br/>成本快照")]
        S3[("Chroma<br/>证据向量")]
    end
    subgraph EXT["外部端点 External"]
        LLM["大模型 API<br/>(OpenAI 兼容)"]
        RPA["模拟 RPA 服务<br/>127.0.0.1:8090"]
        LO["LibreOffice<br/>DOCX→PDF"]
    end
    FE --> API --> CORE --> STORE
    N1 -->|"多模型路由<br/>narrative/decision"| LLM
    R3 -->|"HTTP 严格协议"| RPA
    R2 --> LO
    K1 -.-> G1
```

**要点 / Key points**
- 前端只消费 API 与静态产物；任何数字都由后端确定性计算，前端不做业务运算。
- 报告生成经 JobStore 入队（缓存键=全链路版本指纹），worker 串行处理并在安全检查点恢复。
- 模型网关按任务路由（见 §4），账本按 operation 分开记录调用与预算。

## 2. RAG 检索增强流程 / RAG Pipeline

```mermaid
flowchart LR
    A["原始文档<br/>PDF/DOCX/TXT/JSON"] --> B["解析 section_blocks<br/>标题继承·维修事件行隔离<br/>文档编号/版本/生效日期元数据"]
    B --> C["清洗切分<br/>500字边界+80字重叠<br/>低质分片拒收"]
    C --> D1["FTS5 索引<br/>jieba+企业词表"]
    C --> D2["Chroma 向量<br/>bge-small-zh ONNX"]
    Q["分析查询"] --> E{"知识图谱扩展<br/>(制药上下文)"}
    G["graph<br/>产品→药材/工序"] --> E
    E -->|"BM25 词补充"| F["双路召回"]
    D1 --> F
    D2 --> F
    F --> G2["RRF 融合<br/>词法锚定 0.75/0.25<br/>否则 0.5/0.5"]
    G2 --> H["适用性过滤<br/>产品/工厂/期间/规格/版本"]
    H --> I["证据清单<br/>含来源与页码"]
    I --> J["narrative 有界生成<br/>引用必须原文逐字"]
```

**切分策略 / Chunking**：按段落/换行边界切 500 字、保留 80 字重叠；文档控制行（编号/版本/密级）与短标题行只作元数据不进入正文证据。
**向量化 / Embedding**：`Xenova/bge-small-zh-v1.5` 量化 ONNX，CPU 推理，SHA 指纹纳入知识版本。
**检索策略 / Retrieval**：BM25+向量双路，RRF 融合；含具体参数/文档名词的查询按词法锚定加权；行业包可配置 purpose 补充检索（如当期维修事件预留位）。知识图谱把所选产品的药材与工序名补充进 BM25 查询词（仅制药上下文，召回仍受全部适用性合同约束）。
**来源定位 / Provenance**：每条证据携带文件名、页码/段落位置、文档版本与适用范围；引用进入正文前必须逐字匹配。

## 3. 报告生成链路 / Report Pipeline

```mermaid
flowchart TB
    A["POST /api/reports<br/>(主题/月份/产品/口径)"] --> B["固化分析快照<br/>snapshot_id"]
    B --> C{"版本指纹<br/>检索/模板/Prompt/模型…"}
    C -->|"命中"| Z["复用缓存产物"]
    C -->|"未命中"| D["检索证据"]
    D --> E["模型生成解释<br/>(任务合同约束)"]
    E --> F{"校验器<br/>自由数字/引用/覆盖"}
    F -->|"失败"| E2["有界修复重试<br/>≤2轮"]
    E2 --> F
    F -->|"通过"| G["规则事实编译<br/>数值/告警绑定"]
    G --> H["渲染 DOCX<br/>动态模板+图表"]
    H --> I["LibreOffice → PDF"]
    I --> J["验收 assess_report<br/>结构/插槽/行动合同"]
```

## 4. 多模型协作路由 / Multi-Model Routing

```mermaid
flowchart LR
    subgraph Routes["ModelGateway.for_route"]
        N["narrative 路由<br/>报告解释(大模型)"]
        DC["decision 路由<br/>决策说明(轻量模型)"]
    end
    CFG["PHARMA_MODEL_ROUTES JSON<br/>或 PHARMA_MODEL_<ROUTE>_* 变量<br/>未配置回退主模型"] --> Routes
    N --> L1["glm-5.3-flash"]
    DC --> L2["glm-4.5-air 等"]
    Routes --> LEDGER[("调用账本 SQLite<br/>按 operation 分开<br/>预算/身份核验/缓存")]
```

每次调用记录请求与响应 model 并核验身份（VERIFIED/MISMATCH）；narrative 与 decision 各自独立预算，轻量任务用轻模型降低成本。未配置第二模型时同源回退并在回执中如实标注 `dedicated=false`。

## 5. RPA 整改闭环 / RPA Loop

```mermaid
flowchart LR
    A["模型建议<br/>(可执行行动合同)"] --> B["人工编辑/确认<br/>payload_hash 绑定"]
    B --> C["Outbox 待发队列"]
    C --> D["POST 模拟RPA<br/>严格协议校验"]
    D -->|"200+task_id+sent"| E["SENT"]
    D -->|"超时/异常"| F["CONFLICT/<br/>REMOTE_UNKNOWN<br/>不自动重发"]
    E --> G["责任人确认 acknowledge<br/>(真人署名)"]
```

## 6. 部署视图 / Deployment

- 一键启动：`bash 05_原型/scripts/bootstrap.sh && bash 05_原型/scripts/start.sh`（Windows Git Bash / Linux / WSL 同一入口，解释器与平台差异由 `pharma_python.sh`、`manage.py` 分支处理）。
- 依赖锁定：`requirements.lock`（Windows 自动剔除 POSIX-only 项）+ 前端 `package-lock` 指纹重建。
- 无密钥/无嵌入模型均可降级启动：解释降级（rules 模式）、关键词检索兜底；回执如实标注，不冒充通过。
