"""Independent synthetic defects reproduced on the actual store/API seams."""
import hashlib
import httpx
import pytest
from fastapi.testclient import TestClient
from pharma import api, jobs, reviews
from pharma.actions import ActionStore
from pharma.jobs import JobStore
from test_integration_safety import draft

@pytest.mark.parametrize('changes',[{'assignee':'bad'},{'finding':None},{'suggestion':[]},{'priority':[]}])
def test_wrong_edit_type_returns_4xx_and_keeps_draft(tmp_path,monkeypatch,changes):
    store=ActionStore(tmp_path/'db');a=draft(store);monkeypatch.setattr(api,'actions',store)
    with TestClient(api.app,raise_server_exceptions=False) as client:
        response=client.put('/api/actions/'+a['id'],json=changes)
    assert 400<=response.status_code<500
    assert store.get(a['id'])['payload_hash']==a['payload_hash']
    assert store.get(a['id'])['status']=='DRAFT' and not store.pending()

@pytest.mark.parametrize('field,value',[('assignee',{'name':'Other','department':'Other'}),('suggestion','Unconfirmed action')])
def test_post_receipt_must_reconcile_full_confirmed_payload(tmp_path,field,value):
    store=ActionStore(tmp_path/'db');a=draft(store);store.confirm(a['id'],a['payload_hash'])
    remote={**a['payload'],field:value,'status':'sent','notify_status':{'wechat':'已发送至 Other(Other)','sent_at':'synthetic'}}
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'code':200,'data':remote}))) as client:
        result=store.deliver_one(a['id'],client)
    assert result['status']=='CONFLICT'
    assert result['delivery']['notification']!='SIMULATED_SENT'

def test_incomplete_post_queries_then_timeout_preserves_proven_receipt(tmp_path):
    store=ActionStore(tmp_path/'db');a=draft(store);store.confirm(a['id'],a['payload_hash']);methods=[]
    def handler(r):
        methods.append(r.method)
        remote={**a['payload'],'status':'sent','notify_status':{'wechat':'已发送至 Reviewer(Operations)','sent_at':'synthetic'}}
        if r.method=='POST':remote={'task_id':a['id'],'status':'sent','notify_status':remote['notify_status']}
        return httpx.Response(200,json={'code':200,'data':remote})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:sent=store.deliver_one(a['id'],client)
    assert methods==['POST','GET'] and sent['status']=='SENT'
    def timeout(r):raise httpx.ReadTimeout('synthetic',request=r)
    with httpx.Client(transport=httpx.MockTransport(timeout)) as client:result=store.refresh(a['id'],client)
    assert result['status']=='SENT' and result['remote']==sent['remote']
    assert result['delivery']['notification']=='SIMULATED_SENT'
    assert result['metadata']['last_query']['status']=='FAILED'
    assert result['metadata']['last_query']['at']
    assert not store.pending()

def finished(tmp_path,monkeypatch):
    monkeypatch.setattr(jobs,'ARTIFACTS',tmp_path)
    s=JobStore(tmp_path/'db');j=s.enqueue('report',{'snapshot_id':'synthetic'},'same')
    result={'execution_status':'COMPLETED','human_review_status':'PENDING','snapshot':{'snapshot_id':'synthetic'},'narrative':{'status':'PASS','sentinel':'verified explanation'},'evidence':{'status':'PASS'}}
    for fmt in ('docx','pdf'):
        p=tmp_path/('report.'+fmt);p.write_bytes(b'synthetic-'+fmt.encode())
        result[fmt]=s.artifact(j['id'],{'status':'PASS','path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},fmt)
    s.update(j['id'],'DEGRADED',result)
    return s,j

@pytest.mark.parametrize('damage',['missing','changed'])
def test_unhealthy_cache_rebuilds_artifacts_but_reuses_verified_narrative(tmp_path,monkeypatch,damage):
    s,j=finished(tmp_path,monkeypatch)
    assert s.enqueue('report',{},'same')['id']==j['id']
    p=tmp_path/'report.pdf'
    if damage=='missing':p.unlink()
    else:p.write_bytes(b'changed')
    rebuilt=s.enqueue('report',{'snapshot_id':'synthetic'},'same')
    assert rebuilt['id']!=j['id']
    assert rebuilt['input']['repair_of']==j['id']
    assert rebuilt['result']['narrative']['sentinel']=='verified explanation'
    assert 'pdf' not in rebuilt['result'] and 'docx' not in rebuilt['result']
    assert s.enqueue('report',{},'same')['id']==rebuilt['id']

def test_valid_synthetic_review_synchronizes_projection_and_keeps_other_failure(tmp_path,monkeypatch):
    from pharma import reports
    s,j=finished(tmp_path,monkeypatch);monkeypatch.setattr(api,'store',s)
    rs=reviews.ReviewStore(tmp_path/'reviews');monkeypatch.setattr(reviews,'ReviewStore',lambda:rs)
    job=s.get(j['id']);hashes=api._current_hashes(job)
    rs.submit(job,hashes['docx'],hashes['pdf'],'Synthetic fixture reviewer',4,{k:{'status':'PASS'} for k in reviews.REVIEW_DIMENSIONS})
    monkeypatch.setattr(reports,'assess_report',lambda result,review=None:{'overall':'PASS','model_participation':{'status':'PASS'},**{k:{'status':'PASS' if review else 'PENDING'} for k in reviews.REVIEW_DIMENSIONS}})
    assert api._recalc_acceptance(j['id'])['status']=='PASS'
    current=s.get(j['id']);assert current['status']=='SUCCEEDED'
    assert current['result']['human_review_status']=='PASS'
    monkeypatch.setattr(reports,'assess_report',lambda result,review=None:{'overall':'FAIL','model_participation':{'status':'FAIL'},**{k:{'status':'PASS'} for k in reviews.REVIEW_DIMENSIONS}})
    api._recalc_acceptance(j['id']);current=s.get(j['id'])
    assert current['status']=='DEGRADED' and current['result']['human_review_status']=='PASS'
