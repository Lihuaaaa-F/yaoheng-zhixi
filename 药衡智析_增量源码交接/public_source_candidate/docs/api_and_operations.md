# API与本地运行说明

更新：2026-09-15。API以实际运行的 `/openapi.json`、`/docs` 为准；本文件描述当前v0.1.0接口，不含密钥。

## 环境复用与启动

|项目|实际选择|证据/限制|
|---|---|---|
|系统|WSL2 Ubuntu24.04、x86_64，22逻辑CPU、约15GiB RAM|docs/environment_inventory.json；GPU仅检测，未安装驱动|
|工作目录|用户授权后复制到/home/hujunjie同名目录，ext4|129文件复制哈希基线；D盘只读保留|
|Python|复用系统3.12.3解释器创建05_原型/.venv|系统Python不升级/卸载；实际包import后锁requirements.lock|
|Node|复用24.18.0、npm11.16.0；本项目Linux node_modules|package-lock.json，不复用Windows node_modules|
|PDF|增量安装LibreOffice Writer24.2.7.2和Poppler，复用Noto CJK字体|小样DOCX→PDF已通过，未下载生成模型环境|
|浏览器|复用缓存Chrome for Testing149和Windows Chrome/Edge|基础E2E/Windows只读页面实测证据分开|
|Docker|当前CLI/daemon缺失|运行BLOCKED；不安装另一套WSL Docker Engine|
|Embedding|单个BGE量化ONNX约22.8MB＋tokenizer|CPU，无torch/CUDA训练栈；来源SHA见第三方记录|

```bash
cd '/home/hujunjie/企业赛道_创灵境_基于RAG与大模型的制药企业产品成本智能分析报告系统'
bash 05_原型/scripts/bootstrap.sh
bash 05_原型/scripts/start.sh
bash 05_原型/scripts/verify.sh
# 完成后停止本项目
bash 05_原型/scripts/stop.sh
```

页面：http://localhost:8765；OpenAPI：http://localhost:8765/docs。服务绑定127.0.0.1，Windows localhost经WSL访问。start使用本项目Python启动API8765、原mock8090和单worker；端口若被非受管进程占用则报错，不杀他人服务。stop核对PID创建时间令牌。日志位于05_原型/.runtime/{api,worker,rpa}.log。

## 模型配置

默认读取 `/home/hujunjie/api/DeepSeek/DeepSeek-重庆市AI大赛.txt`。文件只含本项目API密钥，应用内部读取，勿把内容粘贴到终端记录或提交源码。可通过环境选择外部文件，无需改源码：

```bash
export PHARMA_API_KEY_FILE='/home/hujunjie/api/DeepSeek/DeepSeek-重庆市AI大赛.txt'
export PHARMA_MODEL_PROTOCOL='openai'
export PHARMA_MODEL_BASE_URL='https://api.deepseek.com'
export PHARMA_MODEL='deepseek-flash'
bash 05_原型/scripts/start.sh
```

其他OpenAI兼容端点在base_url后追加 `/chat/completions`；如供应商要求/v1，应将/v1放在base_url中。Anthropic格式设 `PHARMA_MODEL_PROTOCOL=anthropic`，base_url配置服务地址，程序追加 `/v1/messages`（已有/v1时追加/messages）。Anthropic只做本地协议夹具验证，未宣称真实供应商联调通过。

`PHARMA_MODEL_MAX_CALLS`限制持久生成调用总数，当前默认40；`PHARMA_MODEL_MAX_REPAIRS`默认2且上限2，可设0进行单次最终联调。改变配置后须重启本项目受管进程。达到预算上限后明确规则降级，不自动增加额度、充值或切换付费服务。未知费用记录UNKNOWN。SQLite调用日志仅记录模型、usage、时间、状态和错误类别；模型原文留在私有.runtime，不进入公开源码。

## 接口表

