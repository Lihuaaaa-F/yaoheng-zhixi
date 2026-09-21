# delivery_20260921 · 修复后实测交付（运行态证据）

生成时间：2026-09-21（修复轮实测，Docker 三服务 yaoheng-web/worker/rpa，镜像含本轮全部修复）。
代码基线：main@39c0e75（问题清单全面修复轮；上一次归档 delivery_20260919_final 基于 04011c2，其七场景叙事为 DEGRADED——本轮已根治，见下）。

## 本目录内容

| 文件 | 说明 |
| --- | --- |
| 六味地黄胶囊_2026-06.docx / .pdf / _machine_audit.json | 场景一实调报告：narrative **PASS**、model_participation **PASS**、evidence_applicability **PASS**（job fe8bfa73…） |
| 银黄口服液_2026-06.docx / .pdf / _machine_audit.json | 场景二实调报告：narrative **PASS**、零违约（job d13e75ee…） |

两份 PDF 均无"基础分析"降级横幅；编制人为"成本智能分析系统（生成稿·待责任人复核署名）"。
job 状态为 DEGRADED 是既有语义（section_completeness/readability/visual_quality 三维待真人评审保持 PENDING，`capability_status=PASS` 为机器维度全过）——与修复前"叙事本身 DEGRADED"性质不同。

## 本轮关键实测数据（2026-09-21）

| 链路 | 修复前 | 修复后 |
| --- | --- | --- |
| 叙事合同 | glm-5.3-flash 连续违约（free business number ×6），全部 DEGRADED | glm-5.3 + v10 四舍五入唯一绑定：两场景 narrative PASS、身份核验 VERIFIED、每份 2 次调用 |
| 对标接口（冷） | 60.6–72.7s 且 DEGRADED | 14.7s（六味）/18.6s（银黄）且 narrative PASS |
| 热力图 | 每次请求 ~14s | 首算 16.5s（进程内首次），二次 **0.29s**（版本化缓存命中） |
| RPA 闭环 | 通过 | 复验通过（DRAFT→confirm→SENT→署名 CONFIRMED） |
| 知识库 | 7 文档/154 chunks | 11 文档/180 chunks（行情/行业基准/异常处理记录/对标基线四份补充入库，检索侧幂等校验自动纳入） |
| 二厂对标明细 | 无（第三步输出缺证清单） | 合成明细可用并全程标注"合成演示数据"（按题包汇总 Decimal 精确校准） |

## 仍未完成（诚实边界）

1. 真人三场景 0–5 归因/可读性/版式评分（human_review PENDING，系统不代填）；
2. 演示视频仍为 demo_20260920（基于 03a5a30），本轮修复后的重录待人工完成；
3. 干净评测机（无代理）首次构建已修复默认值，但建议交付前实测一次净机部署；
4. 热力图进程首次访问仍需 ~16s 首算（缓存后 0.3s），如需更快可在启动器预热。
