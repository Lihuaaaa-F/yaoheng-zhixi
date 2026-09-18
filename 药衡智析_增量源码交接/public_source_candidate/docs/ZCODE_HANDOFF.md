# GLM-5.3 接续入口

以 `current_run.json` 为唯一当前验收索引，条款矩阵见 `implementation_status.md`。起始协作提交 `acc469312c8366e4b0438e702a5f435779e7a125`，工作分支 `codex/core-industry-20260917`。最终受测代码提交、交付文档提交、测试计数与七场景分维度结论见当前索引及该分支HEAD；文档提交不冒称新模型运行。真人0–5归因、可读性与版式仍PENDING。

应用代码与真实模型生成固定于 `47c58069f1bc449d6bda18815f5276d44e72acdb`（`delivery_20260918_47c5806`）。恢复授权资源后的最终受测交付为 `6ff894fd389854ed11fd64cdea6bdfc2a7031cef`，运行 `release_20260918_6ff894f`。本地256项回归、无私有资源/无密钥干净归档190项、真实浏览器8组通过；正式verify退出0，自动维度PASS。七场景均为本轮新DeepSeek调用（非旧GLM记录或缓存），合计10次模型请求，模型身份核验和解释合同7/7通过；Word/PDF与模拟送达7/7通过。随后真实浏览器流程另3次模型请求，账本106→116→119，不能混作七场景推理次数。失败修复历史保留，不追认旧运行。

最终38页PDF已逐页实际看图，字体嵌入/残留插槽/数值与解释绑定另作机器检查。存在一处S2第3页复合单位在斜线后断行：DOCX已带不换行控制，当前LibreOffice仍换行，数字未改；部分来源末页留白偏多。两项明确作为非阻断版式遗留，不写成版式全完成。真人0–5归因、可读性与正式版式均PENDING，因此 `competition_ready=false`。详细回执均从current_run.json进入。

## 实际完成

安全取得协作main后保存旧项目和上游私有快照，以新clone替换原工作位置；未导回旧源码、dist或队列。保留模型身份/usage、summary-only阻断、ReviewStore、人审API、已有安全合并成果。本轮先按初始授权移除私料跟踪，随后用户明确要求保留原有赛题数据并公开提交所有项目内容；现恢复原题数据、知识、模板与本轮静态交付，三个独立合成包继续用于框架验证。历史GLM四场景v3模型参与PASS与视觉NEEDS_FIX仍在工程外历史归档，不替代本轮。

核心采用Pydantic合同、显式策略注册、不可变AnalysisContext和原模块化单体；没有替换Python/FastAPI/React/ECharts/DuckDB/SQLite/Chroma/LlamaIndex。新增行业不复制后台。制药原合同仍严格；机械工单/件/机时与化工批次/kg/能耗、四要素为框架迁移证明，非完成行业落地。见 `adr/0004-industry-packs.md`、`industry/development.md`。

已修复验证指纹/路径/退出码、有限数、适用候选检索、缺证合同、告警覆盖、季度上下文、报告复用、审核哈希漂移、动作字段完整验证、严格通知协议和outbox阻塞。审查追加修复混合粒度双计、机时/能耗量纲与去重、比较口径绕过、企业知识确切入口以及数值验收假阳性。真实模型修复循环和逐页PDF发现的问题及结果在当前索引列示；旧失败记录保留。缓存复用与新生成分别记录，不能把离线重验或报告重新编译当新模型调用。实调发现的具体成本文档名称误拒通过受限同义词合同修复；模型把确定性断言混入缺证正文时仍须拒绝。历史失败不追认成成功。

## 可复现命令

从 `药衡智析_增量源码交接/public_source_candidate` 执行：

```bash
bash 05_原型/scripts/bootstrap.sh
bash 05_原型/scripts/start.sh
TMPDIR=/tmp PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=05_原型/backend \
  05_原型/.venv/bin/python -m pytest -q 05_原型/tests
05_原型/.venv/bin/python 05_原型/scripts/check_environment.py --strict
05_原型/.venv/bin/python 05_原型/scripts/run_acceptance.py \
  --run-id YOUR_UNIQUE_RUN --output-dir 06_评测/YOUR_UNIQUE_RUN
bash 05_原型/scripts/verify.sh --manifest 06_评测/YOUR_UNIQUE_RUN/manifest.json
```

