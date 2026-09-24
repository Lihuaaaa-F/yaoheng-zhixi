"""Synthetic regressions for independently reproduced delivery audit failures."""
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from pharma import knowledge, model_settings, narrative


def _metrics():
    return {'materials': {'metric_id': 'materials', 'label': '材料单位成本',
                          'display_value': '12.49', 'unit': '元/盒'}}


@pytest.mark.parametrize('text', [
    '人工总成本为12.5元，需核对人工工时记录',
    '基期材料单位成本为12.5元/盒，需核查生产记录',
    '人工单位成本为12.5元/盒，需核对人工工时记录',
    '材料单位成本为12.5元/吨，需核对计量记录',
])
def test_rounded_values_cannot_change_unit_subject_or_period(text):
    stripped, bindings = narrative._rounded_metric_bindings(text, _metrics())
    assert not bindings and '12.5' in stripped


def test_legitimate_current_rounded_unit_cost_still_binds():
    stripped, bindings = narrative._rounded_metric_bindings('本期材料单位成本为12.5元/盒，需核查记录', _metrics())
    assert len(bindings) == 1 and '12.5' not in stripped


def test_percent_binding_cannot_change_unit_basis_to_total_basis():
    metrics = {'materials_unit_mom': {'metric_id': 'materials_unit_mom', 'label': '材料单位成本环比',
                                      'display_value': '-15.215', 'unit': '%'}}
    assert not narrative._rounded_metric_bindings('材料总成本下降15.2%', metrics)[1]
    assert narrative._rounded_metric_bindings('材料单位成本下降15.2%', metrics)[1]


@pytest.mark.parametrize('quote', ['设备温度稳定……99%', '设备温度稳定……下降', '99%……设备温度稳定'])
def test_short_fabricated_ellipsis_fragment_cannot_disappear(quote):
    assert not narrative._quote_supported(quote, '设备温度稳定，提取收率尚待核查。')


def test_real_ellipsis_quote_remains_supported():
    assert narrative._quote_supported('设备温度稳定……提取收率尚待核查', '设备温度稳定，说明文字；提取收率尚待核查。')


def _hypothesis(text):
    return {'claim_type': 'hypothesis', 'section': 'materials', 'text_template': text,
            'metric_refs': ['materials'], 'evidence_refs': ['e1'],
            'evidence_quotes': {'e1': '设备老化可能影响提取收率'}, 'hypothesis': True,
            'missing_evidence': ['对应批次生产记录']}


def test_causal_certainty_cannot_be_laundered_by_later_uncertainty():
    evidence = [{'evidence_id': 'e1', 'text': '设备老化可能影响提取收率', 'location': '行1', 'scope': 'general'}]
    with pytest.raises(ValueError, match='causality'):
        narrative.validate_findings([_hypothesis('设备老化是材料成本上升的原因，可能还需核查生产记录。')], {'metrics': _metrics()}, evidence)


def test_qualified_causal_chain_remains_accepted():
    narrative.assert_uncertain_causality('设备老化可能影响提取收率，从而导致材料成本波动。')
    with pytest.raises(ValueError, match='causality'):
        narrative.assert_uncertain_causality('设备老化可能影响提取收率。采购涨价导致材料成本上升。')


def test_explicitly_excluded_document_cannot_be_rescued(monkeypatch):
    evidence = {'evidence_id': 'e1', 'text': '设备老化可能影响提取收率', 'location': '行1', 'scope': 'general'}
    monkeypatch.setattr(knowledge.Knowledge, 'evidence_in_library', classmethod(lambda cls, ref, context=None: evidence))
    with pytest.raises(ValueError, match='excluded'):
        narrative.validate_findings([_hypothesis('设备老化可能影响提取收率。')], {'metrics': _metrics()}, [],
                                    excluded_evidence=[{'evidence_id': 'e1', 'reasons': ['文档版本冲突']}])


def test_rescued_evidence_contains_traceable_source(monkeypatch):
    evidence = {'evidence_id': 'e1', 'text': '设备老化可能影响提取收率', 'location': '行1', 'source': 'synthetic.txt', 'scope': 'general'}
    monkeypatch.setattr(knowledge.Knowledge, 'evidence_in_library', classmethod(lambda cls, ref, context=None: evidence))
    result = narrative.validate_findings([_hypothesis('设备老化可能影响提取收率。')], {'metrics': _metrics()}, [])[0]
    assert result['rescued_evidence'][0]['source'] == 'synthetic.txt'
    assert result['rescued_evidence'][0]['text'] == evidence['text']


