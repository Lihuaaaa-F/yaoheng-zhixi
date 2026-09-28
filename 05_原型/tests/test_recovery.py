from pharma.jobs import JobStore

def test_report_checkpoint_survives_store_recreation(tmp_path):
    s=JobStore(tmp_path/'jobs.sqlite')
    snap={'snapshot_id':'fixed-input','metrics':{'total_cost':{'value':'100'}}}
    s.snapshot(snap);j=s.enqueue('report',{'snapshot_id':'fixed-input'},'versioned-cache-key')
    s.update(j['id'],'GENERATING',{'snapshot':snap,'evidence':{'knowledge_version':'fixed-knowledge'}})
    recovered=JobStore(tmp_path/'jobs.sqlite')
    assert recovered.next()['id']==j['id']
    assert recovered.next()['result']['evidence']['knowledge_version']=='fixed-knowledge'
    assert recovered.get_snapshot('fixed-input')==snap
    assert recovered.enqueue('report',{'snapshot_id':'fixed-input'},'versioned-cache-key')['id']==j['id']

def test_running_report_cannot_download_mutating_file(tmp_path,monkeypatch):
    import pharma.jobs as jobs
    import hashlib,pytest
    monkeypatch.setattr(jobs,'ARTIFACTS',tmp_path)
    s=jobs.JobStore(tmp_path/'state.sqlite');j=s.enqueue('report',{})
    path=tmp_path/'report.docx';path.write_bytes(b'file before TOC update')
    a=s.artifact(j['id'],{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},'docx')
    with pytest.raises(ValueError,match='NOT_FINAL'):s.artifact_path(a['artifact_id'])
    s.update(j['id'],'DEGRADED')
    assert s.artifact_path(a['artifact_id'])==path