公开运行默认三合成场景。原题四场景列表通过 `--private-scenarios competition_configuration/scenarios.json` 传入，包含 `id/context_id/product/month/analysis_type`；按README启用比赛企业配置。runner向本机模拟器执行测试确认，责任人明确“合成验收责任人”，不是真人整改签收。浏览器另运行 `05_原型/frontend/e2e-context.mjs` 和 `e2e-live.mjs`；设置已有Chrome的 `PHARMA_CHROME_PATH`、`TMPDIR=/tmp` 和独立 `PHARMA_E2E_OUT`，完成后将真实新receipt绑定同run/代码commit。模型/浏览器未跑不能写PASS。

环境复用：WSL Python3.12项目venv、现有Node依赖及只读外部bge-small-zh-v1.5；核对锁指纹、FTS5、字体与两模型文件哈希，不覆写外部缓存、不下载大型模型。前端17个构建输入统一指纹，本次实际重建。运行依赖无新增；演示PPT可选 `requirements-docs.lock`（python-pptx 1.0.2/MIT、XlsxWriter 3.2.9/BSD-2-Clause），只装项目环境。

## 凭据、私有恢复与状态

本机按用户指定的受控DeepSeek密钥文件配置 `PHARMA_MODEL_KEY_FILE`、官方 `PHARMA_MODEL_BASE_URL`、`PHARMA_MODEL=deepseek-flash`；其他开发者使用其明确指定的应用API。仓库默认保留glm-5.3-flash适配。本机实调属于DeepSeek，不追认为GLM重跑；Coding Plan凭据不进入应用。用户已明确允许必要赛题资料发送给模型厂商，并在2026-09-18进一步授权保留原赛题数据及本轮交付公开提交；凭据、环境、运行数据库和恢复备份仍不发布。

工程外恢复点包含旧树、只读上游私有快照、逐文件校验及本机环境恢复记录。以 `PHARMA_DATA_PACKAGE` 指向外部原模拟数据目录，仅恢复原件白名单和环境配置；不复制旧源码、dist、数据库或队列。旧待发任务和审核记录隔离保留，若需迁移须逐任务核对状态/幂等标识后另建迁移记录，不重发。已合并clone无需prepare。`privacy-removals.json`记录本轮早期删除历史；最新恢复路径与原件哈希见 `competition-assets.json`，发布授权见 `publication-authorization.md`。本轮未改可见性、共享历史或强推。

## 文件所有权和下一步验收

下表代码路径相对 `05_原型`，文档路径相对应用根。

| 所有者/角色 | 主要文件 | 边界 |
|---|---|---|
| 核心集成 | `backend/pharma/api.py, jobs.py, actions.py, worker.py, reviews.py, reports.py, reference_report.py` 与 `scripts/` | 保持快照、审核、任务幂等合同；公共接口不足先最小反例 |
| 数据核心 | `industry.py, ingestion.py, metrics.py` 与公共合同测试 | Decimal、独立产量、维度/政策可比性、版本；不得绕过合同 |
| 检索生成 | `knowledge.py, narrative.py, context_services.py, industry_rules.py` | 适用证据、类型化解释、模型身份/预算；不得放松验证凑PASS |
| 行业研发GLM-5.3 | `industry_packs/<行业>/`、外部企业配置、独立测试及 `docs/industry/` | 默认只改包与企业配置；不复制backend |
| 前端 | `frontend/src/`、e2e脚本 | 切换取消旧请求、动态单位、真实能力、构建匹配 |
| 真人评审 | 审核API录入 | 真实署名0–5归因分/可读性/版式；所有AI不能代填 |

GLM-5.3先处理当前manifest的版式遗留并组织真人评审，固定未见验证问题检验模型合同稳定性，保留严格证据合同和有界修复；不得只改Prompt或扩词表凑PASS。随后做机械/零部件一个真实受控闭环：研究工单/报工/设备日志授权、设备费分配与返工报废政策，冻结字段、证据门槛和独立golden；跑导入→勾稽→机时指标→适用检索→解释→Word/PDF→确认→模拟送达。记录新增文件、核心是否修改、实际开发/运行耗时、未见问题召回与专业评价，再扩汽配。化工下一步核对配方/密度/批次净产出和电表计量；电子在前一行业稳定后研究BOM版本、替代料、良率与返修。详细台账在 `industry/research-ledger.md`。

