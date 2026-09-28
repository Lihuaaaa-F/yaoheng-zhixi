"""Delivery regressions: isolated artifacts, real queue and model-validation seams."""
import json
import sqlite3
import httpx
import pytest
from pharma import api, narrative, worker, reports, decision
from pharma.jobs import JobStore
from test_report_version_cache import service, submit, complete_with_artifacts
from test_decision import snapshot_factory, job_factory


def test_explicit_retry_discards_pass_checkpoint_and_bypasses_cache(service, monkeypatch):
    client, store = service
    first = submit(client)
    complete_with_artifacts(store, first)
    previous = store.get(first)
    previous['result'].update(snapshot=store.get_snapshot(previous['input']['snapshot_id']),
        evidence={'status': 'PASS', 'evidence': []}, benchmark={},
        narrative={'status': 'PASS', 'findings': [], 'cache_hit': True})
    store.update(first, 'DEGRADED', previous['result'])
    response = client.post('/api/reports', json={**{k: previous['input'][k] for k in
        ('context_id', 'product', 'factory', 'month')}, 'retry': True})
    second = response.json()['job_id']
    assert second != first
    assert 'narrative' not in store.get(second)['result']
    calls = []
    def generate(snapshot, evidence, **options):
        calls.append(options)
        return {'status': 'PASS', 'findings': []}
    monkeypatch.setattr(narrative, 'generate', generate)
    worker.process_job(store, store.get(second))
    assert calls == [{'use_cache': False}]
    assert store.get(second)['input']['retry_of'] == first
    assert store.get(first)['result']['narrative']['cache_hit'] is True


def test_partial_model_result_is_not_reused(tmp_path):
    snap = {'month': '2031-05', 'period': {'start': '2031-05', 'end': '2031-05'},
        'metrics': {}, 'elements': [{'key': 'materials', 'name': '直接材料', 'unit': '12', 'unit_delta': '2'},
                                  {'key': 'labor', 'name': '直接人工', 'unit': '3', 'unit_delta': '1'}],
        'alerts': [{'alert_id':'labor-alert','element_key':'labor','fact_summary':'人工需核查'}]}
    tasks = narrative.required_explanation_sections(snap)
    assert len(tasks) >= 2
    count = []
    def respond(request):
        count.append(request)
        sections = tasks[:1] if len(count) == 1 else tasks
        rows = [{'task_id': 'explain:'+s, 'claim_type': 'insufficient_evidence',
            'text_template': '未提供对应生产记录，尚不能确认变化原因，需核查成本明细。',
            'missing_evidence': ['对应生产记录'], 'recommendation': None} for s in sections]
        return httpx.Response(200, json={'model': 'controlled-model',
            'choices': [{'message': {'content': json.dumps({'explanations': rows})}}]})
    gw = narrative.ModelGateway(runtime=tmp_path, client=httpx.Client(transport=httpx.MockTransport(respond)),
        model='controlled-model', api_key='fixture', max_repairs=0)
    evidence = {'status': 'PASS', 'evidence': []}
    first = narrative.generate(snap, evidence, gateway=gw)
    assert first['status'] == 'DEGRADED' and first['model_live']
    second = narrative.generate(snap, evidence, gateway=gw)
    assert second['status'] == 'PASS' and not second['cache_hit'] and len(count) == 2
    third = narrative.generate(snap, evidence, gateway=gw)
    assert third['status'] == 'PASS' and third['cache_hit'] and len(count) == 2


@pytest.mark.parametrize('topic', [None, '', '  ', '\t\n'])
def test_empty_special_topic_normalized(service, topic):
    client, store = service
    data = client.post('/api/analyses', json={'context_id':'mechanical_demo:synthetic-mechanical',
        'product':'DEMO-01','factory':'示范工厂A','month':'2026-06','analysis_type':'special','topic':topic}).json()
    assert data['topic'] == '成本变化与证据核查'


def test_import_missing_elements_rejected_before_enqueue(service, monkeypatch):
    client, store = service
    from test_import_template_report import import_snapshot
    snap = import_snapshot(); snap['elements'] = snap['elements'][:1]
    monkeypatch.setattr(api, 'scoped_analysis', lambda req: snap)
    def forbidden(*a): pytest.fail('version/model preparation must not run for incomplete report')
    monkeypatch.setattr(api, '_generation_versions', forbidden)
    r = client.post('/api/reports', json={'month':'2026-06'})
    assert r.status_code == 422
    assert '人工' in r.text and '制造费用' in r.text
    assert store.list() == []


