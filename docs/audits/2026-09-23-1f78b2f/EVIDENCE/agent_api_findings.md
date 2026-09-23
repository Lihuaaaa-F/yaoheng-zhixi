# agent_api 审查证据（API 入口 / 任务队列 / RPA 整改闭环）

- 审查对象：worktree `D:/yaoheng-audit-wt-1f78b2f`（yaoheng-zhixi @ 1f78b2f74aad），只读审查，未改任何仓库文件。
- 项目根：`药衡智析_增量源码交接/public_source_candidate/05_原型/`（下文路径均相对此根，简写 `05_原型/`）。
- 范围：`backend/pharma/api.py`（574 行，全文读完）、`jobs.py`、`worker.py`、`actions.py`、`reviews.py`、`context_services.py`、`locks.py`、`versions.py`、`revision.py`、`synthetic_rpa.py`；交叉只读：`frontend/src/api.ts`、`Rectification.tsx`、`hooks.ts`、`App.tsx`、`ReportGeneration.tsx`、`config.py`、`local_validation.py`、`scripts/manage.py`、`data_import.py`（路径安全段）、`import_pipeline.py`（失败/恢复段）、`vector_switch.py`（校验段）、`narrative.py`（findings 字段段）、`decision.py`（selection 段）。
- 对照规范：`00_赛题原始资料/赛题要求_企业出题创灵境.md` 5.4 模块四（157-183 行）、第六节技术路线（207 行起）。

---

## 1. 完整路由表

全局中间件/依赖：
- `optional_token_guard`（api.py:19-27）：仅当环境变量 `PHARMA_API_TOKEN` 非空时，`/api/*`、`/docs`、`/redoc`、`/openapi.json` 须携带 `X-API-Token`（`secrets.compare_digest` 常量时间比较），否则 401 `{code:UNAUTHORIZED}`。`/health` 与静态资源豁免。默认不设 token（本地演示，manage.py 绑 127.0.0.1）。
- 异常映射：`ValueError→422 {VALIDATION_ERROR}`（api.py:62-63）；`KeyError→404 {NOT_FOUND}`（api.py:64-65）；pydantic 默认 422 仍生效。前端 `api.ts:7-8` 解析 `data.error?.message`，契约一致。
- 无 CORS 配置（同源部署：`app.mount('/', StaticFiles(frontend/dist))`，api.py:574）。
- 鉴权情况总结：**所有业务端点默认无认证**（演示态）；token 为可选部署加固。前端 `frontend/src` 全目录 grep `X-API-Token|x-api-token` = **0 hits**（api.ts 只发 Content-Type）——即按注释指引设 token 部署公网时，自带 SPA 将全部 401。