每包必须有单位/币种/粒度/政策/WIP拒错、合法环比/同比/预算、同ID双企业检索/任务隔离、A→B→A、配置/Prompt变化缓存失效、失败导入保旧快照、模型/PDF/RPA故障与恢复负例。新增包若核心不足，给最小反例和兼容方案再改公共接口；不能宣称零改动通用性。

热力图和任务汇总已实现，真人责任确认由本人录入；图谱、运行多模型协作、自主决策和预测已于2026-09-18由GLM-5.3实现并实测（见下节"2026-09-18加分项与质量轮"）。无真实ERP/真实微信/WIP联副产品成本引擎，不宣称所有制造业覆盖。原题缺的历史异常、实价实耗与二厂明细如实标缺。

37.68秒无旁白合成操作视频和8页PPTX稿由公开脚本生成；完整二进制已在 `07_交付/release_20260918/demo/` 随授权静态交付发布（含SHA清单），不存在"仅留本地"的未发布副本。PDF阅读伴本轮可检查；最终讲解版视频与PPT实渲染见当轮交付目录回执。GLM-5.3负责重要非视觉工作，Flash仅按需视觉检查；Flash回执不等于真人评分。

私有制药企业主数据通过 `PHARMA_PRIVATE_MASTERDATA_FILE` 指向受控JSON（仅产品规格/工厂白名单），词典通过 `PHARMA_PRIVATE_TERMINOLOGY_FILE` 指向受控JSON。两者不是包内公共知识或自动推断结果；修改后对应快照/索引版本失效，保持原制药严格校验。没有这两份原企业配置时，只跑独立合成包，不伪造原场景。具体JSON格式及测试以加载器和对应公开合成负例为准。

## 交付与历史边界

同仓工作分支只普通push，不强推。起点acc4693与删除私有资产提交480cf48保留共享祖先；本地开发中间提交曾含待清理素材，未发送远端，已整理为e53ec77及后续公开代码提交。本机审计ref不属于交付分支，不得使用 `git push --all`。旧共享历史保持原样；当前赛题资产由用户最新明确授权纳入交付，未来真实企业资料仍须独立授权。

公开源码归档无需.git可启动并生成合成报告；其回执声明source revision且commit为null。正式带Git交付的verify仍核对真实commit与run_id，二者不能互相冒充。旧任务/审核库隔离，不迁移或重复发送；本轮验收任务只在本机题包模拟器，通知和整改确认状态分开。

当前完整静态交付在 `07_交付/release_20260918`：原受测运行七份DOCX/PDF、逐页图、稳定UI截图及演示视频/PPT草稿，来源与文件SHA在该目录清单。资源发布不把历史模型回执改成本轮，也不把文件存在或模拟送达算成人工通过。

完整交付提交复验：本地256项（19.37秒），含授权题包的干净归档190项（17.42秒）；78资源哈希匹配，仓内配置可直接导入原题并验证季度独立汇总。七场景重编译全部通过且复用47c的七份解释，模型新增请求0（账本119→119）。38页重新渲染，35页与先前实看PNG字节一致，三个合成首图发生像素变化并重新实看；原题页及已知版式遗留不变。静态交付仍保留47c已评读原文件及其准确来源，未重命名成新实调。


## 2026-09-18 加分项与质量轮（GLM-5.3，接续 ca294c4）

唯一当前索引仍为 `current_run.json`（现指向 `release_20260918_26efd3a_air2`，verify=PASS）。本轮由 GLM-5.3 在队友公开分支基础上完成：

