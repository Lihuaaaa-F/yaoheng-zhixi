> 本机接续（2026-09-24）：修复包已接入，正在配置共享环境；本机测试尚未执行，人工检查与评分待进行。下文修复包结果为历史结果。视频、PPT：用户暂缓。本轮状态见应用 `docs/current_run.json`。

# 当前交付状态 · 2026-09-24

已整合队友最新 `d8054ba` 并修复本轮审计问题。受测代码 `2087978`：后端 601 通过、1 跳过，2,160 项原题独立计算核对误差为 0，前端 6 合同及 18 视口通过，原题四场景 Word/PDF、8 次下载和 4 次模拟 RPA 发送通过。

**完整比赛验收仍未通过**：真实模型、完整向量混合检索与真人三场景评分待补齐。本环境 GitHub 写入返回 403，本地修复尚未推送。当前结论与旧运行分开记录。

- [本轮修复与赛题对照](docs/repository/DELIVERY_AUDIT_20260924.md)
- [当前验收索引](药衡智析_增量源码交接/public_source_candidate/docs/current_run.json)
- [当前报告与证据](药衡智析_增量源码交接/public_source_candidate/docs/validation/delivery_verified_20260924/README.md)
- [安装与启动](药衡智析_增量源码交接/public_source_candidate/README.md)

---

# 药衡智析 · 成本智能分析

面向制造企业的成本分析原型，以制药赛题为主场景，提供成本看板、证据支持的分析报告、跨厂对标和模拟 RPA 整改流程。确定性引擎管理数字，大模型辅助解释；机械与化工包采用独立合成数据验证框架迁移。

**当前状态：可继续开发的比赛原型，尚未完成比赛整体验收。** 已有模型和自动验证记录，真人归因、可读性与正式版式评审仍待完成。详见 [本轮交付审计](docs/repository/DELIVERY_AUDIT_20260924.md)。历史模型与媒体保留原始身份。

## 从哪里开始

| 目的 | 入口 |
|---|---|
| 安装、启动与模型配置 | [应用 README](药衡智析_增量源码交接/public_source_candidate/README.md) |
| 当前运行与证据边界 | [当前索引](药衡智析_增量源码交接/public_source_candidate/docs/current_run.json) · [评测说明](药衡智析_增量源码交接/public_source_candidate/docs/evaluation_report.md) |
| 架构、接口和行业包 | [架构](药衡智析_增量源码交接/public_source_candidate/docs/architecture.md) · [API](药衡智析_增量源码交接/public_source_candidate/docs/api_and_operations.md) · [行业包指南](药衡智析_增量源码交接/public_source_candidate/docs/industry/development.md) |
| 比赛交付文件 | [交付导航与成熟度](docs/repository/DELIVERY.md) |
| 接续开发 | [贡献与协作](CONTRIBUTING.md) · [GLM 交接](药衡智析_增量源码交接/public_source_candidate/docs/ZCODE_HANDOFF.md) |
| 目录整理 | [仓库管理方案](docs/repository/STRUCTURE.md) · [已授权清理清单](docs/repository/CLEANUP_PROPOSAL.md) |
| 许可证与资源边界 | [许可证状态](docs/repository/LICENSE_STATUS.md) · [资源发布记录](药衡智析_增量源码交接/public_source_candidate/docs/publication-authorization.md) |

## 本地运行

**方式一（推荐 · 正式运行环境）**：双击仓库根 `药衡智析启动器.bat` → 选择"启动"。首次构建镜像；向量模型下载由 `PHARMA_FETCH_EMBEDDING=1` 显式启用，缺少时如实使用词法检索；日常复用镜像启动，重复双击不会重复启动一套服务。启动器提供启动/停止/状态/日志及更新构建入口，未装 Docker、引擎未运行、WSL 集成未开启、服务启动失败分别给出可操作中文提示。Compose 定义在 `药衡智析_增量源码交接/public_source_candidate/05_原型/deploy/docker-compose.yml`（Web/API、后台任务、模拟 RPA 三服务，命名卷持久化业务数据，默认仅本机 127.0.0.1 访问；赛题原件只读挂载，密钥经 `PHARMA_MODEL_KEY_FILE` 注入、不写入镜像或仓库）。

**方式二（开发环境）**：从仓库根进入现有应用根，复用项目启动入口：

```bash
cd 药衡智析_增量源码交接/public_source_candidate
bash 05_原型/scripts/bootstrap.sh
bash 05_原型/scripts/start.sh
# 浏览器打开 http://127.0.0.1:8765
# 使用结束：bash 05_原型/scripts/stop.sh
```

bootstrap 检测并复用兼容依赖，补装缺项；默认进入赛题制药场景（合成数据与测试上下文不进正式目录）。没有模型或语义检索资产时存在降级模式（启动器与页面均明确标注），不能将降级视为完整 RAG/模型验收。正式 Word→PDF 需要 LibreOffice（Docker 镜像已内置）。模型连接可在「模型与设置 → 模型连接」页配置并执行真实短生成测试；数据接入走「数据中心」向导。具体环境说明见应用 README。

## 能力与限制

- 报告、趋势/结构/瀑布图、三步对标、任务送达及行业切换已实现，有对应测试或运行记录。
- 图谱、任务模型路由、规则决策和预测已有原型；运行成功不能代替增益对照。已补产品×月份网格并修复预测初始化/缺月；预测范围仍属实验，专业收益未验收。
- 机械/化工参考包证明同一核心可处理不同单位与指标，尚无真实行业落地及独立未见评测证据。
- 所有发送为模拟 RPA；真人签收、归因评分及整改完成不由 AI 代填。

## 分支与交付纪律

2026-09-19 审计的开发基线为 `codex/core-industry-20260917@cdd9cb9`，本治理分支为 `codex/repository-governance-20260919`。`main` 当时仍是 `acc4693`；默认分支未整合不能理解为队友没有新成果。治理已按明确授权精确去除18份副本，保留全部提交、分支和标签。M01/C02/C05/L01 已获用户明确批准，按清单校验归档后执行；详见 docs/repository/execution_status.json。

不要在工作区未检查时无条件 `pull --rebase --autostash`，不要强推共享历史。项目源码许可尚未统一确定；第三方声明继续保留。仓库记录了 9 月 18 日赛题资源发布授权，本次未扩大资源发布范围或另行发布原件；后续真实企业数据仍需独立确定边界。

仓库检查：`python3 tools/verify_repository.py`。它仅检查导航、索引一致性和媒体清单，不代表应用测试、模型实调或人工评审通过。

English: A contest prototype for evidence-supported manufacturing cost analysis. Follow the application README for setup; see DELIVERY for artifact provenance. Automated records and human acceptance are separate. Industry examples are synthetic, and RPA delivery is simulated.


2026-09-19 治理更新：C02 的 7 份知识 PDF 使用 PACKAGE 原件，路径映射见 `docs/repository/deduplication_mapping.json`（Git 根相对路径）；CSV 与原 ZIP 保留。C05 另绘阅读 PDF/10 张 PNG 已归档移除，当前阅读使用 `pptx_render` 原生渲染；旧阅读版身份保留于媒体历史清单。默认生成仅 PPTX，`--reading-preview` 可选预览输出到忽略的 `_reading_preview/`。
