# 本轮数据增量合同与验证

原始 CSV、历史评测和原计算保持原样。本次源码仅修改 `05_原型/backend/pharma/metrics.py`、`05_原型/tests/test_metrics.py`。数据读取继续严格 UTF-8，不做批量转码或丢字。公式版本增为 `cost-formulas-1.1`，用于区分新增绑定合同的快照。

## 新增字段

- `elements[].comparisons.{mom,yoy,budget}.{unit,total}`：各自包含 current、base、delta、rate、contribution、numerator、denominator、comparison_period、comparison_object、basis、unit、reason、contribution_reason。贡献率分母必须是同一比较对象、同一单位/总额口径的整体差额。旧的 contribution、unit_contribution、total_contribution 仍仅表示环比，供旧调用兼容。
- `metrics.{element}_{comparison}_{basis}_{delta|rate|contribution}`：注册上述指标，含公式、源行、分子分母和比较期。`elements[].yoy_unit/yoy_rate` 提供同比展示捷径；原 `period_values.yoy.elements_unit` 本来已有有效源数据。
- `materials_summary`：本期各原料按单位消耗成本差额绝对值排序。含 name、current、previous、delta、rate、contribution、numerator、denominator、comparison_period、source_labels、metric_refs。贡献分母为材料单位成本总变动；当前/基期值以完整期间原料总成本除以产量，保持季度加权。无明细返回空列表，缺完整基期返回带原因的空值，不推算二厂原料。
- `materials_summary[].metric_refs` 与 `budget_bridge.metric_refs` 是 `snapshot.metrics` 的字典键；对应指标对象的 `metric_id` 才是模型引用 ID。
- `budget_bridge` 原计算不改；新增注册的 `budget_quantity_effect`、`budget_unit_cost_effect`、`budget_total_delta` 供正文引用。
- `benchmark.elements[]` 新增 contribution、numerator、denominator、comparison_period、comparison_object；`benchmark_analysis` 进一步附 metric_refs 并注册指标，保留左右厂方向和对标分母。
- 折算平均小时工资定义明确写为题包折算口径，不等同基础薪率。

## 实际运行结果

四轮红→绿证据保存在本目录：比较绑定、跨厂结构、原料驱动、原料指标分子分母。首轮 pytest 的临时文件捕获失败原样保留在 `comparisons_red.txt`；随后使用 `TMPDIR=/tmp` 和 `--capture=sys` 取得实际业务断言失败记录，未将环境失败冒充业务红灯。

最终 `data_regression_final.txt`：18 项通过，包括原有季度加权、总额与单位告警、阈值边界、源数据保护和无效快照隔离。

`check_independent_golden.py` 直接读原 CSV，以 Fraction 独立复算，通过公开 analyze/benchmark 接口验证。`independent_golden_result.json`：72 个月度和 24 个完整季度快照、18 组跨厂比较，共 5,574 个观测，0 失败。覆盖三产品、两工厂、三比较、单位与总额。CSV 编码和哈希检查在同一记录中；未改写原件。

板蓝根一厂 2026-05 独立实例：材料环比/同比/预算贡献率分别 78.26%/89.19%/78.72%；去年同期三要素 4.42/1.04/1.64 元/盒；板蓝根原料 2.90→3.05 元/盒，占材料增量 83.33%；预算总额差 131,940 元分为产量影响 84,000 元及单位成本影响 47,940 元。跨厂二厂减一厂差 0.50 元/盒，三要素 0.20/0.13/0.17，贡献 40%/26%/34%。趋势仅至 5 月，2 月 7.25 元/盒保留。

## 限制与后续验收

以上仅证明数据计算与新增引用合同，不证明报告章节、模型解释、证据适用性、人工可读性或逐页视觉合格。Word/PDF 须由集成流程另行导出和逐页检查。人工归因评分仍由人完成。

## 重跑

```bash
TMPDIR=/tmp PYTHONPATH=05_原型/backend 05_原型/.venv/bin/python -m pytest 05_原型/tests/test_metrics.py 05_原型/tests/test_ingestion.py -q --capture=sys
TMPDIR=/tmp 05_原型/.venv/bin/python 06_评测/incremental_20260916/data/check_independent_golden.py
```
