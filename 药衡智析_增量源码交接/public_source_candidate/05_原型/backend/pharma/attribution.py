"""确定性归因引擎（2026-09-22 方法论落地，docs/数据全流程与归因方法评估）。

三层程序化归因，全部同输入同输出、可单测，不调用模型：
- localize   多维根因定位（ADtributor 式）：解释力 EP=Δ_属性/Δ_总量（会计可加），
             维度惊奇度 surprise=JSD(本期份额分布, 基期份额分布)（信息论），
             贪心选取同向属性；总额口径的量/价两因子用 Shapley 精确分配交互
             （二因子 Shapley = 序贯分解的平均，消除口径依赖且精确可加）。
- did        对照厂反事实（DiD）：τ̂=(处理厂前后差)−(对照厂前后差)，单位成本口径；
             附安慰剂检验（前置无事件月应≈0，超界标注“平行趋势存疑”）。
             对照厂选择复用 metrics.benchmark_partner（主数据指定优先+产品感知）。
- price_signal 药材行情价格传导信号：市场价变动% 与材料单位消耗成本变动% 同向时
             给出“价格传导解释度”估计（有界 0-100%，明示为估计而非分解）。
- rank       假设排序：0.5×解释力 + 0.25×价格传导 + 0.25×DiD 方向支持，
             输出 高/中/低 标签——供叙事层与报告引用（模型只拿名称与方向，不拿数字）。

诚实合同：所有输出为程序计算值；数据不满足（缺对照厂、缺行情、缺基期明细）
时该部分返回 UNAVAILABLE+原因，不臆造。
"""
from __future__ import annotations

import math
from decimal import Decimal as D

from .ingestion import load_rows

ATTRIBUTION_VERSION = 'attribution-v1-deterministic'

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
        ecur = {label: (_d(cur_row.get(col)) or D(0)) * q_cur for label, col in _ELEM_COLS}
        ebase = {label: (_d(base_row.get(col)) or D(0)) * q_base for label, col in _ELEM_COLS}
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
    from .metrics import benchmark_partner
    candidates = [control] if control else [p for p in (benchmark_partner(factory, product),) if p]
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
        flag = '未检验（前置月份不足）'
        if placebo is not None:
            bound = max(D('0.05'), _PLACEBO_RATIO * abs(delta))
            flag = '稳健' if abs(placebo) <= bound else '存疑'
        return {'status': 'PASS', 'control': ctrl, 'tau': str(delta.quantize(D('0.0001'))),
                'placebo_tau': None if placebo is None else str(placebo.quantize(D('0.0001'))),
                'parallel_trend': flag,
                'assumption': '平行趋势假设下的双重差分估计（处理厂前后变化−对照厂前后变化）；估计值供核查参考，不构成因果认定'}
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
                 'unit_change_pct': f'{unit:.2f}%', 'consistent': False, 'price_explained': 0.0}
        if market is not None and abs(unit) > 0.05 and (market > 0) == (unit > 0):
            entry['consistent'] = True
            entry['price_explained'] = max(-1.0, min(1.0, float(market / unit)))
        materials.append(entry)
    weighted = 0.0
    if materials:
        total_move = sum(abs(float(m['unit_change_pct'].rstrip('%'))) for m in materials) or 1.0
        weighted = sum(m['price_explained'] * abs(float(m['unit_change_pct'].rstrip('%'))) for m in materials) / total_move
    return {'status': 'PASS', 'materials': materials,
            'aggregate_price_explained_pct': f'{max(0.0, weighted) * 100:.1f}%',
            'note': '价格传导解释度为市场价变动与材料单位成本变动的同向比值（有界估计），非价量精确分解；采购单价与实物耗量数据到位后可升级为严格价差/量差'}


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
                        'basis': f'解释力{cause["ep_pct"]}'
                                 + (f'；行情同向(解释度{price_aff * 100:.0f}%)' if price_aff > 0 else '')
                                 + ('；DiD方向支持' if did_align == 1.0 else ('；DiD方向相反' if did_align == 0.0 and did_tau is not None else '；DiD未定'))})
    ranking.sort(key=lambda r: (-r['score'], r['cause']))
    return ranking[:5]


def analyze_attribution(factory, product, month, basis='unit', compare='mom') -> dict:
    rows = load_rows()
    base_month = _shift(month, -1) if compare == 'mom' else f'{int(month[:4]) - 1}{month[4:]}'
    result = {'version': ATTRIBUTION_VERSION, 'factory': factory, 'product': product,
              'month': month, 'base_month': base_month, 'basis': basis, 'compare': compare}
    try:
        localized = localize(rows, factory, product, month, base_month, basis)
        result.update({'status': 'PASS', **localized})
    except ValueError as exc:
        return {**result, 'status': 'UNAVAILABLE', 'reason': {
            'BASE_PERIOD_DATA_MISSING': '基期成本数据缺失，无法计算多维根因',
            'ELEMENT_UNIT_DATA_MISSING': '要素单位成本列缺失',
            'TOTAL_BASIS_DATA_MISSING': '总额口径产量/单位成本缺失'}.get(str(exc), str(exc))}
    for key, fn in (('did', lambda: did(rows, factory, product, month)),
                    ('price_signal', lambda: price_signal(rows, factory, product, month, base_month) if compare == 'mom'
                     else {'status': 'UNAVAILABLE', 'reason': '同比基期无行情对照（行情仅覆盖当期半年）'})):
        try:
            result[key] = fn()
        except Exception as exc:  # noqa: BLE001 单部件失败不拖垮整体
            result[key] = {'status': 'UNAVAILABLE', 'reason': type(exc).__name__ + ': ' + str(exc)[:120]}
    result['ranking'] = rank(localized, result.get('price_signal'), result.get('did'))
    result['contract'] = '本块全部数值由程序确定性计算（EP/JSD/Shapley/DiD）；估计类输出显式标注假设；数据不满足的部件返回 UNAVAILABLE 而非臆造'
    return result
