# API与运维

默认127.0.0.1:8765；本地单体演示，没有公开互联网认证服务。不要把context隔离当作跨租户鉴权。

| 入口 | 合同 |
|---|---|
| GET /api/industry/catalog | 已安装行业及企业context_id、能力与缺项 |
| GET /api/catalog?context_id=… | 合法产品/工厂/期间/单位 |
| POST /api/analyses | context_id、factory、product、month、analysis_type、basis，返回固定上下文快照 |
| GET /api/benchmarks | context_id、product、month、analysis_type、basis、left、right；季度贯通 |
| POST /api/reports | 与analysis一致；同版本完成结果复用 |
| GET /api/jobs?context_id=… | 本上下文任务；执行状态与解释来源/真人审核分别显示 |
| GET /api/artifacts/{id} | 终态可下载，DEGRADED允许；真实哈希漂移拒绝，preview明确草稿 |
| POST /api/reports/{id}/reviews | 真人署名、0—5归因、章节/可读性/版式；实际产物绑定 |
| GET /api/reports/{id}/acceptance | 重算；产物变化使旧审核STALE |
| POST /api/kb/search | context_id、query、product、month、factory及检索模式 |
| POST /api/actions | snapshot_id、标题/负责人/来源/优先级、建议/核查对象/证据/岗位/期限依据 |
| PUT /api/actions/{id} | 合并后仍通过完整行动合同；未确认可编辑 |
| POST /api/actions/{id}/confirm | 当前payload_hash确认；仅一个outbox |
| POST /api/actions/{id}/acknowledge | 已送达任务的本人署名责任确认；不等于整改完成 |
| POST /api/actions/{id}/refresh | 查询模拟API，严格响应合同；协议错误不抹掉已证明状态 |

发送前确认与责任人整改确认不同；GET返回sent/confirmed/completed分别保存，模拟微信不是真实集成。重启SENDING先GET核对，不盲目重发。旧runtime整体隔离，不恢复待发队列。本轮恢复仅复用兼容依赖和只读模型，原题资料路径由PHARMA_DATA_PACKAGE指定；当前授权原件及复现配置也随仓库交付。

bootstrap采用同一build_inputs.py指纹，node_modules锁指纹不一致则npm ci。缺模型允许基础降级，外置模型不改写。进程管理仅操作记录PID+启动标识。生成与分析按上下文固定，无全局行业切换。

基础测试清除开发者密钥；实调单独用受控.env。verify.sh必须传当前manifest，退出0/1/2=自动通过/失败/未完成；不能用历史browser覆盖本轮，也不预置ENV PASS。

报告任务同时绑定生成校验合同、解析器、术语内容、分目的检索策略、检索器与嵌入版本；任一漂移会新建任务，运行中旧绑定任务拒绝复用。Git源码记录commit；无Git公开归档记录明确的source指纹与commit=null，不查询HOME的仓库。

## 前端构建与浏览器验证

以下命令均从应用根 `药衡智析_增量源码交接/public_source_candidate` 执行。`bootstrap.sh` 完成依赖锁校验、前端编译并写入 `.build-inputs`；单独 `npm run build` 不写该验收指纹。源码或锁文件修改后重新运行 bootstrap，再用环境探针确认 `frontend.dist_matches_sources=true`。`check_environment.py --strict` 的退出码只覆盖依赖能力与构建匹配；还须查看其 LibreOffice、字体等字段，PDF与浏览器的真实可用性由对应导出/浏览器流程验证。

```bash
bash 05_原型/scripts/bootstrap.sh
bash 05_原型/scripts/start.sh
05_原型/.venv/bin/python 05_原型/scripts/check_environment.py --strict
```

若显式复用 `PHARMA_PYTHON`，上面的 Python 命令改用该兼容解释器；bootstrap 不保证另建 `.venv`。WSL 不能复用 Windows venv。

开发热更新在单独终端运行（Ctrl+C 停止该 Vite 进程）：

```bash
cd 05_原型/frontend
npm run dev -- --port 5178 --strictPort
```

开发代理固定指向 API `127.0.0.1:8765`，开发服务器默认端口原为 5173；上面明确设为 5178，与模拟测试默认一致。若仅需交付运行，访问 8765 上由 FastAPI 提供的实际 `dist`，不必启动 Vite。修改 `PHARMA_API_PORT` 不会自动改 Vite 代理。

另一终端从应用根运行模拟浏览器合同测试。所有 API 由测试脚本拦截，不需真实模型或题包；Vite 必须已启动。

```bash
TMPDIR=/tmp PHARMA_E2E_URL=http://127.0.0.1:5178 \
  PHARMA_E2E_OUT=/tmp/yaoheng-context-ui npm --prefix 05_原型/frontend run e2e
```

真实 API 浏览器测试使用受管服务和当前构建：

```bash
TMPDIR=/tmp PHARMA_E2E_URL=http://127.0.0.1:8765 \
  PHARMA_E2E_OUT=/tmp/yaoheng-live-ui npm --prefix 05_原型/frontend run e2e:live
```

两脚本都使用本机已安装的 Chromium：通过 `PHARMA_CHROME_PATH` 指定可执行文件，或由 `PLAYWRIGHT_BROWSERS_PATH` 指向已有的兼容 Playwright 浏览器缓存。bootstrap 只安装 npm 包，不下载浏览器；缺浏览器应记录阻断，不能因 Playwright 包存在就写浏览器 PASS。真实测试仅使用合成企业，会提交机械报告；有凭据时可能触发应用模型调用。测试输出的 `qa.json` 仅证明所列页面/接口断言，提交成功不等于报告完成；图表、字体、解释和页面高度稳定后，仍须实际查看全页截图。演示素材可另运行 `npm --prefix 05_原型/frontend run demo:record`，录像需要兼容的本机 FFmpeg/Playwright 录像依赖，不能以生成视频文件代替内容检查。

## 公开副本与配置

全新公开源码无需题包或模型密钥，默认具备三份独立合成企业。`.env` 仅从 `05_原型/.env` 读取，shell 已导出变量优先；不执行其中的 shell 命令。无密钥试验应使用未恢复 `.env` 或旧 runtime 的独立副本；若同时证明无题包模式，需明确另导出仅源码与合成包的最小副本，同时确认没有继承 `PHARMA_API_KEY`、`GLM_API_KEY`、`ZHIPU_API_KEY` 或密钥文件配置。缺密钥、嵌入模型、PDF工具分别影响相应能力，不应宣称全部模型/混合检索/PDF维度通过。

`run_acceptance.py` 默认使用三份合成场景，会生成报告并向本机模拟器确认测试任务；它不是纯读取探针。三合成场景无需 `--private-scenarios` 参数；启用原题配置后可指向competition_configuration/scenarios.json，但模型及混合检索缺项会如实记为未满足。独立源码归档可运行该流程并获得 `source:<sha>` / `commit=null`；协作提交追溯使用 Git clone。公开仓的 `docs/current_run.json` 是开发交接索引，不包含他人机器的报告数据库，不能直接当作新机器已跑验收。为本机指定唯一 `--run-id` 和独立输出目录，再引用自己的 manifest，保留自动、开发者视觉及真人维度区别。
