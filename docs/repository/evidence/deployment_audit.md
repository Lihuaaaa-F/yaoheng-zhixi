# 部署、验收回执与模型边界只读审计

审计基线：`codex/core-industry-20260917@cdd9cb90d1f2e38fac429e82d89e46765e2317d2`，2026-09-19。应用根为 `药衡智析_增量源码交接/public_source_candidate`，以下相对路径均以此为根。审计读取固定提交及新工作树；未安装依赖、启动服务、调用模型、读取密钥、修改应用源码或执行任何清理/删除脚本。主审随后进行的文档修订不属于本固定提交的原始状态。

## 判断

当前代码相较旧包确有部署修复，不能把旧问题原封不动写成现存缺陷。正式回执记录七个自动维度和七个场景通过，但唯一索引中的七个任务 ID 全部与本次 manifest/verification 不符；这需要修正文档索引，不能以换 ID 代替重跑、补造缺失的回执链或真人评分。GitHub 没有本提交的 CI 检查，已有 PASS 是开发环境自动验收记录。公开代码的默认路径支持合成行业包；完整原题、PDF、混合检索和真实模型各有额外条件，不能把基础环境 PASS 当作净机全功能部署证明。

## 可立即修正的文档与索引问题

### D1：唯一验收索引的七个任务 ID 错配

证据：固定提交的 `docs/current_run.json.scenarios` 与 `docs/validation/release_20260918_5974275/manifest.json.scenarios`、同目录 `verification.json.scenarios` 逐项比较。后两者七个任务一致，前者七个均不同。仅输出无敏感内容的任务标识：

| 场景 | 原索引 ID | manifest 与 verification 一致的 ID |
|---|---|---|
| mechanical | a882b52a2081481481b6db959639083c | bd269b405996469292ef8521e8507568 |
| chemical | 6f83cdd441134e6ab0f78bcc4d332b97 | 44aa6367278a4400838afb5a95ee3b68 |
| pharma_synthetic | eea07536f5a54d1eb90c595b6e16ce27 | d50793d5345e41b08bd985a6d6f350d9 |
| S1 | 28c10accfe4c47f3bac5fe72de0e2120 | e2f1bdf2ed764c04b79fad254c7df948 |
| S2 | 69f3e416e8fa4d78862eaf74a4d37a53 | f33029bd3f63466a9f955f009fe75cf8 |
| S3 | 0c270a2606f14cff8c3cbbc4b29163c0 | 64a710ab34084876b49d3f346039b229 |
| Q2 | b494f0d51f3f46a8bb9b9b4404afd61d | c79ee1a3d13d4410817445fcf90cd206 |

建议本轮只同步索引到一致的 manifest/verification，原七条保存在 `superseded_index_entries` 并标记 `origin: UNVERIFIED`；不能断言它们来自某个其他运行。保留实际 `run_id`、`tested_code_commit`、历史 `automatic_status: PASS` 和 `human_review: PENDING`。新增 `index_reconciliation` 说明源文件、仅索引纠正以及 `rerun_performed: false`。另加 `receipt_linkage: PARTIAL_RUN_LEVEL_ONLY` 并说明是模型/检索/RPA/浏览器回执的任务级与产物级关联不足，避免将已一致的 manifest/verification 任务关联也说成不一致。

### D2：README 仍保留已被用户后续授权覆盖的端点禁令

`README.md:54` 仍写“Coding Plan 凭据禁止用于应用运行时”；`backend/pharma/narrative.py:586`（完整路径为 `05_原型/backend/pharma/narrative.py`）、`docs/current_run.json`、`docs/ZCODE_HANDOFF.md` 和 failover 测试均按 2026-09-18 用户授权实现“主端点优先，1113 额度不足才暂时切 Coding 端点”。应统一文档到已有授权，不应凭过期 README 停用授权功能，也不应擅自扩大授权。

准确描述：每次新的逻辑调用首先使用配置的主端点；其返回 1113 时才转授权的备用端点；普通 429/5xx 重试并不会直接触发该切换；`PHARMA_MODEL_CODING_BASE_URL=''` 可禁用备用。无需为文档同步进行真实模型调用。

## 回执能证明什么

