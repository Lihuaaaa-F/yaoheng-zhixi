"""从已选分析快照定位成本变动，不把相关信号表述为已证实的原因。

快照归因复用同一企业、期间、比较对象与口径的 Decimal 结果；总额两因子
为单位成本×产量的算术分配，不是采购价格×实物耗量分解。行情和跨厂前后
差异在原快照构建时固化，仅供核查参考。经验权重是核查优先级，不是概率。
缺明细、对照、基期或勾稽失败时明确 UNAVAILABLE，不回读其他上下文补数。
"""
from __future__ import annotations

import math
from decimal import Decimal as D

from .ingestion import load_rows

ATTRIBUTION_VERSION = 'attribution-v2-bound-snapshot'

_ELEM_COLS = (('材料', '直接材料(元/盒)'), ('人工', '直接人工(元/盒)'), ('制造费用', '制造费用(元/盒)'))
_EP_SELECT_THRESHOLD = D('0.95')   # 同向属性累计解释力达到 95% 即止
_EP_MIN_ATTRIBUTE = D('0.03')      # 单属性 |EP| ≥3% 才入选
_PLACEBO_RATIO = D('0.3')          # 安慰剂 |τ0| > max(0.05, 0.3|τ|) 视为平行趋势存疑


def _d(value) -> D | None:
    try:
        number = D(str(value).replace(',', ''))
        return number if number.is_finite() else None
    except Exception:
        return None


def _shift(month: str, step: int) -> str:
    year, mon = int(month[:4]), int(month[5:7])
    total = year * 12 + (mon - 1) + step
    return f'{total // 12:04d}-{total % 12 + 1:02d}'


def _direction(delta: D) -> str:
    return '上升' if delta > 0 else ('下降' if delta < 0 else '持平')


def _jsd(p: list[float], q: list[float]) -> float:
    """Jensen-Shannon 散度（自然对数，对称有界 [0, ln2]）。"""
    total_p, total_q = sum(p), sum(q)
    if total_p <= 0 or total_q <= 0:
        return 0.0
    pn = [x / total_p for x in p]
    qn = [x / total_q for x in q]
    jsd = 0.0
    for pi, qi in zip(pn, qn):
        mi = 0.5 * (pi + qi)
        if pi > 0:
            jsd += 0.5 * pi * math.log(pi / mi)
        if qi > 0:
            jsd += 0.5 * qi * math.log(qi / mi)
    return jsd


def _shapley_two_factor(a0: D, a1: D, b0: D, b1: D) -> tuple[D, D]:
    """乘积 T=a×b 的两因子 Shapley 分配：交互项对半分，精确可加。"""
    c_a = ((b0 + b1) / 2) * (a1 - a0)
    c_b = ((a0 + a1) / 2) * (b1 - b0)
    return c_a, c_b


def _cost_data(rows, factory, product, month) -> dict | None:
    for r in rows:
        if r['kind'] == 'cost' and r['factory'] == factory and r['product'] == product and r['month'] == month:
            return r['data']
    return None


def _material_units(rows, factory, product, month) -> dict[str, D]:
    out: dict[str, D] = {}
    for r in rows:
        if r['kind'] == 'materials' and r['factory'] == factory and r['product'] == product and r['month'] == month:
            value = _d(r['data'].get('单位消耗成本(元/盒)'))
            if value is not None:
                out[r['data'].get('原材料名称', '')] = value
    return out


def _market_change(rows, herb: str, month: str, base_month: str):
    """行情行按 月价格 列取名；跨年或列缺失返回 None。"""
    if month[:4] != base_month[:4]:
        return None
    col_cur, col_base = f'{int(month[5:7])}月价格', f'{int(base_month[5:7])}月价格'
    for r in rows:
        if r['kind'] == 'market' and r['data'].get('药材名称') == herb:
            cur, base = _d(r['data'].get(col_cur)), _d(r['data'].get(col_base))
            if cur is None or base is None or base == 0:
                return None
            return (cur - base) / base * 100
    return None


