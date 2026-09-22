# -*- coding: utf-8 -*-
"""确定性归因引擎合同测试（2026-09-22 方法论落地）。

全部断言针对程序化计算：同输入同输出、Decimal 精确可加、已知分布的 JSD、
两因子 Shapley 无残差、DiD/安慰剂算术、价格信号方向与有界性。"""
import json
import math
from decimal import Decimal as D

import pytest

from pharma import attribution as A


def _cost(factory, product, month, um, ul, uo, qty):
    uc = (D(um) + D(ul) + D(uo)).quantize(D('0.01'))
    return {'kind': 'cost', 'factory': factory, 'product': product, 'month': month,
            'data': {'直接材料(元/盒)': str(um), '直接人工(元/盒)': str(ul), '制造费用(元/盒)': str(uo),
                     '单位成本(元/盒)': str(uc), '产量(盒)': str(qty), '总成本(元)': str(uc * D(qty))}}


def _mat(factory, product, month, name, unit):
    return {'kind': 'materials', 'factory': factory, 'product': product, 'month': month,
            'data': {'原材料名称': name, '单位消耗成本(元/盒)': str(unit), '原材料总成本(元)': str(D(unit) * D(100)),
                     '占总材料成本比例': '10%'}}


def _market(herb, p5, p6):
    return {'kind': 'market', 'factory': '', 'product': '', 'month': '',
            'data': {'药材名称': herb, '5月价格': str(p5), '6月价格': str(p6)}}


def _series():
    rows = []
    # 处理厂：1-5 月平稳，6 月材料跳升（事件）；对照厂全期平稳
    for k in range(1, 7):
        m = f'2026-0{k}'
        um = D('4.00') if k < 6 else D('5.00')
        rows.append(_cost('甲厂', '品A', m, um, '1.00', '1.00', 1000))
        rows.append(_cost('乙厂', '品A', m, '4.10', '1.00', '1.00', 800))
    rows += [_mat('甲厂', '品A', '2026-05', n, u) for n, u in (('草一', '2.40'), ('草二', '1.20'), ('草三', '0.40'))]
    rows += [_mat('甲厂', '品A', '2026-06', n, u) for n, u in (('草一', '3.40'), ('草二', '1.10'), ('草三', '0.50'))]
    rows.append(_market('草一', 100, 130))  # 市场价 +30% 与草一单耗 +41.7% 同向
    return rows


def test_jsd_known_values():
    assert A._jsd([1, 0], [0, 1]) == pytest.approx(math.log(2), abs=1e-9)
    assert A._jsd([1, 2], [1, 2]) == pytest.approx(0.0, abs=1e-12)
    assert abs(A._jsd([2, 1], [1, 2]) - A._jsd([1, 2], [2, 1])) < 1e-12  # 对称


def test_shapley_two_factor_exact_additivity():
    # 任意两因子：Shapley 分配之和恒等于总量变化（交互项对半分，无残差）
    for a0, a1, b0, b1 in ((D('2'), D('3'), D('10'), D('12')), (D('7.5'), D('6.2'), D('40'), D('55'))):
        c_a, c_b = A._shapley_two_factor(a0, a1, b0, b1)
        assert c_a + c_b == a1 * b1 - a0 * b0
    # 顺序无关：交换因子角色各自贡献对调（同一交互项均分）
    c_a1, c_b1 = A._shapley_two_factor(D('2'), D('3'), D('10'), D('12'))
    c_b2, c_a2 = A._shapley_two_factor(D('10'), D('12'), D('2'), D('3'))
    assert c_a1 == c_a2 and c_b1 == c_b2


def test_localization_unit_ep_exact_and_material_dim():
    result = A.localize(_series(), '甲厂', '品A', '2026-06', '2026-05', basis='unit')
    # ΔUC = +1.00，材料 +1.00 → 材料 EP = 100%；人工/制造费用未变不入选
    assert result['total_delta'] == '1.00' and result['direction'] == '上升'
    top = result['root_causes'][0]
    assert top['set'] == '要素：材料' and top['ep_pct'] == '100.0%'
    mats = [c for c in result['root_causes'] if c['dim'] == '药材']
    assert mats and mats[0]['set'] == '药材：草一'
    # 草一 Δ=+1.00 → 对 ΔUC=+1.00 的 EP 也是 100%（药材维在材料要素内细分）
    assert mats[0]['ep_pct'] == '100.0%'