| # | 方法+路径 | 处理函数(api.py 行) | 输入校验 | 前端调用 | 备注 |
|---|---|---|---|---|---|
| 1 | GET /health | health(66) | 无 | manage.py worker_ready 探测 | 读 worker.heartbeat，age<180 判活；rpa_mode 如实报 `local_simulator/unverified` |
| 2 | GET /api/industry/catalog | industry_catalog(96) | 无 | App.tsx 载入上下文列表 | |
| 3 | GET /api/catalog | get_catalog(101) | context_id 可选 | App.tsx 初始化选择 | 附 demo_assignee（待分配） |
| 4 | POST /api/analyses | analysis(105) | AnalysisRequest：month 正则、extra=forbid、Literal 枚举 | 分析页 | focus_analysis 可触发自动入队报告（幂等，见 §4） |
| 5 | GET /api/dashboard/heatmap | dashboard_heatmap(123) | month `^20\d{2}-(0[1-9]|1[0-2])$`、basis Literal | 热力图页 | |
| 6 | GET /api/analyses/{id} | get_analysis(131) | KeyError→404 | | |
| 7 | GET /api/benchmarks | get_benchmark(133) | left==right→422；**month/product 无 pattern 校验**（与 5/39 不一致） | 对标页 | 证据去重（153-159） |
| 8 | POST /api/reports (202) | report(201) | ReportRequest：run_id `^[A-Za-z0-9_-]{1,80}$` | ReportGeneration.tsx:32（DEGRADED 时带 retry:true） | 入队幂等，见 §4 |
| 9 | GET /api/jobs | jobs(205) | limit 1..500、offset≥0 | hooks.ts:16 带 context_id | 范围过滤先于分页（fix7，jobs.py:77-85） |
| 10 | GET /api/jobs/{id} | job(209) | KeyError→404 | JobProgress.tsx:18 轮询 | 附 history |
| 11 | GET /api/artifacts/{id} | artifact(211) | preview 可选 | 报告下载 | 哈希+路径包含校验（jobs.py:127-138）；preview 显式标注未审草稿 |
| 12 | POST /api/reports/{job_id}/reviews (201) | submit_review(268) | ReviewRequest extra=forbid、维度枚举、评分 0..5 | 人工评审 | 仅 SUCCEEDED/DEGRADED + docx 产物 + 哈希严格匹配（237-241） |
| 13 | GET /api/reports/{job_id}/reviews | list_reviews(270) | KeyError→404 | | 逐条标注 valid_for_current_artifacts |
| 14 | GET /api/reports/{job_id}/acceptance | report_acceptance(275) | KeyError→404 | | **有副作用的 GET**：重算并回写 jobs.result（见 §6-F） |
| 15 | POST /api/reviews/import (201) | import_reviews(279) | entries 1..50；逐条 try/except 收集错误 | 演示/评测导入 | 无整体事务（逐条提交，失败不回滚已成功项） |
| 16 | POST /api/imports (202) | imports(286) | 无 | | 题包全量 ingest 任务 |
| 17 | POST /api/data/parse (202) | data_parse(303) | DataParseRequest extra=forbid、长度上限 | 数据中心 | 无待解析→422；`_reject_active_parse` 拒并发（290-293，仅扫最近 60 条，见 §6-D） |
| 18 | POST /api/kb/build (202) | kb_build(314) | 无 | 知识库页 | 同上并发拒绝 |
| 19 | POST /api/templates/parse (202) | template_parse(324) | 无 | 模板中心 | |
| 20 | GET /api/templates | templates(335) | 无 | | |
| 21 | POST /api/imports/uploads (201) | import_upload(353) | multipart：kind 白名单、后缀×kind 白名单、≤50MB（**读满内存后**才判，data_import.py:155）、内容哈希幂等 | 上传 | 文件名不参与落盘路径（id=sha256[:16]+kind） |
| 22 | GET /api/imports/{id}/preview | import_preview(358) | KeyError→404 | FilePreview | 只读 |
| 23 | GET /api/imports/{id}/file | import_file(363) | KeyError→404 | | Content-Disposition 用服务端 path.name（original.<ext>），用户文件名仅在 DB |
| 24 | GET /api/imports | import_list(369) | kind 可选 | | |
| 25 | GET /api/imports/{id} | import_detail(373) | KeyError→404 | | |
| 26 | POST /api/imports/{id}/mapping | import_mapping(377) | ImportMappingRequest | | 需表格预览表头，否则 422 |
| 27 | POST /api/imports/{id}/validate | import_validate(386) | 仅 business；options dict | | 结果持久化 last_validation |
| 28 | POST /api/imports/{id}/publish (201) | import_publish(394) | business/knowledge 分支 | | template 用 29 号端点 |
| 29 | POST /api/imports/{id}/template-check | import_template_check(405) | 仅 template | | |
| 30 | GET /api/kb | kb(411) | context_id 可选 | | 非 competition 返回独立合成知识目录 |
| 31 | POST /api/kb/search | kb_search(421) | SearchRequest：query 1..500、mode Literal | | fix2：factory/mode 贯穿检索 |
| 32 | POST /api/actions | draft(436) | ActionRequest：字段长度上限、priority Literal、expected_evidence≥1 | Rectification.tsx:58 | 业务哈希幂等（actions.py:133-134） |
| 33 | GET /api/actions | list_actions(438) | context_id 可选（内存过滤） | hooks.ts:16 | 不带参数返回全部上下文任务 |
| 34 | PUT /api/actions/{id} | edit_action(440) | **裸 dict**（无 pydantic 模型；store 内 validate_edit_types+ExecutableAction 兜底） | Rectification.tsx:57 | 仅 DRAFT 可编辑 |
| 35 | POST /api/actions/{id}/confirm | confirm(442) | ConfirmRequest{payload_hash} | Rectification.tsx:93 | 哈希绑定→outbox |
| 36 | POST /api/actions/{id}/refresh | refresh(444) | 无 body | Rectification.tsx:96 | 向 mock 查询回执 |
| 37 | POST /api/actions/{id}/acknowledge | acknowledge(450) | 姓名 1..80、备注≤2000 | Rectification.tsx:104 | 署名确认，幂等（已确认直接返回） |
| 38 | GET /api/actions/{id} | get_action(454) | KeyError→404 | | |
| 39 | GET /api/forecast | forecast(463) | month `_month_query()` 正则 | | Holt 外推 |
| 40 | GET /api/attribution | attribution(472) | month 正则、basis/compare Literal | | 非 competition 返回 UNAVAILABLE+原因 |
| 41 | GET /api/agent/decision | agent_decision(486) | month 正则 | | 确定性；with_advisory 默认关（GET 不默认耗模型） |
| 42 | POST /api/agent/decision/{id}/apply | apply_decision(501) | decision_id int | | applied_job_id 幂等拒绝（509） |
| 43 | GET /api/kb/graph | kb_graph(515) | context_id 可选 | | |
| 44 | GET /api/model/routes | model_routes(525) | 无 | | |
| 45 | GET /api/settings/models | get_model_settings(536) | 无 | | 密钥不回显 |
| 46 | PUT /api/settings/models | put_model_settings(540) | ModelSettingsPayload | | |
| 47 | POST /api/settings/models/test | test_model_settings(544) | route/overrides | | |
| 48 | GET /api/settings/models/list | list_model_settings(548) | base_url/key_file 可选 | | fix：None 不入覆盖字典 |
| 49 | GET /api/settings/models/presets | model_presets(556) | 无 | | |
| 50 | GET /api/settings/vector-model | vector_model_status(562) | 无 | | |
| 51 | POST /api/settings/vector-model/switch (202) | vector_model_switch(567) | VectorSwitchRequest：path 2..400 | | 本地脚本校验+适配评估+重建（vector_switch.py:97-135） |
| 52 | / (静态) | StaticFiles mount(574) | — | | frontend/dist |

