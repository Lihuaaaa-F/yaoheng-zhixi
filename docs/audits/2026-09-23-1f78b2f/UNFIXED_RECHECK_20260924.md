# 第二份独立审查报告（2026-09-23-1f78b2f 带连字符目录）未修项核对

- **核对日期**：2026-09-24
- **核对基线**：HEAD = `8644859`（main；含本会话修复 00c053f + 8644859）
- **核对方式**：逐项对照报告发现 + 关键不确定项代码亲验（下表"核对方式"列标注"亲验"为本轮 grep/读取确认，其余按报告结论采信——该报告 6 项抽验全部属实，可信度高）
- **本会话已修映射**：00c053f 修复了 AUD-IMP-08 的一部分（XLSX 空值防线）、AUD-DEP-05 的一部分（CI docker build）、另修该报告未覆盖的 8 项（对标异步化/缺省方向/模板同比表头定位/anthropic tokens/热力图三维单图/预测覆盖率实测/图谱增益对照/knowledge 缓存）

## 一、未修复项全景（按报告优先级）

### P0（2 项，均未修）

| 编号 | 问题 | 现状（亲验） | 报告建议 |
|---|---|---|---|
| **AUD-IMP-01** | 自助导入量纲错误：`(元/盒)` 单位成本列按绝对金额入 facts → 总成本错 4.5 万倍且校验零警告（题包真 CSV 已动态复现） | **未修**（亲验：data_import.py:63-65 仍直接映射 element 角色，发布无产量换算；我修的空值防线不覆盖量纲） | FIX-A：映射角色带单位语义（元/盒列×产量转金额）；总成本列落地事实并与 Σ要素校验 |
| **AUD-DEL-01** | 交付证据链断裂：delivery_20260921 十文件与 manifest 哈希零匹配；S3 无回执 | **未修**（交付产物未重制） | FIX-B：HEAD 重跑三场景交付+评测流水线，哈希对拍全 MATCH |

### P1（5 项，均未修；IMP-03 部分缓解）

| 编号 | 问题 | 现状 |
|---|---|---|
| AUD-IMP-02 | 自助导入缺 5 类不变量校验（单位成本=Σ要素/总成本=产量×单位成本/材料占比100%/费用勾稽/父子一致） | 未修（亲验：validate_business 无算式校验） |
| AUD-IMP-03 | 再发布非原子：同名重导覆盖同目录破坏旧注册 | **部分缓解**：00c053f 加了注册失败清理孤儿目录；但"成功重导覆盖旧数据"路径仍在（临时目录+os.replace 或 enterprise_id 纳数据哈希未做） |
| AUD-DEP-01 | requirements.lock 缺 openpyxl → lock 环境数据中心 xlsx 导入 ImportError | 未修（亲验：lock 0 命中/requirements.txt 1 命中；我新增的 xlsx 测试跑在 .venv（txt 全集）故 CI 绿是覆盖假象） |
| AUD-DEL-02 | 交付物早于 Word 根治/TOC/归因引擎等重大修复 | 未修（并入 FIX-B） |
| AUD-DEL-03 | 评测报告三缺口（主文档停 0919/人工 0-5 全 PENDING/场景编号三处互斥） | 未修（FIX-B+真人评分） |

### P2（18 项：已修 2 部分，未修 16）

| 编号 | 问题 | 现状 |
|---|---|---|
| AUD-IMP-04 | 发布后归因异常→整批误标 PARSE_FAILED | 未修 |
| AUD-IMP-05 | PARSING 永久卡死无回收 | 未修 |
| AUD-IMP-06 | 同文件重复主键仅告警累加（双计风险） | 未修 |
| AUD-IMP-07 | 知识 docx 忽略表格内容 | 未修 |
| AUD-REP-01 | legacy findings 形状→整任务 FAILED 而非降级 | 未修 |
| AUD-NAR-01 | 检索未传 document_version（旧版文档可单独命中） | 未修（亲验：context_services/worker 0 命中） |
| AUD-RAG-01 | 报告链知识库与交互库分裂（补充知识/用户上传不进报告检索） | 未修（亲验：context_services 构造 Knowledge(context=…) 时 extra_dir 分支不生效） |
| AUD-RAG-02 | DEGRADED 构建知识静默过期（源变更+部分失败组合） | 未修 |
| AUD-FE-01 | 报告/整改页改筛选后 snapshot 陈旧、新任务卡默认不可见 | 未修（亲验：ReportGeneration 仍按 snapshot_id 过滤） |
| AUD-FE-02 | e2e/demo 脚本半数陈旧（选择器失效） | 未修 |
| AUD-MDL-01 | save_settings 的 key_file 任意路径（部署条件性 P2） | 未修（亲验：仍只查 is_file；我修的是 overrides 参数白名单，非此路径） |
| AUD-DEP-02 | Dockerfile 用 txt 非 lock + 镜像源注释空许 | 未修 |
| AUD-DEP-03 | bootstrap.sh CRLF（原生 Linux 必败） | 未修（亲验：file 显示 CRLF，git i/crlf） |
| AUD-DEP-04 | 容器 root + 无资源限制 | 未修 |
| AUD-DEP-05 | CI 零部署面 | **部分修**：00c053f 已加 docker build；`docker compose config -q` 未加 |
| AUD-DEL-04 | prompt 文档滞后（自称 v18/校验 v9，代码 v21/v10） | 未修 |
| AUD-DEL-06 | 根 LICENSE 未决 + PyMuPDF AGPL 分发评估 | 未修（需团队决策） |
| AUD-DEL-09 | 视频/PPT 绑定旧提交、PPT 缺三场景结果页 | 未修（并入 FIX-B；本轮 Flash 判读提供现状证据） |
| AUD-TST-02 | PDF 真渲染测试 CI 无 LibreOffice 从未执行 | 未修（亲验：CI workflow 0 命中 libreoffice） |
| AUD-TST-03 | 数值链中段自洽重算（display 用引擎自产分子分母） | 未修（独立复算脚本在本目录 EVIDENCE，未转硬编码金标测试） |

