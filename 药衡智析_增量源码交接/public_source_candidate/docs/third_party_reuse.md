# 第三方组件与技能锁定

更新：2026-09-15。仅记录实际采用、明确参考和跳过的内容；安装/阅读不等于系统验收。应用依赖精确版本见 `05_原型/requirements.lock` 与 `05_原型/frontend/package-lock.json`，安装前环境见 `docs/environment_inventory.json`。

## 已采用组件

|来源|实际版本/SHA|许可证与限制|采用位置/验证依据|
|---|---|---|---|
|[React](https://github.com/facebook/react)|react/react-dom 19.1.1|MIT|frontend；实际编译/浏览器|
|[Apache ECharts](https://github.com/apache/echarts)|5.6.0|Apache-2.0|Chart.tsx，本地打包趋势/结构/瀑布|
|[Vite](https://github.com/vitejs/vite) / [TypeScript](https://github.com/microsoft/TypeScript)|6.4.1 / 5.9.2|MIT / Apache-2.0|项目开发依赖，npm锁|
|[Playwright](https://github.com/microsoft/playwright)|1.58.2|Apache-2.0|项目开发依赖；复用Chrome for Testing149；无alpha升级|
|[FastAPI](https://github.com/fastapi/fastapi) / [Pydantic](https://github.com/pydantic/pydantic)|0.141.1 / 2.13.5|MIT|api.py / Finding约束|
|[DuckDB](https://github.com/duckdb/duckdb)|1.5.5|MIT|参数化读Parquet与版本快照|
|[LlamaIndex](https://github.com/run-llama/llama_index)|llama-index-core 0.14.24|MIT|knowledge.py BaseRetriever/TextNode真实执行；自有确定性RRF不额外生成查询|
|[Chroma](https://github.com/chroma-core/chroma)|1.5.9|Apache-2.0|本地向量持久化，真实检索评测|
|[ONNX Runtime](https://github.com/microsoft/onnxruntime) / [Tokenizers](https://github.com/huggingface/tokenizers)|1.30.0 / 0.23.2|MIT / Apache-2.0|CPU CLS向量归一化，无torch/CUDA|
|[jieba](https://github.com/fxsjy/jieba)|0.42.1|MIT|FTS入库/查询相同词典，BM25排序反例测试|
|[python-docx](https://github.com/python-openxml/python-docx)|1.2.0|MIT|原DOCX工作副本、XML位置绑定与动态表|
|[PyMuPDF](https://github.com/pymupdf/PyMuPDF)|1.28.2|AGPL-3.0，另有商业许可；不是MIT|PDF页解析与导出验证；未修改/复制库源码。后续分发需单独处理适用许可，不能把整个应用依赖统称MIT|
|[Matplotlib](https://github.com/matplotlib/matplotlib)|3.11.2|Matplotlib许可证（基于PSF许可），非统一MIT|报告趋势图使用确定性快照|
|[LibreOffice](https://www.libreoffice.org/)|24.2.7.2|项目许可含MPL2.0/LGPLv3+；系统包依各自版权文件|Writer命令行转换，每任务独立profile，中文小样及真实报告|
|[DeepSeek](https://api-docs.deepseek.com/)|deepseek-flash（V4.1 Flash）|商业API服务条款，不是本地开源模型分发许可|真实/models返回可用ID；生成记录与失败日志，密钥外部文件|

未把任何参考仓整仓拼装成产品，未更改或重新分发第三方库源码。本项目无Git仓，新增/改动依据docs/baseline.json及本地文件记录，不强制commit/push。

## CPU embedding来源及权利边界

实际运行的是 [Xenova/bge-small-zh-v1.5固定转换提交](https://huggingface.co/Xenova/bge-small-zh-v1.5/tree/75c43b069aac4d136ba6bc1122f995fedcfd2781)，SHA `75c43b069aac4d136ba6bc1122f995fedcfd2781`。下载仅约22.8MB量化ONNX与tokenizer，存于 `05_原型/.runtime/models/bge-small-zh-v1.5`，manifest记录文件哈希。

基础 [BAAI/bge-small-zh-v1.5模型卡](https://huggingface.co/BAAI/bge-small-zh-v1.5) 声明MIT；本轮未在Xenova转换权重处确认独立许可证文件。因此记录为“基础模型MIT，转换权重单独许可未明确”，不能将基础模型许可自动等同转换分发已获完整确认。当前只作已授权本地CPU演示，模型缓存不进入公开源码包；正式分发前应保留出处并核对对应权利说明。

## 共享工程Skills

用户追加要求共享安装到 `/home/hujunjie/.codex/skills`，不是项目重复副本；此处“系统级”表示用户跨项目共享，不是修改系统Python或安装到/usr。来源固定为 [mattpocock/skills](https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015)，SHA `3cca18b368ae95cdbdebbff572ccafa662551015`、MIT；只选六个engineering目录，保留上游原文、相对引用和agents配置。各SKILL哈希、frontmatter与安装位置在环境盘点，许可证备份见 `docs/Matt-skills-LICENSE.txt`。

|技能name|上游目录|安装/复用|本轮使用阶段与证据|
|---|---|---|---|
|setup-matt-pocock-skills|skills/engineering/setup-matt-pocock-skills|新装共享|用户配置直接适配到AGENTS.md和docs/agents/issue-tracker.md，无重复访谈或外部工单|
|domain-modeling|skills/engineering/domain-modeling|新装共享|CONTEXT单位/总额/送达术语，docs/adr原位修订|
|codebase-design|skills/engineering/codebase-design|新装共享|指标快照、模板绑定、ModelGateway及ActionStore接口；不改栈或加第二套框架|
|tdd|skills/engineering/tdd|新装共享|季度/对标/告警/模板/RPA公开接口红→绿；06评测对应tdd日志|
|diagnosing-bugs|skills/engineering/diagnosing-bugs|新装共享|依赖、模板单位、模型格式和浏览器失败的复现与回归|
|code-review|skills/engineering/code-review|新装共享|A规范/B规格独立审查：review_standards.md、review_spec.md；审查新增/修改文件而非仅HEAD|

当前会话按明确文件路径读取应用；原生发现状态仍记录 `NOT_VERIFIED_THIS_SESSION`，重载/下一会话后实测，不宣称下载安装即已注册。执行工具可用与技能发现分开：Python/Node/Playwright已实测运行。

项目适配写入AGENTS.md，未改上游技能原文。使用现有本地Markdown和单业务上下文；不建GitHub/GitLab/Linear工单，不triage，不强制commit、PR或发布；本轮具体需求优先于通用技能问答和术语限制。

## 已有Skills复用

|能力|已有来源/位置|采用方式与证据|
|---|---|---|
|React性能|build-web-apps插件0.1.2的react-best-practices（已安装Vercel规则）|复用而非重复安装063bee94…版本；App AbortController、独立Promise.all、Chart dispose与事件清理；未套用RSC/迁移Next.js|
|前端验收|同插件frontend-testing-debugging|Browser插件未提供，采用项目稳定Playwright；真实DOM、网络、控制台、trace、截图，1366×768及1920×1080|
|技术方案报告|data-analytics 1.0.8 build-report|沿用90_工具/build_report_artifact.js和现有HTML/artifact原位更新，不新建第二套报告应用或发布站点|
|DOCX/PDF|无另装专项库技能|使用本机python-docx/PyMuPDF/LibreOffice实际接口，不假设ChatGPT专用工具存在|

## 仅参考或跳过

- [docxtpl](https://github.com/elapouya/python-docx-template)：LGPL-2.1，不是MIT；未安装。XML定位＋python-docx已有动态表/跨run，未引入docxcompose。
- [Docling](https://github.com/docling-project/docling)：代码MIT，模型许可另计；现有PDF全部有文本，未安装及下载OCR模型。
- [promptfoo](https://github.com/promptfoo/promptfoo)：MIT；沿用pytest＋固定JSONL、独立断言和失败记录，未安装平台或运行@latest。
- [RAGFlow](https://github.com/infiniflow/ragflow)：Apache-2.0；仅借鉴切片预览/来源定位交互，未部署搜索引擎、存储和Agent平台。
- [Microsoft playwright-cli](https://github.com/microsoft/playwright-cli)：Apache-2.0，候选审查SHA `655530f6d0dc71a0d6bf46ae165877d3c7311099`；已有稳定Playwright，未引入alpha或全局CLI。
- 不安装Superpowers/BMAD/GSD、Docker Engine、生成模型训练环境、NVIDIA驱动或CUDA。不执行上游安装钩子、远程脚本管道或发布命令。

## 验收状态字段

OPEN_SOURCE_REUSE表示组件已实际接入；SKILLS_REUSED/INSTALLED_OR_UPDATED记录上述集合；SKILLS_NATIVE_DISCOVERY待重载验证；SKILLS_USED_BY_FILE指向AGENTS.md及本文件；OPTIONAL_TOOLS_SKIPPED如上。这些状态不能替代RAG、模型、导出和E2E通过。最终系统状态统一见 `06_评测/verification.json`。


## 2026-09-16增量
继续复用原依赖与Noto字体，无新增Python/Node依赖。GLM-5.3-Flash为当前应用默认但无凭据实测，DeepSeek条目仅保留历史来源。模型缓存不打包，固定下载清单与外置复用路径支持交接。


本轮字体：项目assets/fonts内Noto Sans SC TrueType来自notofonts/noto-cjk，SIL OFL 1.1，固定400/700字重实例。来源、原文件哈希、适配说明及许可随包；导出临时Fontconfig仅加载本项目字体，不修改系统。用于修复CJK TTC经LibreOffice Type1子集导出的缩放漏绘。
