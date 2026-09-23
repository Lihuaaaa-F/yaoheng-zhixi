# -*- coding: utf-8 -*-
"""AUD 独立数值复算：不调用 pharma 引擎，纯 csv+Decimal 从题包源字段推导标准答案，
再与 metrics.analyze/benchmark 输出对拍（误差≤1% 为赛题对标准确率口径）。
"""
import csv, io, sys
from decimal import Decimal as D
from pathlib import Path

BASE = Path(r'D:/yaoheng-audit-wt-1f78b2f/药衡智析_增量源码交接/public_source_candidate/00_赛题原始资料/'
            r'模拟数据_V1.1_净化解压/创灵境_考题模拟数据/01_成本明细数据')

def load(name):
    text = (BASE / name).read_text(encoding='utf-8-sig')
    return list(csv.DictReader(io.StringIO(text)))

cost26 = load('中药一厂_成本汇总_2026年1-6月.csv')
cost25 = load('中药一厂_成本汇总_2025年1-6月.csv')
plant2_26 = load('中药二厂_成本汇总_2026年1-6月.csv')
budget = load('中药一厂_预算数据_2026年.csv')

def row(rows, product, month):
    for r in rows:
        if r['产品名称'] == product and r['月份'] == month:
            return r
    return None

P = '银黄口服液'
cur, prev, yoy, p2, bud = (row(cost26, P, '2026-06'), row(cost26, P, '2026-05'),
                           row(cost25, P, '2025-06'), row(plant2_26, P, '2026-06'),
                           row(budget, P, '2026-06'))
uc = lambda r: D(r['单位成本(元/盒)'])
el = lambda r, k: D(r[k])
fields = {'material': '直接材料(元/盒)', 'labor': '直接人工(元/盒)', 'overhead': '制造费用(元/盒)'}

independent = {}
# 1) 环比（单位成本）
independent['unit_mom_rate'] = (uc(cur) - uc(prev)) / uc(prev) * 100
# 2) 同比（单位成本）
independent['unit_yoy_rate'] = (uc(cur) - uc(yoy)) / uc(yoy) * 100
# 3) 预算偏差（单位成本）
independent['unit_budget_rate'] = (uc(cur) - D(bud['预算单位成本(元/盒)'])) / D(bud['预算单位成本(元/盒)']) * 100
# 4) 要素贡献度（单位口径：要素单位成本变动 / 单位成本总变动）
du = uc(cur) - uc(prev)
for k, f in fields.items():
    independent[f'{k}_unit_contribution'] = (el(cur, f) - el(prev, f)) / du * 100
# 5) 对标差异（一厂−二厂，单位成本，以二厂为分母）
independent['benchmark_uc_left'] = uc(cur)
independent['benchmark_uc_right'] = uc(p2)
independent['benchmark_delta'] = uc(cur) - uc(p2)
independent['benchmark_rate'] = (uc(cur) - uc(p2)) / uc(p2) * 100
# 6) 不变量自检：单位成本=三要素和；总成本=产量×单位成本
independent['invariant_uc'] = uc(cur) == sum(el(cur, f) for f in fields.values())
independent['invariant_total'] = D(cur['总成本(元)']) == D(cur['产量(盒)']) * uc(cur)

print('=== 独立推导（银黄口服液 2026-06，一厂）===')
for k, v in independent.items():
    print(f'{k:28s} = {v}')

# ---- 引擎对拍 ----
sys.path.insert(0, r'D:/yaoheng-audit-wt-1f78b2f/药衡智析_增量源码交接/public_source_candidate/05_原型/backend')
import os
os.environ.setdefault('PHARMA_RUNTIME_DIR', r'D:/重庆市AI大赛/docs/audits/2026-09-23-1f78b2f/EVIDENCE/repro_runtime2')
from pharma.metrics import analyze, benchmark
snap = analyze('中药一厂', P, '2026-06', 'monthly', 'unit')
bench = benchmark(P, '2026-06', '中药一厂', '中药二厂')
engine = {
    'unit_mom_rate': D(snap['metrics']['mom']['value']),
    'unit_yoy_rate': D(snap['metrics']['yoy']['value']),
    'unit_budget_rate': D(snap['metrics']['budget']['value']),
    'benchmark_uc_left': D(bench['summary'][0]['left']),
    'benchmark_uc_right': D(bench['summary'][0]['right']),
    'benchmark_delta': D(bench['summary'][0]['delta']),
    'benchmark_rate': D(bench['summary'][0]['rate']),
}
for e in snap['elements']:
    engine[f"{e['key']}_unit_contribution"] = D(e['unit_contribution'])

print('\n=== 引擎输出与对拍（|差异| 应≈0；对标≤1% 为赛题口径）===')
all_ok = True
for k in independent:
    if not isinstance(independent[k], D):
        continue
    ev = engine.get(k)
    if ev is None:
        print(f'{k:28s} : 引擎无对应字段'); all_ok = False; continue
    diff = abs(ev - independent[k])
    ok = diff <= abs(independent[k]) * D('0.01') or diff < D('0.005')
    all_ok = all_ok and ok
    print(f'{k:28s} : 独立={independent[k]:>12.4f}  引擎={ev:>12.4f}  差={diff:.6f}  [{"OK" if ok else "FAIL"}]')
print('\n结论:', '全部对拍通过' if all_ok else '存在对拍失败项')
