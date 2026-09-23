# 交付物规范符合性审查发现（spec-to-code compliance）

- 审查对象：worktree `D:/yaoheng-audit-wt-1f78b2f`（仓库 yaoheng-zhixi，HEAD `1f78b2f`，2026-09-23）
- 审查方式：只读文本/结构/元数据/一致性核对；grep 定位文档宣称并抽查代码对证。**审查者无视觉能力，未看过任何视频画面/PPT渲染/报告版式**，媒体类仅核文件存在性、回执元数据与文本化流程清单。
- 判定分级：满足 / 部分满足 / 不满足 / 未实现 / 待验证+静态确认 / 待人工视觉。
- 严重度：P0（阻断性）P1（高）P2（中）P3（低）INFO。

## 0. 一句话总结

六项交付物在"文件存在"层面全部齐备且文档-代码抽查大体一致，但**全部运行态证据（报告/评测数字/视频）绑定在 HEAD 之前 24–51 个提交的旧代码上**：交付目录 6 份报告哈希与验证 manifest 全部不匹配、S3 场景从未入回执、评测报告文档停在 0919、Prompt 文档停在 v18（代码已 v21）。"旧交付被当最新用"的风险在本次 HEAD 上是现实而非假设。

## 一、赛题必交交付物对照表

| # | 赛题要求 | 判定 | 证据与缺口 |
|---|---|---|---|
| ① | 系统完整代码（Dockerfile/requirements+一键启动+GitHub 公开仓库） | **满足（静态）** | `05_原型/requirements.txt`（fastapi/duckdb/chromadb/llama-index-core 等）、`deploy/Dockerfile`+`docker-compose.yml`（web/worker/rpa 三服务、健康检查、127.0.0.1:8765 端口映射、命名卷）、`scripts/bootstrap.sh/start.sh/stop.sh`、仓库根 `药衡智析启动器.bat`→`deploy/launcher.ps1`。GitHub 公开性：CI 回执含 `github.com/Lihuaaaa-F/yaoheng-zhixi/actions/runs/35436891332`（current_run.json），仓库可见性需人工在浏览器确认（待人工）。**无根 LICENSE 文件**（见 §6） |
| ② | 技术方案文档六要素（架构图/RAG流程含切分·向量化·检索/Prompt/模板解析/API文档） | **满足（含 1 处版本滞后差异）** | 六要素均存在：`docs/architecture.md`（mermaid 架构图）、`docs/rag.md`+`retrieval_contracts.md`、`docs/prompt_design.md`、`docs/template_parsing.md`（含 mermaid 流程）、`docs/api_and_operations.md`。抽查一致性好（见 §3）；差异：prompt_design.md 自称 v18/校验器 v9，代码实际 `PROMPT_VERSION='v21-attribution-directions'`、`VALIDATOR_VERSION='claim-contract-v10-rounded-metric-binding'`（narrative.py:28-29）→ P2 文档滞后 3 个版本 |
| ③ | 评测报告（3 场景：结构完整度/归因 0-5 人工评分/RPA 触发成功率/三步法格式正确率；另 5.3.3 差异计算准确率误差≤1%） | **部分满足（P1）** | 详见 §2。3 场景=六味地黄胶囊/板蓝根颗粒/银黄口服液（均 2026-06，同月不同产品）；机器维度有旧运行存证，人工 0-5 全 PENDING，评测报告主文档本身陈旧 |
| ④ | 演示视频 ≤5 分钟（条件选择→报告→看板→对标→RPA 端到端） | **部分满足（存在+合规+流程覆盖按回执，版本旧+待人工视觉）** | `07_交付/demo_20260920/yaoheng_full_demo_20260920.mp4` 6.14MB，回执 duration_seconds=169.8（2分50秒，≤5min 合规），viewport 1366×768，flow 清单覆盖赛题五环节（①-㉒ 含完整对标三步与 RPA 送达）。绑定 `tested_code_commit=03a5a30`（早于 ded9267，更早于 HEAD 51 提交）；verification.json `media_freshness=PENDING`（"待修复后重录"）；录制方式为 Playwright 无头页面渲染+合成光标（回执如实记载）→ 画面实际效果待人工视觉 |
| ⑤ | 答辩 PPT（决赛） | **部分满足** | `07_交付/demo_20260918/药衡智析_演示与答辩稿.pptx`（10 页，41.6KB）+ `pptx_render/` 10 张 PNG 原生渲染；`delivery_20260919_final/deck/` 另有一份同名 PPTX+native_render_check.json。最后修改停在 26efd3a（0918 时代），其后从未刷新；demo_20260918/README.md 自认"缺三场景结果、基线对照和实际报告证据页"；`test_demo_deck_binding.py` 只测构建函数绑定逻辑，不保证 PPT 内数据与最新报告一致 → 数据来源一致性待人工视觉 |
| ⑥ | 成本预测模型（加分可选） | **满足存在性（INFO）** | `forecasting.py`（Holt 双参数、80% 区间）、`/api/forecast`（api.py 存在）、看板叠加；多份文档一致自认"实验性、增益未验收"——表述诚实 |

