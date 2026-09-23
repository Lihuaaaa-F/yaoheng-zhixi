# 药衡智析性能源码级审查与优化报告（2026-09-23 夜间无人值守运行）

**执行方式**：定时任务触发。先建量化基线，再以动态工作流三路并行子代理（后端热路径/前端/构建链，全部 GLM-5.3-Flash）做源码级审查，20 条发现中 3 条高影响结论经独立子代理交叉验证（驳回 0 条）；随后按"P0/P1 且可验证才实施"的红线逐项落地，每项独立 commit、每项过测试门禁。

**提交清单**（全部基于 main，测试全绿后逐项提交）：

| commit | 内容 |
|---|---|
| de681d6 | GZip 中间件 + 指纹资产 immutable 缓存（后端传输层） |
| dceccf8 | benchmark_analysis 消除左右厂重复 analyze（输出逐字节等价验证） |
| 22e0362 | data_import 建表 DDL 每进程一次 |
| af9e076 | echarts-gl 按需注册 + React.lazy 拆分（首屏 -40%） |
| ff72186 | Chart/Chart3D option 内容短路（悬停不再重建 WebGL 场景） |
| 7d35778 | 任务轮询内容未变跳过 setState |
| 760298e | 知识图谱 e2e 适配 lazy 时序 |

---

## 一、基线数据（优化前实测）

| 路径 | 方法 | 结果 |
|---|---|---|
| 测试套件 | `PYTHONPATH=backend pytest -q tests` | 402 passed / 1 skipped，35.3s |
| `/health` | TestClient GET | 20ms |
| `/api/industry/catalog` | TestClient GET | 27-55ms（响应 2.6KB） |
| 对标计算 `benchmark_analysis('六味地黄胶囊','2026-06')` | 进程内计时×2 | 0.087-0.107s（响应 167KB） |
| 知识库检索 | 进程内 Knowledge().search | 冷 2.448s / 热 0.027s（8644859 双层缓存确认生效） |
| heatmap | HTTP GET 热/冷 | 2-4ms（`_GRID_CACHE` 生效） |
| 前端产物 | dist/assets 清点 | **单 JS chunk 1,532,372B** + CSS 19,233B；`gzip -9` 实测 JS→471,161B（-69%）但**服务端无压缩中间件**，全明文传输 |

sourcemap 归因（审查子代理复现构建，产物 hash 与线上一致 `index-CuIi9vb_.js`）：echarts 449.6KB+zrender 170.4KB、echarts-gl 286.4KB+claygl 210.7KB（GL 栈合计 ≈497KB/35%）、react-dom 174.7KB、应用源码约 104.9KB。

## 二、发现清单（20 条）与处置状态

### 已实施（8 项，含 1 项配套 e2e 修复）

