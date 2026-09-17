"""Independent synthetic regressions: no competition source values."""
import pytest
from pharma.actions import ActionStore,notification_proven
from pharma.jobs import JobStore

def draft(store):
    return store.draft({'snapshot_id':'synthetic','analysis_type':'monthly','month':'2026-03','product':'Synthetic'},'Verify energy ledger',{'name':'Reviewer','department':'Operations'},'Reconcile meter readings',verification_target='Meter ledger',expected_evidence=['Signed meter readings'],responsible_role='Energy accountant',deadline_basis='Before monthly close')

@pytest.mark.parametrize('changes',[{'task_title':''},{'verification_target':''},{'expected_evidence':[]},{'responsible_role':''},{'deadline':'2026-02-31'},{'suggestion':'[[context:month]]'}])
def test_edit_contract_rejects_unexecutable_payload(tmp_path,changes):
    s=ActionStore(tmp_path/'db');a=draft(s)
    with pytest.raises(ValueError):s.edit(a['id'],changes)
    assert s.get(a['id'])['payload_hash']==a['payload_hash']

def test_failed_notification_is_not_sent():
    assert not notification_proven({'notify_status':{'wechat':'failed','sent_at':'2026-01-01'}})

def test_malformed_remote_does_not_erase_verified_delivery(tmp_path):
    import httpx
    s=ActionStore(tmp_path/'db');a=draft(s);s.confirm(a['id'],a['payload_hash'])
    remote={'task_id':a['id'],'status':'sent','notify_status':{'wechat':'已发送至 Reviewer(Operations)','sent_at':'2026-03-01T00:00:00Z'}}
    s._state(a['id'],'SENT',remote)
    with httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=[]))) as client:
        result=s.refresh(a['id'],client)
    assert result['status']=='SENT'
    assert result['remote']==remote
    with s.db() as c:assert 'PROTOCOL' in c.execute('select last_error from outbox').fetchone()[0]

def test_degraded_job_reuses_completed_result(tmp_path):
    s=JobStore(tmp_path/'db');j=s.enqueue('report',{},'same-version');s.update(j['id'],'DEGRADED',{'generation_mode':'llm'})
    assert s.enqueue('report',{},'same-version')['id']==j['id']

def test_review_hashes_read_artifact_bytes(tmp_path,monkeypatch):
    from pharma import api,jobs
    import hashlib
    monkeypatch.setattr(jobs,'ARTIFACTS',tmp_path)
    store=JobStore(tmp_path/'db');monkeypatch.setattr(api,'store',store)
    job=store.enqueue('report',{});p=tmp_path/'file.docx';p.write_bytes(b'original')
    rec=store.artifact(job['id'],{'path':str(p),'sha256':hashlib.sha256(b'original').hexdigest()},'docx')
    store.update(job['id'],'DEGRADED',{'docx':rec});job=store.get(job['id'])
    assert api._current_hashes(job)['docx']==rec['sha256']
    p.write_bytes(b'changed')
    assert api._current_hashes(job)['docx']!=rec['sha256']
    with pytest.raises(ValueError,match='HASH'):api._current_hashes(job,strict=True)

def test_outbox_progresses_while_report_thread_is_blocked(tmp_path,monkeypatch):
    from pharma import worker
    from threading import Event,Thread
    delivered=Event();stop=Event()
    class Queue:
        def pending(self):return [{'action_id':'synthetic'}]
        def deliver_one(self,action_id):delivered.set();stop.set()
    monkeypatch.setattr(worker,'ActionStore',Queue);monkeypatch.setattr(worker,'RUNTIME',tmp_path)
    thread=Thread(target=worker.dispatch_loop,args=(stop,));thread.start()
    assert delivered.wait(2)
    thread.join(2)
    assert (tmp_path/'worker.heartbeat').is_file()