### P3（26 项：全部未修，报告自评多为低风险后置）

CORE-08（材料分母下标0）/ REP-03/04/05/06 / NAR-04/05/06/07/08 / RAG-05/06/07/08 / MDL-04/05/06/07 / IND-04/05/06/07 / API-03/04/05 / FE-05/06/07/08 / DEP-06/08 / TST-04。其中演示前值得优先的三项（报告建议）：IND-05（导入企业误标"合成演示"）、FE-01（任务卡不可见，P2 已列）、DEP-06（启动器发行名探测）。

## 二、已修复项（本会话，供对照）

| 该报告编号 | 对应本会话修复 |
|---|---|
| AUD-IMP-08（部分） | XLSX 空单元格行级警告 + 空值率>50% INVALID + 能力预览 available 真值化 + 孤儿目录清理（00c053f） |
| AUD-DEP-05（部分） | CI 增加 docker-image-build 作业（00c053f） |
| AUD-KB-01（该报告无此编号；另一审查路径） | knowledge.search 分块/适用性双层缓存（8644859） |

## 三、结论

第二份报告的 **P0×2、P1×5、P2×16、P3×26 基本未修**——本会话此前两轮修复针对的是第一份审查报告（20260923 无连字符目录）的问题集，两份报告发现重叠度低（互补）。当前最高优先：**FIX-A（IMP-01/02/06，比赛数据接入可信度）→ FIX-B（DEL-01/02/03/09，必交评测证据链）→ FIX-C（DEP-01/02，半天）**，随后 FIX-D（NAR-01）/FIX-E（RAG-01）/FIX-G（FE-01）。

## 四、视觉项处置（本轮）

VH-01..06 已派 GLM-5.3-Flash 子代理判读（工作流 dwfrun-41acc1fe；材料：存量页图 13×2、HEAD 8644859 样例 17 页、视频 12 帧、PPT 10 页、UI 20 张）；VH-07 人工评分必须真人未派模型；VH-08/09 属净机/实机环境实测未执行。判读结果见 markdown 产物与本目录 FLASH_VISUAL_RESULTS.md。

---

## 五、修复状态更新（2026-09-24，commit b33388c）

上述清单中的代码类问题已全部修复并验证（常规环境 423 测试全绿、空 runtime 422 绿+1 诚实 skip、前端构建通过、bootstrap bash -n 通过、页眉修复经 14/14 页 PDF 顶部文本静态验证）：

- **P0**：AUD-IMP-01 ✅（量纲换算+总成本勾稽，验收 total=481500）；AUD-DEL-01 ⏳（属 FIX-B 交付重制，见下）
- **P1**：IMP-02 ✅、IMP-03 ✅、DEP-01 ✅（lock+openpyxl）；DEL-02/03 ⏳（FIX-B）
- **P2**：IMP-04/05/06/07 ✅、REP-01 ✅、RAG-01/02 ✅、FE-01 ✅、FE-02 ✅（废弃标注）、MDL-01 ✅（10KB 上限取舍方案——路径白名单与产品文案冲突，不做硬白名单）、DEP-02/03/04/05 ✅、DEL-04 ✅、TST-02 ✅（CI 装 LO）、TST-03 ✅（金标硬编码）；DEL-06 ⏳（需团队决策许可证种别）、DEL-09 ⏳（FIX-B）
- **P3**：CORE-08、REP-04、REP-06、NAR-04/05/06/08、RAG-06/07、MDL-04/05/07、IND-05、API-05、TST-04、DEP-06 ✅；NAR-01 经分析**不采纳字面修复**（"当前知识版本"参数与 knowledge_snapshot 语义错位，既有 chunk 元数据透出+同文档多版本冲突排除已覆盖该风险）；RAG-05 随 chunk 元数据现状维持；MDL-06/API-03/API-04/FE-07/FE-08/IND-04/IND-06/IND-07/RAG-08/DEP-08 维持后置（报告自评低优先/待验证）
- **Flash 视觉新发现**：页眉/水印系统性缺失 ✅（根因=前置区手术移除分节丢正文页眉引用；修复+reader-v6+v5 模板自动重建）；p09/p15 整页空白 ⏳（孤行 PBB 策略的已知取舍——用户 2026-09-24 裁定清除 keepNext 黑方块后接受，如需再优化属产品决策）

**FIX-B（交付证据链重制）未在本轮执行**：需在 HEAD 重跑三场景交付+评测流水线（多次真实模型报告生成、manifest/评测文档重写、视频/PPT 重制），是独立的长流程且写入正式交付目录，建议单独执行（人工 0-5 归因评分同批由真人完成）。