- **四个赛题加分项全部实现并实测**：知识图谱（graph.py，题包抽取3产品/11药材/7工序/27边，检索词增强+前端力导图）、多模型路由（ModelGateway.for_route：narrative=glm-5.3-flash / decision=glm-4.5-air 双模型实测，账本按operation分开）、Agent自主决策（decision.py 确定性策略+小模型说明+SQLite台账+/api/agent/decision）、成本预测（forecasting.py Holt+80%区间，趋势图叠加）。新增26项测试，全量215过。
- **Prompt v18**：insufficient_evidence 写作语法与校验器逐字对齐（v16 3/7、v17 1/7 的失败历史保留在 current_run prior_runs）；v18b 新鲜 GLM 调用七场景模型合同 7/7、RPA/检索/文件 7/7、身份 VERIFIED；26efd3a 为缓存复用运行（模型新增0），绑定当前提交并 verify PASS。
- **工程修复**：bootstrap 无环境变量路径不再崩溃（原题摄取仅在显式启用比赛配置时执行）；test_source_revision 在 Windows 无符号链接特权时降级跳过该项断言；.gitignore 白名单目录内 __pycache__ 再忽略；删除死代码（models()、3个孤儿脚本、90_工具重复件）与三处重复逻辑；核心模块中文注释。
- **文档与交付**：双语双README、docs/architecture.md（架构图/RAG流程/路由/闭环 mermaid）、prompt_design.md、template_parsing.md、evaluation_report.md（赛题评测报告四指标）；07_交付/demo_20260918：讲解字幕版演示视频（2分52秒）+10页PPTX（LibreOffice 实渲染验证）。
- **环境事实**：Windows 11 Git Bash 原生全链路（Python3.12 venv/Node24/LibreOffice26.8/Chrome+Playwright ffmpeg）；本机 GLM 应用密钥经 PHARMA_MODEL_KEY_FILE；预算经 PHARMA_MODEL_MAX_CALLS 环境变量调整（v18 轮曾因累计账本触顶回落规则模式，属预算机制而非缺陷）。
- **仍 PENDING**：真人0–5归因/可读性/版式评审；S2第3页复合单位斜线断行与来源页留白两项非阻断版式遗留；真实行业数据与未见检索评估。

### 2026-09-18 深夜补充：glm-5.3-flash 配额耗尽与最终绑定

- 正式重绑链中发现 glm-5.3-flash 触发持续 429；探测确认错误码 1113（资源包余额耗尽，glm-5.3 系列同日不可用，仅 glm-4.5-air 有余量）。当日在该模型上的新鲜生成：v16 3/7 → v17 1/7 → v18 **7/7（bonus_20260918_glm_v18b，全维度PASS）**——提示词与代码路径的 7/7 证据已在档。
- 工程加固：ModelGateway 对 429/5xx 增加有界退避重试（20s/40s，同一逻辑调用共用账本行）——这属可靠性修复而非验收手段。
- 最终绑定 `release_20260918_26efd3a_air2`（提交 26efd3a，narrative=glm-4.5-air 运行时切换）：环境/回归/场景/检索/RPA/浏览器 6 维度全 PASS；model_live 6/7（Q2 季度在 air 上 mixed）。verify 退出 1 仅因该维度。
- 恢复全绿路径：GLM 账户充值后，按 evaluation_report §5 命令重跑 run_acceptance + verify（PHARMA_MODEL 默认 glm-5.3-flash 即可），预计恢复 7/7 与 verify=0。失败运行（c2e086f/5c00919/final）保留在 prior_runs 不追认。

### 2026-09-18 端点回退政策与正式全绿（用户授权）

用户明确授权暂定政策（无余额期间）："先消耗余额，资源包耗尽后端点换 Coding Plan"。据此实现并验证：

- **ModelGateway 端点自动回退**：主端点（paas/v4，扣余额/资源包）遇错误码 1113 时，同一次调用自动切换 `PHARMA_MODEL_CODING_BASE_URL`（默认 `https://open.bigmodel.cn/api/coding/paas/v4`，OpenAI 兼容、JSON 模式与 reasoning_effort 均受支持、model 回显精确）。主端点充值后自动恢复优先。原"coding 端点禁令"由本授权覆盖移除（probe_glm 同步放行，.env.example 有政策说明）。
- 账本 `calls` 表新增 `endpoint` 列（migration 兼容旧库），回执 identity 与 model-response 落盘携带实际端点；新增 5 项回退测试（切端点/无回退立即失败/非1113限流留主端点退避/非重试错误不切/主端点成功不触碰 coding）。
- **正式运行 `release_20260918_5974275`（提交 5974275）**：七场景模型合同 7/7（含 Q2，全部 mode=llm、身份 VERIFIED）；环境/回归/场景/检索/RPA/浏览器七维度全 PASS，verify 退出 0。账本端点分布：narrative→coding 回退 13 次成功；decision(glm-4.5-air)→主端点 4 次成功（air 免费额度仍有余，按"先消耗余额"政策走主端点）。
- 26efd3a_air2（air 主模型 6/7）与 v18b（flash 主端点余额期 7/7）保留为历史运行；当前索引指向 5974275。