## 二、评测报告（要求③）五要素逐项核对

| 要素 | 现状 | 判定 |
|---|---|---|
| 3 个分析场景 | 产品×月份：六味地黄胶囊 2026-06、板蓝根颗粒 2026-06、银黄口服液 2026-06（delivery_20260921 三份 docx/pdf）。**但 current_run.json `required_scenarios` 仅 2 条**（S1 六味/S2 银黄），板蓝根（S3）由 ded9267 之后的提交（3815fa9…29377b6）补入交付目录，**无 job_id/哈希/回执登记**；manifest.json 只含 2 场景（grep 板蓝根=0 命中）。另有编号映射冲突：`competition_configuration/scenarios.json` 定义 S1=银黄 2026-05、S2=板蓝根 2026-05、S3=六味 2026-03、Q2=银黄 2026-06，与 current_run 的 "S1_六味…2026-06" 矛盾；delivery_20260919_final CSV 又是 S1 银黄/S2 板蓝根/S3 六味 | 部分满足（P1：S3 无证据链 + 编号三处互斥） |
| 报告结构完整度 | 机器验收（标题序列=模板章节+残余占位符+数值角色绑定），release_20260918_5974275 七场景 PASS 存档；delivery_20260921 各报告带 `_machine_audit.json` | 满足（机器维度，绑定 0918/0921 旧运行） |
| 归因合理性人工评分 0-5 | `delivery_20260919_final/human_review_pending.csv` 3 行全 PENDING 空表（系统不代填，设计正确）；verification.json `human_review=PENDING` | **不满足（待真人，评测报告唯一硬缺口，文档已诚实标注）** |
| RPA 触发成功率 | `validation/release_20260918_5974275/rpa.json`：7 场景（mechanical/chemical/pharma_synthetic/S1/S2/S3/Q2）SIMULATED_SENT 全 PASS——绑定 0918 提交 5974275；delivery_20260921 verification rpa_loop PASS（2 场景，ded9267）。注意全部为模拟送达，human_acknowledgement=NOT_ENTERED | 部分满足（数据来源=旧运行回执，非 HEAD 实测） |
| 三步法输出格式正确率 | evaluation_report.md 自述"6ff894f 历史 three_step 记录原题 3/3，跨运行证据，不能自动视为完整复跑"；验收文档（0920）称七场景机器 PASS（绑定 5974275）。**HEAD 代码/测试 grep "three_step" 0 命中**（backend+tests），格式核对逻辑在 reference_report 验收器内 | 部分满足（旧运行证据，HEAD 无专属测试锚点） |
| 差异计算准确率误差≤1%（5.3.3） | 双重证据：a) Decimal 精确算术+golden 独立手算对照（`tests/test_industry.py`，文件头注明 "golden arithmetic is written independently"）——但黄金值针对**公开合成行业包**，非赛题制药三场景；b) 独立审查报告（0921）审计员从源 CSV 独立重算单场景全对（-2.8745%、76.92/7.69/15.38%、跨厂 -1.20/-6.39 元等）。**未见针对赛题三场景的逐指标独立对拍表** | 部分满足（待人工对三场景抽算复验） |
| 评测报告文档本身 | `docs/evaluation_report.md` 仅 50 行，头部仍是 0919 更新（"最新自动运行存档为 release_20260918_5974275"），落后 current_run（delivery_20260921）两个 run、落后 HEAD 51 提交；最后一次修改停在 2f5264e（0919） | **部分满足→文档陈旧（P1）** |

