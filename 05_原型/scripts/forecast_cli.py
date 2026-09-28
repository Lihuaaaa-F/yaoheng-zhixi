"""成本预测拟合、状态导出、推理及时间顺序留出评测（不调用大模型）。"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from pharma.forecasting import (ALPHA, BETA, FORECAST_VERSION, MIN_POINTS,
                                RESIDUAL_SCALE, _holt, forecast_series)

TARGETS = [('unit_cost', '单位成本(元/盒)', '元/盒'),
           ('materials', '直接材料(元/盒)', '元/盒'),
           ('labor', '直接人工(元/盒)', '元/盒'),
           ('overhead', '制造费用(元/盒)', '元/盒'),
           ('total_cost', '总成本(元)', '元')]
CONFIG = {'alpha': ALPHA, 'beta': BETA, 'residual_scale': RESIDUAL_SCALE}


def load_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'产品名称', '工厂', '月份', *(column for _, column, _ in TARGETS)}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError('缺少列：' + '、'.join(sorted(missing)))
        rows = list(reader)
    if not rows:
        raise ValueError('输入没有数据')
    result = []
    for factory, product in sorted({(r['工厂'], r['产品名称']) for r in rows}):
        group = sorted((r for r in rows if (r['工厂'], r['产品名称']) == (factory, product)),
                       key=lambda r: r['月份'])
        for target, column, unit in TARGETS:
            history = [[r['月份'], float(r[column]) if r[column].strip() else None] for r in group]
            result.append({'factory': factory, 'product': product, 'target': target,
                           'unit': unit, 'history': history})
    return {'schema_version': 1, 'model_version': FORECAST_VERSION, 'config': CONFIG,
            'source': {'name': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()},
            'series': result}


def metric(errors):
    if not errors:
        return None
    return {'MAE': sum(map(abs, errors)) / len(errors),
            'RMSE': math.sqrt(sum(e * e for e in errors) / len(errors))}


def evaluate(history):
    checks = []
    for t in range(MIN_POINTS, len(history)):
        values = [v for _, v in history[:t]]
        (point,), residuals, _ = _holt(values, 1)
        sigma = math.sqrt(sum(r * r for r in residuals) / len(residuals)) if residuals else 0.0
        actual, naive = history[t][1], values[-1]
        tolerance = 1e-12 * max(1.0, abs(actual), abs(point))
        checks.append({'train_start': history[0][0], 'train_end': history[t - 1][0],
                       'test_month': history[t][0], 'actual': actual, 'prediction': point,
                       'naive_last_value': naive, 'error': point - actual,
                       'baseline_error': naive - actual, 'range_half_width': RESIDUAL_SCALE * sigma,
                       'covered': abs(point - actual) <= RESIDUAL_SCALE * sigma + tolerance})
    return {'origins': len(checks), 'horizon': 1,
            'holt': metric([x['error'] for x in checks]),
            'naive_last_value': metric([x['baseline_error'] for x in checks]),
            'experimental_range': {'covered': sum(x['covered'] for x in checks), 'tested': len(checks)},
            'checks': checks}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input', type=Path, help='原题格式成本汇总CSV')
    source.add_argument('--state-in', type=Path, help='读取已导出的模型状态')
    parser.add_argument('--state-out', type=Path, help='导出可复现状态：配置和训练历史')
    parser.add_argument('--horizon', type=int, default=3, help='外推月数，1–6')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        state = load_csv(args.input) if args.input else json.loads(args.state_in.read_text(encoding='utf-8'))
        if (state.get('schema_version') != 1 or state.get('model_version') != FORECAST_VERSION
                or state.get('config') != CONFIG or not state.get('series')):
            raise ValueError('模型状态版本或参数不兼容，请用相应版本重建状态')
        results = []
        for series in state['series']:
            prediction = forecast_series(series['history'], args.horizon)
            evaluation = evaluate(series['history']) if prediction['status'] == 'PASS' else None
            results.append({**series, 'forecast': prediction, 'rolling_evaluation': evaluation})
        output = {'model_version': FORECAST_VERSION, 'config': {**CONFIG, 'horizon': args.horizon},
                  'source': state['source'], 'results': results,
                  'limits': '固定参数、不随机划分；每个原点仅使用过去数据。范围为残差RMS实验性波动范围，不是已验证置信区间；一步评测不能代表多步性能。'}
        write_json(args.output, output)
        if args.state_out:
            write_json(args.state_out, state)
        print(json.dumps({'series': len(results), 'forecastable': sum(x['forecast']['status'] == 'PASS' for x in results),
                          'holdout_points': sum((x['rolling_evaluation'] or {}).get('origins', 0) for x in results)}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f'预测输入错误：{exc}\n')


if __name__ == '__main__':
    main()
