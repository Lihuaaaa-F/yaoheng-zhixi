"""Deterministic dashboard views. No model calls or mutable dataset writes."""
import threading
from decimal import Decimal, InvalidOperation

FOCUS_VERSION = 'element-mom-focus-v1'

# 产品×月份热力图缓存（2026-09-21 修复 #6：原实现每次请求对 3 产品×6 月
# 做全量分析约 14 秒，且二次请求不命中）。以目录 snapshot_id（数据版本指纹）
# 为失效依据：数据导入/重发布后指纹变化，缓存自动失效。仅缓存默认分析器
# 路径；测试注入的自定义 analyze 不经过缓存。进程内、有界、线程安全。
_GRID_CACHE = {}
_GRID_CACHE_LOCK = threading.Lock()
_GRID_CACHE_MAX = 128


def _grid_cache_get(key):
    with _GRID_CACHE_LOCK:
        return _GRID_CACHE.get(key)


def _grid_cache_put(key, value):
    with _GRID_CACHE_LOCK:
        if len(_GRID_CACHE) >= _GRID_CACHE_MAX:
            _GRID_CACHE.clear()
        _GRID_CACHE[key] = value


def _number(value):
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def focus_analysis(snapshot, *, enqueue=None, enabled=False, model_available=False, latest_job=None):
    """Display exact changes immediately; optionally use the existing report queue.

    Failed automatic attempts remain visible until an explicit manual retry. A
    refreshed page never silently starts another paid attempt for that snapshot.
    """
    items, missing = [], []
    for element in snapshot.get('elements', []):
        for basis, label in (('unit', '单位成本'), ('total', '总成本')):
            comparison = element.get('comparisons', {}).get('mom', {}).get(basis, {})
            current, base = _number(comparison.get('current')), _number(comparison.get('base'))
            unit = snapshot.get('metrics', {}).get('unit_cost' if basis == 'unit' else 'total_cost', {}).get('unit', '')
            identity = {'element_key': element['key'], 'element': element['name'], 'basis': basis,
                        'unit': unit, 'period': snapshot.get('period'),
                        'comparison_period': comparison.get('comparison_period')}
            if current is None or base is None or base == 0:
                missing.append({**identity, 'reason': comparison.get('reason') or
                                ('基期为零，环比无定义' if base == 0 else '缺少完整可比基期或本期')})
                continue
            rate = (current - base) / base * 100
            # 2026-09-24 修复（审计 AUD-NAR-08）：与 metrics.threshold_alert 单点
            # 同源（严格>10），不再双份维护同一阈值常量。
            from .metrics import threshold_alert
            if not threshold_alert(rate):
                continue
            causal_limit = '缺少经核实的业务原因与对应原始记录；成本变化仅支持待核查假设，不能认定因果。'
            if basis == 'total':
                causal_limit += '总成本同时受单位成本与产量影响，需分别核查。'
            items.append({**identity, 'current': str(current), 'base': str(base),
                          'delta': str(current - base), 'rate': str(rate),
                          'text': f'{element["name"]}{label}由 {base} {unit}变为 {current} {unit}，'
                                  f'环比{"上升" if rate > 0 else "下降"} {abs(rate)}%，严格超过 ±10%，列为重点分析。',
                          'missing_evidence': [causal_limit]})
    result = {'version': FOCUS_VERSION, 'snapshot_id': snapshot.get('snapshot_id'), 'items': items,
              'missing': missing, 'model_status': 'NOT_NEEDED', 'job_id': None}
    if not items:
        return result
    if not enabled:
        return {**result, 'model_status': 'DISABLED'}
    if not model_available:
        return {**result, 'model_status': 'NO_MODEL'}
    if latest_job and latest_job['status'] not in ('SUCCEEDED', 'DEGRADED'):
        job = latest_job
    elif enqueue is not None:
        # Completed jobs pass through the queue's artifact integrity check.
        job = enqueue()
    else:
        return {**result, 'model_status': 'UNAVAILABLE'}
    return {**result, 'job_id': job['id'],
            'model_status': 'FAILED' if job['status'] == 'FAILED' else job['status']}


def product_month_grid(context_id, factory, month, basis, *, options=None, analyze=None):
    """Six calendar months, all catalog products, preserving nulls and exact strings."""
    from .industry import catalog, analyze_reference
    from .metrics import _shift
    options = options if options is not None else catalog(context_id)
    default_analyzer = analyze is None
    analyze = analyze or analyze_reference
    if basis not in ('unit', 'total'):
        raise ValueError('INVALID_BASIS')
    if factory not in options['factories']:
        raise ValueError('UNKNOWN_FACTORY')
    version = str(options.get('snapshot_id', options.get('data_version', '')))
    cache_key = (context_id, factory, basis, month, version) if default_analyzer else None
    if cache_key is not None:
        cached = _grid_cache_get(cache_key)
        if cached is not None:
            return cached
    months = [_shift(month, offset) for offset in range(-5, 1)]
    elements = {'all': '全部成本'}
    cells = []
    for product in options['products']:
        for period in months:
            cell = {'product': product, 'month': period, 'values': {}, 'status': 'MISSING'}
            try:
                snapshot = analyze(context_id, factory=factory, product=product, month=period,
                                   analysis_type='monthly', basis=basis)
            except ValueError as exc:
                if str(exc) not in ('INCOMPLETE_PERIOD', 'NO_COMPLETE_PERIOD_DATA'):
                    raise
                cell['reason'] = '该产品在当前工厂缺少完整月份数据'
            else:
                metric = snapshot['metrics']['unit_cost' if basis == 'unit' else 'total_cost']
                unit = metric['unit']
                cell.update(status='AVAILABLE', snapshot_id=snapshot.get('snapshot_id'))
                cell['values']['all'] = {'value': metric.get('value'), 'unit': unit,
                                         'reason': metric.get('reason')}
                for element in snapshot.get('elements', []):
                    elements[element['key']] = element['name']
                    value = element.get(basis)
                    cell['values'][element['key']] = {'value': value, 'unit': unit,
                        'reason': '要素成本或可比产量缺失' if value is None else None}
            cells.append(cell)
    result = {'context_id': context_id, 'factory': factory, 'basis': basis,
            'months': months, 'products': options['products'],
            'elements': [{'key': key, 'name': name} for key, name in elements.items()], 'cells': cells}
    if cache_key is not None:
        _grid_cache_put(cache_key, result)
    return result