## 三、技术方案文档六要素与实现对证（抽查）

| 要素 | 文档宣称 | 代码实证 | 判定 |
|---|---|---|---|
| 切分策略 | rag.md：PDF 按页、DOCX 按段落/表格、TXT 按行段；行业包补 JSON 合成知识 | knowledge.py 解析入口存在（RETRIEVER_VERSION='bm25-chroma-prefilter-rrf-v5-keyword-expansion'，knowledge.py:20） | 一致（静态） |
| 向量化方案 | rag.md/retrieval_contracts.md：CPU ONNX 向量（bge），先适用范围筛选 | embedding_manifest.json：Xenova/bge-large-zh-v1.5@a48549b，MIT 许可已记录 | 一致 |
| 检索策略 | BM25(FTS5)+向量 RRF 融合、适用候选预过滤、无全库 top100 截断、重排序不引外候选 | knowledge.py:68 RRF k=60；:422 BM25 LIMIT max(20,limit)；:437-441 混合权重 [0.75,0.25]（lexical_anchor）或 [0.5,0.5]，注释明示"fixed weights not fit on gold" | 一致（文档未写具体权重数值，无冲突） |
| Prompt 设计 | prompt_design.md：模型不拥有数字/任务程序创建/文档不可信证据/有界修复；自称 Prompt v18、校验器 v9 | narrative.py:28-29 实为 v21 / v10-rounded；v10 四舍五入唯一绑定在 README/current_run 宣称 | **不一致（P2：文档滞后 v18→v21、v9→v10）** |
| 模板解析 | template_parsing.md：{{占位符}}正则+书签锚点 YH_<hash>_<段号>+binding_semantics+水印仅工作副本 | 入口 `pharma/reports.normalize_template`（文档明示路径，与 reports.py 一致）；test_native_toc/test_report_captions 等测试存在 | 一致（静态） |
| API 接口文档 | api_and_operations.md 21 条路由表（industry/catalog、analyses、benchmarks、reports、jobs、artifacts、reviews、acceptance、kb/search、actions CRUD+confirm/acknowledge/refresh…） | api.py 逐一核对：GET /api/industry/catalog(:96)、POST /api/analyses(:105)、GET /api/benchmarks(:133)、POST /api/reports(:201)、PUT /api/actions/{id}、POST …/confirm、/acknowledge、/refresh 全部存在 | 一致（抽查 8/8 命中） |

其他文档-实现一致性：README 一键启动说明与 deploy 实测一致（compose 三服务+launcher.bat 跳板+bootstrap/start/stop）；`/api/*` 需 X-API-Token（api.py:18 middleware）与 api_and_operations.md 声明一致。

## 四、版本绑定矩阵（核心发现）

HEAD=`1f78b2f`。各交付证据绑定的代码版本：

| 交付物 | 绑定 commit | 距 HEAD | 问题 |
|---|---|---|---|
| current_run.json / verification.json / manifest.json（delivery_20260921） | ded9267 | **51 提交** | 回执未随代码更新 |
| delivery_20260921 六份 docx/pdf 实际字节 | 29377b6（最后重制） | 24 提交 | **与 manifest 哈希 6/6 全部 MISMATCH**（python sha256 实测）；早于 4c63335（Word 打开报损坏修复）、a5b06d3/09b2ba2（TOC/版式修复）、6b9a8b8/f086f9e（确定性归因引擎） |
| 演示视频 demo_20260920 | 03a5a30 | 早于 ded9267 | media_freshness=PENDING 自认待重录 |
| PPT | 26efd3a（0918 后未动） | ~60+ 提交 | 自认缺实证页 |
| evaluation_report.md | 2f5264e 内容（0919） | 大量 | 叙述停在 5974275 时代 |
| 数据全流程与归因方法评估_20260922.md | 0f936ff | 数提交 | 文档自标"main 0f936ff" |
| delivery_20260921/README.md | 自称"main@39c0e75" | — | 与同 run 的 current_run（ded9267）**自相矛盾**（39c0e75 vs ded9267） |

