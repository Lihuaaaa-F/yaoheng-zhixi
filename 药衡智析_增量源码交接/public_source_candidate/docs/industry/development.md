# 行业包开发与验收合同

本轮采用模块化单体。`backend/pharma/industry.py` 提供规范化事实、聚合、可比性与不可变 `AnalysisContext`。现有制药专用导入/指标适配器保留在 `ingestion.py` / `metrics.py`，公共 `industry_packs/pharmaceutical/source_contract.json` 仅保留来源字段、要素定义及合成主数据白名单；本次已授权发布的比赛主数据与词典单独保存在应用根 `competition_configuration/`，通过既有 `PHARMA_PRIVATE_MASTERDATA_FILE` 与 `PHARMA_PRIVATE_TERMINOLOGY_FILE` 显式加载，不与包内合成主数据混淆。没有换栈、引入插件框架或复制后端。新增第三方依赖：无。

## 包和企业不是同一个维度

`industry_packs/<id>/manifest.json` 有稳定 ID、版本、`>=1,<2` 核心兼容声明、制造模式、能力所需事实、字段映射/知识/模板/评测入口和可信策略名称。目录为本机管理员安装位置，不接收用户上传 Python、SQL、网络安装命令。`STRATEGIES` 仅允许部署代码注册。`mapping.json` 当前是包映射声明与扩展接口；通用 `import_csv` 仅接受规范字段名，尚未执行任意来源列映射。

`enterprise.json` 是公开合成企业配置，含企业 ID、数据集、政策、币种、计量单位、产品版本和岗位。本次用户授权仅涵盖该比赛资料与交付，不自动授权今后真实企业主数据或知识公开；真实企业资料默认使用工程外受控配置，密钥只从项目环境变量/受控文件读取。行业政策不能由行业名称推定。每包默认一个合成企业；同包可通过 `register_enterprise(pack_id, configuration_path)` 注册多个本地企业配置。注册表在忽略的运行目录，配置与专属 `facts.json` / `knowledge.json` 可在工程外；无上传执行能力。每份配置有独立企业ID、数据集/政策/主数据，并校验事实的企业、产品版本、单位和币种。ERP连接与管理员安装界面未实现。

现有三个包有独立合成企业：制药 `pharmaceutical:synthetic-pharma`、机械 `mechanical_demo:synthetic-mechanical`、化工 `chemical_demo:synthetic-chemical`。两制造样例用于框架验证，不是完整行业适配。三个包均使用 `DEMO-01`，机械/化工均使用相同原始文档 ID，隔离以完整上下文为准。显式配置 `PHARMA_DATA_PACKAGE` 才显示 `pharmaceutical:competition`。赛题原件现按用户最新授权随仓库保留，可指向本仓库原件目录，也可指向经核验一致的工程外副本；应用根 README 提供绝对路径启用命令。赛题原件按源字节保留，不能用修改或改名的赛题数据冒充独立合成行业包。

## 事实与聚合

`CostFact`：企业/工厂、产品及版本、月份和粒度、成本对象、实际/预算/标准情景、要素和父要素、明细/汇总层级、Decimal 金额、币种、分母单位、完工/WIP范围、政策版本、来源行/快照、已归集/驱动重建来源模式。

`QuantityFact`：独立产量关系。按企业、工厂、产品/版本、月份、情景、成本对象和粒度去重；重复导出相同数量不重复累加，冲突数量拒收。成本明细数量连接不会把产量乘以要素数。金额保留源精度，常规金额展示两位；季度单位成本和跨厂表按报告角色展示四位。季度 `Σ金额/Σ独立合格产量`，不平均月单价。零产量单位成本为不可定义，缺期/预算/同比不补零。

`OptionalFact`：工序机时/工时、能耗、采购量价、BOM/配方、报废/返工、联副产品输出的类型化可选接口。已归集成本不与重建成本混加；缺事实返回能力缺口，未实现的 WIP/联副产品分配拒算。机械策略 `machine_hours_per_piece` 的定义是总工序机时/合格件数，不能标为 OEE；化工 `energy_per_kg` 是 kWh/合格净重 kg，不能当电价。

默认拒绝企业、产品版本、币种、包装单位、范围、政策、来源模式冲突；kg↔t有确定换算，件↔kg、L↔kg、盒↔粒没有产品级换算依据就拒绝。现有 comparison 可接受明确月环比、同比、同月实际对预算/标准和跨厂，不因期间或情景不同一律拒绝。`compare(..., alignments=ComparisonAlignment(...))` 支持显式基期对齐：产品/版本绑定的 `UnitConversion`，以及源/目标政策、企业/工厂/产品、期间/情景、审计调整金额和非空证据引用绑定的 `PolicyBridge`。先对基期数量/金额归一化，再计算比较并返回 `alignment_evidence`。kg↔吨因子须符合SI关系，错作用域/空证据拒绝。本轮不自动推导政策调整或汇率。

规范 CSV 入口 `import_csv(cost_path, quantity_path, destination)`；列名就是 Pydantic 字段名。JSON 可先 `NormalizedDataset.model_validate(raw)` 再 `publish_snapshot`。发布前验证类型合同与成本/产量分组，随后写不可变内容文件并原子替换 current 指针；这些验证失败或空导入保留旧指针。可选驱动的产出对象覆盖、量纲等语义由对应分析策略校验，不能把发布成功视为所有专用指标已可用。原题 CSV 继续使用严格制药来源适配器。本轮没有声称连接 SAP/Odoo，也未提供通用 XLSX 上传 UI。