def _select_attrs(cur: dict[str, D], base: dict[str, D], delta_total: D):
    """同向属性贪心选择：返回 [(name, delta, ep)] 与维度惊奇度。"""
    names = sorted(set(cur) | set(base))
    deltas = {n: cur.get(n, D(0)) - base.get(n, D(0)) for n in names}
    same_sign = [n for n in names if delta_total != 0 and deltas[n] != 0
                 and (deltas[n] > 0) == (delta_total > 0) and abs(deltas[n]) >= abs(delta_total) * _EP_MIN_ATTRIBUTE]
    same_sign.sort(key=lambda n: -abs(deltas[n]))
    picked, cumulative = [], D(0)
    for n in same_sign:
        ep = deltas[n] / delta_total if delta_total != 0 else D(0)
        picked.append((n, deltas[n], ep))
        cumulative += abs(ep)
        if cumulative >= _EP_SELECT_THRESHOLD or len(picked) >= 3:
            break
    surprise = _jsd([abs(float(cur.get(n, D(0)))) for n in names],
                    [abs(float(base.get(n, D(0)))) for n in names]) if names else 0.0
    return picked, surprise


def localize(rows, factory, product, month, base_month, basis='unit') -> dict:
    cur_row, base_row = _cost_data(rows, factory, product, month), _cost_data(rows, factory, product, base_month)
    if not cur_row or not base_row:
        raise ValueError('BASE_PERIOD_DATA_MISSING')
    dims, causes = [], []
    if basis == 'unit':
        cur = {label: _d(cur_row.get(col)) for label, col in _ELEM_COLS}
        base = {label: _d(base_row.get(col)) for label, col in _ELEM_COLS}
        if any(v is None for v in cur.values()) or any(v is None for v in base.values()):
            raise ValueError('ELEMENT_UNIT_DATA_MISSING')
        delta_total = sum(cur.values(), D(0)) - sum(base.values(), D(0))
        picked, surprise = _select_attrs(cur, base, delta_total)
        dims.append({'dim': '成本要素', 'surprise': round(surprise, 6),
                     'attributes': [{'name': n, 'delta': str(v), 'ep_pct': f'{ep * 100:.1f}%'} for n, v, ep in picked]})
        causes += [{'set': f'要素：{n}', 'dim': '成本要素', 'attrs': [n], 'ep': ep, 'surprise': surprise,
                    'direction': _direction(v)} for n, v, ep in picked]
        cur_m, base_m = _material_units(rows, factory, product, month), _material_units(rows, factory, product, base_month)
        shared = {n for n in cur_m if n in base_m}
        if len(shared) >= 2:
            mcur, mbase = {n: cur_m[n] for n in shared}, {n: base_m[n] for n in shared}
            picked_m, surprise_m = _select_attrs(mcur, mbase, delta_total)
            dims.append({'dim': '药材（材料单位成本内）', 'surprise': round(surprise_m, 6),
                         'attributes': [{'name': n, 'delta': str(v), 'ep_pct': f'{ep * 100:.1f}%'} for n, v, ep in picked_m]})
            causes += [{'set': f'药材：{n}', 'dim': '药材', 'attrs': [n], 'ep': ep, 'surprise': surprise_m,
                        'direction': _direction(v)} for n, v, ep in picked_m]
        total_delta = delta_total
    else:
        q_cur, q_base = _d(cur_row.get('产量(盒)')), _d(base_row.get('产量(盒)'))
        uc_cur, uc_base = _d(cur_row.get('单位成本(元/盒)')), _d(base_row.get('单位成本(元/盒)'))
        if None in (q_cur, q_base, uc_cur, uc_base):
            raise ValueError('TOTAL_BASIS_DATA_MISSING')
        c_uc, c_q = _shapley_two_factor(uc_base, uc_cur, q_base, q_cur)
        delta_total = (uc_cur * q_cur) - (uc_base * q_base)
        factors = {'单位成本（Shapley）': c_uc, '产量（Shapley）': c_q}
        picked, surprise = _select_attrs(factors, {k: D(0) for k in factors}, delta_total)
        dims.append({'dim': '总量两因子（Shapley 精确分配）', 'surprise': round(surprise, 6),
                     'attributes': [{'name': n, 'delta': str(v), 'ep_pct': f'{ep * 100:.1f}%'} for n, v, ep in picked]})
        causes += [{'set': n, 'dim': '两因子', 'attrs': [n], 'ep': ep, 'surprise': surprise,
                    'direction': _direction(v)} for n, v, ep in picked]
        units_cur = {label: _d(cur_row.get(col)) for label, col in _ELEM_COLS}
        units_base = {label: _d(base_row.get(col)) for label, col in _ELEM_COLS}
        if any(v is None for v in (*units_cur.values(), *units_base.values())):
            raise ValueError('ELEMENT_UNIT_DATA_MISSING')
        ecur = {label: value * q_cur for label, value in units_cur.items()}
        ebase = {label: value * q_base for label, value in units_base.items()}
        picked_e, surprise_e = _select_attrs(ecur, ebase, delta_total)
        dims.append({'dim': '成本要素（总额）', 'surprise': round(surprise_e, 6),
                     'attributes': [{'name': n, 'delta': str(v), 'ep_pct': f'{ep * 100:.1f}%'} for n, v, ep in picked_e]})
        causes += [{'set': f'要素（总额）：{n}', 'dim': '成本要素', 'attrs': [n], 'ep': ep, 'surprise': surprise_e,
                    'direction': _direction(v)} for n, v, ep in picked_e]
        total_delta = delta_total
    causes.sort(key=lambda c: -abs(c['ep']))
    for rank, c in enumerate(causes[:5], 1):
        c['rank'] = rank
        c['ep_pct'] = f'{c["ep"] * 100:.1f}%'
        c['surprise'] = round(c['surprise'], 6)
        c['ep'] = float(c['ep'])  # JSON 可序列化（快照入库走无 default=str 的 dumps）
    return {'total_delta': str(total_delta), 'direction': _direction(total_delta), 'dims': dims,
            'root_causes': [{k: c[k] for k in ('rank', 'set', 'dim', 'attrs', 'ep', 'ep_pct', 'surprise', 'direction')} for c in causes[:5]]}


