# 药衡智析 · 产品成本智能分析报告系统

**基于 RAG 与大模型的制药企业产品成本智能分析报告系统**（2026 年第二届重庆市 AI 大模型创新应用大赛 · 创灵境企业出题）。通用成本分析核心＋可切换行业包：制药赛题合同完整保留，机械零部件、化工为独立合成参考包，用于验证框架横向迁移能力。

> **English summary** — Yaoheng Zhixi is a RAG + LLM powered product-cost analysis and reporting system for a pharmaceutical contest scenario. A deterministic Decimal cost engine feeds an evidence-bound report pipeline (Word/PDF), an ECharts dashboard with attribution/waterfall/heatmap, a cross-factory three-step benchmark, and an RPA task loop against a local simulator. Bonus features implemented: knowledge-graph enhanced retrieval, multi-model routing, agent report-or-dashboard decision, and Holt-based cost forecasting. All numbers are program-owned; the model only picks references and wording under a strict validator contract.

## 功能总览 / Feature Map

| 赛题模块 | 实现 | 入口 |
|---|---|---|
| 模块一 智能报告生成 | Word 模板解析（占位符+书签锚点）、RAG 增强、PDF/Word 双导出 | `05_原型/backend/pharma/reports.py` |
| 模块二 看板与归因 | 趋势/瀑布/结构/热力图、贡献度、±10% 告警重点分析 | `metrics.py`、`frontend/src/Analysis.tsx` |
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
PHARMA_MODEL=glm-5.3-flash
PHARMA_MODEL_BASE_URL=https://open.bigmodel.cn/api/paas/v4
PHARMA_MODEL_KEY_FILE=/受控目录/your_key.txt      # 密钥只走文件路径
# 多模型协作（可选）：轻量任务路由到更经济的模型
PHARMA_MODEL_DECISION_MODEL=glm-4.5-air
# 或 JSON 路由表：PHARMA_MODEL_ROUTES={"decision":{"model":"..."}}
```

支持任意 OpenAI 兼容端点（DeepSeek、通义等）；协议可为 `openai`/`anthropic`。每次调用核验响应 model 身份并记账（预算、usage、缓存）；Coding Plan 凭据禁止用于应用运行时。

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

## 启用比赛数据 / Enable Contest Data

```bash
YAOHENG_APP_ROOT="$(pwd -P)"
export PHARMA_DATA_PACKAGE="$YAOHENG_APP_ROOT/00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据"
export PHARMA_PRIVATE_MASTERDATA_FILE="$YAOHENG_APP_ROOT/competition_configuration/pharmaceutical_masterdata.json"
export PHARMA_PRIVATE_TERMINOLOGY_FILE="$YAOHENG_APP_ROOT/competition_configuration/pharmaceutical_terminology_original.json"
bash 05_原型/scripts/stop.sh 2>/dev/null; bash 05_原型/scripts/bootstrap.sh && bash 05_原型/scripts/start.sh
```

成功后行业/企业选择中出现 `pharmaceutical:competition`（S1/S2/S3/Q2 原题场景）；三个合成上下文独立保留。`competition_configuration/scenarios.json` 是比赛验收场景清单（`run_acceptance.py --private-scenarios`）。未启用时 bootstrap 跳过原题摄取，仅构建合成包，不会用合成合同校验原题数据。
