# -*- coding: utf-8 -*-
"""第9项审批方案实施测试（2026-09-24，docs/audits/2026-09-24-explain-validation-root-cause.md）。

覆盖：C1 整数/一位小数简写唯一绑定、C2 引文归一化与省略号拼接、C3 证据全库
救援（未召回但库内存在+适用→放行留痕）、C4 insufficient 句级合同、C5 身份
白名单环境变量别名、A 预算默认值提升。
"""
import pytest

from pharma import narrative
from pharma.knowledge import Knowledge
from pharma.narrative import (
    _quote_supported,
    _rounded_metric_bindings,
    classify_identity,
    validate_findings,
)


# ---------- C1 整数简写 ----------

def _metrics():
    return {
        'mom_rate': {'metric_id': 'mom_rate', 'label': '材料环比变动率',
                     'display_value': '-15.21528316524437548487199379', 'unit': '%'},
        'contribution': {'metric_id': 'contribution', 'label': '贡献度',
                         'display_value': '76.92307692307692307692307692', 'unit': '%'},
    }


def test_one_decimal_shorthand_binds():
    stripped, bindings = _rounded_metric_bindings('贡献度76.9%', _metrics())
    assert bindings and bindings[0]['metric_id'] == 'contribution'
    assert '76.9' not in stripped


def test_integer_shorthand_ambiguity_still_rejected():
    metrics = _metrics()
    # 两个注册值四舍五入到同一个整数 token → 歧义，不得绑定
    metrics['twin'] = {'metric_id': 'twin', 'label': '另一贡献',
                       'display_value': '77.4', 'unit': '%'}
    stripped, bindings = _rounded_metric_bindings('贡献度77%', metrics)
    assert bindings == [] and '77' in stripped


# ---------- C2 引文归一化与省略号 ----------

_SOURCE = '药材采购价格受季节影响，  提取收率每波动一个百分点，单位材料成本约变化 2%（测试系数）。'


def test_quote_with_whitespace_and_punctuation_variance_supported():
    quote = '提取收率每波动一个百分点，单位材料成本约变化2%'
    assert _quote_supported(quote, _SOURCE)


def test_quote_ellipsis_splice_supported_in_order():
    quote = '药材采购价格受季节影响……单位材料成本约变化 2%（测试系数）。'
    assert _quote_supported(quote, _SOURCE)


def test_quote_out_of_order_fragments_rejected():
    quote = '单位材料成本约变化 2%……药材采购价格受季节影响'
    assert not _quote_supported(quote, _SOURCE)


def test_quote_too_short_rejected():
    assert not _quote_supported('短引', _SOURCE)


# ---------- C4 insufficient 句级合同 ----------

def _insufficient(text_template):
    return {'claim_type': 'insufficient_evidence', 'section': 'materials',
            'text_template': text_template,
            'missing_evidence': ['对应月份采购合同台账'], 'suggestion': '',
            'verification_target': '本期采购台账', 'expected_evidence': ['采购合同台账'],
            'responsible_role': '采购部', 'deadline_basis': ''}


def _snapshot():
    return {'month': '2026-06', 'product': '六味地黄胶囊', 'factory': '中药一厂',
            'specification': '0.3g×60粒/盒', 'period': {'start': '2026-06', 'end': '2026-06'},
            'metrics': {}, 'elements': [{'key': 'materials', 'name': '直接材料'}]}


def test_insufficient_background_clause_within_sentence_passes():
    # 同一句内先写背景从句再补限定（旧分句级合同会拒收）——C4 句级后通过
    text = '现有采购价格波动较大，尚不能确认本期材料下降的具体机制，需核查采购合同台账。'
    findings = validate_findings([_insufficient(text)], _snapshot(), [])
    assert findings[0]['claim_type'] == 'insufficient_evidence'


def test_insufficient_pure_affirmative_sentence_rejected():
    text = '材料价格波动较大。采购台账需要核查。'  # 第一句纯背景无任何限定词
    with pytest.raises(ValueError, match='every sentence'):
        validate_findings([_insufficient(text)], _snapshot(), [])


# ---------- C3 证据全库救援 ----------

_LIBRARY_CHUNK = {'evidence_id': 'lib-evidence-1', 'source': '测试数据_知识文档.txt',
                  'text': '测试药厂采用喷雾干燥制粒工艺，提取收率波动会影响单位材料成本。',
                  'location': '第 2 页', 'scope': 'general'}


def _finding_with_quote():
    return {'claim_type': 'insufficient_evidence', 'section': 'materials',
            'text_template': '未提供对应批次提取收率化验单，尚不能确认收率波动影响，需核查生产记录。',
            'missing_evidence': ['对应批次提取收率化验单'], 'suggestion': '',
            'verification_target': '本期提取收率', 'expected_evidence': ['提取收率化验单'],
            'responsible_role': '生产部', 'deadline_basis': '',
            'evidence_refs': ['lib-evidence-1'],
            'evidence_quotes': {'lib-evidence-1': '提取收率波动会影响单位材料成本'}}


def test_unretrieved_but_in_library_evidence_rescued(monkeypatch):
    monkeypatch.setattr(Knowledge, 'evidence_in_library',
                        classmethod(lambda cls, evidence_id, context=None: dict(_LIBRARY_CHUNK)))
    findings = validate_findings([_finding_with_quote()], _snapshot(), [])
    assert findings[0].get('evidence_rescued') == ['lib-evidence-1']


def test_unknown_evidence_still_rejected(monkeypatch):
    monkeypatch.setattr(Knowledge, 'evidence_in_library',
                        classmethod(lambda cls, evidence_id, context=None: None))
    with pytest.raises(ValueError, match='unknown evidence'):
        validate_findings([_finding_with_quote()], _snapshot(), [])


def test_in_library_but_inapplicable_evidence_rejected(monkeypatch):
    def _inapplicable(cls, evidence_id, context=None):
        return {**_LIBRARY_CHUNK, 'products': ['别的产品']}
    monkeypatch.setattr(Knowledge, 'evidence_in_library', classmethod(_inapplicable))
    with pytest.raises(ValueError, match='inapplicable'):
        validate_findings([_finding_with_quote()], _snapshot(), [])


# ---------- C5 身份白名单环境变量别名 ----------

def test_identity_alias_from_env(monkeypatch):
    monkeypatch.setenv('PHARMA_MODEL_VERIFIED_ALIASES', 'glm-5.3:glm-5.3-flash')
    status, _reason = classify_identity('glm-5.3', 'glm-5.3-flash')
    assert status == 'VERIFIED_ALIAS'


def test_identity_static_alias_overrides_env(monkeypatch):
    monkeypatch.setenv('PHARMA_MODEL_VERIFIED_ALIASES', 'glm-5.3-flash:some-other-id')
    status, _reason = classify_identity('glm-5.3-flash', 'glm-5.3-flash')
    assert status == 'VERIFIED_EXACT'  # 精确一致优先于任何别名表


def test_identity_unlisted_return_still_mismatch(monkeypatch):
    monkeypatch.setenv('PHARMA_MODEL_VERIFIED_ALIASES', '')
    status, _reason = classify_identity('glm-5.3', 'deepseek-chat')
    assert status == 'MISMATCH'


# ---------- A 预算默认值 ----------

def test_budget_default_raised_to_300(monkeypatch):
    monkeypatch.delenv('PHARMA_MODEL_MAX_CALLS', raising=False)
    import inspect
    source = inspect.getsource(narrative.ModelGateway.__init__)
    assert "PHARMA_MODEL_MAX_CALLS','300'" in source