统计：52 条路由（1 health + 51 API）+ 1 静态挂载；POST 22 / GET 27 / PUT 2（含静态共 52 注册）。分页仅 `GET /api/jobs`（limit/offset，SQL 内范围过滤先行）；其余列表端点无分页（actions 全量、imports 全量）。

---

## 2. RPA 整改任务生命周期（分析建议→结构化任务→人工确认→HTTP 调度→回执→前端状态）

1. **分析建议来源（LLM）**：报告 narrative.findings 携带结构化字段 `suggestion/verification_target/expected_evidence/responsible_role/department/priority(Literal high|medium|low)/deadline_basis`（narrative.py:315-320 生成模型、325-336 提案模型、520/633/648 校验非空）。Rectification.tsx:8 `isActionable` 过滤未解析占位符（`[[..]]`/`{{..}}`）后供"载入当前报告建议"下拉（37-42）。
2. **草稿生成** `POST /api/actions`（api.py:436→actions.draft 121-138）：
   - 输入：snapshot_id（必须已存在于 snapshots 表，KeyError→404）、finding、assignee{name,department,role?}、suggestion、priority、四项核查元数据（verification_target/expected_evidence/responsible_role/deadline_basis，API 层 min_length=1）。
   - 服务端组装任务 JSON（actions.py:129）：`task_id='YH-'+business[:24]`；`task_title=finding[:100]`；`source={analysis_type,analysis_month,product,finding+'；分析期间：start 至 end'}`；`deadline=(now+7天).strftime('%Y-%m-%d')`（草稿默认，元数据注明"草稿默认建议七日内复核…非既定业务期限"，前端可改）；`created_at` ISO8601 带时区；`notify_method='wechat'`。**字段规范（赛题模拟 RPA 契约）逐项对齐**：task_id/assignee{name,department,role}/source{analysis_type,analysis_month,product,finding}/priority(high|medium|low)/deadline(YYYY-MM-DD)/suggestion/notify_method/created_at 全部存在且类型正确（synthetic_rpa.Task 模型 synthetic_rpa.py:10-11 与之一致）。
   - `validate_action`（52-53→ExecutableAction.model_validate）：extra=forbid；占位符/空白检测（27-38）；assignee 四键、source 四键必填（40-50）；deadline 为 date 型。校验通过才落库。
   - 幂等：business_hash=digest(action_meta+analysis_context+snapshot_id+finding+assignee+suggestion+priority)（127），`BEGIN IMMEDIATE` 内查重，命中即返回旧记录（133-134）；task_id 撞库时换 uuid 后缀（135-136）。
