"""Header states use observable provenance, not a periodic fabricated timestamp."""
import json
import httpx
from pharma import system_status as status


def test_deployment_config_does_not_equate_docker_with_cloud(monkeypatch):
    monkeypatch.delenv('PHARMA_DEPLOYMENT_MODE',raising=False)
    assert status.deployment_status()['mode']=='local'
    monkeypatch.setenv('PHARMA_DEPLOYMENT_MODE','cloud')
    assert status.deployment_status()['mode']=='cloud'


def test_network_probe_has_no_credentials_or_business_payload_and_is_cached(monkeypatch):
    monkeypatch.setenv('PHARMA_NETWORK_PROBE_URL','https://probe.example')
    status._network_cache.clear()
    calls=[]
    def head(url,**kwargs):
        calls.append((url,kwargs))
        return httpx.Response(403)
    monkeypatch.setattr(httpx,'head',head)
    first=status.network_status();second=status.network_status()
    assert first['status']=='reachable' and second['cached']
    assert len(calls)==1 and calls[0][0]=='https://probe.example'
    assert not any(k in calls[0][1] for k in ('headers','auth','json','data'))


def test_network_failure_is_not_claimed_as_universal_offline(monkeypatch):
    monkeypatch.setenv('PHARMA_NETWORK_PROBE_URL','https://failed.example')
    status._network_cache.clear()
    def fail(*args,**kwargs): raise httpx.ConnectError('fixture')
    monkeypatch.setattr(httpx,'head',fail)
    value=status.network_status()
    assert value['status']=='unreachable' and '不据此断言' in value['detail']
    for target in ('','https://[','https://key:secret@example.test','https://example.test?api_key=x'):
        monkeypatch.setenv('PHARMA_NETWORK_PROBE_URL',target)
        assert status.network_status()['status']=='unverified'


def test_data_updated_time_is_the_published_snapshot_time(tmp_path,monkeypatch):
    from pharma import ingestion,industry
    monkeypatch.setattr(ingestion,'SNAPSHOTS',tmp_path)
    monkeypatch.setattr(industry,'catalog',lambda _: {'months':['2026-06']})
    (tmp_path/'current.json').write_text(json.dumps({'created_at':'2026-09-20T12:00:00+00:00'}))
    first=status.data_status('pharmaceutical:competition')
    assert first==status.data_status('pharmaceutical:competition')
    assert first['updated_at']=='2026-09-20T12:00:00+00:00'
    assert first['latest_period']=='2026-06'
