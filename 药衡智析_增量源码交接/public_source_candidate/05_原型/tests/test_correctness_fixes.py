"""已知反例的定向回归：可信度修复 1—9（2026-09-20）。

每项测试对应一次真实缺陷（单位口径、检索范围、验收合同、模型路由、
重试、Agent 决策、任务过滤、启动状态、跨路径指标合同），防止回归。
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from pharma import api, narrative
from pharma.jobs import JobStore


# ---------- fix1：对标表单位与所选口径共用同一来源 ----------

def _generic_benchmark(context='mechanical_demo:synthetic-mechanical', basis='total'):
    from pharma.industry import analyze_reference, benchmark_reference
    snapshot, comparison = benchmark_reference(context, 'DEMO-01', '2026-06', '示范工厂A', '示范工厂B', basis=basis)
    return snapshot, comparison


def test_benchmark_table_unit_follows_total_basis(tmp_path):
    from pharma.reference_report import render, verify, benchmark_unit_of
    snapshot, comparison = _generic_benchmark(basis='total')
    assert benchmark_unit_of(snapshot, comparison) == snapshot['metrics']['total_cost']['unit']
    assert '元/' not in benchmark_unit_of(snapshot, comparison)  # 总额口径是纯货币单位
    snapshot['trend'] = []
    output = tmp_path / 'report.docx'
    render(snapshot, {'findings': []}, {'evidence': []}, output, comparison)
    result = verify(output, snapshot, comparison)
    assert result['status'] == 'PASS'


def test_benchmark_unit_mismatch_is_detected_by_verifier(tmp_path):
    """单位标错必须被验收识别：把总额口径的对标表标回单位口径应 FAIL。"""
    from pharma.reference_report import render, verify
    snapshot, comparison = _generic_benchmark(basis='total')
    snapshot['trend'] = []
    output = tmp_path / 'report.docx'
    render(snapshot, {'findings': []}, {'evidence': []}, output, comparison)
    tampered = json.loads(json.dumps(comparison))
    tampered['basis'] = 'unit'  # 数值是总额，单位却按单位口径核对
    result = verify(output, snapshot, tampered)
    assert result['status'] == 'FAIL'
    assert any(b['binding'].startswith('benchmark:') for b in result['numeric_binding_failures'])


def test_benchmark_context_carries_basis_for_snapshot_only_verify(tmp_path):
    """worker 产出的快照仅带 benchmark_context；验收器仍能取到口径。"""
    from pharma.industry import analyze_reference
    from pharma.reference_report import benchmark_unit_of
    snapshot, comparison = _generic_benchmark(basis='total')
    snapshot['benchmark_context'] = snapshot.get('benchmark_context') or {}
    snapshot['benchmark_context']['basis'] = comparison['basis']
    assert benchmark_unit_of(snapshot, None) == snapshot['metrics']['total_cost']['unit']


# ---------- fix2：非赛题知识检索完整传递工厂与检索模式 ----------

def test_kb_search_passes_factory_and_mode(monkeypatch):
    captured = {}
    from pharma import industry, context_services
    real_analyze = industry.analyze_reference

    def fake_analyze(cid, **kwargs):
        captured['analyze_kwargs'] = kwargs
        return real_analyze(cid, **kwargs)

    def fake_retrieve(snapshot, query, mode='hybrid', **kwargs):
        captured['snapshot_factory'] = snapshot.get('factory')
        captured['mode'] = mode
        return {'status': 'PASS', 'evidence': []}

    monkeypatch.setattr(industry, 'analyze_reference', fake_analyze)
    monkeypatch.setattr(context_services, 'retrieve', fake_retrieve)
    client = TestClient(api.app)
    response = client.post('/api/kb/search', json={
        'context_id': 'mechanical_demo:synthetic-mechanical',
        'query': '工序 单耗', 'factory': '示范工厂B', 'mode': 'bm25'})
    assert response.status_code == 200, response.text
    body = response.json()
    assert captured['snapshot_factory'] == '示范工厂B'
    assert captured['mode'] == 'bm25'
    assert body['requested_scope'] == {'factory': '示范工厂B', 'product': 'DEMO-01', 'mode': 'bm25'}


def test_kb_search_scope_negative_factory_not_silently_swapped(monkeypatch):
    """跨范围负例：请求工厂 B 时检索不得落在默认工厂 A。"""
    seen = []

    def fake_retrieve(snapshot, query, mode='hybrid', **kwargs):
        seen.append((snapshot.get('factory'), mode))
        return {'status': 'PASS', 'evidence': []}

    monkeypatch.setattr('pharma.context_services.retrieve', fake_retrieve)
    client = TestClient(api.app)
    client.post('/api/kb/search', json={
        'context_id': 'mechanical_demo:synthetic-mechanical',
        'query': '工序', 'factory': '示范工厂B', 'mode': 'vector'})
    assert seen == [('示范工厂B', 'vector')]


# ---------- fix3：验收合同版本明确，不再硬编码绑定数量 ----------

def _result_with_checks(checks):
    from pharma.reports import assess_report
    return assess_report({
        'narrative': {'findings': [], 'model_live': False},
        'evidence': {'status': 'PASS', 'evidence': []},
        'docx': {'status': 'PASS', 'verification': checks},
        'pdf': {'status': 'PASS'}, 'snapshot': {}})


def test_small_generic_report_meets_own_declared_binding_floor():
    """生成方声明下限（<70）时小报告的业务验收不再被旧数量误杀。"""
    checks = {'core_numbers': True, 'contract': 'generic-v2-role-bound',
              'contract_floor': 'expected_bindings', 'expected_bindings': 18,
              'numeric_bindings_checked': 18, 'numeric_binding_failures': []}
    assert _result_with_checks(checks)['calculation_consistency']['status'] == 'PASS'


def test_unknown_contract_version_fails_closed():
    checks = {'core_numbers': True, 'contract': 'generic-v9-unknown',
              'numeric_bindings_checked': 500, 'numeric_binding_failures': []}
    assert _result_with_checks(checks)['calculation_consistency']['status'] == 'FAIL'


def test_generic_v1_legacy_alias_no_longer_accepted():
    checks = {'core_numbers': True, 'contract': 'generic-v1',
              'numeric_bindings_checked': 500, 'numeric_binding_failures': []}
    assert _result_with_checks(checks)['calculation_consistency']['status'] == 'FAIL'


def test_reference_verifier_declares_expected_bindings(tmp_path):
    from pharma.industry import analyze_reference
    from pharma.reference_report import render
    snapshot = analyze_reference('mechanical_demo:synthetic-mechanical', month='2026-06')
    snapshot['trend'] = []
    rendered = render(snapshot, {'findings': []}, {'evidence': []}, tmp_path / 'r.docx')
    checks = rendered['verification']
    assert checks['contract'] == 'generic-v2-role-bound'
    assert checks['contract_floor'] == 'expected_bindings'
    assert 0 < checks['expected_bindings'] <= checks['numeric_bindings_checked']


# ---------- fix4：叙事模型路由贯穿配置解析与实际调用 ----------

def test_generate_defaults_to_narrative_route(monkeypatch, tmp_path):
    routes_requested = []

    class GatewayStub:
        model = 'route-model'; provider = 'openai'; base_url = 'https://route.invalid'
        key = ''; max_repairs = 0; dbpath = str(tmp_path / 'gw.sqlite3')

        def __init__(self, *args, **kwargs): pass

        @classmethod
        def for_route(cls, route, **kwargs):
            routes_requested.append(route)
            return cls()

        def complete(self, *args, **kwargs):
            raise RuntimeError('MODEL_KEY_NOT_SET')

    monkeypatch.setattr(narrative, 'ModelGateway', GatewayStub)
    from pharma.industry import analyze_reference
    snapshot = analyze_reference('mechanical_demo:synthetic-mechanical', month='2026-06')
    result = narrative.generate(snapshot, {'status': 'PASS', 'evidence': []}, use_cache=False)
    assert routes_requested == ['narrative']
    assert result['model'] == 'route-model'


def test_generation_versions_fingerprint_uses_narrative_route(monkeypatch):
    """缓存指纹与实际调用同源：路由换模型后指纹必须变化，旧缓存不再命中。"""
    fingerprint_models = []

    class GatewayStub:
        model = 'route-model'; provider = 'openai'; base_url = 'https://route.invalid'
        key = ''; max_repairs = 0

        def __init__(self, *args, **kwargs): pass

        @classmethod
        def for_route(cls, route, **kwargs):
            return cls()

    from pharma.industry import analyze_reference
    snapshot = analyze_reference('mechanical_demo:synthetic-mechanical', month='2026-06')
    monkeypatch.setattr(narrative, 'ModelGateway', GatewayStub)
    request = api.ReportRequest(context_id='mechanical_demo:synthetic-mechanical',
                                factory='示范工厂A', product='DEMO-01', month='2026-06')
    versions = api._generation_versions(snapshot, request)
    assert versions['model'] == 'route-model'


# ---------- fix5：DEGRADED 报告支持明确重试，旧结果保留 ----------

def _complete_degraded(store, job_id, artifacts_root):
    """构造真实降级形态：DOCX/PDF 产物完整（验收或模型维度降级）。"""
    import hashlib
    folder = Path(artifacts_root) / job_id
    folder.mkdir(parents=True, exist_ok=True)
    result = {'execution_status': 'COMPLETED'}
    for fmt in ('docx', 'pdf'):
        path = folder / ('report.' + fmt)
        path.write_bytes(b'fixture ' + fmt.encode())
        result[fmt] = store.artifact(job_id, {'path': str(path), 'status': 'PASS',
                                              'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}, fmt)
    store.update(job_id, 'DEGRADED', result)


def test_retry_degraded_report_creates_new_job_and_keeps_old(tmp_path, monkeypatch):
    import pharma.jobs as jobs_module
    monkeypatch.setattr(jobs_module, 'ARTIFACTS', tmp_path)
    store = JobStore(tmp_path / 'jobs.sqlite3')
    first = store.enqueue('report', {'snapshot_id': 's1', 'context_id': 'mechanical_demo:synthetic-mechanical'}, cache_key='k1')
    _complete_degraded(store, first['id'], tmp_path)
    again = store.enqueue('report', {'snapshot_id': 's1', 'context_id': 'mechanical_demo:synthetic-mechanical'}, cache_key='k1')
    assert again['id'] == first['id']  # 未要求重试时仍命中缓存（旧行为保留）
    retried = store.enqueue('report', {'snapshot_id': 's1', 'context_id': 'mechanical_demo:synthetic-mechanical'}, cache_key='k1', retry=True)
    assert retried['id'] != first['id']
    assert retried['status'] == 'QUEUED'
    assert retried['input']['retry_of'] == first['id']
    # 复用可用计算结果：确定性部分随新任务继承（夹具产物无 snapshot 时仅带溯源）
    assert retried['result'].get('repair_provenance', {}).get('source_job_id') == first['id']
    old = store.get(first['id'])
    assert old['status'] == 'DEGRADED'  # 旧结果保留
    assert 'CACHE_INVALIDATED_RETRY' in [e['stage'] for e in store.history(first['id'])]


def test_api_report_retry_flag_flows_to_store(tmp_path, monkeypatch):
    import pharma.jobs as jobs_module
    monkeypatch.setattr(jobs_module, 'ARTIFACTS', tmp_path)
    store = JobStore(tmp_path / 'jobs.sqlite3')
    monkeypatch.setattr(api, 'store', store)

    class GatewayStub:
        model = 'm'; provider = 'openai'; base_url = 'https://x.invalid'
        key = ''; max_repairs = 0

        def __init__(self, *a, **k): pass

        @classmethod
        def for_route(cls, route, **k): return cls()

    monkeypatch.setattr(narrative, 'ModelGateway', GatewayStub)
    client = TestClient(api.app)
    payload = {'context_id': 'mechanical_demo:synthetic-mechanical',
               'factory': '示范工厂A', 'product': 'DEMO-01', 'month': '2026-06'}
    first = client.post('/api/reports', json=payload).json()['job_id']
    _complete_degraded(store, first, tmp_path)
    same = client.post('/api/reports', json=payload).json()['job_id']
    assert same == first
    retried = client.post('/api/reports', json={**payload, 'retry': True}).json()['job_id']
    assert retried != first


# ---------- fix6：Agent 决策同时检查产物存在性与可用性 ----------

def _report_job(selection, snapshot_id, status='SUCCEEDED', created='2026-09-20T01:00:00', job_id='job-1'):
    return {'id': job_id, 'kind': 'report', 'status': status, 'created': created,
            'input': {**selection, 'snapshot_id': snapshot_id}, 'result': {}}


def _selection():
    return {'context_id': 'mechanical_demo:synthetic-mechanical', 'factory': '示范工厂A',
            'product': 'DEMO-01', 'month': '2026-06', 'analysis_type': 'monthly', 'basis': 'unit'}


def _snapshot():
    from pharma.industry import analyze_reference
    snapshot = analyze_reference('mechanical_demo:synthetic-mechanical',
                                 factory='示范工厂A', product='DEMO-01', month='2026-06')
    return snapshot


def test_decision_requests_report_when_artifacts_unhealthy():
    from pharma.decision import evaluate
    snapshot = _snapshot()
    jobs = [_report_job(_selection(), snapshot['snapshot_id'])]
    healthy = evaluate(snapshot, jobs, artifact_health=lambda job: False)
    assert healthy['decision'] == 'REPORT_NEEDED'
    assert any(s['id'] == 'artifact_health' for s in healthy['signals'])
    ok = evaluate(snapshot, jobs, artifact_health=lambda job: True)
    assert ok['decision'] == 'DASHBOARD_ONLY'


def test_decision_health_exception_fails_closed():
    from pharma.decision import evaluate
    snapshot = _snapshot()
    jobs = [_report_job(_selection(), snapshot['snapshot_id'])]

    def broken(job):
        raise OSError('artifact disappeared')

    assert evaluate(snapshot, jobs, artifact_health=broken)['decision'] == 'REPORT_NEEDED'


# ---------- fix7：任务列表先按业务范围查询，再分页 ----------

def test_scoped_job_list_not_lost_beyond_global_cutoff(tmp_path):
    store = JobStore(tmp_path / 'jobs.sqlite3')
    import time
    base = time.time() - 10_000
    for i in range(120):  # 更新的全局记录属于企业 A
        store.enqueue('report', {'snapshot_id': f'a{i}', 'context_id': 'ctx-A'})
    for i in range(30):  # 更早的记录属于企业 B
        with store.db() as c:
            created = time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime(base + i))
            c.execute("INSERT INTO jobs(id,cache_key,kind,status,stage,input,result,created,updated,error) "
                      "VALUES(?,NULL,'report','SUCCEEDED','VERIFYING',?,?,?,? ,NULL)",
                      (f'b{i}', json.dumps({'snapshot_id': f'b{i}', 'context_id': 'ctx-B'}),
                       '{}', created, created))
    scoped = store.list_jobs(context_id='ctx-B', limit=100)
    assert len(scoped) == 30  # 全局前100截断曾会吞掉 B 的全部历史
    assert all(j['input']['context_id'] == 'ctx-B' for j in scoped)


def test_api_jobs_endpoint_scoped_before_pagination(tmp_path, monkeypatch):
    store = JobStore(tmp_path / 'jobs.sqlite3')
    monkeypatch.setattr(api, 'store', store)
    for i in range(5):
        store.enqueue('report', {'snapshot_id': f'x{i}', 'context_id': 'ctx-A'})
    client = TestClient(api.app)
    body = client.get('/api/jobs', params={'context_id': 'ctx-A', 'limit': 3, 'offset': 0}).json()
    assert len(body) == 3
    assert all(j['input']['context_id'] == 'ctx-A' for j in body)


# ---------- fix8：启动成功必须包含后台任务处理能力 ----------

def _health_server(worker_alive):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps({'worker': {'alive': worker_alive}}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_worker_ready_requires_heartbeat():
    import importlib.util
    manage_path = Path(api.__file__).resolve().parents[2] / 'scripts' / 'manage.py'
    spec = importlib.util.spec_from_file_location('manage_under_test', manage_path)
    manage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manage)

    dead = _health_server(worker_alive=False)
    try:
        assert manage.worker_ready(dead.server_address[1]) is False
    finally:
        dead.shutdown(); dead.server_close()

    alive = _health_server(worker_alive=True)
    try:
        assert manage.worker_ready(alive.server_address[1]) is True
    finally:
        alive.shutdown(); alive.server_close()


# ---------- fix9：跨路径共用指标合同 ----------

def test_metric_contract_holds_on_all_paths():
    from pharma.industry import analyze_reference
    from pharma.metric_contract import validate_snapshot
    for context in ('mechanical_demo:synthetic-mechanical', 'chemical_demo:synthetic-chemical'):
        assert validate_snapshot(analyze_reference(context, month='2026-06')) == []
    from pharma.metrics import analyze
    pharma = analyze('中药一厂', '银黄口服液', '2026-05')
    assert validate_snapshot(pharma) == []


def test_metric_contract_detects_unit_drift():
    from pharma.industry import analyze_reference
    from pharma.metric_contract import validate_snapshot
    snapshot = analyze_reference('mechanical_demo:synthetic-mechanical', month='2026-06')
    snapshot['metrics']['mom']['unit'] = '元/件'  # 环比单位漂移
    errors = validate_snapshot(snapshot)
    assert any('mom' in e for e in errors)
