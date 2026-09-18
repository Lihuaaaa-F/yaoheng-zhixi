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
