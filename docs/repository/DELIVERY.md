# 比赛交付导航

开发审计基线：cdd9cb9（2026-09-19核验）；运行版本与媒体来源分别记录，不把日期相同当成同一次生成。

| 交付项 | 当前入口 | 判断 |
|---|---|---|
| 系统源码及启动依赖 | [应用README](../../药衡智析_增量源码交接/public_source_candidate/README.md) | 已存在；本次未整机复跑 |
| 技术架构/RAG/Prompt/模板/API | [架构](../../药衡智析_增量源码交接/public_source_candidate/docs/architecture.md)、[文档索引](../../药衡智析_增量源码交接/public_source_candidate/README.md#文档索引--documentation) | 有实现说明，专业能力以审计边界为准 |
| 最新自动运行 | [current_run](../../药衡智析_增量源码交接/public_source_candidate/docs/current_run.json) | 5974275存档七维PASS；本轮纠正七job映射，没有重新实调 |
| 正式评测说明 | [evaluation_report](../../药衡智析_增量源码交接/public_source_candidate/docs/evaluation_report.md) | 真人归因0–5、可读性、版式仍PENDING；competition_ready=false |
| 七份静态DOCX/PDF及页图 | [release_20260918](../../药衡智析_增量源码交接/public_source_candidate/07_交付/release_20260918/README.md) | 来源47c5806 DeepSeek解释，随6ff894f发布；不等于5974275 GLM报告 |
| 演示视频 | [媒体目录](../../药衡智析_增量源码交接/public_source_candidate/07_交付/demo_20260918/README.md) | 实测100.56秒字幕视频；缺实际新RPA发送动作，需补录 |
| 决赛PPT | 同上，10页PPTX与原生渲染 | 有可读稿，需增加实证结果与业务证据页 |
| 第三方许可 | [third_party_reuse](../../药衡智析_增量源码交接/public_source_candidate/docs/third_party_reuse.md) | 保留各组件声明；项目自有代码总许可证待团队决定 |

## 证据范围

manifest与verification的七个job一致；本轮已把current_run同步到这一映射，错误旧条目另存作来源未确认记录。模型/检索/RPA/浏览器回执多数只有run/commit级绑定，缺逐job及产物字节关联，不能据此声称完整链条已独立重验。

本次审计修复文档不会把历史FAIL或PENDING改成实际运行PASS。旧47c/6ff报告、v18b、air2、5974275分别保留来源；air2为6/7、verify退出1。仓库检查CI只验证入口/索引/媒体哈希，不替代222项应用测试、模型API、浏览器和真人评分。

正式提交前：修复AUDIT列出的业务问题；用同一次运行绑定报告、模型/检索、RPA与媒体；真人完成三场景归因评分；补录发送动作并更新答辩证据。清理待批准文件和整合main按CLEANUP_PROPOSAL执行，不先删除原件。


2026-09-19 治理更新：C02 的 7 份知识 PDF 使用 PACKAGE 原件，路径映射见 `docs/repository/deduplication_mapping.json`（Git 根相对路径）；CSV 与原 ZIP 保留。C05 另绘阅读 PDF/10 张 PNG 已归档移除，当前阅读使用 `pptx_render` 原生渲染；旧阅读版身份保留于媒体历史清单。默认生成仅 PPTX，`--reading-preview` 可选预览输出到忽略的 `_reading_preview/`。