def _unit_series(rows, factory, product) -> dict[str, D]:
    out = {}
    for r in rows:
        if r['kind'] == 'cost' and r['factory'] == factory and r['product'] == product:
            uc = _d(r['data'].get('单位成本(元/盒)'))
            if uc is not None:
                out[r['month']] = uc
    return out


def did(rows, factory, product, month, control=None) -> dict:
    # Only the supplied data batch can provide comparison factories. A globally
    # active dataset with matching product names must never become a control.
    available = sorted({r['factory'] for r in rows if r['kind'] == 'cost'
                        and r['product'] == product and r['factory'] != factory})
    candidates = [control] if control else available
    treat, delta = _unit_series(rows, factory, product), None
    window = [_shift(month, -k) for k in (3, 2, 1)]
    for ctrl in candidates:
        series = _unit_series(rows, ctrl, product)
        need = [month] + window
        if not all(m in treat and m in series for m in need):
            continue
        pre_t = sum((treat[m] for m in window), D(0)) / 3
        pre_c = sum((series[m] for m in window), D(0)) / 3
        delta = (treat[month] - pre_t) - (series[month] - pre_c)
        # 安慰剂：把“事件月”前移一期，DiD 应≈0
        placebo_month, placebo_window = _shift(month, -1), [_shift(month, -k) for k in (4, 3, 2)]
        placebo = None
        if all(m in treat and m in series for m in [placebo_month] + placebo_window):
            pt = sum((treat[m] for m in placebo_window), D(0)) / 3
            pc = sum((series[m] for m in placebo_window), D(0)) / 3
            placebo = (treat[placebo_month] - pt) - (series[placebo_month] - pc)
        flag = '未验证'
        diagnostic = '前置月份不足，未计算历史变化差异'
        if placebo is not None:
            bound = max(D('0.05'), _PLACEBO_RATIO * abs(delta))
            diagnostic = ('历史变化差异未超过预设经验阈值' if abs(placebo) <= bound
                          else '历史变化差异超过预设经验阈值，需核查可比性')
        return {'status': 'PASS', 'control': ctrl, 'tau': str(delta.quantize(D('0.0001'))),
                'placebo_tau': None if placebo is None else str(placebo.quantize(D('0.0001'))),
                'label': '跨厂前后变化对照', 'parallel_trend': flag,
                'diagnostic': diagnostic, 'comparison_window': window,
                'current_period': [month], 'value_unit': '元/盒',
                'causal_identification': 'NOT_ESTABLISHED',
                'assumption': '本月相对前三个月均值的本厂变化减去对照厂变化；历史差异阈值仅是描述性检查，不能证明平行趋势。未指定独立干预事件，不能解释为因果效应。'}
    return {'status': 'UNAVAILABLE', 'reason': '缺少可作对照且期间数据完整的同产品其他工厂'}