| # | 发现（file:line） | 影响/风险 | 实施与验证 |
|---|---|---|---|
| SSE-3 | 无 GZip 中间件（api.py:15），1.46MB JS 与 167KB JSON 全明文传输 | 高/P0 | `GZipMiddleware(minimum_size=1024)`；真实 HTTP 验证 asset 与 API JSON 均返回 `content-encoding: gzip`；合同测试入套件 |
| SSE-15 | StaticFiles 无 Cache-Control（api.py:639），指纹文件每次导航重验 | 中/P0 | `_ImmutableAssets` 子类对 `assets/*` 注入 `public, max-age=31536000, immutable`；index.html 保持协商；Windows 反斜杠子路径已归一；真实 HTTP 验证 |
| SSE-2 | `import 'echarts-gl'` 全量副作用注册（Chart3D.tsx:6），globe/graphGL/flowGL 等未用类型全进首屏 | 高/P0 | 删全量 import，改 Bar3D/Scatter3D/Lines3D+Grid3D 按需注册（d.ts 补 components 声明） |
| SSE-1/16 | 单 1.53MB chunk 无拆分（vite.config.ts:3，`chunkSizeWarningLimit:800` 只是掩盖告警） | 高/P0 | Chart3D 改 `React.lazy`+Suspense（Evidence.tsx）；**未用 manualChunks**——lazy 已把 GL 栈自然拆为独立异步块，比手动分块更精确 |
| SSE-5 | benchmark_analysis 左右厂各 analyze 两次（metrics.py:357 与 394-395） | 中/P0 | 抽出 `_benchmark_payload` 共享一次结果，analyze 4→2 次；输出 json 同口径逐字节等价（109,527B 前后一致）；调用次数合同测试 |
| SSE-18 | `_connect` 每次连接执行建表 DDL（data_import.py:114-118），mark_import_status 一次=2连接2次DDL | 低/P0 | `_init_imports_db` 带锁单次初始化；旗标随 `importlib.reload` 重置，与测试 isolated_runtime 目录切换生命周期一致 |
| SSE-12/13 | Chart 调用方全为内联 option 字面量，父组件任意 state 变化即 notMerge 全量重绘；图谱页每次 mouseover 重建 WebGL 场景（≈1100 符号）（Chart.tsx:15、Chart3D.tsx:33、Evidence.tsx:94） | 中/P0 | 序列化签名比对，内容未变跳过 setOption；e2e 悬停 tooltip 用例实测通过 |
| SSE-14 | 任务轮询每 2s 无条件 set 新数组身份，jobs 携带完整 result 大 JSON 反复 parse+diff 整树重渲染（hooks.ts:18） | 中/P0 | 统一 `apply()`：序列化签名相同不触发更新 |

### 未实施——留待白天评审（附理由）

| # | 发现 | 影响/风险 | 不实施理由 |
|---|---|---|---|
| SSE-4 | ingestion 每次分析重新全量解析 CSV+重建指纹（ingestion.py:249） | 中/P0 | 进程级缓存涉及数据新鲜度失效语义，做错属数据正确性事故；需评审缓存键（mtime+文件集哈希）与发布链路交互 |
| SSE-7 | context_services.retrieve 每次对 3.3MB 知识语料全量 sha256（context_services.py:71→knowledge.source_snapshot:103） | 中/P0 | 同上；该哈希是 `KNOWLEDGE_SNAPSHOT_CHANGED` 防篡改合同的一部分，短路逻辑需合同级评审 |
| SSE-8 | ModelGateway 每请求新建 httpx.Client+6 条 sqlite DDL（narrative.py:705-709） | 中/P0 | 实例缓存键须含全部环境指纹，与测试 monkeypatch 隔离机制有交互风险（conftest 逐用例改环境） |
| SSE-10 | 报告入队先全量重算 scoped_analysis 再查缓存（api.py:222）；命中后 artifacts_healthy 全量读盘 sha256（jobs.py:99） | 中/P0 | scoped_analysis 缓存同 SSE-4；artifacts_healthy 短路会削弱产物完整性校验，需安全评审 |
| SSE-11 | industry 每请求重读 facts.json+pydantic 全量校验；capabilities() 每次扫 PATH（industry.py:596/557） | 中/P0 | 校验结果缓存与注册表失效语义耦合（00c053f 刚修过注册表写入时机），不夜间动 |
| SSE-6 | jobs 列表/决策端点全量反序列化每条任务 result 大 JSON（jobs.py:71/88） | 中/P0 | 修复方向是收窄列表载荷=**改对外 API 契约**，触碰红线；需与前端一起设计轻量轮询端点 |
| SSE-9 | convert_pdf 每次新建 LibreOffice 临时 profile+空字体缓存=每次冷启动 soffice（reports.py:1041-1043） | 中/P0 | 本机无 soffice（能力显示 degraded），无法验证；改常驻 soffice 进程属运维架构变更 |
| SSE-17 | Knowledge 按请求实例化，ONNX/chroma 每请求重建（knowledge.py:285、api.py:484/500） | 低/P0 | vector 默认未启用、影响低；实例级缓存与 SSE-8 同类风险 |
| SSE-19 | DataTable 全量渲染无虚拟化、key={i}（Analysis.tsx:20） | 低/P0 | 当前明细行数小无实测瓶颈；虚拟化改交互行为需 GUI 审查流程 |
| SSE-20 | 单 uvicorn worker 承载 API+静态（deploy/entrypoint.sh:9） | 低/P2 | **不应改**：JobStore 进程内存态，多 worker 会分裂任务状态；加了 gzip+immutable 后静态传输已卸载，多人并发演示场景留观察 |

