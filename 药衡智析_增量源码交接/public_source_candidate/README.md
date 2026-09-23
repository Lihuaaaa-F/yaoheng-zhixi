# 当前工作台

界面按“工作台 / 数据中心 / 模型与设置”组织。右侧助手可独立配置 API、本地模型、型号和生成参数，不继承报告模型的密钥。模型子型号与推理强度在输入框内切换；上下文只显示圆环，悬停或键盘聚焦展示估算、容量和预留输出。容量须按当前型号填写，未知时显示灰环。

启动方式仍为下方 `bootstrap.sh` / `start.sh`，或仓库根桌面启动器配合 Compose。更改源码后用启动器“更新构建”，普通启动复用现有镜像。API 文档可访问本机 `/docs`。

详细行为、API、测试与已知限制见 [工作台升级记录](docs/workspace_upgrade_20260923.md)。历史模型测试和报告不代表新工作台已经通过比赛整体验收。

---

历史执行记录（2026-09-19）：当前运行 `delivery_20260919_final`，应用受测修订 `04011c2`。本机用户明确选择 DeepSeek，七次真实调用通过；最终七份 Word/PDF 使用同输入的已验证叙事缓存，新增模型请求为零。数值、检索、模型、模拟 RPA、浏览器与文件关联自动检查通过；真人三场景0—5归因/可读性/版式仍 PENDING，不能据此宣称比赛验收或获奖水平。

当前交付位于 `07_交付/delivery_20260919_final/`（应用根相对路径）：59.16秒实际闭环视频、十页PPT及原生渲染、七份报告共38页、待评表。源码修复和边界见 Git根 `docs/repository/FIXES_20260919.md`。旧运行、旧GLM/DeepSeek和失败回执保持原始来源；下方较早记录为历史背景。

---

# 药衡智析 · 产品成本智能分析报告系统

**基于 RAG 与大模型的制药企业产品成本智能分析报告系统**（2026 年第二届重庆市 AI 大模型创新应用大赛 · 创灵境企业出题）。2026-09-22 三模块改版：系统专注制药赛题定制，界面收敛为 **数据中心（业务数据/知识库数据/报告模板）· 工作台（数据分析/跨厂对标/报告生成/问题整改）· 模型配置（数据提取模型/数据分析模型/向量模型）**；不再出现行业包选择与合成演示数据——数据不足时按“证据支持假设/证据不足”合同输出归因推测。行业包架构（`industry_packs/`、受信策略、企业注册合同）在代码层完整保留，供其他行业改装复用（见 `docs/industry/development.md`）。

> **English summary** — Yaoheng Zhixi is a RAG + LLM powered product-cost analysis and reporting system for a pharmaceutical contest scenario. A deterministic Decimal cost engine feeds an evidence-bound report pipeline (Word/PDF), an ECharts dashboard with attribution/waterfall/heatmap, a cross-factory three-step benchmark, and an RPA task loop against a local simulator. Bonus features implemented: knowledge-graph enhanced retrieval, multi-model routing, agent report-or-dashboard decision, and Holt-based cost forecasting. All numbers are program-owned; the model only picks references and wording under a strict validator contract.

> 2026-09-19审计：功能存在不等于赛题全部通过。当前热力图缺产品×月份交叉；告警解释在生成报告后覆盖，页面阈值自动触发仍需补齐；预测与证据合同另有缺陷。当前记录和历史展示材料来自不同批次，见[本次审计](../../docs/repository/AUDIT_20260919.md)。

## 功能总览 / Feature Map

| 赛题模块 | 实现 | 入口 |
|---|---|---|
| 模块一 智能报告生成 | Word 模板解析（占位符+书签锚点）、RAG 增强、PDF/Word 双导出 | `05_原型/backend/pharma/reports.py` |
| 模块二 看板与归因 | 趋势/瀑布/结构/要素热力图、贡献度、告警事实及报告解释 | `metrics.py`、`frontend/src/Analysis.tsx` |
| 模块三 对标三步法 | 找差异→拆结构→拆原因，差异表/结构树/归因文本 | `metrics.benchmark_analysis`、`industry.benchmark_reference` |
| 模块四 RPA 闭环 | 结构化任务 JSON、模拟 RPA/微信送达、任务追踪看板 | `actions.py`、`synthetic_rpa.py` |
| 加分 知识图谱 | 产品-药材-工序图，检索词增强+前端可视化 | `graph.py`、`/api/kb/graph` |
| 加分 多模型协作 | 按任务路由（报告=大模型，决策说明=轻量模型），独立记账 | `ModelGateway.for_route`、`/api/model/routes` |
| 加分 Agent 自主决策 | 确定性策略判断“生成报告/仅更新看板”+小模型说明+决策台账 | `decision.py`、`/api/agent/decision` |
| 加分 成本预测 | Holt 双参数指数平滑，80% 区间，看板趋势叠加 | `forecasting.py`、`/api/forecast` |

不包含真实 ERP 对接、真实微信发送与联副产品成本引擎；合成行业包仅验证框架迁移，不宣称行业适配完成。

## 快速开始 / Quick Start

本目录为应用根（`药衡智析_增量源码交接/public_source_candidate`），外层是 Git 根。已合并 clone 无需 prepare。

```bash
cd 药衡智析_增量源码交接/public_source_candidate   # 仓库根克隆后先进应用根
bash 05_原型/scripts/bootstrap.sh   # venv + 锁定依赖 + 前端按指纹构建 + 数据冒烟
bash 05_原型/scripts/start.sh       # 启动 api(8765)/worker/模拟RPA(8090)
# 打开 http://127.0.0.1:8765
bash 05_原型/scripts/stop.sh
```

