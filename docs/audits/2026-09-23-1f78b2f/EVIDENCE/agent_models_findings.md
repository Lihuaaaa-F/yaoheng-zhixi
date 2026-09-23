# 模型配置与调用链审查证据（agent_models）

- 审查对象：worktree `D:/yaoheng-audit-wt-1f78b2f`（yaoheng-zhixi @ 1f78b2f），只读审查，未修改仓库。
- 范围文件（全文逐行读完）：`药衡智析_增量源码交接/public_source_candidate/05_原型/backend/pharma/model_settings.py`（391 行）、`model_registry.py`（187 行）。
- 追踪调用方（只读）：`narrative.py`（重点 1-70、660-1099 行 ModelGateway/generate）、`api.py`（设置端点 528-568、鉴权中间件 17-29、ValueError 处理 62-65）、`worker.py`（25-100）、`decision.py`（124-160）、`import_pipeline.py`（85-110、205-230、385-405）、`vector_switch.py:82`、`config.py` 全文、`versions.py`（soft/hard_items）。
- 测试文件（全文读完）：`tests/test_gateway_failover.py`（169 行）、`test_settings_security.py`（62 行）、`test_private_configuration.py`（57 行）、`tests/conftest.py`。
- 前端接线抽查：`frontend/src/ModelConfigForm.tsx`。
- 方法：Trail of Bits audit-context-building + spec-to-code-compliance（portable/manual）；逐函数记录职责/前提/异常路径/调用关系；疑似缺陷先反证。

---

## 一、逐函数记录

### model_settings.py

| 函数/常量 | 行 | 职责 | 前提（谁建立） | 异常路径 | 调用关系 |
|---|---|---|---|---|---|
| `SETTINGS_PATH/KEYS_DIR/ROUTES/FIELDS` | 27-33 | 常量：设置文件、密钥目录、双路由、可写字段 | config.RUNTIME（导入期） | — | 全模块 |
| `canonical_route` | 36-40 | 路由名规范化（narrative→analysis, decision→extraction） | 调用方传路由名 | 未知名 raise `UNKNOWN_MODEL_ROUTE:<name>` | ModelGateway.__init__/for_route、save/test/list |
| `_load` | 43-50 | 读 model_settings.json | 文件可缺 | OSError/ValueError → 返回 {}（静默容错：损坏文件等同未配置） | _migrated/save/resolve/status/embedding_dir/set_vector |
| `_migrated` | 53-62 | 读时迁移旧路由名（不重写文件） | _load | 同上 | resolve/status/embedding_dir |
| `_loopback_host` | 65-72 | 明文 http 白名单：localhost/127.0.0.1/::1/0.0.0.0/host.docker.internal | urlsplit 可解析 | ValueError → False | _validate_base_url |
| `_validate_base_url` | 75-82 | 必须 http(s):// 开头；禁内嵌 @ 凭据；非回环强制 https | — | 返回错误串（不抛） | _sanitize_overrides/_validate_connection |
| `_sanitize_overrides` | 85-104 | 请求参数覆盖项安全化：key_file 仅允许 KEYS_DIR basename；base_url 过校验；effort 枚举 | 修复 #4（2026-09-21） | raise KEY_FILE_OVERRIDE_RESTRICTED / BASE_URL_OVERRIDE_INVALID / REASONING_EFFORT_INVALID | test_connection/list_remote_models；测试 test_settings_security 覆盖 |
| `_validate_connection` | 107-125 | 保存前逐项校验：protocol 枚举、base_url、model 非空白、effort 枚举、tier_error 档位 | — | 返回 errors 列表 | save_settings |
| `save_settings` | 128-161 | 保存连接：api_key → 写 `KEYS_DIR/<route>.key`（chmod 600 尽力）；设置文件只存路径；保留 vector_model | PUT /api/settings/models（api.py:541） | INVALID_SETTINGS_SHAPE/SECTION、KEY_FILE_NOT_FOUND、校验错误（api 层转 422） | api.put_model_settings |
| `resolve` | 164-172 | 返回路由设置（未配置空 dict）；未知路由返回 {} 不抛 | — | — | ModelGateway.for_route/__init__、status、list_remote_models |
| `status` | 175-218 | 对外回显：configured/model/tier/base_url/protocol/key_set/key_file 路径/sources(env/settings/default)；绝不回显密钥内容 | GET /api/settings/models | — | api.get_model_settings |
| `test_connection` | 220-251 | 真实短生成测试：`{"ok":true}` JSON 校验 + returned_model 身份回显 + 耗时 + usage | POST /api/settings/models/test；overrides 过 _sanitize_overrides | NO_KEY / FAILED（reason=str(exc)[:300]，真实失败原因） | api.test_model_settings |
| `list_remote_models` | 259-276 | GET `<base>/models`（OpenAI 协议 Bearer），失败 UNAVAILABLE+hint 手填，timeout=10、trust_env=False | GET /api/settings/models/list | 全异常捕获 → UNAVAILABLE | api.list_model_settings |
| `embedding_dir` | 281-290 | 向量目录解析：env → 设置文件 vector_model.path → RUNTIME/models/bge-large-zh-v1.5 | — | — | knowledge.CpuEmbedding、vector_switch |
| `embedding_fingerprint` | 293-307 | ONNX/tokenizer/config 哈希指纹（入知识版本） | — | OSError → 回退 knowledge.EMBEDDING_SHA | knowledge、vector_status、_probe_dimension_cached |
| `set_vector_model` | 310-318 | 记录向量切换（env 存在时拒绝写） | vector_switch 任务 | raise PHARMA_EMBEDDING_DIR_ENV_TAKES_PRIORITY | vector_switch.run_vector_switch |
| `clear_vector_model` | 321-324 | 清除 vector_model 键（文件不存在时会创建 `{}` 文件，INFO） | — | — | vector_switch |
| `_probe_dimension_cached` | 327-360 | 从 ONNX 输出形状惰性探测维度，按指纹缓存 RUNTIME/vector_dimension.json | onnxruntime 可用 | 全异常 → None（展示降级 "—"） | vector_status |
| `vector_status` | 363-391 | 本地向量模型状态：文件存在性、维度、指纹、note | — | config.json 损坏 → name='' | status、api.vector_model_status |

