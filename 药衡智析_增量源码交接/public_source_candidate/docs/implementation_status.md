# 实施与赛题验收矩阵

唯一当前记录：`current_run.json`。原固定审计acc4693作为起点；历史GLM四场景v3模型参与PASS/整体PENDING、五个视觉NEEDS_FIX保留工程外，不能替代本轮。以下状态不以测试数量或文件生成推定整体验收。

| 类别/条款 | 实现入口 | 测试/产物 | 当前状态及缺口 |
|---|---|---|---|
| 基础：Word动态模板、至少五类规定章节 | reports.normalize_template/render_docx；原赛题适配保留 | 原模板split-run与数值绑定回归；新DOCX | 已实现已验证结构；专业内容待真人 |
| 月度/季度/专题、产品/期间 | API/metrics/行业上下文/UI | 原场景与季度独立golden；真实浏览器 | 已实现已验证；季度Σ成本/Σ产量 |
| 数据＋RAG＋大模型解释 | context_services/generate | 当前model_live回执 | 已实现已验证：本轮七场景解释合同通过；真人归因待评，保留先前失败运行 |
| Word/PDF专业导出 | reports/reference_report/convert_pdf | 真实LibreOffice、逐页图、字体 | 文件生成已验证；真人版式待评 |
| 产品/行业/企业三类知识 | 制药原件适配/行业知识JSON | 适用性与召回测试 | 已实现；题包缺历史异常整改档案，不伪造原有记录 |
| PDF/DOCX/TXT、混合检索、来源定位 | Knowledge/FTS5/Chroma/LlamaIndex BaseRetriever | 101位反例、真实三包混合召回 | 已实现已验证；新行业检索质量仅合成回归，非未见真实质量证明 |
| 环比/同比/预算/贡献率 | metrics/industry | independent golden与勾稽 | 已实现已验证；缺月/零分母不补零，贡献率可负或>100% |
| 近六月趋势/瀑布/结构 | Analysis/Benchmark/ECharts | 真实DOM与稳定截图 | 已实现已验证；数字单位随上下文 |
| 要素严格±10%自动重点 | 稳定alert_id/typed facts/narrative | 阈值边界、全部口径解释覆盖 | 已实现，严格阈值/全告警合同与正文绑定已验证；实调覆盖逐场景记录，失败不转绿 |
| 跨厂找差异→拆结构→拆原因 | benchmark_reference/benchmark_analysis/UI | 双向和季度测试、三步法字段 | 结构已验证；原因专业质量待真人，无二厂原料明细不造下钻 |
| 标准答案≤1% | 原golden本地回归/合成evaluation | 确定性回归通过 | 已验证覆盖范围；不是全部潜在业务情形 |
| 结构化任务标题/负责人/来源/优先级/期限 | ExecutableAction/ActionStore | 编辑负例、真实HTTP合成任务 | 已实现已验证合同；模型建议逐场景审查 |
| 确认后HTTP原mock/模拟微信 | outbox/worker/严格协议 | run_acceptance/RPA回执 | 已实现已验证，七场景模拟送达7/7；长报告阻塞outbox已修为独立调度循环 |
| 幂等/超时/重启 | SQLite/outbox/SENDING先GET | 合成transport与恢复回归 | 已实现已验证；送达≠整改完成 |
| 三场景/真人0–5/RPA率/三步法率 | verify/current manifest/ReviewStore | 分维度回执 | 本轮自动维度PASS；真人评分PENDING，AI不填 |
| Python/Web/OpenAI兼容/一键启动 | FastAPI/React/requirements.lock/bootstrap | 本机探针、干净公开导出测试 | 已实现已验证；无密钥基础降级 |
| 架构/RAG/Prompt/模板/API文档 | docs与包模板 | 本轮原位文档 | 已实现；细分行业深研继续 |
| 公开源码交付 | 同仓工作分支 | staged/tracked清理与远端核验 | 按用户最新明确授权恢复原赛题资产并纳入静态交付；密钥/运行态仍排除 |
| ≤5分钟视频/决赛PPT | record-demo/build_demo_deck | 37.68秒合成视频/8页PPTX稿 | 已生成演示素材；最终讲解剪辑及PowerPoint实渲染待完成 |
| 加分：热力图 | Analysis/ECharts | 真实浏览器 | 已实现已验证 |
| 加分：生成/送达/责任人确认看板 | Tasks/acknowledge | UI合同、状态计算 | 已实现；真人责任确认需实际本人填写，演示不冒签 |
| 加分：行业扩展 | industry/三包/多企业配置 | 机械工单机时、化工批次能耗、四要素 | 框架参考包全链路已验证；尚非完整行业适配 |
| 加分：知识图谱 | graph.py 从知识快照抽取产品-药材-工序图 | test_graph 8项；真实题包抽取3产品/11药材/7工序/27边 | 已实现：检索词增强（仅制药上下文，适用性合同不变）+ /api/kb/graph + 前端力导图 |
| 加分：运行多模型协作 | ModelGateway.for_route 任务路由 | test_decision 路由回退/环境变量/JSON路由表；GLM双模型实调 | 已实现：narrative=glm-5.3-flash，decision=glm-4.5-air 轻量路由实测PASS；未配置时同源回退并如实标注 |
| 加分：自主Agent任务决策 | decision.py 确定性策略+小模型说明+SQLite台账 | test_decision 9项；实调决策说明glm-4.5-air PASS | 已实现：无报告/数据变化→REPORT_NEEDED，同快照→DASHBOARD_ONLY；可按决策入队报告 |
| 加分：预测 | forecasting.py Holt双参数指数平滑 | test_forecasting 8项；七场景快照预测PASS（80%区间） | 已实现：总体+分要素外推，趋势图叠加虚线与区间带，负外推告警；不构成预算承诺 |

