# -*- coding: utf-8 -*-
"""成本预测波动区间覆盖率验证（2026-09-23 审计 AUD-T-09/FIX-8）。

对赛题原始数据（中药一厂 2026 年 1-6 月，3 产品）做滚动原点留出检验：
每个原点 t 用 values[:t] 训练（与 forecasting._holt 完全同口径），以该段的
样本内一步残差均方根 sigma 生成 ±1σ 区间，检验真实值 values[t] 是否落入。

输出 docs/validation/forecast_coverage_20260923.json。
诚实声明：题包每序列仅 6 个月，滚动原点只有 3 个/序列，全部检验点
3 产品 × 5 序列 × 3 原点 = 45 个——样本量不足以做统计显著性结论，
结果仅作为"实验性区间"的实测参考，不构成分布或覆盖概率承诺。
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
sys.path.insert(0, str(APP / 'backend'))

from pharma.forecasting import _holt, FORECAST_VERSION, MIN_POINTS  # noqa: E402

PKG = ROOT / '00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据/01_成本明细数据'
OUT = ROOT / 'docs/validation/forecast_coverage_20260923.json'

SERIES = [('unit_cost', '单位成本(元/盒)'), ('materials', '直接材料(元/盒)'),
          ('labor', '直接人工(元/盒)'), ('overhead', '制造费用(元/盒)'), ('total_cost', '总成本(元)')]


def main():
    rows = list(csv.DictReader((PKG / '中药一厂_成本汇总_2026年1-6月.csv').open(encoding='utf-8-sig')))
    products = sorted({r['产品名称'] for r in rows})
    checks = []
    for product in products:
        months = sorted({r['月份'] for r in rows if r['产品名称'] == product})
        by_month = {r['月份']: r for r in rows if r['产品名称'] == product}
        for key, column in SERIES:
            values = [float(by_month[m][column]) for m in months]
            for t in range(MIN_POINTS, len(values)):
                hist = values[:t]
                (point,), residuals, _init_k = _holt(hist, 1)
                sigma = math.sqrt(sum(r * r for r in residuals) / len(residuals)) if residuals else 0.0
                actual = values[t]
                covered = (point - sigma) <= actual <= (point + sigma)
                checks.append({
                    'product': product, 'series': key, 'origin_t': t, 'residuals_n': len(residuals),
                    'point': round(point, 4), 'sigma': round(sigma, 4),
                    'low': round(point - sigma, 4), 'high': round(point + sigma, 4),
                    'actual': actual, 'covered': covered,
                    'abs_err': round(abs(point - actual), 4),
                    'half_width': round(sigma, 4),
                })
    covered_n = sum(1 for c in checks if c['covered'])
    zero_width = [c for c in checks if c['half_width'] == 0]
    by_series = {}
    for key, _column in SERIES:
        group = [c for c in checks if c['series'] == key]
        by_series[key] = {'checks': len(group), 'covered': sum(1 for c in group if c['covered']),
                          'coverage_pct': round(100 * sum(1 for c in group if c['covered']) / max(len(group), 1), 1)}
    result = {
        'generated_at': '2026-09-23', 'forecast_version': FORECAST_VERSION,
        'method': '滚动原点：values[:t] 训练（含 OLS 初始化），±样本内一步残差RMS 区间，检验 values[t]',
        'data': '题包 中药一厂 2026-01..06 成本汇总（3产品×5序列×3原点）',
        'total_checks': len(checks), 'covered': covered_n,
        'coverage_pct': round(100 * covered_n / len(checks), 1),
        'zero_width_checks': len(zero_width),
        'zero_width_note': '残差极小的原点区间半宽为 0，覆盖率必然为 0——小样本下 ±1σ 区间的固有局限',
        'by_series': by_series,
        'detail': checks,
        'conclusion': '',
    }
    pct = result['coverage_pct']
    result['conclusion'] = (
        f'±1σ 实验性区间滚动留出覆盖率 {pct}%（{covered_n}/{len(checks)}，其中 {len(zero_width)} 个原点区间半宽为 0）。'
        f'样本仅 45 个检验点且每原点残差样本 1-2 个，不能推断总体覆盖率；'
        '该实测用于替代"完全未验证"状态，区间仍应标注实验性。若需趋近常用 68% 经验值，'
        '可将 RESIDUAL_SCALE 上调并重新跑本脚本复核（当前不建议在无更多数据时调参）。')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'detail'}, ensure_ascii=False, indent=1))
    print(f'WRITTEN {OUT}')


if __name__ == '__main__':
    main()
