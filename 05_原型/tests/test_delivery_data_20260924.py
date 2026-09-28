"""交付审计反例：独立假设数据，不改题包、不调用模型。"""
import importlib
import json
from decimal import Decimal
from pathlib import Path

import pytest

from pharma import data_import, import_pipeline, industry, ingestion


@pytest.fixture()
def runtime(tmp_path, monkeypatch):
    from pharma import config
    monkeypatch.setenv('PHARMA_RUNTIME_DIR', str(tmp_path))
    importlib.reload(config)
    importlib.reload(data_import)
    monkeypatch.setattr(industry, 'ENTERPRISE_REGISTRY', tmp_path / 'enterprise_registry.json')
    return tmp_path


def _upload(text, name='成本.csv'):
    record = data_import.create_upload('business', name, text.encode('utf-8'), 'cost_summary')
    mapping = {h: v for h, v in data_import.suggest_mapping(record['meta']['preview']['headers']).items()
               if not h.startswith('_')}
    return record, mapping


def _published_facts(result):
    config_path = Path(industry._registered()[result['context_id']])
    return json.loads((config_path.parent / 'facts.json').read_text(encoding='utf-8'))


def test_public_contract_boots_without_private_or_competition_masterdata(tmp_path, monkeypatch):
    monkeypatch.delenv('PHARMA_PRIVATE_MASTERDATA_FILE', raising=False)
    monkeypatch.setenv('PHARMA_COMPETITION_CONFIG_DIR', str(tmp_path / 'not-installed'))
    contract = ingestion.source_contract()
    assert contract['factories'] and contract['specifications'] and contract['fields']


@pytest.mark.parametrize('publisher', ['single', 'workspace'])
def test_row_budget_marker_preserves_scenarios_after_publication(runtime, publisher):
    record, mapping = _upload('工厂,产品,月份,产量,直接材料,场景\n'
                              'F,P,2026-02,10,100,实际\n'
                              'F,P,2026-02,10,80,预算\n')
    options = {'budget_marker': '预算'}
    assert data_import.validate_business(record, mapping, options)['status'] == 'VALID'
    if publisher == 'single':
        result = data_import.publish_business(record, mapping, options, '企业', 'generic_manufacturing', '件')
    else:
        result = data_import.publish_workspace([(record, mapping, options)])
    facts = _published_facts(result)
    assert {f['scenario']: Decimal(f['amount']) for f in facts['costs']} == {
        'actual': Decimal(100), 'budget': Decimal(80)}
    assert len(facts['quantities']) == 2


def test_mixed_explicit_amount_units_are_normalized_per_column(runtime):
    record, mapping = _upload('工厂,产品,月份,产量,直接材料(万元),直接人工(元)\nF,P,2026-02,10,1,100\n')
    assert mapping['直接材料(万元)'] == 'element:material'
    options = import_pipeline._options_for(record)
    result = data_import.publish_workspace([(record, mapping, options)])
    amounts = {f['element_id']: Decimal(f['amount']) for f in _published_facts(result)['costs']}
    assert amounts == {'material': Decimal(10000), 'labor': Decimal(100)}


def test_non_amount_header_cannot_scale_business_amounts(runtime):
    record, mapping = _upload('工厂,产品,月份,产量,直接材料,备注预算(万元)\nF,P,2026-02,10,100,年度规划\n')
    result = data_import.publish_workspace([(record, mapping, import_pipeline._options_for(record))])
    assert Decimal(_published_facts(result)['costs'][0]['amount']) == 100


@pytest.mark.parametrize('publisher', ['single', 'workspace'])
def test_one_missing_cost_cell_cannot_become_a_low_total(runtime, publisher):
    record, mapping = _upload('工厂,产品,月份,产量,直接材料,直接人工,制造费用\n'
                              'F,P,2026-01,10,31,10,9\n'
                              'F,P,2026-02,10,,10,9\n'
                              'F,P,2026-03,10,36,10,9\n')
    # Preview may retain partial data, but the incomplete February must not be
    # published as total=19 and unit_cost=1.9 (missing material is not zero).
    with pytest.raises(ValueError, match='INCOMPLETE_COST_AMOUNTS'):
        if publisher == 'single':
            data_import.publish_business(record, mapping, {}, '企业', 'generic_manufacturing', '件')
        else:
            data_import.publish_workspace([(record, mapping, {})])
    assert not industry.ENTERPRISE_REGISTRY.exists()


def _material_file(rows, filename='材料.csv'):
    record = data_import.create_upload('business', filename,
        ('工厂,产品,月份,产量,原材料名称,原材料总成本(元)\n' + rows).encode(), 'material_detail')
    mapping = {h: import_pipeline.DETAIL_TYPE_MAPPINGS['material_detail'].get(h, '')
               for h in record['meta']['preview']['headers']}
    return record, mapping, {'scenario': 'actual'}


def test_uploaded_materials_remain_drillable_and_reconcile_without_double_count(runtime):
    summary, mapping = _upload('工厂,产品,月份,产量,直接材料,直接人工\n'
                               'F,P,2026-01,10,80,20\nF,P,2026-02,10,100,20\n')
    detail = _material_file('F,P,2026-01,10,药材甲,50\nF,P,2026-01,10,药材乙,30\n'
                            'F,P,2026-02,10,药材甲,65\nF,P,2026-02,10,药材乙,35\n')
    published = data_import.publish_workspace([(summary, mapping, {}), detail])
    snapshot = industry.analyze_reference(published['context_id'], 'F', 'P', '2026-02')
    assert Decimal(snapshot['metrics']['total_cost']['value']) == 120
    assert snapshot['details']['available'] is True
    assert {r['原材料名称'] for r in snapshot['details']['materials']} == {'药材甲', '药材乙'}
    items = {r['name']: r for r in snapshot['materials_summary']}
    assert Decimal(items['药材甲']['current']) == Decimal('6.5')
    assert Decimal(items['药材甲']['delta']) == Decimal('1.5')
    assert Decimal(items['药材甲']['contribution']) == 75
    assert all(r['source_hash'] and '材料.csv:' in r['row_key'] for r in snapshot['details']['materials'])


