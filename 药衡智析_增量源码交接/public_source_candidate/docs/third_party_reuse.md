# 第三方组件与技能锁定

更新：2026-09-18。仅记录实际采用、明确参考和跳过的内容；安装/阅读不等于系统验收。应用依赖精确版本见 `05_原型/requirements.lock` 与 `05_原型/frontend/package-lock.json`；本轮环境结果见 `docs/current_run.json`。

## 已采用组件

|来源|实际版本/SHA|许可证与限制|采用位置/验证依据|
|---|---|---|---|
|[React](https://github.com/facebook/react)|react/react-dom 19.1.1|MIT|frontend；实际编译/浏览器|
|[Apache ECharts](https://github.com/apache/echarts)|5.6.0|Apache-2.0|Chart.tsx，本地打包趋势/结构/瀑布|
|[Vite](https://github.com/vitejs/vite) / [TypeScript](https://github.com/microsoft/TypeScript)|6.4.1 / 5.9.2|MIT / Apache-2.0|项目开发依赖，npm锁|
|[Playwright](https://github.com/microsoft/playwright)|1.58.2|Apache-2.0|项目开发依赖；复用本机已安装Chromium；无全局升级|
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

未把任何参考仓整仓拼装成产品，未更改或重新分发第三方库源码。

## CPU embedding来源及权利边界

当前运行的是 [Xenova/bge-large-zh-v1.5固定转换提交](https://huggingface.co/Xenova/bge-large-zh-v1.5/tree/a48549b3259a6165364f226599cd91f39923d5d5)，SHA `a48549b3259a6165364f226599cd91f39923d5d5`（2026-09-21 由 bge-small-zh-v1.5 升级，1024 维）。两文件经镜像下载并按 `docs/embedding_manifest.json` 哈希核验后落位本地运行时，不进入公开源码包；此前 bge-small（SHA `75c43b06…`）的身份记录保留在该 manifest 的 previous_model 字段。

基础 [BAAI/bge-large-zh-v1.5模型卡](https://huggingface.co/BAAI/bge-large-zh-v1.5) 声明MIT；未在Xenova转换权重处确认独立许可证文件。因此记录为“基础模型MIT，转换权重单独许可未明确”，不能将基础模型许可自动等同转换分发已获完整确认。当前只作已授权本地CPU演示，模型缓存不进入公开源码包；正式分发前应保留出处并核对对应权利说明。

## 本轮工程Skills

复用已安装的diagnosing-bugs、codebase-design、React/前端测试与code-review指导；没有本轮安装共享技能。规范与规格两轴独立审查发现的真实问题有定向反例及复核，见`validation/audit-summary.json`。早期技能安装/旧报告工具记录属于历史，不作为本轮执行证明。

## 仅参考或跳过

- [docxtpl](https://github.com/elapouya/python-docx-template)：LGPL-2.1，不是MIT；未安装。XML定位＋python-docx已有动态表/跨run，未引入docxcompose。
- [Docling](https://github.com/docling-project/docling)：代码MIT，模型许可另计；现有PDF全部有文本，未安装及下载OCR模型。
- [promptfoo](https://github.com/promptfoo/promptfoo)：MIT；沿用pytest＋固定JSONL、独立断言和失败记录，未安装平台或运行@latest。
- [RAGFlow](https://github.com/infiniflow/ragflow)：Apache-2.0；仅借鉴切片预览/来源定位交互，未部署搜索引擎、存储和Agent平台。
- [Microsoft playwright-cli](https://github.com/microsoft/playwright-cli)：Apache-2.0，候选审查SHA `655530f6d0dc71a0d6bf46ae165877d3c7311099`；已有稳定Playwright，未引入alpha或全局CLI。
- 不安装Superpowers/BMAD/GSD、Docker Engine、生成模型训练环境、NVIDIA驱动或CUDA。不执行上游安装钩子、远程脚本管道或发布命令。

## 当前状态

唯一验收入口为`current_run.json`。协作默认GLM-5.3-Flash，历史GLM成功存档保留工程外；本轮本机按用户指定凭据使用DeepSeek，不能混记为本机GLM重跑。

本轮字体：项目assets/fonts内Noto Sans SC TrueType来自notofonts/noto-cjk，SIL OFL 1.1，固定400/700字重实例。来源、原文件哈希、适配说明及许可随包；导出临时Fontconfig仅加载本项目字体，不修改系统。用于修复CJK TTC经LibreOffice Type1子集导出的缩放漏绘。

本轮新增可选演示文档依赖：python-pptx==1.0.2（MIT）、XlsxWriter==3.2.9（BSD-2-Clause，传递依赖），锁在requirements-docs.lock，仅项目venv用于PPTX生成。现有LibreOffice仅Writer，无Impress；PPTX结构重开验证与PDF阅读版已生成，不能把阅读版称PowerPoint实渲染。


## 工作台界面依赖（2026-09-23）

- [Ant Design](https://github.com/ant-design/ant-design)：`antd 6.6.5`，MIT；复用表单、选择器、抽屉、菜单、提示和主题令牌。
- [Ant Design Icons](https://github.com/ant-design/ant-design-icons)：`@ant-design/icons 6.3.4`，MIT；统一导航与操作图标。
- 本轮借鉴 Codex 风格的输入框布局，所有交互均为项目自身 React 实现，没有复制其源码、商标或产品素材。
- 验证环境的临时 Chromium 包未进入应用依赖、镜像或交付物。
