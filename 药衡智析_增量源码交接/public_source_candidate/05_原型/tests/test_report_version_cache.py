"""Report-level cache contracts, using the public synthetic dataset only."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from pharma import api, knowledge, narrative, worker, reports, context_services
from pharma.jobs import JobStore


@pytest.fixture
def service(tmp_path, monkeypatch):
    store=JobStore(tmp_path/'jobs.sqlite3')
    # 2026-09-22：测试产物根必须隔离——enqueue 去重与 store.artifact 都按
    # jobs.ARTIFACTS 判根；不隔离时桩文件会落进真实 07_交付/业务报告。
    from pharma import jobs
    monkeypatch.setattr(jobs,'ARTIFACTS',tmp_path/'artifacts')
    def forbidden(*args,**kwargs):raise RuntimeError('TEST_DOWNSTREAM_MUST_NOT_RUN')
    monkeypatch.setattr(reports,'render_docx',forbidden)
    monkeypatch.setattr(context_services,'retrieve',forbidden)
    monkeypatch.setattr(api,'store',store)
    class GatewayStub:
        # generate()/版本指纹现在统一经 for_route('narrative') 取网关（fix4），
        # 桩必须同时支持直接构造与路由构造两种入口。
        model='synthetic-model';provider='openai-compatible';base_url='https://synthetic.invalid'
        key='';max_repairs=0
        def __init__(self,*args,**kwargs):pass
        @classmethod
        def for_route(cls,route,**kwargs):return cls()
    monkeypatch.setattr(narrative,'ModelGateway',GatewayStub)
    return TestClient(api.app),store


def submit(client):
    response=client.post('/api/reports',json={'context_id':'mechanical_demo:synthetic-mechanical',
        'product':'DEMO-01','factory':'示范工厂A','month':'2026-06'})
    assert response.status_code==202,response.text
    return response.json()['job_id']


def mutate(monkeypatch,kind):
    if kind=='retrieval_policy':monkeypatch.setattr(context_services,'retrieval_policy_version',lambda context:'synthetic-policy-v-next')
    elif kind=='validator':monkeypatch.setattr(narrative,'VALIDATOR_VERSION','synthetic-validator-v-next',raising=False)
    elif kind=='parser':monkeypatch.setattr(knowledge,'PARSER_VERSION','synthetic-parser-v-next')
    elif kind=='terminology':monkeypatch.setattr(knowledge,'terminology_hash',lambda:'synthetic-terms-v-next')


@pytest.mark.parametrize('kind',['validator','parser','terminology','retrieval_policy'])
def test_completed_report_reused_only_when_all_generation_versions_match(service,monkeypatch,kind):
    client,store=service
    first=submit(client);complete_with_artifacts(store,first)
    assert submit(client)==first
    mutate(monkeypatch,kind)
    second=submit(client)
    assert second!=first
    assert submit(client)==second


@pytest.mark.parametrize('kind',['validator','parser','terminology','retrieval_policy'])
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


@pytest.mark.parametrize('kind',['validator','parser','terminology','retrieval_policy'])
def test_worker_rejects_old_unbound_version_contract(service,kind):
    client,store=service
    id=submit(client);job=store.get(id)
    job['input']['versions'].pop(kind,None)
    worker.process_job(store,job)
    assert kind.upper()+'_VERSION_CHANGED_RESUBMIT' in store.get(id)['error']


def test_api_can_enqueue_from_archive_without_parent_git_discovery(service,tmp_path,monkeypatch):
    client,store=service
    archive=tmp_path/'archive';source=archive/'05_原型/backend/pharma';source.mkdir(parents=True)
    (source/'example.py').write_text('SYNTHETIC = True\n')
    monkeypatch.setattr(api,'ROOT',archive)
    id=submit(client);record=store.get(id)['input']
    assert record['commit'] is None
    assert record['revision_kind']=='source'
    assert record['revision'].startswith('source:')


def complete_with_artifacts(store,job_id):
    import hashlib
    # 2026-09-22 教训：曾用全局 pharma.jobs.ARTIFACTS（真实交付目录），
    # 'synthetic fixture' 桩文件随每次全量测试落进 07_交付/业务报告，用户按
    # 时间排序误当最新报告打开即损坏。调用方（service fixture / 测试）必须先
    # 把 jobs.ARTIFACTS 换成临时根；此护栏确保没人再悄悄写回真实目录。
    from pharma import jobs, config
    if Path(jobs.ARTIFACTS).resolve()==Path(config.ARTIFACTS).resolve():
        raise AssertionError('测试产物根未隔离：complete_with_artifacts 禁止写真实交付目录')
    folder=Path(jobs.ARTIFACTS)/job_id;folder.mkdir(parents=True,exist_ok=True)
    result={'execution_status':'COMPLETED'}
    for fmt in ('docx','pdf'):
        path=folder/('synthetic.'+fmt);path.write_bytes(b'synthetic fixture '+fmt.encode())
        result[fmt]=store.artifact(job_id,{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status':'PASS'},fmt)
    store.update(job_id,'DEGRADED',result)