def price_signal(rows, factory, product, month, base_month) -> dict:
    cur, base = _material_units(rows, factory, product, month), _material_units(rows, factory, product, base_month)
    materials = []
    for name in sorted(set(cur) & set(base)):
        if base[name] == 0:
            continue
        market = _market_change(rows, name, month, base_month)
        unit = (cur[name] - base[name]) / base[name] * 100
        entry = {'name': name, 'market_change_pct': None if market is None else f'{market:.2f}%',
                 'unit_change_pct': f'{unit:.2f}%', 'consistent': False, 'price_explained': 0.0,
                 'aligned_magnitude_ratio': 0.0}
        if market is not None and abs(unit) > 0.05 and (market > 0) == (unit > 0):
            entry['consistent'] = True
            entry['price_explained'] = max(-1.0, min(1.0, float(market / unit)))
            entry['aligned_magnitude_ratio'] = entry['price_explained']
        materials.append(entry)
    weighted = 0.0
    if materials:
        total_move = sum(abs(float(m['unit_change_pct'].rstrip('%'))) for m in materials) or 1.0
        weighted = sum(m['price_explained'] * abs(float(m['unit_change_pct'].rstrip('%'))) for m in materials) / total_move
    if not materials or not any(m['market_change_pct'] is not None for m in materials):
        return {'status': 'UNAVAILABLE', 'materials': materials,
                'reason': '缺少同一期间可匹配的市场行情或原料单位消耗成本，不计算行情同向信号'}
    return {'status': 'PASS', 'materials': materials,
            'aggregate_price_explained_pct': f'{max(0.0, weighted) * 100:.1f}%',
            'aligned_magnitude_index_pct': f'{max(0.0, weighted) * 100:.1f}%',
            'label': '行情同向幅度指标',
            'note': '同向幅度指标是市场价变动与材料单位消耗成本变动的有界比值，仅供核查排序，不是价格解释度、概率或成本贡献。缺少企业采购单价与实耗，不能进行严格价差/量差分解。'}


def rank(localized: dict, price: dict | None, did_result: dict | None) -> list[dict]:
    price_by_name = {m['name']: m for m in (price or {}).get('materials', [])}
    did_tau = _d((did_result or {}).get('tau')) if (did_result or {}).get('status') == 'PASS' else None
    up = localized['direction'] == '上升'
    ranking = []
    for cause in localized['root_causes']:
        price_aff = 0.0
        for attr in cause['attrs']:
            m = price_by_name.get(attr)
            if m and m['consistent']:
                price_aff = max(price_aff, m['price_explained'])
        if did_tau is None:
            did_align = 0.3
        else:
            did_align = 1.0 if ((did_tau > 0) == up and did_tau != 0) else 0.0
        ep = min(abs(float(cause['ep'])), 1.0)
        score = 0.5 * ep + 0.25 * price_aff + 0.25 * did_align
        label = '高' if score >= 0.65 else ('中' if score >= 0.4 else '低')
        ranking.append({'cause': cause['set'], 'direction': cause['direction'],
                        'ep_pct': cause['ep_pct'], 'score': round(score, 3), 'label': label,
                        'priority': label, 'score_kind': 'review_priority_heuristic',
                        'basis': f'占同口径变动{cause["ep_pct"]}'
                                 + ('；存在行情同向信号' if price_aff > 0 else '')
                                 + ('；跨厂变化对照同向' if did_align == 1.0 else ('；跨厂变化对照反向' if did_align == 0.0 and did_tau is not None else '；跨厂变化对照缺失')),
                        'note': '经验权重仅表示核查优先级，不是原因发生概率；不同维度存在包含关系，不可相加。'})
    ranking.sort(key=lambda r: (-r['score'], r['cause']))
    return ranking[:5]