### model_registry.py

| 函数 | 行 | 职责 | 备注 |
|---|---|---|---|
| `ROLE_RULES` | 21-32 | extraction=仅 small、analysis=仅 large 的档位规则 | 赛题多模型协作合同 |
| `_TIER_PATTERNS_*` | 35-36 | 未收录模型的命名兜底 | `3b` 是子串匹配，会误中如 `xx3b-32b`? 检查：large 先判，`32b` 命中 large，顺序正确 |
| `classify_tier` | 124-138 | 注册表精确匹配 → 模式兜底 → None（允许手填） | 未收录不硬拒，与 hint 一致 |
| `tier_error` | 141-150 | 档位限制错误文案（保存时拦截） | tier None 时放行 |
| `effort_body_params` | 153-180 | low/medium/high → 厂商参数：glm-5.3/kimi-k3/gpt-6 → reasoning_effort low/high/max；glm-5.2 → medium/xhigh；deepseek → thinking.type；aliyun → enable_thinking；openai/gpt- → reasoning_effort；未识别 → {} | 注释注明 2026-09-22 逐家核对官方文档；厂商迭代风险已声明 |
| `presets_payload` | 183-187 | 前端预填充数据源 | GET /api/settings/models/presets |

### narrative.py ModelGateway（追踪，非全文范围）

