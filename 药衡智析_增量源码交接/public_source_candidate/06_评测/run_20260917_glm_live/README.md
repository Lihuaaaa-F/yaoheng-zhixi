# run_20260917_glm_live：GLM应用实调运行（主开发者GLM-5.3协调）

## 凭据与边界
密钥仅存受控文件（用户目录，仓库/打包范围外），.env只含PHARMA_MODEL_KEY_FILE路径与PHARMA_MODEL_MAX_CALLS=200；本README与一切产物不含密钥。Coding Plan端点未使用；默认glm-5.3-flash中国站通用端点。

## 探针（glm_probe.json）
文本/结构化JSON/工具调用/SSE流式全部PASS，非流式三项响应model精确=glm-5.3-flash（身份核验一致）；流式按DATA[DONE]合同判过。限流未主动施压（NOT_RUN），真实额度以账号后台为准。

## 迭代过程（保留全部证据）
- scenario_reports.json（第1轮）：真实模型输出大量形态变体（hypothesis字符串、missing_evidence字符串、suggestion数组、附加字段）→ 守卫如实降级；证明缺陷4/5修复在真实模型下工作。
- scenario_reports_v2.json（第2轮）：加入normalize_finding（仅形态归一，业务校验不变）+v10提示词；S2达narrative PASS。
- scenario_reports_v3.json（第3轮，当前有效）：引文键并入refs+覆盖/事件损失句式合同（v11）；四场景全部narrative PASS / generation_mode=llm / model_participation PASS / model_identity VERIFIED；usage按报告聚合（2-3次调用）。

## 当前验收状态
模型参与：PASS（含必要解释覆盖：主要差异章节materials均有hypothesis/实质解释）。整体acceptance：PENDING——真人归因0-5分、章节实质、可读性、视觉三维待真人录入（POST /api/reports/{id}/reviews）；无签收不判合格。job状态DEGRADED仅反映人工维度未评。

pages/=28页渲染（PyMuPDF回退）；browser/=3张截图。v3-*视觉任务已发（dual_model/20260917）。本轮PDF仍为Windows LibreOffice+系统字体回退，最终版式以目标环境为准。
