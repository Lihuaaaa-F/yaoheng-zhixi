# 药衡智析项目实施规则

先读 docs/implementation_status.md、CONTEXT.md、相关 docs/adr。唯一工作目录为本 WSL 目录，D盘只读基线，禁止双向同步。无Git仓：审查以 docs/baseline.json 逐文件哈希为固定点，不强制commit或创建PR。

## Agent skills

共享原文位于 /home/hujunjie/.codex/skills/{setup-matt-pocock-skills,domain-modeling,codebase-design,tdd,diagnosing-bugs,code-review}/SKILL.md，锁定 SHA 3cca18b368ae95cdbdebbff572ccafa662551015。当前会话按路径读取；原生发现以新会话实际结果为准。
- 配置已由用户确认：本地 Markdown；docs/agents/issue-tracker.md；不建外部工单、不triage、不重复访谈。
- 领域术语沿用 CONTEXT.md；允许 API、组件等自然表达。仅在减少真实重复与隔离外部变化时设计接口，不为技能增层。
- TDD已授权接口：指标与单位换算、模板/导出、检索/引用、RPA发送/查询、用户E2E。关键行为逐条红→绿，独立golden。不为文案样式机械加测试。
- 调试用真实复现→观测→修复→回归；明确简单错误无需形式化多假设或千次循环。
- code-review分规范与规格两路，包含基线以来新增及修改，不以HEAD diff替代工作区，不强制提交。

## 代码与数据

源码唯一在05_原型，Python backend/pharma模块：ingestion、metrics、knowledge、narrative、reports、actions、api。React frontend。原材料、原模板、原mock不修改；工作模板可建一份。金额Decimal，指标快照跨看板报告复用，缺值必须含原因。sqlite持久化worker/outbox，发送需确认。密钥仅文件读取，绝不输出或打包。默认127.0.0.1，不外发、不公开。

## 并行所有权

主Agent：配置、环境、reports/actions/api/worker、脚本、集成与最终文档。
数据Agent：ingestion.py、metrics.py、tests/test_metrics.py、tests/test_ingestion.py、数据契约/独立golden。
检索Agent：knowledge.py、narrative.py、相关测试、检索评测集和结果。
前端Agent：frontend全目录、浏览器E2E脚本及证据。
公共合同修改先同步主Agent；不改他人所有文件。
