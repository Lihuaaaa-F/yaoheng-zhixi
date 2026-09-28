"""健康检查不能被并发写入或损坏的心跳文件打断。"""
import time
import pytest
from fastapi.testclient import TestClient
import pharma.api as api

@pytest.mark.parametrize('value', ['', 'not-a-timestamp', 'nan', 'inf'])
def test_invalid_worker_heartbeat_is_unavailable_not_http_error(tmp_path, monkeypatch, value):
    monkeypatch.setattr(api, 'RUNTIME', tmp_path)
    (tmp_path / 'worker.heartbeat').write_text(value)
    response = TestClient(api.app).get('/health')
    assert response.status_code == 200
    assert response.json()['worker'] == {'alive': False, 'heartbeat_age_seconds': None}


def test_fresh_worker_heartbeat_remains_available(tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'RUNTIME', tmp_path)
    (tmp_path / 'worker.heartbeat').write_text(str(time.time()))
    response = TestClient(api.app).get('/health')
    assert response.status_code == 200
    assert response.json()['worker']['alive'] is True