3. **人工编辑** `PUT /api/actions/{id}`（139-166）：仅 DRAFT；字段白名单（144）；改 snapshot_id 拒绝；重新计算 business_hash，与他人重复→422 `DUPLICATE_DRAFT_USE_EXISTING`；`validate_action` 全量重校验（161）。确认后不可编辑（143）。
4. **人工确认** `POST /api/actions/{id}/confirm`（167-176）：`validate_action` 再校验；`payload_hash != 当前 action_identity` → 422 `PAYLOAD_CHANGED_RECONFIRM_REQUIRED`（防止前端展示与库内不一致时误确认）；DRAFT 态写入 outbox(QUEUED) 并置 actions.status=QUEUED，事件表记录 CONFIRMED_BY_USER+哈希。非 DRAFT 幂等返回。
5. **HTTP 调度（worker 后台线程）** worker.py:125-135 `dispatch_loop` 每 0.5s 扫 `outbox.state IN (QUEUED,SENDING)` → `deliver_one`（actions.py:219-243）：
   - 事务内置 SENDING、attempts+1（224-230）；再次核对 `outbox.confirmed_hash == payload_hash`（227）。
   - 恢复语义：发现 status 已是 SENDING（崩溃恢复）→ 直接 `_reconcile` 查询而非重发（229-231）。
   - `POST {RPA_BASE_URL}/api/rpa/tasks`，httpx timeout=10s/connect=3s（222）。RPA_BASE_URL 默认 `http://127.0.0.1:8090`（config.py:35），manage.py 显式设 `http://127.0.0.1:8090`（manage.py:66）——与赛题接口约定 `http://localhost:8090/api/rpa/tasks` 一致（回环等价）。
6. **回执判定（严格）**（233-243）：
   - HTTP 422 → FAILED（终态，"参数被原mock拒绝"）。
   - 响应非协议 JSON → `_reconcile`；`protocol_data`（77-84）要求 `{code:int,data:dict}`，data.status ∈ received/sent/confirmed/in_progress/completed。
   - 判 SENT 需同时满足：HTTP 200 **且** body.code==200 **且** `confirmed_payload_matches`（远端回显逐字段等于本地 payload，64-65）**且** data.status=='sent' **且** `notification_proven`（67-75：notify_status.wechat 匹配 `已发送至 X(Y)` 且 sent_at 非空，或 status_history 含 sent+time）。
   - 任一不符 → `_reconcile` GET `/api/rpa/tasks/{id}`（204-218）：远端存在且 payload 匹配 → SENT（有微信回执）/ACCEPTED（无回执）；payload 不匹配 → CONFLICT；不存在/查询失败 → `_query_failed` → DELIVERY_UNKNOWN，**停止自动重发**（注释言明），仅手动 refresh 可再查。
7. **微信模拟闭环**：模拟 RPA（题包原 mock 优先，否则 synthetic_rpa.py:16-23）落库并返回 `notify_status={'wechat':'已发送至 {name}({department})','sent_at':...}`；系统记录于 actions.remote；前端 Rectification.tsx:80 展示"原 mock 已记录模拟发送"，DeveloperDetails 展示原始回执。**满足赛题"系统记录发送状态，前端展示已发送至XX责任人"**。
8. **前端状态区分（诚实性）**：taskLabel 8 态映射（Rectification.tsx:6）：DRAFT/QUEUED/SENDING/SENT=模拟通知已发送/ACCEPTED=远端已接收,通知未确认/DELIVERY_UNKNOWN/FAILED/CONFLICT。`delivery` 三元组（actions._decode 114-115）：http_accepted、notification（须回执证明）、remediation（confirmed/in_progress/completed 才显示，且文案注明"原 mock 记录完成；真实整改仍须人工验收"）。责任人确认 acknowledge（177-187）与整改完成解耦（remediation_completed=False），前端多处声明"发送前确认不计入，送达不等于整改完成"（34）、"已确认跟进，不代表整改完成"（98）。**判定：状态区分诚实，满足**。
9. **任务追踪看板（赛题加分项 5.4.3）**：Rectification.tsx:28-34 已生成=去重任务数、模拟通知送达=`delivery.notification=='SIMULATED_SENT'`（回执口径）、责任人确认=署名+时间齐备。口径注明。**判定：满足（以真实回执口径实现"已生成/已送达/确认数"）**。
10. **重启恢复**：outbox QUEUED/SENDING 持久于 SQLite；worker 重启后 dispatch_loop 重扫；SENDING 走 reconcile 防重复投递；模拟 RPA 侧 synthetic_rpa 以 task_id 主键幂等（重复 POST → 400 → 触发 reconcile 路径恢复）。

---

## 3. 赛题要求逐条判定（模块四 + 第六节相关）

