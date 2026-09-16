# ZCode 接续交接：药衡智析（2026-09-17缺陷修复版）

## 当前状态一句话

六项工程缺陷已修复并实测；GLM应用实调已通过（探针五项PASS、响应model精确核验glm-5.3-flash、四场景narrative PASS且模型参与PASS）。剩余待办：真人归因/可读性/视觉三维录入（API就绪）、Flash v3视觉终检回执、目标环境（Linux/Word字体）复核。历史BLOCKED证据保留于run_20260917_glm_live与更早运行。

## 本轮已完成的修复（主开发者GLM-5.3）

1. **安全恢复**：prepare_team_workspace.py重写——先核验SHA256.json（401项），只补缺失、同内容跳过、冲突保留队员文件并列incoming副本；幂等。90_工具/prepare_team_workspace_safe.py为项目内副本，打包脚本嵌入安全版。
2. **环境与构建**：bootstrap按前端源码/配置/锁文件输入哈希决定重建（不再因dist存在跳过）；check_dependencies.py逐包版本锁+能力探针；PHARMA_PYTHON统一解析（scripts/pharma_python.sh；manage/start/stop/verify/probe/scenarios/render_pages一致；Windows双布局venv、lock过滤uvloop）；check_environment报告构建新鲜度。
3. **验证入口**：verify.py统一扁平baseline合同+BASELINE_CONTRACT维度；原件保护真实化（并入包外层SHA256.json对00/01/02的钉入+打包写入baseline.json；45项受保护、0漂移实测）；历史job不在当前runtime记NOT_IN_THIS_RUNTIME。
4. **模型覆盖**：主要差异章节必须有模型实质解释（hypothesis/insufficient_evidence/document_fact）；summary-only数字复述=NECESSARY_EXPLANATION_MISSING降级；generation_mode如实mixed/llm/rules。
5. **模型身份**：逐调用requested/returned/identity_status（VERIFIED_EXACT/ALIAS、UNVERIFIED_MISSING、MISMATCH）；未核实不得宣称目标模型实调；usage跨修复调用累计；PROMPT_VERSION v9失效旧缓存。
6. **审核闭环**：POST/GET /api/reports/{id}/reviews、GET …/acceptance（重算+产物变更过期）、POST /api/reviews/import；assess_report人工三维只认哈希绑定的真人记录（模型不代签）；证据维度逐结论核对；?preview=1草稿预览明确标识。
7. **跨平台**：fcntl→locks.py；sqlite句柄显式关闭；PDF转换soffice解析与临时目录跨平台；render_pages无Poppler用PyMuPDF回退；manage.py Windows进程脱离（DETACHED_PROCESS）与存活检测；独立golden.json以Fraction oracle重建（90_工具/rebuild_independent_golden.py）。

## 本轮真实证据（06_评测/run_20260917_local + verify_20260917_defect_fixes）

83项回归全过；四场景DOCX/PDF全PASS（6/6/6/6页，Windows LibreOffice 26.8导出、系统字体回退）；验收FAIL于model_participation（无密钥→规则版，如实）；glm_probe BLOCKED/MODEL_KEY_NOT_SET；审核闭环/混合检索/草稿预览API实测通过；解压启动验收对最终ZIP另出回执。

## 队员接续（按序）

1. **Flash视觉**：ZCode当前版本无固定模型子智能体（Agent工具无model参数），按06_评测/dual_model/20260917/STATUS.md用双会话——新开glm-5.3-flash会话，首条消息让它读该目录FLASH_VISUAL_ROLE.md并处理v0-*/v1-*任务。无人看图前视觉未验证。
2. **GLM应用实调**：✅已完成（2026-09-17）：探针五项PASS、身份精确核验、四场景v3全部narrative PASS/llm。证据：06_评测/run_20260917_glm_live/。凭据在受控文件，不入库不入包。
3. **真人审核**：对终版报告经POST /api/reports/{id}/reviews录入归因0–5分、章节实质、可读性、视觉三维；产物重生成后需重审（旧审核自动过期）。
4. **目标环境复核**：Windows（Word打开DOCX装项目字体）与Linux（LibreOffice+fontconfig注入Noto）分别检查字体分页；本机PDF为系统字体回退路径。

## 固定边界（不变）

原始题包/模板/历史证据不改写；Coding Plan端点禁入应用运行时；不默退DeepSeek；混合检索在已见集0.928571<BM25 1.0，新未见集先冻结再评；文件生成成功≠验收通过；模型与Flash均不代真人签收。

历史背景见 docs/INCREMENTAL_AUDIT.md 与 06_评测/incremental_20260916（保留未动）。
