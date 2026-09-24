"""Framework has no shipped company; registration uses independent test facts."""
import json
from decimal import Decimal

from pharma import industry
from pharma.attribution import analyze_attribution_snapshot


def test_generic_pack_has_no_demonstration_company_or_business_facts(tmp_path, monkeypatch):
    monkeypatch.setattr(industry, 'ENTERPRISE_REGISTRY', tmp_path / 'registry.json')
    monkeypatch.setattr(industry, '_competition_available', lambda: False)
    monkeypatch.delenv('PHARMA_DATA_PACKAGE', raising=False)
    monkeypatch.delenv('PHARMA_SHOW_TEST_CONTEXTS', raising=False)
    pack = industry.load_pack('generic_manufacturing')
    assert pack.enterprise_entry is None and industry._enterprises(pack) == []
    assert not (industry.PACKS / pack.id / 'facts.json').exists()
    assert industry.context_catalog() == {'contexts': [], 'default_context_id': None}


def test_registered_generic_enterprise_is_visible_and_uses_only_its_facts(tmp_path, monkeypatch):
    monkeypatch.setattr(industry, 'ENTERPRISE_REGISTRY', tmp_path / 'registry.json')
    monkeypatch.setattr(industry, '_competition_available', lambda: False)
    monkeypatch.delenv('PHARMA_DATA_PACKAGE', raising=False)
    monkeypatch.delenv('PHARMA_SHOW_TEST_CONTEXTS', raising=False)
    profile = {'id': 'independent-example', 'name': '独立测试企业', 'dataset_id': 'test-only',
               'policy_version': '1', 'quantity_unit': '件', 'currency': 'CNY',
               'products': {'P': {'name': '独立产品', 'specification': '测试规格', 'version': '1'}}}
    costs, quantities = [], []
    for month, material in [('2026-05', '400'), ('2026-06', '600')]:
        scope = {'enterprise_id': profile['id'], 'factory_id': 'F', 'product_id': 'P', 'product_version': '1',
                 'period': month, 'cost_object': 'test-production', 'policy_version': '1',
                 'scope': 'completed', 'source_row': 'test-only:' + month, 'source_snapshot': 'independent'}
        for key, amount in [('materials', material), ('labor', '200')]:
            costs.append(industry.CostFact(**scope, fact_id=month + ':' + key, element_id=key,
                                          amount=amount, currency='CNY', quantity_unit='件'))
        quantities.append(industry.QuantityFact(**scope, fact_id=month + ':quantity', quantity='100', unit='件'))
    dataset = industry.NormalizedDataset(costs=costs, quantities=quantities)
    (tmp_path / 'enterprise.json').write_text(json.dumps(profile), encoding='utf-8')
    (tmp_path / 'facts.json').write_text(dataset.model_dump_json(), encoding='utf-8')
    (tmp_path / 'knowledge.json').write_text('[]', encoding='utf-8')
    context_id = industry.register_enterprise('generic_manufacturing', tmp_path / 'enterprise.json')
    catalog = industry.context_catalog()
    assert [c['context_id'] for c in catalog['contexts']] == [context_id]
    assert catalog['default_context_id'] == context_id
    snapshot = industry.analyze_reference(context_id, 'F', 'P', '2026-06')
    assert snapshot['data_provenance'] == 'user_import'
    assert Decimal(snapshot['period_values']['current']['unit_cost']) == Decimal('8')
    result = analyze_attribution_snapshot(snapshot)
    assert result['status'] == 'PASS' and Decimal(result['total_delta']) == Decimal('2')
    assert result['context_id'] == context_id and result['did']['status'] == 'UNAVAILABLE'
    # Re-registering this framework's first enterprise is permitted; it is not
    # confused with a bundled default and remains the same catalog entry.
    assert industry.register_enterprise('generic_manufacturing', tmp_path / 'enterprise.json') == context_id