def test_localization_total_shapley_split():
    # 量价同变：两因子 Shapley 分配精确可加且顺序无关
    rows = [_cost('丙厂', '品B', '2026-05', '2', '1', '1', 100),
            _cost('丙厂', '品B', '2026-06', '3', '1', '1', 150)]
    result = A.localize(rows, '丙厂', '品B', '2026-06', '2026-05', basis='total')
    assert D(result['total_delta']) == D('350.00')  # 5×150 − 4×100
    c_uc, c_q = A._shapley_two_factor(D('4'), D('5'), D('100'), D('150'))
    assert c_uc + c_q == D('350')
    # 产量不变时零变动因子不入选（同向过滤），全部落在单位成本
    rows2 = _series()
    result2 = A.localize(rows2, '甲厂', '品A', '2026-06', '2026-05', basis='total')
    by_set = {c['set'] for c in result2['root_causes']}
    assert '产量（Shapley）' not in by_set


def test_did_recovers_known_effect_and_placebo_clean():
    rows = _series()
    result = A.did(rows, '甲厂', '品A', '2026-06', control='乙厂')
    assert result['status'] == 'PASS' and result['control'] == '乙厂'
    # 处理厂 6月较前置均值 +1.00，对照厂 0 → τ̂ = +1.0000
    assert D(result['tau']) == D('1.0000')
    assert result['placebo_tau'] is not None and abs(D(result['placebo_tau'])) < D('0.05')
    assert result['parallel_trend'] == '稳健'
    assert '平行趋势' in result['assumption']


def test_did_unavailable_without_control():
    rows = [r for r in _series() if r['factory'] == '甲厂']
    result = A.did(rows, '甲厂', '品A', '2026-06')
    assert result['status'] == 'UNAVAILABLE' and result['reason']


def test_price_signal_direction_and_bounds():
    result = A.price_signal(_series(), '甲厂', '品A', '2026-06', '2026-05')
    by_name = {m['name']: m for m in result['materials']}
    assert by_name['草一']['consistent'] is True
    assert 0 < by_name['草一']['price_explained'] <= 1.0  # 30/41.7≈0.72，有界
    assert by_name['草二']['consistent'] is False  # 单耗下降
    assert '%' in result['aggregate_price_explained_pct']


def test_ranking_orders_and_labels():
    rows = _series()
    localized = A.localize(rows, '甲厂', '品A', '2026-06', '2026-05')
    price = A.price_signal(rows, '甲厂', '品A', '2026-06', '2026-05')
    did_result = A.did(rows, '甲厂', '品A', '2026-06', control='乙厂')
    ranking = A.rank(localized, price, did_result)
    scores = [r['score'] for r in ranking]
    assert scores == sorted(scores, reverse=True)
    assert all(r['label'] in ('高', '中', '低') for r in ranking)
    # 带行情同向支持的药材根因应排在无行情支持的同等 EP 根因之前
    top_basis = ranking[0]['basis']
    assert '解释力' in top_basis


def test_analyze_deterministic_and_shape(monkeypatch):
    rows = _series()
    monkeypatch.setattr(A, 'load_rows', lambda *a, **k: rows)
    import pharma.metrics as _m
    monkeypatch.setattr(_m, 'benchmark_partner', lambda factory=None, product=None: '乙厂')
    first = A.analyze_attribution('甲厂', '品A', '2026-06')
    second = A.analyze_attribution('甲厂', '品A', '2026-06')
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)
    assert first['status'] == 'PASS' and first['version'] == A.ATTRIBUTION_VERSION
    assert first['did']['status'] == 'PASS' and first['price_signal']['status'] == 'PASS'
    assert len(first['ranking']) >= 2 and first['ranking'][0]['label'] == '高'


def test_missing_base_period_is_honest():
    rows = [_cost('甲厂', '品A', '2026-06', '5', '1', '1', 100)]
    with pytest.raises(ValueError, match='BASE_PERIOD_DATA_MISSING'):
        A.localize(rows, '甲厂', '品A', '2026-06', '2026-05')