**English**: same two scripts bootstrap and start the whole stack (FastAPI + worker + simulated RPA) on localhost; Windows Git Bash, Linux and WSL share one entry point. Model key is optional — narrative degrades to deterministic rules; embedding model optional — lexical retrieval remains.

环境要求：Python 3.12（venv）、Node/npm（Vite 锁版本接受 Node 18/20/≥22）；Word→PDF 需 LibreOffice，逐页截图需 `pdftoppm`。Windows：LibreOffice 默认安装即可被自动探测（亦可将 `program` 目录加入 PATH）；Poppler for Windows 解压后把 `bin` 加入 PATH。没有嵌入模型时关键词检索降级可用；不会自动下载大型模型或覆盖外置模型。

**Network / English**: on restricted networks set pip/npm mirrors first (`PIP_INDEX_URL`, `npm_config registry`); offline reviews should pre-build once online (node_modules are required even when `frontend/dist` matches). Common troubleshooting: port conflict → change `PHARMA_API_PORT`/`PHARMA_RPA_PORT` in `05_原型/.env`; no response on 8765 → check worker log under `05_原型/.runtime`; on Windows run scripts from Git Bash.

## 模型配置 / Model Configuration

配置文件 `05_原型/.env`（示例 `.env.example`，仅本机保存，不入库）。可选初始化：
`cp 05_原型/.env.example 05_原型/.env`（无密钥、无 .env 也可基础启动）：

```bash
PHARMA_MODEL=glm-5.3                        # 数据分析模型（大模型）
PHARMA_MODEL_BASE_URL=https://open.bigmodel.cn/api/paas/v4
PHARMA_MODEL_KEY_FILE=/受控目录/your_key.txt      # 密钥只走文件路径
# 数据提取模型（小模型，赛题多模型协作加分项）；未配置回退主模型
PHARMA_MODEL_EXTRACTION_MODEL=glm-4.5-air
# 或 JSON 路由表：PHARMA_MODEL_ROUTES={"extraction":{"model":"..."}}
```

“模型与设置 → 模型连接”页提供厂商预填充（智谱/DeepSeek/通义/Kimi/硅基流动/OpenAI 与本地 Ollama/vLLM/LM Studio，2026-09-22 核对官方文档）与推理强度选择（按厂商映射为 `reasoning_effort`/`thinking`/`enable_thinking`）；模型档位仅作填写建议，兼容型号均可手动输入。向量模型仅本地 ONNX，切换路径后由脚本校验＋数据分析模型适配评估＋知识库重建自动完成。

支持任意 OpenAI 兼容端点（DeepSeek、通义等）；协议可为 `openai`/`anthropic`。每次调用记录响应 model 身份、预算、usage、缓存与实际端点。仓库记录的2026-09-18暂定授权策略为：主端点错误1113后允许切换PHARMA_MODEL_CODING_BASE_URL，置空可禁用。该记录不证明任意账号套餐都可用；本次管理未调用模型、未改变端点策略。详见docs/ZCODE_HANDOFF.md最新政策段。

## 测试与验收 / Tests & Acceptance

```bash
TMPDIR=/tmp PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=05_原型/backend 05_原型/.venv/bin/python -m pytest -q 05_原型/tests   # Windows: .venv/Scripts/python.exe
05_原型/.venv/bin/python 05_原型/scripts/check_environment.py --strict
bash 05_原型/scripts/verify.sh --manifest <运行目录>/manifest.json
```

当前验收索引：[docs/current_run.json](docs/current_run.json)；条款矩阵：[docs/implementation_status.md](docs/implementation_status.md)。verify 退出 0=自动维度通过，1=失败，2=未完成；真人评审（0–5 归因评分等）始终独立，AI 不代填。

## 文档索引 / Documentation

- [系统架构（含架构图/RAG流程图）](docs/architecture.md)
- [Prompt 设计与解释合同](docs/prompt_design.md)
- [报告模板解析逻辑](docs/template_parsing.md)
- [检索与生成合同](docs/retrieval_contracts.md) · [RAG 摘要](docs/rag.md)
- [API 与运维](docs/api_and_operations.md)
- [数据契约](docs/data_contract.md) · [第三方引用与许可](docs/third_party_reuse.md)
- [架构决策记录 ADR](docs/adr/0004-industry-packs.md)
- [行业包开发指南](docs/industry/development.md)
- [GLM-5.3 交接](docs/ZCODE_HANDOFF.md)

## 交付边界 / Delivery Boundary

仓库按用户 2026-09-18 明确授权保留原赛题数据（知识、模板与静态交付）并公开提交；密钥、`.env`、运行数据库、待发队列与恢复备份不入库。赛题数据仅限本次大赛使用（见赛题保密条款），本授权不自动扩展到今后真实企业私有资料。历史移除清单见 [资料边界](docs/privacy_boundary.md)。

## 数据范围 / Data Contexts

赛题数据包位于仓库内，`bootstrap.sh` 默认摄取——启动后“数据范围”即有 `pharmaceutical:competition`（S1/S2/S3/Q2 原题场景，`competition_configuration/scenarios.json` 为验收清单）。通过“数据中心·业务数据”导入并解析的新数据集会追加为新的数据范围。合成演示上下文默认不进目录（`PHARMA_SHOW_TEST_CONTEXTS=1` 可列出校验）；目录为空时工作台引导到数据中心导入。
