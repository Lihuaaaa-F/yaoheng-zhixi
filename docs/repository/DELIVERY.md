# 比赛交付导航 · 2026-09-24

本轮代码已整合队友 `d8054ba`，实测修订为本地 `2087978`。当前离线链路可供团队复验，完整比赛验收尚未通过。GitHub 写入返回 403，补丁尚需由有权限的连接应用并正常推送。

| 交付项 | 当前入口 | 状态 |
|---|---|---|
| 源码与启动依赖 | [应用 README](../../药衡智析_增量源码交接/public_source_candidate/README.md) | Linux 原生启动与依赖实测，Docker/Windows 本轮未实跑 |
| 技术方案与 API | [架构](../../药衡智析_增量源码交接/public_source_candidate/docs/architecture.md)、[API](../../药衡智析_增量源码交接/public_source_candidate/docs/api_and_operations.md) | 既有实现说明与当前审计边界一起阅读 |
| 当前验收 | [运行索引](../../药衡智析_增量源码交接/public_source_candidate/docs/current_run.json) | 五自动维度 PASS，模型/混合检索 FAIL，真人 PENDING |
| 评测及逐条赛题 | [评测](../../药衡智析_增量源码交接/public_source_candidate/docs/evaluation_report.md)、[审计](DELIVERY_AUDIT_20260924.md) | 实测证据和外部缺口明确分开 |
| 本轮四场景 Word/PDF | [报告与证据](../../药衡智析_增量源码交接/public_source_candidate/docs/validation/delivery_verified_20260924/README.md) | 规则降级，8 文件生成与实际下载通过 |
| 本轮演示与答辩稿 | 当前媒体路径见运行索引 | 演示保留本轮模型与向量降级提示 |
| 历史演示 | `07_交付/demo_20260920/yaoheng_full_demo_20260920.mp4`（应用根） | 2分50秒历史全流程，不记为本轮验证 |
| 历史十页 PPT | `07_交付/delivery_20260919_final/deck/药衡智析_演示与答辩稿.pptx` | 保留旧来源，不将旧指标移用到当前代码 |
| 真人待评 | [待评表](../../药衡智析_增量源码交接/public_source_candidate/docs/validation/delivery_verified_20260924/human_review_pending.csv) | S1/S2/S3 归因、可读性与版式由真人署名填写 |

报告、检索、模型、模拟 RPA、浏览器回执已按同一 run/commit/attempt/job/snapshot/artifacts 关联。没有把历史失败改为通过，没有把旧调用记为新调用。模拟送达不等于真人确认或业务整改完成。

原题资源保持原样，原有媒体清单不改写。仓库自有代码许可证仍由团队决定，各第三方声明继续保留。`tools/verify_repository.py` 仅检查导航、索引和既有媒体身份，不能代替应用或人工验收。
