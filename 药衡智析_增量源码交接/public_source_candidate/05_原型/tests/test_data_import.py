"""数据中心导入向导与模型设置的产品合同回归。"""
import json
import os
from pathlib import Path

import pytest

from pharma import data_import, model_settings


@pytest.fixture()
def isolated_runtime(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_RUNTIME_DIR', str(tmp_path))
    import importlib
    import pharma.config as config
    importlib.reload(config)
    importlib.reload(data_import)
    importlib.reload(model_settings)
    return tmp_path


CSV = ('工厂,产品名称,核算期间,完工数量,直接材料,直接人工,制造费用\n'
       '示范工厂F,产品Z,2026年1月,500,15000,6000,4000\n'
       '示范工厂F,产品Z,2026年2月,520,15600,6100,4050\n'
       '示范工厂F,产品Z,2025年1月,480,14000,5800,3900\n')


def _mapping(headers):
    preset = {'工厂': 'factory_id', '产品名称': 'product_id', '核算期间': 'period',
              '完工数量': 'quantity', '直接材料': 'element:material',
              '直接人工': 'element:labor', '制造费用': 'element:overhead'}
    return {h: preset.get(h, '') for h in headers}


def test_wide_table_upload_validate_capabilities_and_publish(isolated_runtime):
    record = data_import.create_upload('business', '成本宽表F.csv', CSV.encode('utf-8'))
    assert record['encoding'].startswith('utf-8')
    mapping = _mapping(record['meta']['preview']['headers'])
    validation = data_import.validate_business(record, mapping, {})
    assert validation['status'] == 'VALID'
    caps = {c['capability']: c['available'] for c in validation['capabilities']}
    assert caps['unit_cost_analysis'] and caps['yoy_comparison']          # 有产量、有去年同期
    assert not caps['budget_comparison'] and not caps['price_volume_decomposition']
    # 真实注册链路（隔离运行时）：企业配置经完整合同校验后登记
    result = data_import.publish_business(record, mapping, {}, '示范企业F', 'pharmaceutical', '件')
    assert result['context_id'].startswith('pharmaceutical:imp-')
    enterprise_dir = Path(data_import.IMPORTS_ROOT) / 'enterprises' / result['enterprise_id']
    dataset = json.loads((enterprise_dir / 'facts.json').read_text(encoding='utf-8'))
    assert len(dataset['quantities']) == 3 and len(dataset['costs']) == 9  # 产量独立、要素长表


def test_error_rows_point_to_file_row_and_reason(isolated_runtime):
    broken = CSV.replace('520', 'abc')  # 产量列非法值
    record = data_import.create_upload('business', 'b.csv', broken.encode('utf-8'))
    validation = data_import.validate_business(record, _mapping(record['meta']['preview']['headers']), {})
    assert validation['status'] == 'INVALID'
    row_errors = [e for e in validation['errors'] if '产量' in e['reason']]
    assert row_errors and row_errors[0]['row'] == 3 and row_errors[0]['file'] == 'b.csv'


def test_quantity_conflict_detected(isolated_runtime):
    conflict = ('工厂,产品名称,核算期间,完工数量,直接材料\n'
                'F1,P1,2026-01,100,3000\nF1,P1,2026-01,120,3600\n')
    record = data_import.create_upload('business', 'c.csv', conflict.encode('utf-8'))
    mapping = _mapping(record['meta']['preview']['headers'])
    validation = data_import.validate_business(record, mapping, {})
    assert any('冲突产量' in e['reason'] for e in validation['errors'])


def test_mapping_plan_reuse_by_header_fingerprint(isolated_runtime):
    record = data_import.create_upload('business', 'a.csv', CSV.encode('utf-8'))
    headers = record['meta']['preview']['headers']
    data_import.save_mapping(headers, _mapping(headers), '标准宽表')
    suggested = data_import.suggest_mapping(headers)
    assert suggested.get('_saved_name') == '标准宽表'
    assert suggested['完工数量'] == 'quantity'


def test_model_settings_save_resolve_and_no_secret_echo(isolated_runtime):
    result = model_settings.save_settings({'connections': {
        'narrative': {'model': 'm-x', 'base_url': 'https://api.invalid/v4', 'protocol': 'openai',
                      'api_key': 'sk-SECRET-VALUE'}}})
    conn = result['connections']['narrative']
    assert conn['configured'] and conn['key_set']
    assert 'sk-SECRET-VALUE' not in json.dumps(result)            # 状态不回显密钥
    assert 'sk-SECRET-VALUE' not in (isolated_runtime / 'model_settings.json').read_text(encoding='utf-8')
    resolved = model_settings.resolve('narrative')
    assert resolved['model'] == 'm-x' and resolved.get('key_file')
    assert Path(resolved['key_file']).read_text(encoding='utf-8') == 'sk-SECRET-VALUE'


def test_model_settings_rejects_inline_credentials_in_url(isolated_runtime):
    with pytest.raises(ValueError, match='INVALID_SETTINGS_SECTION'):
        model_settings.save_settings({'connections': {
            'narrative': {'base_url': 'https://user:pass@api.invalid/v4'}}})
