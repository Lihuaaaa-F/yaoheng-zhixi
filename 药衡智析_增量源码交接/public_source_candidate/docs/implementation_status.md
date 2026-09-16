# 实施进度（2026-09-17接续：六项工程缺陷修复）

源码仍为现有05_原型，无Git。2026-09-16增量版的全部历史证据保留于06_评测/incremental_20260916；本节记录本轮接续修改与真实运行结果，不回改历史。

## 本轮修复（主开发者GLM-5.3，全部非视觉工作）

1. **安全恢复**：包根prepare_team_workspace.py重写为核验SHA256.json→仅补缺失→同内容跳过→冲突保留队员文件并列incoming副本；幂等可重复执行。本机实测：401项核验通过、合并323项、二次执行0新增323跳过、模拟队员修改后保留并列副本不覆盖。打包脚本不再内嵌旧覆盖版。
2. **环境与构建**：bootstrap区分运行准备与开发构建——前端按src/配置/锁文件输入哈希决定是否重建（dist/.build-inputs），不再以dist/index.html存在即跳过；依赖检查升级为check_dependencies.py逐包版本锁定+能力探针；PHARMA_PYTHON统一解析（scripts/pharma_python.sh + manage/verify/probe/scenarios/render_pages一致，Windows双布局venv）；Windows过滤lock中丢失平台标记的uvloop；check_environment报告构建新鲜度。
3. **验证入口**：verify.py统一扁平baseline合同（兼容旧嵌套），新增BASELINE_CONTRACT维度；原件保护不再空转——verify.py并入包外层SHA256.json对00/01/02原件的实际钉入，打包时把原件哈希写入baseline.json；历史job不在当前runtime按NOT_IN_THIS_RUNTIME记录不冒充。
4. **模型覆盖**：generate按报告任务计算必要解释章节（|单位成本变动|最大要素对应章节），模型必须给出该章节的hypothesis/insufficient_evidence/document_fact实质解释；summary数字复述不算归因（NECESSARY_EXPLANATION_MISSING降级）；generation_mode如实mixed/llm/rules；新增summary-only、空解释、必要章节缺失行为测试。
5. **模型身份**：ModelGateway逐调用记录requested_model/returned_model/identity_status（VERIFIED_EXACT/VERIFIED_ALIAS/UNVERIFIED_MISSING/MISMATCH），响应缺身份不默认为目标型号；generate聚合model_identity，MISMATCH/UNVERIFIED时model_live为False不得宣称目标模型实调成功；usage跨修复调用累计（calls+tokens合计）；PROMPT_VERSION升至v9自动失效旧缓存。
6. **审核闭环**：新增ReviewStore与API——POST /api/reports/{id}/reviews（审核人、0–5归因分、章节实质/可读性/视觉三维、意见）、GET …/reviews（含对当前产物哈希的有效性）、GET …/acceptance（重算并使产物变更后的旧审核过期）、POST /api/reviews/import（批量导入）；assess_report接入审核记录，无审核保持PENDING不代签；证据维度改为逐结论核对（每条hypothesis/document_fact的证据引用与产品/期间/工厂/规格适用性、numeric_fact的metric_refs、insufficient_evidence的缺证标注）；草稿预览下载（?preview=1，文件名"草稿预览_未审核_"前缀+响应头标识）。

另修：knowledge/narrative/worker的fcntl改为跨平台锁（locks.py）；knowledge索引sqlite句柄显式关闭（Windows文件替换被占用句柄阻塞）；PDF转换临时目录跨平台；render_pages无Poppler时PyMuPDF回退；manage.py双布局venv路径；golden.json以独立Fraction oracle重建（90_工具/rebuild_independent_golden.py，csv直读+Fraction精确算术，未导入生产metrics；与既有季度加权独立断言交叉一致）。

## 本轮真实运行（2026-09-17，Windows开发机）

- Python回归83项全部通过（原70项+新增13项行为测试），pytest于项目venv。
- bootstrap实跑：依赖能力检查通过、前端按输入哈希重建、数据摄取/知识库/工作模板生成。（详见本轮run记录）
- 修复验证：测试内含缺陷1幂等/冲突、缺陷4三类反例、缺陷5身份缺失/错配/记录、缺陷6审核绑定/过期/预览合同。
- 仍未通过：GLM应用实调（本机无受控凭据，保持BLOCKED_NO_KEY不冒充）；真人归因0–5分、可读性、版式（PENDING，模型不代签）；Flash视觉（V0基线任务已建，等待队员在另一会话触发glm-5.3-flash实际读图）。

历史（2026-09-16）：70项回归、5574独立观测、999报告复核、48/18/9浏览器/RPA检查为上一轮证据，见06_评测/incremental_20260916；不因历史PASS推定当前通过。


## GLM应用实调（2026-09-17晚，真实凭据）

- 探针五项PASS；非流式响应model精确=glm-5.3-flash，身份核验一致（无别名假设）。
- 真实模型暴露并修复输出形态问题：normalize_finding仅归一布尔/数组/字符串/引文键形态，类型化插槽、逐字引文、适用性等业务校验全部保持；提示词v9→v11（覆盖合同、字段类型、事件损失规范句式）。
- 四场景v3：narrative全部PASS/llm、model_participation PASS、model_identity VERIFIED、usage跨调用聚合；首轮与第2轮失败证据保留于run_20260917_glm_live（不追认）。
- 整体验收仍PENDING：真人三维+归因0-5分未录入；Flash v3视觉终检任务待回执。
