from pharma.actions import ActionStore


def test_draft_edit_preserves_original_factory_selection(tmp_path):
    store = ActionStore(tmp_path / 'actions.sqlite')
    snapshot = {'snapshot_id': 'second-factory', 'context_id': 'demo:company',
                'factory': '二厂', 'product': '测试产品', 'month': '2026-06',
                'analysis_type': 'special', 'basis': 'total', 'topic': '材料核查'}
    draft = store.draft(snapshot, '核查原料记录', {'name': '演示责任人', 'department': '财务'},
                        '核对入库单', verification_target='入库单', expected_evidence=['入库单'],
                        responsible_role='成本会计', deadline_basis='月度结账前')
    edited = store.edit(draft['id'], {'suggestion': '核对领退料和入库记录'})
    assert edited['metadata']['selection'] == {k: snapshot[k] for k in
        ('factory', 'product', 'month', 'analysis_type', 'basis', 'topic')}
    assert edited['metadata']['snapshot_id'] == 'second-factory'
    assert 'selection' not in edited['payload']  # 官方 RPA 请求合同不扩展。


def test_invalid_template_keeps_previously_installed_bytes(tmp_path, monkeypatch):
    from docx import Document
    from pharma import reports
    import pytest
    target = tmp_path / 'templates'
    target.mkdir()
    old_doc = target / 'monthly.docx'
    old_map = target / 'monthly.placeholder_map.json'
    old_doc.write_bytes(b'previous validated template')
    old_map.write_text('{"previous":true}')
    source = tmp_path / 'candidate.docx'
    doc = Document()
    doc.add_paragraph('{{产品名称}}')
    doc.save(source)
    monkeypatch.setattr(reports, 'RUNTIME_TEMPLATES', target)
    def reject(_):
        raise ValueError('invalid candidate')
    monkeypatch.setattr(reports, 'validate_word_compat', reject)
    with pytest.raises(ValueError, match='invalid candidate'):
        reports.install_template(source, 'monthly')
    assert old_doc.read_bytes() == b'previous validated template'
    assert old_map.read_text() == '{"previous":true}'


def test_export_compilation_note_discloses_actual_generation_mode():
    from pharma.reports import compilation_note
    fallback=compilation_note({'generation_mode':'rules','model_live':False,'status':'DEGRADED'})
    assert '程序规则' in fallback and '本次未形成' in fallback
    assert '本次调用' not in fallback
    cached=compilation_note({'generation_mode':'llm','model_live':True,'status':'PASS','cache_hit':True})
    assert '复用既有结果' in cached and '本次调用' not in cached
    mixed=compilation_note({'generation_mode':'mixed','model_live':True,'status':'DEGRADED'})
    assert '混合解释' in mixed and '降级' in mixed


def test_local_rpa_sends_and_refreshes_with_unavailable_system_proxy(tmp_path, monkeypatch):
    import json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread
    from pharma.actions import _rpa_trust_environment
    for key in ('ALL_PROXY','HTTP_PROXY','HTTPS_PROXY','all_proxy','http_proxy','https_proxy'):
        monkeypatch.setenv(key,'socks5://127.0.0.1:1')
    for key in ('NO_PROXY','no_proxy'):
        monkeypatch.setenv(key,'')
    received={}
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.update(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.do_GET()
        def do_GET(self):
            data={**received,'status':'sent','notify_status':{'wechat':'已发送至 测试责任人(财务)','sent_at':'2026-09-24T12:00:00'}}
            body=json.dumps({'code':200,'data':data}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        store=ActionStore(tmp_path/'actions.sqlite')
        draft=store.draft({'snapshot_id':'local-proxy','product':'测试产品','month':'2026-06','analysis_type':'monthly'},
                          '核查采购单',{'name':'测试责任人','department':'财务'},'核对采购台账',
                          verification_target='采购单',expected_evidence=['采购台账'],responsible_role='成本会计',deadline_basis='结账前')
        store.confirm(draft['id'],draft['payload_hash'])
        url=f'http://127.0.0.1:{server.server_port}'
        sent=store.deliver_one(draft['id'],base_url=url)
        assert sent['status']=='SENT' and sent['delivery']['notification']=='SIMULATED_SENT'
        assert store.refresh(draft['id'],base_url=url)['status']=='SENT'
        assert received['task_id']==draft['id']
        assert _rpa_trust_environment('https://external-rpa.example') is True
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