def support_for_rows(rows, factory, product, month, analysis_type='monthly', control=None):
    """Freeze optional evidence while the official snapshot's data is available.

    Consumers never reopen that dataset; imported enterprises do not use this
    pharmaceutical-only adapter. Quarterly market/causal identification is not
    inferred from the final month of the quarter.
    """
    if analysis_type == 'quarterly':
        return {key: {'status': 'UNAVAILABLE', 'reason': reason} for key, reason in (
            ('did', '当前季度尚无已验证的跨厂前后对照方法；不使用季度末单月结果替代'),
            ('price_signal', '季度缺少可比采购价格与实耗；不把末月行情替代整个季度'))}
    out = {}
    for key, fn in (
        ('did', lambda: did(rows, factory, product, month, control)),
        ('price_signal', lambda: price_signal(rows, factory, product, month, _shift(month, -1))),
    ):
        try:
            out[key] = fn()
        except (ValueError, KeyError, TypeError) as exc:
            out[key] = {'status': 'UNAVAILABLE', 'reason': '当前数据无法计算此项：' + str(exc)[:120]}
    return out


def _snapshot_localize(snapshot, compare):
    basis = snapshot.get('basis', 'unit')
    delta_total = _d((snapshot.get('comparison', {}).get(compare) or {}).get('delta'))
    if delta_total is None:
        raise ValueError('BASE_PERIOD_DATA_MISSING')
    cur, base = {}, {}
    for element in snapshot.get('elements', []):
        values = element.get('comparisons', {}).get(compare, {}).get(basis, {})
        key = element.get('name') or element['key']
        cur[key], base[key] = _d(values.get('current')), _d(values.get('base'))
    if not cur or any(v is None for v in (*cur.values(), *base.values())):
        raise ValueError('ELEMENT_UNIT_DATA_MISSING')
    if abs(sum(cur.values(), D(0)) - sum(base.values(), D(0)) - delta_total) > D('0.000000000001'):
        raise ValueError('ELEMENTS_DO_NOT_RECONCILE')
    dims, causes = [], []

    def dimension(name, current, previous, prefix):
        picked, surprise = _select_attrs(current, previous, delta_total)
        dims.append({'dim': name, 'surprise': round(surprise, 6),
                     'attributes': [{'name': n, 'delta': str(v), 'ep_pct': f'{ep * 100:.1f}%'}
                                    for n, v, ep in picked]})
        causes.extend({'set': prefix + n, 'dim': name, 'attrs': [n], 'ep': ep,
                       'surprise': surprise, 'direction': _direction(v)} for n, v, ep in picked)

    dimension('成本要素' if basis == 'unit' else '成本要素（总额）', cur, base, '要素：')
    if basis == 'total':
        periods = snapshot.get('period_values') or {}
        current, previous = periods.get('current') or {}, periods.get(compare) or {}
        values = [_d(row.get(key)) for row in (previous, current) for key in ('unit_cost', 'quantity')]
        if None not in values:
            u0, q0, u1, q1 = values
            c_u, c_q = _shapley_two_factor(u0, u1, q0, q1)
            if abs(c_u + c_q - delta_total) > D('0.000000000001'):
                raise ValueError('TOTAL_FACTORS_DO_NOT_RECONCILE')
            factors = {'单位成本（Shapley）': c_u, '产量（Shapley）': c_q}
            dimension('总量两因子（Shapley 精确分配）', factors, {k: D(0) for k in factors}, '')
    elif compare == 'mom':
        material_current, material_base = {}, {}
        for material in snapshot.get('materials_summary') or []:
            a, b = _d(material.get('current')), _d(material.get('previous'))
            if a is not None and b is not None:
                material_current[material['name']], material_base[material['name']] = a, b
        if material_current:
            dimension('原料明细（材料内，限完整记录）', material_current, material_base, '原料：')
    causes.sort(key=lambda c: -abs(c['ep']))
    roots = []
    for index, cause in enumerate(causes[:5], 1):
        roots.append({**cause, 'rank': index, 'ep_pct': f'{cause["ep"] * 100:.1f}%',
                      'ep': float(cause['ep']), 'surprise': round(cause['surprise'], 6)})
    return {'total_delta': str(delta_total), 'direction': _direction(delta_total),
            'dims': dims, 'root_causes': roots}


