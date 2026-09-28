# 药衡智析

基于 RAG 与大模型的制药企业产品成本分析系统。提供成本看板、跨厂对标、月度/季度/专题报告、知识库、成本预测及本地模拟整改闭环。

本目录是唯一正式源码与交付入口。Python 3.12、Node.js 20/22/24；PDF 导出需要 LibreOffice 和中文字体。

## 安装与启动

Linux / WSL：

```bash
bash 安装.sh
bash 启动.sh
# 浏览器打开 http://127.0.0.1:8765
bash 停止.sh
```

已有兼容 Python 虚拟环境时，先按 `05_原型/requirements.lock` 补齐依赖，再通过 `PHARMA_PYTHON=/你的虚拟环境/bin/python` 接入。启动器不会在指定环境缺依赖时另建环境。未指定时，普通安装在项目独立虚拟环境中运行，不修改系统 Python。

Windows / Docker：先准备 Docker Desktop 的 WSL 集成或已有 Docker Engine，再双击 [药衡智析启动器.bat](药衡智析启动器.bat)。命令行等价入口：

```bash
docker compose -f 05_原型/deploy/docker-compose.yml up -d --build
docker compose -f 05_原型/deploy/docker-compose.yml stop
```

容器在普通用户下运行，数据存入命名卷；不要用 `down -v` 删除业务数据。镜像自带运行依赖，不依赖宿主机 `/opt`。云模型及向量模型须在容器设置页单独配置。

## 使用流程

1. 数据中心上传成本表，预览后解析；旧表修订时明确选择替代关系，原件保留。
2. 上传产品、行业、企业知识，构建真实向量索引；模型连接页配置分析、提取、助手和向量模型。
3. 在成本分析、跨厂对标中选择工厂、产品、期间和单位/总额口径。
4. 生成报告并下载 Word/PDF。整改建议先生成草稿，确认后只发送本地模拟通知。

[赛题原始资料](00_赛题原始资料/)随仓库保留；未来企业私密资料、密钥、运行数据库及对话记录不属于公开交付。没有云模型或向量资产时会明确降级；关键词检索不等于混合检索通过。

## 交付文件

| 项目 | 入口 |
|---|---|
| 完整源码及必要测试 | [05_原型](05_原型/) |
| 中文技术方案 | [技术方案](docs/技术方案.md) |
| 三场景评测报告 | [Word](docs/evaluation/评测报告.docx) · [PDF](docs/evaluation/评测报告.pdf) · [Markdown](docs/evaluation/评测报告.md) |
| 人工评分与样本 | [评分记录](docs/evaluation/人工评分记录.json) · [评测样本](docs/evaluation/评测样本/) |
| 成本预测模型 | [方法、运行及评测说明](docs/forecast/README.md) |
| 部署及共享环境复用 | [环境与部署](docs/环境与部署.md) |
| 实际验证及限制 | [验证结果](docs/验证结果.md) · [机器索引](docs/current_run.json) |
| API | 运行后访问 http://127.0.0.1:8765/docs |

视频和系统演示 PPT：**用户暂缓**，未作为本次完成项。人工评分只记录在交付评测中，网站业务报告的用户验收独立处理。

## 开发验证

```bash
PYTHONPATH=05_原型/backend TMPDIR=/tmp PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$PHARMA_PYTHON" -m pytest -q 05_原型/tests
npm run build --prefix 05_原型/frontend
python3 tools/verify_repository.py
```

未设置 `PHARMA_PYTHON` 时，将测试命令中的解释器替换为项目虚拟环境的 Python。预测 CLI 使用标准库，可单独执行。依赖锁文件、构建指纹和验收版本用于复现，不限制正常分支开发或合并。
