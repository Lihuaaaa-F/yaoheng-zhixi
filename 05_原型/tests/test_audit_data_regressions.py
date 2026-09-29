"""Independent synthetic regressions for data-path audit findings."""
import hashlib
import json
from pathlib import Path

import pytest
from pharma import attribution, data_import, decision, industry, ingestion, metrics
from test_attribution_snapshot import snapshot
from test_decision import FakeGateway, snapshot_factory, job_factory


@pytest.fixture
def imports(tmp_path, monkeypatch):
    monkeypatch.setattr(data_import, 'IMPORTS_ROOT', tmp_path / 'imports')
    monkeypatch.setattr(data_import, 'IMPORT_DB', tmp_path / 'imports.sqlite3')
    monkeypatch.setattr(data_import, '_imports_db_ready', False)
    return tmp_path / 'imports'


def test_invalid_workbook_can_be_retried_without_orphan(imports):
    payload = b'not an xlsx archive'
    for _ in range(2):
        with pytest.raises(Exception) as failure:
            data_import.create_upload('business', 'broken.xlsx', payload)
        assert not isinstance(failure.value, KeyError)
    assert not list(imports.glob('*/original.xlsx'))


def test_existing_orphan_upload_self_heals(imports):
    payload = '工厂,产品,月份,产量,直接材料\nF,P,2030-01,10,25\n'.encode()
    id_ = hashlib.sha256(payload).hexdigest()[:16] + '-business-cost_summary'
    folder = imports / id_
    folder.mkdir(parents=True)
    (folder / 'original.csv').write_bytes(payload)
    record = data_import.create_upload('business', '成本.csv', payload)
    assert record['status'] == 'UPLOADED'
    assert data_import.create_upload('business', '成本.csv', payload)['dedup']


def test_two_columns_cannot_map_to_one_detail_amount(imports):
    record = data_import.create_upload('business', '明细.csv',
        '工厂,产品,月份,产量,材料总成本,材料单位成本\nF,P,2030-01,10,100,10\n'.encode(), 'material_detail')
    mapping = dict(zip(record['meta']['preview']['headers'],
                       ['factory_id', 'product_id', 'period', 'quantity', 'element:material', 'element:material']))
    result = data_import.validate_business(record, mapping, {})
    assert result['status'] == 'INVALID'
    assert any('重复映射' in error['reason'] for error in result['errors'])


def test_zero_did_is_not_opposite_direction():
    result = attribution.rank({'direction': '上升', 'root_causes': [
        {'set': '材料', 'attrs': [], 'ep': .5, 'ep_pct': '50%', 'direction': '上升'}]}, None,
        {'status': 'PASS', 'tau': '0'})
    assert '反向' not in result[0]['basis']
    assert '无变化' in result[0]['basis']


@pytest.mark.parametrize(('residual', 'status'), [('0.0000005', 'PASS'), ('0.000002', 'UNAVAILABLE')])
def test_attribution_uses_ingestion_reconciliation_tolerance(residual, status):
    from decimal import Decimal
    value = snapshot()
    value['comparison']['mom']['delta'] = str(Decimal('2') + Decimal(residual))
    assert attribution.analyze_attribution_snapshot(value)['status'] == status


def test_artifact_repair_is_a_valid_advisory_signal():
    value = snapshot_factory()
    evaluation = decision.evaluate(value, [job_factory()], artifact_health=lambda _: False)
    route = FakeGateway({'decision': 'REPORT_NEEDED', 'signal_ids': ['artifact_health']})
    result = decision.advise(evaluation, value, gateway_factory=lambda _: route)
    assert result['advisory_status'] == 'PASS'
    assert result['decision'] == 'REPORT_NEEDED'


def test_dataset_cache_is_bounded(tmp_path, monkeypatch):
    config = tmp_path / 'enterprise.json'
    facts = tmp_path / 'facts.json'
    config.write_text('{}')
    facts.write_text('{}')
    monkeypatch.setattr(industry, '_DATASET_CACHE', {})
    monkeypatch.setattr(industry, '_read_dataset_uncached', lambda *args: object())
    for number in range(100):
        enterprise = {'_base_dir': tmp_path, '_config_file': config, 'facts_entry': 'facts.json', 'id': str(number)}
        industry._read_dataset({}, enterprise)
    assert len(industry._DATASET_CACHE) <= 32


