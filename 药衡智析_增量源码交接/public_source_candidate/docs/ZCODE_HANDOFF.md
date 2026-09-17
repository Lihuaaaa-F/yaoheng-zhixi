# GLM-5.3 接续入口

以 `current_run.json` 为唯一当前验收索引，条款矩阵见 `implementation_status.md`。起始协作提交 `acc469312c8366e4b0438e702a5f435779e7a125`，工作分支 `codex/core-industry-20260917`。最终受测代码提交、交付文档提交、测试计数与七场景分维度结论见当前索引及该分支HEAD；文档提交不冒称新模型运行。真人0–5归因、可读性与版式仍PENDING。

本轮最终受测代码为 `47c58069f1bc449d6bda18815f5276d44e72acdb`，运行 `delivery_20260918_47c5806`。本地256项回归、无私有资源/无密钥干净归档190项、真实浏览器8组通过；正式verify退出0，自动维度PASS。七场景均为本轮新DeepSeek调用（非旧GLM记录或缓存），合计10次模型请求，模型身份核验和解释合同7/7通过；Word/PDF与模拟送达7/7通过。随后真实浏览器流程另3次模型请求，账本106→116→119，不能混作七场景推理次数。失败修复历史保留，不追认旧运行。

最终38页PDF已逐页实际看图，字体嵌入/残留插槽/数值与解释绑定另作机器检查。存在一处S2第3页复合单位在斜线后断行：DOCX已带不换行控制，当前LibreOffice仍换行，数字未改；部分来源末页留白偏多。两项明确作为非阻断版式遗留，不写成版式全完成。真人0–5归因、可读性与正式版式均PENDING，因此 `competition_ready=false`。详细回执均从current_run.json进入。

## 实际完成

安全取得协作main后保存旧项目和上游私有快照，以新clone替换原工作位置；未导回旧源码、dist或队列。保留模型身份/usage、summary-only阻断、ReviewStore、人审API、已有安全合并成果。当前树删除私有原件与派生报告的跟踪，以三个独立合成包支持公开启动。历史GLM四场景v3模型参与PASS与视觉NEEDS_FIX仍在工程外历史归档，不替代本轮。

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

公开运行默认三合成场景。原题四场景列表通过 `--private-scenarios /external/private-scenarios.json` 受控传入，包含 `id/context_id/product/month/analysis_type`，不发布该文件。runner向本机模拟器执行测试确认，责任人明确“合成验收责任人”，不是真人整改签收。浏览器另运行 `05_原型/frontend/e2e-context.mjs` 和 `e2e-live.mjs`；设置已有Chrome的 `PHARMA_CHROME_PATH`、`TMPDIR=/tmp` 和独立 `PHARMA_E2E_OUT`，完成后将真实新receipt绑定同run/代码commit。模型/浏览器未跑不能写PASS。

环境复用：WSL Python3.12项目venv、现有Node依赖及只读外部bge-small-zh-v1.5；核对锁指纹、FTS5、字体与两模型文件哈希，不覆写外部缓存、不下载大型模型。前端17个构建输入统一指纹，本次实际重建。运行依赖无新增；演示PPT可选 `requirements-docs.lock`（python-pptx 1.0.2/MIT、XlsxWriter 3.2.9/BSD-2-Clause），只装项目环境。

## 凭据、私有恢复与状态

本机按用户指定的受控DeepSeek密钥文件配置 `PHARMA_MODEL_KEY_FILE`、官方 `PHARMA_MODEL_BASE_URL`、`PHARMA_MODEL=deepseek-flash`；其他开发者使用其明确指定的应用API。仓库默认保留glm-5.3-flash适配。本机实调属于DeepSeek，不追认为GLM重跑；Coding Plan凭据不进入应用。用户已明确允许必要赛题资料发送给模型厂商；原件、知识、派生完整报告仍不得公开提交。

工程外恢复点包含旧树、只读上游私有快照、逐文件校验及本机环境恢复记录。以 `PHARMA_DATA_PACKAGE` 指向外部原模拟数据目录，仅恢复原件白名单和环境配置；不复制旧源码、dist、数据库或队列。旧待发任务和审核记录隔离保留，若需迁移须逐任务核对状态/幂等标识后另建迁移记录，不重发。已合并clone无需prepare。精确移除路径见 `privacy-removals.json`；旧Git历史/已下载副本需仓库负责人另行处理，本轮未改可见性、历史或强推。

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

热力图和任务汇总已实现，真人责任确认由本人录入；图谱、运行多模型协作、自主决策和预测未实现。无真实ERP/真实微信/WIP联副产品成本引擎，不宣称所有制造业覆盖。原题缺的历史异常、实价实耗与二厂明细如实标缺。

37.68秒无旁白合成操作视频和8页PPTX稿由公开脚本生成，完整二进制留本地 `07_交付/demo/`；不与原题完整报告一起公开。PDF阅读伴本轮可检查，PowerPoint实渲染、最终讲解剪辑与真实评审尚待完成。GLM-5.3负责重要非视觉工作，Flash仅按需视觉检查；Flash回执不等于真人评分。

私有制药企业主数据通过 `PHARMA_PRIVATE_MASTERDATA_FILE` 指向受控JSON（仅产品规格/工厂白名单），词典通过 `PHARMA_PRIVATE_TERMINOLOGY_FILE` 指向受控JSON。两者不是包内公共知识或自动推断结果；修改后对应快照/索引版本失效，保持原制药严格校验。没有这两份原企业配置时，只跑独立合成包，不伪造原场景。具体JSON格式及测试以加载器和对应公开合成负例为准。

## 交付与历史边界

同仓工作分支只普通push，不强推。起点acc4693与删除私有资产提交480cf48保留共享祖先；本地开发中间提交曾含待清理素材，未发送远端，已整理为e53ec77及后续公开代码提交。本机审计ref不属于交付分支，不得使用 `git push --all`。这不清除原共享历史中的私有资料；负责人后续处理范围见privacy-removals.json。

公开源码归档无需.git可启动并生成合成报告；其回执声明source revision且commit为null。正式带Git交付的verify仍核对真实commit与run_id，二者不能互相冒充。旧任务/审核库隔离，不迁移或重复发送；本轮验收任务只在本机题包模拟器，通知和整改确认状态分开。
