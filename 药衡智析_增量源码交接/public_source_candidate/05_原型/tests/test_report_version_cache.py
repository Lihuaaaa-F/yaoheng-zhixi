"""Report-level cache contracts, using the public synthetic dataset only."""
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from pharma import api, knowledge, narrative, worker, reports, context_services
from pharma.jobs import JobStore


@pytest.fixture
def service(tmp_path, monkeypatch):
    store=JobStore(tmp_path/'jobs.sqlite3')
    def forbidden(*args,**kwargs):raise RuntimeError('TEST_DOWNSTREAM_MUST_NOT_RUN')
    monkeypatch.setattr(reports,'render_docx',forbidden)
    monkeypatch.setattr(context_services,'retrieve',forbidden)
    monkeypatch.setattr(api,'store',store)
    monkeypatch.setattr(narrative,'ModelGateway',lambda:SimpleNamespace(
        model='synthetic-model',provider='openai-compatible',base_url='https://synthetic.invalid',
        key='',max_repairs=0))
    return TestClient(api.app),store


def submit(client):
    response=client.post('/api/reports',json={'context_id':'mechanical_demo:synthetic-mechanical',
        'product':'DEMO-01','factory':'示范工厂A','month':'2026-06'})
    assert response.status_code==202,response.text
    return response.json()['job_id']


def mutate(monkeypatch,kind):
    if kind=='validator':monkeypatch.setattr(narrative,'VALIDATOR_VERSION','synthetic-validator-v-next',raising=False)
    elif kind=='parser':monkeypatch.setattr(knowledge,'PARSER_VERSION','synthetic-parser-v-next')
    elif kind=='terminology':monkeypatch.setattr(knowledge,'terminology_hash',lambda:'synthetic-terms-v-next')


@pytest.mark.parametrize('kind',['validator','parser','terminology'])
def test_completed_report_reused_only_when_all_generation_versions_match(service,monkeypatch,kind):
    client,store=service
    first=submit(client);store.update(first,'DEGRADED',{'execution_status':'COMPLETED'})
    assert submit(client)==first
    mutate(monkeypatch,kind)
    second=submit(client)
    assert second!=first
    assert submit(client)==second


@pytest.mark.parametrize('kind',['validator','parser','terminology'])
def test_worker_rejects_changed_version_before_reusing_partial_result(service,monkeypatch,kind):
    client,store=service
    id=submit(client)
    store.update(id,'GENERATING',{'narrative':{'status':'PASS','findings':[]}})
    mutate(monkeypatch,kind)
    worker.process_job(store,store.get(id))
    job=store.get(id)
    assert job['status']=='FAILED'
    assert kind.upper()+'_VERSION_CHANGED_RESUBMIT' in job['error']
    assert not any(row['stage']=='RENDERING_DOCX' for row in store.history(id))


@pytest.mark.parametrize('kind',['validator','parser','terminology'])
def test_worker_rejects_old_unbound_version_contract(service,kind):
    client,store=service
    id=submit(client);job=store.get(id)
    job['input']['versions'].pop(kind,None)
    worker.process_job(store,job)
    assert kind.upper()+'_VERSION_CHANGED_RESUBMIT' in store.get(id)['error']
