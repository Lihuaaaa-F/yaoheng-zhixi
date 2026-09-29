"""Audit regressions use isolated databases and injected local failures."""
import hashlib
import runpy
import sqlite3
from pathlib import Path
from threading import Event
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from pharma import api, reviews, worker, assistant
from pharma.jobs import JobStore
from pharma.reviews import ReviewStore
from test_actions import prepared
from test_workspace_assistant import services, enqueue, OfflineGateway
from test_report_version_cache import service


@pytest.mark.parametrize('stage', ['QUEUED', 'GENERATING', 'FAILED'])
def test_acceptance_get_preserves_unfinished_or_failed_job(tmp_path, monkeypatch, stage):
    store = JobStore(tmp_path/'jobs.sqlite')
    monkeypatch.setattr(api, 'store', store)
    monkeypatch.setattr(reviews, 'ReviewStore', lambda: ReviewStore(tmp_path/'reviews.sqlite'))
    job = store.enqueue('report', {})
    if stage != 'QUEUED':
        store.update(job['id'], stage)
    before = store.get(job['id'])
    response = TestClient(api.app).get('/api/reports/'+job['id']+'/acceptance')
    assert response.status_code == 422
    assert 'REVIEW_TARGET_NOT_FINAL' in response.text
    assert store.get(job['id']) == before
    if stage != 'FAILED':
        assert store.next()['id'] == job['id']


@pytest.mark.parametrize('failure', ['pending', 'heartbeat', 'state', 'init'])
def test_dispatcher_recovers_next_iteration(tmp_path, monkeypatch, failure):
    stop = Event()
    actions = Mock()
    actions.pending.side_effect = [sqlite3.OperationalError('locked'), []] if failure == 'pending' else [[{'action_id':'a'}], []]
    if failure == 'state':
        actions.deliver_one.side_effect = RuntimeError('delivery failed')
        actions._state.side_effect = sqlite3.OperationalError('locked')
    factory = Mock(side_effect=[sqlite3.OperationalError('locked'), actions]) if failure == 'init' else Mock(return_value=actions)
    monkeypatch.setattr(worker, 'ActionStore', factory)
    monkeypatch.setattr(worker, 'RUNTIME', tmp_path)
    original = Path.write_text
    failed = []
    def write(path, *args, **kwargs):
        if failure == 'heartbeat' and not failed:
            failed.append(True)
            raise OSError('disk temporarily unavailable')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'write_text', write)
    iterations = []
    def wait(_):
        iterations.append(1)
        if len(iterations) == 2:
            stop.set()
    monkeypatch.setattr(stop, 'wait', wait)
    worker.dispatch_loop(stop)
    assert len(iterations) == 2
    assert (tmp_path/'worker.heartbeat').exists()
    assert actions.pending.called


def test_assistant_claim_failure_does_not_kill_scheduler(tmp_path, monkeypatch):
    ledger = Mock(path=tmp_path/'assistant.sqlite')
    done = Event()
    calls = []
    def claim():
        calls.append(1)
        if len(calls) == 1:
            raise sqlite3.OperationalError('database is locked')
        done.set()
        return None
    ledger.claim.side_effect = claim
    stop, thread = assistant.start_worker(ledger, None, None, None)
    try:
        assert done.wait(2), 'scheduler died before retrying claim'
        assert thread.is_alive()
    finally:
        stop.set()
        thread.join(2)


def test_assistant_sqlite_retrieval_failure_keeps_facts(services):
    ledger, jobs, actions, snapshot = services
    _, turn = enqueue(services)
    def retrieve(*args, **kwargs):
        raise sqlite3.OperationalError('database is locked')
    assistant.run_turn(ledger, turn, lambda _:snapshot, jobs, actions, OfflineGateway, retrieve)
    result = ledger.turn(turn['id'])
    assert result['status'] == 'completed'
    assert result['message']['facts'][0]['value'] == '12.34'
    assert {'name':'search_knowledge','status':'unavailable'} in result['message']['tools']


def test_acknowledgement_endpoint_is_named_idempotent_and_not_completion(tmp_path, monkeypatch):
    store, action = prepared(tmp_path)
    monkeypatch.setattr(api, 'actions', store)
    client = TestClient(api.app)
    url = '/api/actions/'+action['id']+'/acknowledge'
    assert client.post(url, json={'confirmed_by':'测试责任人'}).status_code == 422
    store._state(action['id'], 'SENT')
    assert client.post(url, json={'confirmed_by':' '}).status_code == 422
    first = client.post(url, json={'confirmed_by':'测试责任人','comment':'已接责'}).json()
    second = client.post(url, json={'confirmed_by':'另一测试人'}).json()
    assert first['metadata']['responsibility_confirmation'] == second['metadata']['responsibility_confirmation']
    assert first['metadata']['responsibility_confirmation']['remediation_completed'] is False
    assert first['status'] == 'SENT'


@pytest.mark.parametrize('status', ['confirmed', 'in_progress', 'completed'])
def test_sending_recovery_queries_without_resending(tmp_path, status):
    store, action = prepared(tmp_path)
    store._state(action['id'], 'SENDING')
    methods = []
    def handle(request):
        methods.append(request.method)
        return httpx.Response(200, json={'code':200, 'data':{**action['payload'], 'status':status}})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        recovered = store.deliver_one(action['id'], client)
        assert recovered['status'] == 'ACCEPTED'
        assert recovered['delivery']['notification'] == 'UNKNOWN'
        store.deliver_one(action['id'], client)
    assert methods == ['GET']


