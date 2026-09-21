# -*- coding: utf-8 -*-
"""生成中药二厂合成明细数据（2026-09-21 修复 #19，用户授权"构建标注合成明细"）。

背景：题包中中药二厂只有成本汇总、零明细，对标三步法第三步只能输出缺证清单。

方法（可复跑、可审计）：
1. 读取题包《中药一厂》原料/费用明细的结构比例（同名原料与费用类别的占比）；
2. 按《中药二厂成本汇总》的 直接材料/制造费用 单位成本逐产品逐月精确分解——
   Decimal 运算，末项吸收舍入残差，保证：
   Σ单位消耗 = 汇总直接材料(元/盒)、Σ总成本 = 直接材料×产量、占比合计=100%，
   全部满足 ingestion.audit 的精确校验（容差 1e-6 / 展示精度半点）；
3. 人工明细：直接人工总额 = 汇总直接人工(元/盒)×产量（精确）；工时按一厂
   同产品单位产量工时折算，人数/天数沿用一厂同产品值。

输出：competition_configuration/synthetic_detail_中药二厂/ 下三份 CSV，
文件名含"合成"字样；ingest 以覆盖目录并入（快照版本指纹随之变化）。
数据边界：合成演示数据，数值按题包汇总校准；用于补齐对标拆解的结构演示，
不作为真实二厂经营事实。
"""
import csv
import os
import sys
from collections import defaultdict
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '05_原型' / 'backend'))
os.environ.setdefault('PHARMA_RUNTIME_DIR', str(ROOT / '05_原型/.runtime'))

from pharma.config import ROOT as CFG_ROOT, PACKAGE  # noqa: E402

DATA_DIR = PACKAGE / '01_成本明细数据'
OUT_DIR = CFG_ROOT / 'competition_configuration/synthetic_detail_中药二厂'
STRUCTURE_MONTH = '2026-06'  # 结构比例取一厂该月（一厂明细文件仅2026年1-6月）
Q2 = D('0.01')


