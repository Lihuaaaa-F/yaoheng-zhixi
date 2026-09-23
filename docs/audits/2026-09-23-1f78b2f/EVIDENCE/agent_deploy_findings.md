# 部署/脚本/CI 子域审查证据（agent_deploy）

- 审查对象：yaoheng-zhixi @ `1f78b2f74aadebb8a48d37aa5baab70a71dfc461`（worktree `D:/yaoheng-audit-wt-1f78b2f`，只读）
- 审查人：独立审查子任务（无视觉能力，静态阅读 + 本机 Git Bash 有限实测）
- 范围：`药衡智析_增量源码交接/public_source_candidate/05_原型/deploy/`（4 文件）、`scripts/`（16 文件）、仓库根 `药衡智析启动器.bat`、`.github/workflows/`（2 文件）、`tools/verify_repository.py`、依赖锁定状态
- 分级口径：满足 / 部分 / 不满足 / 未实现 / 待实测（附静态确认）。严重度 P0-P3/INFO。
- 环境声明：本机无可用 Docker/Linux 验证环境，所有容器行为均为静态推断 + 少量 Git Bash 复现；标"待实测"处不视为产品缺陷结论。

---

## 1. 服务拓扑与启动链路

### 1.1 正式（Docker）链路 —— 满足"同一套 Compose 服务"要求

```
双击 药衡智析启动器.bat (仓库根)
  └─ powershell -NoProfile -ExecutionPolicy Bypass -File <deploy/launcher.ps1> [%*]
       └─ Resolve-Docker: Get-Command docker → 固定路径 docker.exe → WSL(Ubuntu-20.04) 回退
       └─ Ensure-Engine: docker info 失败 → 启动 Docker Desktop.exe，轮询 ≤120s
       └─ docker compose -f <deploy/docker-compose.yml> up -d     [首次=构建，日常=复用]
            ├─ rpa     (yaoheng-app:latest, command=rpa)     uvicorn pharma.synthetic_rpa:app :8090（仅容器网）
            ├─ worker  (同镜像, command=worker)               python -m pharma.worker；心跳 /data/runtime/worker.heartbeat 0.5s 刷新
            └─ web     (同镜像, command=web)                   uvicorn pharma.api:app :8765；depends_on rpa+worker service_healthy
                 端口 127.0.0.1:8765:8765（仅本机）；静态前端 frontend/dist 由 api.py:574 StaticFiles 挂载
       └─ 轮询 http://127.0.0.1:8765/health 至 worker.alive（≤180s）
       └─ GET /api/model/routes → routes.narrative.key_set 区分"核心就绪"vs"完整能力"
       └─ Start-Process http://127.0.0.1:8765
```

- 构建上下文 = `public_source_candidate/`（compose `context: ../..` 相对 deploy/，与 Dockerfile `COPY 05_原型/...` 一致，已静态核对）。
- `.dockerignore` 位于上下文根，白名单式：`*` 全排除后重新包含 `05_原型/{backend,industry_packs,assets,scripts,frontend,requirements.txt,deploy}`、`competition_configuration`、`docs/embedding_manifest.json`；再排除 node_modules/dist/.venv/.runtime/e2e-*.mjs 等。赛题原件 `00_赛题原始资料`（实测 5.5MB）不进上下文。核对通过。
- 卷：`appdata:/data/runtime`（SQLite/心跳/模板/向量模型）、`artifacts:/data/artifacts`（报告产物）命名卷持久化；`../../00_赛题原始资料/.../创灵境_考题模拟数据:/app/package:ro` 只读挂载（路径存在性已确认 PKG_EXISTS）。
- 密钥：`PHARMA_MODEL_KEY_FILE` 只传文件路径（宿主 env 注入），不落镜像/compose/仓库；deploy/ 下无 `.env`。narrative.py:684 解析顺序 显式参数→PHARMA_MODEL_KEY_FILE→PHARMA_API_KEY_FILE→设置文件。

### 1.2 开发（非 Docker）链路 —— 与正式链路并存，不冲突

```
bash scripts/bootstrap.sh   → pharma_python.sh 解析解释器 → check_dependencies.py（能力探针）
                              → 缺失时 pip install -r requirements.lock（Windows 变体剔除 uvloop）
                              → npm ci + 前端按 input-hash 增量重建 → 赛题数据摄取冒烟
bash scripts/start.sh       → manage.py start：冷启动顺序 rpa → api → worker（api 先于 worker，
                              worker 就绪=api /health 心跳，非进程存在）；stop.sh → SIGTERM 受管进程
```