def test_artifact_hash_drift_rejects_review_endpoint(tmp_path, monkeypatch):
    from pharma import jobs
    store = JobStore(tmp_path/'jobs.sqlite')
    monkeypatch.setattr(api, 'store', store)
    monkeypatch.setattr(jobs, 'ARTIFACTS', tmp_path)
    job = store.enqueue('report', {})
    path = tmp_path/'report.docx'
    path.write_bytes(b'original')
    docx = store.artifact(job['id'], {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}, 'docx')
    store.update(job['id'], 'DEGRADED', {'docx':docx})
    path.write_bytes(b'changed')
    response = TestClient(api.app).post('/api/reports/'+job['id']+'/reviews', json={
        'reviewer':'测试审核人', 'attribution_score':4,
        **{key:{'status':'PASS','comment':''} for key in ('section_completeness','readability','visual_quality')}})
    assert response.status_code == 422
    assert 'HASH' in response.text


def test_missing_process_identity_never_counts_as_owned(monkeypatch):
    manage = runpy.run_path(str(Path(__file__).parents[1]/'scripts/manage.py'))
    monkeypatch.setitem(manage['alive'].__globals__, 'token', lambda pid:None)
    assert not manage['alive']({'pid':99999999,'token':None})


def test_rejected_action_can_be_corrected_but_requires_fresh_confirmation(tmp_path):
    store, action = prepared(tmp_path)
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(422,json={'detail':'invalid'}))) as client:
        failed = store.deliver_one(action['id'], client)
    assert failed['error'].startswith('HTTP_422')
    assert failed['retryable_edit'] is True
    edited = store.edit(action['id'], {'suggestion':'修订后重新核查'})
    assert edited['status'] == 'DRAFT'
    assert store.pending() == []
    with pytest.raises(ValueError, match='USER_CONFIRMATION_REQUIRED'):
        with httpx.Client() as client:
            store.deliver_one(action['id'], client)
    with pytest.raises(ValueError, match='RECONFIRM'):
        store.confirm(action['id'], action['payload_hash'])
    assert store.confirm(action['id'], edited['payload_hash'])['status'] == 'QUEUED'


@pytest.mark.parametrize('saved,current,expected', [(None,'123',False),('122','123',False),('123','123',True),('123',None,False)])
def test_windows_creation_time_prevents_pid_reuse(monkeypatch, saved, current, expected):
    import ctypes
    from types import SimpleNamespace
    manage=runpy.run_path(str(Path(__file__).parents[1]/'scripts/manage.py'))
    kernel=SimpleNamespace(OpenProcess=Mock(return_value=123456789012),CloseHandle=Mock())
    def exit_code(handle, code):
        code._obj.value=259
        return True
    def times(handle, created, *args):
        created._obj.dwHighDateTime=0
        created._obj.dwLowDateTime=int(current or 0)
        return current is not None
    kernel.GetExitCodeProcess=Mock(side_effect=exit_code)
    kernel.GetProcessTimes=Mock(side_effect=times)
    monkeypatch.setattr(ctypes,'WinDLL',lambda *a,**kw:kernel,raising=False)
    globals_=manage['alive'].__globals__
    monkeypatch.setitem(globals_,'token',manage['_windows_token'])
    assert manage['alive']({'pid':42,'token':saved}) is expected
    if saved is not None:
        kernel.CloseHandle.assert_called_once_with(123456789012)


def test_environment_checker_still_emits_json_when_font_probe_fails(monkeypatch,capsys):
    import sys,json,subprocess
    from types import SimpleNamespace
    scripts=Path(__file__).parents[1]/'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    checker=runpy.run_path(str(scripts/'check_environment.py'))['main']
    monkeypatch.setattr(subprocess,'run',lambda *a,**kw:SimpleNamespace(stdout='{"status":"PASS"}',stderr='',returncode=0))
    monkeypatch.setattr(subprocess,'check_output',Mock(side_effect=subprocess.CalledProcessError(1,['fc-match'])))
    monkeypatch.setitem(checker.__globals__,'frontend_input_hash',lambda:('fixture',1))
    monkeypatch.setattr(checker.__globals__['shutil'],'which',lambda _: '/fixture/tool')
    checker()
    result=json.loads(capsys.readouterr().out)
    assert result['font']=='FONT_CHECK_FAILED:CalledProcessError'


def test_worker_persists_unicode_record_under_non_utf8_locale(service, monkeypatch, tmp_path):
    import json
    from pharma import jobs
    from test_report_version_cache import submit, complete_with_artifacts
    client, store = service
    job_id = submit(client)
    complete_with_artifacts(store, job_id)
    job = store.get(job_id)
    snap = store.get_snapshot(job['input']['snapshot_id'])
    snap['attribution'] = {'status':'UNAVAILABLE'}
    job['result'].update(snapshot=snap,evidence={'status':'DEGRADED','evidence':[]},benchmark={},
                         narrative={'status':'DEGRADED','findings':[],'text':'合成说明🧪'})
    monkeypatch.setattr(worker,'ARTIFACTS',jobs.ARTIFACTS)
    folder=jobs.ARTIFACTS/job_id
    (folder/'report.docx').write_bytes(b'synthetic document')
    original=Path.write_text
    def legacy_locale(path,text,*args,**kwargs):
        if 'encoding' not in kwargs:
            text.encode('cp936')
        return original(path,text,*args,**kwargs)
    monkeypatch.setattr(Path,'write_text',legacy_locale)
    worker.process_job(store,job)
    result=store.get(job_id)
    assert result['status'] in ('SUCCEEDED','DEGRADED'),result['error']
    assert json.loads((folder/'record.json').read_text(encoding='utf-8'))['narrative']['text']=='合成说明🧪'