def test_rescued_source_merge_preserves_retrieval_status_and_inputs():
    retrieved = {'mode': 'hybrid', 'status': 'DEGRADED', 'reason': 'VECTOR_DISABLED',
                 'retrieval_status': 'DEGRADED', 'evidence': [{'evidence_id': 'e1', 'text': 'retrieved'}]}
    generated = {'findings': [{'evidence_refs': ['e1', 'e2'], 'evidence_rescued': ['e2'],
                              'rescued_evidence': [{'evidence_id': 'e2', 'text': 'verified original'}]}]}
    result = narrative.merge_rescued_evidence(retrieved, generated)
    assert [row['evidence_id'] for row in result['evidence']] == ['e1', 'e2']
    assert result['status'] == result['retrieval_status'] == 'DEGRADED'
    assert result['reason'] == 'VECTOR_DISABLED' and result['mode'] == 'hybrid'
    result['evidence'][0]['text'] = 'modified'
    result['evidence'][1]['text'] = 'modified'
    assert retrieved['evidence'][0]['text'] == 'retrieved'
    assert generated['findings'][0]['rescued_evidence'][0]['text'] == 'verified original'
    assert len(narrative.merge_rescued_evidence(result, generated)['evidence']) == 2


@pytest.mark.parametrize('url,expected', [
    ('https://[2001:4860:4860::8888]/v1', False),
    ('https://[fd00::1]/v1', True),
    ('https://8.8.8.8/v1', False),
    ('http://127.0.0.1:11434/v1', True),
])
def test_intranet_ipv6_classification(url, expected):
    assert model_settings._intranet_host(url) is expected


def test_isolation_keeps_settings_readable_and_can_switch_to_local(tmp_path, monkeypatch):
    monkeypatch.setattr(narrative, 'RUNTIME', tmp_path)
    model_settings.save_network_isolation(True)
    result = model_settings.status()
    assert result['connections']['analysis']['available'] is False
    monkeypatch.delenv('PHARMA_MODEL_BASE_URL', raising=False)
    monkeypatch.delenv('PHARMA_MODEL', raising=False)
    result = model_settings.save_settings({'connections': {'analysis': {
        'model': 'local-model', 'base_url': 'http://127.0.0.1:11434/v1', 'auth_mode': 'none'}}})
    assert result['connections']['analysis']['available'] is True


def test_isolation_toggle_blocks_existing_gateway_before_network(tmp_path):
    requests = []
    def response(request):
        requests.append(request)
        return httpx.Response(200, json={'model': 'synthetic-model', 'choices': [{'message': {'content': '{}'}}]})
    gateway = narrative.ModelGateway(runtime=tmp_path, api_key='synthetic-test-key',
                                    base_url='https://external.invalid/v1', model='synthetic-model',
                                    client=httpx.Client(transport=httpx.MockTransport(response)))
    model_settings.save_network_isolation(True)
    with pytest.raises(RuntimeError, match='NETWORK_ISOLATION_BLOCKED'):
        gateway.complete('synthetic system', 'synthetic private input')
    assert requests == []


def test_gateway_does_not_inherit_environment_proxy(tmp_path, monkeypatch):
    seen = {}
    original = httpx.Client
    def client(**kwargs):
        seen.update(kwargs)
        return original(transport=httpx.MockTransport(lambda request: httpx.Response(200)), **kwargs)
    monkeypatch.setattr(narrative.httpx, 'Client', client)
    narrative.ModelGateway(runtime=tmp_path, base_url='http://127.0.0.1:11434/v1', model='synthetic-model')
    assert seen.get('trust_env') is False


def test_intranet_name_must_resolve_to_private_addresses(monkeypatch):
    import socket
    model_settings.save_network_isolation(True)
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *args, **kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))])
    with pytest.raises(RuntimeError, match='NETWORK_ISOLATION_BLOCKED'):
        model_settings.assert_network_allowed('https://intranet.lan/v1')


def test_library_rescue_uses_same_scoped_index_as_retrieval(tmp_path, monkeypatch):
    from pharma import context_services
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'synthetic.txt').write_text('合成企业的设备运行记录需与材料投入记录一起复核。')
    instance = knowledge.Knowledge(root=tmp_path, source_dir=source, vector_enabled=False)
    instance.build()
    found = instance.search('设备', mode='bm25')['evidence'][0]
    contexts = []
    monkeypatch.setattr(context_services, 'knowledge_for_context', lambda context: contexts.append(context) or instance)
    context = {'industry_id': 'generic_manufacturing', 'enterprise_id': 'synthetic-enterprise'}
    rescued = knowledge.Knowledge.evidence_in_library(found['evidence_id'], context=context)
    assert contexts == [context] and rescued['text'] == found['text']
    rescued['text'] = 'must not mutate cache'
    assert knowledge.Knowledge.evidence_in_library(found['evidence_id'], context=context)['text'] == found['text']


