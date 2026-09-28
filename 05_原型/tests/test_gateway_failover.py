"""端点回退合同（用户2026-09-18授权暂定政策）：主端点先消耗余额/资源包，
错误码1113（额度耗尽）自动切换 Coding Plan 端点；充值后自动回到主端点。"""
import json
import sqlite3
import httpx
import pytest
from pharma.narrative import ModelGateway

PRIMARY = 'https://open.bigmodel.cn/api/paas/v4'
CODING = 'https://open.bigmodel.cn/api/coding/paas/v4'


def _response(status, payload):
    return httpx.Response(status, json=payload, request=httpx.Request('POST', 'urn:test'))


def _ok():
    return _response(200, {'model': 'glm-5.3-flash', 'usage': {'total_tokens': 1},
                           'choices': [{'message': {'content': '{"explanations":[]}'}}]})


def _quota():
    return _response(429, {'error': {'code': '1113', 'message': '余额不足或无可用资源包'}})


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.urls = []

    def post(self, url, **kwargs):
        self.urls.append(url)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture(autouse=True)
def _fake_key(monkeypatch):
    # conftest 会清空密钥环境；本文件只测端点策略，统一注入假 key
    monkeypatch.setenv('PHARMA_API_KEY', 'unit-test-key')


def test_quota_1113_falls_back_to_coding_and_records_endpoint(tmp_path):
    client = FakeClient([_quota(), _ok()])
    gateway = ModelGateway(client=client, runtime=tmp_path, base_url=PRIMARY)
    text, _usage, identity = gateway.complete('s', 'u')
    assert text == '{"explanations":[]}'
    # 主端点先试（消耗余额），1113 后同一次调用切换 Coding Plan 端点
    assert client.urls == [PRIMARY + '/chat/completions', CODING + '/chat/completions']
    assert identity['endpoint'] == CODING + '/chat/completions' and identity['identity_status'] == 'VERIFIED_EXACT'
    with sqlite3.connect(tmp_path / 'model_gateway.sqlite3') as db:
        row = db.execute('SELECT status, endpoint FROM calls').fetchone()
    assert row == ('PASS', CODING + '/chat/completions')