| 赛题条款 | 判定 | 依据（静态确认） |
|---|---|---|
| 5.4.1 大模型自动生成结构化任务 JSON（标题/责任人部门岗位/来源/优先级高中低/截止时间） | **满足**（链路：LLM findings 结构化字段→前端载入→服务端组装完整 JSON；截止时间默认 now+7d 可改；含人工确认门，超出赛题的诚实设计）。严格说"全自动无人工"未做——设计选择为"草稿+人工确认"，字段生成源头确为 LLM 叙事 | narrative.py:315-336；actions.py:129-130；Rectification.tsx:37-42 |
| 5.4.2 HTTP API 发送到模拟 RPA，200=成功触发 | **满足**（且强于字面：HTTP200+code200+回显匹配+status=sent 四重判定） | actions.py:233-243 |
| 5.4.2 模拟微信消息闭环：记录发送状态，前端展示"已发送至XX责任人" | **满足** | synthetic_rpa.py:19；actions.py:67-75；Rectification.tsx:80 |
| 5.4.3 任务追踪看板（已生成/已送达/确认数） | **满足** | Rectification.tsx:28-34 |
| 六 6.1 FastAPI 后端 / requirements 一键启动 | **满足**（uvicorn+manage.py 三进程编排，含就绪门控） | scripts/manage.py:60-110 |
| 模拟 RPA 字段规范（task_id/assignee/source/priority/deadline/suggestion/notify_method/created_at） | **满足**，字段名/枚举/日期格式逐项一致 | actions.py:129 vs synthetic_rpa.py:10-11 |

待实测（静态无法闭环）：端到端演示视频流程（选择→生成→看板→对标→发 RPA）；RPA 触发成功率统计（评测报告口径，代码外交付物）。

---

## 4. 幂等 / 重复提交 / 缓存键

- **报告任务幂等**：`_generation_versions`（api.py:164-186）= soft_items（renderer/model/protocol/endpoint/prompt/attribution）+ hard_items（retrieval_policy/validator/parser/terminology/retriever/embedding，versions.py:17-34）+ snapshot_id + knowledge_snapshot + template 哈希 + **完整 analysis_context** + model_available + generation/retrieval 参数 + run_id。sha256 为 cache_key，jobs.cache_key UNIQUE（jobs.py:16）。
- `enqueue`（jobs.py:39-67）在 `BEGIN IMMEDIATE` 内判重：
  - 旧任务非 FAILED 且（非终态 / 非 report / 产物健康）→ 返回旧任务（浏览级幂等，POST /api/reports 与 GET /api/analyses 自动入队共用）；
  - DEGRADED + retry=True → 复用已验证部分（snapshot/evidence/benchmark/PASS 的 narrative），记 retry_of；旧任务保留（fix5）；
  - 产物丢失/哈希不符 → repair_of，仅重渲染；
  - 旧 FAILED → 清空旧 cache_key 建新任务（失败可重提）。
- **worker 侧防旧结果误用**（worker.py:40-48）：analysis_context 全等比对、soft 项变化拒收、hard 项缺失即拒收、template 哈希比对（`*_VERSION_CHANGED_RESUBMIT`）；数据版本 `ingest()['snapshot_id']!=snapshot.data_version` 双点校验（75、97）。
- **actions 幂等**：business_hash UNIQUE（同内容重复提交返回既有）；confirm 以 payload_hash 绑定；deliver 前复核 confirmed_hash；acknowledge 二次调用幂等返回。
- **上传幂等**：import_id=内容 sha256[:16]+kind，同内容直接返回既有记录（data_import.py:163-167）。
- **decision apply 幂等**：applied_job_id 已绑定即拒绝（api.py:509）。

## 5. 超时 / 失败重试 / 重启恢复

- RPA HTTP：timeout(10, connect=3)；refresh 查询 timeout 8s。网络/协议异常一律转 `_reconcile` 查证，查证失败 → DELIVERY_UNKNOWN 停止自动重发（防重发风暴）；无指数退避（设计选择，注释言明"停止自动重发"）。
- worker 重启：`store.next()` 取全部非终态任务（含 RUNNING，jobs.py:102-105）；process_job 逐键跳过已算结果（snapshot/evidence/benchmark/narrative/docx）实现检查点续跑；data_parse/kb/template_parse 从 payload['import_ids'] 重放（import_pipeline.py:244-245），PARSING 中记录可恢复；解析失败统一 `_fail` → 记录 PARSE_FAILED + 任务 FAILED（import_pipeline.py:84-87、316-320），PARSE_FAILED 可重试（waiting_imports 收录，data_import.py:579）。
- 单实例保证：`try_exclusive(RUNTIME/'worker.lock')`（worker.py:139；locks.py:30-45 Windows msvcrt/NIX fcntl 双实现），重复启动 SystemExit。
- worker 就绪/退出：manage.py fix8 以 api /health 心跳为就绪判据（先 rpa→api→worker 冷启动顺序）；worker.py:143-149 try/finally 停 dispatcher（join 12s）；心跳 0.5s 刷新（129），/health age<180 判活。
- 例外：进程被 kill -9 时 outbox SENDING 由重启 reconcile 覆盖；heartbeat 文件残留仅导致 /health 短暂报 not alive，无功能影响。