def q2(value):
    return value.quantize(Q2, rounding=ROUND_HALF_UP)


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    plant2_cost = [r for r in read_csv(DATA_DIR / '中药二厂_成本汇总_2026年1-6月.csv')] + \
                  [r for r in read_csv(DATA_DIR / '中药二厂_成本汇总_2025年1-6月.csv')]
    m1 = [r for r in read_csv(DATA_DIR / '中药一厂_原材料消耗明细_2026年1-6月.csv') if r['月份'] == STRUCTURE_MONTH]
    e1 = [r for r in read_csv(DATA_DIR / '中药一厂_制造费用明细_2026年1-6月.csv') if r['月份'] == STRUCTURE_MONTH]
    l1 = [r for r in read_csv(DATA_DIR / '中药一厂_人工工时明细_2026年1-6月.csv') if r['月份'] == STRUCTURE_MONTH]
    material_template = defaultdict(list)   # product -> [(name, unit)]
    expense_template = defaultdict(list)
    labor_template = {}
    for r in m1:
        material_template[r['产品名称']].append((r['原材料名称'], D(r['单位消耗成本(元/盒)'])))
    for r in e1:
        expense_template[r['产品名称']].append((r['费用类别'], D(r['单位费用(元/盒)'])))
    for r in l1:
        labor_template[r['产品名称']] = (D(r['总工时(小时)']), D(r['产量(盒)']), r['生产人数(人)'], r['工作天数(天)'])

    materials_rows, expenses_rows, labor_rows = [], [], []
    for summary in plant2_cost:
        product = summary['产品名称']
        spec = summary['产品规格']
        month = summary['月份']
        qty = D(summary['产量(盒)'])
        if product not in material_template:
            raise SystemExit(f'一厂结构模板缺少产品: {product}')
        # 原料明细：按一厂结构比例分解二厂直接材料单位成本，末项吸收残差
        target_material = D(summary['直接材料(元/盒)'])
        template = material_template[product]
        total_weight = sum(w for _, w in template)
        units, acc = [], D('0')
        for i, (name, weight) in enumerate(template):
            if i == len(template) - 1:
                unit = target_material - acc
            else:
                unit = q2(target_material * weight / total_weight)
                acc += unit
            units.append((name, unit))
        # 份额从取整后的单位计算（与 audit 的 materials_share 同口径）：
        # Σ单位=目标(精确)，故 unit/Σunit×100 即 audit 的 actual 值；
        # 每项取整偏差 ≤ 半步（0.005）落在单项容差内；合计偏差 ≤ N×半步，
        # 也落在 share_rollup 的累计容差（Σ半步）内，无需末项强补 100%。
        unit_sum = sum(u for _, u in units)
        assert unit_sum == target_material
        shares = [q2(u / unit_sum * 100) for _, u in units]
        for (name, unit), share in zip(units, shares):
            cost = q2(unit * qty)
            materials_rows.append({'工厂': '中药二厂', '产品名称': product, '产品规格': spec, '月份': month,
                                   '产量(盒)': summary['产量(盒)'], '原材料名称': name,
                                   '单位消耗成本(元/盒)': f'{unit:.2f}', '原材料总成本(元)': f'{cost:.2f}',
                                   '占总材料成本比例': f'{share:.2f}%'})
        # 费用明细：同一厂费用类别结构
        target_expense = D(summary['制造费用(元/盒)'])
        etemplate = expense_template[product]
        etotal = sum(w for _, w in etemplate)
        eunits, eacc = [], D('0')
        for i, (name, weight) in enumerate(etemplate):
            if i == len(etemplate) - 1:
                unit = target_expense - eacc
            else:
                unit = q2(target_expense * weight / etotal)
                eacc += unit
            eunits.append((name, unit))
        for name, unit in eunits:
            cost = q2(unit * qty)
            expenses_rows.append({'工厂': '中药二厂', '产品名称': product, '产品规格': spec, '月份': month,
                                  '产量(盒)': summary['产量(盒)'], '费用类别': name,
                                  '单位费用(元/盒)': f'{unit:.2f}', '费用总额(元)': f'{cost:.2f}'})
        # 人工明细：总额精确等于汇总；工时按一厂单位产量工时折算
        total_labor = q2(D(summary['直接人工(元/盒)']) * qty)
        hours1, qty1, workers, days = labor_template[product]
        hours = int((hours1 / qty1 * qty).quantize(D('1'), rounding=ROUND_HALF_UP))
        labor_rows.append({'工厂': '中药二厂', '产品名称': product, '产品规格': spec, '月份': month,
                           '产量(盒)': summary['产量(盒)'], '直接人工总额(元)': f'{total_labor:.2f}',
                           '总工时(小时)': str(hours), '生产人数(人)': workers, '工作天数(天)': days})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = [
        ('中药二厂_原材料消耗明细_合成_2025-2026.csv',
         ['工厂', '产品名称', '产品规格', '月份', '产量(盒)', '原材料名称', '单位消耗成本(元/盒)', '原材料总成本(元)', '占总材料成本比例'],
         materials_rows),
        ('中药二厂_制造费用明细_合成_2025-2026.csv',
         ['工厂', '产品名称', '产品规格', '月份', '产量(盒)', '费用类别', '单位费用(元/盒)', '费用总额(元)'],
         expenses_rows),
        ('中药二厂_人工工时明细_合成_2025-2026.csv',
         ['工厂', '产品名称', '产品规格', '月份', '产量(盒)', '直接人工总额(元)', '总工时(小时)', '生产人数(人)', '工作天数(天)'],
         labor_rows),
    ]
    for name, fields, rows in outputs:
        with (OUT_DIR / name).open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f'written {name}: {len(rows)} rows')
    # 自校验：复算 rollup 与汇总精确一致
    for summary in plant2_cost:
        key = (summary['产品名称'], summary['月份'])
        msum = sum(D(r['单位消耗成本(元/盒)']) for r in materials_rows if (r['产品名称'], r['月份']) == key)
        esum = sum(D(r['单位费用(元/盒)']) for r in expenses_rows if (r['产品名称'], r['月份']) == key)
        lsum = next(D(r['直接人工总额(元)']) for r in labor_rows if (r['产品名称'], r['月份']) == key)
        assert msum == D(summary['直接材料(元/盒)']), (key, msum)
        assert esum == D(summary['制造费用(元/盒)']), (key, esum)
        assert lsum == q2(D(summary['直接人工(元/盒)']) * D(summary['产量(盒)'])), (key, lsum)
    print(f'self-check OK: {len(plant2_cost)} product-months calibrated exactly to plant-2 summaries')


if __name__ == '__main__':
    main()
