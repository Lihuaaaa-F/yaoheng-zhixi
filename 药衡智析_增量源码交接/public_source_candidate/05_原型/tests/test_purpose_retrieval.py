"""Synthetic purpose retrieval: bounded queries, reserved slots and scope safety."""
import json
from hashlib import sha256
import pytest
from pharma import context_services as services, industry, knowledge


def setup_kb(tmp_path,monkeypatch,*,industry_id='pharmaceutical',include_current=True):
    records=[{'products':['SYNTH-P'],'text':'合成演示配方验证规程要求按生产批次核查成本及归集记录。'+f'附录{n}'} for n in range(12)]
    event={'products':['SYNTH-P'],'factory':'合成甲厂','event_period':'2031-05',
           'text':'合成演示传动部件磨损后发生生产运行异常，需要结合生产及费用记录核查影响。'}
    if include_current:records.append(event)
    records.extend([{**event,'products':['OTHER-P']},{**event,'event_period':'2031-04'},
                    {**event,'factory':'合成乙厂'},{**event,'event_period':None}])
    path=tmp_path/'enterprise_kb.json';path.write_text(json.dumps(records,ensure_ascii=False))
    context=industry.AnalysisContext(enterprise_id='synthetic-purpose',dataset_id='synthetic-kb',industry_id=industry_id,
        industry_version='1',policy_version='1',data_snapshot='synthetic',knowledge_snapshot=sha256(path.read_bytes()).hexdigest(),template_version='1',formula_version='1')
    monkeypatch.setattr(industry,'knowledge_entry_for_context',lambda c:path)
    monkeypatch.setattr(knowledge,'RUNTIME',tmp_path/'runtime')
    calls=[]
    class CountingKnowledge(knowledge.Knowledge):
        def __init__(self,**kwargs):super().__init__(vector_enabled=False,**kwargs)
        def search(self,query,**kwargs):
            calls.append({'query':query,**kwargs})
            return super().search(query,**kwargs)
    monkeypatch.setattr(services,'Knowledge',CountingKnowledge)
    snapshot={'analysis_context':context.model_dump(),'product':'SYNTH-P','factory':'合成甲厂','period':{'start':'2031-05','end':'2031-05'}}
    return snapshot,calls,path


def test_purpose_event_displaces_general_head_without_increasing_limit(tmp_path,monkeypatch):
    snapshot,calls,path=setup_kb(tmp_path,monkeypatch)
    baseline=knowledge.Knowledge(source_files=(path,),context=snapshot['analysis_context'],vector_enabled=False).search(
        '配方 验证',product='SYNTH-P',factory='合成甲厂',period=snapshot['period'],mode='bm25',limit=8)
    assert len(baseline['evidence'])==8 and not any(e.get('event_period') for e in baseline['evidence'])
    result=services.retrieve(snapshot,'配方 验证',mode='bm25',limit=8)
    assert result['status']=='PASS' and len(result['evidence'])==8
    assert len({e['evidence_id'] for e in result['evidence']})==8
    events=[e for e in result['evidence'] if e.get('event_period')]
    assert len(events)==1 and events[0]['event_period']=='2031-05'
    assert events[0]['products']==['SYNTH-P'] and events[0]['factory']=='合成甲厂'
    assert events[0]['retrieval_purpose']=='current_period_maintenance'
    assert len(calls)==2 and calls[-1]['event_only'] is True
    assert calls[0]['limit']==calls[1]['limit']==8
    assert result['purpose_retrieval']['eligible_event_count']==1


def test_wrong_product_period_factory_or_undated_event_is_not_supplemented(tmp_path,monkeypatch):
    snapshot,calls,_=setup_kb(tmp_path,monkeypatch,include_current=False)
    result=services.retrieve(snapshot,'配方 验证',mode='bm25',limit=8)
    assert not any(e.get('event_period') for e in result['evidence'])
    assert result['purpose_retrieval']['status']=='NO_APPLICABLE_EVENT_RECALLED'
    assert result['purpose_retrieval']['eligible_event_count']==0 and len(calls)==2


def test_baseline_current_event_uses_no_extra_query(tmp_path,monkeypatch):
    snapshot,calls,_=setup_kb(tmp_path,monkeypatch)
    result=services.retrieve(snapshot,'磨损',mode='bm25',limit=8)
    assert result['purpose_retrieval']['status']=='ALREADY_COVERED'
    assert len(calls)==1


def test_other_industries_do_not_inherit_pharmaceutical_queries(tmp_path,monkeypatch):
    snapshot,calls,_=setup_kb(tmp_path,monkeypatch,industry_id='mechanical_demo')
    result=services.retrieve(snapshot,'配方 验证',mode='bm25',limit=8)
    assert result['purpose_retrieval']['status']=='NOT_CONFIGURED' and len(calls)==1


def test_policy_rejects_unbounded_queries_and_policy_changes_change_version():
    context={'industry_id':'pharmaceutical'};policy=services.retrieval_policy(context)
    with pytest.raises(ValueError):services.RetrievalPolicy.model_validate({**policy.model_dump(),'max_supplemental_queries':2})
    with pytest.raises(ValueError):services.EventPurpose.model_validate({**policy.purpose.model_dump(),'reserved_slots':2})
    changed=policy.model_copy(update={'version':'next'})
    assert services._policy_version(changed)!=services._policy_version(policy)