def test_quota_1113_without_fallback_fails_immediately(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_MODEL_CODING_BASE_URL', '')
    client = FakeClient([_quota(), _quota()])
    gateway = ModelGateway(client=client, runtime=tmp_path, base_url=PRIMARY)
    with pytest.raises(httpx.HTTPStatusError):
        gateway.complete('s', 'u')
    # 无备用端点时不退避（等待无法恢复余额）、不重试
    assert len(client.urls) == 1


def test_rate_limit_without_quota_code_still_retries_same_endpoint(tmp_path, monkeypatch):
    import pharma.narrative as narrative
    monkeypatch.setattr(narrative.time, 'sleep', lambda *_: None)
    plain_429 = _response(429, {'error': {'code': '1302', 'message': '并发上限'}})
    client = FakeClient([plain_429, _ok()])
    gateway = ModelGateway(client=client, runtime=tmp_path, base_url=PRIMARY)
    text, _usage, identity = gateway.complete('s', 'u')
    assert text == '{"explanations":[]}'
    # 非余额类限流留在主端点退避重试，不切 Coding Plan
    assert client.urls == [PRIMARY + '/chat/completions'] * 2
    assert identity['endpoint'] == PRIMARY + '/chat/completions'


def test_non_retryable_client_error_never_switches(tmp_path):
    client = FakeClient([_response(400, {'error': {'code': '1210', 'message': '参数错误'}})])
    gateway = ModelGateway(client=client, runtime=tmp_path, base_url=PRIMARY)
    with pytest.raises(httpx.HTTPStatusError):
        gateway.complete('s', 'u')
    assert len(client.urls) == 1


def test_primary_success_never_touches_coding(tmp_path):
    client = FakeClient([_ok()])
    gateway = ModelGateway(client=client, runtime=tmp_path, base_url=PRIMARY)
    gateway.complete('s', 'u')
    assert client.urls == [PRIMARY + '/chat/completions']

@pytest.mark.parametrize('provider,base_url', [('openai', 'https://other.invalid/v1'),
                                              ('anthropic', PRIMARY)])
def test_other_provider_or_protocol_never_uses_zhipu_fallback(tmp_path, provider, base_url):
    client = FakeClient([_quota(), _ok()])
    gateway = ModelGateway(client=client, runtime=tmp_path, provider=provider, base_url=base_url)
    with pytest.raises(httpx.HTTPStatusError):
        gateway.complete('s', 'u')
    assert len(client.urls) == 1


def test_coding_override_cannot_receive_primary_credential(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_MODEL_CODING_BASE_URL', 'https://other.invalid/v1')
    client = FakeClient([_quota(), _ok()])
    gateway = ModelGateway(client=client, runtime=tmp_path, base_url=PRIMARY)
    with pytest.raises(httpx.HTTPStatusError):
        gateway.complete('s', 'u')
    assert len(client.urls) == 1


def test_failed_attempt_is_retained_after_success_without_secrets(tmp_path):
    client = FakeClient([_quota(), _ok()])
    gateway = ModelGateway(client=client, runtime=tmp_path, base_url=PRIMARY)
    gateway.complete('s', 'u')
    with sqlite3.connect(gateway.dbpath) as db:
        attempts = db.execute('SELECT endpoint,status,http_status,error FROM call_attempts ORDER BY id').fetchall()
    assert attempts[0][1:] == ('FAILED', 429, 'HTTPStatusError:429:1113')
    assert attempts[1][1] == 'PASS'
    assert 'unit-test-key' not in repr(attempts)


def test_route_cannot_borrow_other_supplier_credential(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_MODEL_ROUTES', json.dumps({'decision': {'base_url': 'https://other.invalid/v1'}}))
    gateway = ModelGateway.for_route('decision', runtime=tmp_path)
    assert gateway.key == ''
    assert gateway.credential_scope['source'] == 'ROUTE_KEY_REQUIRED'
    own_key = tmp_path / 'fake-key'
    own_key.write_text('route-fixture-key')
    monkeypatch.setenv('PHARMA_MODEL_ROUTES', json.dumps({'decision': {
        'base_url': 'https://other.invalid/v1', 'key_file': str(own_key)}}))
    assert ModelGateway.for_route('decision', runtime=tmp_path).key == 'route-fixture-key'
    own_key.unlink()
    assert ModelGateway.for_route('decision', runtime=tmp_path).key == ''


def test_glm_environment_key_is_supplier_scoped(tmp_path, monkeypatch):
    monkeypatch.delenv('PHARMA_API_KEY')
    monkeypatch.setenv('GLM_API_KEY', 'fake-glm-key')
    assert ModelGateway(runtime=tmp_path, base_url=PRIMARY).key == 'fake-glm-key'
    assert ModelGateway(runtime=tmp_path, base_url='https://other.invalid/v1').key == ''
    assert ModelGateway(runtime=tmp_path, base_url=PRIMARY, provider='anthropic').key == ''


def test_gateway_does_not_follow_redirect_or_log_query_secret(tmp_path):
    seen = []
    def transport(request):
        seen.append(str(request.url))
        return httpx.Response(307, headers={'location': 'https://other.invalid/v1'})
    gateway = ModelGateway(runtime=tmp_path, base_url=PRIMARY + '?token=fixture-secret',
        client=httpx.Client(transport=httpx.MockTransport(transport), follow_redirects=True))
    with pytest.raises(httpx.HTTPStatusError):
        gateway.complete('s', 'u')
    assert len(seen) == 1
    with sqlite3.connect(gateway.dbpath) as db:
        attempts = db.execute('SELECT endpoint,status,http_status,error FROM call_attempts').fetchall()
        calls = db.execute('SELECT endpoint,error FROM calls').fetchall()
    assert attempts[0][1:] == ('FAILED', 307, 'HTTPStatusError:307')
    assert 'fixture-secret' not in repr(attempts + calls)


def test_network_failure_has_attempt_record(tmp_path):
    gateway = ModelGateway(runtime=tmp_path, client=FakeClient([httpx.ConnectError('unit-test-key')]))
    with pytest.raises(httpx.ConnectError):
        gateway.complete('s', 'u')
    with sqlite3.connect(gateway.dbpath) as db:
        assert db.execute('SELECT status,error FROM call_attempts').fetchall() == [('FAILED', 'ConnectError')]