**P0 结论**：仓库至少出现 6 个互不相同的"当前版本"宣称（04011c2/39c0e75/ded9267/03a5a30/0f936ff/1f78b2f）。旧审计问题 #16（交付物版本漂移）在修复轮后**复发且加重**：交付报告被后续提交重制但 manifest/verification/current_run 未刷新，证据链断裂；S3 场景全程无回执。任何人以 current_run.json 校验当前交付目录将全部失败。

**P1 推论**：交付的三场景报告生成于归因引擎落地与 Word 兼容修复**之前**——交付物既不体现最新归因方法（与 docs/数据全流程_20260922 描述的新引擎不一致），也可能仍带 Word 打开兼容隐患（4c63335 修复的存在证明旧产物确有问题；需人工用 Word/WPS 打开交付 docx 复验）。

## 五、视频 / PPT 细节

- 视频：169.8s ≤ 300s 合规；回执 flow 22 步覆盖赛题五环节（条件选择→看板→±10%重点→对标三步完整顺序→报告生成下载→建议转任务→确认发送模拟 RPA→任务统计）；`benchmark_narrative_model_live=true`；`report_job_mode=llm（预热生成，录制时命中缓存）`——录制时报告为缓存命中而非现场生成（回执如实记载）。合成光标+字幕注释（非真人操作录像）。**待人工视觉**：画面是否真实完成各操作、字幕与操作是否同步。
- PPT：10 页存在+原生渲染 PNG 10 张（slide-01..10）；demo_20260918/README 自认"以文字提纲为主，缺三场景结果、基线对照和实际报告证据页；正式答辩应补充验证证据并由真人审阅"；另有历史更正记录"旧 README 的 2分52秒与四个 SHA 均不符合现存文件"（说明该目录曾发生文件替换而说明滞后——与本次 delivery_20260921 哈希断裂同模式）。**待人工视觉**。
- 媒体指向矛盾（P3）：current_run.json media 段指 `delivery_20260919_final/demo/yaoheng_demo_narrated.webm`（59.16s），而同文件 media_freshness 与根 README 指 demo_20260920（169.8s）——同一份索引内两个"当前视频"。

## 六、README / 启动 / 许可证 / 开源标注

- 一键启动：README（根+应用根）宣称与 deploy/ 实际一致（compose 三服务、launcher.bat→launcher.ps1、bootstrap/start/stop、127.0.0.1、PHARMA_MODEL_KEY_FILE 注入、赛题原件只读挂载）。静态一致。
- 源码与运行数据分离：`.runtime`/运行库不入库（privacy_boundary.md 明示）；交付静态产物单独目录。一致。
- 许可证：**仓库根无 LICENSE 文件**（find 仅命中 docs/repository/LICENSE_STATUS.md）；LICENSE_STATUS.md 明示"项目自有源码许可尚未统一确定，不擅自选择"。赛题 6.3（引用开源代码需标注来源与许可证）：third_party_reuse.md 逐组件标注版本+许可证（React MIT、ECharts Apache-2.0、FastAPI MIT、DuckDB MIT、LlamaIndex MIT、Chroma Apache-2.0、jieba MIT、python-docx MIT、**PyMuPDF AGPL-3.0**——已如实警示"不是 MIT，后续分发需单独处理适用许可"）。判定：第三方标注**满足**；自有代码许可证**未决（P2）**；PyMuPDF AGPL 对比赛分发的影响需团队确认（P2）。
- 竞赛数据边界：privacy_boundary.md 记录用户 0918 授权范围（赛题原件+派生静态交付可发布；密钥/.env/运行状态排除；未来真实企业数据需独立确认）；二厂合成明细（对标第三步用）全程标注"合成演示数据"并有 `PHARMA_SYNTHETIC_DETAIL_DIR=''` 停用开关与 test_synthetic_plant2_details.py；合成行业包（机械/化工）与赛题制药配置目录分离（competition_configuration/ vs industry_packs/）。**未见赛题数据被用于非赛题用途的迹象**；唯一注意点：对标"拆原因"的第三步输出混入合成明细（已标注），答辩时需向评委明示（INFO）。