| 方法 | 行 | 要点 |
|---|---|---|
| `__init__` | 668-716 | 解析链：显式参数→env→设置文件→默认（config.py:39-42 单一来源）；coding 端点 env 可禁用；GLM/ZHIPU env 密钥仅官方端点可用（供应商作用域）；建 calls/call_attempts/cache 三表（SQLite 账本）+ 旧表列迁移 |
| `_headers` | 718-719 | anthropic 用 x-api-key+version；openai 用 Bearer |
| `for_route` | 721-775 | PHARMA_MODEL_ROUTES(JSON) → 路由级 env（含旧名）→ 主配置回退；设置文件路由密钥提升为显式参数（2026-09-22 修复遮蔽 bug）；**跨主机保护**：base_url/protocol 与主配置不一致且无专属 key_file → 清空 key、credential_source=ROUTE_KEY_REQUIRED |
| `routes_status` | 777-788 | 各路由实际生效配置（验收回执） |
| `complete/_complete` | 790-878 | 预算：`SELECT count(*) FROM calls WHERE operation=?` ≥ max_calls(默认40) → MODEL_CALL_BUDGET_REACHED（跨进程文件锁仅覆盖计数事务）；HTTP 不串行；openai body: max_tokens(env 8192)/temperature=0/response_format=json_object + effort_body_params；重试：429/5xx 退避 20/40s 共 3 次；1113(智谱余额) → 切 coding 端点（同次调用）；其余异常直接 raise；每次尝试入 call_attempts（endpoint 经 _safe_endpoint 脱敏）；usage/returned_model/identity 回填 calls；原始响应落 `RUNTIME/model-response-<id>.json` |
| `generate` | 934-1098 | 有界生成：缓存键=全链路版本指纹 sha256（含 model/protocol/base_url/prompt/validator/retrieval/...）；**generation_parameters.reasoning_effort 取 `os.getenv('PHARMA_MODEL_REASONING_EFFORT','low')` 而非 gateway.reasoning_effort**（955 行）；修复轮 max_repairs=2（冻结已过单元）；身份汇总 MISMATCH→DEGRADED、model_live 需 VERIFIED；失败/断网 → rules/mixed 降级模式，failure_reasons 留痕；缓存仅在实际模型产出后写入 |

### 调用方清单（配置消费点）

| 调用点 | 路由 | operation | 失败降级 |
|---|---|---|---|
| narrative.generate（worker 报告 + api benchmarks） | analysis | generate | rules/mixed 降级 |
| api._generation_versions | analysis（与 generate 同源，fix4） | — | — |
| api.get_analysis 自动解释 | ModelGateway() 默认=analysis | — | model_available=False 降级 |
| import_pipeline._extraction_mapping | extraction | import_mapping | None → 预设映射（确定性回退） |
| import_pipeline._analysis_hypotheses | analysis | import_attribution | None → 规则文本 |
| import_pipeline._template_binding_analysis | analysis | template_binding | None → 确定性绑定语义 |
| decision 智能体 | for_route(route) | decision | DEGRADED |
| vector_switch 适配评估 | analysis | vector_switch | 失败回退 |
| model_settings.test_connection | 任意 | settings_test | FAILED/NO_KEY |

---

## 二、配置 → 调用链路图

```
前端 ModelConfigForm.tsx (api_key type=password, "留空保持不变")
   │  PUT /api/settings/models {connections:{analysis:{model,base_url,protocol,key_file?,api_key?,vendor,reasoning_effort}}}
   ▼
api.put_model_settings → model_settings.save_settings (128)
   ├─ api_key → RUNTIME/keys/<route>.key (chmod 600 尽力；Windows 不完全生效, 149-152)
   ├─ key_file 存在性检查 (155)          ★仅 is_file，不限 KEYS_DIR —— 问题 F1
   └─ RUNTIME/model_settings.json（只存路径与端点，无密钥）
   ▼（API 进程与 worker 共读同一文件）
ModelGateway.for_route(route) (narrative 721)
   ├─ PHARMA_MODEL_ROUTES JSON → 路由级 env（旧名 NARRATIVE/DECISION）→ resolve()（settings.json）→ config.py 默认
   ├─ 跨主机保护 (771-774)：不同 host/protocol 且无专属 key_file → key=''（防借用主密钥外发）
   ▼
_complete (797)：Authorization/x-api-key 头 → POST <base>/chat/completions（或 /v1/messages）
   ├─ 429/5xx：退避 20/40s 重试 ≤3        ★Timeout/ConnectError 不重试 —— 问题 F4
   ├─ 智谱 1113：切 coding 端点（仅官方双端点，_official_zhipu_endpoint 严格校验 host/scheme/path）
   └─ 账本 model_gateway.sqlite3：calls + call_attempts(endpoint 脱敏, credential_source)
   ▼
generate (934)：缓存键=版本指纹 → 命中即 cache_hit=True 返回
   ├─ 实调 → validate_findings（自由数字拒绝 + _rounded_metric_bindings 唯一绑定）
   └─ 失败 → generation_mode=rules/mixed（DEGRADED，failure_reasons 留痕）

向量链（不走 API）：embedding_dir() → knowledge.CpuEmbedding（本地 ONNX CPU）
切换：POST /api/settings/vector-model/switch → vector_switch 任务 → set_vector_model + 知识库按 embedding_fingerprint 重建
```