|方法/路径|输入|输出/行为|
|---|---|---|
|GET /health|无|API身份、worker心跳年龄、simulation|
|GET /api/catalog|无|可用工厂、产品、月份、演示责任人|
|POST /api/analyses|AnalysisRequest|确定性指标快照及snapshot_id，同步|
|GET /api/analyses/{id}|快照ID|已固定快照|
|GET /api/benchmarks|product/month/left/right|同月双方向差异、明细、知识证据、模型状态与findings|
|POST /api/reports|AnalysisRequest|202＋job_id/status/cache_source_time；持久worker处理|
|GET /api/jobs、/api/jobs/{id}|无/任务ID|队列、阶段、结果；单任务含history|
|GET /api/artifacts/{id}|受控artifact_id|哈希校验后的Word/PDF；不接受任意路径|
|POST /api/imports|无|202＋job_id；重验本地受控原始CSV，非任意文件上传入口|
|POST /api/kb/build|无|202＋job_id；重建受控知识源，版本未变复用|
|GET /api/kb|无|知识版本、来源、构建状态|
|POST /api/kb/search|query/product可选/mode|bm25/vector/hybrid；原文、真实位置、知识版本和降级原因|
|POST /api/actions|snapshot_id/finding/assignee/suggestion/priority|DRAFT，尚未发送|
|PUT /api/actions/{id}|允许编辑字段|仅DRAFT可改；返回新payload_hash|
|POST /api/actions/{id}/confirm|payload_hash|确认当前内容并事务写outbox，重复确认幂等|
|GET /api/actions、/api/actions/{id}|无/ID|本地与远端状态分别返回|
|POST /api/actions/{id}/refresh|无|向配置原mock查询同ID；不会再次发送|

AnalysisRequest示例：

```json
{"factory":"中药一厂","product":"银黄口服液","month":"2026-05","analysis_type":"monthly","basis":"unit"}
```

analysis_type为monthly/quarterly/special，basis为unit/total。季度month必须为03/06/09/12并有完整季度数据。跨厂页面API当前按月份比较；季度报告内部使用完整季度对标，不把月度对标当季度指标。

业务错误使用 `error.code/message` 与FAILED，参数格式验证还可能返回FastAPI标准422 detail；调用方需同时兼容。无比较期的业务数值是null/N/A及reason，不是HTTP故障。模型/向量/PDF分别降级或失败并保留原因，不能仅根据HTTP200判断全部功能通过。

## 数据、报告与恢复

标准数据在 `.runtime/data` 的不可变Parquet，以current.json原子发布；知识在 `.runtime/knowledge/<version>`。任务/快照/outbox为 `.runtime/app.sqlite3`；不要在运行中随意删除数据库、CURRENT或历史版本。

报告位于 `07_交付/业务报告/<job_id>/`，包含report.docx、report.pdf（成功时）、report.png、record.json。`06_评测/scenario_reports.json`指向四个当前验收任务，旧目录不等于最终产物清单。不同阶段结果写入SQLite，进程恢复从安全检查点继续；版本变化会报*_VERSION_CHANGED_RESUBMIT，需要重新提交，不能静默换输入。

原mock的POST已模拟发送微信，无额外notify接口。超时或400先GET同ID比较payload；未知结果停止盲发。原mock内存数据重启清空，曾成功任务查询404变REMOTE_UNKNOWN，不自动重建。sent/received/confirmed/completed代表不同含义，均为演示状态。

## 验证命令与范围

`verify.sh`生成 `06_评测/verification.json`，合并必要pytest、原件完整性和当前报告检查。浏览器证据由 `05_原型/tests/e2e.mjs`、`e2e_narrative.mjs`、`e2e_windows.mjs` 的实际执行产生；重跑浏览器涉及本地mock模拟确认，限本项目演示会话。

最终冻结：FINAL_STATUS=PARTIAL。42项合并测试通过；S1/S3/Q2为真实DeepSeek生成通过，S2专题因未绑定文档数字触发严格拒绝而明确规则降级。四份DOCX/PDF均通过，原文与原数据哈希未变。跨产品设备误引已补校验，原错误S2已撤回，不能下载冒充通过。

模型当前已记录30次生成尝试，默认有限总上限40，为用户后续演示预留最多10次。本轮验证已停止模型调用。超过上限、超时或结构/引用错误明确降级，不自动充值。真人评分填写06_评测/human_scoring.json。