manage.py 细节（正确性确认）：POSIX `/proc/<pid>/stat` start-time token 防 PID 复用；Windows OpenProcess/GetExitCodeProcess；端口被非本项目进程占用时拒绝启动且不杀未知进程；Windows 用 DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP（尝试 CREATE_BREAKAWAY_FROM_JOB）避免随控制台死亡。

---

## 2. 逐文件记录（职责 / 前提 / 失败路径）

### deploy/

| 文件 | 职责 | 前提 | 失败路径 | 判定 |
|---|---|---|---|---|
| Dockerfile | 两阶段：node:20-alpine 构建前端（npm ci）→ python:3.12-slim 装 LibreOffice-writer+fonts-noto-cjk+requirements.txt，拷 backend/industry_packs/assets/scripts/前端dist/competition_configuration/embedding_manifest | 上下文=public_source_candidate；网络可达 pypi/npmjs（国内默认源，无镜像配置） | apt/pip/npm 任一网络失败即构建失败 | 部分（见 F2/F4/F8） |
| docker-compose.yml | 单镜像三服务（web/worker/rpa），`name: yaoheng`，x-app-base 锚点，init:true，restart:unless-stopped，健康检查三套，web depends_on 条件启动 | compose v2（顶层 name）；镜像构建成功 | 构建失败→up 失败；worker 不健康→web 不启 | 满足（资源限制缺失见 F4） |
| entrypoint.sh | case 映射 web/worker/rpa→启动命令；web/worker 先校验/补齐 embedding 资产（hash 固定，可 hf-mirror），失败降级不阻断；`exec $EXEC` | /entrypoint.sh LF（已验证 LF） | embedding 下载失败→stderr 警告+词法检索降级 | 满足（小瑕疵 F8） |
| launcher.ps1 | Docker 定位→引擎拉起→compose up/stop/status/logs→健康轮询→密钥状态披露→开浏览器 | Windows PowerShell 5.1；docker on PATH 或固定路径或 WSL Ubuntu-20.04 | 每步均有中文可操作提示（见 §4 矩阵） | 部分（F6/F9） |
| 药衡智析启动器.bat | chcp 65001 + 免策略跳板，`%~dp0` 相对定位 ps1，透传 %* | bat 与仓库根同层 | 路径含空格已加引号；中文路径经 chcp 65001 | 满足 |

### scripts/（16 个）

| 脚本 | 职责与要点 | 判定 |
|---|---|---|
| bootstrap.sh | 开发环境初始化（见 §1.2）；Windows/MSYS 分支剔除 uvloop | 部分：**CRLF 提交，原生 Linux 必败（F3）**；Git Bash 实测可跑（cygwin 文本模式剥 CR，本机复现 exit=0） |
| start.sh / stop.sh | 4 行 exec 跳板至 manage.py | 满足 |
| pharma_python.sh | PHARMA_PYTHON→venv(两布局)→系统 python 统一解析 | 满足 |
| manage.py | 进程编排骨干（token 存活校验、端口预检、冷启动顺序、worker 心跳门控） | 满足（fix8 语义正确：Web 可开≠后台可用） |
| check_dependencies.py | 16 模块安装+版本锁定+能力探针（pydantic 校验/duckdb 查询/jieba 分词/FTS5 等） | 部分：探针集不含 openpyxl → F1 盲区 |
| check_environment.py | 环境/前端新鲜度(hash)/字体/数据包/锁存在性报告，--strict 失败退出 | 满足（Windows LibreOffice 明示"另行安装"） |
| fetch_embedding.py | 按 docs/embedding_manifest.json 的 sha256 下载/校验 bge-large-zh-v1.5（onnx+tokenizer），PHARMA_EMBEDDING_DIR 外置只校不写，PHARMA_EMBEDDING_MIRROR=1 走 hf-mirror | 满足（manifest 无 size 字段，进度无法预估，INFO） |
| verify.py | 当前运行验证器：干净树强制（文档-only 后代放行）、run_id/commit/attempt 绑定、7 维度（environment/regression/scenarios/retrieval/rpa/browser/model_live）、退出码 0/1/2 | 满足 |
| run_acceptance.py | 环回限定验收：3 合成场景(+私有)、任务哈希绑定、RPA 双确认幂等 | 满足（属评测链，非部署链） |
| verify.sh | verify.py 的 bash 包装（PYTHONPATH/TMPDIR/OTEL 环境） | 满足 |
| generate_scenarios.py | 兼容入口转发 run_acceptance.main | 满足 |
| probe_glm.py | 模型网关显式探针（文本/JSON/工具/流式；无密钥→BLOCKED 不误报） | 满足 |
| build_inputs.py | 前端输入指纹（src/public/配置文件 sha256）供增量构建 | 满足 |
| build_demo_deck.py | 验收 run → 10 页 PPTX（内容工具，非部署链） | 未深入（范围外，静态无异常） |
| generate_synthetic_plant2_details.py | 中药二厂合成明细生成（数据工具） | 未深入（范围外） |