---

## 三、密钥处理清单

| 检查项 | 结论 | 证据 |
|---|---|---|
| 设置文件存密钥明文？ | 否（只存 key_file 路径） | model_settings.py:129-160 |
| DB 存密钥？ | 否（calls/call_attempts 无密钥字段；endpoint 经 _safe_endpoint 去 query/凭据并替换 key 为 [REDACTED]） | narrative.py:64-67, 804, 861 |
| 前端回显完整密钥？ | 否（status 只回 key_set/key_file 路径；表单 password + 留空保持） | model_settings.py:208-210；ModelConfigForm.tsx:126 |
| 日志/print 泄漏？ | 未发现 print/logger 输出密钥（三文件 grep 无命中） | grep 复核 |
| RUNTIME 进仓库？ | .gitignore 拦截（docstring 声明；RUNTIME=.runtime） | model_settings.py:11-14 |
| 请求覆盖 key_file 任意路径？ | 已限 KEYS_DIR basename（修复 #4，有测试） | model_settings.py:93-97；test_settings_security:12-18 |
| **保存的 key_file 任意路径？** | **允许（仅 is_file 检查）** —— F1 | model_settings.py:154-156 |
| base_url 内嵌凭据？ | '@' 拒绝；query 未拒 —— F6 | model_settings.py:78-81 |
| GLM/ZHIPU env 密钥作用域 | 仅官方智谱端点可用，其他 host 清空（有测试） | narrative.py:688-695；test_gateway_failover:139-144 |
| 密钥借给异构路由？ | 跨主机保护清 key（有测试） | narrative.py:771-774；test_gateway_failover:125-136 |
| 重定向外泄？ | follow_redirects=False（客户端与请求均设） | narrative.py:705, 842；test:147-161 |
| 代理外泄？ | list_remote_models trust_env=False | model_settings.py:267 |
| 测试桩真密钥？ | 无（unit-test-key/route-fixture-key/fake-glm-key；conftest 清空全部密钥 env） | conftest.py:5-11 |
| test_connection reason 泄漏面 | str(exc)[:300]——httpx 异常文本含 URL（含 query）；密钥在头不在 URL，正常无泄漏 | model_settings.py:235-237 |

---

## 四、判定分级（重点核查项）

| # | 核查项 | 判定 | 依据 |
|---|---|---|---|
| 1 | 云 API + 本地服务双通道配置 | 满足 | registry API_VENDORS(6家)/LOCAL_VENDORS(ollama/vllm/lmstudio 127.0.0.1)；保存/回显/预填充链完整 |
| 2 | 地址/模型ID/凭据保存（不入库明文） | 满足（key_file 路径白名单缺口→F1） | settings.json 无密钥；密钥独立文件 |
| 3 | 连接测试 | 满足 | 真实短生成+JSON 结构校验+身份回显+耗时/usage；NO_KEY 分支 |
| 4 | 能力检查（模型清单） | 部分 | list_remote_models 仅 OpenAI 协议 GET /models+Bearer；anthropic 端点不支持（固定路径/头）；失败不阻塞可手填 |
| 5 | 任务路由（生成 vs 向量分开配置调用） | 满足 | extraction/analysis 双路由 7 个消费点 + vector 本地 ONNX 独立；档位限制保存时拦截 |
| 6 | 页面配置真实影响 API 调用与后台任务 | 部分满足（F3 缓存键缺口） | API 与 worker 同读 settings.json；fix4 同源网关；versions soft_items 含 model/protocol/endpoint，**不含 reasoning_effort** |
| 7 | 容器/宿主机地址语义 | 满足 | status notes 明示 host.docker.internal；_loopback_host 白名单；WSL 场景未提及（INFO） |
| 8 | 超时/限流/格式错误/断网 | 部分满足 | timeout 90s(15s connect) env 可调；429/5xx 退避重试；格式错误修复轮 ≤2；断网→异常→rules 降级（F4 不重试网络错） |
| 9 | 有限重试 | 部分满足 | 3 次退避重试仅 429/5xx；Timeout/ConnectError 零重试（F4） |
| 10 | 缓存与调用账本可区分 | 满足 | cache_hit/cache_source_time；generation_mode(rules/mixed/llm)；model_responded/model_identity；三表账本 |
| 11 | 成本限制 | 部分满足 | max_calls=40/operation 终身累计可 env 调（PHARMA_MODEL_MAX_CALLS）；无重置机制（F5）；cost 恒 'UNKNOWN' 无金额核算 |
| 12 | 密钥不回显/日志脱敏/测试桩 | 满足 | 见密钥清单 |
| 13 | failover 多网关/多模型切换 | 部分满足（按设计） | 智谱主→coding 端点 1113 切换真实现，8 个测试场景覆盖；非通用多厂商 failover（设计即单厂商双端点，注释声明用户 2026-09-18 授权政策） |
| 14 | 模型输出不改确定性数字 | 满足（静态确认） | narrative.py:1-12 合同；validate_findings(512)+_rounded_metric_bindings(446) 拒绝自由数字；rule_findings(881) 数字全部来自程序快照；prompt 969 行数字纪律。深度验证属 narrative 审查范围 |

