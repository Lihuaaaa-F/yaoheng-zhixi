# 2026-09-24 当前验收证据

受测代码 `2087978854a7b091191aba94568418d6730204d3`，原题运行 `delivery_verified_20260924`。本地已整合队友最新 `d8054ba`。后续文档与静态证据提交不改变受测代码身份。

**完整验收未通过**：五个自动维度通过，真实模型与完整混合检索缺少配置/资产，真人评分待填。`verification.json` 保留 FAIL 与 `competition_ready=false`。四份报告采用规则降级，不能作为大模型生成效果证明。

| 场景 | 原题选择 | Word | PDF |
|---|---|---|---|
| S1 | 银黄口服液，2026-05，月度 | [Word](reports/S1/report.docx) | [PDF](reports/S1/report.pdf) |
| S2 | 板蓝根颗粒，2026-05，专题 | [Word](reports/S2/report.docx) | [PDF](reports/S2/report.pdf) |
| S3 | 六味地黄胶囊，2026-03，月度 | [Word](reports/S3/report.docx) | [PDF](reports/S3/report.pdf) |
| Q2 | 银黄口服液，2026-06，第二季度 | [Word](reports/Q2/report.docx) | [PDF](reports/Q2/report.pdf) |

`manifest.json` 绑定本轮任务、快照与文件字节。`browser.json` 记录真实浏览器的四条报告记录与八次下载，`rpa.json` 记录本机模拟发送。`regression.json/xml/log` 与 `environment.json/log` 来自本轮实际执行。`real_corpus_retrieval.json` 仅为固定已知查询与 BM25 证据。`human_review_pending.csv` 留给真实评审填写。

前端分段流程保留 `with_later_failure` 原始失败回执，说明已完成步骤与后续失败，不把整段改成 PASS。最新构建、六项合同、十八视口与最终报告下载有独立通过回执。

目录不包含密钥、运行数据库、聊天库、待发队列或大模型资产。复验需重新启动应用并创建新运行，不将静态证据伪装成新机器的任务数据库。

视觉修复页的便携副本保存在 `visual_evidence/`，`index.json` 对照原检查路径。独立数据脚本可从应用根运行：`05_原型/.venv/bin/python docs/validation/delivery_verified_20260924/verify_official_csv.py 05_原型 /tmp/yaoheng-independent-check`，会在指定输出目录创建独立运行环境。

当前界面的 [110.88 秒演示视频](media/delivery-demo-2087978.webm) 展示分析、对标、原报告下载和已验证的模拟送达回执。未录制新任务发送、真人签收或真实模型调用，详情见 [录制回执](media/demo_receipt.json)。

十页当前答辩稿：[PPTX](media/药衡智析_答辩与离线验收_20260924_定稿.pptx) · [阅读 PDF](media/药衡智析_答辩与离线验收_20260924_定稿.pdf)。实测与待验事项已更新，逐页原生渲染检查见 `media/deck_receipt.json`。