### CI / 工具

| 文件 | 内容 | 判定 |
|---|---|---|
| .github/workflows/application.yml | ubuntu-24.04，工作目录=05_原型（中文路径）；venv + `pip install -r requirements.lock` + `npm ci --ignore-scripts`；跑 `pytest -q tests`（38 个测试文件）+ `npm run build` + `node --test record_demo_20260918.test.mjs`（纯单元，无浏览器）；env 清空三种 API key；action pin 到 commit SHA | 部分：应用面覆盖良好，但 **不构建 Docker 镜像、不跑 `docker compose config`（F5）**；lock 缺 openpyxl 使 CI 环境与生产不同（F1） |
| .github/workflows/repository-contracts.yml | 5 分钟，跑 tools/verify_repository.py | 满足 |
| tools/verify_repository.py | 只读仓库契约：current_run.json 与 manifest/verification 的 run_id/commit/场景映射一致、competition_ready 须人工 PASS、媒体 sha256、README/docs 本地链接不破 | 满足（自声明"非应用/模型/人工验收"，边界诚实） |

### 依赖锁定

| 项 | 状态 |
|---|---|
| frontend/package-lock.json | 存在，lockfileVersion 3，127 个 resolved 条目；Dockerfile `npm ci`、bootstrap `npm ci --ignore-scripts`、CI `npm ci` 三处均走锁。**满足** |
| backend requirements.txt（16 行） | 范围约束（>=,<），jieba 精确 ==0.42.1；**Dockerfile 用它装生产依赖** |
| backend requirements.lock（129 行） | 全 `==` 精确锁定；CI 与 bootstrap 默认用它。**不完整：缺 openpyxl（F1）**；含 uvloop==0.22.1（Linux 专属，bootstrap Windows 分支已处理） |
| backend pyproject.toml / uv.lock | **未实现**（搜索词 `pyproject.toml`、`uv.lock`、`setup.py`，backend/ 下 0 命中）——项目用 requirements 双文件体系，非缺陷，如实记录 |
| requirements-docs.lock | 3 行（python-pptx、XlsxWriter，注释明示"可选 deck 工具"） |

---

## 3. 发现清单（严重度排序）

### F1 [P1] requirements.lock 缺 openpyxl → 锁定环境下"数据中心 xlsx 导入"运行时 ImportError，且 CI/自检双盲区
- 证据：`requirements.txt:16` 有 `openpyxl>=3.1,<4`；`grep openpyxl requirements.lock` 0 命中（129 行全量核对）；使用点 `backend/pharma/data_import.py:192,210` 函数内 `import openpyxl`（懒导入，失败=500，无优雅降级）；`tests/` 中 `xlsx|openpyxl|load_workbook` 0 命中（无测试覆盖）；`check_dependencies.py` PROBES 无 openpyxl（自检不报）。
- 影响面：CI（application.yml 只装 lock）、bootstrap 默认路径（Linux 装 lock 原文、Windows 装剔除 uvloop 的变体，两者都无 openpyxl）——数据中心导入 xlsx 的功能在这两条受支持路径上静默损坏；README 明示"数据接入走『数据中心』向导"为文档化功能。Docker 正式镜像装 requirements.txt 反而可用（与 F2 叠加：CI 测的依赖集 ≠ 生产运行的依赖集）。
- 反证尝试：openpyxl 是否可经其它锁定包传递安装？chromadb/llama-index/matplotlib 等依赖树均不含 openpyxl（lock 中无任何行声明它）→ 反证失败，缺陷成立。
- 修复建议：requirements.lock 增 `openpyxl==<当前镜像内版本>`；check_dependencies.py PROBES 增 openpyxl 探针；补一条 xlsx 导入冒烟测试。

