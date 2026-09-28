"""Independent assistant connections and credential-safe settings regression tests.

All network responses are in-memory fixtures; no external model call is made.
"""
import json
import os
from pathlib import Path

import httpx
import pytest

from pharma import model_settings, model_registry, narrative


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.setattr(model_settings, 'SETTINGS_PATH', tmp_path / 'model_settings.json')
    monkeypatch.setattr(model_settings, 'KEYS_DIR', tmp_path / 'keys')
    monkeypatch.setattr(narrative, 'RUNTIME', tmp_path)
    monkeypatch.delenv('PHARMA_MODEL_ROUTES', raising=False)
    for route in ('ASSISTANT', 'ANALYSIS', 'EXTRACTION', 'NARRATIVE', 'DECISION'):
        for field in (*model_settings.FIELDS, 'api_key'):
            monkeypatch.delenv('PHARMA_MODEL_' + route + '_' + field.upper(), raising=False)
    return tmp_path


def _save(route='assistant', **extra):
    return model_settings.save_settings({'connections': {route: {
        'model': 'test-model', 'base_url': 'https://assistant.invalid/v1', **extra}}})


def _mock_client(seen):
    def respond(request):
        seen.append(request)
        return httpx.Response(200, json={'model': 'test-model', 'usage': {'total_tokens': 1},
            'choices': [{'message': {'content': '{"ok":true}'}}]})
    return httpx.Client(transport=httpx.MockTransport(respond))


def test_partial_saves_keep_other_routes_and_blank_preserves_key(settings):
    _save('analysis', api_key='analysis-secret')
    _save('assistant', api_key='assistant-secret')
    original = model_settings.resolve('assistant')['key_file']
    result = model_settings.save_settings({'connections': {'assistant': {'model': 'new-model', 'api_key': ''}}})
    assert model_settings.resolve('analysis')['model'] == 'test-model'
    assert model_settings.resolve('assistant')['key_file'] == original
    assert Path(original).read_text() == 'assistant-secret'
    assert 'assistant-secret' not in json.dumps(result)
    assert result['connections']['assistant']['key_file'] == Path(original).name
    # 0600 权限位仅在 POSIX 语义成立；Windows NTFS 用 ACL 表达，st_mode 恒为
    # 通用的读写位（2026-09-24 审查：该断言使 Windows 本地全量必红，改为平台感知）。
    if os.name == 'posix':
        assert (Path(original).stat().st_mode & 0o777) == 0o600
    else:
        assert Path(original).is_file()


def test_clear_key_revokes_reference_without_deleting_file(settings, monkeypatch):
    _save(api_key='old-key')
    key_file = Path(model_settings.resolve('assistant')['key_file'])
    model_settings.save_settings({'connections': {'assistant': {'clear_api_key': True}}})
    monkeypatch.setenv('PHARMA_API_KEY', 'global-secret')
    assert key_file.read_text() == 'old-key'
    assert narrative.ModelGateway.for_route('assistant').key == ''
    assert model_settings.status()['connections']['assistant']['key_set'] is False


def test_assistant_is_independent_from_all_global_configuration(settings, monkeypatch):
    monkeypatch.setenv('PHARMA_API_KEY', 'global-secret')
    monkeypatch.setenv('GLM_API_KEY', 'glm-secret')
    monkeypatch.setenv('PHARMA_MODEL_REASONING_EFFORT', 'high')
    monkeypatch.setenv('PHARMA_MODEL_MAX_TOKENS', '12000')
    monkeypatch.setenv('PHARMA_MODEL_TIMEOUT', '170')
    gateway = narrative.ModelGateway.for_route('assistant')
    assert (gateway.model, gateway.base_url, gateway.key, gateway.reasoning_effort) == ('', '', '', '')
    assert not gateway.configured and not gateway.available
    assert gateway.max_tokens == 8192 and gateway.timeout_seconds == 90
    assert gateway.coding_base_url == ''
    monkeypatch.setenv('PHARMA_MODEL_ASSISTANT_MODEL', 'independent-model')
    monkeypatch.setenv('PHARMA_MODEL_ASSISTANT_BASE_URL', 'https://own.invalid/v1')
    monkeypatch.setenv('PHARMA_MODEL_ASSISTANT_API_KEY', 'own-secret')
    gateway = narrative.ModelGateway.for_route('assistant')
    assert gateway.model == 'independent-model' and gateway.key == 'own-secret'


