"""传输层性能合同（2026-09-23 审查 SSE-3/SSE-15）：API JSON 与前端资产必须压缩/可缓存。

独立合成验证：不依赖赛题数据内容，仅断言响应头合同。
"""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from pharma import api

APP = Path(api.APP)
client = TestClient(api.app)


def test_api_json_responses_are_gzipped_above_minimum_size():
    r = client.get('/api/industry/catalog', headers={'Accept-Encoding': 'gzip'})
    assert r.status_code == 200
    assert r.headers.get('content-encoding') == 'gzip'
    assert r.json()['contexts']


@pytest.mark.skipif(not (APP / 'frontend/dist/assets').is_dir(), reason='CI 无前端构建产物，静态托管未挂载')
def test_fingerprinted_assets_are_immutable_cached():
    assets = sorted((APP / 'frontend/dist/assets').glob('*.js'))
    name = 'assets/' + assets[0].name
    r = client.get('/' + name)
    assert r.status_code == 200
    cc = r.headers.get('cache-control', '')
    assert 'immutable' in cc and 'max-age=31536000' in cc


@pytest.mark.skipif(not (APP / 'frontend/dist').is_dir(), reason='CI 无前端构建产物，静态托管未挂载')
def test_index_html_is_not_immutable_cached():
    r = client.get('/')
    assert r.status_code == 200
    cc = r.headers.get('cache-control', '')
    assert 'immutable' not in cc
