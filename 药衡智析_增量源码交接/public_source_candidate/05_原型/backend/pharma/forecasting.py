"""成本趋势预测（赛题加分项）：基于历史月度序列的确定性时序外推。

设计原则：
- 只消费已固化的分析快照趋势数据（snapshot['trend']），不引入新依赖；
- 方法透明可审计：Holt 双参数指数平滑（固定 α/β），区间由样本内一步残差估计；
- 预测是趋势外推参考，不是预算或承诺，所有输出必须携带告示文案；
- 数值全部走 float 常规运算后按 4 位小数取整，保证同输入同输出（可测试）。
"""
import math

# 方法版本号：参数或口径变化时必须递增，调用方据此判断缓存/回执有效性。
FORECAST_VERSION = 'holt-alpha0.6-beta0.3-v1'
ALPHA, BETA = 0.6, 0.3          # 水平/斜率平滑系数：固定值，不拟合调参
Z_80 = 1.2815515655446004       # 正态分布 80% 区间分位数（双侧）
MIN_POINTS = 3                  # 少于 3 个有效月度点无法区分水平与斜率
MAX_HORIZON = 6                 # 外推步数上限，防止把短线趋势外推太远
CAVEAT = '预测基于历史成本趋势的统计外推，仅供管理参考，不构成预算承诺；实际成本受采购、工艺与产量影响。'


def _next_month(month, step=1):
    """'YYYY-MM' 字符串加 step 个月，处理跨年。"""
    year, mon = int(month[:4]), int(month[5:7])
    total = year * 12 + (mon - 1) + step
    return f'{total // 12:04d}-{total % 12 + 1:02d}'


def _holt(values, horizon):
    """Holt 线性指数平滑：返回 (预测列表, 样本内一步残差列表)。

    以首两个点初始化水平与斜率，随后逐步更新；残差只收集实际的一步预测
    误差（初始化点的恒零残差不计入，避免系统性低估区间宽度）。
    """
    level, slope = values[0], values[1] - values[0]
    residuals = []
    for actual in values[2:]:
        residuals.append(actual - (level + slope))
        prev_level = level
        level = ALPHA * actual + (1 - ALPHA) * (level + slope)
        slope = BETA * (level - prev_level) + (1 - BETA) * slope
    points, level_now = [], level
    for _ in range(horizon):
        level_now = level_now + slope  # 仅外推，不再吸收新观测
        points.append(level_now)
    return points, residuals


def forecast_series(series, horizon=3):
    """对 [(month, value|None), ...] 序列做外推预测。

    返回结构含状态、方法、逐月点预测与 80% 区间；数据不足时返回
    INSUFFICIENT_HISTORY 状态而非伪造结果。
    """
    if not isinstance(horizon, int) or isinstance(horizon, bool) or not 1 <= horizon <= MAX_HORIZON:
        raise ValueError('INVALID_FORECAST_HORIZON')
    points = [(m, v) for m, v in series if v is not None and isinstance(v, (int, float)) and math.isfinite(float(v))]
    if len(points) < MIN_POINTS:
        return {'status': 'INSUFFICIENT_HISTORY', 'reason': f'有效月度观测不足 {MIN_POINTS} 个，不输出预测',
                'forecast_version': FORECAST_VERSION, 'observations': len(points), 'points': []}
    months = [m for m, _ in points]
    if len(set(months)) != len(months):
        raise ValueError('DUPLICATE_FORECAST_MONTH')
    if any(later <= earlier for earlier, later in zip(months, months[1:])):
        raise ValueError('UNORDERED_FORECAST_MONTH')
    values = [float(v) for _, v in points]
    projections, residuals = _holt(values, horizon)
    # 小样本用总体标准差：单一残差时 σ=|r|，不为 0（3 点序列也应有非零区间）
    sigma = math.sqrt(sum(r * r for r in residuals) / len(residuals)) if residuals else 0.0
    rows = []
    for step, point in enumerate(projections, 1):
        low, high = point - Z_80 * sigma, point + Z_80 * sigma
        rows.append({'month': _next_month(months[-1], step), 'point': round(point, 4),
                     'low': round(low, 4), 'high': round(high, 4),
                     'negative_warning': point <= 0})
    return {'status': 'PASS', 'forecast_version': FORECAST_VERSION, 'method': 'Holt双参数指数平滑(α=0.6,β=0.3)',
            'observations': len(points), 'history_months': [months[0], months[-1]],
            'residual_std': round(sigma, 4), 'interval': '80%（样本内一步残差估计）',
            'points': rows, 'caveat': CAVEAT}


def _to_float(value):
    """趋势行中的数值是 Decimal 转字符串，解析失败按缺失处理。"""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def forecast_snapshot(snapshot, horizon=3):
    """对分析快照做总体与分要素单位成本/总成本预测。

    trend 行形如 {month, unit_cost, total_cost, quantity, <要素key>...}；
    要素 key 从 snapshot['elements'] 推导，避免硬编码三要素名称。
    """
    trend = snapshot.get('trend') or []
    if not trend:
        return {'status': 'INSUFFICIENT_HISTORY', 'reason': '快照无趋势数据', 'points': [],
                'forecast_version': FORECAST_VERSION, 'series': []}
    basis = snapshot.get('basis', 'unit')
    element_keys = [e['key'] for e in snapshot.get('elements') or [] if e.get('key')]
    targets = ['unit_cost' if basis == 'unit' else 'total_cost', *element_keys]
    labels = {'unit_cost': '单位成本', 'total_cost': '总成本'}
    unit = (snapshot.get('metrics', {}).get('unit_cost', {}) or {}).get('unit') if basis == 'unit' else \
        (snapshot.get('metrics', {}).get('total_cost', {}) or {}).get('unit')
    series_out = []
    for key in targets:
        rows = [(row.get('month'), _to_float(row.get(key))) for row in trend]
        # 分要素趋势行在 unit/total 口径下 key 相同，但缺数月必须容忍
        result = forecast_series(rows, horizon)
        entry = {'key': key, 'label': labels.get(key) or key, 'unit': unit, **result}
        series_out.append(entry)
    overall = next((s for s in series_out if s['key'] == ('unit_cost' if basis == 'unit' else 'total_cost')), series_out[0])
    return {'status': overall['status'], 'reason': overall.get('reason'),
            'forecast_version': FORECAST_VERSION, 'basis': basis,
            'product': snapshot.get('product'), 'factory': snapshot.get('factory'),
            'history_months': overall.get('history_months'), 'series': series_out,
            'points': overall.get('points', []), 'caveat': CAVEAT}