1. `release_20260918_5974275/verification.json` 记录 environment、regression、scenarios、retrieval、rpa、browser、model_live 七维 PASS，七个场景 PASS；真人仍 PENDING，`competition_ready: false`。存在 `DEGRADED` 任务状态不自动推翻该记录：任务状态还包含真人未完成等边界，应查看各维度原因。
2. 实测代码提交为 `5974275ca90d8ba5dd524c5320845c3906348dfa`。固定 HEAD 是其后一个文档提交，两者仅九个文档/回执文件变化；使用 Git `--name-only -z` 确认无代码、行业包或依赖变化。不能仅因 SHA 不同把回执判为代码过期。`verify.py` 也明确允许仅文档后继提交。
3. 本次模型回执七场景均声明真实生成、请求与返回模型 `glm-5.3-flash`、身份 VERIFIED、非零 usage；其中有界修复后的最终 PASS 与保留历史格式失败原因并不矛盾。各场景记录的逻辑调用数合计 13。
4. 回执未保留每次调用的 endpoint 与 call_id 映射。因此“13 次 narrative 经 Coding、4 次 decision 经主端点”的端点分布是开发记录陈述，不能只靠当前公开回执独立复算。应后续导出脱敏逐调用/逐尝试凭据：run、scenario、job、call、attempt、请求/返回模型、端点 origin/path、HTTP/供应商错误码、usage、最终状态；不附密钥、完整提示词或原始响应正文。
5. `verify.py:check_receipt` 仅核对 run_id、commit 和回执顶层状态，不把检索/模型/RPA/浏览器项与 manifest 的 job_id、产物哈希逐项连接。`run_acceptance.py` 也未禁止同 run_id 重用覆盖回执。这是同运行内不同尝试被混合的风险，并非已经证明此次回执被伪造。未来用唯一 attempt ID、不可覆盖的运行目录和明确任务/产物映射解决。
6. browser 回执明确区分 8 项真实 UI 检查与 10 项 mocked 合同检查，并说明报告任务命中叙事缓存；不能称 18 项全都验证真实模型/下载/RPA。记录视口为 1440×1000、390×844，不等于已证明 1366×768。
7. RPA 回执证明 `SIMULATED_SENT` 与重复确认保持同任务，真人应答为 NOT_ENTERED；不能据此声称真实微信已发送、责任人已处理或整改完成。
8. `static_delivery` 指向较早的 `delivery_20260918_47c5806`；视觉记录还有更早来源，且保留未完成布局项。应保留它们的原始来源，不把静态交付统一重标为当前 GLM 运行产物。

## GitHub CI 与可复核程度

固定提交树没有 `.github/workflows/`。GitHub commit checks API 返回 `total_count: 0`，commit status 返回 `total_count: 0`、`statuses: []`、`state: pending`。因此当前没有可引用的 GitHub CI 全绿记录。Actions workflows API 受工具端点限制未读取；目录树和该提交检查结果已足以支持“没有此提交的 CI 结果”，不推断未读取的运行历史。

来源：

- https://api.github.com/repos/Lihuaaaa-F/yaoheng-zhixi/commits/cdd9cb90d1f2e38fac429e82d89e46765e2317d2/check-runs
- https://api.github.com/repos/Lihuaaaa-F/yaoheng-zhixi/commits/cdd9cb90d1f2e38fac429e82d89e46765e2317d2/status
- https://github.com/Lihuaaaa-F/yaoheng-zhixi/compare/5974275ca90d8ba5dd524c5320845c3906348dfa...cdd9cb90d1f2e38fac429e82d89e46765e2317d2

本审计进行了固定文件解析、七场景 ID 比较、Git 文档差分及源代码审查，没有本机重跑 222 passed/1 skipped 或净机安装。现有回执是开发者提交的历史证据，不是本次审计重新产生的测试结果。建议后续补无密钥合成包 CI，再将模型、图形、真人验证独立运行；不要为了本次索引修订重调付费模型。

## 默认启动与完整比赛模式

正确工作目录是应用根；`bash 05_原型/scripts/bootstrap.sh` 然后 `bash 05_原型/scripts/start.sh`，公开 clone 无需旧 `prepare_team_workspace.py`。默认 API、worker、模拟 RPA 为本地模式，默认三个合成行业上下文独立，原题数据需按 README 显式配置启用。

| 层次 | 代码实际行为 | 验收边界 |
|---|---|---|
| Python | 本项目 venv/显式 PHARMA_PYTHON 优先，按依赖探针复用；不足时项目 venv 使用锁文件安装 | 不应据此声称已在干净 Ubuntu 安装成功 |
| 前端 | node_modules 单独核对 lock hash，dist 核对源码输入 hash | 已有 dist 仍需 npm/node_modules，完全离线前需预备 |
| 默认数据 | bootstrap 构建三个合成包，不拿合成合同校验比赛数据 | 不等于三官方场景已在本机启用 |
| PDF | 依赖 LibreOffice/soffice；逐页检查需要 pdftoppm | 环境探针只报告这些命令存在情况，不纳入基础 PASS |
| 检索 | 嵌入模型仅 check-only；缺少时关键词降级，不下载大模型 | 基础启动不等于满足语义+BM25 正式验收 |
| 模型 | 无密钥可确定性降级；真实生成另测 | 基础环境 PASS 不等于 model_live PASS |
| 当前运行核验 | verify 读取本地 JobStore、产物和既有回执，同时跑环境/回归 | 克隆不会带运行数据库，不能直接拿别人的 manifest 重新绿灯 |
| 源码 ZIP | revision_record 有源文件指纹回退；verify.py 仍要求 Git HEAD/祖先关系 | ZIP 可启动不等于 ZIP 无 Git 时支持完整 current-run verifier |