### F2 [P2] 生产镜像依赖不可复现：Dockerfile 用 requirements.txt（范围约束）而非 requirements.lock；且"pip/npm 配国内镜像"的注释与实现不符
- 证据：`deploy/Dockerfile:39-40` `COPY 05_原型/requirements.txt` + `pip install -r`；全文件无 `PIP_INDEX_URL`/`pip.conf`/`.npmrc`/`--registry`（grep 0 命中，frontend/ 下也无 .npmrc）；而 `docker-compose.yml:15` 注释称"apt 已用国内源，pip/npm 配国内镜像，干净评测机可直接构建"——实际仅 apt 换了 tuna 源（Dockerfile:32）。
- 影响：同一 commit 两次构建可能得到不同依赖版本（范围解析漂移）；CI 验证的是 lock 集合，镜像运行的是非 lock 集合；国内无代理评测机上 pip(pypi.org)/npm(npmjs.org) 直连慢或失败的构建风险由注释掩盖。
- 反证：compose build-args 仅传代理（HTTP_PROXY/HTTPS_PROXY），无镜像源注入 → 反证失败。

### F3 [P2] scripts/bootstrap.sh 以 CRLF 提交（git 索引即 CRLF）→ 原生 Linux 上 README"方式二"必败
- 证据：`git ls-files --eol` 显示 `i/crlf w/crlf`（对照 entrypoint.sh 为 i/lf）；.gitattributes 无该文件规则。Linux bash 不剥离 CR：`set -euo pipefail\r` 报 invalid option、变量赋值尾随 `\r` 进入值导致解释器路径失效。
- 实测：本机 Git Bash（cygwin 5.3.15）文本模式剥 CR，最小复现 exit=0 —— 开发者环境可用，掩盖了问题。
- 影响面：Linux 评测机按 README:34-40 走"方式二（开发环境）"直接失败；方式一（Docker，推荐）不受影响（entrypoint.sh 为 LF）。
- 反证：是否有 Linux 调用方？CI 不调 bootstrap（直接 pip install）；Docker 镜像不执行它 → 仅 README 文档路径受影响，维持 P2。

### F4 [P2] 容器以 root 运行且 compose 无资源限制
- 证据：Dockerfile 全文无 `USER`；/data 运行时目录 root 属主；compose 无 `deploy.resources`/`mem_limit`/`cpus`。审查要点"非 root""资源限制"两项不满足。
- 缓解：端口仅 127.0.0.1 绑定、rpa/worker 不暴露、单机部署场景风险有限。反证：无任何 USER/chown 痕迹 → 成立。

### F5 [P2] CI 零覆盖部署面：不构建 Docker 镜像、不校验 compose/entrypoint
- 证据：application.yml 仅 venv+pytest+npm build+node 单测；无 `docker build`/`docker compose config` 步骤。Dockerfile COPY 路径、.dockerignore 白名单、compose 语法、entrypoint 映射的回归只能靠人工在评测机首次暴露。
- 一致性对照：本地一键启动入口=compose，CI 却完全不触碰该链路——"CI 绿"不能推"可部署"。
- 反证：repository-contracts.yml 仅查文档契约 → 无部署覆盖，成立。

### F6 [P3] launcher WSL 回退硬编码 Ubuntu-20.04；WSL 模式引擎未运行的补救动作错误
- 证据：launcher.ps1:39 `$distros -contains 'Ubuntu-20.04'`；非该名（Ubuntu-22.04/Debian/自定义）→ 落入 `throw 'DOCKER_NOT_INSTALLED'`，提示"未检测到 Docker，请安装"（用户实际可能有其它发行版里的 docker，误导）；Ensure-Engine(69-84) 在 WSL 模式下仍启动 Windows `Docker Desktop.exe`——发行版内 docker 引擎未运行时该补救无效。
- 反证：典型 Docker Desktop 场景 docker.exe 在 PATH，不走该分支 → 维持 P3（边缘场景）。