## 不可变上下文与调用

`resolve_context(context_id)` 返回冻结的企业、数据集、包版本、政策、数据/知识快照、模板内容哈希、公式版本；`context_hash` 由全部字段生成。稳定选择 ID 和不可变内容哈希不是一回事。报告创建后保留快照，不能在运行时仅凭选择 ID重新读取新资料。

- `context_catalog()` → 可选企业/行业/能力；`catalog(context_id)` → 合法工厂、产品、期间及单位。
- `analyze_reference(context_id, factory, product, month, analysis_type, basis)` → 与现有报告共享的指标快照。
- `benchmark_reference(context_id, product, month, left, right, analysis_type, basis)` → `(snapshot, comparison)`，对比方向由请求工厂确定。
- `context_services.retrieve(snapshot, query)` → 同一 Knowledge/LlamaIndex/BM25/向量流程。知识候选先按上下文与产品限定。
- `generation_key` 还绑定实际输入、Prompt、模型/供应商、嵌入模型、检索器与参数版本。企业配置内容哈希另作为 `enterprise_config_version` 参与上下文，职责/单位/产品配置变化不能命中旧任务。

能力由包声明、数据与当前服务检查共同确定。目前 Word/PDF 检查本机依赖是否存在；模型凭据配置只标 configured，不能冒充实调。RPA 尚无自动在线探测，能力目录保守标 degraded，实际调度和模拟送达由独立验收确认；连接配置不等于在线或送达，送达不等于整改完成。

## 独立合成标准答案

| 包 | 六月总成本 | 六月合格产出 | 单位成本 | 专用指标 |
|---|---:|---:|---:|---|
| 机械 | 3600 CNY | 120 件 | 30 CNY/件 | 60 小时 / 120 件 = 0.5 小时/件 |
| 化工 | 2400 CNY | 200 kg | 12 CNY/kg | 600 kWh / 200 kg = 3 kWh/kg |
| 制药合成 | 1350 CNY | 150 盒 | 9 CNY/盒 | 不附造专用指标 |

机械 Q2 标准答案为 `(2400+3400+3600)/(80+120+120)=29.375`。化工有独立能源第四要素。工厂B合成成本设置为A的两倍，仅用于方向/分母断言。所有数字与阈值均为独立合成，不是题包数字或行业基准。

## GLM-5.3 执行顺序与文件所有权

1. 先挑一个细分行业，研究真实流程、来源授权、成本政策、字段与证据门槛；填写 `research-ledger.md`。机械、汽配可共享离散策略，不能因名称相近跳过政策审查。
2. 复制参考包目录作为脚手架，只改包/企业配置/公开合成题，不复制 `backend`。读取 manifest、mapping、enterprise、facts、knowledge、template、evaluation 七类文件；固定上述接口后记录新增文件和实际开发用时。
3. 先加入独立手算 golden 和负例，再导入、勾稽、查询与季度分析；两会话使用相同产品/文档 ID回归隔离。
4. 接报告→结构化核查任务→人工确认→模拟送达闭环，检查 Word/PDF 每页与前端。模型不足、缺知识或缺数据应降级；真人归因0–5、可读性、版式仍由真人签署。
5. 公共接口不足时提交最小反例与向后兼容提议，由核心维护者修改 `industry.py` 和通用验收一次。行业研究者默认所有权为 `industry_packs/<新包>/`、独立 `tests/test_<新包>.py` 和本台账；不要改 API/outbox/worker 的隔离合同。

复现：在 `05_原型` 中运行 `PYTHONPATH=backend .venv/bin/python -m pytest -s tests/test_industry.py -q`。原题回归须先配置比赛数据与配套主数据/词典，按 `competition_configuration/scenarios.json` 执行；恢复发布原件不等于回归已在本机通过。`-s` 是本WSL当前 pytest 文件描述符捕获环境兼容选择。

## 最终数值合同补充

同一聚合拒绝混用 product_period、work_order、batch 粒度，防产品汇总与工单明细重叠累计。所有实际分析的完整环比/同比/预算基期先执行 `compare` 可比性合同；除明确 factory 比较外必须同厂，跨厂也不能豁免政策、单位或来源模式差异。

可选驱动定义为每个产出对象、工序、类型的一条完整归集事实。相同ID的完全相同导出幂等去重，冲突ID或不同ID重复同对象工序拒绝。驱动必须属于本期同企业/工厂/产品/版本/政策/粒度的完工对象；有未知对象、WIP或量纲冲突拒算，缺产出对象的驱动覆盖则专用指标与能力降级，不将部分机时除以全量产出。

机时按小时计，分钟/秒用已知时间比例精确换算；能耗按kWh计，Wh/MWh按SI比例换算；件不能冒充kg。单位能耗产出允许kg/吨的已知质量换算。转换后的真实分子、分母及驱动来源行写入指标，不把60分钟标为60小时或把MWh当kWh。公式版本 `normalized-cost-2-typed-drivers` 使旧计算缓存失效。

比赛主数据与词典是独立的企业配置，不是合成包知识或自动推断结果；即使本次获准公开，也保持原制药严格校验和内容哈希。缺少任一必要配置时不能伪造比赛原场景。既有变量名中的 `PRIVATE` 仅为兼容加载接口；未来真实企业配置的披露需要独立授权。旧删除清单保留为历史过程记录，恢复不得覆盖新源码、构建或整份运行状态；密钥、环境文件、数据库、待发队列与恢复备份不属于本次发布内容。