def test_candidate_key_is_used_without_saving_and_overrides_do_not_collide(settings, monkeypatch):
    _save(api_key='saved-secret')
    before = model_settings.SETTINGS_PATH.read_bytes()
    seen = []
    original = narrative.ModelGateway.for_route
    monkeypatch.setattr(narrative.ModelGateway, 'for_route',
        lambda route, **kwargs: original(route, client=_mock_client(seen), **kwargs))
    result = model_settings.test_connection('assistant', {'model': 'test-model',
        'base_url': 'https://new.invalid/v1', 'api_key': 'candidate-secret',
        'protocol': 'openai', 'temperature': .4, 'top_p': .8,
        'max_tokens': 1024, 'timeout_seconds': 15, 'reasoning_effort': ''})
    assert result['status'] == 'PASS'
    assert seen[0].headers['Authorization'] == 'Bearer candidate-secret'
    payload = json.loads(seen[0].content)
    assert payload['temperature'] == .4 and payload['top_p'] == .8 and payload['max_tokens'] == 1024
    assert 'reasoning_effort' not in payload
    assert model_settings.SETTINGS_PATH.read_bytes() == before
    assert 'candidate-secret' not in json.dumps(result)
    assert all('candidate-secret' not in f.read_text() for f in model_settings.KEYS_DIR.glob('*.key'))


def test_new_destination_does_not_receive_old_key(settings):
    _save(api_key='old-secret')
    for base in ('https://other.invalid/v1', 'https://assistant.invalid/different-tenant'):
        with pytest.raises(ValueError, match='CREDENTIAL_REENTRY_REQUIRED'):
            model_settings.test_connection('assistant', {'base_url': base})
        with pytest.raises(ValueError, match='CREDENTIAL_REENTRY_REQUIRED'):
            model_settings.save_settings({'connections': {'assistant': {'base_url': base}}})


def test_global_endpoint_override_does_not_rebind_saved_key(settings, monkeypatch):
    _save('analysis', api_key='saved-for-original-host')
    monkeypatch.setenv('PHARMA_MODEL_BASE_URL', 'https://different.invalid/v1')
    gateway = narrative.ModelGateway.for_route('analysis')
    assert gateway.key == '' and not gateway.available
    assert gateway.credential_scope['source'] == 'SETTINGS_ENDPOINT_MISMATCH'
    assert gateway.parameter_warnings


def test_local_unauthenticated_endpoint_sends_no_fake_authorization(settings):
    seen = []
    gateway = narrative.ModelGateway.for_route('assistant', model='test-model',
        base_url='http://127.0.0.1:11434/v1', client=_mock_client(seen))
    assert gateway.available and not gateway.key
    gateway.complete('Return JSON', 'test')
    assert 'Authorization' not in seen[0].headers
    assert 'temperature' not in json.loads(seen[0].content)
    required = narrative.ModelGateway.for_route('assistant', model='test-model',
        base_url='http://localhost:1234/v1', auth_mode='required')
    assert not required.available
    with pytest.raises(ValueError, match='MODEL_AUTH_MODE_INVALID'):
        narrative.ModelGateway.for_route('assistant', model='x', base_url='https://remote.invalid', auth_mode='none')


def test_none_auth_cannot_accidentally_send_saved_key(settings):
    seen = []
    gateway = narrative.ModelGateway.for_route('assistant', model='test-model', api_key='do-not-send',
        base_url='http://localhost:11434/v1', auth_mode='none', client=_mock_client(seen))
    gateway.complete('Return JSON', 'test')
    assert not gateway.key and 'Authorization' not in seen[0].headers


def test_assistant_never_retries_or_switches_endpoint(settings):
    seen = []
    def fail(request):
        seen.append(request)
        return httpx.Response(429, json={'error': {'code': '1113'}})
    gateway = narrative.ModelGateway.for_route('assistant', model='glm-5.3', api_key='synthetic',
        base_url='https://open.bigmodel.cn/api/paas/v4',
        client=httpx.Client(transport=httpx.MockTransport(fail)))
    with pytest.raises(httpx.HTTPStatusError):
        gateway.complete('s', 'u')
    assert len(seen) == 1


