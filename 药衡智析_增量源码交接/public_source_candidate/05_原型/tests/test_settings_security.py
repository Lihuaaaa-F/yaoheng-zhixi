# -*- coding: utf-8 -*-
"""设置端点安全收紧回归（2026-09-21 修复 #4）。

- 请求参数携带的 key_file 只允许 RUNTIME/keys/ 内的文件名（防任意文件读取外发）；
- base_url 覆盖必须 https，或回环/容器内宿主机地址的明文 http；
- PHARMA_API_TOKEN 设置后 /api/* 需要 X-API-Token，未设置时行为不变。
"""
import pytest
from pharma import model_settings


def test_override_key_file_rejects_paths_outside_keys_dir():
    with pytest.raises(ValueError, match='KEY_FILE_OVERRIDE_RESTRICTED'):
        model_settings._sanitize_overrides({'key_file': 'C:/Users/secret.txt'})
    with pytest.raises(ValueError, match='KEY_FILE_OVERRIDE_RESTRICTED'):
        model_settings._sanitize_overrides({'key_file': '../../etc/passwd'})
    with pytest.raises(ValueError, match='KEY_FILE_OVERRIDE_RESTRICTED'):
        model_settings._sanitize_overrides({'key_file': 'keys/narrative.key'})


def test_override_key_file_accepts_keys_dir_basename():
    cleaned = model_settings._sanitize_overrides({'key_file': 'narrative.key'})
    assert cleaned['key_file'].endswith('narrative.key')
    assert model_settings.KEYS_DIR.as_posix() in cleaned['key_file'].replace('\\', '/') or \
        str(model_settings.KEYS_DIR) in cleaned['key_file']


def test_override_base_url_https_or_loopback_only():
    with pytest.raises(ValueError, match='BASE_URL_OVERRIDE_INVALID'):
        model_settings._sanitize_overrides({'base_url': 'http://evil.example.com/v4'})
    ok_https = model_settings._sanitize_overrides({'base_url': 'https://api.example.com/v4'})
    assert ok_https['base_url'].startswith('https://')
    ok_loopback = model_settings._sanitize_overrides({'base_url': 'http://127.0.0.1:8000/v4'})
    assert ok_loopback['base_url'].startswith('http://127.0.0.1')
    ok_docker_host = model_settings._sanitize_overrides({'base_url': 'http://host.docker.internal:3000/v4'})
    assert 'host.docker.internal' in ok_docker_host['base_url']


def test_saved_settings_reject_plaintext_external_base_url():
    errors = model_settings._validate_connection('analysis', {'base_url': 'http://api.example.com/v4', 'protocol': 'openai'})
    assert any('https' in e for e in errors)
    errors_ok = model_settings._validate_connection('analysis', {'base_url': 'http://host.docker.internal:3000/v4', 'protocol': 'openai'})
    assert errors_ok == []


def test_api_token_guard_blocks_and_allows(monkeypatch):
    from fastapi.testclient import TestClient
    from pharma import api as api_module
    monkeypatch.setenv('PHARMA_API_TOKEN', 'demo-token')
    client = TestClient(api_module.app)
    unauthorized = client.get('/api/catalog')
    assert unauthorized.status_code == 401
    authorized = client.get('/api/catalog', headers={'X-API-Token': 'demo-token'})
    assert authorized.status_code == 200


def test_api_token_unset_keeps_open_behavior(monkeypatch):
    from fastapi.testclient import TestClient
    from pharma import api as api_module
    monkeypatch.delenv('PHARMA_API_TOKEN', raising=False)
    client = TestClient(api_module.app)
    assert client.get('/api/catalog').status_code == 200