def test_same_total_cannot_hide_conflicting_material_breakdown(runtime):
    old = _material_file('F,P,2026-02,10,药材甲,60\nF,P,2026-02,10,药材乙,40\n', '原明细.csv')
    data_import.publish_workspace([old])
    before = industry.ENTERPRISE_REGISTRY.read_bytes()
    conflict = _material_file('F,P,2026-02,10,药材甲,50\nF,P,2026-02,10,药材乙,50\n', '新明细.csv')
    with pytest.raises(ValueError, match='DETAIL_BREAKDOWN_CONFLICT'):
        data_import.publish_workspace([conflict])
    assert industry.ENTERPRISE_REGISTRY.read_bytes() == before


@pytest.mark.parametrize('publisher', ['single', 'workspace'])
def test_original_product_specifications_survive_import_without_global_fill(runtime, publisher):
    record, mapping = _upload('工厂,产品,产品规格,月份,产量,直接材料\n'
                              'F,P,2片/盒,2026-02,10,100\n'
                              'F,Q,5ml×10支/盒,2026-02,10,120\n'
                              'F,R,,2026-02,10,80\n')
    # A whole-file hint must not replace per-product source declarations or
    # masquerade as the original specification of a different product.
    options = {'specification': '无来源的全局规格'}
    if publisher == 'single':
        published = data_import.publish_business(record, mapping, options, '企业', 'generic_manufacturing', '盒')
    else:
        published = data_import.publish_workspace([(record, mapping, options)], quantity_unit='盒')
    for product, expected in [('P', '2片/盒'), ('Q', '5ml×10支/盒'), ('R', '导入数据未声明规格')]:
        snapshot = industry.analyze_reference(published['context_id'], 'F', product, '2026-02')
        assert snapshot['specification'] == expected


@pytest.mark.parametrize('publisher', ['single', 'workspace'])
def test_same_product_with_different_source_specifications_is_not_comparable(runtime, publisher):
    record, mapping = _upload('工厂,产品,产品规格,月份,产量,直接材料\n'
                              'F1,P,2片/盒,2026-02,10,100\n'
                              'F2,P,4片/盒,2026-02,10,120\n')
    with pytest.raises(ValueError, match='PRODUCT_SPECIFICATION_CONFLICT'):
        if publisher == 'single':
            data_import.publish_business(record, mapping, {}, '企业', 'generic_manufacturing', '盒')
        else:
            data_import.publish_workspace([(record, mapping, {})], quantity_unit='盒')
    assert not industry.ENTERPRISE_REGISTRY.exists()


def test_later_conflicting_specification_preserves_last_valid_workspace(runtime):
    first, mapping = _upload('工厂,产品,产品规格,月份,产量,直接材料\nF1,P,2片/盒,2026-02,10,100\n')
    data_import.publish_workspace([(first, mapping, {})], quantity_unit='盒')
    before = industry.ENTERPRISE_REGISTRY.read_bytes()
    second, mapping = _upload('工厂,产品,产品规格,月份,产量,直接材料\nF2,P,4片/盒,2026-02,10,120\n', '二厂.csv')
    with pytest.raises(ValueError, match='PRODUCT_SPECIFICATION_CONFLICT'):
        data_import.publish_workspace([(second, mapping, {})])
    assert industry.ENTERPRISE_REGISTRY.read_bytes() == before


@pytest.mark.parametrize('hypothesis', [
    '采购价格上涨导致成本增加，后续可能核查合同。',
    '可能节约 99 元，需核查采购合同。',
    '可能节约九万元，需核查采购合同。',
])
def test_import_model_cannot_bypass_numeric_or_causal_contract(monkeypatch, hypothesis):
    from types import SimpleNamespace
    from pharma import narrative
    gateway = SimpleNamespace(available=True, key='test-only', model='fixture', complete=lambda *a, **kw:
        (json.dumps({'hypotheses': [{'alert_id': 'a-total', 'element': '材料', 'hypothesis': hypothesis,
            'missing_evidence': ['对应月份采购合同台账'], 'suggestion': '核查合同'}]}, ensure_ascii=False), {}, {}))
    monkeypatch.setattr(narrative.ModelGateway, 'for_route', lambda role: gateway)
    assert import_pipeline._analysis_hypotheses([{'alert_id': 'a-total', 'element': '材料', 'basis': 'total'}]) is None


def test_import_model_keeps_trusted_alert_basis_and_marks_unverified_hypothesis(monkeypatch):
    from types import SimpleNamespace
    from pharma import narrative
    gateway = SimpleNamespace(available=True, key='test-only', model='fixture', complete=lambda *a, **kw:
        (json.dumps({'hypotheses': [{'alert_id': 'a-total', 'element': '伪造要素', 'basis': 'unit',
            'hypothesis': '采购价格变化可能影响材料成本，尚需核查。',
            'missing_evidence': ['对应月份采购合同台账'], 'suggestion': '核查采购合同台账'}]}, ensure_ascii=False), {}, {}))
    monkeypatch.setattr(narrative.ModelGateway, 'for_route', lambda role: gateway)
    result = import_pipeline._analysis_hypotheses([{'alert_id': 'a-total', 'element': '材料', 'basis': 'total'}])
    assert result[0]['basis'] == 'total' and result[0]['element'] == '材料'
    assert result[0]['evidence_support'] == 'unverified_import_hypothesis'