def analyze_attribution_snapshot(snapshot, compare='mom') -> dict:
    """Use the exact frozen period, enterprise, basis and figures being shown."""
    if compare not in ('mom', 'yoy', 'budget'):
        raise ValueError('INVALID_COMPARISON')
    basis = snapshot.get('basis', 'unit')
    if basis not in ('unit', 'total'):
        raise ValueError('INVALID_BASIS')
    period = snapshot.get('period') or {}
    base_period = (snapshot.get('metrics', {}).get(compare) or {}).get('comparison_period') or []
    result = {'version': ATTRIBUTION_VERSION,
              **{key: snapshot.get(key) for key in ('snapshot_id', 'context_id', 'factory', 'product', 'month', 'analysis_type')},
              'period': period, 'base_period': base_period,
              'base_month': base_period[-1] if base_period else None, 'basis': basis, 'compare': compare,
              'value_unit': (snapshot.get('metrics', {}).get('unit_cost' if basis == 'unit' else 'total_cost') or {}).get('unit'),
              'ranking_label': '核查优先级', 'ranking_is_probability': False}
    try:
        localized = _snapshot_localize(snapshot, compare)
    except ValueError as exc:
        code = str(exc)
        return {**result, 'status': 'UNAVAILABLE', 'reason_code': code, 'reason': {
            'BASE_PERIOD_DATA_MISSING': '缺少完整比较期数据，无法计算变动定位',
            'ELEMENT_UNIT_DATA_MISSING': '比较期要素数据缺失；不将缺失当作零',
            'ELEMENTS_DO_NOT_RECONCILE': '要素变化与所选口径总变化不勾稽，需先核查数据',
            'TOTAL_FACTORS_DO_NOT_RECONCILE': '产量与单位成本乘积未能与总成本变化勾稽',
        }.get(code, code)}
    support = snapshot.get('attribution_support') or {}
    for key in ('did', 'price_signal'):
        result[key] = support.get(key) if compare == 'mom' and support.get(key) else {
            'status': 'UNAVAILABLE', 'reason': '当前数据范围与比较期未提供此项可验证信号；不读取其他企业或期间的数据'}
    result.update({'status': 'PASS', **localized})
    result['ranking'] = rank(localized, result['price_signal'], result['did'])
    result['contract'] = ('归因定位复用当前数据快照与同一比较期的程序计算；占变动比例不是因果解释率。'
                          '核查优先级不是概率，跨维度不可相加。行情与跨厂变化只能支持待核查假设。')
    return result


def analyze_attribution(factory, product, month, basis='unit', compare='mom', *,
                        analysis_type='monthly', context_id=None, snapshot=None) -> dict:
    """Compatibility entry point; callers with a frozen snapshot pass it directly."""
    if snapshot is None:
        if context_id is not None:
            from .industry import analyze_reference
            snapshot = analyze_reference(context_id, factory, product, month, analysis_type, basis)
        else:
            from .metrics import analyze
            snapshot = analyze(factory, product, month, analysis_type, basis)
    return analyze_attribution_snapshot(snapshot, compare)