def test_key_file_paths_and_symlinks_are_rejected_on_save(settings, tmp_path):
    external = tmp_path / 'outside.key'
    external.write_text('not-for-network')
    with pytest.raises(ValueError, match='KEY_FILE_OVERRIDE_RESTRICTED'):
        _save(key_file=str(external))
    model_settings.KEYS_DIR.mkdir()
    try:
        (model_settings.KEYS_DIR / 'linked.key').symlink_to(external)
    except OSError:
        # Windows 需要管理员/开发者模式特权才能建符号链接（WinError 1314）；
        # 符号链接拒绝逻辑由 POSIX CI 覆盖，此处跳过而非误报。
        pytest.skip('当前平台无特权创建符号链接，符号链接拒绝路径由 POSIX CI 覆盖')
    with pytest.raises(ValueError, match='KEY_FILE_OVERRIDE_RESTRICTED'):
        _save(key_file='linked.key')


@pytest.mark.parametrize('field,value', [('max_tokens', 0), ('max_tokens', 1.5),
    ('temperature', -1), ('temperature', float('nan')), ('top_p', 2), ('timeout_seconds', 181)])
def test_invalid_parameters_fail_before_key_write(settings, field, value):
    with pytest.raises(ValueError, match='MODEL_PARAMETER_INVALID'):
        _save(api_key='not-written', **{field: value})
    assert not model_settings.SETTINGS_PATH.exists()
    assert not model_settings.KEYS_DIR.exists()


def test_reasoning_mapping_is_explicit_and_default_sends_nothing():
    assert model_registry.effort_body_params('glm-5.3', 'https://open.bigmodel.cn/api/paas/v4', '') == {}
    assert model_registry.effort_body_params('glm-5.3', 'x', 'max') == {'reasoning_effort': 'max'}
    params, warnings, errors = model_registry.reasoning_parameters('glm-5.3', 'x', 'medium')
    assert params == {'reasoning_effort': 'high'} and warnings and not errors
    assert model_registry.reasoning_parameters('glm-5.3', 'x', 'none')[2]
    assert model_registry.effort_body_params('deepseek-flash', 'https://api.deepseek.com', 'none') == {'thinking': {'type': 'disabled'}}


def test_context_windows_merge_by_exact_model_and_null_revokes(settings):
    _save(model_context_windows={'model-a': 32000, 'model-b': 128000})
    result = model_settings.save_settings({'connections': {'assistant': {
        'model': 'model-b', 'model_context_windows': {'model-a': None, 'model-c': 64000}}}})
    assert result['connections']['assistant']['model_context_windows'] == {'model-b': 128000, 'model-c': 64000}
    assert model_settings.context_window_metadata('assistant', 'model-b') == {
        'model': 'model-b', 'context_window': 128000, 'source': 'user_configured'}
    assert model_settings.context_window_metadata('assistant', 'model-a')['context_window'] is None
    assert model_settings.context_window_metadata('assistant', 'never-configured')['source'] == 'unknown'


def test_context_window_is_not_reused_across_endpoints_or_in_http_payload(settings):
    _save(model_context_windows={'test-model': 64000})
    assert model_settings.context_window_metadata('assistant', 'test-model', 'https://other.invalid/v1')['context_window'] is None
    seen = []
    gateway = narrative.ModelGateway.for_route('assistant', api_key='synthetic', client=_mock_client(seen))
    gateway.complete('Return JSON', 'test')
    assert 'model_context_windows' not in json.loads(seen[0].content)
    assert 'model_context_windows' not in gateway.generation_parameters
    model_settings.save_settings({'connections': {'assistant': {'base_url': 'https://other.invalid/v1'}}})
    assert model_settings.context_window_metadata('assistant', 'test-model')['context_window'] is None


@pytest.mark.parametrize('windows', [None, [], {'': 32000}, {' model': 32000}, {'a' * 161: 32000},
    {'model': True}, {'model': '32000'}, {'model': 32000.5}, {'model': 1023}, {'model': 2000001},
    {str(i): 32000 for i in range(101)}])
def test_invalid_context_window_metadata_is_rejected(settings, windows):
    with pytest.raises(ValueError, match='MODEL_CONTEXT_WINDOWS_INVALID'):
        _save(model_context_windows=windows)
    assert not model_settings.SETTINGS_PATH.exists()


def test_context_window_limit_applies_after_partial_merge(settings):
    _save(model_context_windows={str(i): 32000 for i in range(100)})
    before = model_settings.SETTINGS_PATH.read_bytes()
    with pytest.raises(ValueError, match='MODEL_CONTEXT_WINDOWS_INVALID'):
        model_settings.save_settings({'connections': {'assistant': {'model_context_windows': {'extra': 32000}}}})
    assert model_settings.SETTINGS_PATH.read_bytes() == before