## 七、旧审计"声称已修复"待复验清单（仅列出，复验由主审执行）

来源：docs/问题清单_全面审计_20260921.md 修复状态总览（git 25d44bc..c080cfc）+ docs/独立审查报告_20260921.md。

| 项 | 声称 | 本次静态核查 | 需主审复验 |
|---|---|---|---|
| #1 叙事合同 v10 双场景 narrative/model_participation PASS | ded9267 实测（verification.json 在案） | 证据真实存在；但 HEAD 已推进 51 提交且 PROMPT v21+确定性归因引擎落地 | **在 HEAD 重新实调一次三场景报告**，确认 v21 合同仍 PASS |
| #5 对标冷 14.7-18.6s | ded9267 实测 | current_run runtime_measurements 在案 | 新归因引擎后重测耗时 |
| #6 热力图缓存 0.29s | ded9267 实测 | 同上 | HEAD 重测 |
| #7 KB 11 源 180 chunks | 0921 补四份知识入库 | embedding_manifest（bge-large-zh-v1.5）存在 | HEAD 上重建索引核对源数/chunk 数 |
| #2 前端降级重试出口 | 已修 | **静态确认**：NarrativePanel.tsx:13、ReportGeneration.tsx:33-34 "重新生成（忽略缓存）" 存在 | 运行态点击验证 |
| #3 Compose 默认直连（净机构建） | 已修 | **静态确认**：docker-compose.yml 注释"默认不走代理" | 净机部署演练（README 自认"建议交付前实测一次"，仍未做） |
| #4 settings 安全（key_file 白名单/https 强制） | 已修+6 项回归 | test_settings_security.py 存在（未运行） | 跑测试+黑盒 |
| #11 报告成色四项（建议去重/亮点/附录/编制人） | 已修（RENDERER v4→后续 v5） | 代码存在 | 人工读 HEAD 新生成的报告 |
| #12 断行"误判修正" | 声称几何验证不成立 | **反证信号**：其后 4c63335（Word 打开报损坏根治）、c001cbb/3815fa9（真人评审版式多轮修复）说明版式问题真实存在过 | 交付 docx（29377b6 产物，早于 4c63335）用 Word/WPS 实际打开 |
| #16 交付物版本漂移 | 声称"current_run/回执/README 已刷新至 20260921" | **本次实证已复发**（§4 哈希 6/6 MISMATCH） | 主审以 verify_repository 思路重跑对拍（本次未执行 tools/verify_repository.py，避免副作用） |
| #17 三场景 0-5 评分 | 待真人 | CSV 仍全 PENDING | 真人 |
| #16 视频重录 | 待人工 | 仍为 03a5a30 版 | 真人 |
| #29 净机部署演练 | 待人工 | 未做 | 真人 |
| 复审新发现四项（App 重试不重置企业上下文/去重空核查对象/亮点跨厂归属//docs 与 openapi.json 鉴权） | ded9267 声称已修 | api.py:18 token middleware 静态可见 | 测试+黑盒 |
| 验收文档避重就轻（独立审查 #2/问题清单 #18） | — | 赛题要求逐条对照验收_20260920.md 仍宣称"✅✅ 全链路"且引 0918 回执，未见修订说明 | 主审判断是否需出勘误 |

## 八、判定统计与严重度汇总

判定统计（6 项必交+1 加分）：满足 3（①②⑥）· 部分满足 3（③④⑤）· 不满足 0（硬缺口=③的人工评分，归入部分满足内的待真人项）· 待人工视觉 3（视频画面/PPT 渲染/报告版式与 Word 兼容）· 待验证+静态确认 4（性能数字/KB 规模/净机部署/GitHub 公开可见性）。