---

## 五、问题清单（先反证后定级）

### F1 (P3，部署改配则升 P2)：保存的 key_file 不限路径，可作本机文件外读信道
- 位置：model_settings.py:154-156（仅 `Path(entry['key_file']).is_file()`）；入口 api.py:541-543。
- 链路：PUT /api/settings/models 设 `key_file=C:/Users/x/.ssh/id_rsa` + `base_url=https://attacker/`（https 通过校验）→ test_connection 或任意后续任务把文件内容作 `Authorization: Bearer` 发出。
- 反证（已做）：① 修复 #4 只限了 overrides 未限 save 路径——非疏漏即不一致，且 test_settings_security 未覆盖 save 路径；② api.py:17 注释称"默认仅绑 127.0.0.1"；③ docker-compose.yml:72 确为 `127.0.0.1:8765:8765`（宿主侧仅回环），deploy/entrypoint.sh:9 容器内绑 0.0.0.0——若用户改用 `-p 8765:8765` 直发端口则暴露。前端 ModelConfigForm.tsx:127 本就提供自由路径输入（部分属便利性设计）。
- 结论：默认部署下需本机访问权限（同级攻击者可直接读文件），故 P3 硬化建议：save 路径与 overrides 同样限制到 KEYS_DIR，或至少拒绝明显敏感目录；文档标注该信道。

### F3 (P3)：设置文件 reasoning_effort 不进版本指纹/缓存键 → 改档位后可命中旧缓存
- 位置：narrative.py:955（`os.getenv('PHARMA_MODEL_REASONING_EFFORT','low')`）；api.py:178-181 同样 env-only；versions.py soft_items（22-26）无 effort 项。
- 影响：effort 是 settings.json 可存字段（FIELDS）且真实改变请求体（effort_body_params），但缓存键/任务版本指纹不含设置文件值——用户在页面改 effort 后，同指纹任务返回旧缓存，"配置真实影响调用"打折。
- 反证（已做）：两处指纹均查证为 env-only；gateway.reasoning_effort 确含 settings 来源（699-703）。无其它 effort 进键的路径。确认成立。

### F4 (P3)：网络类错误（Timeout/ConnectError）零重试
- 位置：narrative.py:856-858（`except Exception: attempt_error=type; raise` 直穿）；generate:1052 捕获后 break 降级。
- 影响：瞬时网络抖动直接降级为 rules 模式；"有限重试"仅覆盖 429/5xx。
- 反证（已做）：无网络错误重试分支；结合注释"单次最长 ~4 分钟"（792）与 90s 超时，属延迟取舍但未文档化。确认为设计缺口而非未实现。

### F5 (P3)：调用预算无重置机制
- 位置：narrative.py:802-803（count 为 operation 终身累计）；grep `DELETE FROM calls` 全库无命中。
- 影响：每 operation 满 40 次后永久 MODEL_CALL_BUDGET_REACHED，仅能调 PHARMA_MODEL_MAX_CALLS 或删 RUNTIME/model_gateway.sqlite3；前端无提示入口。
- 反证（已做）：无任何清理/重置代码；属"成本上限"语义而非 bug，但对演示续跑不友好。

