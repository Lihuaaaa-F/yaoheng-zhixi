# 数据与指标契约

## 领域与公开接口

词汇沿用 CONTEXT.md。「要素单位环比」是同产品相邻显式月份每盒要素成本变动率；「要素总额环比」先把单位要素乘该月产量再比较，两种告警不可互换。「贡献率」以同口径总变动额作分母，可负或超过100%；分母0显示N/A。

TDD已授权公开接口：`ingest(source=None,destination=None)`、`load_rows(destination=None)`、`catalog()`、`analyze(factory,product,month,analysis_type='monthly',basis='unit')`、`benchmark(product,month,left='中药二厂',right='中药一厂')`、`change(current,base)`、`threshold_alert(rate)`、`contribution(delta,total_delta)`。输入路径仅本地导入工具调用，Web不直接接受任意服务器路径。

## 原始、派生与版本

唯一原始CSV在 `01_数据/00_原始`；旧清洗副本不是生产数据源。CSV按UTF-8 BOM读取，不因ZIP文件名显示乱码改写内容。`ingestion.FIELDS`逐类列出完整字段白名单；未知或缺字段、非法数值、重复主键、断月、关联缺失和勾稽失败拒绝发布，失败清单保存在 `.runtime/data/rejected-{hash}.json`。成功快照先写临时Parquet再原子替换`current.json`；旧快照保留，worker单进程，DuckDB每次只读独立内存连接。缓存复用检查CSV哈希、契约版本及Parquet哈希。

- 成本/预算：主键 工厂、产品、月份；产品规格必须明确一致。
- 原料/费用：再加原材料名称/费用类别；必须关联唯一成本汇总。
- 人工：工厂、产品、月份，工时仅作效率描述；8小时关系不作强制通过条件。
- 行业：产品类别、指标；市场：药材名称。行业数据是静态模拟，市场价不是采购价。
- 每行保留CSV文件名、1起始物理行号（表头第1行）、源文件SHA256。
- ZIP仅核验既有安全解压材料：检查路径穿越、绝对路径、Windows盘符、符号链接、重名、单文件100MB/总500MB/压缩比1000上限；映射CP437显示到UTF-8原名，排除Mac资源文件。

## 独立审计

当前原件实际10 CSV/334行，16组810算术观测及51组月份连续检查。16组明细在`06_评测/数据治理审计.json`：汇总/预算构成与乘法、原料/费用/人工产量关联、原料乘法与比例、费用乘法、人工总额、原料/费用单位与总额汇总、原料比例汇总。比例每行允许其最后一位显示精度的一半百分点，比例求和容差累加；金额绝对容差0.000001元（未发现失败）。原始字节不修改。

## 指标契约

所有业务数字为Decimal运算后JSON字符串；缺失值null，`display=N/A`及`reason`。每个Metric带`metric_id,value,display,unit,formula,formula_version,numerator,denominator,comparison_period,row_keys,source_hash`。快照ID包含数据版本、公式和筛选条件；知识/模型/模板版本由报告任务合并固定。报告与看板共享这份结果。

- 单位成本=Σ总成本/Σ产量，季度按同产品盒数加权。季度输入月份必须为03/06/09/12期末，比较要求完整对应三月；Q1无2025Q4，2026-01无2025-12，均N/A。
- `basis=unit|total`决定主要环比和瀑布。elements始终同时返回单位和总额告警，严格绝对值>10%；±10%不触发。
- `period_values`提供current/mom/yoy/budget的数量、单位、总额、要素单位与总额；`period_changes`提供三个口径全部比较。跨规格产品不混算每盒效率。
- 预算桥接=(实际量−预算量)×预算单位成本＋实际量×(实际单位成本−预算单位成本)，仅完整已有预算；二厂N/A。
- 对标默认二厂−一厂，以一厂为分母；交换后分母随right变化。三步为总览→要素/可用明细→原因假设/缺证项，文档依据由检索层补充，不能仅凭数值证明原因。
- 行业换算验证完整产品规格后每盒÷10支、÷20袋、÷60粒，保留行业单位；收入缺失不能计算毛利率。
- `labor_metrics`工时/万盒=Σ工时/Σ量×10000，时薪=Σ人工总额/Σ工时，效率=Σ产量/Σ(生产人数×工作天数)，盒/人·日；费用汇总按产量加权。

## 独立golden与验证证据

`06_评测/recompute_golden.py`只读原始CSV，用标准库Fraction重算固定S1/S2/S3/Q2，不导入生产公式；`golden.json`含源哈希。真实red/green日志单独记录，依赖缺失日志不算行为失败。所有变异fixture位于pytest临时目录，不写比赛原件。

## 本轮两路自审

A 规范：公式集中在metrics，API/报告不应另算；外部数据读写集中在ingestion，DuckDB全部参数化。未引入第二种数据框架或新解释器。按固定哈希基线判断本轮文件，未提交用户旧修改。

B 规格：已修正审查发现的季度非期末隐式包含未来月份（现在拒绝非期末），过滤月度市场未来价格字段；报告效率改为盒/人·日，避免套8小时假设；elements显式区分unit/total的delta与contribution，报告固定单位表不得误用总額字段。对标原因的文档证据由API检索补充，metrics层只返回数值事实及待核查假设，不伪称带引用即证实因果。

实际行为通过状态以测试日志为准；编译/独立算术审计均不替代生产Parquet→analyze链路执行。

## 本轮实际执行结果

`TMPDIR=/tmp PYTHONPATH=05_原型/backend 05_原型/.venv/bin/python -m pytest 05_原型/tests/test_metrics.py 05_原型/tests/test_ingestion.py -q`：12 passed，真实Parquet发布、DuckDB读取、四场景指标、缺基期、阈值、负贡献、原件审计、坏导入保留旧快照及ZIP安全。默认TMPDIR指向跨系统位置曾导致pytest捕获临时文件失败，改本项目命令TMPDIR=/tmp后正常，未动全局环境。

四份实际指标快照在`06_评测/snapshots/{S1,S2,S3,Q2}.json`，对标快照`S2_benchmark.json`。性能记录`metrics_performance.json`为6次本机调用（1首次测量+5热请求）小样本，非生产P95保证。季度及对标先前red日志与该合并green日志共同构成证据；安装未完成的pytest缺模块日志不算行为red。

最终按新增公开接口并发回归与独立golden全场景比较需要，合并运行`test_metrics.py test_ingestion.py test_concurrency.py`：**16 passed in 0.97s**，覆盖真实一厂45个要素环比中单位0条/总额31条告警。见覆盖更新后的`data_metrics_tests.log`。前述12通过是先前阶段结果，不单独宣称全功能验收。
