# ZCode CLI 接续交接：药析证链／药衡智析

## 当前事实与入口

这是一项对现有初版的增量修复。源码仍在 `05_原型`，没有另起项目。原项目没有 Git；恢复基线保存在原工作机 `/home/hujunjie/pharma_recovery_baselines/20260916T022230/`，含完整归档和逐文件 SHA256。原始题包、原模板、历史 DeepSeek 成功/失败证据没有改写。

用户已澄清：没有另外提供的 `02_audit` 交接包，本轮依据当前 WSL 项目与历史证据执行；交接包是本轮输出。开发工具 ZCode CLI 位于队员电脑，本工作机运行的是 Codex，不能宣称已在 ZCode 中执行，也不能杜撰其命令参数。

## 在队员电脑先做什么

1. 用**已安装 ZCode 的实际入口**打开交接包恢复后的项目目录，先读 `AGENTS.md`、本文件、`docs/INCREMENTAL_AUDIT.md` 和本轮 `verification.json`。不要重新创建工程。
2. 如果只解压公开源码候选包，它不含题包与报告；请使用队内总交接包根目录的 `prepare_team_workspace.py` 合并内部目录到工作副本。不能把公开候选包当成独立全数据系统。
3. 运行 `05_原型/scripts/check_environment.py`。依赖只装到本项目 venv；已有兼容解释器可通过 `PHARMA_PYTHON` 显式复用。执行 `bash 05_原型/scripts/bootstrap.sh`、`bash 05_原型/scripts/start.sh`。默认 `127.0.0.1:8765`，原题包 mock 为8090；端口冲突可用 `.env` 的项目专用端口配置。不得终止其他项目服务。
4. 检索模型缓存没有打包。`fetch_embedding.py` 仅下载缺失的固定版本模型/tokenizer，并验证清单SHA；网络不可用时，设置 `PHARMA_EMBEDDING_DIR` 指向已授权、哈希匹配的现有资产。没有语义资产时混合检索不能标通过。
5. 本机原Noto CJK字体经LibreOffice导出为Type1子集后出现缩放相关漏绘，已补项目内Noto Sans SC TrueType Regular/Bold及SIL OFL许可证（05_原型/assets/fonts）。Linux导出以临时Fontconfig配置加载，不改系统字体；Windows Word打开时安装包内同字体。仍须在队员电脑实际检查LibreOffice/浏览器/Word渲染，不能批量转码。

## 首要阻塞：GLM应用API真实验证

**当前真实结果为 BLOCKED / MODEL_KEY_NOT_SET**。已配置默认 `glm-5.3-flash`，没有用 `glm-5.3`、旧DeepSeek或规则输出来冒充GLM成功。

- 开发Agent的Coding Plan与应用运行时API是两件事；无限开发token额度不证明应用调用免费。
- 中国站通用候选：`https://open.bigmodel.cn/api/paas/v4`；国际站通用候选：`https://api.z.ai/api/paas/v4`。先按账户和当日官方文档核验，不用包含 `/coding/` 的端点。
- 官方依据：[Z.AI Chat Completion](https://docs.z.ai/api-reference/llm/chat-completion)。当日本次读取的文档注明GLM-5.3-FLASH仅支持启用思考，`reasoning_effort` 为 low/high/max。网关未照搬DeepSeek的disabled，默认low，输出预算8192。官方通用模型列表未完整列出此精确型号，账号可用性必须实调确认。
- 密钥用受控文件，`.env`只填写 `PHARMA_MODEL_KEY_FILE` 路径；亦支持环境GLM_API_KEY/ZHIPU_API_KEY。禁止粘贴到聊天、截图、日志、代码或交接包。
- 运行 `05_原型/.venv/bin/python 05_原型/scripts/probe_glm.py --output 06_评测/新运行目录/glm_probe.json`。探针仅发送极小连接测试内容，分别检查文本、JSON、工具调用、SSE流式和返回的精确模型ID。不得将HTTP200当成结构与身份通过。
- 真实限流/超时目前未观测；本地HTTP夹具覆盖失败降级。核验账户配额、应用费用、429/Retry-After与超时表现，避免用压力攻击制造429。没有验证就保持待检查。
- 探针通过后，重新生成 S1银黄5月、S2板蓝根5月专题、S3六味3月、Q2银黄4—6月季度。使用 `generate_scenarios.py --output 06_评测/新运行目录/scenario_reports.json`，不要覆写本次失败证据。检查章节级model参与/repair记录和实际usage。
- 报告默认基础版是有价值的确定性分析，但模型参与未通过；禁止默退DeepSeek、放开模型自算或删除数字校验。

## 真人必须接续的审核

四场景 DOCX/PDF 已按本轮记录逐页渲染与Agent检查；这**不等于真人验收**。对每一场景填写：

- 归因合理性0—5分、审核人、日期、评语，明确事实/假设/建议。
- 内容可读性、全部页版式（目录页码、标题连排、表格续页、图例单位、字体缺字和裁切）。
- 章节实质完整和证据支持程度；尤其二厂原料明细仍缺，不能推算填补。
- 实際业务负责人分配任务和日期；发送必须确认当前完整载荷，模拟通知不等于真实整改完成。

所有强制维度必须通过才可将报告总体验收改PASS。当前文件打开、计算、业务内容、证据、阅读、视觉、任务和模型分别记录；不要恢复旧“DOCX/PDF PASS即合格”的表述。

## 检索后续探索边界

v4固定规则在历史已见集混合Recall@5为0.928571、BM25为1.0。该集和原holdout已经被检查，不能再称新保留集或据其反复调参后宣称泛化。建立**新未见问题集**并先冻结：产品串扰、跨期事件、文档版本冲突、无证据问题。比较语义/BM25/混合分项；当前仍不能宣称混合优于BM25。每次解析版本变更重新建索引，禁止沿用旧版本结果伪装当前质量。

## 可直接交给ZCode的探索prompt

> 在现有药衡智析项目上接续，不另起工程。先核验本交接包的哈希、运行记录和上述阻塞。复用兼容环境，按账号官方文档实测应用模型glm-5.3-flash，严禁Coding端点、旧模型冒名和秘密输出。保留所有历史证据，分章节校验与局部降级。只针对实际失败修复，重新跑受影响测试和四场景报告，全部页渲染并等待真人评分。新增未见检索负例先冻结再评测，不用已见holdout调参宣称泛化。任务用户确认后才发送；任何HTTP成功不代替通知证据或整改完成。原位更新方案HTML/artifact与真实分项状态，最后重新打包、解压启动验收，报告未通过项必须保留。