| 严重度 | 问题 | 位置/证据 | 反证（已排除的解释） |
|---|---|---|---|
| **P0** | 交付目录 6 份报告哈希与 validation manifest 全部不匹配；S3 板蓝根从未进入 manifest/verification/current_run——证据链断裂 | `07_交付/delivery_20260921/` vs `docs/validation/delivery_20260921/manifest.json`（python sha256 逐文件比对）；git log 路径显示文件由 3815fa9…29377b6 重制而回执停在 ded9267 | 已排除"manifest 哈希属其他目录"：manifest run_id=delivery_20260921 且其中仅 S1/S2 两场景 |
| **P1** | 交付报告早于 Word 兼容修复（4c63335）、TOC/版式修复与确定性归因引擎（6b9a8b8）——交付物不含最新修复与最新归因方法 | §4 版本矩阵 | 已排除"引擎不影响报告"：数据全流程_20260922 以新引擎为叙述基础，交付报告却生成于引擎之前 |
| **P1** | 评测报告主文档（evaluation_report.md）停在 0919/5974275 时代；RPA 7/7、三步法 3/3、结构 7/7 全部绑定 0918 运行；人工 0-5 全 PENDING | §2 | 已排除"另有新版评测报告"：全仓搜索 evaluation 相关文件，50 行版为唯一现行本 |
| **P1** | 三场景中 S3 无证据链；场景编号三处互斥（scenarios.json vs current_run vs 0919 CSV） | §2 第一行 | 已排除"scenarios.json 为废文件"：competition_configuration 为 README 宣称的正式比赛启用配置 |
| **P2** | prompt_design.md v18/v9 vs 代码 v21/v10，滞后 3 版 | narrative.py:28-29 | 已排除"另有版本文件同步"：retrieval_contracts.md 亦未提 v21 |
| **P2** | PPT 自 0918 未刷新、自认缺实证页；与最新报告数据无绑定保证 | §5 | — |
| **P2** | 视频绑定 03a5a30、media_freshness=PENDING、录制时报告为缓存命中 | demo_receipt.json | — |
| **P2** | DELIVERY.md 交付导航陈旧（仍指 0918 视频与 5974275 为"当前"），与根 README 矛盾 | docs/repository/DELIVERY.md | — |
| **P2** | 无根 LICENSE（自有代码许可未决）；PyMuPDF AGPL-3.0 分发影响未决 | §6 | LICENSE_STATUS.md 已如实披露，属"已知未决"而非隐瞒 |
| **P3** | current_run.json media 段自相矛盾（59.16s webm vs media_freshness 指 demo_20260920）；delivery_20260921/README 基线 39c0e75 vs current_run ded9267 | §4/§5 | — |
| **P3** | 差异≤1% 的黄金值仅覆盖合成行业包，赛题三场景无逐指标独立对拍表；"three_step"在 HEAD 代码/测试 0 命中（搜索词：`three_step`、`三步`，后者仅 metric_contract.py:3 注释命中） | §2 | 独立审查员单场景重算可作部分独立证据 |
| INFO | 竞赛数据边界合规迹象良好（授权记录/合成标注/停用开关/目录分离）；诚实性设计（PENDING 不代填、DEGRADED 不冒充）贯穿全部回执 | §6/§7 | — |

## 九、未覆盖残留（本次审查范围外或能力受限）

1. 视频画面、PPT 渲染、报告版式的视觉判断——待人工视觉。
2. 未运行任何测试/verify_repository.py/哈希工具以外的构建（只读纪律）；346/374 测试通过为文档宣称，未复跑。
3. GitHub 仓库公开可见性、CI 现状——需网络访问人工确认。
4. docs/repository/ 其余文件（FIXES/AUDIT_20260919/cleanup_inventory 283 行等）与 docs/adr、industry 子目录仅抽查未逐行。
5. 净机部署、Docker 镜像实际构建——未执行。
