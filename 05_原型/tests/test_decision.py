"""Agent 自主决策（赛题加分项）：确定性策略、模型说明合同与台账。"""
import json
import pytest
from pharma import decision
from pharma.narrative import ModelGateway


def snapshot_factory(snapshot_id='snap-1',alerts=1):
    return {'snapshot_id':snapshot_id,'context_id':'pharmaceutical:synthetic-pharma','factory':'合成制药厂甲',
            'product':'合成制剂甲','month':'2026-06','analysis_type':'monthly','basis':'unit','period':{'start':'2026-06','end':'2026-06'},
            'elements':[{'key':'materials','name':'直接材料'}],
            'alerts':[{'alert_id':'alert-x','element_key':'materials','fact_summary':'直接材料 单位 环比 12%'}]*alerts}


def job_factory(job_id='job-1',status='SUCCEEDED',snapshot_id='snap-1',created='2026-06-02T10:00:00'):
    return {'id':job_id,'kind':'report','status':status,'created':created,
            'input':{'context_id':'pharmaceutical:synthetic-pharma','factory':'合成制药厂甲','product':'合成制剂甲',
                     'month':'2026-06','analysis_type':'monthly','basis':'unit','snapshot_id':snapshot_id}}


def test_no_report_for_period_requires_report():
    result=decision.evaluate(snapshot_factory(),[])
    assert result['decision']=='REPORT_NEEDED'
    assert result['engine']=='deterministic' and result['policy_version']==decision.DECISION_POLICY_VERSION
    assert any(s['id']=='report_for_period' and s['value']=='缺失' for s in result['signals'])


def test_same_snapshot_report_means_dashboard_only():
    jobs=[job_factory()]
    result=decision.evaluate(snapshot_factory(),jobs)
    assert result['decision']=='DASHBOARD_ONLY'
    assert any(s['id']=='snapshot_binding' and s['value']=='一致' for s in result['signals'])


def test_changed_snapshot_requires_report():
    jobs=[job_factory(snapshot_id='snap-OLD')]
    result=decision.evaluate(snapshot_factory('snap-NEW'),jobs)
    assert result['decision']=='REPORT_NEEDED'
    assert any(s['id']=='snapshot_binding' and s['value']=='过期' for s in result['signals'])


def test_other_selection_jobs_do_not_count():
    other=[job_factory(job_id='job-other',snapshot_id='snap-1')]
    other[0]['input']['month']='2026-05'
    result=decision.evaluate(snapshot_factory(),other)
    assert result['decision']=='REPORT_NEEDED'


def test_failed_jobs_are_ignored():
    jobs=[job_factory(status='FAILED',snapshot_id='snap-1')]
    assert decision.evaluate(snapshot_factory(),jobs)['decision']=='REPORT_NEEDED'


class FakeGateway:
    """模拟决策路由：可控返回与调用记录。"""
    def __init__(self,response=None,error=None):
        self.model='fake-small-model';self.key='k';self.response=response;self.error=error;self.calls=[]
    def complete(self,system,user,operation='generate',prompt_version=None):
        self.calls.append((system,user,operation,prompt_version))
        if self.error:raise self.error
        return json.dumps(self.response),{},{'requested_model':self.model,'returned_model':self.model,'identity_status':'VERIFIED_EXACT'}


def test_advisory_pass_shape_and_operation_route():
    fake=FakeGateway(response={'decision':'REPORT_NEEDED','signal_ids':['active_alerts','report_for_period']})
    result=decision.advise(decision.evaluate(snapshot_factory(),[]),snapshot_factory(),gateway_factory=lambda r:fake)
    assert result['advisory_status']=='PASS' and result['advisory_model']=='fake-small-model'
    assert '成本要素' in result['rationale']
    assert fake.calls and fake.calls[0][2]=='decision' and fake.calls[0][3]==decision.ADVISORY_PROMPT_VERSION


def test_advisory_rejects_bad_shape_and_never_changes_decision():
    for bad in ({'rationale':''},{'other':1},{'rationale':'x'*121},
                {'rationale':'材料环比上涨15%，建议出报告'},{'rationale':'缺三份记录需核查'}):
        fake=FakeGateway(response=bad)
        result=decision.advise(decision.evaluate(snapshot_factory(),[]),snapshot_factory(),gateway_factory=lambda r:fake)
        assert result['advisory_status']=='DEGRADED' and result['decision']=='REPORT_NEEDED'


def test_advisory_without_key_degrades_to_deterministic():
    class NoKey(FakeGateway):
        def __init__(self):super().__init__();self.key=''
    result=decision.advise(decision.evaluate(snapshot_factory(),[]),snapshot_factory(),gateway_factory=lambda r:NoKey())
    assert result['advisory_status']=='NO_KEY' and result['decision']=='REPORT_NEEDED'


def test_decision_store_records_and_binds(tmp_path):
    ledger=decision.DecisionStore(path=tmp_path/'decision.sqlite3')
    evaluation=decision.evaluate(snapshot_factory(),[])
    did=ledger.append({**evaluation,'advisory_status':'NO_KEY','advisory_model':'none'})
    rows=ledger.list()
    assert len(rows)==1 and rows[0]['decision']=='REPORT_NEEDED' and rows[0]['applied_job_id'] is None
    ledger.bind_job(did,'job-9')
    assert ledger.list()[0]['applied_job_id']=='job-9'