def test_import_template_change_rejected_before_render(service, monkeypatch, tmp_path):
    client, store = service
    from test_import_template_report import import_snapshot
    snap = import_snapshot()
    template = tmp_path/'template.docx'; template.write_bytes(b'first template')
    monkeypatch.setattr(reports, 'working_template', lambda kind: (template, tmp_path/'map.json'))
    # Reuse a valid registered context contract while retaining the real imported ID branch.
    base = api.scoped_analysis(api.ReportRequest(context_id='mechanical_demo:synthetic-mechanical',month='2026-06'))
    snap['analysis_context'] = base['analysis_context']
    monkeypatch.setattr(api, 'scoped_analysis', lambda req: snap)
    from pharma import industry
    from types import SimpleNamespace
    monkeypatch.setattr(industry, 'resolve_context', lambda cid: SimpleNamespace(model_dump=lambda: snap['analysis_context']))
    j, _ = api._enqueue_report(api.ReportRequest(month='2026-06'))
    template.write_bytes(b'changed after enqueue')
    worker.process_job(store, store.get(j['id']))
    assert store.get(j['id'])['error'] == 'ValueError: TEMPLATE_VERSION_CHANGED_RESUBMIT'


def test_decision_does_not_accept_model_failure():
    job = job_factory(status='DEGRADED')
    job['result'] = {'capability_status':'DEGRADED','narrative':{'status':'DEGRADED'}}
    assert decision.evaluate(snapshot_factory(), [job], lambda j: True)['decision'] == 'REPORT_NEEDED'


def test_decision_pending_human_only_does_not_recall_model():
    job = job_factory(status='DEGRADED')
    job['result'] = {'capability_status':'PASS','human_review_status':'PENDING'}
    assert decision.evaluate(snapshot_factory(), [job], lambda j: True)['decision'] == 'DASHBOARD_ONLY'


def test_decision_distinguishes_special_topics():
    snap=snapshot_factory();snap.update(analysis_type='special',topic='材料核查')
    job=job_factory();job['input'].update(analysis_type='special',topic='人工核查')
    assert decision.evaluate(snap,[job],lambda j:True)['decision']=='REPORT_NEEDED'


def s3_direction_snapshot():
    return {'elements':[{'key':'materials','name':'直接材料','unit':'11.99','unit_delta':'-0.36',
                        'total_delta':'100','share':'70.44653349'}],
        'metrics':{'unit_cost':{'value':'17.02','unit':'元/盒'}},
        'comparison':{'mom':{'base':'17.60'}},
        'period_changes':{'quantity':{'mom':{'delta':'100'}}}}


@pytest.mark.parametrize('text', [
    '制造费用与直接人工单位成本下降，可能摊薄材料占比。',
    '直接材料占比下降。', '材料单位成本上升。', '材料总额下降。'])
def test_contradictory_cost_directions_rejected(text):
    from pharma.narrative import validate_cost_directions
    with pytest.raises(ValueError, match='COST_DIRECTION_CONTRADICTION'):
        validate_cost_directions(text,s3_direction_snapshot())


def test_material_unit_decline_and_share_rise_are_distinct():
    from pharma.narrative import validate_cost_directions
    validate_cost_directions('材料单位成本下降，材料占比上升；材料总额上升。',s3_direction_snapshot())


@pytest.mark.parametrize('wording', ['属事件损失，不等于当月净减产。',
    '属事件口径，不能直接等同当月净减产，需核设备运行日志。',
    '属事件损失，不能直接当作当月净减产原因。'])
def test_event_loss_limitation_accepts_equivalent_language(wording):
    from pharma.narrative import validate_event_output
    validate_event_output('计量盘磨损可能影响产出，'+wording,s3_direction_snapshot())


@pytest.mark.parametrize('wording',['停工造成当月净减产。','本期产量下降，事件损失不等于本月净减产。'])
def test_actual_monthly_growth_cannot_be_relabelled_decline(wording):
    from pharma.narrative import validate_event_output
    with pytest.raises(ValueError,match='event loss'):
        validate_event_output(wording,s3_direction_snapshot())


def test_fresh_request_does_not_attach_to_ordinary_running_job(service):
    client,store=service
    first=submit(client)
    payload={k:store.get(first)['input'][k] for k in ('context_id','factory','product','month')}
    second=client.post('/api/reports',json={**payload,'generation_mode':'fresh_model'}).json()['job_id']
    assert second!=first and store.get(second)['input']['retry_of']==first
    assert client.post('/api/reports',json={**payload,'generation_mode':'fresh_model'}).json()['job_id']==second


def test_semantic_guards_run_at_finding_validation_boundary():
    snap=s3_direction_snapshot()
    snap['metrics']['material']={'value':'11.99','display':'11.99','unit':'元/盒'}
    ev={'evidence_id':'independent-fixture','source':'独立设备记录.txt','location':'第1行','text':'计量盘磨损可能影响批次合格产出'}
    finding={'claim_type':'hypothesis','hypothesis':True,'section':'materials',
        'text_template':'计量盘磨损可能影响产出，属事件损失，不能直接等同当月净减产。',
        'metric_refs':['material'],'evidence_refs':[ev['evidence_id']],
        'evidence_quotes':{ev['evidence_id']:ev['text']},'missing_evidence':['批次产出记录']}
    accepted=narrative.validate_findings([finding],snap,[ev])
    assert accepted[0]['claim_type']=='hypothesis'
    with pytest.raises(ValueError,match='COST_DIRECTION_CONTRADICTION'):
        narrative.validate_findings([{**finding,'text_template':'计量盘磨损可能摊薄材料占比。'}],snap,[ev])
