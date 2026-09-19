当前交付与运行已更新：见 [执行结果](FIXES_20260919.md)。以下旧审计来源保留，当前入口以应用 docs/current_run.json 为准。

# 仓库结构与整理范围

本轮先建立清楚的根入口、当前版本说明、贡献约定、交付导航与只读检查，保留应用实际路径，避免移动目录破坏配置、脚本及产物来源。当前专业交付的首要缺口是默认分支未整合、索引冲突和交付声明失真，而不是单纯改用英文目录名。

| 职责 | 当前权威位置 |
|---|---|
| 项目入口与协作 | 根 README.md、CONTRIBUTING.md |
| 应用源码、测试、锁与脚本 | 药衡智析_增量源码交接/public_source_candidate/05_原型/ |
| 架构、合同、当前运行及历史回执 | 应用根 docs/ |
| 合成行业与企业配置 | 05_原型/industry_packs/；比赛配置另在competition_configuration/ |
| 题包原件及现存数据/知识 | 应用根00/01/02目录，保留既有范围和原件字节 |
| 选定静态报告与演示 | 应用根07_交付/release_20260918、demo_20260918，按DELIVERY说明来源 |
| 仓库治理与删除清单 | 根docs/repository/ |

不按“越旧越应该删”处理历史回执。原始ZIP、净化解压、解析/索引及实际依赖的CSV副本作用不同；内容相同不代表可直接移除。源代码、字体及许可不能为缩小仓库一并清除。

## 待批准后的实施

先按CLEANUP_PROPOSAL的精确清单处理冗余入口/派生件，再正常整合已审计工作分支到main。整合会使main应用队友已有的删除，因此该部分也在待批准范围内。保留所有共享提交、分支和标签，不重写历史。

目录整体改名不是本次已执行事项。若团队随后希望进一步压平，可将05_原型作为app/、技术docs提升根目录、资源与交付分别集中，但须先验证ROOT推导、报告索引、脚本/测试和文档引用，再列出源→目标清单；不能在当前批准清单之外顺带搬迁。

参考：[GitHub README与相对链接](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)。


2026-09-19 治理更新：C02 的 7 份知识 PDF 使用 PACKAGE 原件，路径映射见 `docs/repository/deduplication_mapping.json`（Git 根相对路径）；CSV 与原 ZIP 保留。C05 另绘阅读 PDF/10 张 PNG 已归档移除，当前阅读使用 `pptx_render` 原生渲染；旧阅读版身份保留于媒体历史清单。默认生成仅 PPTX，`--reading-preview` 可选预览输出到忽略的 `_reading_preview/`。
