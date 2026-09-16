/* Update the existing portable report in place. No new app, ID or runtime. */
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const crypto = require('crypto');
const root = path.resolve(__dirname, '..');
const output = process.argv[2] || path.join(root, '07_交付/artifact.json');
const htmlPath = path.join(root, '07_交付/药析证链_制药成本智能分析一等奖方案.html');
const read = relative => JSON.parse(fs.readFileSync(path.join(root, relative), 'utf8'));
const optional = relative => fs.existsSync(path.join(root, relative)) ? read(relative) : null;
const artifact = JSON.parse(fs.readFileSync(output, 'utf8'));
const htmlOriginal = fs.readFileSync(htmlPath, 'utf8');
const generatedAt = new Date().toISOString();
const audit = read('06_评测/数据治理审计.json').audit;
const run='06_评测/incremental_20260916/';
const retrieval = optional(run+'retrieval/v4_final/retrieval_results.json') || read('06_评测/retrieval_results.json');
const reports = optional(run+'scenario_reports_delivery.json') || [];
const verification = optional(run+'verification.json');
const snapshots = Object.fromEntries(['S1','S2','S3','Q2'].map(id => [id, read(`07_交付/业务报告/${reports.find(r=>r.scenario===id).job_id}/record.json`).snapshot]));
const benchmark = read(`07_交付/业务报告/${reports.find(r=>r.scenario==='S2').job_id}/record.json`).benchmark;
const modelLive = optional(run+'glm_probe.json');
const reportsPassed = reports.length===4 && reports.every(r=>r.acceptance?.overall==='PASS');
const modelStatus = modelLive?.status || 'NOT_RUN';
const model = 'glm-5.3-flash';
const reportSummary = reports.map(r => `${r.scenario}：${r.status}，DOCX ${r.artifacts?.docx?.status || 'NOT_RUN'} / PDF ${r.artifacts?.pdf?.status || 'NOT_RUN'}`).join('；');
const metric = (s,k) => Number(s.metrics[k].value);
const statusText = verification ? `统一初版FINAL_STATUS=${verification.status.FINAL_STATUS==='PASS'&&!reportsPassed?'待重核（统一记录PASS但当前报告源含降级）':verification.status.FINAL_STATUS}；COMPETITION_READY=${verification.status.COMPETITION_READY}。人工评分、最终视频/PPT与正式发布待完成；Docker运行${verification.status.DOCKER_RUNTIME}，不是本轮原生初版必须项。` : '统一初版状态待06_评测/verification.json；人工评分、最终视频/PPT和正式发布未完成，COMPETITION_READY不能为PASS。';
const req = artifact.snapshot.datasets.requirements;
const groups = [
 [['R01','R02'], '已验证','原Word工作模板完成位置绑定与跨run填充；四场景导出有实际文件','python-docx XML位置映射；101唯一/108次原占位符，原模板只读','04_方案与文档/placeholder_map.json；06_评测/scenario_reports.json'],
 [['R03','R04','R05','R06','R07','R08','R35'],'已验证','7PDF/116页，真实CPU向量及中文FTS5检索；支持PDF/DOCX/TXT位置证据','PyMuPDF/python-docx；LlamaIndex Core节点与检索适配；Chroma+中文BM25+RRF','06_评测/retrieval_results.json；tests/test_knowledge.py'],
 [['R09','R10','R11','R12'],reportsPassed?'已验证':'部分满足',reportsPassed?'四场景月度/专题/季度实际任务SUCCEEDED；DOCX/PDF分别PASS，真实模型非缓存':'月度/专题/季度DOCX和PDF已生成；任务存在降级，不能冒充完整模型报告通过','持久worker、固定指标快照、原Word工作模板、LibreOffice逐任务转换','06_评测/scenario_reports.json；报告完整状态待verification.json'],
 [['R13','R22'],'待人工','归因合理性量表与待评分记录已保留；无人类已评分结果','事实、文档事实、待核查假设、建议分开；真人按0—5分量表评分','06_评测/human_scoring.json；人工签名/评语待填'],
 [['R14','R15','R16','R23','R24','R29'],'已验证','10CSV/334行；16组810算术观测和51连续组无失败；单位0/总额31条阈值告警','Decimal；显式比较月份；季度加权；二厂−一厂以一厂为分母；严格±10%','06_评测/golden.json；data_metrics_tests.log；threshold_golden.json'],
 [['R17','R18','R19','R25','R26','R27','R28','R36'],'已实现','四入口React界面、ECharts趋势/结构/瀑布、精确表、三步对标和证据抽屉已实现','React+TypeScript+Vite+ECharts；截至筛选月；请求竞态防护；图表销毁','05_原型/frontend；06_评测浏览器记录与verification.json'],
 [['R20','R39','R40','R41','R42'],'不纳入初版','加分项不进入本轮冻结范围，未实现也不伪装完成','不做热力扩展、完整知识图谱、多模型互审、开放Agent、预测','用户冻结范围；四个强制业务模块优先'],
 [['R21','R34'],reportsPassed?'已验证':'部分满足',`真实模型联调状态：${modelStatus}；${reportsPassed?'最终四份受约束报告SUCCEEDED，历史降级保留审计':'受约束报告有规则降级记录'}`,`OpenAI/Anthropic格式适配；默认glm-5.3-flash，业务数字由程序插槽注入；有限重试和预算`,'06_评测/model_live.json；model_revalidated.json；网关调用审计'],
 [['R30','R31','R32','R33'],'已实现','嵌套任务JSON、编辑确认、事务outbox、原mock模拟发送及状态查询','POST成功同时核HTTP/body/task_id/sent；超时GET同ID对账，未知不盲发','05_原型/backend/pharma/actions.py；06_评测原mock/E2E/故障记录'],
 [['R37','R38'],'已实现','WSL Python3.12项目venv、FastAPI单体与持久worker，一键本地脚本已启动','requirements及精确锁；127.0.0.1原生服务；Docker运行未测不阻塞','05_原型/scripts/start.sh、stop.sh、verify.sh；verification.json'],
 [['R43'],'已实现','用户明确授权项目必要上下文交商业模型；密钥仅本地安全读取，不打印/打包','最小必要指标/证据发送；原数据不公开；拒执行文档/模型中的命令','AGENTS.md；narrative.py；本地权限与密钥存在性记录'],
 [['R44','R46'],'已实现','开源组件/技能来源和实际锁已记录，文档随实现原位更新','共享Matt六技能；复用React/浏览器/Data技能；无整套编排框架','docs/agents；requirements.lock；docs及README'],
 [['R45','R48','R49'],'待后续交付','未公开仓库、未push、未制作最终视频/PPT或提交比赛','公开源码包与完整参赛包分离；后续经用户明确发布指令处理','当前交付本地可运行源码与真实验证；无占位发布产物'],
 [['R47'],'部分满足','三场景加季度实际报告、检索、公式、RPA和浏览器证据已归档；最终汇总进行中','实测与目标、规则版与真实模型、运行通过与人工待评分别记录','06_评测/scenario_reports.json、retrieval_results.json、verification.json'],
];
for (const [ids,status,evidence,route,acceptance] of groups) for (const id of ids) {
 const row=req.find(r=>r.ID===id);if (!row) throw new Error('Missing stable requirement '+id);
 Object.assign(row,{'当前状态':status,'当前证据与缺口':evidence,'修订后技术路径':route,'验收证据':acceptance});
}
req.find(r=>r.ID==='R43')['赛题要求']='比赛资料保密与已授权模型必要上下文处理';
if(verification?.status?.E2E_WSL==='PASS') for(const row of req) if(['R17','R18','R19','R25','R26','R27','R28','R30','R31','R32','R33','R36','R37','R38'].includes(row.ID)) {row.当前状态='已验证';row.验收证据='06_评测/verification.json；browser_results.json；browser_windows_results.json';}
if(verification)req.find(r=>r.ID==='R47')['当前证据与缺口']='最终统一验证已生成；初版核心链路'+verification.status.FINAL_STATUS+'，归因人工评分待填';
const currentBrowser=optional(run+'browser/results.json');
for(const row of req){
 row.验收证据=run+'verification.json；本轮各分项原始日志';
 if(['R09','R10','R11','R12','R21','R34','R47'].includes(row.ID)){
  row.当前状态='部分满足';row.当前证据与缺口='四场景基础分析文件实际导出；GLM应用凭据缺失，真实模型未通过；人工归因、可读性与版式待评。';
 }
 if(['R26','R27','R28'].includes(row.ID)){
  row.当前状态='部分满足';row.当前证据与缺口='已修复章节内容、跨厂结构和可执行建议；功能存在不等于单份报告验收通过。默认业务输出与机器审计分离，视觉与真人评分见本轮记录。';
 }
 if(['R17','R18','R19','R25','R36'].includes(row.ID)){
  row.当前状态=currentBrowser?.status==='PASS'?'已验证':'已实现';row.当前证据与缺口='三要素结构、变动瀑布、趋势及三步对标有实现；筛选、图表交互、终态下载以本轮浏览器记录为准。';
 }
 if(['R14','R15','R16','R23','R24','R29'].includes(row.ID))row.当前证据与缺口='本轮独立CSV/Fraction复算96快照、18组跨厂、5574观测零差异；环比同比预算贡献分别绑定。';
}
const statusOrder=['已验证','已实现','部分满足','待人工','待后续交付','不纳入初版'];
artifact.snapshot.datasets.compliance_summary=statusOrder.map(status=>({'当前状态':status,'要求数':req.filter(r=>r.当前状态===status).length,'占比':Number((100*req.filter(r=>r.当前状态===status).length/req.length).toFixed(1)),'总要求':req.length}));
const details=[];const comparisons=[];
for(const id of ['S1','S2','S3']){
 const s=snapshots[id];const elements=s.elements;const record={'场景':`${s.product}·${s.month}`,'单位成本元每盒':metric(s,'unit_cost'),'环比百分比':metric(s,'mom'),'同比百分比':metric(s,'yoy'),'预算差异百分比':metric(s,'budget'),'跨厂差异百分比':id==='S2'?Number(benchmark.summary[0].rate):null,'确定性结论':id==='S3'?'单位成本下降；总成本492800→595700元，不能把设备事件当作已证实净因果':`单位成本变动${s.period_changes.unit_cost.mom.delta}元/盒；材料贡献${elements[0].unit_contribution}%`,'证据边界':id==='S2'?'跨厂方向二厂−一厂，分母一厂；二厂缺原料明细':'原料单位消耗成本不是采购价/耗量；行情与设备只支持待核查假设'};
 details.push(record);
 for(const [key,label] of [['mom','环比'],['yoy','同比'],['budget','预算差异']]) comparisons.push({'产品':s.product,'比较基准':label,'差异率':metric(s,key),'场景月份':s.month,'单位成本':metric(s,'unit_cost'),'主要贡献':'直接材料','主要贡献率':elements[0].comparisons[key].unit.contribution===null?null:Number(elements[0].comparisons[key].unit.contribution),'基期':elements[0].comparisons[key].unit.comparison_period,'分子元每盒':elements[0].comparisons[key].unit.numerator,'分母元每盒':elements[0].comparisons[key].unit.denominator});
}
artifact.snapshot.datasets.scenario_detail=details;artifact.snapshot.datasets.scenario_comparison=comparisons;
artifact.snapshot.datasets.stack_decisions=[
 ['前端','React + TypeScript + Vite + ECharts','四入口与精确表/证据抽屉','Chrome/Edge各按实际运行证据标记'],
 ['API','Python 3.12 + FastAPI + Pydantic','公开接口与输入验证','单体；127.0.0.1'],
 ['分析','Decimal + DuckDB + Parquet','确定性指标/数据版本','校验后原子发布，失败保留旧快照'],
 ['状态','SQLite WAL + 单持久worker','任务、审计、事务outbox','并发幂等；恢复检查点'],
 ['RAG','LlamaIndex Core + Chroma + FTS5 BM25 + RRF','中文切片与双路检索','CPU ONNX小embedding；向量故障明确降级'],
 ['模型','GLM-5.3-Flash + 可替换协议网关','证据和指标插槽解释','有限超时/修复；规则版清晰标记；未知费用UNKNOWN'],
 ['报告','python-docx + matplotlib + LibreOffice','原模板DOCX与PDF','格式分别记状态；正式输出验证后归档'],
 ['部署','WSL本地脚本 + requirements精确锁','启动API/worker/原mock','复用Linux环境；Docker runtime未运行不伪称通过'],
].map(([层级,选择,责任,兼容与降级])=>({层级,选择,责任,兼容与降级}));
// Old page-count data remains valid; obsolete page-per-chunk counts are not live index metrics.
for(const d of artifact.snapshot.datasets.corpus_documents){d.切片数=null;d.清洗字符=null;d.删除重复行=null;}
const comparisonTable={id:'scenario-contribution-table',title:'三场景材料贡献与比较口径',dataset:'scenario_comparison',description:'贡献分子为材料单位成本差额，分母为同一比较对象的总单位成本差额；单位元/盒，贡献率为百分比。',columns:['产品','比较基准','基期','分子元每盒','分母元每盒','主要贡献率'].map(field=>({field,label:field,type:field==='主要贡献率'?'number':'text',format:field==='主要贡献率'?{maximumFractionDigits:2}:undefined}))};
artifact.manifest.tables=artifact.manifest.tables.filter(t=>t.id!==comparisonTable.id);artifact.manifest.tables.push(comparisonTable);
if(!artifact.manifest.blocks.some(b=>b.id==='scenario-contribution-table-block'))artifact.manifest.blocks.splice(artifact.manifest.blocks.findIndex(b=>b.id==='scenario-meaning'),0,{id:'scenario-contribution-table-block',type:'table',tableId:comparisonTable.id});
const all=retrieval.metrics;
const blocks={
 'title':'# 药析证链：赛题合规审计与详细技术方案\n\n药衡智析——基于RAG与大模型的制药企业产品成本智能分析报告系统。',
 'technical-summary':`## 实施摘要\n\n本地初版已经具备确定性计算、混合检索、模板报告与模拟RPA闭环源码及运行证据。${reportSummary}。\n\n本轮独立CSV/Fraction复算5574项观测无差异。混合检索28题Recall@5实测${all.hybrid.all['Recall@5'].toFixed(4)}，不是目标值抄录。\n\n${statusText}`,
 'scope':'## 状态口径\n\n已验证表示对应分项已有运行记录；已实现表示代码已落地，整体验收仍读verification.json；部分满足表示真实缺口或降级；待人工与待后续交付均不能算比赛完成。保留原49行追踪结构，不把自设性能、多供应商或Docker运行当成赛题强制条件。业务数据截至2026-06，实施审计日期2026-09-16。',
 'verdict':`## 当前证据与剩余条件\n\n四份真实DOCX/PDF已生成，当前任务状态详见下文与scenario_reports.json。四份报告按文件、计算、章节、证据、可读性、视觉、任务及模型八维验收；历史失败/规则降级记录保留，不能以单次模型成功替代报告验收。人工归因评分、最终视频/PPT、公开发布未完成。${statusText}`,
 'architecture-overview':'## 实际架构\n\nReact/ECharts → FastAPI → 固定指标快照；DuckDB只读Parquet、SQLite持久任务与审计。单worker依次检索、受约束生成、原Word模板填充、LibreOffice转换、验证归档；原mock默认8090。LlamaIndex适配的Chroma向量与中文FTS5 BM25各自排序后RRF融合。没有开放Agent或GPU生成模型。',
 'component-contracts':'## 公开数据契约\n\n指标含metric_id、原值/展示值、单位、公式、分子分母、比较期、源行和哈希。Finding区分数字事实、文档事实、原因假设、证据不足和建议。报告/看板共享快照；任务保存已确认payload哈希。API以实际OpenAPI为准，详细字段在docs/data_contract.md。',
 'data-path':'## 数据保护与导入\n\n原始CSV/ZIP/PDF/模板只读。ZIP安全检查保留原名→修复名映射，CSV继续UTF-8 BOM读取。字段白名单、主键、数值、关联、勾稽失败留下拒绝记录，不发布新快照。成功先写临时Parquet再原子切换清单，旧快照保留。',
 'metric-method':'## 成本公式与边界\n\n单位成本=材料+人工+制造费用，总成本=产量×单位成本；月份显式连接，缺月或零分母N/A。贡献=要素变动额/同口径总变动额，负值和大于100%不裁剪。严格±10%边界不触发；实际45个要素环比单位0条/总额31条触发。季度Σ总成本/Σ产量，必须完整对应季度。跨厂二厂−一厂，以一厂为分母；交换工厂分母随之改变。',
 'scenario-meaning':`## 三场景与季度\n\nS1银黄2026-05单位11.21元/盒，材料/人工/制造费用单位变动0.22/0.03/0.06元。S2板蓝根二厂7.97、一厂7.47，正向+6.6934404%、反向−6.2735257%。S3六味地黄2026-03单位17.60→17.02、总额492800→595700；设备页4维修记录只能支持待核查假设。\n\n银黄2026Q2总额1796180元、产量163000盒，加权单位${snapshots.Q2.metrics.unit_cost.value}元/盒；独立Fraction golden与生产接口逐项核验。`,
 'rag-pipeline':`## 真实混合检索\n\n7PDF共116页，本轮索引${retrieval.built.chunks}切片。PyMuPDF文字解析、python-docx标题/表格和TXT位置；中文jieba词典同时用于FTS入库/查询。向量使用${retrieval.built.embedding.repo}，锁${retrieval.built.embedding.sha}，CPU ONNX量化运行。BM25越小越相关，RRF按名次而非原分数相加；不隐式额外调用模型改写查询。`,
 'rag-quality':`## 检索评测实测\n\n冻结28道有来源位置的问题（20开发、8保留）及负例。BM25 Recall@5=${all.bm25.all['Recall@5'].toFixed(4)} / MRR=${all.bm25.all.MRR.toFixed(4)}；向量=${all.vector.all['Recall@5'].toFixed(4)} / ${all.vector.all.MRR.toFixed(4)}；混合=${all.hybrid.all['Recall@5'].toFixed(4)} / ${all.hybrid.all.MRR.toFixed(4)}。目标0.85与实测分开（${all.hybrid.all['Recall@5']>=0.85?'本次达到':'本次未达到'}）；混合当前低于BM25，不宣传全面优于单路，保留集未用于调参。`,
 'report-compiler':`## 原模板与四份业务报告\n\n原模板101唯一占位符、108次出现、9表、3分节保留；工作副本按XML位置拆分人工/制造费用同名金额与比例。动态表按真实块插入，中文字体和图表由指标快照生成。DOCX/PDF分开核验和下载。\n\n${reportSummary}。模板数字映射、残留占位符、章节、表格和代表页证据见scenario_reports.json及06_评测截图。`,
 'model-gateway':`## 模型接入与约束\n\n应用默认GLM-5.3-Flash，实际模型记录${model}；本次探测状态${modelStatus}。保留OpenAI及Anthropic请求格式兼容；其他供应商未做真实调用即不标PASS。用户已授权必要上下文处理，密钥只从本地文件/环境读取。数字由程序填入metric插槽，文档事实须来源位置和原文支持，失败输出明确规则版。调用日志记模型、usage、耗时、失败和实际/估算费用，未知UNKNOWN。`,
 'benchmark-engine':'## 跨厂三步法\n\n差异总览→三要素及可用明细→检索来源、待核查原因和建议。默认二厂−一厂；一厂有原料/费用/工时，二厂缺明细明确显示。行业每盒成本按10支/20袋/60粒换算后比较静态题包分位数；市场价格不是企业采购价，缺收入不计算毛利率。',
 'rpa-engine':'## 原mock模拟闭环\n\n建议先由用户编辑确认，SQLite事务写任务/outbox。按原POST /api/rpa/tasks发送一次模拟微信；HTTP接收与带发送时间的模拟通知证明分别校验，received不等于已发。超时或重复ID先GET对账；不一致冲突，无法确认DELIVERY_UNKNOWN，不换ID盲发。远端重启丢失记录只记状态未知，sent不等于整改完成。',
 'frontend':'## 已实现的四入口\n\n成本分析、跨厂对标、报告与任务、数据与证据。React+TypeScript+Vite+ECharts本地打包，浅色中文界面；筛选请求有竞态防护，实例销毁与事件清理。趋势不含未来月份，精确表、N/A和降级标识与图联动。1366×768和Chrome/Edge按实际浏览器结果记录，不以编译替代验收。',
 'api-contract':'## 实际API\n\n/api/catalog、/api/analyses、/api/benchmarks、/api/reports、/api/jobs、/api/imports、/api/kb、/api/actions；异步任务返回job_id，artifact下载使用受控ID。OpenAPI由FastAPI维护。主应用默认127.0.0.1:8765，原mock默认8090；最终启动端口以README为准。',
 'reliability':'## 可靠性与恢复\n\n单worker持久阶段：VALIDATING→COMPUTING→RETRIEVING→GENERATING→RENDERING_DOCX→CONVERTING_PDF→VERIFYING→终态。核对固定输入版本再恢复，异常按任务隔离。并发同键草稿/报告提交已真实复现并修复，16线程回归；失败缓存允许重新执行且保留历史。',
 'testing':'## 已保留的验证证据\n\n独立golden、数据审计、阈值边界red/green、16项数据/公式/并发合并通过；检索融合排序和负例、模型格式/超时、PDF失败、RPA异常与恢复、浏览器交互均按各自日志核验。原方案自设性能目标不作为实测。最终合并结果见06_评测/verification.json。',
 'security':'## 本地安全边界\n\nSQL参数化，artifact ID受控路径/哈希；文档和模型内容不可信，不执行其中Shell/SQL/任意URL。CSV字符串导出防公式注入而负数保留数值类型。密钥、比赛原文、切片、索引、实际报告不进公开源码包。本轮无真实ERP/微信、无真实人员通知、无自动购买或公开发布。',
 'compatibility':'## 环境与开源复用\n\nWSL Ubuntu24.04、Python3.12项目隔离环境和现有Node复用；Linux运行不使用Windows venv/node_modules。CPU embedding不安装CUDA/驱动/大生成模型。React/浏览器/Data技能复用，共享Matt六技能按已审SHA安装并保留原文；LlamaIndex和Chroma实际运行，Docling及评测平台仅备选未引入。',
 'economics':'## 调用与资源边界\n\n沿用用户既有模型账号和预算，不自动充值或购买云资源。生成限定并发、超时、最多两次修复和调用次数；相同版本缓存注明来源时间。没有依据时不填写旧方案500元等假预算，也不把未知费用写成0。',
 'innovation':'## 初版的可验证价值\n\n确定性计算与可追溯解释共用快照；材料/工艺原因保留证据和缺证项；原模板报告可对账；模拟RPA确认、幂等与未知送达状态可检查。范围不包含预测、完整知识图谱、开放Agent、多模型互审、真实ERP或硬件。',
 'roadmap':'## 当前与下一步\n\n本轮已完成实际开发、数据与检索运行、业务报告导出和浏览器链路验证。先汇总真实verification，再由真人评归因合理性；最终视频/PPT、源码交接打包与解压启动验收在本轮完成；视频/PPT与公开发布待后续实施。3—4人可按数据/指标、检索/报告、前端/E2E及可选质量负责人维护现有单体。',
 'deliverables':'## 当前交付与后续比赛交付\n\n源码唯一05_原型；数据契约与实施文档原位更新；06_评测保留真实golden、检索/故障/E2E记录，07_交付/业务报告保留四场景DOCX/PDF。现有方案HTML和artifact本次同步更新，公开仓、比赛提交、视频/PPT尚未执行。',
 'questions':`## 剩余条件\n\n${statusText}\n\n历史模型请求与报告降级保留；本轮分项修复证据不能代表报告总体验收通过；中文浏览器/PDF视觉验证按记录逐项判断。采购价格/实耗、二厂明细、收入和完整因果链缺失时保持证据不足。GLM应用真实参与和真人评审仍待完成。`,
 'data-notes':`## 数据、方法与更新说明\n\n此页为本地实施与技术审计报告，业务源数据截至2026-06。本次从现有原始字节哈希、独立golden和运行记录更新，未向外部数据库或真实业务系统写入。更新时间${generatedAt}。${verification ? '已发现统一验证文件；具体键值以该文件为准。' : '统一verification.json尚在生成，本文不提前标整体验收PASS。'}\n\nData build-report技能按用户原位约束用于来源复核、状态区分和视觉检查；没有新建替代Data app或更换原便携runtime。`,
};
Object.assign(blocks,{
 'title':'# 药析证链：赛题合规审计与详细技术方案\n\n药衡智析——基于RAG与大模型的制药企业产品成本智能分析报告系统。',
 'report-compiler':`## 业务报告与验收\n\n六个固定章节及原模板对应关系保留；重复封面、空文控表与IT阅读指南已整理。首页展示产品、工厂、期间、发现及建议；导出前按实际分页更新目录。成本结构、变动瀑布、趋势、跨厂结构直接读取指标快照。正文及图表使用项目内Noto Sans SC TrueType与SIL OFL许可证，修复原Type1子集缩放漏绘；Linux以临时Fontconfig加载，Windows按同字体复核。\n\n${reportSummary}。文件可打开、计算一致、章节实质完整、证据适用、内容可读、视觉合格、任务可执行、模型实际参与分开记录。强制环节未全通过，报告不合格。机器审计附件保存JSON、哈希与原证据，业务正文仅保留短来源与限制。真人评分仍待评。`,
 'model-gateway':`## GLM-5.3-Flash应用网关\n\n实际默认ID为glm-5.3-flash，中国站通用端点https://open.bigmodel.cn/api/paas/v4；国际账号使用官方对应通用端点。禁止Coding专用端点进入业务运行时。模型思考不传旧disabled，依官方支持配置。\n\n本机凭据缺失，探测状态${modelStatus}；文本、结构化、工具、流式、真实限流与超时均未实测。ZCode CLI在队员电脑，接续项见docs/ZCODE_HANDOFF.md。基础分析明确降级，不切回DeepSeek；历史DeepSeek记录保留原模型值。`,
 'rag-engine':`## 产品与期间适用的混合检索\n\nPDF按位置读取、产品标题跨页继承，维修表按事件期间独立切片。空产品标签不代表通用。引用按产品、工厂、规格、期间与版本核验；多版本冲突不静默合并。\n\n本轮历史已见集混合Recall@5为0.9286，BM25为1.0000。保留语义+BM25能力，原开发/保留集均已查看，只作为历史回归；不能声称独立泛化提高或混合全面更优。产品串扰、跨期、冲突和无证据回归见本轮检索目录。`,
 'testing':'## 本轮验证范围\n\n计算由独立CSV/Fraction复算；检索包含负例与适用性合同；模型格式与降级用HTTP夹具，GLM应用实调受凭据阻塞。最终四场景23页全部逐页渲染查看；70项Python回归、应用浏览器48项、方案浏览器18项和隔离原mock9项通过。浏览器在1366×768和1920×1080核验筛选、证据、生成、下载、任务及失败状态。机器视觉检查不替代真人0—5归因评分及可读性评审。',
 'deliverables':'## 可运行源码交接\n\n现有05_原型源码、锁文件、工作模板、依赖检测/启动脚本、脱敏配置、真实验证与样例保留。公开源码候选与仅供队内的题包、知识和原始数据分离；不含密钥、个人配置、虚拟环境、node_modules、缓存及作废产物。解压启动验收范围与限制见交接记录。',
 'data-notes':`## 数据与状态\n\n本轮增量修复记录位于${run}。历史记录保持独立，不用当前GLM配置改写历史DeepSeek模型值。截至5月的报告只使用1—5月趋势；季度回归独立使用完整季度。真人审核缺失保持待评。`
});
// Locate the RAG narrative by stable block ID if this shell uses a different name.
for(const id of Object.keys(blocks))if(id!=='rag-engine' && /rag|retriev/.test(id))blocks[id]=blocks['rag-engine'];
for(const block of artifact.manifest.blocks) if(block.type==='markdown'){
 if(!blocks[block.id])throw new Error('Unupdated block '+block.id);
 block.body=blocks[block.id];block.sourceId='implementation-evidence';
}
artifact.manifest.description='药衡智析本地初版实施审计：确定性计算、真实混合检索、模板报告与模拟RPA；实测、降级和待人工明确区分。';
const sources=[{id:'implementation-evidence',label:'本轮实施状态与真实运行证据',path:'docs/implementation_status.md'},
 {id:'quality-checks',label:'本轮独立CSV/Fraction复算',path:run+'data/report_independent_audit.json'},
 {id:'scenario-data',label:'独立golden与四场景指标快照',path:'06_评测/golden.json'},
 {id:'retrieval',label:'真实BM25/向量/混合28题实测',path:run+'retrieval/v4_final/retrieval_results.json'},
 {id:'reports',label:'四场景DOCX/PDF分别验证',path:run+'scenario_reports_delivery.json'},
 {id:'verification',label:'最终统一验证（生成中则以分项记录为准）',path:run+'verification.json'}];
