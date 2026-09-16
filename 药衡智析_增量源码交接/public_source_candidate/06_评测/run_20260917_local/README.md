# run_20260917_local 运行说明（主开发者GLM-5.3，Windows开发机）

本目录是2026-09-17六项工程缺陷修复后的本地真实运行证据。历史证据在 ../incremental_20260916，未覆盖。

## 环境

- Windows 11 + Git Bash；项目venv（Python 3.12.7，requirements.lock过滤uvloop后按锁安装）
- Node v24.15.0；前端按输入哈希重建（dist/.build-inputs dcba089fa186）
- LibreOffice 26.8（winget静默安装）用于PDF导出；系统字体回退，未注入项目Noto（与目标机Linux fontconfig路径不同，版式以目标环境为准）
- embedding模型 bge-small-zh-v1.5 按manifest下载并验SHA

## 真实结果

- **Python回归83/83通过**（原70项+新增13项行为测试；详见 ../verify_20260917_defect_fixes/verification.json）
- **四场景报告**：S1/S2/S3/Q2全部 DOCX PASS、PDF PASS、6/6/6/6页（scenario_reports.json）。状态DEGRADED，直接原因=无应用密钥→规则版（model_live=False）；验收FAIL于model_participation，如实未通过。
- **glm_probe.json**：BLOCKED / MODEL_KEY_NOT_SET（无受控凭据；不冒充、不默退其他模型）。
- **审核闭环实测**：对S1 job提交模拟审核→重算填充人工三维+归因分；非法分数422拒绝；?preview=1草稿预览带“草稿预览_未审核_”文件名与X-Artifact-Preview头。该审核为通道验证录入，**非真人签收**，业务验收保持待评。
- **混合检索实测**（服务在线）：/api/kb/search hybrid PASS，产品过滤生效。
- **verify_20260917_defect_fixes**：CORE_CALC/DATA_INTEGRITY/BASELINE_CONTRACT PASS（45项原件经包外层SHA256.json真实钉入保护，0漂移）；历史job如实标NOT_IN_THIS_RUNTIME。

## 视觉

pages/为本轮24页PyMuPDF 120dpi渲染（本机无Poppler回退路径）；browser/为新前端4张1366截图。均已作为v1-*任务交视觉审阅（../dual_model/20260917），**无人实际看图前视觉未验证**。

## 未通过/待续

GLM应用实调（待受控密钥）、真人归因0–5分与可读性版式评审、Flash视觉回执、目标环境（Linux/Word字体）复核。


## V2（Flash V0回执处置后，同日）

scenario_reports_v2.json + pages/（26页）+ browser_v2/：修复V0-001/002/003/009/011/012/013/014后重建（83项回归仍全过）；V0-004经程序量化为可滚动容器非裁切；V0-005/006/007/008/010/015缓办理由见 dual_model/20260917/STATUS.md。v2-*视觉复查任务PENDING_FLASH。
