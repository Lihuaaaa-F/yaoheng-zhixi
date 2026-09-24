# 当前开发状态 · 2026-09-23

本轮将工作台统一为左侧导航、成本分析区和右侧 AI 助手，完善数据与知识导入、独立模型连接和证据查看。助手的型号、推理强度、上下文圆环位于输入框内，密钥在模型连接页管理；顶栏显示部署位置、外网探测和数据快照更新时间。

- [本轮实现与验证边界](药衡智析_增量源码交接/public_source_candidate/docs/workspace_upgrade_20260923.md)
- [唯一当前验收索引](药衡智析_增量源码交接/public_source_candidate/docs/current_run.json)
- [安装和启动](药衡智析_增量源码交接/public_source_candidate/README.md)

本轮没有使用真实付费模型账号，云模型质量、Docker 净机部署和真人比赛评审仍需分别验收。下面保留历史版本的结果和来源，不能用旧回执代替本轮验收。

---

历史执行记录（2026-09-21）：按《[问题清单_全面审计_20260921](docs/问题清单_全面审计_20260921.md)》完成全面修复并实测（git 25d44bc..16e6301）：**归因主线根治**——叙事合同升级 v10（注册值四舍五入唯一绑定，模型写"下降15.2%"由程序绑定 -15.2153%，编造数字仍拒收）+ 默认模型 glm-5.3（reasoning_effort=low，端点明示不支持关闭思考），实测两场景 narrative/model_participation 双 **PASS**（身份 VERIFIED、每份 2 次调用），PDF 无降级横幅；对标冷请求 60-72s→**14.7-18.6s**；热力图每次 14s→**缓存命中 0.29s**；降级报告前端一键"重新生成（忽略缓存）"；净机 Docker 构建默认直连（代理不再默认）；设置端点安全收紧（key_file 白名单/https 强制/可选 token）；RAG 补齐四份知识文档（11 源 180 chunks）；二厂合成明细全程标注；报告成色四项（建议去重/亮点规则/附录扩充/编制人）；版本指纹与模型默认值单一来源。新交付证据：`07_交付/delivery_20260921/`（current_run 已刷新）。**仍待真人**：三场景 0-5 评分、演示视频重录、净机部署演练。

此前更新（2026-09-20）：完成可信度修复九项（对标单位口径/检索范围/验收合同版本化/叙事路由贯穿/降级重试/Agent产物健康/任务范围分页/启动就绪/跨路径指标合同，回归 307 通过+1 跳过，定向反例测试入档）；新增**正式 Docker 交付**（三服务 Compose + 健康检查 + 持久卷，容器内报告链路实测 docx+pdf PASS）与**桌面启动器**（仓库根 `药衡智析启动器.bat`，启停/状态/日志/防重复启动实测通过）；产品侧新增**数据中心导入向导**（上传→预览→映射→质检→能力预览→发布，新企业免改码接入实测）、**知识中心**与**系统设置**（模型连接统一配置、真实短生成测试、密钥不回显）；正式演示目录收敛到赛题制药（机械/化工仅测试可见，`PHARMA_SHOW_TEST_CONTEXTS=1`）。项目评估见 `docs/项目评估报告_20260920.md`。**现行演示视频**：`07_交付/demo_20260920/yaoheng_full_demo_20260920.mp4`（2分50秒全流程：分析条件选择→成本看板→口径溯源→±10%重点分析→对标三步法完整顺序→报告生成与下载→建议转整改任务→确认发送模拟RPA送达→任务统计；可见光标+逐步中文注释；三个旧演示视频文件已删除并在原清单标注替代关系）。真人三场景 0—5 评分仍待补，不能据此宣称比赛验收完成。

此前更新（2026-09-19）：当前运行 `delivery_20260919_final`，应用受测修订 `04011c2`。本机用户明确选择 DeepSeek，七次真实调用通过；最终七份 Word/PDF 使用同输入的已验证叙事缓存，新增模型请求为零。数值、检索、模型、模拟 RPA、浏览器与文件关联自动检查通过。当前交付位于 `07_交付/delivery_20260919_final/`（应用根相对路径）：59.16秒实际闭环视频、十页PPT及原生渲染、七份报告共38页、待评表。源码修复和边界见 Git根 `docs/repository/FIXES_20260919.md`。旧运行、旧GLM/DeepSeek和失败回执保持原始来源；下方较早记录为历史背景。

---

# 药衡智析 · 成本智能分析

面向制造企业的成本分析原型，以制药赛题为主场景，提供成本看板、证据支持的分析报告、跨厂对标和模拟 RPA 整改流程。确定性引擎管理数字，大模型辅助解释；机械与化工包采用独立合成数据验证框架迁移。

**当前状态：可继续开发的比赛原型，尚未完成比赛整体验收。** 已有模型和自动验证记录，真人归因、可读性与正式版式评审仍待完成。详见 [本次修复与验证](docs/repository/FIXES_20260919.md)，[旧审计](docs/repository/AUDIT_20260919.md)保留为基线。

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