Ubuntu/WSL 上的一个未覆盖组合：`bootstrap.sh:15` 在发现 Windows `.venv/Scripts/python.exe` 时可能跳过 Linux venv 创建，而 `pharma_python.sh` 在 WSL 不选择该解释器。于是可能回落系统 Python 后尝试 pip。跨系统复制旧工作目录时，应按平台校验 venv；不能复用 Windows venv，也不能用 `--break-system-packages` 掩盖。此项来自分支条件审查，未在本环境伪造跨系统目录复现。

## 后续代码修复项：本轮不修改业务源码

### C1：验收脚本“仅模拟”边界只有注释

`05_原型/scripts/run_acceptance.py:11` 接收任意 `--base-url`；34 行注释称 localhost simulator only，39 行直接调用任务确认。未验证 URL 为 loopback，也未核对目标服务实际处于模拟模式。故该脚本被指向另一个服务时，会先确认任务，再在事后检查 `SIMULATED_SENT`，事后失败不能撤回已下发动作。

后续应先要求 loopback 地址和服务端明确的 simulator 能力标识，再执行自动确认；远端测试必须有单独显式模式。本审计没有运行该脚本，没有证据说当前回执发送了真实任务。

### C2：授权备用端点没有按供应商和协议限制

`narrative.py:589` 默认设置智谱 Coding URL，688–696 行把它附加到任何主端点候选列表，并复用相同 headers、key 和 body。README 又声明支持其他 OpenAI 兼容厂商及 Anthropic。若其他供应商的主端点返回 1113，当前通用路由也会向智谱发送该凭据/请求；Anthropic body 亦不适用于默认 OpenAI 协议备用。

当前配置的智谱主端点→同供应商授权 Coding 端点不因此自动违规。本问题是可切换网关的配置隔离缺口，应将默认备用限定于已确认的智谱主端点/协议，并支持每路由显式备用配置与独立凭据；加入其他厂商返回 1113 时不得进入默认智谱备用的测试。

### C3：失败尝试端点记账不足

`narrative.py:665,699,722` 的 used_endpoint 只在成功响应后改变。若主端点 1113 后备用也失败，最终账本可能仍记录主端点；每个逻辑调用只有一行，也不保留每次尝试的错误码。补逐尝试脱敏账本，不把最终成功端点与完整调用路径混为一谈。

### C4：进程启动仍需故障恢复验证

`scripts/manage.py` 顺序启动本地组件，但未见跨进程管理锁、原子状态写入及后续组件启动失败时的完整回滚。已有端口冲突拒绝和本地绑定是积极措施；不能因此直接声称并发双启动、部分启动失败都已通过。后续用隔离运行目录与自有端口做限定反例，不能杀死未知占用进程。

## 已修复旧问题与保留边界

- bootstrap/environment 已共享 `build_inputs.py`，解决旧版输入指纹不一致。
- npm 依赖有独立 lock hash，不再仅因 node_modules 目录存在就认定兼容。
- `verify.sh` 先求绝对脚本路径再改变目录，旧相对路径错误已修。
- 依赖探针不再把 False 当通过，SQLite FTS5 包含建表、写入和查询能力检查。
- `verify.py` 要求 manifest，与实际 run/commit 绑定，真人评审始终独立，退出码 0/1/2 区分通过、失败、未完成。
- 用户 2026-09-18 已明确授权同一公开仓库保留本次比赛材料及静态交付；不沿用旧“不得发布原题”结论。赛题原件保持只读源字节，不能把授权扩大到密钥、运行数据库、恢复备份或未来真实企业资料。
- 本轮不删除任何文件，不运行带 cleanup 的旧打包流程；只读审计结论不构成清理授权。

本轮最小可交付修订应是 D1/D2 及证据边界说明。C1–C4 放入明确后续修复清单并保留当前代码和历史回执原样；无需通过不必要的模型重跑或依赖安装为文档修订制造新证据。
