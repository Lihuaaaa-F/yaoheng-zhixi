# SOURCES.md —— 本轮审查外部/内部资料来源

## 外部资料（下载并核实版本）

| 资料 | URL | 访问日期 | 版本/修订 | 支持的审查项 | 借鉴范围 |
|---|---|---|---|---|---|
| Trail of Bits skills: audit-context-building | https://github.com/trailofbits/skills | 2026-09-23 | rev 32e34f8173796e3566a51aee877dc96bc5191f64（clone --filter=blob:none + checkout --detach，HEAD 与工作区校验通过） | 全部模块的方法框架（函数级假设/依赖/异常路径记录、nothing found 规则） | 方法论全文加载（SKILL.md/DOMAIN_NOTES/ANALYSIS_FORMAT/function-analyzer.md），portable/manual 执行 |
| Trail of Bits skills: spec-to-code-compliance | 同上 | 同上 | 同上 | 赛题→REQ→六值判定、absent 的 searched 记录规则 | 同上（含 spec-compliance-checker.md） |
| Matt Pocock codebase-design（本机已装） | C:/Users/ShiyuFang/.zcode/skills/codebase-design/SKILL.md | 2026-09-23 | 本地 2026-09-21 更新版（1.2.3 序列） | FIX 方案的模块/接口/接缝比较用语 | 仅架构建议；未启动其 issue-tracker/HTML 流程 |
| Trail of Bits property-based-testing / sharp-edges | 未下载 | — | — | — | 按任务书"按需"：本轮数值验证以独立对拍实现同等目的，未引入 PBT 库；无新危险配置面需专项扫描，故未调用（如实记录） |

## 内部权威资料（仓库内，审查对象自带——来源优先级：原始件 > 项目改写件）

| 资料 | 路径（worktree 内） | 用途 |
|---|---|---|
| 赛题原始 DOCX | 药衡智析_增量源码交接/public_source_candidate/00_赛题原始资料/7.（创灵境）...企业出题.docx | REQ 唯一权威来源（python-docx 逐段/逐表提取，EVIDENCE/brief_original_extract.txt） |
| 模拟数据包 README + 问题检查报告 | 同目录 模拟数据_V1.1_净化解压/创灵境_考题模拟数据/{README.md, 问题检查报告.md} | 数据结构与不变量基准（单位成本=三要素和、总成本=产量×单位成本、预算年度固定、V1.1 修复记录） |
| 模拟 RPA 接口文档 | 同目录 05_RPA接口文档/模拟RPA接口文档.md | M4 模块字段/状态/端点契约（POST /api/rpa/tasks、200 判定、微信回执、六态状态机） |
| 报告模板 DOCX | 同目录 04_报告模板/月度成本分析报告模板.docx | M1 章节与占位符覆盖对照（EVIDENCE/report_template_extract.txt，101 唯一占位符） |
| 题包成本数据 CSV ×10 | 同目录 01_成本明细数据/、02_行业参考数据/ | 独立数值复算源（EVIDENCE/repro_numeric_independent.py） |
| 项目改写赛题摘要 | 00_赛题原始资料/赛题要求_企业出题创灵境.md | 仅作交叉核对（以其与原文差异为核查点，未作为 REQ 来源） |

## 官方文档核对声明（诚实边界）

- model_settings 的 effort 档位映射注释声称"2026-09-22 逐家核对官方文档"（各厂商 API 文档）——本轮**未联网复核**该映射，按"待实测"处理（AUD-MDL 相关）。
- 检索文档（RRF k=60/权重 0.75/0.25/bge-large-zh MIT）以仓库 docs 与代码一致性核对为准，未外查原论文/许可证文本（MIT 声明采信仓库内 third_party_reuse 记录）。
- 除上表外部技能仓库外，本轮未引用其他外部网络资料；所有结论均可溯源至仓库内容或本轮隔离运行产物。

## 许可证与来源保留

- ToB skills 仓库 LICENSE 保留于 WSL 克隆目录内（~/.cache/yaoheng-audit-skills/trailofbits-32e34f8173796e3566a51aee877dc96bc5191f64/LICENSE），未修改、未运行其中脚本，仅加载文本。
- 本审查产物（docs/audits/2026-09-23-1f78b2f/）归项目所有，未发布至任何外部站点。