### 预存问题（与本次无关，已记录）

- `e2e-context.mjs` 在当前 main 即已失败：用例等待 `行业包` 选择器，而 App.tsx:18 注明"专为本制药赛题定制：无行业包选择、无合成演示数据"——9-21/22 演示收敛时 UI 移除了该控件，用例未同步。本次改动未触碰该流程（未改 App.tsx）。

## 三、优化后量化对比

| 指标 | 优化前 | 优化后 | 变化 |
|---|---|---|---|
| 首屏 JS（未压缩） | 1,532.4KB | 921.3KB | **-39.9%** |
| 首屏 JS 传输（gzip，vite 口径） | 474.7KB（有中间件前为 1,532KB 明文） | 304.5KB | **明文→gzip：传输 -80%** |
| GL 依赖（echarts-gl+claygl） | 首屏内 ≈497KB | 独立块 459.3KB（gzip 126.6KB），仅抽屉打开时加载 | 首屏移出 |
| 静态资产回访 | 每次导航 304 重验 | `immutable` 一年缓存 | 重验 RTT→0 |
| benchmark 路径 analyze 调用 | 4 次 | 2 次 | 计算减半（输出逐字节等价） |
| 导入流水线 sqlite DDL | 每连接 1 次 | 每进程 1 次 | 微IO消除 |
| 图谱悬停 | 重建 WebGL 场景 | 0 setOption | 交互不掉帧路径 |
| 任务轮询 | 每 2s 整树重渲染 | 内容未变 0 渲染 | 大 JSON parse/diff 消除 |
| 测试 | 402 passed/1 skipped | **406 passed/1 skipped**（+4 合同测试） | 全绿 |

## 四、验证记录

- 全套 pytest 三轮门禁（每实施项后）：406 passed / 1 skipped。
- 真实 uvicorn（8765）+ Playwright：`e2e-knowledge-graph.mjs` **7/7 PASS**（大窗口/放大视图/左键旋转/滚轮缩放/平移/悬停 tooltip"板蓝根（药材）"/无运行时错误）——覆盖 lazy 加载、按需注册、option 短路全部改动面。
- 真实 HTTP 头验证：`/assets/*.js` 返回 `content-encoding: gzip` + `cache-control: immutable`；`/`（index.html）无 immutable；`/api/industry/catalog` gzip。
- 基线复测：GZip 后 benchmark JSON 167KB→gzip 传输（TestClient 合同测试锁定）。

## 五、运维备注（夜间运行事实记录）

- 端口 8765 发现**改动前遗留的旧 uvicorn 进程**（旧代码、无 gzip），为真实验证予以终止并重启新服务，验证完毕后已停止（本机开发进程，无数据影响；任务状态存 sqlite 不受影响）。
- `scripts/manage.py` 存在**先前遗留的未提交改动**（23+/4-，非本次产生），本次所有提交均未包含它，保持原样。
- 临时测量脚本位于 `D:/tmp/perf_baseline/`（仓库外）。

## 六、建议的后续白天工作（按收益排序）

1. SSE-4/7/8/10/11 进程级缓存族：统一评审缓存键与失效语义后一次性落地（对标与报告链路预计再降一个量级）。
2. SSE-6：设计轻量任务轮询端点（status/版本号），列表载荷收窄（需前后端同动，过 API 契约评审）。
3. `e2e-context.mjs` 与现行 UI 对齐（行业包选择器移除后未同步），并在 CI 固化 `e2e-knowledge-graph.mjs`。
4. 多人演示场景压测（SSE-20），确认单 worker 余量。
