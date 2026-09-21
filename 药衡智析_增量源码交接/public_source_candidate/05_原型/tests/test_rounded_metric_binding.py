# -*- coding: utf-8 -*-
"""注册指标值四舍五入简写绑定（claim-contract-v10）单元与合同测试。

背景（2026-09-21 审计问题 #1）：实测 glm-5.3-flash 与 DeepSeek 都会在
suggestion/missing_evidence 等字段写出注册值的四舍五入简写（注册
-15.2152% 被写成"下降15.2%"），旧合同一概拒收导致报告/对标全线
DEGRADED。v10 合同按确定性规则唯一绑定这类简写；编造数字依然拒收。
"""
import pytest
from pharma.narrative import _rounded_metric_bindings, validate_findings


def _metrics():
    return {
        'mom_rate': {'metric_id': 'mom_rate', 'label': '材料环比变动率',
                     'display_value': '-15.21528316524437548487199379', 'unit': '%'},
        'contribution': {'metric_id': 'contribution', 'label': '贡献度',
                         'display_value': '76.92307692307692307692307692', 'unit': '%'},
        'unit_delta': {'metric_id': 'unit_delta', 'label': '单位变动额',
                       'display_value': '-0.40', 'unit': '元/盒'},
        'quantity': {'metric_id': 'quantity', 'label': '产量',
                     'display_value': '35000', 'unit': '盒'},
    }


def test_unique_rounded_percent_binds_with_direction_word():
    text = '材料总成本下降15.2%，需核查采购台账'
    stripped, bindings = _rounded_metric_bindings(text, _metrics())
    assert '15.2' not in stripped
    assert bindings == [{'type': 'rounded_registered_metric', 'metric_id': 'mom_rate',
                         'shown': '15.2%', 'registered': '-15.21528316524437548487199379'}]


def test_signed_token_binds_without_direction_word():
    stripped, bindings = _rounded_metric_bindings('变动率为-15.22%', _metrics())
    assert bindings and bindings[0]['metric_id'] == 'mom_rate'


def test_unsigned_positive_token_without_direction_word_rejected():
    stripped, bindings = _rounded_metric_bindings('变动15.2%', _metrics())
    assert bindings == [] and '15.2' in stripped


def test_direction_word_contradiction_rejected():
    # “上升”搭配负值注册：方向词与符号矛盾，不得绑定
    stripped, bindings = _rounded_metric_bindings('出现上升15.2%的波动', _metrics())
    assert bindings == []


def test_integer_shorthand_cannot_launder_fractional_value():
    stripped, bindings = _rounded_metric_bindings('贡献度77%', _metrics())
    assert bindings == [] and '77' in stripped


def test_exact_integer_value_binds():
    stripped, bindings = _rounded_metric_bindings('本月产量35000盒待核', _metrics())
    assert bindings and bindings[0]['metric_id'] == 'quantity'


def test_percent_family_mismatch_not_bound():
    # 无百分号 token 不得绑定 % 单位注册值（0.15 与 -15.2152 数值也不同，双保险）
    stripped, bindings = _rounded_metric_bindings('差异0.15元', _metrics())
    assert bindings == []


def test_ambiguous_candidate_not_bound():
    metrics = _metrics()
    metrics['twin'] = {'metric_id': 'twin', 'label': '另一环比',
                       'display_value': '-15.21528316524437548487199379', 'unit': '%'}
    stripped, bindings = _rounded_metric_bindings('下降15.2%', metrics)
    assert bindings == []


def test_iso_date_digits_not_treated_as_number():
    stripped, bindings = _rounded_metric_bindings('核查2026-06台账与77%占比', _metrics())
    assert any(b['shown'] == '77%' for b in bindings) is False
    assert '2026-06' in stripped


def _insufficient_finding(suggestion):
    return {'claim_type': 'insufficient_evidence', 'section': 'materials',
            'text_template': '未提供对应月份采购合同台账，尚不能确认价格机制，需核查采购记录。',
            'missing_evidence': ['对应月份采购合同台账'], 'suggestion': suggestion,
            'verification_target': '本期采购台账', 'expected_evidence': ['采购合同台账'],
            'responsible_role': '采购部', 'deadline_basis': ''}


def _snapshot():
    return {'month': '2026-06', 'product': '六味地黄胶囊', 'factory': '中药一厂',
            'specification': '0.3g×60粒/盒', 'period': {'start': '2026-06', 'end': '2026-06'},
            'metrics': {
                'mom_rate': {'metric_id': 'mom_rate', 'label': '材料环比变动率',
                             'display_value': '-15.21528316524437548487199379', 'unit': '%'},
                'contribution': {'metric_id': 'contribution', 'label': '贡献度',
                                 'display_value': '76.92307692307692307692307692307692', 'unit': '%'},
                'quantity': {'metric_id': 'quantity', 'label': '产量',
                             'display_value': '35000', 'unit': '盒'},
            },
            'elements': [{'key': 'materials', 'name': '直接材料'}]}


def test_validate_accepts_rounded_shorthand_in_suggestion():
    out = validate_findings([_insufficient_finding('按批次核对采购价，重点覆盖下降15.2%的品项')], _snapshot(), [])
    bindings = out[0]['numeric_bindings']
    assert any(b.get('type') == 'rounded_registered_metric' and b.get('shown') == '15.2%' for b in bindings)


def test_validate_still_rejects_fabricated_number():
    with pytest.raises(ValueError, match='free business number forbidden'):
        validate_findings([_insufficient_finding('重点核对下降77%的品项')], _snapshot(), [])


def test_validate_still_rejects_unsigned_ambiguous_number():
    with pytest.raises(ValueError, match='free business number forbidden'):
        validate_findings([_insufficient_finding('重点核对差异3%的品项')], _snapshot(), [])