### F7 (P3)：overrides 携带 vendor 字段 → TypeError 500
- 位置：model_settings.py:31（FIELDS 含 vendor）→ narrative.py:767 `cls(..., **overrides)` 构造器无 vendor 形参（668-669）；api.py:62 ValueError 处理器不接 TypeError。
- 反证（已做）：前端 test() 只发 model/base_url/protocol/reasoning_effort 四字段（ModelConfigForm.tsx:89），正常 UI 不触发；仅直接 API 调用可触发。低危健壮性。

### F6 (INFO)：base_url 允许携带 query 串
- _validate_base_url（75-82）未禁 query；_safe_endpoint 记账时剥离 query（narrative 64-67），但 test_connection 的 `reason=str(exc)`（235-237）会原样回显 httpx 异常中的完整 URL（含 query）。若用户把 token 放 query（非常规用法）可在前端错误信息中回显。test_gateway_failover:147-161 已针对记账面防 query 秘密，回显面未防。

### 其余 INFO
- list_remote_models 不支持 anthropic 协议（固定 /models + Bearer，267-268）；registry 也无 anthropic 厂商，通道存在但基本不可用（手填 protocol=anthropic 时）。
- 缓存表无 TTL 无容量上限（narrative 712, 1097-1098）。
- Windows chmod 600 尽力而为（149-152，注释已声明）。
- `_loopback_host` 白名单含 `0.0.0.0`（目标地址语义特殊，影响轻微）。
- WSL 场景（Windows 宿主服务经 WSL2 访问需镜像网络/宿主 IP）文档未覆盖；仅覆盖 Docker。
- clear_vector_model 在设置文件不存在时会创建 `{}` 文件（321-324，无害）。
- conftest 设置 PHARMA_MODEL=glm-5.3-flash 保证测试确定性（无真实调用）。

---

## 六、测试对照

| 测试 | 断言要点 | 对照结论 |
|---|---|---|
| test_gateway_failover.py（169 行，10 场景） | 1113→coding 切换且账本记 endpoint；无 fallback 不退避不重试；普通 429 留原端点退避；400 不切换不重试；主端点成功不碰 coding；非智谱/非 openai 不用智谱 fallback；coding 覆盖为外部域时不接收主密钥；失败尝试留痕且无密钥；路由不借他厂密钥；GLM env 密钥供应商作用域；不跟重定向且 query 秘密不入账；网络失败有 attempt 记录 | failover/重试/密钥作用域/账本留痕均与实现一致（FakeClient 桩，无真实外呼） |
| test_settings_security.py（62 行，6 用例） | overrides key_file 路径限制（3 拒 1 收）；base_url https/回环限制；保存拒绝明文外网 http；API token 401/放行/未设开放 | 与 _sanitize_overrides/_validate_connection 一致；**未覆盖 save 路径 key_file 限制（F1 缺口所在）** |
| test_private_configuration.py（57 行） | 私有术语/主数据 JSON 动态加载+形状校验+知识版本联动 | 与模型密钥无直接关系（私有业务配置面）；其"仅虚拟产品/设备"原则满足，桩数据无真实企业信息 |

---

## 七、未实现/待验证搜索记录

- "多网关通用 failover（任意厂商 A→B 切换）"：搜索 `candidates`/`failover`，仅智谱双端点一组（narrative 829-833）——非未实现，属设计范围声明。
- "金额成本核算"：`cost` 恒 'UNKNOWN'（804/1093），无计价表——部分实现（仅有次数预算）。
- "预算重置/账单导出"：`DELETE FROM`/`max_calls=` 重置点无命中——未实现（F5）。
- "anthropic 模型清单"：list_remote_models 固定 OpenAI 形状——未实现（INFO）。
- 动态验证（真实外呼、真实 WSL/Docker 网络行为、ONNX 维度探测实测）：本次为静态审查，未实测，标"待实测"。

## 八、残留未覆盖（移交主线）

1. narrative.py 70-660 行验证器全文（validate_findings 细节、metric 绑定边界）属另一审查范围，本报告仅静态引用其合同。
2. 前端 ModelConfigForm 之外的页面（向导/报告页）对模型状态的展示真实性未逐页核对。
3. vector_switch 任务全流程（重建进度、失败恢复）仅核对入口与 set_vector_model 拒写逻辑。
4. 未实测：Windows 实机 chmod 效果、Docker 内 host.docker.internal 解析、glm-5.3 reasoning_effort 档位映射的线上行为（依据为注释所述 2026-09-22 官方文档核对）。
