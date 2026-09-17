# 药衡智析

通用成本分析核心＋可切换行业包。制药竞赛合同保留；机械零部件、化工为独立合成参考包，用于验证框架迁移，尚非完成行业适配。基础修复、自动验证和真人验收分别记录于 [当前运行](docs/current_run.json) 与 [实施状态](docs/implementation_status.md)。

## 启动

本目录为应用根（`药衡智析_增量源码交接/public_source_candidate`），外层是Git根。已合并clone无需prepare。

```bash
bash 05_原型/scripts/bootstrap.sh
bash 05_原型/scripts/start.sh
# http://127.0.0.1:8765
bash 05_原型/scripts/stop.sh
```

Ubuntu 24.04 使用 Python 3.12（需可用的 `venv`）、Node/npm；当前 Vite 锁版本接受 Node 18、20 或 ≥22。Word→PDF 需要 LibreOffice，PDF逐页截图需要 `pdftoppm`；中文字体按环境探针确认。bootstrap 会在项目环境安装锁定依赖，首次安装需要可访问包源；系统工具不会由该脚本自动安装。没有题包时使用公开合成制药/机械/化工；没有嵌入模型时关键词可降级。不会自动下载大型模型或覆盖外置模型。

源码归档与 Git clone 使用相同启动命令，不要求私有题包、模型密钥或 `.git`。全新公开副本不必创建 `.env` 即可基础启动；没有凭据时解释降级，不能记作模型通过。`start.sh` 仅启动服务，源码或锁文件变化后必须先重新运行 `bootstrap.sh`：它校验 npm 锁指纹并重建变化的前端输入。不要仅复制旧 `dist`，也不要用开发服务器截图冒充 8765 上的构建验收。

配置文件位置为 `05_原型/.env`（示例 `05_原型/.env.example`），仅本机保存；应用根的 `.env` 不会自动读取。其他开发者设置 `PHARMA_MODEL_KEY_FILE`、`PHARMA_MODEL_BASE_URL`、`PHARMA_MODEL`；已导出的环境变量优先于该文件。协作默认模型保持 `glm-5.3-flash` 与 OpenAI 兼容适配；本机按用户追加指令使用 DeepSeek 官方应用密钥和 `deepseek-flash`。模型供应商与端点必须匹配，不使用 Coding Plan 凭据。凭据和本机绝对路径不入库。已有 `.env` 或 shell 中的密钥/私有配置会生效，不能把这种环境当作无密钥公开副本测试。

```bash
TMPDIR=/tmp PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=05_原型/backend 05_原型/.venv/bin/python -m pytest -q 05_原型/tests
05_原型/.venv/bin/python 05_原型/scripts/check_environment.py --strict
bash 05_原型/scripts/verify.sh --manifest docs/current_run.json
```

verify将模型回执绑定实际执行的代码commit；只含Markdown/验收摘要的后续文档提交可沿用该代码证据，任何代码、模板或配置变化必须新跑。运行目录及完整报告不随公开仓分发，其他机器须先按交接生成自己的manifest；缺本机job会如实失败。

verify退出0表示自动维度通过，1失败，2未完成；真人评审始终独立。公开clone仅运行合成测试；已授权本机保留的题包回归不随仓库发布。

前端开发、无网络模型的模拟浏览器测试与真实服务测试的完整命令见 [API与运维](docs/api_and_operations.md#前端构建与浏览器验证)。`e2e:live` 会读取真实 API 并提交一份合成报告；若服务配置了模型密钥，可能产生模型调用。它只断言报告提交，不等于文件、RPA或真人验收通过。

## 交付边界

仓库目前公开。本轮移除当前树中的题包、私有知识和完整派生产物跟踪；旧Git历史及已有副本未清除。精确范围与负责人后续事项见 [公开资料处理](docs/privacy_boundary.md)。`team_internal`曾与源码一起被跟踪，不构成权限隔离。

- [架构决策](docs/adr/0004-industry-packs.md)
- [API与运维](docs/api_and_operations.md)
- [检索与生成](docs/rag.md)
- [行业包开发指南](docs/industry/development.md)
- [GLM-5.3交接](docs/ZCODE_HANDOFF.md)

不包含完整ERP、业务知识图谱、多模型路由、自主决策或预测。热力图、模拟任务汇总与行业切换是独立加分项，不能替代制药基础验收。

私有制药企业主数据通过 `PHARMA_PRIVATE_MASTERDATA_FILE` 指向受控JSON（仅产品规格/工厂白名单），词典通过 `PHARMA_PRIVATE_TERMINOLOGY_FILE` 指向受控JSON。两者不是包内公共知识或自动推断结果；修改后对应快照/索引版本失效，保持原制药严格校验。没有这两份原企业配置时，只跑独立合成包，不伪造原场景。具体JSON格式及测试以加载器和对应公开合成负例为准。

无 `.git` 的公开源码归档使用 `source:<sha>` 标识固定源码集合，记录 `commit=null`，不会误认上级目录为本项目Git仓。正式 `verify.sh` 的提交追溯在协作Git clone中执行；独立归档支持启动、分析、创建报告和分维度运行记录。