def test_model_route_fallback_and_env_override(tmp_path,monkeypatch):
    monkeypatch.delenv('PHARMA_MODEL_ROUTES',raising=False)
    for var in ('PHARMA_MODEL_DECISION_MODEL','PHARMA_MODEL_DECISION_BASE_URL','PHARMA_MODEL_DECISION_PROTOCOL','PHARMA_MODEL_DECISION_KEY_FILE'):
        monkeypatch.delenv(var,raising=False)
    gateway=ModelGateway.for_route('narrative',runtime=tmp_path)
    assert gateway.model==ModelGateway(runtime=tmp_path).model
    decision_gw=ModelGateway.for_route('decision',runtime=tmp_path)
    assert decision_gw.model==gateway.model and decision_gw.base_url==gateway.base_url  # 未配置时同源回退
    monkeypatch.setenv('PHARMA_MODEL_DECISION_MODEL','glm-4-flash')
    assert ModelGateway.for_route('decision',runtime=tmp_path).model=='glm-4-flash'
    with pytest.raises(ValueError):ModelGateway.for_route('unknown-route')
    monkeypatch.setenv('PHARMA_MODEL_ROUTES',json.dumps({'decision':{'model':'qwen-turbo'}}))
    assert ModelGateway.for_route('decision',runtime=tmp_path).model=='qwen-turbo'
    # 部分路由表：未配置的 narrative 路由必须回退主配置而非报错
    assert ModelGateway.for_route('narrative',runtime=tmp_path).model==ModelGateway(runtime=tmp_path).model
    monkeypatch.setenv('PHARMA_MODEL_ROUTES','{"decision":"bad-shape"}')
    with pytest.raises(ValueError):ModelGateway.for_route('decision',runtime=tmp_path)


def test_routes_status_reports_dedicated_flags(tmp_path,monkeypatch):
    monkeypatch.delenv('PHARMA_MODEL_ROUTES',raising=False)
    # 2026-09-22 三模块改版：路由更名 extraction/analysis；旧名 DECISION 仍可注入
    monkeypatch.setenv('PHARMA_MODEL_DECISION_MODEL','glm-4-flash')
    # 以临时 runtime 构造，避免读写本机运行库
    from pharma.narrative import ModelGateway as GW
    original=GW.__init__
    monkeypatch.setattr(GW,'__init__',lambda self,**kw:original(self,runtime=tmp_path,**kw))
    status=GW.routes_status()
    assert set(status['routes'])=={'extraction','analysis','assistant'}
    assert status['routes']['assistant']['independent'] is True
    assert status['routes']['assistant']['available'] is False
    assert status['routes']['extraction']['dedicated'] is True
    assert status['routes']['analysis']['dedicated'] is False
    assert status['routes']['extraction']['model']=='glm-4-flash'

@pytest.mark.parametrize('identity_status', ['MISMATCH', 'UNVERIFIED_MISSING'])
def test_advisory_rejects_unverified_identity(tmp_path, identity_status):
    fake = FakeGateway(response={'rationale': '当前期间缺少报告，建议生成报告。',
                                 'decision': 'REPORT_NEEDED', 'signal_ids': ['report_for_period']})
    complete = fake.complete
    def unverified(*args, **kwargs):
        raw, usage, identity = complete(*args, **kwargs)
        return raw, usage, {**identity, 'identity_status': identity_status, 'returned_model': None}
    fake.complete = unverified
    result = decision.advise(decision.evaluate(snapshot_factory(), []), snapshot_factory(), lambda _: fake)
    assert result['advisory_status'] == 'DEGRADED'
    assert result['advisory_identity']['identity_status'] == identity_status


def test_advisory_cannot_accept_opposite_free_text():
    fake = FakeGateway(response={'rationale': '无需生成报告，仅更新看板即可。'})
    result = decision.advise(decision.evaluate(snapshot_factory(), []), snapshot_factory(), lambda _: fake)
    assert result['advisory_status'] == 'DEGRADED'
    assert '无需生成报告' not in result['rationale']

@pytest.mark.parametrize('payload', [
    {'decision': 'DASHBOARD_ONLY', 'signal_ids': ['report_for_period']},
    {'decision': 'REPORT_NEEDED', 'signal_ids': ['invented']},
    {'decision': 'REPORT_NEEDED', 'signal_ids': ['active_alerts']},
    {'decision': 'REPORT_NEEDED', 'signal_ids': [None]},
    {'decision': 'REPORT_NEEDED', 'signal_ids': ['report_for_period'], 'rationale': '无需报告'},
])
def test_advisory_rejects_unbound_or_opposite_signals(payload):
    result = decision.advise(decision.evaluate(snapshot_factory(), []), snapshot_factory(),
                             lambda _: FakeGateway(response=payload))
    assert result['advisory_status'] == 'DEGRADED'
    assert result['decision'] == 'REPORT_NEEDED'
    assert '建议生成报告' in result['rationale']


def test_dashboard_advisory_is_bound_and_persisted(tmp_path):
    evaluation = decision.evaluate(snapshot_factory(), [job_factory()])
    result = decision.advise(evaluation, snapshot_factory(), lambda _: FakeGateway(
        response={'decision': 'DASHBOARD_ONLY', 'signal_ids': ['snapshot_binding']}))
    assert result['advisory_status'] == 'PASS'
    assert '仅更新看板即可' in result['rationale']
    ledger = decision.DecisionStore(tmp_path / 'decisions.sqlite3')
    row = ledger.get(ledger.append(result))
    evidence = json.loads(row['advisory_evidence'])
    assert evidence['advisory_identity']['returned_model'] == 'fake-small-model'
    assert evidence['advisory_signal_ids'] == ['snapshot_binding']
