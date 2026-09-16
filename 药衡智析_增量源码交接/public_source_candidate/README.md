# 药衡智析／药析证链

现有初版的增量修复，唯一源码为 `05_原型`。六个固定报告章节、Decimal计算、React/ECharts、本地混合检索、DOCX/PDF和原题包RPA mock继续沿用。

## 当前状态

本轮依据实际运行证据逐项记录，见 `06_评测/incremental_20260916/verification.json`。GLM默认型号已迁移到**glm-5.3-flash**；本机无应用API凭据，报告保留明确基础分析。真人归因0—5评分、内容可读性和版式审核待完成，不能把文件生成PASS视为报告合格。

- 增量修复范围：[INCREMENTAL_AUDIT](docs/INCREMENTAL_AUDIT.md)
- 队员ZCode CLI接续：[ZCODE_HANDOFF](docs/ZCODE_HANDOFF.md)
- 当前实际报告索引：`06_评测/incremental_20260916/scenario_reports_delivery.json`
- 历史DeepSeek记录、旧S2失败和旧评测保留原值。

## 本地运行

```bash
bash 05_原型/scripts/bootstrap.sh
bash 05_原型/scripts/start.sh
# http://127.0.0.1:8765
bash 05_原型/scripts/stop.sh
```

bootstrap复用兼容项目环境，只安装缺项；Python依赖在项目venv中，Node锁在frontend内。若使用现有兼容解释器，显式设置PHARMA_PYTHON；缺依赖时脚本要求新建项目venv，不修改其他环境。检索模型缓存不随交接包分发，fetch_embedding.py按固定版本和SHA下载缺项；也可用PHARMA_EMBEDDING_DIR复用已授权现有资产。

配置样例为 `05_原型/.env.example`，应用密钥只用受控文件或环境，不输出、不打包。Coding Plan端点不能作为运行时API。默认监听127.0.0.1；端口可在项目.env设置，不结束其他项目进程。

```bash
05_原型/.venv/bin/python 05_原型/scripts/check_environment.py --strict
TMPDIR=/tmp PYTHONPATH=05_原型/backend 05_原型/.venv/bin/python -m pytest -q 05_原型/tests
05_原型/.venv/bin/python 05_原型/scripts/probe_glm.py --output 06_评测/新运行目录/glm_probe.json
05_原型/.venv/bin/python 05_原型/scripts/generate_scenarios.py --output 06_评测/新运行目录/scenario_reports.json
```

生成运行只向受控模型发送必要指标与证据。缺凭据时不自动切回DeepSeek；已存在历史调用不重命名。任务先形成草稿，由用户确认当前内容后才模拟发送。HTTP接收、模拟通知和整改完成分别展示。

## 源码与内部资料

交接总包内 `public_source_candidate` 为未发布的源码候选，`team_internal` 为仅供队内的题包、知识、工作模板、真实样例及测试证据。执行包根目录prepare_team_workspace.py后，工作副本包含内部资料，不可直接公开。

公开源码候选不含秘密、个人账号配置、venv、node_modules、运行缓存。历史恢复基线保存在原工作机独立目录，见交接文档。原题包/原模板只读，工作模板独立维护。

## 本轮交接验证

现有源码、工作模板、方案HTML/artifact已增量更新。四报告共23页已逐页查看，真人评审与GLM应用凭据仍待补；报告总体验收未通过。解压启动13项检查实际通过（复用同机兼容解释器和外置检索模型），最终ZIP以包旁unpack_acceptance.json的SHA256对应记录为准。队员ZCode接续步骤见docs/ZCODE_HANDOFF.md。