## 本轮发现与修复索引

A/B：共享构建指纹、锁指纹、解释器/FTS探针、manifest退出码、发行/原件/开发模式分开、外置模型只读。C/D/E：缺证语义、全告警覆盖、有限数、先过滤后检索。F/G：季度与双厂上下文、已完成结果复用、实际产物审核STALE。H：行动插槽统一渲染、两类残留、正文锚点目录、左对齐与数字断行。I：完整行动合同、严格通知协议、畸形响应保持既有证明状态。J：唯一当前manifest、历史回执和本轮区分。

模型真实联调另发现数值引用正确但角色错误，已增加确定性告警事实编译；无效条目不能进入正文。仍需真实评审对专业归因和报告可读性评分。

本轮最终运行、代码版本、测试计数、模型调用与逐页检查只认 `current_run.json` 及其绑定回执。先前模型PASS但报告正文绑定失败、公开归档依赖Git、版式缺陷以及证据名称误拒均保留原始失败结论；修复后的离线重验与新API请求分别记录。自动维度通过也不代表真人归因、可读性或比赛整体验收通过。来源末页留白仍有优化空间。

应用代码与真实模型生成固定于 `47c58069f1bc449d6bda18815f5276d44e72acdb`（`delivery_20260918_47c5806`）。恢复授权资源后的最终受测交付为 `6ff894fd389854ed11fd64cdea6bdfc2a7031cef`，运行 `release_20260918_6ff894f`。本地256项回归、无私有资源/无密钥干净归档190项、真实浏览器8组通过；正式verify退出0，自动维度PASS。七场景均为本轮新DeepSeek调用（非旧GLM记录或缓存），合计10次模型请求，模型身份核验和解释合同7/7通过；Word/PDF与模拟送达7/7通过。随后真实浏览器流程另3次模型请求，账本106→116→119，不能混作七场景推理次数。失败修复历史保留，不追认旧运行。

最终38页PDF已逐页实际看图，字体嵌入/残留插槽/数值与解释绑定另作机器检查。存在一处S2第3页复合单位在斜线后断行：DOCX已带不换行控制，当前LibreOffice仍换行，数字未改；部分来源末页留白偏多。两项明确作为非阻断版式遗留，不写成版式全完成。真人0–5归因、可读性与正式版式均PENDING，因此 `competition_ready=false`。详细回执均从current_run.json进入。

完整交付提交复验：本地256项（19.37秒），含授权题包的干净归档190项（17.42秒）；78资源哈希匹配，仓内配置可直接导入原题并验证季度独立汇总。七场景重编译全部通过且复用47c的七份解释，模型新增请求0（账本119→119）。38页重新渲染，35页与先前实看PNG字节一致，三个合成首图发生像素变化并重新实看；原题页及已知版式遗留不变。静态交付仍保留47c已评读原文件及其准确来源，未重命名成新实调。
