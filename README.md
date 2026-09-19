# 药衡智析 · 成本智能分析

面向制造企业的成本分析原型，以制药赛题为主场景，提供成本看板、证据支持的分析报告、跨厂对标和模拟 RPA 整改流程。确定性引擎管理数字，大模型辅助解释；机械与化工包采用独立合成数据验证框架迁移。

**当前状态：可继续开发的比赛原型，尚未完成比赛整体验收。** 已有模型和自动验证记录，真人归因、可读性与正式版式评审仍待完成。详见 [本次审计](docs/repository/AUDIT_20260919.md)。

## 从哪里开始

| 目的 | 入口 |
|---|---|
| 安装、启动与模型配置 | [应用 README](药衡智析_增量源码交接/public_source_candidate/README.md) |
| 当前运行与证据边界 | [当前索引](药衡智析_增量源码交接/public_source_candidate/docs/current_run.json) · [评测说明](药衡智析_增量源码交接/public_source_candidate/docs/evaluation_report.md) |
| 架构、接口和行业包 | [架构](药衡智析_增量源码交接/public_source_candidate/docs/architecture.md) · [API](药衡智析_增量源码交接/public_source_candidate/docs/api_and_operations.md) · [行业包指南](药衡智析_增量源码交接/public_source_candidate/docs/industry/development.md) |
| 比赛交付文件 | [交付导航与成熟度](docs/repository/DELIVERY.md) |
| 接续开发 | [贡献与协作](CONTRIBUTING.md) · [GLM 交接](药衡智析_增量源码交接/public_source_candidate/docs/ZCODE_HANDOFF.md) |
| 目录整理 | [仓库管理方案](docs/repository/STRUCTURE.md) · [待批准清理清单](docs/repository/CLEANUP_PROPOSAL.md) |
| 许可证与资源边界 | [许可证状态](docs/repository/LICENSE_STATUS.md) · [资源发布记录](药衡智析_增量源码交接/public_source_candidate/docs/publication-authorization.md) |

## 本地运行

从仓库根进入现有应用根，复用项目启动入口：

```bash
cd 药衡智析_增量源码交接/public_source_candidate
bash 05_原型/scripts/bootstrap.sh
bash 05_原型/scripts/start.sh
# 浏览器打开 http://127.0.0.1:8765
# 使用结束：bash 05_原型/scripts/stop.sh
```

bootstrap 检测并复用兼容依赖，补装缺项；默认合成数据无需比赛原件或模型密钥。没有模型或语义检索资产时存在降级模式，不能将降级视为完整 RAG/模型验收。正式 Word→PDF 需要 LibreOffice；具体环境与比赛数据启用方式见应用 README。上述启动能力有历史验证，本次仓库管理没有重新安装或启动整套系统。

## 能力与限制

- 报告、趋势/结构/瀑布图、三步对标、任务送达及行业切换已实现，有对应测试或运行记录。
- 图谱、任务模型路由、规则决策和预测已有原型；运行成功不能代替增益对照。当前热力图不完整覆盖产品×月份维度，预测还有已确认缺陷。
- 机械/化工参考包证明同一核心可处理不同单位与指标，尚无真实行业落地及独立未见评测证据。
- 所有发送为模拟 RPA；真人签收、归因评分及整改完成不由 AI 代填。

## 分支与交付纪律

2026-09-19 审计的开发基线为 `codex/core-industry-20260917@cdd9cb9`，本治理分支为 `codex/repository-governance-20260919`。`main` 当时仍是 `acc4693`；默认分支未整合不能理解为队友没有新成果。治理提交只新增或修订文档、索引和仓库检查，不删除文件、分支、标签或提交。含文件删除的整合/清理等待用户按精确清单批准。

不要在工作区未检查时无条件 `pull --rebase --autostash`，不要强推共享历史。项目源码许可尚未统一确定；第三方声明继续保留。仓库记录了 9 月 18 日赛题资源发布授权，本次未扩大资源发布范围或另行发布原件；后续真实企业数据仍需独立确定边界。

仓库检查：`python3 tools/verify_repository.py`。它仅检查导航、索引一致性和媒体清单，不代表应用测试、模型实调或人工评审通过。

English: A contest prototype for evidence-supported manufacturing cost analysis. Follow the application README for setup; see DELIVERY for artifact provenance. Automated records and human acceptance are separate. Industry examples are synthetic, and RPA delivery is simulated.