## 6. 发现清单（严重度 + 反证过程）

- **[P3-A] FAILED/CONFLICT 整改任务为同内容死端**：draft 按 business_hash 返回旧记录（actions.py:133-134），edit 拒绝非 DRAFT（143），refresh 不接受 FAILED/CONFLICT（249），actions.py 无 delete/reset（grep `delete|DELETE` 0 hits，api.py 亦无对应路由）。同内容无法重新发起，只能改字段（哈希变化）绕过。反证：确认存在此组合路径，无恢复入口；影响限于演示流程边缘（422/CONFLICT 少见），不涉数据损坏 → P3 非 P2。
- **[P3-B] 设置 PHARMA_API_TOKEN 后自带前端全 401**：middleware 保护 /api/*（api.py:22），frontend/src grep X-API-Token=0 hits（api.ts:2 仅 Content-Type），UI 无 token 输入机制。注释宣称"部署到局域网/公网时设置"（api.py:16-18）照做即 UI 不可用。反证：默认演示不受影响（不设 token 行为不变），属部署文档与实现不一致，非安全漏洞本身。
- **[P3-C] `_recalc_acceptance` 读-改-写无事务**（api.py:247-266）：store.get（连接1）→ 计算 → UPDATE（连接2）。反证：终态 job 的 result 写者仅此函数与 worker（worker 只处理非终态，修复路径开新任务不改旧行，jobs.py:56-62），并发双评审提交各自全量重算、last-write-wins，且 GET /acceptance 幂等重算可收敛 → 无持久损害，P3。
- **[P3-D] `_reject_active_parse` 竞态 + 60 条窗口**（api.py:290-293）：list_jobs(limit=60) 只看最近 60 条；两并发 POST 均过检查则双任务入队（TOCTOU）。反证：单 worker 串行执行；第二个任务从 payload['import_ids'] 重放会重复解析发布（import_pipeline.py:244），publish_business_batch 重复发布风险存在但需 ≥60 条更新的任务或精确并发窗口 → P3。
- **[P3-E] GET /api/benchmarks 的 month/product 无 pattern 校验**（api.py:134）：与 heatmap(125)/forecast(\_month_query) 不一致，畸形月份进入分析层（下游 ValueError→422 或 KeyError→404 兜底存在）。P3/INFO 交界，取 P3 因错误信息口径不一。
- **[P3-F] GET /api/reports/{job_id}/acceptance 是有副作用的 GET**（api.py:275-278 → 264 回写 jobs）：违反 GET 幂等惯例；影响与 C 同域（单写者下可控）。
- **[P3-G] 上传先整读内存后判 50MB**（api.py:356 `await file.read()` → data_import.py:155 才检查）：畸形大请求可造成内存尖峰；本地演示影响小。
- **[INFO-H] PUT /api/actions/{id} 请求体为裸 dict**（api.py:441）：OpenAPI schema 弱化；实际校验由 validate_edit_types + ExecutableAction 兜底（长度/枚举/占位符全覆盖，含 deadline date 强转 → pydantic ValidationError 是 ValueError 子类 → 422 兜底成立）。
- **[INFO-I] synthetic_rpa.create 直接取 assignee['name']**（synthetic_rpa.py:19）：缺键 500；上游 ExecutableAction.assignee_complete 强制 name/department（actions.py:40-44）→ 仅当绕过主系统直打模拟器才触发；模拟器定位内部。
- **[INFO-J] 企业隔离为查询参数级而非强制**：/api/jobs、/api/actions 不带 context_id 返回全上下文（jobs.py:81-82、api.py:439）；前端恒带（hooks.ts:16）；配合可选 token 属演示态设计，README 口径内。
- **[INFO-K] vector-model/switch 的 path 参数可指向任意本地目录**（api.py:567→vector_switch.py:97 `_probe_local(Path(raw_path))`）：只读校验+写配置，属管理员设置面；默认无认证时本地任意用户可切换（回环绑定缓解）。
- 路径穿越专项：**未发现**。产物路径来自 artifacts 表（id 必须命中）+ `is_relative_to(ARTIFACTS)` + 哈希复核（jobs.py:123-137）；导入文件路径=IMPORTS_ROOT/内容哈希id/original.suffix（data_import.py:574-578），用户文件名不进路径；Content-Disposition 用服务端 path.name（api.py:368）。

## 7. 逐函数记录（职责/前提/异常/调用）

### api.py
- `optional_token_guard`(19)：可选鉴权；前提=环境变量；无异常路径（比较失败即 401 响应）。
- `health`(66)：读心跳+RPA 模式；`require_loopback` 异常被捕获转 simulation=False（诚实降级）。前提：RUNTIME 可写（config 建目录）。
- `selected_context`(75)/`scoped_analysis`(79)/`resolved_analysis`(88)：上下文缺省解析；前提=context_catalog() 可用（industry.py，范围外）；GET/POST 口径一致（88-94 注释）。
- `analysis`(105)：快照落库（INSERT OR IGNORE）→ focus_analysis（可能触发 enqueue 回调）。异常下沉 ValueError→422。
- `dashboard_heatmap`(123)/`get_analysis`(131)：透传。
- `get_benchmark`(133)：双工厂对比；competition 走 benchmark_analysis+context_services.retrieve，否则 benchmark_reference；证据去重；narrative generate。前提：narrative.generate 不抛（范围外）。
- `_generation_versions`(164)：版本指纹；前提：TEMPLATE 存在（不存在则 normalize_template 补，175）；gateway 与 generate 同源（fix4）。
- `_enqueue_report`(188)：入队共用路径（reports 端点+agent apply）。前提：revision_record(ROOT) 可计算（revision.py：git checkout→rev-parse，否则源码哈希；env 剥离 GIT_* 覆盖）。
- `report`(201)/`jobs`(205)/`job`(209)/`artifact`(211)：薄封装。
- `_current_hashes`(218)：产物哈希；strict=True 缺失即抛（REVIEW_TARGET_HAS_NO_DOCX）；否则 'STALE'。
- `_submit_review`(237)：终态+哈希门控→ReviewStore.submit→_recalc_acceptance。
- `_recalc_acceptance`(247)：见 §6-C；STALE→file_openable FAIL+overall FAIL（255-257）；human_review_status/capability_status/execution_status 回写；过期审核清单（265）。
- `import_reviews`(279)：批量，逐条 try/except(ValueError,KeyError)。
- `_reject_active_parse`(290)：见 §6-D。
- `data_parse`(303)/`kb_build`(314)/`template_parse`(324)：等待列表→并发拒绝→入队→标记 PARSING。注意 data_parse 在 job 实际运行前就置 PARSING，失败由 `_fail` 纠正为 PARSE_FAILED。
- `import_upload`(353)：async 读→create_upload（幂等）。
- `import_preview`(358)/`import_file`(363)/`import_list`/`import_detail`/`import_mapping`/`import_validate`/`import_publish`/`import_template_check`：见路由表；KeyError→404、ValueError→422 统一。
- `kb`(411)/`kb_search`(421)：上下文分流；KNOWLEDGE_SNAPSHOT_CHANGED→422（context_services.py:71-77）。
- `draft`(436)/`list_actions`(438)/`edit_action`(440)/`confirm`(442)/`refresh`(444)/`acknowledge`(450)/`get_action`(454)：见 §2。
- `forecast`(463)/`attribution`(472)/`agent_decision`(486)/`apply_decision`(501)/`kb_graph`(515)/`model_routes`(525)：透传+决策台账；apply 的 selection 恰为 AnalysisRequest 六键（decision.py:54），ReportRequest 反序列化成立（extra=forbid 不触发）。
- settings 五端点(536-572)：model_settings 模块（范围外，只确认路由契约）。

### jobs.py（JobStore）
- `__init__`(13)：DDL+三列渐进迁移（ALTER 容错 OperationalError）。前提：DB_PATH 可写。
- `db`(26)：sqlite3 timeout=15+WAL；`with c:` 事务。
- `snapshot`(32)/`get_snapshot`(35)：INSERT OR IGNORE 幂等；KeyError('SNAPSHOT_NOT_FOUND')。
- `enqueue`(39)：见 §4；异常=UNIQUE 冲突理论上不可能（事务内先清旧 key）。
- `_decode`(68)/`get`(73)/`list`(76)/`list_jobs`(77)/`list_reports`(86)/`latest_report_for_snapshot`(89)：查询族；list_reports limit=300 供决策引擎。
- `artifacts_healthy`(93)：docx+pdf PASS+文件存在+哈希一致；OSError/ValueError/KeyError→False。
- `next`(102)：非终态最旧一条（重启恢复入口）。
- `update`(106)：状态机+进度+事件表；error 列非原子清空（传 None 即置 None，COALESCE 仅对 progress/detail/result）。
- `history`(120)/`artifact`(122)/`artifact_path`(127)：见 §6 路径穿越段。

### worker.py
- `process_job`(8)：报告主链+四类专用任务分流；全部异常→FAILED（错误串 700 字截断）+traceback；产物原子写（tmp.replace，118）；audit 注册（109）；TOC 刷新后重注册 docx 哈希（107）。
- `dispatch_loop`(125)：outbox+心跳；deliver 异常→DELIVERY_UNKNOWN('worker:'+类型)（133）。
- `main`(137)：单例锁+daemon 线程+轮询 0.5s。

### actions.py（ActionStore）
- 模块级纯函数：`digest`(11)；`ExecutableAction`(13-50)（校验器三连）；`validate_action`(52)；`validate_edit_types`(55)；`confirmed_payload_matches`(64)；`notification_proven`(67)；`protocol_data`(77)；`action_details`(86)；`action_identity`(90)；`now`(93)。
- `ActionStore.__init__`(96)：actions/outbox/action_events 三表。
- `db`(102)：timeout=10+WAL+foreign_keys。
- `_decode`(109)：delivery 三元组推导（§2.8）。
- `get`/`list`(117-120)：list 全量按 updated DESC（无分页，INFO）。
- `draft`(121)/`edit`(139)/`confirm`(167)/`acknowledge`(177)：见 §2。
- `pending`(188)：QUEUED/SENDING。
- `_state`(190)：三表同步写（actions/outbox/events）。
- `_protocol_error`(196)：保留已证状态，未知隔离 DELIVERY_UNKNOWN。
- `_query_failed`(200)：last_query 记录+转 protocol_error。
- `_reconcile`(204)：查询-对账；远端缺回执但本地曾证明→保留旧回执（214）。
- `deliver_one`(219)/`refresh`(244)：见 §2/§5。

### reviews.py（ReviewStore）
- `submit`(39)：reviewer 非空、评分 0..5、三维度枚举；哈希由调用方绑定（api._submit_review strict 模式）。
- `latest_valid`(70)：哈希全等最新一条；FAIL 也是有效评审（仅内容漂移过期）。

### context_services.py
- `retrieval_policy`(27)：仅装包供 JSON 策略；术语黑名单校验。
- `_matching_event`(55)：期间+词命中+适用性。
- `retrieve`(63)：limit 1..100；知识快照指纹强校验（71-77）；图谱扩词仅制药上下文、异常降级 DEGRADED（86-90）；目的检索二次校验 knowledge_version 一致（108）；槽位保留合并（113-118）。

### locks.py / versions.py / revision.py / synthetic_rpa.py
- `exclusive`(11)/`try_exclusive`(30)：双平台文件锁；errno 白名单外异常上抛。
- `soft_items`/`hard_items`（versions.py:17-34）：版本键单一来源（fix21）。
- `source_files`(19)/`code_revision`(38)/`revision_record`(53)：git 可信根判定（路径结构断言）或源码哈希；env 剥离 GIT_*。
- synthetic_rpa：`health`(14)/`create`(16)（task_id 主键幂等，重复 400）/`get`(24)。

### 前端契约核对（frontend/src/api.ts 等）
- `api()`(1-10)：/api 前缀、body 即 POST、错误取 error.message；与后端 `{error:{code,message}}` 形状匹配；无 token 头（§6-B）。
- hooks.ts `useJobsActions`(7-27)：jobs+actions 按 context_id 轮询（2s）；context 切换 AbortController+currentContext 防串台。
- Rectification.tsx：全 7 个 action 端点调用形状与后端模型一致（confirm 传 payload_hash、acknowledge 传 confirmed_by/comment、PUT 传全量表单）。
- ReportGeneration.tsx:32：`api('/reports',{...selection, ...(needsRetry?{retry:true}:{})})`——不带 run_id（缓存键稳定，重复点击幂等）。

## 8. 未覆盖残留（移交主审）
- reports.py（113k 行）、narrative.py、industry.py、metrics.py、data_import.py 主体、import_pipeline.py 主体、model_settings.py、knowledge.py——仅按调用链局部只读，未整读（他人范围）。
- 交付物评测报告中的 RPA 触发成功率、演示视频流程——代码外，待实测。
- 多 uvicorn worker / 反代部署形态（现约定单进程单 worker，manage.py 无 --workers）。
- 题包原 mock_rpa_server.py 的行为（发布包内不存在，代码路径以 synthetic_rpa 为准；manage.py 优先用原 mock）。

— 审查者：agent_api（无视觉能力，纯静态）；完成时间 2026-09-23。