def test_ingestion_utf8_does_not_depend_on_windows_locale(tmp_path, monkeypatch):
    from pharma import config
    write_text, read_text = Path.write_text, Path.read_text
    monkeypatch.setattr(Path, 'write_text', lambda self, data, encoding=None, **kw:
                        write_text(self, data, encoding=encoding or 'cp936', **kw))
    monkeypatch.setattr(Path, 'read_text', lambda self, encoding=None, **kw:
                        read_text(self, encoding=encoding or 'cp936', **kw))
    monkeypatch.setattr(config, 'SYNTHETIC_DETAIL_DIR', None)
    rows = [{'kind': 'cost', 'factory': '合成工厂', 'product': '合成产品', 'month': '2030-01',
             'row_key': 'synthetic:1', 'source_hash': 'synthetic', 'data': {'中文': '🙂'}}]
    monkeypatch.setattr(ingestion, '_read', lambda _: (rows, [], []))
    monkeypatch.setattr(ingestion, 'source_contract_hash', lambda: 'synthetic-contract')
    monkeypatch.setattr(ingestion, 'audit', lambda *args: {'status': 'VALID', 'errors': []})
    ingestion.ingest(tmp_path / 'source', tmp_path / 'snapshots')
    assert ingestion.load_rows(tmp_path / 'snapshots') == rows


def test_benchmark_display_rounds_half_up(monkeypatch):
    from copy import deepcopy
    base = {'metrics': {'unit_cost': {'value': '1', 'row_keys': [], 'source_hash': []}}, 'elements': []}
    monkeypatch.setattr(metrics, '_benchmark_factories', lambda *a, **kw: ('A', 'B'))
    monkeypatch.setattr(metrics, 'analyze', lambda *a, **kw: deepcopy(base))
    monkeypatch.setattr(metrics, '_benchmark_payload', lambda *a: {
        'summary': [{'key': 'unit_cost', 'name': '单位成本', 'delta': '-0.405', 'rate': '-40.5', 'right': '1'}],
        'elements': [], 'direction': 'A−B', 'period': {}, 'left': 'A', 'right': 'B', 'limits': [], 'basis': 'unit'})
    result, _ = metrics.benchmark_analysis('P', '2030-01')
    assert result['metrics']['benchmark:A:B:P:2030-01:unit_cost:delta']['display'] == '-0.41'


def test_missing_material_element_does_not_use_labor_denominator(monkeypatch):
    rows = []
    for month, amount in [('2030-01', '10'), ('2030-02', '20')]:
        common = {'factory': 'F', 'product': 'P', 'month': month, 'source_hash': 'synthetic'}
        rows.append({**common, 'kind': 'cost', 'row_key': month + ':cost', 'data': {
            '产量(盒)': '10', '总成本(元)': amount, '直接人工(元/盒)': str(int(amount) // 10), '产品规格': '合成规格'}})
        rows.append({**common, 'kind': 'materials', 'row_key': month + ':materials', 'data': {
            '产量(盒)': '10', '原材料总成本(元)': amount, '原材料名称': '独立合成材料'}})
    monkeypatch.setattr(metrics, 'ELEMENTS', {'labor': '直接人工'})
    monkeypatch.setattr(metrics, 'ingest', lambda: {'snapshot_id': 'synthetic', 'masterdata_hash': 'synthetic', 'contract_version': 'test'})
    monkeypatch.setattr(metrics, 'load_rows', lambda: rows)
    monkeypatch.setattr(metrics, 'source_contract_hash', lambda: 'synthetic')
    monkeypatch.setattr(metrics, 'source_contract', lambda: {'specifications': {'P': ['合成规格', 1, '盒', '合成类别']}})
    result = metrics.analyze('F', 'P', '2030-02')
    assert result['materials_summary'][0]['denominator'] is None
    assert result['materials_summary'][0]['contribution'] is None


def test_industry_utf8_snapshot_round_trip_under_windows_locale(tmp_path, monkeypatch):
    from test_industry import dataset, fact, qty
    value = dataset([fact(enterprise_id='合成🙂')], [qty(enterprise_id='合成🙂')])
    write_text, read_text = Path.write_text, Path.read_text
    monkeypatch.setattr(Path, 'write_text', lambda self, data, encoding=None, **kw:
                        write_text(self, data, encoding=encoding or 'cp936', **kw))
    monkeypatch.setattr(Path, 'read_text', lambda self, encoding=None, **kw:
                        read_text(self, encoding=encoding or 'cp936', **kw))
    industry.publish_snapshot(value, tmp_path)
    assert industry.load_snapshot(tmp_path)['dataset']['costs'][0]['enterprise_id'] == '合成🙂'
