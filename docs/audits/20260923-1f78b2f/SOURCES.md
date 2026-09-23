# SOURCES.md — 审查依据与外部资料

## 一、仓库内权威来源（本轮全文/关键部分读取）

| 来源 | 用途 | 核对点 |
|---|---|---|
| `00_赛题原始资料/7.（创灵境）…企业出题.docx` | 赛题规范唯一基准 | python-docx 全文提取（160 段落+5 表格），逐条拆为 REQ-ID；项目转写版 `赛题要求_企业出题创灵境.md` 关键条款抽查一致 |
| `模拟数据_V1.1…/README.md` | 数据口径说明（6 波动设计/派生公式/对照表） | 人工工时派生公式、月度特征、预算口径与 metrics.labor_metrics 实现核对一致 |
| `模拟数据_V1.1…/问题检查报告.md` | 出题方数据修复记录 | P0 预算/工时补齐说明，与数据包文件核对 |
| `04_报告模板/月度成本分析报告模板.md/.docx` | 模板占位符合同 | md 全读；docx 经 normalize_template 提取（约 88 占位符） |
| `05_RPA接口文档/模拟RPA接口文档.md` + `mock_rpa_server.py` | RPA 协议规范 | 全读；RPA 端到端实测即运行该原版 mock |
| `docs/`（architecture/rag/prompt_design/template_parsing/api_and_operations/evaluation_report/third_party_reuse/publication-authorization/retrieval_contracts 头部） | 技术方案五要素、评测、许可证、发布授权 | 与实现一致性核对 |

## 二、外部资料（访问日期均为 2026-09-23）

| URL | 支持的审查项 | 借鉴范围 |
|---|---|---|
| https://github.com/trailofbits/skills @32e34f8 | 审查方法论（audit-context-building / spec-to-code-compliance / agents 定义） | portable/manual 模式全文加载；应用于"跟随调用链/absent 须有搜索记录/六态判定/独立反证"；property-based-testing 与 sharp-edges 按需节选其纪律（未另行逐字加载全文） |
| `C:\Users\ShiyuFang\.zcode\skills\codebase-design\SKILL.md`（Matt Pocock，本机 1.2.3 系） | 架构评价词汇（deep module/seam/adapter） | 仅用于 AUD-GEN/ARCH 的表述与改进方案比较 |
| OpenAI 兼容格式约定（chat/completions、response_format、usage/model 回显） | AUD-T-01/MODEL-03 身份核验与结构化输出判断 | 依据广泛公开的 OpenAI API 语义 + 项目 third_party_reuse 版本表；未另拉网页 |
| 智谱 BigModel 端点（open.bigmodel.cn/api/paas/v4 与 coding 端点）、错误码 1113 | 双端点回退政策判断 | 代码内注释记载的用户 2026-09-18 授权政策 + 本轮 V5 实测响应；官方文档页面本轮未抓取（政策依据为团队授权记录，已在 AUD-SEC-01 标注边界） |

## 三、未使用/无法访问

- 赛事官方评分细则、获奖概率信息：**不存在于题包**，本轮未编造任何权重/合格线。
- 演示视频画面、PPT 渲染、报告逐页视觉效果：无视觉能力，全部转 VISUAL_HANDOFF。
- 净机 Docker 构建实测：未执行（见 REVIEW V8 缺口标注）。
