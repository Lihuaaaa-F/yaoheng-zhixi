#!/usr/bin/env python3
"""Rebuild 06_评测/golden.json from the original CSVs with exact Fraction
arithmetic — an independent oracle, deliberately not importing pharma.metrics.

The original machine's golden.json was not packaged. This rebuild is a fresh
independent computation (csv + fractions.Fraction only); the standing test
compares production analyze() against it. Run from anywhere:
    python 90_工具/rebuild_independent_golden.py
"""
import csv
import json
import sys
from datetime import date
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path


def to_decimal(value):
    """Exact fraction -> high-precision decimal string for Decimal() consumers."""
    if value is None:
        return None
    with localcontext() as ctx:
        ctx.prec = 50
        return str(Decimal(value.numerator) / Decimal(value.denominator))

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / '01_数据/00_原始'


def read_costs():
    """factory/product/month -> dict of Fractions from the cost & budget CSVs."""
    rows = {}
    for path in sorted(ORIGINAL.rglob('*.csv')):
        if '成本汇总' not in path.name and '预算数据' not in path.name:
            continue
        budget = '预算数据' in path.name
        with path.open(encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                key = (row['工厂'], row['产品名称'], row['月份'])
                if budget:
                    rows.setdefault(key, {})['budget_unit_cost'] = Fraction(row['预算单位成本(元/盒)'])
                    rows.setdefault(key, {})['budget_total'] = Fraction(row['预算总成本(元)'])
                    rows[key]['budget_quantity'] = Fraction(row['预算产量(盒)'])
                else:
                    rows.setdefault(key, {}).update(
                        unit_cost=Fraction(row['单位成本(元/盒)']),
                        total_cost=Fraction(row['总成本(元)']),
                        quantity=Fraction(row['产量(盒)']))
    return rows


def months_of(month, quarterly):
    year, number = map(int, month.split('-'))
    if not quarterly:
        return [month]
    assert number % 3 == 0, 'quarter end month required'
    return [f'{year:04}-{m:02}' for m in range(number - 2, number + 1)]


def shift(month, amount):
    year, number = map(int, month.split('-'))
    total = year * 12 + (number - 1) + amount
    return f'{total // 12:04}-{total % 12 + 1:02}'


def aggregate(rows, factory, product, months, kind):
    """Weighted unit cost = Σ total / Σ quantity over the months (exact)."""
    field_total = 'total_cost' if kind == 'cost' else 'budget_total'
    field_quantity = 'quantity' if kind == 'cost' else 'budget_quantity'
    field_unit = 'unit_cost' if kind == 'cost' else 'budget_unit_cost'
    present = [rows[(factory, product, m)] for m in months if (factory, product, m) in rows]
    if len(present) != len(months) or any(field_total not in r for r in present):
        return None
    if len(months) == 1:
        return present[0][field_unit]
    total = sum(r[field_total] for r in present)
    quantity = sum(r[field_quantity] for r in present)
    if quantity == 0:
        return None
    return total / quantity


def rate(current, base):
    if current is None or base is None or base == 0:
        return None
    return (current - base) / base * 100


def main():
    rows = read_costs()
    scenarios = {
        'S1': ('中药一厂', '银黄口服液', '2026-05', False),
        'S3': ('中药一厂', '六味地黄胶囊', '2026-03', False),
        'Q2': ('中药一厂', '银黄口服液', '2026-06', True),
    }
    golden = {'_provenance': {
        'rebuilt_at': date.today().isoformat(),
        'method': 'csv + fractions.Fraction independent rebuild (90_工具/rebuild_independent_golden.py)；未导入pharma.metrics',
        'reason': '原机golden.json未随交接包送达；此文件为独立重算，非生产代码回抄',
        'note': 'mom=上一期(月度为上月/季度为上季度)；yoy=-12月；budget=同期预算加权单位成本；rate=(current-base)/base*100'}}
    for name, (factory, product, month, quarterly) in scenarios.items():
        months = months_of(month, quarterly)
        step = -3 if quarterly else -1
        current = aggregate(rows, factory, product, months, 'cost')
        mom = rate(current, aggregate(rows, factory, product, months_of(shift(month, step), quarterly), 'cost'))
        yoy = rate(current, aggregate(rows, factory, product, months_of(shift(month, -12), quarterly), 'cost'))
        budget = rate(current, aggregate(rows, factory, product, months, 'budget'))
        golden[name] = {'unit_cost': to_decimal(current), 'mom': to_decimal(mom), 'yoy': to_decimal(yoy), 'budget': to_decimal(budget)}
    out = ROOT / '06_评测/golden.json'
    out.write_text(json.dumps(golden, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(golden, ensure_ascii=False, indent=2))
    if any(v is None for name, values in golden.items() if not name.startswith('_') for v in values.values()):
        print('WARNING: 有None基期，请核对数据连续性', file=sys.stderr)


if __name__ == '__main__':
    main()