### F7 [P3] worker 首启 embedding 下载与 depends_on 门控叠加，慢网下首启体验为"失败路径"
- 证据：entrypoint.sh:15-19 worker 启动前同步下载 bge-large-zh-v1.5（onnx 量化模型，manifest 无 size 字段，量级估计数百 MB，待实测）；worker healthcheck 宽限 ≈ start_period 30s + retries 8×15s = 150s；web `depends_on: service_healthy`；launcher 再等 180s。下载超 150s → worker 一度 unhealthy → web 不启 → launcher 180s 超时报错（提示语已含"首次启动在下载向量模型（可稍等后在浏览器直接访问）"）。模型落 `/data/runtime/models`（命名卷）持久，二次启动 `--check-only` 秒过（幂等设计正确）。
- 顺序性反证（并发下载竞态）：web 仅在 worker healthy 后启动，而心跳只有在 worker 主循环开始（即其 embedding 下载完成）后才写 → web 的 check-only 不会与 worker 下载并发，共享卷写竞态被 depends_on 顺序消解。成立为"慢而非错"。

### F8 [P3] Dockerfile 无 CMD；entrypoint `exec $EXEC` 未引号
- `docker run yaoheng-app`（不经 compose）→ $1 为空 → `EXEC=""` → `exec` 无参为 no-op → 容器立即退出码 0。仅 compose 用法正确。`exec $EXEC` 依赖分词，带空格参数的自定义命令会被拆散（当前命令集不受影响）。

### F9 [P3] 更新代码后启动器无重建入口
- launcher 只 `up -d`，镜像 tag 固定 `yaoheng-app:latest` 已存在即复用（README:31 已声明"已有镜像直接复用"为设计）。用户拉取新版仓库后双击启动仍运行旧代码，需手动 `docker compose build`。首次/日常同入口的目标达成，但"升级"路径缺失且无提示。

### F10 [INFO] /health 语义正确落实"Web 存活≠业务就绪"
- api.py:66-74：`worker.alive = 心跳文件 age < 180s`；心跳由 worker.py:129 dispatch 线程 0.5s 刷新（报告/模型阻塞不影响）。compose web healthcheck 与 launcher 轮询均以 `worker.alive` 为判据，而非 TCP/HTTP 存活；模型密钥可用性另行经 `/api/model/routes` → `routes.narrative.key_set`（narrative.py:778-787 返回形状与 launcher.ps1:130 访问路径核对一致）。心跳 `write_text` 非原子，半写瞬间读方 `float()` 抛错→/health 500，由 healthcheck retries（10×15s）吸收，未观测到实例。

### F11 [INFO] 安全面（正面确认）
- 端口默认 `127.0.0.1:8765:8765`；rpa/worker 无 ports；密钥仅文件路径注入，compose/env/.env 均无明文密钥；CI actions pin 到 commit SHA（11bd719…=checkout v4.2.2）+ persist-credentials:false；CI 清空三种 API key env。注意：`PHARMA_API_TOKEN` 默认空=本机无鉴权（loopback 绑定下可接受；若设置 token，launcher 的模型状态探测会 401→落入 catch 打印温和警告，不误导）。

### F12 [INFO] 优雅退出与任务恢复
- compose `init: true`（tini 转发信号）；uvicorn 处理 SIGTERM；worker 无自定义信号处理，`docker compose stop`（默认 10s）SIGTERM 即死/SIGKILL，被杀任务的 job 停在非终态——jobs.py:102-105 `next()` 取"非 SUCCEEDED/DEGRADED/FAILED"的最老任务，worker 重启后自动重跑，恢复语义闭环。`manage.py stop` 本地路径 SIGTERM+10s 轮询。

### F13 [INFO] 本地 manage.py 与 Docker 是两套并行运行方式
- 不违反"快捷方式与启动脚本启动同一套 Compose 服务"：Windows 桌面链路（bat→ps1→compose）自洽；start.sh/manage.py 是文档化的开发链路，健康判据（心跳）、降级披露与 Docker 链路同构。

---

## 4. 错误场景矩阵（启动器/compose 链路）