@pytest.mark.parametrize('relative', ['model_quantized.onnx', 'onnx/model_quantized.onnx', 'model.onnx'])
def test_vector_loader_honours_paths_supported_by_settings(tmp_path, monkeypatch, relative):
    import onnxruntime
    from tokenizers import Tokenizer
    model = tmp_path / relative
    model.parent.mkdir(parents=True, exist_ok=True)
    model.write_bytes(b'synthetic-onnx-path-fixture')
    (tmp_path / 'tokenizer.json').write_text('{}')
    loaded = []
    disabled = []
    monkeypatch.setattr(onnxruntime, 'disable_telemetry_events', lambda: disabled.append(True))
    def create_session(path, **kwargs):
        assert disabled, 'ONNX telemetry must be disabled before any session'
        loaded.append(path)
        return object()
    monkeypatch.setattr(onnxruntime, 'InferenceSession', create_session)
    monkeypatch.setattr(Tokenizer, 'from_file', lambda path: SimpleNamespace(enable_padding=lambda **kwargs: None, enable_truncation=lambda **kwargs: None))
    knowledge.CpuEmbedding(tmp_path)
    assert Path(loaded[0]) == model


def test_vector_dimension_probe_disables_telemetry_before_session(tmp_path, monkeypatch):
    import onnxruntime
    (tmp_path / 'model.onnx').write_bytes(b'synthetic-onnx')
    monkeypatch.setattr(model_settings, 'RUNTIME', tmp_path)
    calls = []
    monkeypatch.setattr(onnxruntime, 'disable_telemetry_events', lambda: calls.append('disable'))
    def create_session(*args, **kwargs):
        assert calls == ['disable']
        calls.append('session')
        return SimpleNamespace(get_outputs=lambda: [SimpleNamespace(shape=[1, 7])])
    monkeypatch.setattr(onnxruntime, 'InferenceSession', create_session)
    assert model_settings._probe_dimension_cached(tmp_path) == 7
    assert calls == ['disable', 'session']


def _failed_vector_index(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'synthetic.txt').write_text('合成设备记录用于独立检验向量中断时的词法检索降级，不代表真实语义模型。')
    instance = knowledge.Knowledge(root=tmp_path, source_dir=source)
    attempts = []
    def unavailable():
        attempts.append(True)
        raise RuntimeError('SYNTHETIC_INTERRUPTED_EMBEDDING')
    monkeypatch.setattr(instance, '_model', unavailable)
    assert instance.build()['status'] == 'DEGRADED'
    return instance, attempts


def test_explicit_rebuild_retries_failed_vector_index_without_changed_sources(tmp_path, monkeypatch):
    instance, attempts = _failed_vector_index(tmp_path, monkeypatch)
    assert instance.build()['status'] == 'DEGRADED'
    assert len(attempts) == 2


@pytest.mark.parametrize('mode', ['hybrid', 'vector'])
def test_incomplete_vector_build_cannot_be_reported_as_pass(tmp_path, monkeypatch, mode):
    instance, _ = _failed_vector_index(tmp_path, monkeypatch)
    # Only an execution-control fixture: it supplies no semantic embeddings and
    # must never be used as a real retrieval-quality acceptance result.
    calls = []
    class EmptyPartialCollection:
        def query(self, **kwargs):
            calls.append(kwargs)
            return {'ids': [[]]}
    monkeypatch.setattr(instance, '_model', lambda: SimpleNamespace(encode=lambda *args, **kwargs: [[]]))
    instance._collection = (instance.version, EmptyPartialCollection())
    result = instance.search('设备记录', mode=mode)
    assert result['status'] == 'DEGRADED'
    assert result['reason'].startswith('VECTOR_INDEX_INCOMPLETE')
    assert calls == []
    assert bool(result['evidence']) is (mode == 'hybrid')
    lexical = instance.search('设备记录', mode='bm25')
    assert lexical['status'] == 'PASS' and lexical['evidence']


def test_explicit_root_does_not_use_another_projects_vector_settings(tmp_path, monkeypatch):
    from pharma import model_settings
    from pharma.knowledge import Knowledge
    monkeypatch.delenv('PHARMA_EMBEDDING_DIR', raising=False)
    foreign = tmp_path / 'another-project-model'
    monkeypatch.setattr(model_settings, 'embedding_dir', lambda: foreign)
    isolated = tmp_path / 'isolated-project'
    kb = Knowledge(root=isolated)
    assert kb.model_dir == isolated / '05_原型/.runtime' / model_settings.DEFAULT_EMBEDDING_SUBDIR
