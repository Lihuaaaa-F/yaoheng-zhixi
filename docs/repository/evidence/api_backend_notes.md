# 2026-09-19 API、任务、RPA 与人审只读复核

固定基线：`Lihuaaaa-F/yaoheng-zhixi@cdd9cb90d1f2e38fac429e82d89e46765e2317d2`，分支 `codex/core-industry-20260917`。先用 GitHub `fetch_file(ref=完整 commit)` 获取源码，随后核验新 worktree 的 HEAD 与目录树相符；未使用旧 clone 代替新代码。

后端路径以下均相对 `药衡智析_增量源码交接/public_source_candidate/05_原型/backend/pharma/`。本次实际运行 `api_isolated/repro.py`，结果 `api_isolated/result.json`。原始 ActionStore、JobStore、ReviewStore 直接导入；审核函数使用固定 ref 的原始 AST，合成文件与 SQLite 隔离。HTTP 为显式 fake，未加载项目 config/密钥、未调用模型、未访问真实 RPA、未改源码、未删除文件。不是全应用集成测试，人工审核记录仅为隔离合成测试，不能作为业务签字。

## 旧 A01–A06 的当前状态

| 旧编号 | 结论 | 固定 ref 证据 |
|---|---|---|
| A01 季度对标参数丢失 | 原核心问题已修 | `App.tsx:17` URL 和 effect 含 analysis_type；`api.py:92-101` 向 benchmark_analysis 传入；metrics benchmark 返回 analysis_type 和 period。前端 Benchmark 明示成本要素按单位比较。未运行真实数据季度 E2E，不声称完整验证。 |
| A02 重复生成与审核状态 | 缓存费用问题已修，状态契约部分未完成 | `jobs.py:38` 复用 DEGRADED；实测相同 key 返回同 job。审核 PASS 后 `human_review_status` 仍 PENDING，见 N03。 |
| A03 产物变化审核不失效 | 已修并复现正向控制 | `_current_hashes` 调 artifact_path 并核验实际字节；修改隔离 DOCX 后 acceptance=FAIL、active_review=null、expired_count=1。 |
| A04 编辑绕过必填 | 核心空值绕过已修，类型错误仍有 500 | `ExecutableAction` 在草稿、编辑和确认共用；空 verification_target、空 expected_evidence、非法日期均拒绝。非法结构仍在校验前触发 AttributeError，见 N02。 |
| A05 字符串 failed 当发送成功 | 原反例已修，另有 POST 回显绑定缺口 | 原 failed 反例现在 ACCEPTED/UNKNOWN，经过 1 次 GET；错误收件人仍可在 POST 快速分支成为 SENT，见 N01。 |
| A06 JSON [] 导致刷新异常 | 原反例已修 | `protocol_data` 检查字典/枚举结构，刷新 JSON [] 保留 ACCEPTED 并记录协议错误，不抛异常。网络错误另会清空既有回执，见 N04。 |

## 仍确认的问题

### N01 · P2：POST 成功分支没有把回显内容与确认载荷绑定

- 位置：`actions.py:221-223`。这里只检查 HTTP/business code、task_id、status 和 notification_proven。GET 对账分支 `actions.py:193-194` 已逐字段比较，两个入口合同不一致。
- 实测：原确认收件人 test/test；fake POST 200 回显同 task_id，却替换 assignee 为 WRONG RECIPIENT/OTHER、suggestion 为 WRONG ACTION，并给合法形状回执。结果 `SENT`、`SIMULATED_SENT`、GET 次数 0，错误内容被保存在 remote。
- 影响：受控远端错误/冲突响应能被当成已按用户确认内容成功发送。这是可靠性合同反例，不代表原 mock 正常响应会犯错。
- 修复：POST 与 GET 共用完整载荷比较；若 POST 协议只保证部分字段，则不能用该响应单独确认载荷一致，转 GET 对账。不能只验证任务 ID 或用发送文案代替收件人绑定。

### N02 · P2：编辑先调用 `.get/.strip`，错误类型绕过统一校验错误处理

- 位置：`actions.py:134,142,146` 在 `validate_action`（147）之前；`api.py` PUT 接收裸 dict，仅注册 ValueError/KeyError handler。
- 实测：`assignee='bad'`、`finding=null`、`suggestion=[]` 各抛 AttributeError（不是 ValueError），HTTP 路由会成为 500；事务回滚后仍为 DRAFT，未产生发送副作用。
- 修复：先用编辑 schema 校验类型，再合并并验证完整可执行动作；不要对未验证值先调用字符串/字典方法。仍应保留现有确认时完整验证与 payload_hash。

### N03 · P2：审核通过后业务状态仍自相矛盾；过期产物继续命中缓存

- 位置：`worker.py:88-90` 增加 execution_status=COMPLETED 与 human_review_status=PENDING；`api.py:212-214` 人审只更新 acceptance 和 binding；`jobs.py:38` 只按作业 FAILED 判断能否复用。
- 实测：合成机器项通过并加入隔离人审后 acceptance=PASS，而 job.status=DEGRADED、result.human_review_status=PENDING。修改文件后 A03 正确把验收置 FAIL，但再次同 key 入队仍返回同一破损报告。
- 影响：新增的人审字段与实际审核不一致；普通再次生成不能修复失效产物。已有 run_id 可以改变缓存输入，不能将其作为缓存健康检查已实现的证明。
- 修复：明确 execution/capability/acceptance 各自含义；更新绑定人审状态、时间和事件。缓存命中应检查完整产物有效性，失效时创建可追踪重建任务；不得因此重新引入所有 DEGRADED 无条件重跑。`record.json` 若声明“生成时快照”，应明确其时点；若用于当前验收交付，则同步或追加独立审核记录，避免无说明的双版本。
- 不再把“所有 DEGRADED 每次调用重跑模型”列为现存缺陷。

### N04 · P2：一次查询超时抹掉已经确认的发送回执

- 位置：`actions.py:198,200` 给 `_state` 的 remote 参数为 None；`_state:178` 覆盖 remote，`_decode:104` 再由状态派生 http_accepted。
- 实测：先 fake 成功发送，http_accepted=true/notification=SIMULATED_SENT；随后 fake GET 抛 HTTPError，结果 REMOTE_UNKNOWN、remote=null、http_accepted=false/notification=UNKNOWN。
- 影响：最新查询失败与历史已证实发送混在一个字段，用户失去先前成功证据；`action_events` 只保存状态/错误，没有保存被覆盖回执全文。
- 修复：保留 last_confirmed_remote / last_confirmed_delivery；独立记录当前查询 UNKNOWN、查询时间和错误。协议错误路径 `_protocol_error` 已采用保留策略，网络错误与非 200 路径应一致。不得为解决状态未知而自动重发。

## 保留的有效控制与审计边界

- 重复确认仍只有 1 条 outbox。SENDING 恢复仅 1 次 GET、0 次 POST，返回 ACCEPTED；不应继续笼统声称任务重启会重复发送。
- 已确认内容禁止编辑，确认前核对 payload_hash；空必填/非法日期的防线有效。
- 下载路径边界与实际 SHA 校验保留有效；产物漂移审核失效已实测通过。
- 季度对标修复是源码路径核验；没有把没有跑过的真实数据、模型、浏览器测试写成 PASS。
- 前端仍发送 basis，但制药 benchmark 内部固定单位要素比较；当前页面已经明确该比较口径，不把这个产品取舍单独列为数值错误。若以后承诺要素总额对标，再补齐参数与图表合同。

建议优先修 N01（确认载荷一致性）、N03（审核与缓存有效性），随后修 N02/N04。无需改动已修的重复确认和重启对账行为。