| # | 场景 | 行为（静态判定） | 判定 |
|---|---|---|---|
| 1 | 未装 Docker | DOCKER_NOT_INSTALLED → "请先安装 Docker Desktop（WSL2 后端），见 README「部署」" | 满足 |
| 2 | 引擎未运行 | 自动启动 Docker Desktop，≤120s 轮询；超时提示查 WSL2/虚拟化 | 满足（WSL 模式补救错，F6） |
| 3 | 首次构建网络受限 | up -d 失败 → 自动 `logs --tail 40` + 三条常见原因（网络/端口/磁盘） | 满足；但 pip/npm 无镜像加大国内失败率（F2） |
| 4 | 8765/8090 端口占用 | 无预检；compose 报错后靠提示文案"②端口被占用" | 部分（本地 manage.py 有 occupied() 预检可对照） |
| 5 | 首启 embedding 下载慢 | worker 迟迟不健康→web 不启→180s 超时，提示"稍后直接访问" | 可恢复的失败体验（F7） |
| 6 | 重复双击 | `up -d` 幂等（compose 项目名 yaoheng 固定），README 明示不重复起一套 | 满足；构建中二次双击→compose 项目锁串行化，待实测 |
| 7 | 密钥未配置 | 核心就绪 + 黄色降级提示（routes.key_set=false） | 满足 |
| 8 | stop 后再启动 | unless-stopped 尊重手动 stop；命名卷保数据 | 满足 |
| 9 | 仓库更新后双击 | 旧镜像继续运行（F9） | 部分 |
| 10 | WSL 发行名≠Ubuntu-20.04 | 误导性"未安装 Docker"（F6） | 不满足（该子场景） |
| 11 | 路径含中文/空格 | bat 引号+%~dp0、chcp 65001；WSL 路径换算 /mnt/<盘>；数组传参不经 shell 分词 | 待实测（静态无硬伤；本 worktree 中文路径下所有只读操作正常） |
| 12 | 心跳文件半写 | /health 偶发 500 → healthcheck retries 吸收 | INFO |
| 13 | worker 被强杀 | 非终态 job 重启重跑（jobs.next） | 满足 |
| 14 | Linux 跑 bootstrap.sh | CRLF 崩溃（F3） | 不满足 |
| 15 | lock 环境导入 xlsx | ImportError→500（F1） | 不满足 |

---

## 5. 判定统计

| 检查项 | 判定 |
|---|---|
| Dockerfile：多阶段/前端构建进镜像/npm ci/层缓存 | 满足 |
| Dockerfile：中文字体（PDF）/LibreOffice | 满足（fonts-noto-cjk + 项目 assets/fonts 双保险；libreoffice-writer） |
| Dockerfile：pip 依赖锁定 | 不满足（用 requirements.txt 范围约束，F2） |
| Dockerfile：非 root | 不满足（F4） |
| Compose：服务清单/端口绑定/持久卷/重启策略/密钥注入 | 满足 |
| Compose：健康检查语义/depends_on 条件 | 满足 |
| Compose：资源限制 | 不满足（F4） |
| entrypoint：初始化顺序/幂等/降级 | 满足 |
| entrypoint：worker 门控 | 满足（经 compose depends_on+心跳实现） |
| 启动器：同一套 compose/未装/未运行/幂等/提示可操作 | 满足 |
| 启动器：端口预检/WSL 发行名/升级路径 | 部分-不满足（F4 场景、F6、F9） |
| CI：后端测试+前端构建+锁定安装 | 满足 |
| CI：与部署面一致性 | 不满足（零 Docker 覆盖，F5） |
| 依赖锁定：frontend | 满足 |
| 依赖锁定：backend lock 完整性 | 不满足（缺 openpyxl，F1） |
| "Web 存活≠业务就绪" | 满足（心跳+密钥分级披露） |

统计：满足 12 / 部分 3 / 不满足 5（F1、F2 之锁定面、F4 两项、F5、F3-F6 场景项）/ 待实测 2（中文路径全链路、compose 并发锁）。
严重度：P1×1（F1）、P2×4（F2、F3、F4、F5）、P3×4（F6-F9）、INFO×4。

## 6. 未覆盖残留（移交说明）

- build_demo_deck.py、generate_synthetic_plant2_details.py 仅静态浏览头部与逻辑框架，未逐行（内容生成工具，非部署链）。
- backend/ 应用逻辑（api/reports/ingestion 等）仅追踪部署相关触点（/health、静态挂载、模板目录、心跳、LibreOffice 调用），非本子域完整审查。
- 所有 Docker 运行时行为（构建成功、健康检查实际通过、首启时长、compose 项目锁并发）本机无 Docker 环境未实测。
