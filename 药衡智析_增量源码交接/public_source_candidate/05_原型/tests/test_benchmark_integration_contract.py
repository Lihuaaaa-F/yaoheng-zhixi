"""Public synthetic regressions for cross-factory scope and model inputs."""
from types import SimpleNamespace
from pharma.jobs import JobStore

def test_competition_benchmark_uses_bound_retrieval(tmp_path, monkeypatch):
    from pharma import api, industry, narrative, context_services, knowledge
    seen=[]
    context={'enterprise_id':'competition','industry_id':'pharmaceutical','data_snapshot':'synthetic-only'}
    monkeypatch.setattr(api,'selected_context',lambda _: 'pharmaceutical:competition')
    monkeypatch.setattr(api,'benchmark_analysis',lambda *a,**k: ({'snapshot_id':'synthetic','factory':'Synthetic A','period':{}},{'elements':[]}))
    monkeypatch.setattr(industry,'resolve_context',lambda _: SimpleNamespace(model_dump=lambda:context,context_hash='scope'))
    def bound(snapshot,query,*,limit=5):
        seen.append(snapshot['analysis_context']);return {'status':'PASS','evidence':[]}
    monkeypatch.setattr(context_services,'retrieve',bound)
    def forbidden(*a,**k):raise AssertionError('unscoped retrieval bypass')
    monkeypatch.setattr(knowledge,'Knowledge',lambda *a,**k:SimpleNamespace(search=forbidden))
    monkeypatch.setattr(narrative,'generate',lambda *a,**k:{'findings':[]})
    monkeypatch.setattr(api,'store',JobStore(tmp_path/'db'))
    api.get_benchmark('Synthetic','2031-06','Synthetic A','Synthetic B',context_id='pharmaceutical:competition')
    assert seen==[context]

def test_reference_report_worker_passes_cross_metrics_to_generation(tmp_path, monkeypatch):
    from pharma import worker, industry, narrative, context_services
    snapshot=industry.analyze_reference('mechanical_demo:synthetic-mechanical',month='2026-06')
    from pharma.knowledge import PARSER_VERSION,RETRIEVER_VERSION,EMBEDDING_SHA,terminology_hash
    versions={'retrieval_policy':context_services.retrieval_policy_version(snapshot['analysis_context']),'validator':narrative.VALIDATOR_VERSION,'parser':PARSER_VERSION,'retriever':RETRIEVER_VERSION,'embedding':EMBEDDING_SHA,'terminology':terminology_hash()}
    store=JobStore(tmp_path/'db');store.snapshot(snapshot);job=store.enqueue('report',{'snapshot_id':snapshot['snapshot_id'],'versions':versions})
    captured=[]
    monkeypatch.setattr(context_services,'retrieve',lambda *a,**k:{'status':'PASS','evidence':[]})
    class GatewayStub:
        # worker/generate 现在统一经 for_route('narrative') 取网关（fix4）。
        model='synthetic';provider='openai';base_url='https://example.invalid'
        def __init__(self,*args,**kwargs):pass
        @classmethod
        def for_route(cls,route,**kwargs):return cls()
    monkeypatch.setattr(narrative,'ModelGateway',GatewayStub)
    def capture(value,evidence):
        captured.append(value)
        raise RuntimeError('stop after inspected model boundary; no network')
    monkeypatch.setattr(narrative,'generate',capture)
    worker.process_job(store,job)
    assert len(captured)==1
    cross=captured[0]['benchmark_context']
    refs={ref for row in cross['summary']+cross['elements'] for ref in row['metric_refs'].values()}
    assert refs
    assert refs<=set(captured[0]['metrics'])