artifact.sources=sources;artifact.manifest.sources=sources;
for(const item of [...artifact.manifest.charts,...artifact.manifest.tables]){
 item.source={label:'本次本地受控证据快照',path:'07_交付/artifact.json',metricDefinitions:'数据源为当前审计、独立golden和实际运行记录；非实时ERP。'};
 if(item.id==='compliance-status-chart')item.description='49条沿用原追踪矩阵；状态来自本次分项证据，非全比赛完成率。';
 if(item.id==='scenario-comparison-chart'){item.title='三个场景的单位成本比较';item.description='单位为百分比，分别为环比、同比和预算偏差；跨厂采用独立明细表的二厂−一厂口径。';}
 if(item.id==='corpus-pages-chart')item.description='原7PDF共116页；当前实际索引以本轮检索记录为准。旧逐页切片/清洗计数已清空，防混作本轮实测。';
 if(item.id==='compliance-matrix-table')item.description='保留原行ID和字段结构；功能实现、分项通过、降级、人工及后续交付分别记录。';
 if(item.id==='scenario-table')item.description='跨厂差异仅S2展示：二厂−一厂，以一厂为分母；其他行空值不是0。';
}
artifact.generatedAt=artifact.manifest.generatedAt=artifact.snapshot.generatedAt=generatedAt;
artifact.snapshot.status='ready';
// Preserve the original portable shell and compressed runtime byte-for-byte.
const escape = x=>String(x??'N/A').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const markdown = text=>text.split(/\n\n+/).map(p=>p.startsWith('## ')?`<h2>${escape(p.slice(3))}</h2>`:p.startsWith('# ')?`<h1>${escape(p.slice(2))}</h1>`:`<p>${escape(p).replaceAll('\n','<br>')}</p>`).join('');
function fallbackTable(item){
 const rows=artifact.snapshot.datasets[item.dataset]||[];const columns=item.columns||Object.keys(rows[0]||{}).map(field=>({field,label:field}));
 return `<section class="portable-block"><h2>${escape(item.title)}</h2><p>${escape(item.description||'')}</p><div style="overflow:auto"><table><thead><tr>${columns.map(c=>`<th>${escape(c.label||c.field)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${columns.map(c=>`<td>${escape(r[c.field])}</td>`).join('')}</tr>`).join('')}</tbody></table></div></section>`;
}
const fallback='<main id="data-analytics-portable-fallback" class="portable-fallback" data-portable-fallback="true" data-portable-surface="report"><header class="portable-page-header"><div class="portable-page-heading"><h1>'+escape(artifact.manifest.title)+'</h1><p>'+escape(artifact.manifest.description)+'</p></div></header><div class="portable-block-stack">'+artifact.manifest.blocks.map(b=>b.type==='markdown'?`<section class="portable-block portable-markdown" data-artifact-block-id="${escape(b.id)}">${markdown(b.body)}</section>`:fallbackTable((b.type==='table'?artifact.manifest.tables:artifact.manifest.charts).find(x=>x.id===(b.tableId||b.chartId)))).join('')+'</div></main>';
const serialized=JSON.stringify(artifact);
const payload=zlib.gzipSync(Buffer.from(serialized)).toString('base64').match(/.{1,100}/g).join('\n');
const pattern=/<template id="data-analytics-portable-artifact-payload-source"[^>]*>[\s\S]*?<\/template>/;
if(!pattern.test(htmlOriginal))throw new Error('Portable artifact payload not found');
let html=htmlOriginal.replace(/<main id="data-analytics-portable-fallback"[\s\S]*?<\/main>/,fallback).replace(pattern,`<template id="data-analytics-portable-artifact-payload-source" data-compression="gzip-base64">\n${payload}\n</template>`);
const runtimePattern=/<template id="data-analytics-portable-reader-runtime-source"[^>]*>[\s\S]*?<\/template>/;
if(html.match(runtimePattern)?.[0]!==htmlOriginal.match(runtimePattern)?.[0])throw new Error('Runtime unexpectedly changed');
const decoded=JSON.parse(zlib.gunzipSync(Buffer.from(html.match(pattern)[0].replace(/^<template[^>]*>|<\/template>$/g,'').replace(/\s/g,''),'base64')).toString());
if(JSON.stringify(decoded)!==serialized)throw new Error('Embedded artifact mismatch');
fs.writeFileSync(output+'.tmp',JSON.stringify(artifact,null,2));fs.renameSync(output+'.tmp',output);
fs.writeFileSync(htmlPath+'.tmp',html);fs.renameSync(htmlPath+'.tmp',htmlPath);
const validation={status:'PASS',scope:'artifact schema/data and embedded payload consistency; browser rendering separate',generatedAt,stable_title:artifact.manifest.title,stable_block_ids:artifact.manifest.blocks.map(b=>b.id),requirements: req.length,runtime_unchanged:true,payload_matches_artifact:true,html_sha256:crypto.createHash('sha256').update(html).digest('hex'),final_verification_present:Boolean(verification)};
fs.writeFileSync(path.join(root,run+'report_artifact_validation.json'),JSON.stringify(validation,null,2));
console.log(JSON.stringify({artifact:output,html:htmlPath,...validation}));
